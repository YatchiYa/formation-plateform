"""Analyse réelle de ventes.csv : rapport (rapport.md), graphique (PNG) et contrôle des chiffres.

Lancer : python run.py [chemin.csv]
"""
import asyncio
import re
import sys

import pandas as pd
from google.adk.runners import InMemoryRunner
from google.genai import errors

from agent import construire_message, root_agent

QUESTION = "Analyse ces ventes 2025 : statistiques, tendances, un graphique et tes recommandations."


def reference(chemin_csv: str) -> dict:
    """Les chiffres attendus, calculés par nous avec pandas : la « vérité terrain »."""
    d = pd.read_csv(chemin_csv)
    par_region = d.groupby("region").chiffre_affaires.sum()
    return {"ca_total": int(d.chiffre_affaires.sum()),
            "meilleure_region": par_region.idxmax(), "ca_meilleure_region": int(par_region.max())}


def verifier(rapport: str, ref: dict) -> dict:
    """Le rapport cite-t-il les bons chiffres ? (on ignore les séparateurs : 414 644 = 414,644 = 414644)"""
    nombres = {int(re.sub(r"[\s .,]", "", n)) for n in re.findall(r"\d[\d\s .,]*\d|\d", rapport)
               if re.sub(r"[\s .,]", "", n).isdigit()}
    return {"ca_total": ref["ca_total"] in nombres,
            "meilleure_region": ref["meilleure_region"] in rapport and ref["ca_meilleure_region"] in nombres}


async def main(chemin_csv):
    runner = InMemoryRunner(agent=root_agent, app_name="analyse")
    for essai in range(4):
        s = await runner.session_service.create_session(app_name="analyse", user_id="moi")
        rapport, nb_codes = "", 0
        try:
            async for ev in runner.run_async(user_id="moi", session_id=s.id,
                                             new_message=construire_message(QUESTION, chemin_csv)):
                for p in ev.content.parts if ev.content else []:
                    if p.executable_code:
                        nb_codes += 1
                        print(f"--- code exécuté n°{nb_codes} ---\n{p.executable_code.code[-400:]}")
                    if p.code_execution_result:
                        print(f"--- résultat ({p.code_execution_result.outcome.name}) ---\n"
                              f"{(p.code_execution_result.output or '')[:600]}")
                    if p.text and ev.is_final_response() and not p.text.startswith("Saved as artifact"):
                        rapport += p.text
            break
        except errors.APIError as e:  # 429 / 503 : on attend puis on recommence
            if e.code not in (429, 503) or essai == 3:
                raise
            await asyncio.sleep(15 * (essai + 1))
    # Les images produites par le bac à sable sont rangées par ADK dans le service d'artefacts.
    for nom in await runner.artifact_service.list_artifact_keys(app_name="analyse", user_id="moi", session_id=s.id):
        image = await runner.artifact_service.load_artifact(app_name="analyse", user_id="moi",
                                                            session_id=s.id, filename=nom)
        open(f"graphique_{nom}", "wb").write(image.inline_data.data)
        print("Graphique enregistré :", f"graphique_{nom}")
    open("rapport.md", "w", encoding="utf-8").write(rapport)
    print("\n=== RAPPORT ===\n" + rapport)
    print("CONTRÔLE :", verifier(rapport, reference(chemin_csv)))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "ventes.csv"))
