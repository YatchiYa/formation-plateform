"""Comparaison texte seul / multimodal / multimodal + expansion par page, sur 12 questions (10 dont la réponse est dans une figure).

Deux mesures par mode :
  - page trouvée : un des 3 chunks récupérés vient de la bonne page ;
  - réponse exacte : la réponse contient la valeur attendue (après normalisation).
Usage : python evaluate.py   (≈ 4 descriptions d'images en 1re exécution, 2 embeddings, 36 générations)
"""
import json
import re
import unicodedata

from multimodal_rag import HERE, Index, answer, embed, gemini


def norm(s: str) -> str:
    """minuscules, sans accents, sans espaces (y compris insécables), virgule décimale -> point."""
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", "", s).replace(",", ".")


def is_correct(text: str, expected: list[str]) -> bool:
    return any(norm(e) in norm(text) for e in expected)


if __name__ == "__main__":
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    client = gemini()
    index = Index.build(client)
    q_vecs = embed(client, [q["question"] for q in questions])
    score = {m: {"page": 0, "ok": 0, "ok_fig": 0} for m in ("texte", "multimodal", "page")}
    n_fig = sum(q["source"] == "figure" for q in questions)
    for q, v in zip(questions, q_vecs):
        line = [f"- {q['question']}"]
        for mode in score:
            text, hits = answer(index, q["question"], v, mode)
            ok = is_correct(text, q["expected"])
            score[mode]["page"] += any(h["page"] == q["page"] for h in hits)
            score[mode]["ok"] += ok
            score[mode]["ok_fig"] += ok and q["source"] == "figure"
            line.append(f"    [{mode:10}] {'OK ' if ok else 'NON'} {text[:110]!r}")
        print("\n".join(line))
    print(f"\n| Mode | Page trouvée (top 3) | Réponses exactes | dont questions sur figure ({n_fig}) |\n|---|---|---|---|")
    for m, s in score.items():
        print(f"| {m} | {s['page']}/{len(questions)} | {s['ok']}/{len(questions)} | {s['ok_fig']}/{n_fig} |")
