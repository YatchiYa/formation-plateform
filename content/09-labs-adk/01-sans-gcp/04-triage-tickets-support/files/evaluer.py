"""Évaluation réelle du routage sur les 20 tickets fictifs de tickets.json.

Lancer : python evaluer.py            (écrit resultats.json)
"""
import asyncio
import json
from collections import Counter

from google.adk.runners import InMemoryRunner
from google.genai import errors, types

from agent import root_agent


async def trier(runner, ticket):
    """Un ticket = une nouvelle session. Renvoie l'équipe qui a traité, la priorité, la réponse."""
    for essai in range(4):
        s = await runner.session_service.create_session(app_name="triage", user_id="support")
        try:
            async for _ in runner.run_async(user_id="support", session_id=s.id, new_message=types.Content(
                    role="user", parts=[types.Part(text=ticket["texte"])])):
                pass
            break
        except errors.APIError as e:  # 429 / 503 : on attend puis on recommence
            if e.code not in (429, 503) or essai == 3:
                raise
            await asyncio.sleep(15 * (essai + 1))
    s = await runner.session_service.get_session(app_name="triage", user_id="support", session_id=s.id)
    triage = s.state.get("triage") or {"equipe": "aucune", "priorite": "-", "reponse_proposee": ""}
    return {"id": ticket["id"], "attendu": ticket["equipe"], "obtenu": triage["equipe"],
            "priorite_attendue": ticket["priorite"], "priorite": triage["priorite"],
            "reponse_proposee": triage["reponse_proposee"]}


def scores(resultats):
    """Fonction pure : exactitude du routage, de la priorité, et confusions."""
    n = len(resultats)
    return {
        "routage": sum(r["attendu"] == r["obtenu"] for r in resultats) / n,
        "priorite": sum(r["priorite_attendue"] == r["priorite"] for r in resultats) / n,
        "confusions": dict(Counter(f"{r['attendu']}->{r['obtenu']}" for r in resultats if r["attendu"] != r["obtenu"])),
    }


async def main():
    tickets = json.load(open("tickets.json", encoding="utf-8"))
    runner = InMemoryRunner(agent=root_agent, app_name="triage")
    resultats = []
    for t in tickets:
        r = await trier(runner, t)
        resultats.append(r)
        ok = "OK " if r["attendu"] == r["obtenu"] else "ERR"
        print(f"{ok} {r['id']} attendu={r['attendu']:<11} obtenu={r['obtenu']:<11} "
              f"prio {r['priorite_attendue']}/{r['priorite']}")
    json.dump(resultats, open("resultats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    await runner.close()
    s = scores(resultats)
    print(f"\nRoutage : {s['routage']:.0%}   Priorité : {s['priorite']:.0%}   Confusions : {s['confusions'] or 'aucune'}")


if __name__ == "__main__":
    asyncio.run(main())
