"""Banc de charge asyncio : compare 3 stratégies sur le même jeu de questions.

  big     : toujours le grand modèle (référence qualité)
  small   : toujours le petit modèle
  router  : cache sémantique + petit modèle + escalade selon la confiance

Usage : python bench.py [--concurrency 4] [--strategies big,small,router] [--out resultats.json]
Nombre d'appels : ~16 (big) + 16 (small) + 1 embedding + ~12-16 (router) < 80.
"""
import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

import router as R

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))


def pct(values: list, p: int) -> float:
    """Percentile p (inclusif). Avec 16 mesures, le p95 est presque le max : restez prudent."""
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[p - 1]


def summarize(name: str, rows: list, wall: float) -> dict:
    lat = [r["latency"] for r in rows]
    ttft = [r["ttft"] for r in rows]
    routes = [r["route"] for r in rows]
    return {
        "strategie": name, "n": len(rows),
        "ttft_p50": pct(ttft, 50), "ttft_p95": pct(ttft, 95),
        "lat_p50": pct(lat, 50), "lat_p95": pct(lat, 95),
        "debit_rps": len(rows) / wall,
        "qualite": sum(r["ok"] for r in rows) / len(rows),
        "cout_usd": sum(r["cost"] for r in rows),
        "appels_llm": sum(r["n_calls"] for r in rows),
        "tokens_entree": sum(r["prompt_tokens"] for r in rows),
        "tokens_caches": sum(r["cached_tokens"] for r in rows),
        "tokens_sortie": sum(r["output_tokens"] for r in rows),
        "cache": routes.count("cache"), "escalades": routes.count("escalated"),
    }


def row(q: dict, res: "R.Result") -> dict:
    return {
        "id": q["id"], "route": res.route, "ok": R.grade(res.answer, q["expect"]),
        "latency": res.latency, "ttft": res.ttft, "cost": res.cost, "n_calls": len(res.calls),
        "prompt_tokens": sum(c.prompt_tokens for c in res.calls),
        "cached_tokens": sum(c.cached_tokens for c in res.calls),
        "output_tokens": sum(c.output_tokens for c in res.calls),
        "confidence": [round(c.confidence, 2) for c in res.calls], "similarity": round(res.similarity, 3),
        "answer": res.answer,
    }


async def run_fixed(client, model: str, questions: list, concurrency: int) -> list:
    sem = asyncio.Semaphore(concurrency)  # limite le nombre de requêtes en vol

    async def one(q):
        async with sem:
            c = await R.ask(client, model, q["question"])
            res = R.Result(c.answer, "big" if model == R.BIG_MODEL else "small", [c],
                           latency=c.latency, ttft=c.ttft)
            return row(q, res)
    return await asyncio.gather(*(one(q) for q in questions))


async def run_router(client, questions: list, concurrency: int) -> tuple:
    vecs = await R.embed(client, [q["question"] for q in questions])  # 1 seul appel pour tout le lot
    embed_cost = R.cost_usd(R.EMBED_MODEL, sum(len(q["question"]) // 4 for q in questions), 0, 0)
    rt = R.Router(client, R.SemanticCache())
    sem = asyncio.Semaphore(concurrency)

    async def one(q, v):
        async with sem:
            return row(q, await rt.answer(q["question"], v))
    # Les reformulations arrivent après les originales, comme un trafic réel qui se répète.
    first = [(q, v) for q, v in zip(questions, vecs) if "repeat_of" not in q]
    later = [(q, v) for q, v in zip(questions, vecs) if "repeat_of" in q]
    rows = await asyncio.gather(*(one(q, v) for q, v in first))
    rows += await asyncio.gather(*(one(q, v) for q, v in later))
    return rows, embed_cost


async def main():
    load_dotenv()
    from google import genai

    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--strategies", default="big,small,router")
    ap.add_argument("--out", default="resultats.json")
    a = ap.parse_args()

    client = genai.Client()
    summaries, details = [], {}
    for s in a.strategies.split(","):
        t0 = time.perf_counter()
        if s == "router":
            rows, embed_cost = await run_router(client, QUESTIONS, a.concurrency)
            summary = summarize(s, rows, time.perf_counter() - t0)
            summary["cout_usd"] += embed_cost
        else:
            model = R.BIG_MODEL if s == "big" else R.SMALL_MODEL
            rows = await run_fixed(client, model, QUESTIONS, a.concurrency)
            summary = summarize(f"{s} ({model})", rows, time.perf_counter() - t0)
        summaries.append(summary)
        details[s] = rows

    print(f"{'stratégie':32} {'TTFT p50':>8} {'p95':>6} {'lat p50':>8} {'p95':>6} {'req/s':>6} "
          f"{'qualité':>8} {'coût $':>9} {'appels':>6} {'cache':>5} {'escal.':>6}")
    for m in summaries:
        print(f"{m['strategie']:32} {m['ttft_p50']:8.2f} {m['ttft_p95']:6.2f} {m['lat_p50']:8.2f} "
              f"{m['lat_p95']:6.2f} {m['debit_rps']:6.2f} {m['qualite']:8.0%} {m['cout_usd']:9.5f} "
              f"{m['appels_llm']:6d} {m['cache']:5d} {m['escalades']:6d}")
    for m in summaries:
        print(f"{m['strategie']:32} tokens entrée={m['tokens_entree']} dont en cache={m['tokens_caches']} "
              f"sortie+réflexion={m['tokens_sortie']}")
    Path(a.out).write_text(json.dumps({"resume": summaries, "details": details}, ensure_ascii=False,
                                      indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
