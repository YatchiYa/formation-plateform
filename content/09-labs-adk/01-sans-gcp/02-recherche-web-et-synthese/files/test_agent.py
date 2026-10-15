"""Tests SANS clé d'API : callback de sources, structure des agents, et vrai Runner
(agent principal -> AgentTool -> chercheur) piloté par de faux modèles.

Lancer : pytest -q
"""
import asyncio

from google.adk.agents import Agent
from google.adk.models import BaseLlm, LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, google_search
from google.genai import types

import agent as veille


class FauxModele(BaseLlm):
    reponses: list
    vus: list = []  # requêtes reçues, pour vérifier ce qu'ADK envoie au modèle

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        yield self.reponses.pop(0)


def ancre(texte, *sites):
    """Réponse comme celles de Gemini + Google Search : texte + métadonnées d'ancrage."""
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=texte)]),
        grounding_metadata=types.GroundingMetadata(grounding_chunks=[
            types.GroundingChunk(web=types.GroundingChunkWeb(title=t, uri=f"https://{t}/page")) for t in sites]))


def test_structure_respecte_la_contrainte_google_search():
    assert veille.chercheur.tools == [google_search]          # outil intégré seul dans son agent
    assert any(isinstance(t, AgentTool) for t in veille.root_agent.tools)


def test_bibliographie():
    assert veille.bibliographie([{"titre": "a.org", "url": "https://a.org"}]) == "1. [a.org](https://a.org)"


def test_pipeline_complet_avec_faux_modeles():
    faux_chercheur = FauxModele(model="gemini-faux", reponses=[
        ancre("Fait A (2026).", "a.org", "b.org"), ancre("Fait B (2025).", "b.org", "c.org")])
    chercheur = Agent(name="chercheur_web", model=faux_chercheur, instruction="x",
                      tools=[google_search], after_model_callback=veille.memoriser_sources)

    def appel(nom, **args):
        return LlmResponse(content=types.Content(role="model", parts=[
            types.Part(function_call=types.FunctionCall(name=nom, args=args))]))

    principal = Agent(name="analyste", model=FauxModele(model="gemini-faux", reponses=[
        appel("chercheur_web", request="q1"), appel("chercheur_web", request="q2"),
        LlmResponse(content=types.Content(role="model", parts=[types.Part(text="## Synthèse\nA [1], B [3].")]))]),
        instruction="x", tools=[veille.date_du_jour, AgentTool(agent=chercheur)])

    async def run():
        runner = InMemoryRunner(agent=principal, app_name="t")
        s = await runner.session_service.create_session(app_name="t", user_id="u")
        retours = []
        async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
                role="user", parts=[types.Part(text="question")])):
            for p in ev.content.parts if ev.content else []:
                if p.function_response:
                    retours.append(p.function_response.response["result"])
        s = await runner.session_service.get_session(app_name="t", user_id="u", session_id=s.id)
        return retours, s.state

    retours, etat = asyncio.run(run())
    # Les sources sont dédoublonnées et numérotées d'une recherche à l'autre...
    assert [s["titre"] for s in etat["sources"]] == ["a.org", "b.org", "c.org"]
    # ... et le texte renvoyé à l'agent principal porte les bons numéros.
    assert retours[0].endswith("Sources : [1] a.org ; [2] b.org")
    assert retours[1].endswith("Sources : [2] b.org ; [3] c.org")
    # L'outil intégré a bien été transmis au modèle du chercheur sous sa forme native.
    assert any(t.google_search for t in faux_chercheur.vus[0].config.tools)
