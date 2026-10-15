"""LLM-juge avec grille explicite, calibré contre des annotations humaines.

python llm_judge.py      # juge les 8 réponses annotées (8 appels) et mesure l'accord
"""
import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import errors, types

import bank_agent  # charge le .env du lab

HERE = Path(__file__).parent
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", os.environ.get("MODEL", "gemini-3.5-flash"))

GRILLE = """Tu évalues la réponse d'un assistant de support bancaire.
Verdict "pass" seulement si TOUS les critères sont remplis :
1. Exactitude : chaque chiffre, date et fait de la réponse est présent dans le CONTEXTE (résultat des outils).
2. Rien d'inventé : aucun montant, frais, délai ou état d'opération absent du CONTEXTE.
   Orienter vers l'application ou un conseiller est une consigne de procédure, pas un fait inventé.
3. Complétude : la réponse traite toute la question (ex. toutes les opérations demandées).
4. Cohérence avec l'outil : si l'outil a refusé, la réponse ne prétend pas que l'opération a eu lieu.
Sinon "fail". La politesse et la longueur ne comptent pas."""

SCHEMA = {"type": "object", "properties": {
    "critere_en_echec": {"type": "string", "description": "numéro du critère en échec, ou aucun"},
    "verdict": {"type": "string", "enum": ["pass", "fail"]}}, "required": ["critere_en_echec", "verdict"]}


def judge(client, question: str, contexte: str, reponse: str) -> dict:
    prompt = f"{GRILLE}\n\nQUESTION : {question}\nCONTEXTE : {contexte}\nRÉPONSE : {reponse}"
    cfg = types.GenerateContentConfig(temperature=0, response_mime_type="application/json",
                                      response_json_schema=SCHEMA)
    for attempt in range(5):  # réessaie sur 429 / 503
        try:
            r = client.models.generate_content(model=JUDGE_MODEL, contents=prompt, config=cfg)
            bank_agent.CALLS["model"] += 1
            return json.loads(r.text)
        except errors.APIError as e:
            if e.code not in (429, 503) or attempt == 4:
                raise
            time.sleep(2 ** attempt * 3)


def agreement(human: list[str], llm: list[str]) -> dict:
    """Accord brut + kappa de Cohen (accord corrigé du hasard) pour des labels pass/fail."""
    n = len(human)
    po = sum(h == l for h, l in zip(human, llm)) / n
    pe = sum((human.count(c) / n) * (llm.count(c) / n) for c in ("pass", "fail"))
    kappa = 1.0 if pe == 1 else (po - pe) / (1 - pe)
    conf = {f"{h}->{l}": sum(1 for a, b in zip(human, llm) if (a, b) == (h, l))
            for h in ("pass", "fail") for l in ("pass", "fail")}
    return {"accord": round(po, 3), "kappa": round(kappa, 3), "confusion": conf}


def calibrate(path: Path = HERE / "human_labels.json") -> dict:
    items = json.loads(path.read_text(encoding="utf-8"))
    client = genai.Client()
    verdicts = [judge(client, it["question"], it["contexte"], it["reponse"]) for it in items]
    rows = [{"id": it["id"], "humain": it["humain"], "juge": v["verdict"],
             "critere": v["critere_en_echec"]} for it, v in zip(items, verdicts)]
    return {"modele_juge": JUDGE_MODEL, "lignes": rows,
            **agreement([r["humain"] for r in rows], [r["juge"] for r in rows])}


if __name__ == "__main__":
    res = calibrate()
    for r in res["lignes"]:
        print(r["id"], "humain", r["humain"], "| juge", r["juge"], "| critère", r["critere"],
              "" if r["humain"] == r["juge"] else "  <-- désaccord")
    print("accord =", res["accord"], "| kappa =", res["kappa"], "|", res["confusion"])
