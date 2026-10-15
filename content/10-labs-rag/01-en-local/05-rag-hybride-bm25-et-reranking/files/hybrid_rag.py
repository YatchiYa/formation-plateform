"""RAG hybride : BM25 + recherche vectorielle, fusion RRF, reranking par Gemini.

Usage : python hybrid_rag.py "Que signifie l'erreur HEL-6030 ?"
"""
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel
from rank_bm25 import BM25Okapi

HERE = Path(__file__).parent
load_dotenv(HERE / ".env")
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))

STOPWORDS = set("""le la les l un une des de du d et ou a à au aux en dans sur pour par avec sans ce cet cette ces
que qui quoi quel quelle quels quelles est sont être faire fait je j tu il elle on nous vous ils mon ma mes
son sa ses nos vos leur leurs se s ne n pas plus comment pourquoi combien peut il y ai as""".split())


# ---------- Appels Gemini (avec nouvelles tentatives sur 429/503) ----------
def gemini():
    from google import genai
    return genai.Client()  # lit GOOGLE_API_KEY (ou GEMINI_API_KEY) dans l'environnement


def with_retry(fn, tries=6):
    from google.genai import errors
    for i in range(tries):
        try:
            return fn()
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == tries - 1:
                raise
            time.sleep(2 ** i)


def embed(client, texts: list[str]) -> np.ndarray:
    """Un vecteur normalisé (norme 1) par texte."""
    from google.genai import types
    out = []
    for i in range(0, len(texts), 50):
        # Avec gemini-embedding-2, une liste de chaînes est fusionnée en UN seul vecteur :
        # on passe donc un Content par texte pour obtenir un vecteur par texte.
        contents = [types.Content(parts=[types.Part(text=t)]) for t in texts[i:i + 50]]
        r = with_retry(lambda: client.models.embed_content(
            model=EMBED_MODEL, contents=contents,
            config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM)))
        out += [e.values for e in r.embeddings]
    v = np.array(out, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


# ---------- Briques de recherche (fonctions pures, testables sans clé) ----------
def tokenize(text: str) -> list[str]:
    """Minuscules, sans accents, en gardant les identifiants entiers (hel-6030, sync.batch_size)."""
    text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return [t for t in re.findall(r"[a-z0-9_]+(?:[.-][a-z0-9_]+)*", text) if t not in STOPWORDS]


def bm25_search(bm25: BM25Okapi, query: str, k: int = 20) -> list[int]:
    scores = bm25.get_scores(tokenize(query))
    return [int(i) for i in np.argsort(-scores)[:k] if scores[i] > 0]


def vector_search(doc_vecs: np.ndarray, q_vec: np.ndarray, k: int = 20) -> list[int]:
    return [int(i) for i in np.argsort(-(doc_vecs @ q_vec))[:k]]


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    """Reciprocal Rank Fusion : score(d) = somme des 1 / (k + rang), rang commençant à 1."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda d: -scores[d])


class Ranking(BaseModel):
    ids: list[str]


def llm_rerank(client, question: str, docs: list[dict], candidates: list[int]) -> list[int]:
    """Demande à Gemini de trier les candidats ; ceux qu'il oublie sont remis à la fin, dans l'ordre initial."""
    from google.genai import types
    listing = "\n".join(f"[{docs[i]['id']}] {docs[i]['text']}" for i in candidates)
    prompt = (f"Question : {question}\n\nDocuments candidats :\n{listing}\n\n"
              "Classe les identifiants des documents du plus utile au moins utile pour répondre à la question. "
              "Un document qui contient l'identifiant exact cité dans la question (code d'erreur, paramètre) passe devant.")
    r = with_retry(lambda: client.models.generate_content(
        model=MODEL, contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=Ranking,
                                           thinking_config=types.ThinkingConfig(thinking_budget=0))))
    return merge_ranking(r.parsed.ids if r.parsed else [], docs, candidates)


def merge_ranking(llm_ids: list[str], docs: list[dict], candidates: list[int]) -> list[int]:
    by_id = {docs[i]["id"]: i for i in candidates}
    ranked = list(dict.fromkeys(by_id[x] for x in llm_ids if x in by_id))  # ignore les ids inventés, dédoublonne
    return ranked + [i for i in candidates if i not in ranked]


# ---------- L'index ----------
class HybridIndex:
    def __init__(self, docs: list[dict], doc_vecs: np.ndarray, client=None):
        self.docs, self.doc_vecs, self.client = docs, doc_vecs, client
        self.bm25 = BM25Okapi([tokenize(d["text"]) for d in docs])

    @classmethod
    def build(cls, docs: list[dict], client):
        """Calcule (ou relit dans .cache/) les embeddings du corpus."""
        key = hashlib.sha256(json.dumps([EMBED_MODEL, EMBED_DIM, docs]).encode()).hexdigest()[:16]
        cache = HERE / ".cache" / f"docs-{key}.npy"
        if cache.exists():
            vecs = np.load(cache)
        else:
            vecs = embed(client, [d["text"] for d in docs])
            cache.parent.mkdir(exist_ok=True)
            np.save(cache, vecs)
        return cls(docs, vecs, client)

    def search(self, question: str, mode: str = "rerank", k: int = 5, q_vec: np.ndarray | None = None) -> list[int]:
        """mode : bm25 | vector | hybrid | rerank."""
        if mode == "bm25":
            return bm25_search(self.bm25, question, k)
        if q_vec is None:
            q_vec = embed(self.client, [question])[0]
        if mode == "vector":
            return vector_search(self.doc_vecs, q_vec, k)
        fused = rrf([bm25_search(self.bm25, question, 20), vector_search(self.doc_vecs, q_vec, 20)])
        if mode == "hybrid":
            return fused[:k]
        return llm_rerank(self.client, question, self.docs, fused[:20])[:k]


def load_corpus() -> list[dict]:
    return [json.loads(line) for line in open(HERE / "corpus.jsonl", encoding="utf-8")]


def answer(index: HybridIndex, question: str) -> str:
    from google.genai import types
    hits = index.search(question, "rerank", k=5)
    context = "\n".join(f"[{index.docs[i]['id']}] {index.docs[i]['text']}" for i in hits)
    prompt = (f"Réponds en français, en 3 phrases maximum, uniquement à partir des documents ci-dessous, "
              f"et cite l'identifiant entre crochets de chaque document utilisé. Si la réponse n'y est pas, dis-le.\n\n"
              f"{context}\n\nQuestion : {question}")
    r = with_retry(lambda: index.client.models.generate_content(model=MODEL, contents=prompt))
    return r.text.strip()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Que signifie l'erreur HEL-6030 et comment la corriger ?"
    idx = HybridIndex.build(load_corpus(), gemini())
    print("Question :", q)
    print("Réponse  :", answer(idx, q))
