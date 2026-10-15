"""Agent de recherche web avec ancrage Google Search (Google ADK 2.10, clé d'API Gemini).

Contrainte ADK / API Gemini : l'outil intégré google_search ne se combine pas
librement avec des outils « fonction » dans le même agent. On l'isole donc dans
un sous-agent `chercheur_web`, exposé à l'agent principal comme un outil (AgentTool).
"""
import datetime
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import AgentTool, google_search
from google.genai import types

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")


def memoriser_sources(callback_context, llm_response):
    """Après chaque réponse du chercheur : relève les sources réellement utilisées
    (métadonnées d'ancrage renvoyées par Google Search), les numérote dans l'état
    de session et les ajoute à la fin du texte pour que l'agent principal puisse les citer."""
    gm = llm_response.grounding_metadata
    if not gm or not gm.grounding_chunks or not llm_response.content:
        return None
    sources = list(callback_context.state.get("sources", []))
    lignes = []
    for chunk in gm.grounding_chunks:
        if not chunk.web or not chunk.web.uri:
            continue
        source = {"titre": chunk.web.title or chunk.web.domain or "source", "url": chunk.web.uri}
        if source not in sources:
            sources.append(source)
        lignes.append(f"[{sources.index(source) + 1}] {source['titre']}")
    callback_context.state["sources"] = sources
    llm_response.content.parts.append(types.Part(text="\n\nSources : " + " ; ".join(dict.fromkeys(lignes))))
    return llm_response


def bibliographie(sources: list) -> str:
    """Fonction pure : liste Markdown numérotée des sources."""
    return "\n".join(f"{i}. [{s['titre']}]({s['url']})" for i, s in enumerate(sources, 1))


def date_du_jour() -> dict:
    """Renvoie la date du jour, pour situer les questions d'actualité."""
    return {"date": datetime.date.today().isoformat()}


chercheur = Agent(
    name="chercheur_web",
    model=MODEL,
    description="Cherche sur le web (Google Search) et renvoie des faits datés et sourcés sur UNE question précise.",
    instruction=("Tu fais une recherche Google sur la question reçue et tu réponds en français par 3 à 6 faits "
                 "précis, chacun avec sa date ou sa période. Pas d'opinion, pas de remplissage."),
    tools=[google_search],  # seul outil de cet agent : c'est la règle
    after_model_callback=memoriser_sources,
)

INSTRUCTION = """Tu es un analyste de veille. Tu réponds en français.
1. Appelle date_du_jour.
2. Découpe la question de l'utilisateur en 2 ou 3 sous-questions précises.
3. Appelle chercheur_web une fois par sous-question.
4. Rédige un rapport Markdown avec exactement ces sections :
   ## Synthèse (3 phrases)
   ## Points clés (puces ; chaque puce finit par le ou les numéros de source, ex. [1][3])
   ## Ce qui reste incertain
N'utilise QUE les faits renvoyés par chercheur_web et ne cite QUE les numéros [n] qu'il donne.
Ne recopie pas la liste des sources : elle est ajoutée automatiquement."""

root_agent = Agent(
    name="analyste_recherche",
    model=MODEL,
    description="Rapport de veille structuré et sourcé à partir de recherches web.",
    instruction=INSTRUCTION,
    tools=[date_du_jour, AgentTool(agent=chercheur)],
)
