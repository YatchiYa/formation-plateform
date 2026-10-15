"""Tests sans clé d'API : faux embeddings (sac de mots haché) et faux modèle."""
import hashlib

import numpy as np
import pytest

import eval as ev
import make_pdfs
import rag


def fake_embed(texts, kind="doc", titles=None):
    v = np.zeros((len(texts), 256), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in t.lower().replace("?", " ").replace(".", " ").split():
            v[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 256] += 1
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


@pytest.fixture
def setup(tmp_path):
    docs = tmp_path / "docs"
    make_pdfs.build(docs)
    return rag.connect(str(tmp_path / "t.db")), docs


def test_chunk_respecte_la_taille_et_couvre_le_texte():
    text = "Une phrase courte. " * 100
    parts = rag.chunk(text, size=200, overlap=40)
    assert all(len(p) <= 200 for p in parts)
    assert parts[0].startswith("Une phrase") and parts[-1].endswith("courte.")
    assert rag.chunk("court") == ["court"]


def test_extraction_garde_les_numeros_de_page(setup):
    _, docs = setup
    pages = rag.read_pdf(docs / "notes-de-frais.pdf")
    assert [p for p, _ in pages] == [1, 2, 3]
    assert "120 euros" in pages[1][1]


def test_reindexation_incrementale(setup):
    db, docs = setup
    s1 = rag.index_folder(db, docs, fake_embed)
    assert s1["ajoutes"] == 3 and s1["morceaux"] > 0
    s2 = rag.index_folder(db, docs, fake_embed)
    assert s2 == {"ajoutes": 0, "modifies": 0, "inchanges": 3, "supprimes": 0, "morceaux": 0}
    make_pdfs.DOCS["guide-accueil.pdf"][0][1].append("Nouveau : une salle de sport ouvre au 3e étage.")
    make_pdfs.build(docs)
    (docs / "notes-de-frais.pdf").unlink()
    s3 = rag.index_folder(db, docs, fake_embed)
    assert s3["modifies"] == 1 and s3["supprimes"] == 1 and s3["inchanges"] == 1
    assert db.execute("SELECT COUNT(*) FROM chunks WHERE path='notes-de-frais.pdf'").fetchone()[0] == 0
    make_pdfs.DOCS["guide-accueil.pdf"][0][1].pop()


def test_recherche_et_reponse_citee(setup):
    db, docs = setup
    rag.index_folder(db, docs, fake_embed)
    hits = rag.search(db, "plafond hôtel nuit Paris", 2, fake_embed)
    assert hits[0]["path"] == "notes-de-frais.pdf" and hits[0]["page"] == 2
    seen = {}
    fake_gen = lambda prompt, **kw: seen.setdefault("p", prompt) and "120 euros [notes-de-frais.pdf p. 2]"
    r = rag.answer(db, "plafond hôtel nuit Paris", 2, fake_embed, fake_gen)
    assert "[notes-de-frais.pdf p. 2]" in seen["p"] and not r["refus"]


def test_metriques():
    hits = [{"path": "a.pdf", "page": 1}, {"path": "b.pdf", "page": 2}]
    assert ev.recall_at_k(hits, ["a.pdf#1", "c.pdf#1"]) == 0.5
    golden = [{"question": "q1", "attendu": ["a.pdf#1"]}, {"question": "hors", "attendu": []}]
    answers = {"q1": {"answer": "x", "hits": hits, "refus": False},
               "hors": {"answer": rag.REFUS, "hits": hits, "refus": True}}
    res = ev.evaluate(None, golden, 2, lambda db, q, k: answers[q], lambda a, h: True)
    assert (res["rappel@1"], res["fidelite"], res["refus_corrects"], res["faux_refus"]) == (1.0, 1.0, 1.0, 0.0)
