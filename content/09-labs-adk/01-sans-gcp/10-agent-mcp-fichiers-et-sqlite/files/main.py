"""Pose une ou plusieurs questions à l'agent et affiche les appels d'outils MCP.

    python main.py "Quel client pro a le plus dépensé en septembre ?"
    python main.py            # questions de démonstration
"""
import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from agent import root_agent  # noqa: E402

DEMO = [
    "Quel client professionnel a le plus dépensé en septembre 2026 (montant TTC) ?",
    "Sacha Bernard veut retourner sa commande 105. Est-ce possible ? Et peux-tu l'annuler ?",
]


async def demander(runner: InMemoryRunner, session_id: str, question: str) -> str:
    for essai in range(4):
        try:
            final = ""
            msg = types.Content(role="user", parts=[types.Part(text=question)])
            async for ev in runner.run_async(user_id="u", session_id=session_id, new_message=msg):
                for p in (ev.content.parts if ev.content else []):
                    if p.function_call:
                        print(f"   [MCP] {p.function_call.name} {dict(p.function_call.args)}")
                    if p.text and ev.is_final_response():
                        final += p.text
            return final.strip()
        except Exception as e:
            if essai == 3 or not any(c in str(e) for c in ("429", "503", "UNAVAILABLE")):
                raise
            await asyncio.sleep(10 * (essai + 1))


async def main() -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="mcp_lab")
    try:
        for q in sys.argv[1:] or DEMO:
            s = await runner.session_service.create_session(app_name="mcp_lab", user_id="u")
            print(f"\nQUESTION > {q}")
            print(f"AGENT > {await demander(runner, s.id, q)}")
    finally:
        await runner.close()  # ferme proprement les sous-processus MCP


if __name__ == "__main__":
    asyncio.run(main())
