"""Tests sans clé d'API : faux embeddings et faux modèle."""
import hashlib

import numpy as np
import pytest

import code_rag as cr
import eval as ev
import make_project


def fake_embed(texts, kind="doc", titles=None):
    v = np.zeros((len(texts), 512), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in cr.tokens(t):
            v[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


@pytest.fixture
def db(tmp_path):
    make_project.build(tmp_path / "p")
    d = cr.connect(str(tmp_path / "t.db"))
    cr.index_folder(d, tmp_path / "p", fake_embed)
    return d


def test_le_projet_fictif_a_16_fichiers_valides(tmp_path):
    paths = make_project.build(tmp_path / "p")
    assert len(paths) == 16
    for p in paths:
        compile(p.read_text(), str(p), "exec")


def test_chunk_python_fonctions_methodes_classes_constantes():
    src = make_project.FICHIERS["facturo/models.py"]
    by_name = {c["name"]: c for c in cr.chunk_python("facturo/models.py", src)}
    assert by_name["Facture"]["kind"] == "classe" and "def total_ttc(self): ..." in by_name["Facture"]["text"]
    m = by_name["Facture.total_ttc"]
    assert m["kind"] == "methode" and src.splitlines()[m["start"] - 1].strip().startswith("def total_ttc")
    assert src.splitlines()[m["end"] - 1].strip().startswith("return")
    tva = {c["name"]: c for c in cr.chunk_python("facturo/tva.py", make_project.FICHIERS["facturo/tva.py"])}
    assert tva["TAUX_TVA"]["kind"] == "constante" and "module" not in {c["kind"] for c in tva.values()}
    assert cr.titre(tva["calcul_tva"]) == "facturo/tva.py (Taux et calcul de la TVA.) fonction calcul_tva"


def test_decorateur_inclus_dans_le_morceau():
    src = "import functools\n\n\n@functools.cache\ndef f(x):\n    return x\n"
    (c,) = [c for c in cr.chunk_python("m.py", src) if c["name"] == "f"]
    assert c["start"] == 4 and c["text"].startswith("@functools.cache")


def test_tokens_decoupe_les_identifiants():
    assert cr.tokens("planifier_relances DepotFactures") == ["planifier", "relances", "depot", "factures"]
    assert cr.tokens("la numérotation") == cr.tokens("numerotation.py")[:1] == ["numerotation"]


def test_index_incremental(db, tmp_path):
    assert cr.index_folder(db, tmp_path / "p", fake_embed)["inchanges"] == 16
    (tmp_path / "p" / "facturo" / "devises.py").unlink()
    assert cr.index_folder(db, tmp_path / "p", fake_embed)["supprimes"] == 1


def test_bm25_trouve_un_identifiant(db):
    hits = cr.search(db, "PALIERS_RELANCE", 3, mode="bm25")
    assert any(h["name"] == "PALIERS_RELANCE" for h in hits)


def test_ou_est_gere_renvoie_fichier_ligne(db):
    out = cr.ou_est_gere(db, "relances factures impayées retard", embed_fn=fake_embed)
    assert any(o.startswith("facturo/relances.py:") for o in out[:3])


def test_citations_et_liens():
    hits = [{"path": "facturo/tva.py", "start": 6, "end": 10}]
    assert cr.citations_valides("Voir facturo/tva.py:8.", hits)
    assert not cr.citations_valides("Voir facturo/tva.py:30.", hits)    # hors de l'extrait
    assert not cr.citations_valides("La TVA est calculée.", hits)       # aucune citation
    assert cr.citations_valides("Je ne sais pas", [])
    assert not cr.citations_valides("Voir facturo/tva.py:8-12.", hits)  # la plage déborde
    assert cr.liens("cf. facturo/tva.py:8") == "cf. [facturo/tva.py:8](projet_demo/facturo/tva.py#L8)"
    assert cr.liens("cf. `facturo/tva.py:6-10`") == "cf. [facturo/tva.py:6-10](projet_demo/facturo/tva.py#L6-L10)"
    assert cr.liens("`facturo/tva.py:3-3`") == "[facturo/tva.py:3](projet_demo/facturo/tva.py#L3)"


def test_answer_rejette_une_citation_inventee(db):
    r = cr.answer(db, "taux de TVA", 3, fake_embed, lambda p: "Dans facturo/inexistant.py:3.")
    assert r["refus"] and not r["citations_ok"]


def test_metriques():
    hits = [{"path": "a.py", "name": "f"}]
    assert ev.recall(hits, ["a.py::f", "a.py::g"]) == 0.5
    golden = [{"attendu": ["a.py::f"]}, {"attendu": []}]
    rows = [{"refus": False, "brut": "x", "hits": hits, "citations_ok": True},
            {"refus": True, "brut": "Je ne sais pas", "hits": [], "citations_ok": True}]
    assert ev.complet(golden, rows, lambda a, h: True) == {
        "fidelite": 1.0, "citations_valides": 1.0, "refus_corrects": 1.0, "faux_refus": 0.0}
