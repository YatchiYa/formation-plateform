"""Tests sans clé ni GCP : outils purs + client HTTP simulé. Lancer : pytest -q"""
import json

import httpx

import agent
import client


def test_politique_trouvee_sans_accents():
    r = agent.chercher_politique("Télétravail")
    assert r["trouve"] and r["sujet"] == "teletravail"


def test_politique_absente_liste_les_sujets():
    r = agent.chercher_politique("cantine")
    assert not r["trouve"] and "vpn" in r["sujets_connus"]


def test_ticket_et_journal_structure(capsys):
    r = agent.ouvrir_ticket("IT", "Le VPN ne se connecte plus")
    assert r["statut"] == "ouvert" and r["id"].startswith("TCK-")
    ligne = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert ligne["severity"] == "INFO" and ligne["evenement"] == "ticket_ouvert"


def test_ticket_categorie_invalide():
    assert "erreur" in agent.ouvrir_ticket("compta", "x")


def test_agent_declare_ses_outils():
    noms = {t.__name__ for t in agent.root_agent.tools}
    assert noms == {"chercher_politique", "ouvrir_ticket"}


def test_client_envoie_le_jeton_et_lit_la_reponse():
    vus = []

    def repondre(req: httpx.Request) -> httpx.Response:
        vus.append(req)
        assert req.headers["Authorization"] == "Bearer jeton-factice"
        if req.url.path == "/run":
            return httpx.Response(200, json=[
                {"content": {"parts": [{"functionCall": {"name": "chercher_politique", "args": {}}}]}},
                {"content": {"parts": [{"text": "2 jours par semaine."}]}},
            ])
        return httpx.Response(200, json={"id": "s"})

    r = client.demander("télétravail ?", "https://exemple.run.app", "jeton-factice",
                        transport=httpx.MockTransport(repondre))
    assert r == {"reponse": "2 jours par semaine.", "outils": ["chercher_politique"]}
    assert [v.url.path for v in vus][-1] == "/run"
