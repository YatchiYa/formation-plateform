"""Recherche réelle (Gemini + Google Search). Écrit le rapport dans rapport.md.

Lancer : python run.py "Votre question d'actualité"
"""
import asyncio
import sys

from google.adk.runners import InMemoryRunner
from google.genai import errors, types

from agent import bibliographie, root_agent

QUESTION = "Quelles sont les dernières nouveautés de Google Agent Development Kit (ADK) ?"


async def main(question):
    runner = InMemoryRunner(agent=root_agent, app_name="veille")
    for essai in range(4):
        s = await runner.session_service.create_session(app_name="veille", user_id="moi")
        rapport = ""
        try:
            async for ev in runner.run_async(user_id="moi", session_id=s.id, new_message=types.Content(
                    role="user", parts=[types.Part(text=question)])):
                for p in ev.content.parts if ev.content else []:
                    if p.function_call:
                        print(f"[outil] {p.function_call.name}({dict(p.function_call.args or {})})")
                    if p.text and ev.is_final_response() and ev.author == root_agent.name:
                        rapport += p.text
            break
        except errors.APIError as e:  # quota (429) ou surcharge (503) : on attend et on recommence
            if e.code not in (429, 503) or essai == 3:
                raise
            await asyncio.sleep(15 * (essai + 1))
    s = await runner.session_service.get_session(app_name="veille", user_id="moi", session_id=s.id)
    sources = s.state.get("sources", [])
    texte = f"# {question}\n\n{rapport.strip()}\n\n## Sources\n{bibliographie(sources)}\n"
    open("rapport.md", "w", encoding="utf-8").write(texte)
    print(texte)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else QUESTION))
