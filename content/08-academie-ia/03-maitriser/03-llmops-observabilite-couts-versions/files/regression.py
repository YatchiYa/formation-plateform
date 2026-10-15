"""Test de non-régression d'une version de prompt sur le jeu de référence (golden.jsonl).

  python regression.py --version v1 --save-baseline   # mesure la version en production et fige son score
  python regression.py --version v2                    # code de sortie 1 si v2 fait moins bien

Règle : la candidate échoue si son exactitude baisse de plus de TOLERANCE par rapport à la
référence, ou si une seule réponse n'est pas un JSON exploitable.
"""
import argparse
import json
import sys
from pathlib import Path

from llm_wrapper import call_llm, gemini_generate

GOLDEN = Path(__file__).with_name("golden.jsonl")
BASELINE = Path(__file__).with_name("baseline.json")
TOLERANCE = 0.05


def parse(text):
    try:
        d = json.loads(text or "")
        return d if isinstance(d, dict) else None
    except json.JSONDecodeError:
        return None


def evaluate(version: str, generate=gemini_generate, cases=None) -> dict:
    cases = cases or [json.loads(l) for l in GOLDEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    ok = valid = 0
    failures = []
    for c in cases:
        r = call_llm("router", version, generate=generate, demande=c["demande"])
        d = parse(r["text"])
        valid += d is not None
        got = (d or {}).get("service"), (d or {}).get("urgence")
        if got == (c["service"], c["urgence"]):
            ok += 1
        else:
            failures.append({"demande": c["demande"][:60], "attendu": [c["service"], c["urgence"]], "obtenu": list(got)})
    n = len(cases)
    return {"version": version, "cas": n, "exactitude": round(ok / n, 3), "json_valide": round(valid / n, 3),
            "echecs": failures}


def gate(candidate: dict, baseline: dict, tolerance: float = TOLERANCE) -> list[str]:
    """Raisons de refuser la candidate (liste vide = acceptée)."""
    reasons = []
    if candidate["exactitude"] < baseline["exactitude"] - tolerance:
        reasons.append(f"exactitude {candidate['exactitude']:.2f} < référence {baseline['exactitude']:.2f} - {tolerance}")
    if candidate["json_valide"] < 1.0:
        reasons.append(f"JSON valide {candidate['json_valide']:.0%} < 100 %")
    return reasons


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--save-baseline", action="store_true")
    a = ap.parse_args()
    result = evaluate(a.version)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if a.save_baseline:
        if result["json_valide"] < 1.0:
            print("Refus : une référence doit être mesurée sans erreur (voir calls.jsonl)", file=sys.stderr)
            return 1
        BASELINE.write_text(json.dumps({k: result[k] for k in ("version", "cas", "exactitude", "json_valide")},
                                       indent=2) + "\n")
        print(f"Référence enregistrée dans {BASELINE.name}", file=sys.stderr)
        return 0
    reasons = gate(result, json.loads(BASELINE.read_text()))
    for r in reasons:
        print("RÉGRESSION :", r, file=sys.stderr)
    print("ÉCHEC" if reasons else "OK : pas de régression", file=sys.stderr)
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
