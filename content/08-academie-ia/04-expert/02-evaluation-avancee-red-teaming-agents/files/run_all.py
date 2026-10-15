"""Lance toute l'évaluation (vrai modèle) et écrit results.json. Environ 30 appels.

python run_all.py && python report.py --ci
"""
import asyncio
import json
from datetime import date
from pathlib import Path

import bank_agent
import guardrails
import harness
import llm_judge

HERE = Path(__file__).parent


async def main():
    out = {"date": date.today().isoformat(), "modele": bank_agent.MODEL}
    out["trajectoire"] = await harness.evaluate(bank_agent.build_agent(hardened=True), harness.load_evalset())
    cases = json.loads((HERE / "guardrail_cases.json").read_text(encoding="utf-8"))
    out["garde_fous"] = await guardrails.run(False, cases) + await guardrails.run(True, cases)
    out["juge"] = llm_judge.calibrate()
    out["appels_modele"] = bank_agent.CALLS["model"]
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("results.json écrit,", out["appels_modele"], "appels au modèle")


if __name__ == "__main__":
    asyncio.run(main())
