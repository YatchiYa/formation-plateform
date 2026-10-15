"""L'index : un seul fichier SQLite. Documents, morceaux (« chunks »), vecteurs, et index plein texte FTS5.

Recherche hybride : mots-clés (BM25 de FTS5) + sens (cosinus sur les vecteurs), fusionnées par rang (RRF).
ponytail: cosinus en mémoire (numpy) sur tous les vecteurs : instantané jusqu'à ~100 000 morceaux ; au-delà, un index
ANN (sqlite-vec, Qdrant…).
"""

import sqlite3
import threading

import numpy as np

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS docs (
  id TEXT PRIMARY KEY,          -- « <source>:<clé> »
  source TEXT NOT NULL, title TEXT NOT NULL, link TEXT, version TEXT NOT NULL, indexed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
  id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES docs(id) ON DELETE CASCADE,
  ord INTEGER NOT NULL, text TEXT NOT NULL, emb BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS chunks_doc ON chunks(doc_id);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, content='chunks', content_rowid='id',
                                                        tokenize='unicode61 remove_diacritics 2');
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
  INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text); END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
  INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.id, old.text); END;
"""


class Store:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.executescript(SCHEMA)
        self.lock = threading.Lock()  # le serveur et la synchro écrivent depuis des fils différents
        self._cache = None  # (ids, matrice normalisée) pour la recherche vectorielle

    # --- méta (modèle d'embeddings, jetons de page Drive…) -------------------------------
    def get(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key: str, value: str) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, value))

    # --- documents --------------------------------------------------------------------
    def versions(self, source: str) -> dict:
        """{doc_id: version} des documents d'une source (pour savoir quoi réindexer)."""
        return dict(self.db.execute("SELECT id, version FROM docs WHERE source = ?", (source,)))

    def put(self, doc_id: str, source: str, title: str, link: str, version: str, chunks: list[str],
            vectors: np.ndarray) -> None:
        with self.lock, self.db:
            self.db.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
            self.db.execute("INSERT INTO docs VALUES (?, ?, ?, ?, ?, datetime('now'))",
                            (doc_id, source, title, link, version))
            self.db.executemany("INSERT INTO chunks (doc_id, ord, text, emb) VALUES (?, ?, ?, ?)",
                                [(doc_id, i, t, v.astype(np.float32).tobytes())
                                 for i, (t, v) in enumerate(zip(chunks, vectors))])
            self._cache = None

    def delete(self, doc_id: str) -> None:
        with self.lock, self.db:
            self.db.execute("DELETE FROM docs WHERE id = ?", (doc_id,))
            self._cache = None

    def delete_source(self, source: str) -> int:
        with self.lock, self.db:
            n = self.db.execute("DELETE FROM docs WHERE source = ?", (source,)).rowcount
            self._cache = None
        return n

    def clear(self) -> None:
        with self.lock, self.db:
            self.db.execute("DELETE FROM docs")
            self._cache = None

    def documents(self) -> list[dict]:
        rows = self.db.execute("SELECT d.id, d.source, d.title, d.link, d.indexed_at, COUNT(c.id) FROM docs d "
                               "LEFT JOIN chunks c ON c.doc_id = d.id GROUP BY d.id ORDER BY lower(d.title)")
        return [dict(zip(("id", "source", "titre", "lien", "indexe", "morceaux"), r)) for r in rows]

    # --- recherche ----------------------------------------------------------------------
    def _matrix(self):
        if self._cache is None:
            rows = self.db.execute("SELECT id, emb FROM chunks").fetchall()
            if not rows:
                self._cache = ([], np.zeros((0, 1), np.float32))
            else:
                m = np.stack([np.frombuffer(e, np.float32) for _, e in rows])
                m /= np.linalg.norm(m, axis=1, keepdims=True) + 1e-9
                self._cache = ([i for i, _ in rows], m)
        return self._cache

    def search(self, query: str, qvec: np.ndarray, k: int = 8, pool: int = 30) -> list[dict]:
        ids, m = self._matrix()
        ranks: dict[int, float] = {}
        if ids:
            q = qvec / (np.linalg.norm(qvec) + 1e-9)
            for r, i in enumerate(np.argsort(-(m @ q))[:pool]):
                ranks[ids[i]] = ranks.get(ids[i], 0) + 1 / (60 + r)  # RRF, k = 60
        terms = " OR ".join('"' + w.replace('"', "") + '"' for w in query.split() if len(w) > 1)
        if terms:
            for r, (cid,) in enumerate(self.db.execute(
                    "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?",
                    (terms, pool))):
                ranks[cid] = ranks.get(cid, 0) + 1 / (60 + r)
        best = sorted(ranks, key=ranks.get, reverse=True)[:k]
        if not best:
            return []
        q = f"SELECT c.id, c.text, d.title, d.link, d.source FROM chunks c JOIN docs d ON d.id = c.doc_id WHERE c.id IN ({','.join('?' * len(best))})"
        rows = {r[0]: r for r in self.db.execute(q, best)}
        return [{"texte": rows[i][1], "titre": rows[i][2], "lien": rows[i][3], "source": rows[i][4],
                 "score": round(ranks[i], 4)} for i in best if i in rows]
