"""Évaluation comparative : BM25 seul, vecteurs seuls, hybride RRF, hybride + reranking LLM.

Mesures sur les 25 questions de questions.json :
  - rappel@5 : part des documents pertinents retrouvés dans les 5 premiers résultats ;
  - MRR (Mean Reciprocal Rank) : moyenne de 1 / rang du premier document pertinent (0 s'il est absent du top 10).
Usage : python evaluate.py            (≈ 2 appels d'embedding + 25 appels de reranking)
        python evaluate.py --no-rerank
"""
import json
import sys

from hybrid_rag import HERE, HybridIndex, embed, gemini, load_corpus

MODES = ["bm25", "vector", "hybrid", "rerank"]


def recall_at_k(ranked_ids: list[str], relevant: list[str], k: int = 5) -> float:
    return len(set(ranked_ids[:k]) & set(relevant)) / len(relevant)


def reciprocal_rank(ranked_ids: list[str], relevant: list[str], k: int = 10) -> float:
    for rank, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def evaluate(index: HybridIndex, questions: list[dict], q_vecs, modes=MODES) -> dict:
    rows = {m: [] for m in modes}
    for qi, q in enumerate(questions):
        for m in modes:
            ranked = [index.docs[i]["id"] for i in index.search(q["question"], m, k=10, q_vec=q_vecs[qi])]
            rows[m].append({"type": q["type"], "r5": recall_at_k(ranked, q["relevant"]),
                            "rr": reciprocal_rank(ranked, q["relevant"]), "top": ranked[:3]})
    return rows


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def report(rows: dict) -> str:
    types = ["identifiant", "paraphrase", "mixte"]
    lines = ["| Méthode | Rappel@5 | MRR | Rappel@5 identifiant | paraphrase | mixte |", "|---|---|---|---|---|---|"]
    for m, rs in rows.items():
        by_t = [f"{mean([r['r5'] for r in rs if r['type'] == t]):.2f}" for t in types]
        lines.append(f"| {m} | {mean([r['r5'] for r in rs]):.2f} | {mean([r['rr'] for r in rs]):.2f} | " + " | ".join(by_t) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    modes = [m for m in MODES if not ("--no-rerank" in sys.argv and m == "rerank")]
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    client = gemini()
    index = HybridIndex.build(load_corpus(), client)
    q_vecs = embed(client, [q["question"] for q in questions])  # un seul appel pour les 25 questions
    rows = evaluate(index, questions, q_vecs, modes)
    print(report(rows))
    print("\nÉchecs au rang 1 de la meilleure méthode :")
    best = modes[-1]
    for q, r in zip(questions, rows[best]):
        if r["rr"] < 1:
            print(f"- {q['question']}  attendu={q['relevant']}  obtenu={r['top']}")
    (HERE / ".cache").mkdir(exist_ok=True)
    (HERE / ".cache" / "last_eval.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
