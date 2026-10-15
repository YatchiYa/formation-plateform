"""L'agent : répond uniquement à partir des documents indexés (Drive + dépôts), en citant ses sources."""

import logging
import os

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

import kit


def rechercher_documents(question: str) -> dict:
    """Cherche dans les documents de l'entreprise (Google Drive et fichiers déposés).

    Args:
        question: la question ou les mots-clés à chercher, reformulés pour être précis.

    Returns:
        Les extraits les plus pertinents, chacun avec le titre et le lien du document.
    """
    try:
        resultats = kit.search(question)
    except Exception as e:  # une panne de recherche ne doit pas faire tomber la conversation
        logging.exception("recherche en échec")
        return {"erreur": f"La recherche dans les documents a échoué ({type(e).__name__}). Dis-le à l'utilisateur."}
    return {"resultats": resultats} if resultats else {"resultats": [], "note": "Aucun document ne correspond."}


MODEL = os.getenv("MODEL", "gemini-2.5-flash")
# Réflexion « basse » : sinon, quand l'info n'existe pas, Gemini 3.5 réfléchit ~200 s entre deux recherches (vérifié).
# (thinking_level n'existe que pour Gemini 3 ; les 2.x gardent leur réglage par défaut.)
THINKING = (types.ThinkingConfig(thinking_level=os.getenv("THINKING_LEVEL", "low").upper())
            if MODEL.startswith("gemini-3") else None)

RETRY = types.HttpRetryOptions(attempts=6, initial_delay=2, max_delay=30)

root_agent = Agent(
    name="assistant_documents",
    # 429 (quota partagé saturé) fréquents sur un projet neuf (vérifié) : jusqu'à 6 essais espacés.
    model=Gemini(model=MODEL, retry_options=RETRY),
    description="Répond aux questions à partir des documents Google Drive et des fichiers déposés, avec citations.",
    instruction="""Tu es l'assistant documentaire de l'équipe. Tu réponds en français, de façon précise et concise.

Règles :
1. Pour toute question sur l'entreprise, ses documents, chiffres, règles ou personnes, appelle d'abord
   `rechercher_documents`. Si les extraits ne répondent pas, réessaie AU PLUS 2 fois avec d'autres mots,
   puis conclus.
2. Réponds UNIQUEMENT avec ce que disent les extraits. Si la réponse n'y est pas, dis-le clairement
   (« Je ne trouve pas cette information dans les documents. ») et n'invente rien.
3. Cite chaque information avec un lien markdown vers sa source : [titre](lien). Termine par une ligne
   « Sources : » listant les documents utilisés.
4. Si des documents se contredisent, signale-le en citant les deux.
5. Pour une simple salutation ou une question sur ton fonctionnement, réponds sans chercher.""",
    tools=[rechercher_documents],
    # 30 s max par tentative : un appel bloqué (vu : 87 s puis annulation) est relancé au lieu d'attendre.
    generate_content_config=types.GenerateContentConfig(thinking_config=THINKING,
                                                        http_options=types.HttpOptions(timeout=30_000, retry_options=RETRY)),
)
