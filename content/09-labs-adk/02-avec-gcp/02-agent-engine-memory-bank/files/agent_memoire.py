"""Assistant support IT interne avec mémoire long terme (Memory Bank).

Le même objet `root_agent` tourne en local (mémoire en RAM) et sur Agent Engine
(mémoire Memory Bank) : seul le service de mémoire change, pas le code de l'agent.
"""
import os
import random

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.google_llm import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


def creer_ticket(sujet: str, priorite: str, tool_context: ToolContext) -> dict:
    """Crée un ticket de support IT (système fictif).

    Args:
        sujet: description courte du problème.
        priorite: 'basse', 'normale' ou 'haute'.
    """
    if priorite not in {"basse", "normale", "haute"}:
        return {"erreur": "priorite doit valoir 'basse', 'normale' ou 'haute'"}
    numero = f"IT-{random.randint(10000, 99999)}"
    tool_context.state["tickets"] = tool_context.state.get("tickets", []) + [numero]
    return {"numero": numero, "sujet": sujet, "priorite": priorite, "statut": "ouvert"}


async def memoriser(callback_context: CallbackContext) -> None:
    """after_agent_callback : envoie la conversation au service de mémoire.

    En local : InMemoryMemoryService (copie brute, recherche par mots-clés).
    Sur Agent Engine : Memory Bank extrait des faits durables, en arrière-plan.
    """
    await callback_context.add_session_to_memory()


def creer_agent(model=None) -> Agent:
    return Agent(
        name="assistant_it",
        model=model or Gemini(model=MODEL, retry_options=types.HttpRetryOptions(
            initial_delay=2, attempts=6)),
        description="Assistant de support informatique interne, avec mémoire.",
        instruction="""Tu es l'assistant de support informatique interne d'une entreprise
fictive. Tu réponds en français, en 3 phrases au plus.
- Utilise ce que tu sais déjà de la personne (souvenirs fournis plus haut, s'il y en a) :
  site, équipement, préférences. Ne redemande pas une information déjà connue.
- Si la personne signale une panne, crée un ticket avec creer_ticket, puis donne son numéro.
- Ne demande jamais de mot de passe ni de code d'accès.""",
        tools=[PreloadMemoryTool(), creer_ticket],
        after_agent_callback=memoriser,
    )


root_agent = creer_agent()
