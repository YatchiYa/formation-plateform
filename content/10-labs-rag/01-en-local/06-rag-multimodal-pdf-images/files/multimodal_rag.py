"""RAG multimodal sur un PDF : texte des pages + figures décrites par Gemini à l'indexation.

Usage : python multimodal_rag.py "Quelle a été la disponibilité en août ?"
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from pypdf import PdfReader

HERE = Path(__file__).parent
CACHE = HERE / ".cache"
load_dotenv(HERE / ".env")
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))
PDF = HERE / "rapport_verdalis_t3.pdf"

DESCRIBE_PROMPT = """Tu prépares l'indexation d'un rapport pour un moteur de recherche.
Décris cette figure en français, en texte brut :
1. son type (graphique en barres, courbe, tableau, schéma…) et son titre exact ;
2. TOUTES les valeurs lisibles, avec leur libellé et leur unité (une ligne par valeur) ;
3. pour un schéma : chaque élément et chaque liaison, dans l'ordre ;
4. en une phrase, ce que la figure permet de conclure (maximum, minimum, seuil dépassé…).
N'invente aucune valeur absente de l'image."""


def gemini():
    from google import genai
    return genai.Client()  # lit GOOGLE_API_KEY (ou GEMINI_API_KEY)


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
    from google.genai import types
    contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]  # un Content par texte = un vecteur par texte
    r = with_retry(lambda: client.models.embed_content(
        model=EMBED_MODEL, contents=contents, config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM)))
    v = np.array([e.values for e in r.embeddings], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


# ---------- 1. Extraction du PDF (sans réseau) ----------
def extract(pdf_path: Path = PDF) -> list[dict]:
    """Un chunk « texte » par page, et un chunk « figure » par image (l'image est enregistrée dans .cache/)."""
    CACHE.mkdir(exist_ok=True)
    chunks = []
    for n, page in enumerate(PdfReader(pdf_path).pages, start=1):
        chunks.append({"id": f"p{n}-texte", "page": n, "kind": "texte", "text": page.extract_text().strip()})
        for j, im in enumerate(page.images, start=1):
            path = CACHE / f"p{n}-figure{j}.png"
            im.image.save(path)
            chunks.append({"id": f"p{n}-figure{j}", "page": n, "kind": "figure", "image": str(path), "text": ""})
    return chunks


# ---------- 2. Description des figures par Gemini (mise en cache) ----------
def describe_figures(client, chunks: list[dict]) -> list[dict]:
    from google.genai import types
    cache_file = CACHE / "descriptions.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    for c in chunks:
        if c["kind"] != "figure":
            continue
        data = Path(c["image"]).read_bytes()
        key = hashlib.sha256((MODEL + DESCRIBE_PROMPT).encode() + data).hexdigest()[:16]
        if key not in cache:
            r = with_retry(lambda: client.models.generate_content(
                model=MODEL, contents=[types.Part.from_bytes(data=data, mime_type="image/png"), DESCRIBE_PROMPT]))
            cache[key] = r.text.strip()
        page_text = next(x["text"] for x in chunks if x["page"] == c["page"] and x["kind"] == "texte")
        # le titre de la page aide la recherche : on le préfixe à la description
        c["text"] = f"Figure de la page {c['page']} ({page_text.splitlines()[0]}).\n{cache[key]}"
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return chunks


# ---------- 3. Index et recherche ----------
class Index:
    def __init__(self, chunks: list[dict], vecs: np.ndarray, client=None):
        self.chunks, self.vecs, self.client = chunks, vecs, client

    @classmethod
    def build(cls, client, pdf_path: Path = PDF):
        chunks = describe_figures(client, extract(pdf_path))
        return cls(chunks, embed(client, [c["text"] for c in chunks]), client)

    def search(self, q_vec: np.ndarray, k: int = 3, mode: str = "page") -> list[dict]:
        """mode « texte »      : on ignore les figures (RAG classique sur le texte extrait du PDF) ;
        mode « multimodal » : texte + descriptions de figures, top k ;
        mode « page »       : idem, puis on ajoute les figures des pages retrouvées (expansion par page)."""
        allowed = [i for i, c in enumerate(self.chunks) if mode != "texte" or c["kind"] == "texte"]
        scores = self.vecs[allowed] @ q_vec
        hits = [self.chunks[allowed[i]] for i in np.argsort(-scores)[:k]]
        if mode == "page":
            pages = {h["page"] for h in hits}
            hits += [c for c in self.chunks if c["kind"] == "figure" and c["page"] in pages and c not in hits]
        return hits


def build_contents(question: str, hits: list[dict]) -> list:
    """Contexte envoyé au modèle : le texte des chunks, et pour une figure, l'IMAGE elle-même en plus de sa description."""
    from google.genai import types
    parts = ["Réponds en français, en 2 phrases maximum, uniquement à partir des extraits et des images ci-dessous. "
             "Cite l'identifiant entre crochets de chaque extrait utilisé. Si l'information n'y est pas, dis-le."]
    for h in hits:
        parts.append(f"\n[{h['id']}]\n{h['text']}")
        if h["kind"] == "figure":
            parts.append(types.Part.from_bytes(data=Path(h["image"]).read_bytes(), mime_type="image/png"))
    parts.append(f"\nQuestion : {question}")
    return parts


def answer(index: Index, question: str, q_vec=None, mode: str = "page") -> tuple[str, list[dict]]:
    if q_vec is None:
        q_vec = embed(index.client, [question])[0]
    hits = index.search(q_vec, 3, mode)
    r = with_retry(lambda: index.client.models.generate_content(model=MODEL, contents=build_contents(question, hits)))
    return (r.text or "").strip(), hits


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Quelle a été la disponibilité des chambres froides en août ?"
    idx = Index.build(gemini())
    for mode in ("texte", "page"):
        text, hits = answer(idx, q, mode=mode)
        print(f"[{mode}] sources={[h['id'] for h in hits]}\n  {text}")
