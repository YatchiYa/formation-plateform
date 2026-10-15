"""Mémoire long terme : faits extraits par un LLM, stockés dans SQLite avec leur embedding,
rappelés par similarité. Une seule table, aucune base vectorielle à installer."""
import os
import sqlite3
import time

import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-2")
EXTRACT_MODEL = os.getenv("EXTRACT_MODEL", "gemini-3.5-flash-lite")
DIM = int(os.getenv("EMBED_DIM", "768"))  # gemini-embedding-2 : 3072 dims par défaut, réductible


def with_retry(fn, tries=6):
    """Réessaie sur 429 (quota) et 5xx, avec attente croissante."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            if getattr(e, "code", None) not in (429, 500, 503) or i == tries - 1:
                raise
            time.sleep(2 ** i * 3)


def gemini_embedder(c):
    """Renvoie embed(text, kind) -> vecteur normalisé. Préfixes asymétriques recommandés pour
    gemini-embedding-2 (une requête ne se formule pas comme un fait stocké)."""
    from google.genai import types

    def embed(text: str, kind: str = "doc") -> np.ndarray:
        prompt = f"task: question answering | query: {text}" if kind == "query" else f"title: none | text: {text}"
        # Un contenu par appel : gemini-embedding-2 agrège une liste en UN seul vecteur
        # (API Gemini) ou la refuse (Vertex AI).
        r = with_retry(lambda: c.models.embed_content(
            model=EMBED_MODEL, contents=prompt, config=types.EmbedContentConfig(output_dimensionality=DIM)))
        v = np.array(r.embeddings[0].values, dtype=np.float32)
        return v / np.linalg.norm(v)  # normalisé : produit scalaire = similarité cosinus
    return embed


class Memory:
    def __init__(self, path: str, embed):
        self.db = sqlite3.connect(path)
        self.embed = embed
        self.db.execute("""CREATE TABLE IF NOT EXISTS facts (
            id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, text TEXT NOT NULL,
            vec BLOB NOT NULL, updated_at REAL NOT NULL)""")
        self.db.execute("CREATE INDEX IF NOT EXISTS facts_user ON facts(user_id)")
        # Journal : un remplacement ou une suppression ne perd jamais l'ancienne version
        # (un LLM d'extraction peut remplacer le mauvais fait : on doit pouvoir le voir et le restaurer).
        self.db.execute("""CREATE TABLE IF NOT EXISTS facts_history (
            fact_id INTEGER, user_id TEXT, old_text TEXT, op TEXT, at REAL)""")

    def _archive(self, user: str, fact_id: int, op: str):
        self.db.execute("INSERT INTO facts_history SELECT id, user_id, text, ?, ? FROM facts WHERE id=? AND user_id=?",
                        (op, time.time(), fact_id, user))

    def add(self, user: str, text: str) -> int:
        cur = self.db.execute("INSERT INTO facts(user_id, text, vec, updated_at) VALUES (?,?,?,?)",
                              (user, text, self.embed(text).tobytes(), time.time()))
        self.db.commit()
        return cur.lastrowid

    def replace(self, user: str, fact_id: int, text: str):
        # le filtre user_id empêche un utilisateur de modifier les faits d'un autre
        self._archive(user, fact_id, "remplacer")
        self.db.execute("UPDATE facts SET text=?, vec=?, updated_at=? WHERE id=? AND user_id=?",
                        (text, self.embed(text).tobytes(), time.time(), fact_id, user))
        self.db.commit()

    def delete(self, user: str, fact_id: int):
        self._archive(user, fact_id, "supprimer")
        self.db.execute("DELETE FROM facts WHERE id=? AND user_id=?", (fact_id, user))
        self.db.commit()

    def history(self, user: str) -> list[tuple[int, str, str]]:
        return self.db.execute("SELECT fact_id, old_text, op FROM facts_history WHERE user_id=? ORDER BY at",
                               (user,)).fetchall()

    def all(self, user: str) -> list[tuple[int, str]]:
        return self.db.execute("SELECT id, text FROM facts WHERE user_id=? ORDER BY id", (user,)).fetchall()

    def recall(self, user: str, query: str, k: int = 4) -> list[tuple[float, int, str]]:
        """Les k faits de CET utilisateur les plus proches de la requête : (score, id, texte)."""
        rows = self.db.execute("SELECT id, text, vec FROM facts WHERE user_id=?", (user,)).fetchall()
        if not rows:
            return []
        # Limite connue : scan complet en numpy, suffisant jusqu'à quelques dizaines de milliers de faits
        # par utilisateur ; au-delà, index vectoriel (sqlite-vec, pgvector, Vector Search).
        m = np.frombuffer(b"".join(r[2] for r in rows), dtype=np.float32).reshape(len(rows), -1)
        scores = m @ self.embed(query, "query")
        best = np.argsort(-scores)[:k]
        return [(float(scores[i]), rows[i][0], rows[i][1]) for i in best]


# ---------- Extraction des faits par le LLM ----------
class Remplacement(BaseModel):
    id: int
    texte: str


class Operations(BaseModel):
    ajouter: list[str]
    remplacer: list[Remplacement]
    supprimer: list[int]


EXTRACT_PROMPT = """Tu gères la mémoire long terme d'un assistant.
Lis le dernier message de l'utilisateur et décide quels FAITS DURABLES retenir sur lui :
identité, préférences, contraintes (santé, disponibilités), contexte de travail, outils.
Ignore les demandes ponctuelles, les questions et les politesses.
Chaque fait : une phrase courte, autonome, à la 3e personne (« L'utilisateur ... »).
Si le message met à jour ou contredit un fait connu, utilise « remplacer » avec son id ;
s'il l'annule sans le remplacer, « supprimer ». Ne duplique pas un fait déjà connu.

Faits déjà connus (id : texte) :
{known}

Dernier message de l'utilisateur :
{message}"""


def extract_operations(c, message: str, known: list[tuple[int, str]]) -> Operations:
    known_txt = "\n".join(f"{i} : {t}" for i, t in known) or "(aucun)"
    cfg = {"response_mime_type": "application/json", "response_schema": Operations}
    r = with_retry(lambda: c.models.generate_content(
        model=EXTRACT_MODEL, contents=EXTRACT_PROMPT.format(known=known_txt, message=message), config=cfg))
    return Operations.model_validate_json(r.text)


def apply_operations(mem: Memory, user: str, ops: Operations, allowed_ids: set[int]) -> dict:
    """N'applique un remplacement/une suppression qu'aux faits montrés au LLM (allowed_ids)."""
    done = {"ajoutés": [], "remplacés": [], "supprimés": []}
    for r in ops.remplacer:
        if r.id in allowed_ids:
            mem.replace(user, r.id, r.texte)
            done["remplacés"].append(r.texte)
    for i in ops.supprimer:
        if i in allowed_ids:
            mem.delete(user, i)
            done["supprimés"].append(i)
    for t in ops.ajouter:
        done["ajoutés"].append(t)
        mem.add(user, t)
    return done
