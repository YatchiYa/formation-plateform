"""Tests sans clé ni GCP. Lancer : pytest -q"""
import httpx

import client_a2a
import commandes_agent
import stock_agent


def test_verifier_stock():
    assert stock_agent.verifier_stock(" vis-m6 ")["disponible"] == 1200
    assert stock_agent.verifier_stock("XYZ")["trouve"] is False


def test_calculer_devis():
    assert commandes_agent.calculer_devis(500, 0.08) == {"total_ht": 40.0, "tva": 8.0, "total_ttc": 48.0}
    assert "erreur" in commandes_agent.calculer_devis(0, 1)


def test_carte_a2a_servie_par_l_app_starlette():
    from starlette.testclient import TestClient
    with TestClient(stock_agent.app) as c:
        carte = c.get("/.well-known/agent-card.json").json()
    assert carte["name"] == "agent_stock"
    assert carte["supportedInterfaces"][0]["url"].startswith("http://localhost:8001")
    assert any(s["name"] == "verifier_stock" for s in carte["skills"])


def test_jeton_seulement_vers_https(monkeypatch):
    assert commandes_agent.client_http("http://localhost:8001").auth is None
    from google.oauth2 import id_token
    monkeypatch.setattr(id_token, "fetch_id_token", lambda req, aud: f"jeton-pour-{aud}")
    auth = commandes_agent.JetonIdentite("https://stock.example.run.app")
    req = next(auth.auth_flow(httpx.Request("POST", "https://stock.example.run.app/")))
    assert req.headers["Authorization"] == "Bearer jeton-pour-https://stock.example.run.app"


def test_client_a2a_lit_la_tache():
    def serveur(req: httpx.Request) -> httpx.Response:
        assert req.headers["Authorization"] == "Bearer t"
        if req.method == "GET":
            return httpx.Response(200, json={"name": "agent_commandes",
                                             "supportedInterfaces": [{"url": "https://cmd.example/"}]})
        assert req.url == "https://cmd.example/"
        return httpx.Response(200, json={"result": {"task": {
            "status": {"state": "TASK_STATE_COMPLETED"},
            "artifacts": [{"parts": [{"text": "Total TTC : 48 €"}]}],
            "history": [{"parts": [{"data": {"name": "agent_stock"}, "metadata": {"adk_type": "function_call"}}]}],
        }}})

    r = client_a2a.appeler("https://cmd.example", "devis", "t", transport=httpx.MockTransport(serveur))
    assert r == {"agent": "agent_commandes", "etat": "TASK_STATE_COMPLETED",
                 "outils": ["agent_stock"], "reponse": "Total TTC : 48 €"}


def test_agent_stock_est_un_outil_distant():
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from google.adk.tools.agent_tool import AgentTool
    outils = commandes_agent.root_agent.tools
    distant = next(t for t in outils if isinstance(t, AgentTool))
    assert len(outils) == 2 and isinstance(distant.agent, RemoteA2aAgent) and distant.agent.name == "agent_stock"
