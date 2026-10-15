"""La synchro, identique pour toutes les sources : ce qui a disparu sort de l'index, ce qui est nouveau ou dont la
version a changé est (re)lu, découpé, vectorisé. Une passe à la fois ; une passe planifiée toutes les POLL_SECONDS
pour les sources en « auto » (Drive : l'API `changes` ne renvoie que ce qui a bougé, une passe sans changement est
quasi gratuite)."""

import os
import threading
import time
import traceback
from datetime import datetime, timezone

from parse import chunks, extract
from sources import load_sources, open_source

POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))


class Syncer:
    def __init__(self, store, embedder):
        self.store, self.embedder = store, embedder
        self.lock = threading.Lock()
        self.last = None  # dernier rapport
        self.running = False
        if store.get("embedder") != embedder.name:  # modèle d'embeddings changé : vecteurs incompatibles
            store.clear()
            store.set("embedder", embedder.name)

    def run(self, only: list[str] | None = None, auto_only: bool = False) -> dict:
        with self.lock:  # une passe à la fois ; les demandes suivantes attendent leur tour
            self.running = True
            try:
                return self._run(only, auto_only)
            finally:
                self.running = False

    def _run(self, only, auto_only) -> dict:
        t0 = time.time()
        report = {"debut": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "statut": "ok", "sources": [],
                  "erreurs": []}
        for src in load_sources():
            if (only and src["id"] not in only) or (auto_only and not src.get("auto", True)):
                continue
            stats = {"source": src.get("nom", src["id"]), "ajoutes": 0, "modifies": 0, "retires": 0, "inchanges": 0,
                     "echecs": 0}
            try:
                wanted = open_source(src).listing()
            except Exception as e:  # source illisible : on ne touche pas à ses documents
                report["erreurs"].append(f"{stats['source']} : {type(e).__name__} : {str(e)[:200]}")
                report["sources"].append(stats)
                continue
            present = {k.split(":", 1)[1]: v for k, v in self.store.versions(src["id"]).items()}
            for key in present.keys() - wanted.keys():
                self.store.delete(f"{src['id']}:{key}")
                stats["retires"] += 1
            reader = open_source(src)
            for key, meta in wanted.items():
                if present.get(key) == meta["version"]:
                    stats["inchanges"] += 1
                    continue
                try:
                    name, data = reader.fetch(key)
                    parts = chunks(extract(name, data))
                    vectors = self.embedder.documents(parts)
                    self.store.put(f"{src['id']}:{key}", src["id"], meta["title"], meta["link"], meta["version"],
                                   parts, vectors)
                    stats["modifies" if key in present else "ajoutes"] += 1
                except Exception as e:
                    stats["echecs"] += 1
                    report["erreurs"].append(f"« {meta['title']} » : {type(e).__name__} : {str(e)[:200]}")
            report["sources"].append(stats)
        if report["erreurs"]:
            report["statut"] = "avertissement"
        report["duree_s"] = round(time.time() - t0, 1)
        report["documents"] = len(self.store.documents())
        self.last = report
        return report

    def start_background(self) -> None:
        def loop():
            while True:
                time.sleep(POLL_SECONDS)
                try:
                    self.run(auto_only=True)
                except Exception:
                    traceback.print_exc()
        threading.Thread(target=loop, daemon=True, name="synchro").start()
