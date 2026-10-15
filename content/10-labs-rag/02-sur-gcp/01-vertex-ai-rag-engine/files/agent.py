"""Agent ADK qui cherche dans le corpus RAG Engine avec l'outil VertexAiRagRetrieval.

    RAG_CORPUS=projects/…/locations/europe-west4/ragCorpora/… python agent.py "Ma question"
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
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from google.genai import types

from rag_engine_lab import cited_sources

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
RAG_CORPUS = os.environ.get("RAG_CORPUS", "")

# Avec un modèle Gemini, ADK n'appelle pas une fonction Python : il ajoute l'outil natif « retrieval »
# à la requête, et c'est Vertex AI qui interroge le corpus (vu dans le code d'ADK 2.10).
recherche_documents = VertexAiRagRetrieval(
    name="recherche_documents",
    description="Cherche dans les documents internes de Nimbus Conseil (RH, frais, sécurité, accueil).",
    rag_corpora=[RAG_CORPUS] if RAG_CORPUS else None,
    similarity_top_k=4,
    vector_distance_threshold=0.6,
)

root_agent = Agent(
    name="assistant_documentaire",
    # 429 (quota partagé) : jusqu'à 5 essais espacés au lieu d'échouer au premier refus.
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2)),
    instruction=(
        "Tu es l'assistant documentaire de Nimbus Conseil. Tu réponds en français, brièvement. "
        "Pour toute question sur les règles internes, appuie-toi sur les documents trouvés par "
        "recherche_documents et cite le nom du document. Si l'information n'y est pas, dis-le."
    ),
    tools=[recherche_documents],
)


async def ask(question: str) -> str:
    runner = InMemoryRunner(agent=root_agent, app_name="lab_rag_engine")
    s = await runner.session_service.create_session(app_name="lab_rag_engine", user_id="u")
    final = ""
    async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
            role="user", parts=[types.Part(text=question)])):
        if ev.is_final_response() and ev.content:
            final = "".join(p.text or "" for p in ev.content.parts)
            final += f"\n[sources citées : {cited_sources(ev.grounding_metadata)}]"
    return final.strip()


if __name__ == "__main__":
    if not RAG_CORPUS:
        sys.exit("Définissez RAG_CORPUS (nom complet affiché par `python rag_engine_lab.py setup`).")
    print(asyncio.run(ask(" ".join(sys.argv[1:]) or "Quel est le plafond d'un hôtel à Paris ?")))
