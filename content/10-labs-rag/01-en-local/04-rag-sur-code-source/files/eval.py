"""Évaluation chiffrée sur golden.json.

  python eval.py --recherche   # 1 appel d'embedding : rappel@k vecteur / BM25 / hybride
  python eval.py               # + réponses : fidélité (LLM-juge), citations valides, refus
"""
import json
import os
import sys

import code_rag as cr

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash-lite")
K = int(os.environ.get("K", "5"))
JUDGE = """Tu es un évaluateur strict. Voici des extraits de code puis une réponse à une question sur ce code.
Réponds OUI si TOUTES les affirmations de la réponse sont soutenues par les extraits, sinon NON. Un seul mot.

Extraits :
{context}

Réponse : {answer}"""


def recall(hits, attendu):
    found = {f"{h['path']}::{h['name']}" for h in hits}
    return sum(a in found for a in attendu) / len(attendu)


def judge(answer, hits, generate_fn=cr.generate):
    context = "\n\n".join(f"--- {h['path']}:{h['start']}-{h['end']}\n{h['text']}" for h in hits)
    return generate_fn(JUDGE.format(context=context, answer=answer), model=JUDGE_MODEL).upper().startswith("OUI")


def recherche(golden, qvecs, chunks):
    ins = [(g, q) for g, q in zip(golden, qvecs) if g["attendu"]]
    return {f"rappel@{K} {mode}": round(sum(recall(cr.search(None, g["question"], K, mode, qvec=q, chunks=chunks),
                                                    g["attendu"]) for g, q in ins) / len(ins), 3)
            for mode in ("vecteur", "bm25", "hybride")}


def complet(golden, rows, judge_fn):
    ins = [(g, r) for g, r in zip(golden, rows) if g["attendu"]]
    outs = [r for g, r in zip(golden, rows) if not g["attendu"]]
    answered = [r for g, r in ins if not r["refus"]]
    for r in answered:
        r["fidele"] = judge_fn(r["brut"], r["hits"])
    fid = [r["fidele"] for r in answered]
    return {
        "fidelite": round(sum(fid) / len(fid), 3) if fid else None,
        "citations_valides": round(sum(r["citations_ok"] for r in rows) / len(rows), 3),
        "refus_corrects": round(sum(r["refus"] for r in outs) / len(outs), 3),
        "faux_refus": round(sum(r["refus"] for g, r in ins) / len(ins), 3),
    }


if __name__ == "__main__":
    golden = json.load(open(os.path.join(os.path.dirname(__file__), "golden.json"), encoding="utf-8"))
    db = cr.connect()
    chunks = cr.load(db)
    qvecs = cr.embed([g["question"] for g in golden], kind="query")
    res = recherche(golden, qvecs, chunks)
    if "--recherche" not in sys.argv:
        rows = [cr.answer(db, g["question"], K, qvec=q) for g, q in zip(golden, qvecs)]
        res.update(complet(golden, rows, judge))
        for g, r in zip(golden, rows):
            tag = "REFUS" if r["refus"] else ("ok" if r.get("fidele") else "NON FIDÈLE")
            print(f"[{tag}] {g['question']}\n        {r['answer']}")
    print(json.dumps(res, ensure_ascii=False))
