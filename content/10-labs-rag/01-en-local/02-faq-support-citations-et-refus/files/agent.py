"""Agent ADK du SAV : un seul outil, rechercher_faq, et un garde-fou de citations après coup.

Usage : python agent.py "Ma batterie ne charge plus"
"""
import asyncio
import os
import sys

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

import faq_rag

_index = None


def index():
    global _index
    if _index is None:
        _index = faq_rag.FAQIndex()
    return _index


def rechercher_faq(question: str) -> dict:
    """Cherche dans la FAQ officielle de la boutique Roue Libre les entrées qui répondent à la question.

    Args:
        question: la question du client, reformulée en une phrase claire.

    Returns:
        {"status": "ok", "resultats": [{"id", "question", "reponse", "score"}]} ou
        {"status": "hors_perimetre"} si aucune entrée n'est assez proche.
    """
    return faq_rag.rechercher(index(), question)


INSTRUCTION = f"""Tu es l'assistant du service client de la boutique de vélos électriques Roue Libre.
Règles strictes :
1. Pour toute question du client, appelle d'abord l'outil rechercher_faq.
2. Réponds en français, en 1 à 3 phrases, UNIQUEMENT avec le contenu des résultats, et cite chaque
   identifiant utilisé entre crochets, par exemple [FAQ-02].
3. Si le statut est hors_perimetre, ou si les résultats ne répondent pas vraiment à la question,
   commence ta réponse exactement par "{faq_rag.REFUS}" et propose le formulaire de contact.
4. N'invente jamais un délai, un prix ou une politique qui n'est pas dans les résultats.
5. Pas de déduction, de conseil ni de formule de politesse qui ajoute une information : si le client
   demande « est-ce normal ? », rappelle la règle de la FAQ et laisse-le conclure.
6. N'utilise que les résultats qui répondent à la question ; ignore les autres."""

agent = Agent(name="sav_roue_libre", model=os.environ.get("MODEL", faq_rag.MODEL),
              instruction=INSTRUCTION, tools=[rechercher_faq])


async def ask(question: str) -> dict:
    """Une question, une session neuve. Renvoie la réponse finale, les id vus et le refus éventuel."""
    runner = InMemoryRunner(agent=agent, app_name="sav")
    s = await runner.session_service.create_session(app_name="sav", user_id="client")
    final, ids, appels = "", [], 0
    msg = types.Content(role="user", parts=[types.Part(text=question)])
    async for ev in runner.run_async(user_id="client", session_id=s.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call:
                appels += 1
            if p.function_response and p.function_response.response:
                ids += [r["id"] for r in p.function_response.response.get("resultats", [])]
            if p.text and ev.is_final_response():
                final += p.text
    final = final.strip()
    if not faq_rag.verifier_citations(final, ids):  # le modèle a cité un id non récupéré, ou rien
        faq_rag.log_non_couverte(question, None)
        return {"answer": faq_rag.MESSAGE_REFUS, "refus": True, "ids": ids, "appels_outil": appels,
                "raison": "citation invalide"}
    refus = final.startswith(faq_rag.REFUS)
    if refus and ids:  # l'outil a trouvé des entrées, mais aucune ne répondait : à signaler aussi
        faq_rag.log_non_couverte(question, None)
    return {"answer": final, "refus": refus, "ids": ids,
            "appels_outil": appels, "raison": None}


if __name__ == "__main__":
    r = asyncio.run(ask(sys.argv[1]))
    print(r["answer"], f"\n  (outil appelé {r['appels_outil']} fois, id récupérés : {r['ids']})")
