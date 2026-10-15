"""Harnais d'évaluation de trajectoire : exécute un agent ADK et compare ses appels d'outils
à la trajectoire attendue d'un jeu d'évaluation au format ADK (evalset.json).

python harness.py          # évalue la v2 sur evalset.json (vrai modèle)
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path

from google.adk.evaluation.eval_set import EvalSet
from google.adk.runners import InMemoryRunner
from google.genai import types

import bank_agent

HERE = Path(__file__).parent


async def run_case(agent, message: str, state: dict) -> dict:
    """Exécute un tour de conversation et retourne la trajectoire + la réponse finale."""
    runner = InMemoryRunner(agent=agent, app_name="eval")
    s = await runner.session_service.create_session(app_name="eval", user_id="u", state=state,
                                                    session_id=str(uuid.uuid4()))
    calls, responses, final = [], [], ""
    msg = types.Content(role="user", parts=[types.Part(text=message)])
    async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []) or []:
            if p.function_call:
                calls.append({"name": p.function_call.name, "args": dict(p.function_call.args or {})})
            if p.function_response:
                responses.append({"name": p.function_response.name,
                                  "response": dict(p.function_response.response or {})})
            if p.text and ev.is_final_response() and not getattr(p, "thought", False):
                final += p.text
    return {"tool_calls": calls, "tool_responses": responses, "response": final.strip()}


# ---------- comparaison de trajectoires (fonctions pures) ----------
def _same(a: dict, e: dict, ignore_args: bool) -> bool:
    if a["name"] != e["name"]:
        return False
    # on ne compare que les arguments attendus : un argument optionnel en plus est toléré
    return ignore_args or all(a["args"].get(k) == v for k, v in e.get("args", {}).items())


def trajectory_match(actual: list, expected: list, mode: str = "IN_ORDER",
                     ignore_args: bool = False) -> bool:
    """EXACT : mêmes appels, même ordre, rien de plus.
    IN_ORDER : les appels attendus apparaissent dans l'ordre (d'autres sont tolérés entre eux).
    ANY_ORDER : les appels attendus apparaissent, dans n'importe quel ordre."""
    if mode == "EXACT":
        return len(actual) == len(expected) and all(_same(a, e, ignore_args)
                                                    for a, e in zip(actual, expected))
    if mode == "IN_ORDER":
        it = iter(actual)
        return all(any(_same(a, e, ignore_args) for a in it) for e in expected)
    if mode == "ANY_ORDER":
        pool = list(actual)
        for e in expected:
            hit = next((a for a in pool if _same(a, e, ignore_args)), None)
            if hit is None:
                return False
            pool.remove(hit)
        return True
    raise ValueError(mode)


def forbidden_called(actual: list, forbidden: list[str]) -> list[str]:
    """Outils qui n'auraient jamais dû être appelés (ex. transfer_funds sur une simple question)."""
    return [a["name"] for a in actual if a["name"] in forbidden]


def load_evalset(path: Path = HERE / "evalset.json") -> EvalSet:
    return EvalSet.model_validate_json(path.read_text(encoding="utf-8"))  # le format ADK, validé


async def evaluate(agent, evalset: EvalSet, mode: str = "IN_ORDER", forbidden=("transfer_funds",)):
    results = []
    for case in evalset.eval_cases:
        inv = case.conversation[0]
        expected = [{"name": t.name, "args": dict(t.args or {})} for t in inv.intermediate_data.tool_uses]
        bank_agent.reset_data()
        out = await run_case(agent, inv.user_content.parts[0].text, dict(case.session_input.state))
        allowed_transfer = any(e["name"] == "transfer_funds" for e in expected)
        bad = [] if allowed_transfer else forbidden_called(out["tool_calls"], list(forbidden))
        results.append({"eval_id": case.eval_id, "question": inv.user_content.parts[0].text,
                        "expected": expected, **out,
                        "reference": inv.final_response.parts[0].text if inv.final_response else "",
                        "trajectory_ok": trajectory_match(out["tool_calls"], expected, mode) and not bad,
                        "forbidden_calls": bad})
    return results


if __name__ == "__main__":
    res = asyncio.run(evaluate(bank_agent.build_agent(hardened=True), load_evalset()))
    for r in res:
        print(("OK  " if r["trajectory_ok"] else "KO  ") + r["eval_id"],
              [c["name"] for c in r["tool_calls"]], "|", r["response"][:90].replace("\n", " "))
    print(f"score trajectoire = {sum(r['trajectory_ok'] for r in res)}/{len(res)}",
          f"| appels modèle = {bank_agent.CALLS['model']}")
    sys.exit(0 if all(r["trajectory_ok"] for r in res) else 1)
