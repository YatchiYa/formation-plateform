"""Embeddings et reranking : Voyage AI si une clé est fournie (VOYAGE_API_KEY), sinon un modèle local (fastembed)."""

import os

import numpy as np

VOYAGE_MODEL = os.getenv("VOYAGE_MODEL", "voyage-4")
RERANK_MODEL = os.getenv("RERANK_MODEL", "rerank-2.5")
LOCAL_MODEL = os.getenv("LOCAL_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


class Embedder:
    """`name` identifie le modèle : s'il change, tout l'index doit être recalculé (vecteurs incompatibles)."""

    def __init__(self, mode: str = os.getenv("EMBEDDINGS", "auto")):
        if mode == "auto":
            mode = "voyage" if os.getenv("VOYAGE_API_KEY") else "local"
        self.mode = mode
        if mode == "voyage":
            import voyageai
            self.client = voyageai.Client(max_retries=3)  # lit VOYAGE_API_KEY
            self.name = f"voyage:{VOYAGE_MODEL}"
        elif mode == "local":
            from fastembed import TextEmbedding
            self.model = TextEmbedding(LOCAL_MODEL, cache_dir=os.getenv("MODELS_DIR"))
            self.name = f"local:{LOCAL_MODEL}"
        else:
            raise ValueError(f"EMBEDDINGS={mode!r} : « auto », « voyage » ou « local »")

    def documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1), np.float32)
        if self.mode == "voyage":
            out = []
            for i in range(0, len(texts), 128):  # lots raisonnables par requête
                out += self.client.embed(texts[i:i + 128], model=VOYAGE_MODEL, input_type="document").embeddings
            return np.array(out, np.float32)
        return np.array(list(self.model.embed(texts, batch_size=32)), np.float32)

    def query(self, text: str) -> np.ndarray:
        if self.mode == "voyage":
            return np.array(self.client.embed([text], model=VOYAGE_MODEL, input_type="query").embeddings[0], np.float32)
        return np.array(next(iter(self.model.query_embed(text))), np.float32)

    def rerank(self, query: str, hits: list[dict], k: int) -> list[dict]:
        """Second tri des extraits (Voyage seulement) ; en local, l'ordre de la recherche hybride est gardé."""
        if self.mode != "voyage" or len(hits) <= 1:
            return hits[:k]
        r = self.client.rerank(query, [h["texte"] for h in hits], model=RERANK_MODEL, top_k=k)
        return [hits[x.index] for x in r.results]
