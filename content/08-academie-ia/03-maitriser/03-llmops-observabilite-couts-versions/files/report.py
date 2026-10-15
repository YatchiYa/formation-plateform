"""Rapport de coûts et de latences à partir du journal calls.jsonl.

  python report.py [calls.jsonl] > rapport.md
"""
import json
import math
import sys
from collections import defaultdict


def percentile(values: list[float], p: float) -> float:
    """Percentile « au rang le plus proche » : la valeur sous laquelle tombent p % des mesures."""
    s = sorted(values)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]


def summarize(records: list[dict]) -> dict:
    groups = defaultdict(list)
    for r in records:
        groups[f"{r['prompt_id']}@{r['prompt_version']} ({r['model']})"].append(r)
    out = {}
    for key, rs in sorted(groups.items()):
        lat = [r["latency_ms"] for r in rs if r["ok"]] or [0]
        cost = sum(r["cost_usd"] or 0 for r in rs)
        out[key] = {"appels": len(rs), "taux_erreur": round(sum(not r["ok"] for r in rs) / len(rs), 3),
                    "p50_ms": percentile(lat, 50), "p95_ms": percentile(lat, 95),
                    "tokens_in_moy": round(sum(r["tokens_in"] for r in rs) / len(rs)),
                    "tokens_out_moy": round(sum(r["tokens_out"] for r in rs) / len(rs)),
                    "cout_total_usd": round(cost, 6), "cout_1000_appels_usd": round(cost / len(rs) * 1000, 4)}
    return out


def to_markdown(summary: dict) -> str:
    cols = ["appels", "taux_erreur", "p50_ms", "p95_ms", "tokens_in_moy", "tokens_out_moy",
            "cout_total_usd", "cout_1000_appels_usd"]
    lines = ["| version | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    lines += [f"| {k} | " + " | ".join(str(v[c]) for c in cols) + " |" for k, v in summary.items()]
    return "\n".join(lines)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "calls.jsonl"
    with open(path, encoding="utf-8") as f:
        records = [json.loads(l) for l in f if l.strip()]
    print(to_markdown(summarize(records)))
