"""Lance l'agent SRE. Usage : python lancer.py [journal] [heures]   (journal vide = tout le projet)"""
import asyncio
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

import agent


async def main(journal: str, heures: int) -> None:
    runner = InMemoryRunner(agent=agent.root_agent, app_name="sre")
    s = await runner.session_service.create_session(app_name="sre", user_id="astreinte")
    cible = f"du journal {journal}" if journal else "de tout le projet"
    question = f"Analyse les erreurs {cible} sur les {heures} dernières heures et propose des remédiations."
    async for ev in runner.run_async(user_id="astreinte", session_id=s.id,
                                     new_message=types.Content(role="user", parts=[types.Part(text=question)])):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call:
                print("OUTIL ", p.function_call.name, dict(p.function_call.args or {}))
            if p.function_response:
                r = p.function_response.response or {}
                print("  ->", {k: r[k] for k in ("entrees_lues", "par_severite") if k in r},
                      f"{len(r.get('correlations', []))} corrélation(s)" if "correlations" in r else "")
            if p.text and ev.is_final_response():
                print("\n" + p.text.strip())


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "", int(sys.argv[2]) if len(sys.argv) > 2 else 1))
