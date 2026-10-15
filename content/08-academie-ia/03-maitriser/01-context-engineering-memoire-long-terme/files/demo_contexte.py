"""Mesures sur le contexte long : document entier vs RAG, cache implicite, cache explicite.

Usage : python demo_contexte.py
Tout ce qui est créé (le cache explicite) est supprimé à la fin, même en cas d'erreur."""
import os
import time

from dotenv import load_dotenv
from rank_bm25 import BM25Okapi

import catalogue
from memoire import with_retry

load_dotenv()
MODEL = os.getenv("MODEL", "gemini-3.5-flash")
QUESTION = "Quel est le prix et l'entrepôt d'expédition de la référence AT-1137 ? Et la livraison express est-elle possible ?"


def bm25_top(chunks: list[str], query: str, k: int = 3) -> list[str]:
    """Recherche lexicale : idéale pour des identifiants exacts comme « AT-1137 »."""
    tok = lambda s: s.lower().replace(":", " ").replace(".", " ").split()
    scores = BM25Okapi([tok(c) for c in chunks]).get_scores(tok(query))
    return [chunks[i] for i in sorted(range(len(chunks)), key=lambda i: -scores[i])[:k]]


def ask(c, contents, **cfg):
    t = time.time()
    r = with_retry(lambda: c.models.generate_content(model=MODEL, contents=contents, config=cfg or None))
    u = r.usage_metadata
    return {"s": round(time.time() - t, 2), "in": u.prompt_token_count,
            "cached": u.cached_content_token_count or 0, "out": u.candidates_token_count, "text": r.text.strip()}


def show(label, res):
    print(f"{label:<28} {res['s']:>5} s | entrée {res['in']:>5} (dont cache {res['cached']:>5}) | "
          f"sortie {res['out']:>4} | {res['text'][:120]!r}")


def main():
    from google import genai
    from google.genai import types
    c = genai.Client()
    doc = catalogue.document()
    head = doc.split("## Produits")[0]  # les conditions générales, toujours utiles
    print(f"Document : {len(doc)} caractères, {c.models.count_tokens(model=MODEL, contents=doc).total_tokens} tokens\n")

    # 1. Document entier vs RAG : même question, contexte très différent
    show("document entier", ask(c, f"{doc}\n\nQuestion : {QUESTION}"))
    passages = "\n".join(bm25_top(catalogue.chunks(), QUESTION))
    show("RAG (BM25, 3 passages)", ask(c, f"{head}\n{passages}\n\nQuestion : {QUESTION}"))

    # 2. Cache implicite : même long préfixe, envoyé deux fois de suite
    for i in (1, 2):
        show(f"implicite, appel {i}", ask(c, f"{doc}\n\nQuestion : prix de AT-1050 ?"))

    # 3. Cache explicite : on paie le stockage du préfixe pendant le TTL, on le réutilise par son nom
    cache = c.caches.create(model=MODEL, config=types.CreateCachedContentConfig(
        display_name="lab-context-engineering", contents=[doc], ttl="300s",
        system_instruction="Tu réponds uniquement à partir du catalogue fourni, en une phrase."))
    try:
        print(f"\ncache créé : {cache.usage_metadata.total_token_count} tokens, expire {cache.expire_time:%H:%M:%S} UTC")
        for q in [QUESTION, "Quelle est la garantie de la référence AT-1050 ?"]:
            show("explicite", ask(c, q, cached_content=cache.name))
    finally:
        c.caches.delete(name=cache.name)
        left = [x.name for x in c.caches.list() if x.display_name == "lab-context-engineering"]
        print("cache supprimé ; caches restants du lab :", left)


if __name__ == "__main__":
    main()
