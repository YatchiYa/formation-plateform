"""Évaluation chiffrée sur golden.json : rappel@k, fidélité (LLM-juge), refus corrects.

Usage : python eval.py [k]      (l'index doit exister : python rag.py index docs)
"""
import json
import os
import sys

import rag

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash-lite")

JUDGE = """Tu es un évaluateur strict. Voici des extraits de documents puis une réponse.
Réponds OUI si TOUTES les affirmations de la réponse sont soutenues par les extraits, sinon NON.
Réponds par un seul mot.

Extraits :
{context}

Réponse : {answer}"""


def recall_at_k(hits: list[dict], attendu: list[str]) -> float:
    """Part des passages attendus (fichier#page) présents dans les k résultats."""
    found = {f"{h['path']}#{h['page']}" for h in hits}
    return sum(a in found for a in attendu) / len(attendu)


def judge(answer: str, hits: list[dict], generate_fn=rag.generate) -> bool:
    context = "\n\n".join(f"[{h['path']} p. {h['page']}] {h['text']}" for h in hits)
    verdict = generate_fn(JUDGE.format(context=context, answer=answer), model=JUDGE_MODEL)
    return verdict.strip().upper().startswith("OUI")


def evaluate(db, golden: list[dict], k: int = 4, answer_fn=rag.answer, judge_fn=judge) -> dict:
    rows = []
    for g in golden:
        r = answer_fn(db, g["question"], k)
        in_scope = bool(g["attendu"])
        row = {"question": g["question"], "refus": r["refus"], "dans_perimetre": in_scope,
               "reponse": r["answer"]}
        if in_scope:
            row["rappel"] = recall_at_k(r["hits"], g["attendu"])
            row["rappel1"] = recall_at_k(r["hits"][:1], g["attendu"])
            if not r["refus"]:
                row["fidele"] = judge_fn(r["answer"], r["hits"])
        rows.append(row)
    ins = [r for r in rows if r["dans_perimetre"]]
    outs = [r for r in rows if not r["dans_perimetre"]]
    judged = [r for r in ins if "fidele" in r]
    return {
        "k": k,
        "rappel@1": round(sum(r["rappel1"] for r in ins) / len(ins), 3),
        "rappel@k": round(sum(r["rappel"] for r in ins) / len(ins), 3),
        "fidelite": round(sum(r["fidele"] for r in judged) / len(judged), 3) if judged else None,
        "refus_corrects": round(sum(r["refus"] for r in outs) / len(outs), 3) if outs else None,
        "faux_refus": round(sum(r["refus"] for r in ins) / len(ins), 3),
        "details": rows,
    }


if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    golden = json.load(open("golden.json", encoding="utf-8"))
    res = evaluate(rag.connect(), golden, k)
    for r in res.pop("details"):
        flag = "REFUS" if r["refus"] else "ok"
        print(f"[{flag:5}] rappel={r.get('rappel', '-')} fidele={r.get('fidele', '-')}  {r['question']}")
    print(json.dumps(res, ensure_ascii=False))
