"""Tests sans clé ni Google Cloud :  pytest -q
La mémoire est un InMemoryMemoryService ; le modèle est un faux modèle scripté."""
import asyncio
import json

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

import deployer
import local
from agent_memoire import creer_agent


class FauxModele(BaseLlm):
    script: list = []
    vus: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        yield LlmResponse(content=self.script.pop(0))


def texte(t):
    return types.Content(role="model", parts=[types.Part(text=t)])


def appel(nom, **args):
    return types.Content(role="model", parts=[types.Part(
        function_call=types.FunctionCall(name=nom, args=args))])


def test_la_session_2_recoit_les_souvenirs_de_la_session_1():
    modele = FauxModele(model="faux", vus=[], script=[
        texte("Bonjour Camille, c'est noté : Nantes, MacBook."),
        appel("creer_ticket", sujet="MacBook ne démarre plus", priorite="haute"),
        texte("Ticket créé."),
    ])
    asyncio.run(local.main(creer_agent(model=modele)))
    # 2e session, 1er appel au modèle : PreloadMemoryTool a inséré les souvenirs dans la
    # requête, sous la forme d'un message <PAST_CONVERSATIONS> (ADK 2.10).
    requete_s2 = json.dumps([c.model_dump(mode="json") for c in modele.vus[1].contents])
    assert "PAST_CONVERSATIONS" in requete_s2 and "Nantes" in requete_s2
    # ... alors que la 1re session n'avait aucun souvenir.
    requete_s1 = json.dumps([c.model_dump(mode="json") for c in modele.vus[0].contents])
    assert "PAST_CONVERSATIONS" not in requete_s1


def test_creer_ticket_valide_la_priorite():
    modele = FauxModele(model="faux", vus=[], script=[
        appel("creer_ticket", sujet="écran", priorite="urgente"),
        texte("Priorité invalide."),
    ])
    runner = InMemoryRunner(agent=creer_agent(model=modele), app_name="t")
    asyncio.run(local.tour(runner, "u", "écran noir"))
    retour = json.dumps([c.model_dump(mode="json") for c in modele.vus[1].contents])
    assert "priorite doit valoir" in retour


def test_configuration_de_deploiement_sobre():
    cfg = deployer.configuration("gs://lab-agent-engine-memory-bank-test")
    assert cfg["min_instances"] == 0 and cfg["max_instances"] == 1
    assert cfg["resource_limits"] == {"cpu": "1", "memory": "1Gi"}
    assert cfg["labels"] == {"formation-lab": "agent-engine-memory-bank"}
    assert cfg["display_name"].startswith("lab-agent-engine-memory-bank")
    ttl = cfg["context_spec"]["memory_bank_config"]["ttl_config"]["default_ttl"]
    assert ttl == f"{30 * 24 * 3600}s"                    # souvenirs effacés après 30 jours
    assert "agent_memoire.py" in cfg["extra_packages"]
