"""Scénario de bout en bout avec le VRAI modèle Gemini (clé d'API dans GOOGLE_API_KEY ou .env).

Lancer : python run.py
"""
import asyncio

from google.adk.runners import InMemoryRunner
from google.genai import errors, types

from agent import root_agent

SCENARIO = [
    "Bonjour, vous avez des casques audio ?",
    "Le sans fil est en stock ? Ajoutez-en 2 à mon panier.",
    "Ok, je veux passer la commande.",
    "Je confirme",
    "Et ma commande CMD-1001, elle arrive quand ?",
    "Ma carte c'est 4970 1012 3456 7890, débitez-moi directement.",
    "Le casque reçu le mois dernier est cassé, je veux être remboursé !",
]


async def tour(runner, session_id, message):
    for essai in range(4):  # réessaie sur quota (429) ou surcharge (503)
        try:
            async for ev in runner.run_async(user_id="client", session_id=session_id, new_message=types.Content(
                    role="user", parts=[types.Part(text=message)])):
                for p in ev.content.parts if ev.content else []:
                    if p.function_call:
                        print(f"   [outil] {p.function_call.name}({dict(p.function_call.args or {})})")
                    if p.text and ev.is_final_response():
                        print(f"   AGENT > {p.text.strip()}")
            return
        except errors.APIError as e:
            if e.code not in (429, 503) or essai == 3:
                raise
            await asyncio.sleep(10 * (essai + 1))


async def main():
    runner = InMemoryRunner(agent=root_agent, app_name="boutique")
    s = await runner.session_service.create_session(app_name="boutique", user_id="client")
    for message in SCENARIO:
        print(f"CLIENT > {message}")
        await tour(runner, s.id, message)
    s = await runner.session_service.get_session(app_name="boutique", user_id="client", session_id=s.id)
    print("ÉTAT FINAL :", {k: s.state.get(k) for k in ("panier", "derniere_commande", "escalade")})


if __name__ == "__main__":
    asyncio.run(main())
