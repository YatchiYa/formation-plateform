"""RAG sur une base de code Python : découpage par fonction/classe (ast), métadonnées fichier:ligne,
recherche hybride (embeddings + BM25), réponses avec liens fichier:ligne vérifiés.

Usage :
  python code_rag.py index projet_demo
  python code_rag.py ou "les relances de paiement"          # où est géré X ? (sans génération)
  python code_rag.py ask "Comment est calculée la TVA d'une facture ?"
"""
import ast
import hashlib
import os
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
DIM = int(os.environ.get("EMBED_DIM", "768"))
DB_PATH = os.environ.get("DB_PATH", "code.db")
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
    """Tâche « code retrieval » : la question est en langage naturel, les documents sont du code."""
    from google.genai import types
    if kind == "query":
        texts = [f"task: code retrieval | query: {t}" for t in texts]
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


# --- Découpage par l'arbre syntaxique ---------------------------------------

def chunk_python(path: str, source: str) -> list[dict]:
    """Un morceau par fonction, par méthode, par classe (en-tête + signatures) et par constante de module.
    La docstring du module n'est pas un morceau à part : elle sert de contexte à tous les morceaux (titre)."""
    tree = ast.parse(source)
    module_doc = (ast.get_docstring(tree) or "").split("\n")[0]
    lines = source.splitlines()
    seg = lambda a, b: "\n".join(lines[a - 1:b])
    chunks = []

    def add(kind, name, node, text=None):
        start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno])
        chunks.append({"path": path, "kind": kind, "name": name, "start": start, "end": node.end_lineno,
                       "text": text or seg(start, node.end_lineno), "module_doc": module_doc})

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add("fonction", node.name, node)
        elif isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            # La classe seule = en-tête + docstring + signatures : une vue d'ensemble compacte.
            resume = [seg(node.lineno, node.lineno)]
            if ast.get_docstring(node):
                resume.append(f'    """{ast.get_docstring(node)}"""')
            resume += [f"    def {m.name}({ast.unparse(m.args)}): ..." for m in methods]
            add("classe", node.name, node, "\n".join(resume))
            for m in methods:
                add("methode", f"{node.name}.{m.name}", m)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            if names and names[0] != "__version__":
                add("constante", names[0], node)
    return chunks


def titre(c) -> str:
    """Titre d'embedding : fichier, rôle du module (1re ligne de sa docstring), type et nom."""
    return f"{c['path']} ({c['module_doc']}) {c['kind']} {c['name']}"


def label(c) -> str:
    return f"{c['path']}:{c['start']}"


# --- Index SQLite (incrémental par fichier) ---------------------------------

def connect(db_path=DB_PATH):
    db = sqlite3.connect(db_path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, sha256 TEXT);
        CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY, path TEXT, kind TEXT, name TEXT,
                                           start INTEGER, end INTEGER, text TEXT, vec BLOB);
    """)
    return db


def index_folder(db, root, embed_fn=embed) -> dict:
    stats = {"fichiers_indexes": 0, "inchanges": 0, "supprimes": 0, "morceaux": 0}
    known = dict(db.execute("SELECT path, sha256 FROM files"))
    seen = set()
    for f in sorted(Path(root).rglob("*.py")):
        rel = f.relative_to(root).as_posix()
        src = f.read_text(encoding="utf-8")
        digest = hashlib.sha256(src.encode()).hexdigest()
        seen.add(rel)
        if known.get(rel) == digest:
            stats["inchanges"] += 1
            continue
        chunks = chunk_python(rel, src)
        vecs = embed_fn([c["text"] for c in chunks],
                        titles=[titre(c) for c in chunks]) if chunks else []
        with db:
            db.execute("DELETE FROM chunks WHERE path = ?", (rel,))
            db.executemany("INSERT INTO chunks(path, kind, name, start, end, text, vec) VALUES (?,?,?,?,?,?,?)",
                           [(c["path"], c["kind"], c["name"], c["start"], c["end"], c["text"], v.tobytes())
                            for c, v in zip(chunks, vecs)])
            db.execute("INSERT OR REPLACE INTO files VALUES (?, ?)", (rel, digest))
        stats["fichiers_indexes"] += 1
        stats["morceaux"] += len(chunks)
    for gone in set(known) - seen:
        with db:
            db.execute("DELETE FROM chunks WHERE path = ?", (gone,))
            db.execute("DELETE FROM files WHERE path = ?", (gone,))
        stats["supprimes"] += 1
    return stats


# --- Recherche hybride -------------------------------------------------------

def tokens(text: str) -> list[str]:
    """Mots du code ET de la question : snake_case et CamelCase découpés, minuscules, SANS accents
    (le code écrit « numerotation », la question « numérotation »)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    words = re.findall(r"[A-Za-z]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", text))
    return [w.lower() for w in words if len(w) > 2]


