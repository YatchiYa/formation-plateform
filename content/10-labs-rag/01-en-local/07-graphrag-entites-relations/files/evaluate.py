"""GraphRAG contre RAG vectoriel classique sur 15 questions relationnelles (1 à 3 sauts).

Score d'une réponse = part des éléments attendus présents (ex. 1/2 si un seul des deux projets est cité).
Usage : python evaluate.py   (≈ 1 embedding + 15 repérages d'entités + 30 générations, graphe en cache)
"""
import json
import re
import unicodedata

from graphrag import HERE, GraphRAG, VectorRAG, embed, gemini, load_corpus


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode())


def coverage(text: str, expected: list[str]) -> float:
    return sum(norm(e) in norm(text) for e in expected) / len(expected)


def table(scores: dict, questions: list[dict]) -> str:
    lines = ["| Méthode | Score moyen | 1 saut | 2 sauts | 3 sauts | Réponses complètes |", "|---|---|---|---|---|---|"]
    for m, s in scores.items():
        by_hop = []
        for h in (1, 2, 3):
            xs = [x for x, q in zip(s, questions) if q["hops"] == h]
            by_hop.append(f"{sum(xs) / len(xs):.2f}")
        lines.append(f"| {m} | {sum(s) / len(s):.2f} | " + " | ".join(by_hop) + f" | {sum(x == 1 for x in s)}/{len(s)} |")
    return "\n".join(lines)


if __name__ == "__main__":
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    client, docs = gemini(), load_corpus()
    graph, vector = GraphRAG.build(client, docs), VectorRAG.build(client, docs)
    q_vecs = embed(client, [q["question"] for q in questions])
    scores = {"vecteurs (top 4)": [], "graphe": []}
    for q, v in zip(questions, q_vecs):
        vt, ids = vector.answer(q["question"], v)
        gt, seeds = graph.answer(q["question"])
        scores["vecteurs (top 4)"].append(coverage(vt, q["expected"]))
        scores["graphe"].append(coverage(gt, q["expected"]))
        print(f"- [{q['hops']} saut(s)] {q['question']}  attendu={q['expected']}")
        print(f"    vecteurs {scores['vecteurs (top 4)'][-1]:.2f} docs={ids} {vt[:120]!r}")
        print(f"    graphe   {scores['graphe'][-1]:.2f} entités={seeds} {gt[:120]!r}")
    print("\n" + table(scores, questions))
