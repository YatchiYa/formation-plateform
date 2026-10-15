"""Tests sans clé d'API : génération du PDF, extraction, description (faux client), recherche, contexte. pytest -q"""
from types import SimpleNamespace

import numpy as np

import make_pdf
import multimodal_rag as mr
from evaluate import is_correct


class FakeClient:
    """Imite client.models.generate_content : renvoie une description fixe et compte les appels."""
    def __init__(self):
        self.calls = 0
        self.models = self

    def generate_content(self, model, contents):
        self.calls += 1
        return SimpleNamespace(text="Graphique en barres. Lyon : 412 MWh")


def test_pdf_genere_texte_et_figures(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "CACHE", tmp_path / ".cache")
    pdf = make_pdf.build(tmp_path / "r.pdf")
    chunks = mr.extract(pdf)
    assert [c["id"] for c in chunks if c["kind"] == "figure"] == ["p2-figure1", "p3-figure1", "p4-figure1", "p5-figure1"]
    page2 = next(c for c in chunks if c["id"] == "p2-texte")["text"]
    assert "figure 1" in page2 and "412" not in page2  # la valeur n'existe QUE dans l'image


def test_descriptions_mises_en_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(mr, "CACHE", tmp_path / ".cache")
    chunks = mr.extract(make_pdf.build(tmp_path / "r.pdf"))
    fake = FakeClient()
    mr.describe_figures(fake, chunks)
    assert fake.calls == 4
    fig = next(c for c in chunks if c["id"] == "p2-figure1")
    assert fig["text"].startswith("Figure de la page 2 (2. Consommation énergétique)") and "412" in fig["text"]
    mr.describe_figures(fake, mr.extract(tmp_path / "r.pdf"))
    assert fake.calls == 4  # 2e passage : tout vient du cache


def _index():
    chunks = [{"id": "p1-texte", "page": 1, "kind": "texte", "text": "a"},
              {"id": "p2-texte", "page": 2, "kind": "texte", "text": "b"},
              {"id": "p2-figure1", "page": 2, "kind": "figure", "text": "c", "image": ""}]
    vecs = np.array([[1, 0, 0], [0.6, 0.8, 0], [0, 0, 1]], dtype=np.float32)
    return mr.Index(chunks, vecs)


def test_modes_de_recherche():
    idx, q = _index(), np.array([0, 0.6, 0.8], dtype=np.float32)
    assert [h["id"] for h in idx.search(q, 1, "texte")] == ["p2-texte"]
    assert [h["id"] for h in idx.search(q, 1, "multimodal")] == ["p2-figure1"]
    q2 = np.array([0, 1, 0], dtype=np.float32)  # proche du texte de la page 2 seulement
    assert [h["id"] for h in idx.search(q2, 1, "page")] == ["p2-texte", "p2-figure1"]


def test_contexte_joint_l_image(tmp_path):
    img = tmp_path / "f.png"
    img.write_bytes(b"\x89PNG fake")
    parts = mr.build_contents("Q ?", [{"id": "p2-figure1", "kind": "figure", "text": "desc", "image": str(img)}])
    assert any(getattr(p, "inline_data", None) is not None for p in parts)
    assert parts[-1].endswith("Q ?")


def test_normalisation_des_reponses():
    assert is_correct("Le taux était de 96,8 % en août", ["96.8"])
    assert is_correct("12 000 palettes", ["12000"])
    assert is_correct("En Août", ["aout"]) and not is_correct("en juillet", ["août"])
