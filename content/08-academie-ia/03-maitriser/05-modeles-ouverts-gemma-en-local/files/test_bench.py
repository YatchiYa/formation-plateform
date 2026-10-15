"""Tests sans clé ni serveur : notation, nettoyage, configuration et client (httpx.MockTransport)."""
import json
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import bench  # noqa: E402
from client_llm import BASES, ClientLLM, configuration, nettoyer  # noqa: E402

QUESTIONS = json.loads(Path(__file__).with_name("questions.json").read_text(encoding="utf-8"))
Q = {q["id"]: q for q in QUESTIONS}


def test_quinze_questions_bien_formees():
    assert len(QUESTIONS) == 15 and len(Q) == 15
    assert {q["type"] for q in QUESTIONS} <= {"contient", "nombre", "json", "regex"}


@pytest.mark.parametrize("qid,texte,ok", [
    ("q01", "Na", True), ("q01", "Le symbole est K.", False),
    ("q02", "288 €", True), ("q02", "288,00", True), ("q02", "240", False),
    ("q03", "1 350 / 15 = 90", True),
    ("q05", "2026-04-29", True), ("q05", "2026-04-30", False),
    ("q06", '```json\n{"nom": "Léa Martin", "ville": "Nantes", "montant": 129.90}\n```', True),
    ("q06", '{"nom": "Léa Martin", "ville": "Nantes", "montant": "129,90"}', False),
    ("q08", "Négatif", True), ("q08", "NEUTRE", False),
    ("q11", "NON", True), ("q11", "Non, jamais", True), ("q11", "OUI", False),
    ("q14", "SELECT COUNT(*) FROM commandes WHERE statut = 'annulee';", True),
    ("q14", "SELECT * FROM commandes", False),
])
def test_notation(qid, texte, ok):
    assert bench.noter(Q[qid], texte) is ok


def test_nettoyage_du_raisonnement():
    assert nettoyer("<thought>* La capitale…</thought>Paris") == "Paris"
    assert nettoyer("<think>\nhmm\n</think>\n\nNON") == "NON"


def test_configuration_par_fournisseur(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "cle-factice")
    assert configuration("gemini") == (BASES["gemini"], "cle-factice")
    assert configuration("ollama") == ("http://localhost:11434/v1", "local")
    monkeypatch.setenv("LLM_BASE_URL", "http://serveur:8000/v1/")
    assert configuration("gemini")[0] == "http://serveur:8000/v1"


def _faux_serveur(reponses):
    """Serveur compatible OpenAI simulé : renvoie les statuts/contenus dans l'ordre."""
    appels = []

    def gerer(requete: httpx.Request):
        appels.append(json.loads(requete.content))
        statut, contenu = reponses.pop(0)
        return httpx.Response(statut, json={"choices": [{"message": {"content": contenu}}],
                                            "usage": {"completion_tokens": 3}})
    return httpx.MockTransport(gerer), appels


def test_client_agnostique_et_reessai(monkeypatch):
    monkeypatch.setattr("client_llm.time.sleep", lambda s: None)
    transport, appels = _faux_serveur([(429, ""), (200, "<thought>…</thought>Paris")])
    client = ClientLLM("http://localhost:11434/v1", "local", transport=transport)
    r = client.discuter("gemma4:e2b", "Capitale ?", "Sois bref.")
    assert r.texte == "Paris" and r.jetons_sortie == 3
    assert len(appels) == 2 and appels[0]["model"] == "gemma4:e2b"
    assert appels[0]["messages"][0] == {"role": "system", "content": "Sois bref."}


def test_banc_complet_avec_faux_serveur():
    bonnes = {"q01": "Na", "q02": "288", "q03": "90", "q04": "15", "q05": "2026-04-29",
              "q06": '{"nom": "Léa Martin", "ville": "Nantes", "montant": 129.9}', "q07": "B2",
              "q08": "NEGATIF", "q09": "SERVICES_GENERAUX", "q10": "OUI", "q11": "NON", "q12": "T2",
              "q13": "465", "q14": "SELECT COUNT(*) FROM commandes WHERE statut = 'annulee'", "q15": "Hugo"}
    transport, _ = _faux_serveur([(200, bonnes[q["id"]]) for q in QUESTIONS])
    r = bench.evaluer(ClientLLM("http://x/v1", "k", transport=transport), "faux", QUESTIONS)
    assert r["score"] == 15 and r["total"] == 15
    assert "| faux | 15/15 |" in bench.tableau([r])
