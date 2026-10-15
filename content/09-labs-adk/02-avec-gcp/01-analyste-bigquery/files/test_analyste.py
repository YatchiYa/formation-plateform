"""Tests sans clé ni compte Google Cloud :  pytest -q
Le dry-run est remplacé par une fausse estimation ; le modèle par un faux modèle scripté."""
import asyncio

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.integrations.bigquery.config import WriteMode
from google.genai import types

import agent
from evaluer import meme_resultat

D = agent.DATASET


def est(type_="SELECT", octets=5_000_000, tables=(f"{D}.orders",)):
    return {"type": type_, "octets": octets, "tables": sorted(tables)}


def test_verifier_accepte_une_lecture_raisonnable():
    assert agent.verifier(est()) is None


@pytest.mark.parametrize("estimation,mot", [
    (est(type_="DROP_TABLE"), "SELECT"),
    (est(type_="DELETE"), "SELECT"),
    (est(tables=[f"{D}.users"]), "non autorisées"),
    (est(tables=[f"{D}.orders", f"{D}.events"]), "non autorisées"),
    (est(tables=["autre-projet.rh.salaires"]), "non autorisées"),
    (est(octets=2_000_000_000), "trop coûteuse"),
])
def test_verifier_refuse(estimation, mot):
    assert mot in agent.verifier(estimation)


def test_plafond_et_lecture_seule():
    assert agent.MAX_OCTETS <= 1_000_000_000
    outils = asyncio.run(agent.root_agent.tools[0].get_tools())
    assert sorted(t.name for t in outils) == ["execute_sql", "get_table_info"]
    cfg = agent.root_agent.tools[0]._tool_settings
    assert cfg.write_mode == WriteMode.BLOCKED and cfg.maximum_bytes_billed == agent.MAX_OCTETS


class FauxOutil:
    def __init__(self, name):
        self.name = name


class FauxContexte:
    def __init__(self):
        self.state = {}


def test_controle_cout_bloque_avant_execution(monkeypatch):
    vus = []
    monkeypatch.setattr(agent, "estimer", lambda q: vus.append(q) or est(tables=[f"{D}.users"]))
    ctx = FauxContexte()
    r = agent.controle_cout(FauxOutil("execute_sql"), {"query": "SELECT email FROM x"}, ctx)
    assert r["status"] == "ERROR" and "users" in r["error_details"]
    assert vus == ["SELECT email FROM x"] and ctx.state["estimations"][0]["octets"] == 5_000_000
    # Une requête autorisée passe : le callback renvoie None et l'outil s'exécute.
    monkeypatch.setattr(agent, "estimer", lambda q: est())
    assert agent.controle_cout(FauxOutil("execute_sql"), {"query": "SELECT 1"}, ctx) is None


def test_get_table_info_limite_aux_tables_autorisees():
    ctx = FauxContexte()
    ok = {"project_id": "bigquery-public-data", "dataset_id": "thelook_ecommerce",
          "table_id": "orders"}
    assert agent.controle_cout(FauxOutil("get_table_info"), ok, ctx) is None
    assert agent.controle_cout(FauxOutil("get_table_info"), {**ok, "table_id": "users"},
                               ctx)["status"] == "ERROR"


class FauxModele(BaseLlm):
    script: list = []

    async def generate_content_async(self, llm_request, stream=False):
        yield LlmResponse(content=self.script.pop(0))


def test_agent_refus_puis_reponse(monkeypatch):
    monkeypatch.setattr(agent, "estimer", lambda q: est(tables=[f"{D}.users"]))
    modele = FauxModele(model="faux", script=[
        types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(
            name="execute_sql", args={"project_id": "p", "query": "SELECT email FROM users"}))]),
        types.Content(role="model", parts=[types.Part(text="Je ne peux pas lire users.")]),
    ])
    reponse, etat = asyncio.run(agent.demander("e-mails ?", agent.creer_agent(model=modele)))
    assert reponse == "Je ne peux pas lire users."
    assert etat["resultats"][0]["status"] == "ERROR"          # BigQuery n'a jamais été appelé


def test_comparaison():
    assert meme_resultat([["Jeans", 1.004]], [[1.0, "Jeans"]])
    assert not meme_resultat([["Jeans", 1.0]], [["Jeans", 1.0], ["Swim", 2.0]])
