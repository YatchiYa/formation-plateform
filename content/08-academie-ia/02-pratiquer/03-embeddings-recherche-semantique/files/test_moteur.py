"""Tests SANS clé : un faux embedder (sac de mots haché) remplace Gemini.

Lancer :  pytest -q
"""
import json
import re
import zlib
from types import SimpleNamespace

import numpy as np
import pytest

import evaluer
import moteur


def faux_embed(textes, dim=64):
    m = np.zeros((len(textes), dim), dtype=np.float32)
    for i, t in enumerate(textes):
        for mot in re.findall(r"\w+", t.lower()):
            m[i, zlib.crc32(mot.encode()) % dim] += 1
    return moteur.normaliser(m + 1e-6)


class Compteur:
    def __init__(self):
        self.n = 0

    def __call__(self, textes):
        self.n += len(textes)
        return faux_embed(textes)


@pytest.fixture
def produits():
    with open("produits.json", encoding="utf-8") as f:
        return json.load(f)


def test_cosinus_et_top_k():
    v = moteur.normaliser(np.array([[1, 0], [0.9, 0.1], [0, 1]], dtype=np.float32))
    res = moteur.top_k(v, v[0], k=2)
    assert [i for i, _ in res] == [0, 1] and res[0][1] == pytest.approx(1.0)
    assert [i for i, _ in moteur.top_k(v, v[0], k=1, exclure=[0])] == [1]


def test_index_persistant_et_cache(tmp_path, produits):
    e = Compteur()
    assert moteur.indexer(produits, e, tmp_path) == 60
    assert moteur.indexer(produits, e, tmp_path) == 0          # rien n'a changé
    produits[4]["description"] += " Nouveau coloris."
    assert moteur.indexer(produits, e, tmp_path) == 1          # une seule fiche recalculée
    v, ps = moteur.charger_index(tmp_path)
    assert v.shape == (60, 64) and ps[4]["id"] == "P005"
    assert np.allclose(np.linalg.norm(v, axis=1), 1, atol=1e-5)


def test_recherche_similaires_doublons(tmp_path, produits):
    moteur.indexer(produits, faux_embed, tmp_path)
    v, ps = moteur.charger_index(tmp_path)
    assert moteur.chercher(v, ps, faux_embed, "valise cabine roues")[0][0]["id"] == "P043"
    assert "P019" not in [p["id"] for p, _ in moteur.similaires(v, ps, "P019")]
    paires = {(ps[i]["id"], ps[j]["id"]) for i, j, _ in moteur.doublons(v, 0.6)}
    assert ("P037", "P060") in paires


def test_kmeans_separe_deux_groupes():
    rng = np.random.default_rng(1)
    a = moteur.normaliser(np.array([1, 0, 0]) + rng.normal(0, 0.05, (10, 3)))
    b = moteur.normaliser(np.array([0, 0, 1]) + rng.normal(0, 0.05, (10, 3)))
    e = moteur.kmeans(np.vstack([a, b]).astype(np.float32), 2)
    assert len(set(e[:10])) == 1 and len(set(e[10:])) == 1 and e[0] != e[10]


def test_rappel_at_k():
    assert evaluer.rappel_at_k(["P1", "P2", "P3"], ["P2", "P9"], k=5) == 0.5
    assert evaluer.rappel_at_k(["P1", "P2", "P3"], ["P3"], k=2) == 0.0


def test_embedder_envoie_une_content_par_texte():
    appels = []

    def embed_content(model, contents, config):
        appels.append(len(contents))
        assert all(hasattr(c, "parts") for c in contents)      # pas une liste de str
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[3.0, 4.0]) for _ in contents])

    client = SimpleNamespace(models=SimpleNamespace(embed_content=embed_content))
    m = moteur.embedder_gemini(client, dim=2, lot=20)([f"t{i}" for i in range(45)])
    assert appels == [20, 20, 5] and m.shape == (45, 2)
    assert np.allclose(m[0], [0.6, 0.8])                       # normalisé


def test_prefixes():
    assert moteur.texte_requete("tente").startswith("task: search result | query: ")
    assert moteur.texte_document({"nom": "X", "categorie": "C", "description": "d"}) == "title: X | text: C. d"


def test_purete():
    assert moteur.purete(np.array([0, 0, 1, 1]), ["a", "a", "b", "b"]) == 1.0
    assert moteur.purete(np.array([0, 0, 0, 0]), ["a", "a", "b", "b"]) == 0.5
