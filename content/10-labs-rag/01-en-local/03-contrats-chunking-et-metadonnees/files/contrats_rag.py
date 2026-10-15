"""RAG sur des contrats : découpage par structure (articles, clauses), métadonnées, filtres,
questions comparatives et tableau récapitulatif.

Usage :
  python contrats_rag.py index contrats
  python contrats_rag.py ask "Quel est le préavis de résiliation du contrat avec Kerlogic ?"
  python contrats_rag.py tableau
"""
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
FAST_MODEL = os.environ.get("FAST_MODEL", "gemini-3.5-flash-lite")  # filtres et tableau
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
DIM = int(os.environ.get("EMBED_DIM", "768"))
DB_PATH = os.environ.get("DB_PATH", "contrats.db")
REFUS = "Je ne sais pas"

_client = None


def client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client()
    return _client


def retry(fn, tries=5):
    from google.genai import errors
    for i in range(tries):
        try:
            return fn()
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == tries - 1:
                raise
            time.sleep(2 ** i * 2)


def embed(texts, kind="doc", titles=None):
    from google.genai import types
    if kind == "query":
        texts = [f"task: question answering | query: {t}" for t in texts]
    else:
        texts = [f"title: {ti} | text: {t}" for ti, t in zip(titles or ["none"] * len(texts), texts)]
    out = []
    for i in range(0, len(texts), 100):
        batch = [types.Content(parts=[types.Part(text=t)]) for t in texts[i:i + 100]]
        r = retry(lambda: client().models.embed_content(
            model=EMBED_MODEL, contents=batch,
            config=types.EmbedContentConfig(output_dimensionality=DIM)))
        out += [e.values for e in r.embeddings]
    v = np.array(out, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def generate(prompt, model=MODEL):
    return retry(lambda: client().models.generate_content(model=model, contents=prompt)).text.strip()


def generate_json(prompt, schema, model=FAST_MODEL):
    """Sortie structurée : Gemini renvoie un JSON conforme au modèle pydantic `schema`."""
    from google.genai import types
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema)
    return retry(lambda: client().models.generate_content(model=model, contents=prompt, config=cfg)).parsed


# --- Analyse de la structure ------------------------------------------------

ARTICLE = re.compile(r"^Article (\d+) – (.+)$", re.M)


def parse_contract(text: str) -> dict:
    """En-tête « Clé : valeur » puis articles « Article N – Titre » et clauses « N.i texte »."""
    head, _, body = text.partition("\n\n")
    lines = head.splitlines()
    meta = dict(l.split(" : ", 1) for l in lines[1:] if " : " in l)
    contrat = {"titre": lines[0], "ref": meta["Référence"], "type": meta["Type"],
               "parties": meta["Parties"].split(" ; "), "date": meta["Date de signature"], "articles": []}
    heads = list(ARTICLE.finditer(body))
    for h, nxt in zip(heads, heads[1:] + [None]):
        block = body[h.end():nxt.start() if nxt else len(body)]
        clauses = re.findall(r"^(\d+\.\d+) (.+)$", block, re.M)
        contrat["articles"].append({"num": int(h.group(1)), "titre": h.group(2), "clauses": clauses})
    return contrat


def chunk_structure(contrat: dict, max_chars: int = 500) -> list[dict]:
    """Un morceau par article ; un article trop long est coupé ENTRE deux clauses, titre répété."""
    chunks = []
    for a in contrat["articles"]:
        head = f"Article {a['num']} – {a['titre']}"
        group = []
        for num, txt in a["clauses"]:
            line = f"{num} {txt}"
            if group and len(head) + sum(len(g) + 1 for g in group) + len(line) > max_chars:
                chunks.append({"article": a["num"], "titre_article": a["titre"], "text": "\n".join([head] + group)})
                group, head = [], f"Article {a['num']} – {a['titre']} (suite)"
            group.append(line)
        chunks.append({"article": a["num"], "titre_article": a["titre"], "text": "\n".join([head] + group)})
    return chunks


def chunk_taille(text: str, size: int = 400, overlap: int = 60) -> list[dict]:
    """Découpage naïf par taille, pour comparaison : ignore complètement la structure."""
    step = size - overlap
    return [{"article": None, "titre_article": None, "text": text[i:i + size]}
            for i in range(0, max(len(text) - overlap, 1), step)]


