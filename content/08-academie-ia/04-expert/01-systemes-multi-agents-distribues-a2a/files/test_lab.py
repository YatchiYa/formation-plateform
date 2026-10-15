"""Tests SANS clé ni réseau sortant : outils, Agent Card, authentification, découverte.

pytest -q
"""
import json
import os

os.environ.setdefault("A2A_TOKEN", "jeton-de-test-0123456789")

import pytest
from starlette.testclient import TestClient

import client
import orchestrator
import pricing_agent
import stock_agent
from common import CARD_PATH, serve

TOKEN = os.environ["A2A_TOKEN"]


def test_check_stock():
    r = stock_agent.check_stock("chaise-ergo")
    assert r["status"] == "ok" and r["total"] == 12 and r["par_entrepot"]["lille"] == 0
    assert stock_agent.check_stock("INCONNU")["status"] == "error"


@pytest.mark.parametrize("qty,remise,total", [(1, 0.0, 189.0), (5, 0.05, 897.75),
                                              (12, 0.10, 2041.2), (20, 0.15, 3213.0)])
def test_quote_price_paliers(qty, remise, total):
    r = pricing_agent.quote_price("CHAISE-ERGO", qty)
    assert (r["remise"], r["total_ht"]) == (remise, total)


def test_quote_price_erreurs():
    assert pricing_agent.quote_price("CHAISE-ERGO", 0)["status"] == "error"
    assert pricing_agent.quote_price("XXX", 1)["status"] == "error"


@pytest.fixture
def stock_server():
    with TestClient(serve(stock_agent.root_agent, port=8101, token=TOKEN)) as c:  # lance le lifespan
        yield c


def test_agent_card_publique(stock_server):
    card = stock_server.get(CARD_PATH).json()
    assert card["name"] == "stock_agent"
    assert card["supportedInterfaces"][0]["url"] == "http://localhost:8101"
    assert "check_stock" in [s["name"] for s in card["skills"]]


def test_rpc_refuse_sans_jeton_ou_mauvais_jeton(stock_server):
    body = client._payload("SendMessage", "stock ?")
    assert stock_server.post("/", json=body).status_code == 401
    bad = {"Authorization": "Bearer pas-le-bon"}
    assert stock_server.post("/", json=body, headers=bad).status_code == 401


def test_rpc_accepte_le_jeton_et_verifie_la_version(stock_server):
    # Jeton valide mais sans en-tête A2A-Version : refus du protocole (pas du middleware)
    r = stock_server.post("/", json=client._payload("SendMessage", "x"),
                          headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200 and "not supported" in r.json()["error"]["message"]


def test_decouverte_ecarte_les_agents_injoignables(tmp_path):
    reg = tmp_path / "registry.json"
    reg.write_text(json.dumps({"agents": [{"name": "fantome", "url": "http://127.0.0.1:9"}]}))
    found, missing = orchestrator.discover(reg, timeout=0.5)
    assert found == [] and missing == ["fantome"]


def test_orchestrateur_construit_un_outil_par_agent():
    found = [{"name": "stock_agent", "description": "stock", "skills": [],
              "card_url": "http://localhost:8101" + CARD_PATH}]
    agent = orchestrator.build_orchestrator(found, ["pricing_agent"], TOKEN)
    assert [t.name for t in agent.tools] == ["stock_agent"]
    assert "indisponibles en ce moment : pricing_agent" in agent.instruction


def test_jeton_trop_court(monkeypatch):
    monkeypatch.setenv("A2A_TOKEN", "court")
    with pytest.raises(RuntimeError):
        serve(stock_agent.root_agent, port=8101)


def test_payload_a2a_v1():
    p = client._payload("SendMessage", "bonjour")
    assert p["method"] == "SendMessage" and p["params"]["message"]["role"] == "ROLE_USER"
    assert p["params"]["message"]["parts"] == [{"text": "bonjour"}]
