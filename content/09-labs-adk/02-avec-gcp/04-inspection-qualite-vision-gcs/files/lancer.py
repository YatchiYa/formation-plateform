"""Lance une inspection complète puis compare au fichier verite_terrain.json.

Usage : BUCKET=lab-inspection-qualite-xxx python lancer.py
"""
import asyncio
import json
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.genai import types

import agent


def evaluer(resultats: dict[str, dict], verite: dict[str, str]) -> dict:
    """Exactitude du défaut, et rejets manqués (le pire cas : une pièce défectueuse acceptée)."""
    justes = sum(resultats.get(f"images/{nom}", {}).get("defaut") == d for nom, d in verite.items())
    manques = [n for n, d in verite.items() if d != "aucun" and resultats.get(f"images/{n}", {}).get("conforme")]
    return {"exactitude": justes / len(verite), "defectueuses_acceptees": manques}


async def main() -> None:
    runner = InMemoryRunner(agent=agent.root_agent, app_name="inspection")
    s = await runner.session_service.create_session(app_name="inspection", user_id="atelier")
    msg = types.Content(role="user", parts=[types.Part(text="Lance l'inspection du lot du jour.")])
    async for ev in runner.run_async(user_id="atelier", session_id=s.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call:
                print("OUTIL ", p.function_call.name, dict(p.function_call.args or {}))
            if p.text and ev.is_final_response():
                print("\nSYNTHESE\n" + p.text.strip())
    verite = json.loads(Path("verite_terrain.json").read_text(encoding="utf-8"))
    print("\nEVALUATION", evaluer(agent._resultats, verite))


if __name__ == "__main__":
    asyncio.run(main())
