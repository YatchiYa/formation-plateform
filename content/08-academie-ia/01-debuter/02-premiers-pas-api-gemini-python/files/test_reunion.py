"""Tests sans clé ni réseau : on remplace le client Gemini par un faux.  Lancer : pytest -q"""
import io
import json
from types import SimpleNamespace as NS

import pytest
from google.genai import errors

import reunion

CR = {"resume": "Lancement de la v2 décalé.", "decisions": ["Lancement le 4 novembre"],
      "actions": [{"tache": "Prévenir le support", "responsable": "Inès", "echeance": "vendredi"}]}
USAGE = NS(prompt_token_count=1000, candidates_token_count=200, thoughts_token_count=300)


class FakeClient:
    def __init__(self, *reponses):
        self.reponses = list(reponses)
        self.appels = []
        self.models = self
        self.chats = self

    def _suivante(self, **kw):
        self.appels.append(kw)
        r = self.reponses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    def generate_content(self, **kw):
        return self._suivante(**kw)

    def generate_content_stream(self, **kw):
        return iter(self._suivante(**kw))

    def count_tokens(self, **kw):
        return self._suivante(**kw)

    def create(self, **kw):  # client.chats.create
        self.appels.append(kw)
        return NS(send_message=lambda q: NS(text=f"Réponse à : {q}"))


def test_cout_compte_la_pensee_en_sortie(monkeypatch):
    monkeypatch.setattr(reunion, "PRIX_ENTREE_1M", 1.0)
    monkeypatch.setattr(reunion, "PRIX_SORTIE_1M", 10.0)
    # 1000 x 1 $ + (200 + 300) x 10 $, par million
    assert reunion.cout(USAGE) == pytest.approx(0.006)


def test_cout_tolere_les_champs_vides():
    assert reunion.cout(NS(prompt_token_count=None, candidates_token_count=None,
                           thoughts_token_count=None)) == 0


def test_compte_rendu_structure(monkeypatch):
    monkeypatch.setenv("TEMPERATURE", "0.2")
    client = FakeClient(NS(text=json.dumps(CR), usage_metadata=USAGE))
    cr, dollars = reunion.compte_rendu(client, "Inès : on décale.")
    assert cr.actions[0].responsable == "Inès" and dollars > 0
    cfg = client.appels[0]["config"]
    assert cfg.response_mime_type == "application/json" and cfg.temperature == 0.2
    assert "n'inventes" in cfg.system_instruction


def test_temperature_absente_par_defaut(monkeypatch):
    monkeypatch.delenv("TEMPERATURE", raising=False)
    assert reunion.config().temperature is None


def test_markdown_contient_le_tableau_des_actions():
    md = reunion.en_markdown(reunion.CompteRendu.model_validate(CR))
    assert "| Prévenir le support | Inès | vendredi |" in md


def test_stream_concatene_les_morceaux(capsys):
    client = FakeClient([NS(text="Bon"), NS(text="jour"), NS(text=None)])
    assert reunion.resume_stream(client, "x") == "Bonjour"
    assert "Bonjour" in capsys.readouterr().out


def test_tokens():
    assert reunion.tokens(FakeClient(NS(total_tokens=42)), "x") == 42


def test_chat_multi_tours(capsys):
    client = FakeClient()
    reunion.chat(client, "transcription", entrees=io.StringIO("Qui ?\nQuand ?\n\nignorée\n"))
    out = capsys.readouterr().out
    assert "Réponse à : Qui ?" in out and "Réponse à : Quand ?" in out and "ignorée" not in out
    assert len(client.appels[0]["history"]) == 2


def test_reessais_sur_503_puis_succes(monkeypatch):
    monkeypatch.setattr(reunion.time, "sleep", lambda s: None)
    panne = errors.ServerError(503, {"error": {"message": "surcharge", "status": "UNAVAILABLE"}})
    client = FakeClient(panne, panne, NS(total_tokens=7))
    assert reunion.tokens(client, "x") == 7 and len(client.appels) == 3


def test_pas_de_reessai_sur_cle_invalide():
    refus = errors.ClientError(400, {"error": {"message": "API key not valid", "status": "INVALID_ARGUMENT"}})
    with pytest.raises(errors.ClientError):
        reunion.tokens(FakeClient(refus, NS(total_tokens=1)), "x")


def test_abandon_apres_n_essais(monkeypatch):
    monkeypatch.setattr(reunion.time, "sleep", lambda s: None)
    quota = errors.ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    with pytest.raises(errors.ClientError):
        reunion.avec_reessais(lambda: (_ for _ in ()).throw(quota), essais=3)


@pytest.mark.parametrize("valeur,attendu", [("TRUE", "Vertex AI"), ("false", "clé d'API"), ("", "clé d'API")])
def test_mode(monkeypatch, valeur, attendu):
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", valeur)
    assert reunion.mode() == attendu
