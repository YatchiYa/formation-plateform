"""Tests sans clé ni GCP : bucket simulé, modèle de vision simulé. Lancer : pytest -q"""
import io

from PIL import Image

import agent
import generer_images
from lancer import evaluer


class FauxBlob:
    def __init__(self, store, name):
        self.store, self.name = store, name

    def download_as_bytes(self):
        return self.store[self.name]

    def upload_from_string(self, data, content_type=None):
        self.store[self.name] = data


class FauxBucket:
    def __init__(self):
        self.store = {}

    def blob(self, name):
        return FauxBlob(self.store, name)

    def list_blobs(self, prefix=""):
        return [FauxBlob(self.store, n) for n in sorted(self.store) if n.startswith(prefix)]


def test_images_generees(tmp_path):
    pieces = generer_images.generer(tmp_path / "images")
    assert set(pieces.values()) == set(agent.DEFAUTS)
    img = Image.open(tmp_path / "images" / "piece-01.png")
    assert img.size == (512, 512)
    assert (tmp_path / "verite_terrain.json").exists()


def test_parcours_complet_avec_faux_bucket(monkeypatch, tmp_path):
    bucket = FauxBucket()
    for nom, defaut in [("piece-01.png", "aucun"), ("piece-02.png", "fissure")]:
        buf = io.BytesIO()
        generer_images.dessiner_piece(defaut, 0).save(buf, "PNG")
        bucket.store[f"images/{nom}"] = buf.getvalue()
    bucket.store["autre/notes.txt"] = b"ignorer"

    def faux_classer(image, mime="image/png"):
        assert image[:4] == b"\x89PNG"
        defaut = "fissure" if len(faux_classer.vus) else "aucun"
        faux_classer.vus.append(1)
        return agent.Inspection(conforme=defaut == "aucun", defaut=defaut,
                                gravite="aucune" if defaut == "aucun" else "majeure",
                                confiance=0.9, description="test")
    faux_classer.vus = []

    monkeypatch.setattr(agent, "_bucket", lambda: bucket)
    monkeypatch.setattr(agent, "classer_image", faux_classer)
    monkeypatch.setattr(agent, "_resultats", {})
    monkeypatch.setenv("BUCKET", "bucket-de-test")

    assert agent.lister_images() == {"nombre": 2, "images": ["images/piece-01.png", "images/piece-02.png"]}
    assert agent.inspecter_image("autre/notes.txt")["erreur"]
    agent.inspecter_image("images/piece-01.png")
    agent.inspecter_image("images/piece-02.png")
    r = agent.publier_rapport()
    assert r["rejets"] == ["images/piece-02.png"]
    rapport = bucket.store[agent.CHEMIN_RAPPORT]
    assert "Pièces à rejeter : 1" in rapport and "| images/piece-02.png | REJET | fissure |" in rapport
    assert evaluer(agent._resultats, {"piece-01.png": "aucun", "piece-02.png": "fissure"}) == \
        {"exactitude": 1.0, "defectueuses_acceptees": []}


def test_evaluer_signale_une_piece_defectueuse_acceptee():
    res = {"images/p.png": {"defaut": "aucun", "conforme": True}}
    assert evaluer(res, {"p.png": "rayure"}) == {"exactitude": 0.0, "defectueuses_acceptees": ["p.png"]}


def test_schema_refuse_un_defaut_inconnu():
    import pydantic
    try:
        agent.Inspection(conforme=True, defaut="bosse", gravite="aucune", confiance=1, description="x")
    except pydantic.ValidationError:
        return
    raise AssertionError("défaut inconnu accepté")
