"""Logique du RAG local, sans réseau : découpage, recherche hybride, synchro d'un dossier (ajout, modification,
suppression). Un faux embedder (vecteurs déterministes) remplace le modèle : les tests restent instantanés."""
import hashlib
import importlib
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class FakeEmbedder:
    name = "faux"

    def _v(self, text):  # sac de mots haché : deux textes qui partagent des mots sont proches
        v = np.zeros(64, np.float32)
        for w in text.lower().split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 64] += 1
        return v

    def documents(self, texts):
        return np.array([self._v(t) for t in texts], np.float32)

    def query(self, text):
        return self._v(text)

    def rerank(self, q, hits, k):
        return hits[:k]


def fresh(tmp_path):
    os.environ["DATA_DIR"] = str(tmp_path / "data")
    import sources, store, sync
    for m in (sources, store, sync):
        importlib.reload(m)
    st = store.Store(str(tmp_path / "data" / "index.sqlite"))
    return sources, st, sync.Syncer(st, FakeEmbedder())


def test_chunks():
    from parse import chunks
    assert chunks("") == []
    assert chunks("Court.") == ["Court."]
    long = " ".join(f"Phrase numéro {i} assez longue pour remplir." for i in range(200))
    parts = chunks(long, size=500, overlap=100)
    assert len(parts) > 5 and all(len(p) <= 600 for p in parts)
    assert parts[0][-50:].split()[-1] in parts[1]  # recouvrement entre morceaux voisins


def test_sync_et_recherche(tmp_path):
    sources, st, syncer = fresh(tmp_path)
    folder = tmp_path / "docs"
    (folder / "rh").mkdir(parents=True)
    (folder / "teletravail.md").write_text("Chaque salarié a droit à trois jours de télétravail par semaine.")
    (folder / "rh" / "mutuelle.txt").write_text("Le contrat de mutuelle porte le numéro PEL-8826-NG.")
    (folder / "photo.png").write_bytes(b"\x89PNG")  # format non indexable : ignoré
    sources.save_sources([{"id": "depot", "type": "depot", "nom": "Dépôts", "auto": True},
                          {"id": "d1", "type": "dossier", "nom": "Docs", "chemin": str(folder), "auto": True}])

    r = syncer.run()
    d1 = next(s for s in r["sources"] if s["source"] == "Docs")
    assert d1["ajoutes"] == 2 and r["documents"] == 2, r

    hits = st.search("numéro de contrat mutuelle", FakeEmbedder().query("numéro de contrat mutuelle"))
    assert hits[0]["titre"] == "mutuelle.txt" and "PEL-8826-NG" in hits[0]["texte"]
    assert st.search("PEL-8826-NG", FakeEmbedder().query("PEL-8826-NG"))[0]["titre"] == "mutuelle.txt"  # mot exact (FTS)

    r = syncer.run()  # rien n'a changé
    assert next(s for s in r["sources"] if s["source"] == "Docs")["inchanges"] == 2

    time.sleep(0.01)
    (folder / "rh" / "mutuelle.txt").write_text("Le contrat de mutuelle porte désormais le numéro NEW-0001.")
    r = syncer.run()
    assert next(s for s in r["sources"] if s["source"] == "Docs")["modifies"] == 1
    assert "NEW-0001" in st.search("NEW-0001", FakeEmbedder().query("NEW-0001"))[0]["texte"]

    (folder / "teletravail.md").unlink()
    r = syncer.run()
    assert next(s for s in r["sources"] if s["source"] == "Docs")["retires"] == 1 and r["documents"] == 1


def test_source_illisible_ne_supprime_rien(tmp_path):
    sources, st, syncer = fresh(tmp_path)
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("Bonjour le monde.")
    sources.save_sources([{"id": "d1", "type": "dossier", "nom": "Docs", "chemin": str(folder), "auto": True}])
    syncer.run()
    folder.rename(tmp_path / "ailleurs")  # dossier disparu (disque débranché…)
    r = syncer.run()
    assert r["documents"] == 1 and r["erreurs"], r  # signalé, et l'index est gardé


def test_auto_desactive(tmp_path):
    sources, st, syncer = fresh(tmp_path)
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.txt").write_text("Bonjour le monde.")
    sources.save_sources([{"id": "d1", "type": "dossier", "nom": "Docs", "chemin": str(folder), "auto": False}])
    assert syncer.run(auto_only=True)["documents"] == 0  # passe planifiée : source ignorée
    assert syncer.run()["documents"] == 1  # « Synchroniser maintenant » : traitée


def test_chemin_hors_dossier_refuse(tmp_path):
    sources, st, syncer = fresh(tmp_path)
    src = sources.LocalFolder({"id": "d1", "type": "dossier", "chemin": str(tmp_path)})
    try:
        src.fetch("../../etc/passwd")
        assert False
    except PermissionError:
        pass
