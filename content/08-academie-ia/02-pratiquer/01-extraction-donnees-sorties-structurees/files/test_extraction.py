"""Tests sans clé d'API : schémas, réparation, revue humaine, évaluation.

Lancer :  pytest -q
"""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

import evaluer
import extraction
from schemas import CV, SCHEMAS, CompteRendu, Ligne

ICI = Path(__file__).parent
COMMANDE_OK = {"client": "Boulangerie Garnier & Fils", "contact": "Élodie Garnier",
               "lignes": [{"reference": "CAF-1KG", "quantite": 2}], "date_livraison": None,
               "urgence": "urgente", "mode": "livraison", "confiance": 0.95, "champs_incertains": []}


def faux_modele(monkeypatch, *reponses):
    """Remplace l'appel Gemini par une file de réponses JSON préparées."""
    file, prompts = [json.dumps(r) for r in reponses], []
    monkeypatch.setattr(extraction, "appeler", lambda prompt, schema: prompts.append(prompt) or file.pop(0))
    return prompts


def test_regles_metier_des_schemas():
    with pytest.raises(ValidationError, match="absente du catalogue"):
        Ligne(reference="CAF-1K", quantite=2)
    with pytest.raises(ValidationError):
        Ligne(reference="CAF-1KG", quantite=0)
    with pytest.raises(ValidationError, match="antérieure"):
        CompteRendu(projet="X", date_reunion="2026-10-08", participants=[], statut="bloque",
                    actions=[{"responsable": "A", "tache": "t", "echeance": "2026-10-01"}],
                    confiance=1, champs_incertains=[])
    with pytest.raises(ValidationError, match="e-mail invalide"):
        CV(nom="A", email="a[at]b.fr", annees_experience=1, niveau_etudes="bac",
           competences=[], confiance=1, champs_incertains=[])


def test_reparation_reussie(monkeypatch):
    mauvais = {**COMMANDE_OK, "lignes": [{"reference": "CAF-1K", "quantite": 2}]}
    prompts = faux_modele(monkeypatch, mauvais, COMMANDE_OK)
    r = extraction.extraire("commande", "2 CAF-1K svp")
    assert r["reparations"] == 1 and r["donnees"]["lignes"][0]["reference"] == "CAF-1KG"
    assert "absente du catalogue" in prompts[1]  # l'erreur exacte est renvoyée au modèle
    assert r["raisons"] == ["réparé 1 fois"]  # valide, mais à faire relire


def test_echec_apres_reparation_part_en_revue(monkeypatch):
    mauvais = {**COMMANDE_OK, "lignes": []}
    faux_modele(monkeypatch, mauvais, mauvais)
    r = extraction.extraire("commande", "...")
    assert r["donnees"] is None and r["a_revoir"] and "invalide" in r["raisons"][0]


def test_confiance_basse_ou_champ_incertain_part_en_revue(monkeypatch):
    faux_modele(monkeypatch, {**COMMANDE_OK, "confiance": 0.6},
                {**COMMANDE_OK, "champs_incertains": ["date_livraison"]})
    assert extraction.extraire("commande", "...")["raisons"] == ["confiance 0.6 < 0.8"]
    assert extraction.extraire("commande", "...")["a_revoir"]


def test_normalisation():
    assert evaluer.norm("Électrotechnique ") == evaluer.norm("electrotechnique")
    assert evaluer.norm(["SQL", "Python"]) == evaluer.norm(["python", "sql"])
    assert evaluer.norm(None) != evaluer.norm([])


def test_evaluation_par_champ():
    annotes = [{"id": "d1", "type": "compte_rendu",
                "attendu": {"projet": "Atlas", "actions": [{"responsable": "Paul", "echeance": "2026-10-15"}]}}]
    predits = {"d1": {"donnees": {"projet": "atlas", "actions": [
        {"responsable": "Paul", "tache": "texte libre ignoré", "echeance": "2026-10-15"}]}}}
    scores, erreurs = evaluer.evaluer(annotes, predits)
    assert scores[("compte_rendu", "projet")] == [1, 1] and erreurs == []
    scores, erreurs = evaluer.evaluer(annotes, {})  # document non extrait = tout faux
    assert sum(s[0] for s in scores.values()) == 0 and len(erreurs) == 2


def test_jeu_annote_coherent_avec_les_schemas():
    docs = [json.loads(l) for l in (ICI / "jeu_annote.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(docs) == 15 and len({d["id"] for d in docs}) == 15
    for d in docs:
        assert set(d["attendu"]) <= set(SCHEMAS[d["type"]].model_fields), d["id"]
        if d["type"] != "compte_rendu":  # les annotations respectent elles-mêmes les règles métier
            SCHEMAS[d["type"]].model_validate({**d["attendu"], "confiance": 1, "champs_incertains": []})
