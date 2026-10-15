"""Partie locale : deux sessions successives, la 2e se souvient de la 1re.

    python local.py
Mémoire : InMemoryMemoryService (dans la RAM du processus, perdue à l'arrêt).
"""
import asyncio

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv()
from agent_memoire import root_agent  # noqa: E402  (après load_dotenv : MODEL)

SESSION_1 = "Bonjour, je suis Camille, je travaille sur le site de Nantes avec un MacBook."
SESSION_2 = "Mon ordinateur ne démarre plus depuis ce matin. Tu peux créer un ticket ?"


async def tour(runner, user_id: str, texte: str) -> str:
    """Une question dans une NOUVELLE session ; renvoie la réponse finale."""
    s = await runner.session_service.create_session(app_name=runner.app_name, user_id=user_id)
    reponse = ""
    async for ev in runner.run_async(user_id=user_id, session_id=s.id, new_message=types.Content(
            role="user", parts=[types.Part(text=texte)])):
        if ev.is_final_response() and ev.content and ev.content.parts:
            reponse = "".join(p.text or "" for p in ev.content.parts)
    return reponse


async def main(agent=root_agent):
    runner = InMemoryRunner(agent=agent, app_name="assistant_it")
    print("Session 1 >", SESSION_1)
    print("Assistant <", await tour(runner, "camille", SESSION_1))
    print("Session 2 >", SESSION_2)
    reponse = await tour(runner, "camille", SESSION_2)
    print("Assistant <", reponse)
    return reponse


if __name__ == "__main__":
    asyncio.run(main())