def load(db) -> list[dict]:
    cols = ["path", "kind", "name", "start", "end", "text", "vec"]
    return [dict(zip(cols, r)) for r in db.execute(f"SELECT {', '.join(cols)} FROM chunks ORDER BY id")]


def search(db, question, k=5, mode="hybride", embed_fn=embed, qvec=None, chunks=None) -> list[dict]:
    """mode : vecteur | bm25 | hybride (fusion des rangs, RRF)."""
    chunks = chunks if chunks is not None else load(db)
    if not chunks:
        return []
    ranks = []
    if mode in ("vecteur", "hybride"):
        q = embed_fn([question], kind="query")[0] if qvec is None else qvec
        s = np.stack([np.frombuffer(c["vec"], dtype=np.float32) for c in chunks]) @ q
        ranks.append(np.argsort(-s))
    if mode in ("bm25", "hybride"):
        # Limite connue : BM25 reconstruit à chaque question, instantané sous ~10 000 morceaux ; au-delà, le mettre en cache.
        bm = BM25Okapi([tokens(f"{c['path']} {c['name']} {c['text']}") for c in chunks])
        ranks.append(np.argsort(-bm.get_scores(tokens(question))))
    # Reciprocal Rank Fusion : score = somme de 1 / (60 + rang) ; pas de normalisation de scores à régler.
    fused = {}
    for order in ranks:
        for r, i in enumerate(order):
            fused[int(i)] = fused.get(int(i), 0) + 1 / (60 + r + 1)
    best = sorted(fused, key=fused.get, reverse=True)[:k]
    keys = ("path", "kind", "name", "start", "end", "text")
    return [{**{key: chunks[i][key] for key in keys}, "rrf": round(fused[i], 4)} for i in best]


def ou_est_gere(db, sujet, k=5, embed_fn=embed) -> list[str]:
    """« Où est géré X ? » : une liste d'emplacements, sans appel de génération."""
    return [f"{label(h)}  {h['kind']} {h['name']}" for h in search(db, sujet, k, embed_fn=embed_fn)]


# --- Réponse avec liens fichier:ligne vérifiés -------------------------------

PROMPT = """Tu réponds à des questions sur le code du projet facturo, UNIQUEMENT à partir des extraits.
Cite chaque emplacement utilisé au format fichier:ligne, par exemple facturo/tva.py:12, en reprenant
l'en-tête de l'extrait (ou une ligne située à l'intérieur de cet extrait), sans backticks. Réponds en français, en 2 à 5
phrases. Si les extraits ne permettent pas de répondre, réponds exactement : "{refus}".

{context}

Question : {question}"""

# fichier.py:12 ou fichier.py:12-20, éventuellement entre backticks (que le modèle ajoute souvent)
CITATION = re.compile(r"`?([\w/]+\.py):(\d+)(?:-(\d+))?`?")


def citations_valides(texte, hits) -> bool:
    """Chaque fichier:ligne cité doit tomber dans un extrait fourni. Au moins une citation si pas de refus."""
    cites = CITATION.findall(texte)
    if texte.startswith(REFUS):
        return True
    return bool(cites) and all(any(h["path"] == p and h["start"] <= int(a) <= int(b or a) <= h["end"] for h in hits)
                               for p, a, b in cites)


def liens(texte, base="projet_demo") -> str:
    """facturo/tva.py:12-14 -> [facturo/tva.py:12-14](projet_demo/facturo/tva.py#L12-L14) (format GitHub)."""
    def lien(m):
        path, a, b = m.groups()
        texte_lien, ancre = (f"{path}:{a}-{b}", f"L{a}-L{b}") if b and b != a else (f"{path}:{a}", f"L{a}")
        return f"[{texte_lien}]({base}/{path}#{ancre})"
    return CITATION.sub(lien, texte)


def answer(db, question, k=5, embed_fn=embed, generate_fn=generate, qvec=None) -> dict:
    hits = search(db, question, k, embed_fn=embed_fn, qvec=qvec)
    context = "\n\n".join(f"--- {h['path']}:{h['start']}-{h['end']} ({h['kind']} {h['name']})\n{h['text']}"
                          for h in hits)
    text = generate_fn(PROMPT.format(refus=REFUS, context=context, question=question))
    ok = citations_valides(text, hits)
    return {"answer": liens(text) if ok else f"{REFUS} (citations non vérifiables)", "brut": text,
            "refus": text.startswith(REFUS) or not ok, "citations_ok": ok, "hits": hits}


if __name__ == "__main__":
    db = connect()
    cmd, arg = sys.argv[1], sys.argv[2]
    if cmd == "index":
        print(index_folder(db, arg))
    elif cmd == "ou":
        print("\n".join(ou_est_gere(db, arg)))
    elif cmd == "ask":
        r = answer(db, arg)
        print(r["answer"])
