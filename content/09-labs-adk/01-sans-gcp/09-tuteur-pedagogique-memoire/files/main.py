"""Lance le tuteur avec une mémoire SQLite.

  python main.py --user alice              # nouvelle session (la progression « user: » est conservée)
  python main.py --user alice --reprendre  # reprend la dernière session (historique compris)
  python main.py --user alice --demo       # élève simulé par un 2e appel Gemini (test de bout en bout)
"""
import argparse
import asyncio
import os

from dotenv import load_dotenv
from google import genai
from google.adk.runners import Runner
from google.adk.sessions.sqlite_session_service import SqliteSessionService
from google.genai import types

load_dotenv()
from agent import APP_NAME, root_agent  # noqa: E402  (après load_dotenv pour lire MODEL)

DB = os.environ.get("TUTEUR_DB", "tuteur.db")


async def tour(runner: Runner, user: str, session_id: str, texte: str) -> str:
    """Envoie un message, affiche les appels d'outils, renvoie la réponse finale (avec réessais 429/503)."""
    for essai in range(4):
        try:
            final = ""
            msg = types.Content(role="user", parts=[types.Part(text=texte)])
            async for ev in runner.run_async(user_id=user, session_id=session_id, new_message=msg):
                for p in (ev.content.parts if ev.content else []):
                    if p.function_call:
                        print(f"   [outil] {p.function_call.name} {dict(p.function_call.args)}")
                    if p.text and ev.is_final_response():
                        final += p.text
            return final.strip()
        except Exception as e:  # erreurs réseau / quota : on attend et on réessaie
            if essai == 3 or not any(c in str(e) for c in ("429", "503", "UNAVAILABLE")):
                raise
            await asyncio.sleep(10 * (essai + 1))


def eleve_simule(question: str, juste: bool) -> str:
    """Un « faux élève » : un appel Gemini direct qui répond juste ou faux exprès."""
    consigne = "correctement" if juste else "en faisant une erreur typique de débutant"
    client = genai.Client()  # garder une référence : sinon le client est fermé avant la requête
    r = client.models.generate_content(
        model=os.environ.get("MODEL", "gemini-3.5-flash"),
        contents=f"Tu joues un élève. Réponds en une ou deux phrases, {consigne}, "
                 f"à la DERNIÈRE question de ce message du tuteur :\n{question}")
    return r.text.strip()


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="eleve-demo")
    ap.add_argument("--reprendre", action="store_true")
    ap.add_argument("--demo", nargs="*", metavar="JUSTE",
                    help="ex. --demo 1 1 1 0 : réponses simulées justes (1) ou fausses (0)")
    args = ap.parse_args()

    service = SqliteSessionService(DB)
    runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=service)
    sessions = (await service.list_sessions(app_name=APP_NAME, user_id=args.user)).sessions
    if args.reprendre and sessions:
        session = sessions[-1]  # triées de la plus ancienne à la plus récente
        print(f"Reprise de la session {session.id}")
    else:
        session = await service.create_session(app_name=APP_NAME, user_id=args.user)
        print(f"Nouvelle session {session.id} ({len(sessions)} session(s) précédente(s))")

    if args.demo is not None:
        reponse = await tour(runner, args.user, session.id, "Salut ! Je veux progresser en Python.")
        print(f"TUTEUR > {reponse}\n")
        for juste in [x == "1" for x in args.demo]:
            texte = eleve_simule(reponse, juste)
            print(f"ÉLÈVE ({'juste' if juste else 'faux'}) > {texte}")
            reponse = await tour(runner, args.user, session.id, texte)
            print(f"TUTEUR > {reponse}\n")
    else:
        while (texte := input("VOUS > ").strip()) not in ("", "quit", "exit"):
            print(f"TUTEUR > {await tour(runner, args.user, session.id, texte)}\n")

    fin = await service.get_session(app_name=APP_NAME, user_id=args.user, session_id=session.id)
    print("Progression enregistrée :", fin.state.get("user:progression"))


if __name__ == "__main__":
    asyncio.run(main())
