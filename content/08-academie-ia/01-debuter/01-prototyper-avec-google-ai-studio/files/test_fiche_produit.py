"""Tests sans clé : un faux client remplace Gemini.  Lancer : pytest -q"""
import json
from types import SimpleNamespace

import pytest
from google.genai import errors

import fiche_produit as fp

FICHE = {"titre": "Gourde isotherme 500 ml en inox", "accroche": "Fraîcheur toute la journée.",
         "description": "Une gourde en inox de 500 ml.", "points_forts": ["500 ml", "Inox"],
         "mots_cles": ["gourde", "inox"]}


class FakeModels:
    def __init__(self, reponses):
        self.reponses, self.appels = list(reponses), []

    def generate_content(self, model, contents, config):
        self.appels.append((model, contents, config))
        r = self.reponses.pop(0)
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(text=r)


def fake_client(*reponses):
    return SimpleNamespace(models=FakeModels(reponses))


def test_config_reprend_le_prototype(monkeypatch):
    monkeypatch.delenv("TEMPERATURE", raising=False)
    monkeypatch.delenv("TOP_P", raising=False)
    c = fp.build_config()
    assert c.temperature is None and c.top_p is None  # valeurs par défaut du modèle
    assert c.response_mime_type == "application/json"
    assert "N'invente AUCUNE" in c.system_instruction


def test_temperature_et_top_p_optionnels(monkeypatch):
    monkeypatch.setenv("TEMPERATURE", "0.2")
    monkeypatch.setenv("TOP_P", "0.9")
    c = fp.build_config()
    assert c.temperature == 0.2 and c.top_p == 0.9


def test_exemples_puis_demande():
    contents = fp.build_contents("Gourde 500 ml")
    assert [c.role for c in contents] == ["user", "model", "user"]
    assert json.loads(contents[1].parts[0].text)["titre"]  # l'exemple est du JSON valide
    assert contents[-1].parts[0].text == "Gourde 500 ml"


def test_rediger_fiche_valide_le_json():
    client = fake_client(json.dumps(FICHE))
    fiche = fp.rediger_fiche(client, "  Gourde isotherme 500 ml  ")
    assert fiche.titre.startswith("Gourde")
    assert client.models.appels[0][1][-1].parts[0].text == "Gourde isotherme 500 ml"


def test_json_incomplet_refuse():
    with pytest.raises(Exception):
        fp.rediger_fiche(fake_client('{"titre": "x"}'), "Gourde")


def test_description_vide_refusee():
    with pytest.raises(ValueError):
        fp.rediger_fiche(fake_client(), "   ")


def test_reessaie_sur_429(monkeypatch):
    monkeypatch.setattr(fp.time, "sleep", lambda s: None)
    quota = errors.ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    client = fake_client(quota, json.dumps(FICHE))
    assert fp.rediger_fiche(client, "Gourde").titre
    assert len(client.models.appels) == 2


def test_ne_reessaie_pas_sur_400():
    mauvaise = errors.ClientError(400, {"error": {"message": "bad", "status": "INVALID_ARGUMENT"}})
    with pytest.raises(errors.ClientError):
        fp.rediger_fiche(fake_client(mauvaise), "Gourde")
