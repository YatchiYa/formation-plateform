"""Tests SANS clé d'API : scores, jeu de tickets, et vrai Runner ADK multi-agents
(routeur -> transfert -> spécialiste) piloté par de faux modèles.

Lancer : pytest -q
"""
import asyncio
import json

from google.adk.agents import Agent
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

import agent as support
from evaluer import scores


class FauxModele(BaseLlm):
    reponses: list
    appels: int = 0

    async def generate_content_async(self, llm_request, stream=False):
        self.appels += 1
        yield self.reponses.pop(0)


def appel(nom, **args):
    return LlmResponse(content=types.Content(role="model", parts=[
        types.Part(function_call=types.FunctionCall(name=nom, args=args))]))


def test_jeu_de_tickets_equilibre():
    tickets = json.load(open("tickets.json", encoding="utf-8"))
    assert len(tickets) == 20 and len({t["id"] for t in tickets}) == 20
    assert {t["equipe"] for t in tickets} == {"facturation", "technique", "compte"}
    assert {t["priorite"] for t in tickets} <= set(support.PRIORITES)


def test_scores():
    r = [{"attendu": "compte", "obtenu": "compte", "priorite_attendue": "P1", "priorite": "P1"},
         {"attendu": "technique", "obtenu": "facturation", "priorite_attendue": "P2", "priorite": "P1"}]
    assert scores(r) == {"routage": 0.5, "priorite": 0.5, "confusions": {"technique->facturation": 1}}


def test_specialistes_ne_renvoient_pas_le_ticket():
    for a in support.root_agent.sub_agents:
        assert a.disallow_transfer_to_parent and a.disallow_transfer_to_peers


def test_transfert_puis_triage_en_etat():
    faux_routeur = FauxModele(model="faux", reponses=[appel("transfer_to_agent", agent_name="technique")])
    faux_tech = FauxModele(model="faux", reponses=[
        appel("etat_des_services"),
        appel("enregistrer_triage", priorite="P2", resume="Export PDF en panne",
              reponse_proposee="Nous avons identifié la panne de l'export PDF.")])
    tech = support.technique.clone(update={"model": faux_tech})
    routeur = Agent(name="routeur_support", model=faux_routeur, instruction="x",
                    sub_agents=[tech, support.facturation.clone(), support.compte.clone()])

    async def run():
        runner = InMemoryRunner(agent=routeur, app_name="t")
        s = await runner.session_service.create_session(app_name="t", user_id="u")
        auteurs = []
        async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
                role="user", parts=[types.Part(text="L'export PDF plante")])):
            auteurs.append(ev.author)
        s = await runner.session_service.get_session(app_name="t", user_id="u", session_id=s.id)
        return auteurs, s.state

    auteurs, etat = asyncio.run(run())
    assert "technique" in auteurs
    assert etat["triage"]["equipe"] == "technique" and etat["triage"]["priorite"] == "P2"
    # skip_summarization : le spécialiste s'arrête après enregistrer_triage (2 appels, pas 3).
    assert faux_tech.appels == 2 and faux_tech.reponses == []


def test_priorite_invalide_refusee():
    class Ctx:
        state, agent_name = {}, "compte"
    assert "erreur" in support.enregistrer_triage("urgent", "x", "y", Ctx())
