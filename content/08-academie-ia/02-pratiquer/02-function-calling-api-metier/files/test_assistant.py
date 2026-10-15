"""Tests SANS clé ni réseau : faux modèle scripté + API RH en mémoire (TestClient).

Lancer :  pytest -q
"""
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from google.genai import types

import api_rh
import assistant
import outils_rh


@pytest.fixture(autouse=True)
def api_en_memoire(tmp_path, monkeypatch):
    api_rh.reset()
    monkeypatch.setattr(outils_rh, "http", TestClient(api_rh.app))
    monkeypatch.setattr(assistant, "AUDIT_PATH", str(tmp_path / "audit.jsonl"))


def audit():
    with open(assistant.AUDIT_PATH, encoding="utf-8") as f:
        return [json.loads(l) for l in f]


class FauxModele:
    """Rejoue une liste de réponses ; chaque réponse = liste de FunctionCall ou un texte."""
    def __init__(self, script):
        self.script, self.configs = list(script), []
        self.models = self

    def generate_content(self, model, contents, config):
        self.configs.append(config)
        etape = self.script.pop(0)
        parts = ([types.Part(text=etape)] if isinstance(etape, str) else
                 [types.Part(function_call=types.FunctionCall(id=f"c{i}", name=n, args=a))
                  for i, (n, a) in enumerate(etape)])
        return types.GenerateContentResponse(candidates=[types.Candidate(
            content=types.Content(role="model", parts=parts))])


def test_api_jours_ouvres_et_solde():
    assert api_rh.jours_ouvres(api_rh.date(2030, 1, 4), api_rh.date(2030, 1, 8)) == 3  # ven→mar
    r = outils_rh.creer_demande_conges("E001", "E001", "rtt", "2030-01-07", "2030-01-08")
    assert r["jours"] == 2 and outils_rh.consulter_solde("E001", "E001")["rtt"] == 2


def test_api_controle_acces():
    assert outils_rh.consulter_solde("E004", "E001")["employe_id"] == "E001"  # manager
    assert outils_rh.consulter_solde("E001", "E002")["code_http"] == 403      # collègue
    assert outils_rh.consulter_solde("E004", "E999")["code_http"] == 404


@pytest.mark.parametrize("nom,args,message", [
    ("consulter_solde", {"employe_id": "Camille"}, "E001"),
    ("consulter_solde", {"employe_id": "E001", "admin": True}, "non prévus"),
    ("creer_demande_conges", {"employe_id": "E001", "type_conge": "rtt",
                              "date_debut": "2030-02-10", "date_fin": "2030-02-01"}, "avant"),
    ("creer_demande_conges", {"employe_id": "E001", "type_conge": "sabbatique",
                              "date_debut": "2030-02-01", "date_fin": "2030-02-02"}, "type_conge"),
    ("supprimer_tout", {}, "inconnu"),
])
def test_validation_refuse(nom, args, message):
    with pytest.raises(ValueError, match=message):
        outils_rh.valider(nom, args)


def test_validation_normalise():
    assert outils_rh.valider("consulter_solde", {"employe_id": " e001 "}) == {"employe_id": "E001"}


def test_appels_paralleles_puis_reponse():
    faux = FauxModele([[("consulter_solde", {"employe_id": "E001"}),
                        ("consulter_solde", {"employe_id": "E002"})],
                       "E001 a 4 RTT, E002 en a 9."])
    h = []
    rep = assistant.repondre(faux, h, "RTT de mon équipe ?", "E004", lambda *a: True, afficher=lambda *_: None)
    assert rep == "E001 a 4 RTT, E002 en a 9."
    reponses = [p.function_response for p in h[2].parts]
    assert [r.id for r in reponses] == ["c0", "c1"]                # ids recopiés
    assert reponses[1].response["rtt"] == 9
    assert [e["statut"] for e in audit()] == ["ok", "ok"]


def test_action_sensible_refusee_ne_touche_pas_l_api():
    faux = FauxModele([[("creer_demande_conges", {"employe_id": "E001", "type_conge": "rtt",
                                                   "date_debut": "2030-03-04", "date_fin": "2030-03-05"})],
                       "D'accord, je n'ai rien créé."])
    assistant.repondre(faux, [], "Pose 2 RTT", "E001", lambda *a: False, afficher=lambda *_: None)
    assert api_rh.DEMANDES == {} and api_rh.SOLDES["E001"]["rtt"] == 4
    assert audit()[0]["statut"] == "refuse_utilisateur"


def test_erreur_api_renvoyee_au_modele():
    faux = FauxModele([[("consulter_solde", {"employe_id": "E003"})], "Accès refusé."])
    h = []
    assistant.repondre(faux, h, "Solde de E003 ?", "E004", lambda *a: True, afficher=lambda *_: None)
    assert h[2].parts[0].function_response.response["code_http"] == 403
    assert audit()[0]["statut"] == "erreur"


def test_timeout_devient_message(monkeypatch):
    def lent(request):
        raise httpx.ReadTimeout("trop lent", request=request)
    monkeypatch.setattr(outils_rh, "http", httpx.Client(base_url="http://x", transport=httpx.MockTransport(lent)))
    assert "pas répondu à temps" in outils_rh.consulter_solde("E001", "E001")["erreur"]


def test_mode_any_seulement_au_premier_tour_et_limite_de_tours():
    faux = FauxModele([[("consulter_solde", {"employe_id": "E001"})]] * assistant.MAX_TOURS)
    rep = assistant.repondre(faux, [], "Boucle", "E001", lambda *a: True, mode="ANY", afficher=lambda *_: None)
    modes = [c.tool_config.function_calling_config.mode for c in faux.configs]
    assert modes[0] == "ANY" and set(modes[1:]) == {"AUTO"}
    assert "humain" in rep and len(faux.configs) == assistant.MAX_TOURS
