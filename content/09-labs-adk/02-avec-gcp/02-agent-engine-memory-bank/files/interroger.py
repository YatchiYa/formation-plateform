"""Interroge l'agent déployé : session 1 (se présenter), souvenirs générés, session 2.

    python interroger.py
"""
import asyncio
import json
import time

import vertexai

from deployer import ETAT, PROJET, REGION
from local import SESSION_1, SESSION_2

UTILISATEUR = "camille"


async def tour(distant, texte: str) -> str:
    session = await distant.async_create_session(user_id=UTILISATEUR)
    morceaux = []
    async for ev in distant.async_stream_query(user_id=UTILISATEUR, session_id=session["id"],
                                               message=texte):
        for part in (ev.get("content") or {}).get("parts", []):
            if part.get("function_call"):
                print("   [outil]", part["function_call"]["name"], part["function_call"]["args"])
            if part.get("text"):
                morceaux.append(part["text"])
    return "".join(morceaux)


def souvenirs(client, nom: str) -> list[str]:
    return [m.fact for m in client.agent_engines.memories.list(name=nom)]


async def main():
    nom = json.loads(ETAT.read_text())["agent_engine"]
    client = vertexai.Client(project=PROJET, location=REGION)
    distant = client.agent_engines.get(name=nom)

    print("Session 1 >", SESSION_1)
    print("Assistant <", await tour(distant, SESSION_1))

    # La génération des souvenirs est asynchrone, côté Memory Bank : on attend qu'ils arrivent.
    for _ in range(18):
        faits = souvenirs(client, nom)
        if faits:
            break
        time.sleep(10)
    print("Souvenirs dans Memory Bank :", faits)

    print("Session 2 >", SESSION_2)
    print("Assistant <", await tour(distant, SESSION_2))


if __name__ == "__main__":
    asyncio.run(main())
