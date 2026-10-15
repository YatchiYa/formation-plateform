"""Lance le pipeline de bout en bout et affiche la trace.

python run_pipeline.py "Composants Arvenne"
"""
import asyncio
import logging
import sys
import time

from google.adk.runners import InMemoryRunner
from google.genai import types

from agent import construire_pipeline


async def due_diligence(fournisseur: str, model=None) -> dict:
    runner = InMemoryRunner(agent=construire_pipeline(model), app_name="due_diligence")
    session = await runner.session_service.create_session(app_name="due_diligence", user_id="acheteur")
    demande = types.Content(role="user", parts=[types.Part(text=f"Due diligence du fournisseur : {fournisseur}")])
    debut, passages = time.perf_counter(), 0
    async for ev in runner.run_async(user_id="acheteur", session_id=session.id, new_message=demande):
        for p in (ev.content.parts if ev.content else []):
            if p.function_call:
                print(f"[{ev.author}] appel outil {p.function_call.name}({dict(p.function_call.args or {})})")
            elif p.text and not p.thought and ev.is_final_response():
                print(f"[{ev.author}] {p.text.strip()[:90]!r}")
        if ev.author == "redacteur" and ev.is_final_response():
            passages += 1
    etat = (await runner.session_service.get_session(
        app_name="due_diligence", user_id="acheteur", session_id=session.id)).state
    await runner.close()
    return {"score": etat.get("score_risque"), "statut": etat.get("statut_relecture", "non approuvé"),
            "passages": passages, "duree_s": round(time.perf_counter() - debut, 1), "rapport": etat.get("rapport", "")}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s %(message)s")
    for nom in ("httpx", "google_adk", "google_genai"):
        logging.getLogger(nom).setLevel(logging.WARNING)
    r = asyncio.run(due_diligence(sys.argv[1] if len(sys.argv) > 1 else "Composants Arvenne"))
    print(f"\nScore : {r['score']}\nStatut : {r['statut']} après {r['passages']} passage(s) "
          f"de rédaction, en {r['duree_s']} s\n\n{r['rapport']}")
