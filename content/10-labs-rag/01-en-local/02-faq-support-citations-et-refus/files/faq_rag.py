"""RAG sur une FAQ de SAV (boutique fictive « Roue Libre ») : seuil de pertinence, citations obligatoires,
refus explicite et journal des questions non couvertes.

Usage :
  python faq_rag.py ask "Combien coûte la livraison ?"     # chaîne simple, sans agent
  python faq_rag.py rapport                                 # questions non couvertes, les plus fréquentes d'abord
"""
import collections
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
DIM = int(os.environ.get("EMBED_DIM", "768"))
SEUIL = float(os.environ.get("SEUIL", "0.71"))  # calibré avec eval.py --calibrer
K = int(os.environ.get("TOP_K", "3"))
HERE = Path(__file__).parent
FAQ_PATH = Path(os.environ.get("FAQ_PATH", HERE / "faq.json"))
INDEX_PATH = Path(os.environ.get("INDEX_PATH", HERE / "faq_index.npz"))
LOG_PATH = Path(os.environ.get("LOG_PATH", HERE / "questions_non_couvertes.jsonl"))
REFUS = "Je ne sais pas"
MESSAGE_REFUS = (f"{REFUS} : cette question n'est pas couverte par notre FAQ. "
                 "Un conseiller peut vous répondre via le formulaire de contact.")

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


def embed(texts, kind="doc"):
    from google.genai import types
    fmt = "task: question answering | query: {}" if kind == "query" else "title: none | text: {}"
    out = []
    for i in range(0, len(texts), 100):
        batch = [types.Content(parts=[types.Part(text=fmt.format(t))]) for t in texts[i:i + 100]]
        r = retry(lambda: client().models.embed_content(
            model=EMBED_MODEL, contents=batch,
            config=types.EmbedContentConfig(output_dimensionality=DIM)))
        out += [e.values for e in r.embeddings]
    v = np.array(out, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def generate(prompt, model=MODEL):
    return retry(lambda: client().models.generate_content(model=model, contents=prompt)).text.strip()


# --- Index : une entrée de FAQ = un morceau ---------------------------------

class FAQIndex:
    def __init__(self, faq_path=FAQ_PATH, index_path=INDEX_PATH, embed_fn=embed):
        self.embed_fn = embed_fn
        raw = Path(faq_path).read_bytes()
        self.entries = json.loads(raw)
        self.by_id = {e["id"]: e for e in self.entries}
        digest = hashlib.sha256(raw + f"{EMBED_MODEL}/{DIM}".encode()).hexdigest()
        cache = Path(index_path) if index_path else None
        if cache and cache.exists() and str(np.load(cache)["digest"]) == digest:
            self.vecs = np.load(cache)["vecs"]
        else:  # FAQ modifiée (ou modèle changé) : on recalcule tout, c'est petit
            self.vecs = embed_fn([f"{e['question']}\n{e['reponse']}" for e in self.entries])
            if cache:
                np.savez(cache, vecs=self.vecs, digest=digest)

    def search(self, question, k=K, qvec=None):
        q = self.embed_fn([question], kind="query")[0] if qvec is None else qvec
        scores = self.vecs @ q
        return [{**self.entries[i], "score": round(float(scores[i]), 3)} for i in np.argsort(-scores)[:k]]


def log_non_couverte(question, meilleur_score, path=None):
    with open(path or LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "question": question, "meilleur_score": meilleur_score},
                           ensure_ascii=False) + "\n")


def rechercher(index, question, seuil=None, k=K, log_path=None):
    """Le cœur partagé par la chaîne simple et l'outil de l'agent."""
    seuil = SEUIL if seuil is None else seuil
    hits = index.search(question, k)
    gardes = [h for h in hits if h["score"] >= seuil]
    if not gardes:
        log_non_couverte(question, hits[0]["score"] if hits else None, log_path)
        return {"status": "hors_perimetre", "meilleur_score": hits[0]["score"] if hits else None}
    return {"status": "ok", "resultats": [
        {"id": h["id"], "question": h["question"], "reponse": h["reponse"], "score": h["score"]}
        for h in gardes]}


def verifier_citations(texte, ids_autorises):
    """Une réponse (non refusée) doit citer au moins un id, et uniquement des id récupérés."""
    if texte.startswith(REFUS):
        return True
    cites = set(re.findall(r"FAQ-\d+", texte))
    return bool(cites) and cites <= set(ids_autorises)


PROMPT = """Tu es l'assistant du service client de la boutique Roue Libre. Réponds en français, en 1 à 3
phrases, UNIQUEMENT avec les entrées de FAQ ci-dessous, et cite l'identifiant entre crochets, par
exemple [FAQ-02]. Si les entrées ne répondent pas à la question, réponds exactement : "{refus}".

{context}

Question du client : {question}"""


def repondre(index, question, generate_fn=generate, seuil=None, log_path=None):
    """Chaîne simple (sans agent) : seuil -> génération -> garde-fou des citations."""
    r = rechercher(index, question, seuil, log_path=log_path)
    if r["status"] != "ok":  # aucun appel au modèle : rapide, gratuit, sûr
        return {"answer": MESSAGE_REFUS, "refus": True, "ids": [], "raison": "seuil"}
    ids = [h["id"] for h in r["resultats"]]
    context = "\n".join(f"[{h['id']}] {h['question']} {h['reponse']}" for h in r["resultats"])
    text = generate_fn(PROMPT.format(refus=REFUS, context=context, question=question))
    if not verifier_citations(text, ids):
        log_non_couverte(question, r["resultats"][0]["score"], log_path)
        return {"answer": MESSAGE_REFUS, "refus": True, "ids": ids, "raison": "citation invalide"}
    if text.startswith(REFUS):
        log_non_couverte(question, r["resultats"][0]["score"], log_path)
        return {"answer": MESSAGE_REFUS, "refus": True, "ids": ids, "raison": "modele"}
    return {"answer": text, "refus": False, "ids": ids, "raison": None}


def rapport(log_path=None, top=10):
    """Questions non couvertes regroupées (texte normalisé), les plus fréquentes d'abord."""
    log_path = log_path or LOG_PATH
    if not Path(log_path).exists():
        return []
    norm = lambda q: " ".join(re.sub(r"[^\w\s]", " ", q.lower()).split())
    lignes = [json.loads(l) for l in open(log_path, encoding="utf-8") if l.strip()]
    compte = collections.Counter(norm(l["question"]) for l in lignes)
    return compte.most_common(top)


if __name__ == "__main__":
    if sys.argv[1] == "rapport":
        for q, n in rapport():
            print(f"{n:3} x {q}")
    else:
        r = repondre(FAQIndex(), sys.argv[2])
        print(r["answer"], f"\n  (sources : {r['ids']}, raison du refus : {r['raison']})")
