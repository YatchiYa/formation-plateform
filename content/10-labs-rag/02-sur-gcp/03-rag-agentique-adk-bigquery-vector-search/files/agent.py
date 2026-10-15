"""Agent ADK « RAG agentique » : il décide s'il faut chercher, reformule, choisit les filtres SQL.

    python agent.py "Je suis nouveau, combien de jours de télétravail ai-je droit ?"
"""

import asyncio
import os
import sys
import warnings

from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.genai import types

import bq_rag

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


MAX_RECHERCHES = 2  # par question : la consigne seule ne suffit pas (vu : 3 recherches pour une info absente)


def rechercher_documents(requete: str, tool_context: ToolContext, categorie: str = "", annee_min: int = 0) -> dict:
    """Recherche sémantique dans les documents internes de Nimbus Conseil (table BigQuery).

    Args:
        requete: mots-clés précis reformulés à partir de la question (pas la question brute).
        categorie: "rh", "finance" ou "securite" si le domaine est évident, sinon "" (toutes).
        annee_min: année minimale du document (ex. 2026 pour la version en vigueur), 0 = pas de filtre.

    Returns:
        Les extraits les plus proches, avec titre, année et distance (plus petit = plus proche).
    """
    n = tool_context.state.get("temp:recherches", 0) + 1  # « temp: » = remis à zéro à chaque question
    tool_context.state["temp:recherches"] = n
    if n > MAX_RECHERCHES:
        return {"erreur": f"Limite de {MAX_RECHERCHES} recherches atteinte : réponds avec ce que tu as."}
    try:
        rows = bq_rag.search(requete, categorie or None, annee_min or None)
    except ValueError as e:  # catégorie inventée par le modèle : on lui explique, il corrigera
        return {"erreur": str(e)}
    return {"resultats": [{k: r[k] for k in ("titre", "annee", "distance", "texte")} for r in rows]}


root_agent = Agent(
    name="assistant_rag_bigquery",
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2)),
    instruction="""Tu es l'assistant documentaire de Nimbus Conseil (société fictive). Réponds en français, brièvement.

1. Salutation, question sur toi ou calcul simple : réponds SANS chercher.
2. Sinon appelle rechercher_documents avec une requête reformulée en mots-clés, et des filtres :
   - categorie si le domaine est clair (télétravail, accueil -> rh ; frais, remboursement -> finance ;
     mots de passe, incident -> securite) ;
   - annee_min=2026 quand on demande la règle actuelle (par défaut), 0 si on demande l'historique.
3. Si les extraits ne suffisent pas, refais AU PLUS une recherche (autres mots, ou sans filtre).
4. Réponds uniquement avec les extraits, cite le titre du document entre parenthèses.
   Si l'information n'y est pas, dis-le sans inventer.""",
    tools=[rechercher_documents],
)


async def ask(question: str) -> str:
    runner = InMemoryRunner(agent=root_agent, app_name="lab_rag_bq")
    s = await runner.session_service.create_session(app_name="lab_rag_bq", user_id="u")
    final = ""
    async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
            role="user", parts=[types.Part(text=question)])):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call:
                print("  OUTIL", p.function_call.name, dict(p.function_call.args))
            if p.text and ev.is_final_response():
                final += p.text
    return final.strip()


if __name__ == "__main__":
    print(asyncio.run(ask(" ".join(sys.argv[1:]) or "Combien de jours de télétravail par semaine ?")))
