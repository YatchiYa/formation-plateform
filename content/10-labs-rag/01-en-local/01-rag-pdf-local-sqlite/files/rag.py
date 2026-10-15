"""RAG minimal sur des PDF : pypdf -> découpage -> embeddings Gemini -> SQLite + numpy -> réponse citée.

Usage :
  python rag.py index docs                       # (ré)indexe le dossier, incrémental
  python rag.py ask "Combien de jours de télétravail ?"
"""
import hashlib
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
DIM = int(os.environ.get("EMBED_DIM", "768"))
DB_PATH = os.environ.get("DB_PATH", "index.db")
REFUS = "Je ne sais pas"

_client = None


def client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client()  # lit GOOGLE_API_KEY (ou GEMINI_API_KEY)
    return _client


def retry(fn, tries=5):
    """Réessaie sur 429 (quota) / 500 / 503 (surcharge) avec attente exponentielle."""
    from google.genai import errors
    for i in range(tries):
        try:
            return fn()
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == tries - 1:
                raise
            time.sleep(2 ** i * 2)


# --- Modèles (remplaçables par des faux dans les tests) ---------------------

def embed(texts: list[str], kind: str = "doc", titles: list[str] | None = None) -> np.ndarray:
    """Un vecteur par texte. gemini-embedding-2 n'a pas de task_type : la tâche va dans le texte."""
    from google.genai import types
    if kind == "query":
        texts = [f"task: question answering | query: {t}" for t in texts]
    else:
        titles = titles or ["none"] * len(texts)
        texts = [f"title: {ti} | text: {t}" for ti, t in zip(titles, texts)]
    out = []
    for i in range(0, len(texts), 100):  # 100 textes par requête au plus
        batch = [types.Content(parts=[types.Part(text=t)]) for t in texts[i:i + 100]]
        r = retry(lambda: client().models.embed_content(
            model=EMBED_MODEL, contents=batch,
            config=types.EmbedContentConfig(output_dimensionality=DIM)))
        out += [e.values for e in r.embeddings]
    v = np.array(out, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def generate(prompt: str, model: str = MODEL) -> str:
    return retry(lambda: client().models.generate_content(model=model, contents=prompt)).text.strip()


# --- Extraction et découpage -----------------------------------------------

def read_pdf(path: Path) -> list[tuple[int, str]]:
    """[(numéro de page à partir de 1, texte)] ; les pages vides sont ignorées."""
    pages = []
    for i, page in enumerate(PdfReader(path).pages, start=1):
        text = " ".join((page.extract_text() or "").split())
        if text:
            pages.append((i, text))
    return pages


def chunk(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    """Morceaux d'environ `size` caractères, coupés sur une fin de phrase, avec chevauchement."""
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind(". ", start + size // 2, end)
            end = cut + 1 if cut != -1 else end
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


# --- Index SQLite -----------------------------------------------------------

def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    db = sqlite3.connect(db_path)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY, path TEXT NOT NULL, page INTEGER NOT NULL,
            text TEXT NOT NULL, vec BLOB NOT NULL);
        CREATE INDEX IF NOT EXISTS chunks_path ON chunks(path);
    """)
    return db


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_folder(db, folder: str, embed_fn=embed) -> dict:
    """Indexe les PDF nouveaux ou modifiés, oublie les PDF supprimés. Renvoie des compteurs."""
    stats = {"ajoutes": 0, "modifies": 0, "inchanges": 0, "supprimes": 0, "morceaux": 0}
    known = dict(db.execute("SELECT path, sha256 FROM files"))
    seen = set()
    for pdf in sorted(Path(folder).glob("*.pdf")):
        key, digest = pdf.name, sha256(pdf)
        seen.add(key)
        if known.get(key) == digest:
            stats["inchanges"] += 1
            continue
        stats["modifies" if key in known else "ajoutes"] += 1
        rows = [(page, c) for page, text in read_pdf(pdf) for c in chunk(text)]
        vecs = embed_fn([c for _, c in rows], kind="doc", titles=[key] * len(rows)) if rows else []
        with db:  # une transaction par fichier : jamais d'index à moitié écrit
            db.execute("DELETE FROM chunks WHERE path = ?", (key,))
            db.executemany("INSERT INTO chunks(path, page, text, vec) VALUES (?, ?, ?, ?)",
                           [(key, p, c, v.astype(np.float32).tobytes()) for (p, c), v in zip(rows, vecs)])
            db.execute("INSERT OR REPLACE INTO files VALUES (?, ?)", (key, digest))
        stats["morceaux"] += len(rows)
    for gone in set(known) - seen:
        with db:
            db.execute("DELETE FROM chunks WHERE path = ?", (gone,))
            db.execute("DELETE FROM files WHERE path = ?", (gone,))
        stats["supprimes"] += 1
    return stats


def search(db, question: str, k: int = 4, embed_fn=embed) -> list[dict]:
    """Similarité cosinus (produit scalaire de vecteurs normés) sur tous les morceaux."""
    # Limite connue : parcours complet en numpy, suffisant jusqu'à ~100 000 morceaux ; au-delà, index ANN (sqlite-vec, FAISS).
    rows = db.execute("SELECT path, page, text, vec FROM chunks").fetchall()
    if not rows:
        return []
    mat = np.stack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
    scores = mat @ embed_fn([question], kind="query")[0]
    best = np.argsort(-scores)[:k]
    return [{"path": rows[i][0], "page": rows[i][1], "text": rows[i][2], "score": float(scores[i])}
            for i in best]


PROMPT = """Tu es l'assistant documentaire d'Atelier Nova. Réponds en français, en 1 à 3 phrases,
UNIQUEMENT à partir des extraits ci-dessous. Après chaque affirmation, cite la source au format
[fichier.pdf p. N]. Si les extraits ne contiennent pas la réponse, réponds exactement : "{refus}".

Extraits :
{context}

Question : {question}"""


def answer(db, question: str, k: int = 4, embed_fn=embed, generate_fn=generate) -> dict:
    hits = search(db, question, k, embed_fn)
    context = "\n\n".join(f"[{h['path']} p. {h['page']}] {h['text']}" for h in hits)
    text = generate_fn(PROMPT.format(refus=REFUS, context=context, question=question))
    return {"question": question, "answer": text, "hits": hits, "refus": text.startswith(REFUS)}


if __name__ == "__main__":
    cmd, arg = sys.argv[1], sys.argv[2]
    db = connect()
    if cmd == "index":
        print(index_folder(db, arg))
    elif cmd == "ask":
        r = answer(db, arg)
        print(r["answer"])
        for h in r["hits"]:
            print(f"  - {h['path']} p. {h['page']} (score {h['score']:.3f})")
