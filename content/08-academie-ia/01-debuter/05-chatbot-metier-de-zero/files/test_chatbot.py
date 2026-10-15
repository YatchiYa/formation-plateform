"""Tests sans clé d'API : un faux modèle remplace Gemini.

Lancer :  pytest -q test_chatbot.py
"""
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from google.genai import errors

import app
import chatbot


class FauxModele:
    """Imite client.models.generate_content_stream et garde ce qu'on lui envoie."""

    def __init__(self, morceaux=("Bonjour, ", "la salle ouvre à 6h.")):
        self.morceaux, self.appels = morceaux, []

    def generate_content_stream(self, model, contents, config):
        self.appels.append(contents)
        for m in self.morceaux:
            yield SimpleNamespace(text=m)


@pytest.fixture
def faux(monkeypatch, tmp_path):
    modele = FauxModele()
    monkeypatch.setattr(chatbot, "get_client", lambda: SimpleNamespace(models=modele))
    monkeypatch.setattr(chatbot, "JOURNAL", tmp_path / "journal.jsonl")
    chatbot.MEMOIRE.clear()
    return modele


web = TestClient(app.app)


def test_prompt_contient_regles_et_connaissances():
    assert "N'invente jamais" in chatbot.SYSTEM_PROMPT
    assert "54 € / mois" in chatbot.SYSTEM_PROMPT  # tarif Premium de la fiche


def test_memoire_garde_les_derniers_messages():
    chatbot.MEMOIRE.clear()
    for i in range(15):
        chatbot.memoriser("s", "user", f"m{i}")
    h = chatbot.historique("s")
    assert len(h) == chatbot.MAX_MESSAGES and h[-1].parts[0].text == "m14"
    chatbot.memoriser("vide", "user", "x")
    assert len(chatbot.historique("vide")) == 1  # moins que la limite : rien n'est oublié


def test_masquer_donnees_personnelles():
    t = chatbot.masquer("Moi c'est jo@exemple.fr, 06 12 34 56 78, FR76 3000 6000 0112 3456 7890 189")
    assert t == "Moi c'est [EMAIL], [TEL], [IBAN]"


def test_chat_streaming_memoire_et_journal(faux):
    r = web.post("/chat", json={"session": "s1", "message": "Vous ouvrez à quelle heure ?"})
    assert r.status_code == 200 and r.text == "Bonjour, la salle ouvre à 6h."
    assert r.headers["x-echange-id"]
    # 2e tour : le modèle reçoit l'historique (question 1, réponse 1, question 2)
    web.post("/chat", json={"session": "s1", "message": "Et le dimanche ?"})
    assert [c.role for c in faux.appels[1]] == ["user", "model", "user"]
    assert chatbot.statistiques()["echanges"] == 2


def test_avis_et_satisfaction(faux):
    eid = web.post("/chat", json={"session": "s2", "message": "Tarifs ?"}).headers["x-echange-id"]
    assert web.post("/avis", json={"echange_id": eid, "note": 1}).status_code == 200
    assert web.post("/avis", json={"echange_id": eid, "note": -1}).status_code == 200
    assert web.post("/avis", json={"echange_id": eid, "note": 5}).status_code == 422
    s = web.get("/stats").json()
    assert s["avis"] == 2 and s["satisfaction"] == 0.5


def test_validation_des_entrees(faux):
    assert web.post("/chat", json={"session": "s", "message": ""}).status_code == 422
    assert web.post("/chat", json={"session": "s", "message": "x" * 2001}).status_code == 422


def test_panne_du_modele_message_poli(monkeypatch, tmp_path):
    def en_panne(**_):
        raise errors.APIError(400, {"error": {"message": "requête invalide", "status": "INVALID_ARGUMENT"}})
    monkeypatch.setattr(chatbot, "get_client",
                        lambda: SimpleNamespace(models=SimpleNamespace(generate_content_stream=en_panne)))
    monkeypatch.setattr(chatbot, "JOURNAL", tmp_path / "journal.jsonl")
    r = web.post("/chat", json={"session": "s3", "message": "Bonjour"})
    assert r.text == chatbot.MESSAGE_ERREUR
    assert chatbot.historique("s3") == []  # une erreur n'est pas mémorisée
    assert chatbot.statistiques()["erreurs"] == 1


def test_page_html_servie():
    r = web.get("/")
    assert r.status_code == 200 and "getReader" in r.text