# --- Index SQLite avec métadonnées ------------------------------------------

def connect(db_path=DB_PATH):
    db = sqlite3.connect(db_path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS contrats (
            ref TEXT PRIMARY KEY, fichier TEXT, type TEXT, titre TEXT,
            parties TEXT, date TEXT, sha256 TEXT, texte TEXT);
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY, ref TEXT, strategie TEXT, article INTEGER,
            titre_article TEXT, text TEXT, vec BLOB);
        CREATE INDEX IF NOT EXISTS chunks_ref ON chunks(ref, strategie);
    """)
    return db


def titre_embedding(c):
    return f"{c['ref']} {c['titre']} ({', '.join(c['parties'])})"


def index_folder(db, folder, embed_fn=embed) -> dict:
    stats = {"indexes": 0, "inchanges": 0, "morceaux_structure": 0, "morceaux_taille": 0}
    known = dict(db.execute("SELECT fichier, sha256 FROM contrats"))
    for f in sorted(Path(folder).glob("*.txt")):
        text = f.read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode()).hexdigest()
        if known.get(f.name) == digest:
            stats["inchanges"] += 1
            continue
        c = parse_contract(text)
        rows = [("structure", ch) for ch in chunk_structure(c)] + [("taille", ch) for ch in chunk_taille(text)]
        vecs = embed_fn([ch["text"] for _, ch in rows], titles=[titre_embedding(c)] * len(rows))
        with db:
            db.execute("DELETE FROM chunks WHERE ref = ?", (c["ref"],))
            db.execute("INSERT OR REPLACE INTO contrats VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (c["ref"], f.name, c["type"], c["titre"], json.dumps(c["parties"], ensure_ascii=False),
                        c["date"], digest, text))
            db.executemany("INSERT INTO chunks(ref, strategie, article, titre_article, text, vec) VALUES (?,?,?,?,?,?)",
                           [(c["ref"], s, ch["article"], ch["titre_article"], ch["text"], v.tobytes())
                            for (s, ch), v in zip(rows, vecs)])
        stats["indexes"] += 1
        for s, _ in rows:
            stats[f"morceaux_{s}"] += 1
    return stats


def valeurs_connues(db) -> dict:
    types = sorted(r[0] for r in db.execute("SELECT DISTINCT type FROM contrats"))
    parties = sorted({p for (js,) in db.execute("SELECT parties FROM contrats") for p in json.loads(js)})
    return {"types": types, "parties": parties}


def search(db, question, k=4, strategie="structure", filtres=None, par_contrat=None, embed_fn=embed, qvec=None):
    """Filtre SQL sur les métadonnées, PUIS similarité. par_contrat=n : n meilleurs morceaux par contrat."""
    f = filtres or {}
    sql = ("SELECT c.ref, ch.article, ch.titre_article, ch.text, ch.vec, c.type, c.parties, c.date FROM chunks ch "
           "JOIN contrats c ON c.ref = ch.ref WHERE ch.strategie = ?")
    args = [strategie]
    for col, op, key in [("c.type", "=", "type"), ("c.parties", "LIKE", "partie"),
                         ("c.date", ">=", "apres"), ("c.date", "<=", "avant")]:
        if f.get(key):
            sql += f" AND {col} {op} ?"
            args.append(f"%{f[key]}%" if op == "LIKE" else f[key])
    rows = db.execute(sql, args).fetchall()
    if not rows:
        return []
    q = embed_fn([question], kind="query")[0] if qvec is None else qvec
    scores = np.stack([np.frombuffer(r[4], dtype=np.float32) for r in rows]) @ q
    order = np.argsort(-scores)
    if par_contrat:
        pris, best = {}, []
        for i in order:
            if pris.get(rows[i][0], 0) < par_contrat:
                pris[rows[i][0]] = pris.get(rows[i][0], 0) + 1
                best.append(i)
    else:
        best = order[:k]
    return [{"ref": rows[i][0], "article": rows[i][1], "titre_article": rows[i][2], "text": rows[i][3],
             "score": round(float(scores[i]), 3), "type": rows[i][5],
             "parties": " / ".join(json.loads(rows[i][6])), "date": rows[i][7]} for i in best]


def contexte(hits):
    """Les métadonnées vont AUSSI dans le contexte : sans elles, le modèle ne sait pas quel contrat il lit."""
    return "\n\n".join(f"[{h['ref']} art. {h['article']}] (contrat de {h['type']} entre {h['parties']}, "
                       f"signé le {h['date']})\n{h['text']}" for h in hits)


# --- Filtres extraits de la question (self-query) ---------------------------

class Filtres(BaseModel):
    type: Optional[str] = None
    partie: Optional[str] = None
    apres: Optional[str] = None
    avant: Optional[str] = None
    comparatif: bool = False


FILTRES_PROMPT = """Extrais les filtres de recherche de la question sur des contrats.
- type : une valeur parmi {types}, ou null si la question ne vise pas un type précis.
- partie : une valeur parmi {parties} SAUF "Atelier Nova" (partie à tous les contrats), ou null.
  Si la question nomme une société absente de la liste, recopie son nom tel quel.
- apres / avant : dates de signature AAAA-MM-JJ si la question en donne, sinon null.
- comparatif : true si la question compare ou liste plusieurs contrats.
Question : {question}"""


def extraire_filtres(db, question, generate_json_fn=generate_json) -> dict:
    v = valeurs_connues(db)
    f = generate_json_fn(FILTRES_PROMPT.format(question=question, **v), Filtres)
    f = f if isinstance(f, dict) else f.model_dump()
    if f.get("type") not in v["types"]:  # garde-fou : jamais de valeur inventée dans un filtre de type
        f["type"] = None
    return f


PROMPT = """Tu es l'assistant juridique d'Atelier Nova. Réponds en français UNIQUEMENT à partir des extraits.
Cite chaque affirmation au format [CT-AAAA-NNN art. N]. Si la question compare plusieurs contrats,
réponds par un tableau Markdown avec une ligne par contrat. Si les extraits ne permettent pas de
répondre, réponds exactement : "{refus}".

Extraits :
{context}

Question : {question}"""


def answer(db, question, embed_fn=embed, generate_fn=generate, generate_json_fn=generate_json) -> dict:
    filtres = extraire_filtres(db, question, generate_json_fn)
    hits = search(db, question, k=4, filtres=filtres,
                  par_contrat=2 if filtres.get("comparatif") else None, embed_fn=embed_fn)
    if not hits:  # aucun contrat ne correspond aux filtres : inutile d'appeler le modèle
        return {"answer": f"{REFUS} : aucun contrat ne correspond ({filtres}).", "refus": True,
                "hits": [], "filtres": filtres}
    text = generate_fn(PROMPT.format(refus=REFUS, context=contexte(hits), question=question))
    return {"answer": text, "refus": text.startswith(REFUS), "hits": hits, "filtres": filtres}


# --- Tableau récapitulatif --------------------------------------------------

class Recap(BaseModel):
    duree: str
    preavis_resiliation: str
    montant: str
    juridiction: str


RECAP_PROMPT = """Extrais de ce contrat, en quelques mots chacun : la durée, le préavis de résiliation
(ou de non-renouvellement), le montant (avec sa périodicité) et la juridiction compétente.
Écris "non précisé" si le contrat ne le dit pas. N'invente rien.

{texte}"""


def tableau(db, generate_json_fn=generate_json) -> str:
    lignes = ["| Contrat | Type | Partie | Signé le | Durée | Préavis | Montant | Juridiction |",
              "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for ref, type_, parties, date, texte in db.execute(
            "SELECT ref, type, parties, date, texte FROM contrats ORDER BY date"):
        r = generate_json_fn(RECAP_PROMPT.format(texte=texte), Recap)
        r = r if isinstance(r, dict) else r.model_dump()
        autre = [p for p in json.loads(parties) if p != "Atelier Nova"][0]
        lignes.append(f"| {ref} | {type_} | {autre} | {date} | {r['duree']} | {r['preavis_resiliation']} "
                      f"| {r['montant']} | {r['juridiction']} |")
    return "\n".join(lignes)


if __name__ == "__main__":
    db = connect()
    cmd = sys.argv[1]
    if cmd == "index":
        print(index_folder(db, sys.argv[2]))
    elif cmd == "ask":
        r = answer(db, sys.argv[2])
        print("filtres :", {k: v for k, v in r["filtres"].items() if v})
        print(r["answer"])
        for h in r["hits"]:
            print(f"  - {h['ref']} art. {h['article']} {h['titre_article']} (score {h['score']})")
    elif cmd == "tableau":
        print(tableau(db))
