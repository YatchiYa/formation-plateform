"""Évaluation chiffrée sur golden.json.

  K=2 python eval.py --recherche   # 1 appel d'embedding : rappel@k, découpage par taille vs par structure
  python eval.py               # + filtres, réponses, fidélité (LLM-juge), refus corrects
"""
import json
import os
import sys

import contrats_rag as cr

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash-lite")
K = int(os.environ.get("K", "4"))
JUDGE = """Tu es un évaluateur strict. Voici des extraits de contrats puis une réponse.
Réponds OUI si TOUTES les affirmations de la réponse sont soutenues par les extraits, sinon NON.
Un seul mot.

Extraits :
{context}

Réponse : {answer}"""


def recall(hits, attendu):
    """Un passage attendu est trouvé si un morceau du BON contrat contient la preuve."""
    return sum(any(h["ref"] == a["ref"] and a["preuve"] in h["text"] for h in hits) for a in attendu) / len(attendu)


def filtres_ok(obtenus, attendus):
    def ok(a, o):  # "DataPlume" et "DataPlume SAS" désignent la même partie
        a, o = (a or "").lower(), (o or "").lower()
        return a == o or bool(a and o and (a in o or o in a))
    return all(ok(attendus[c], obtenus.get(c)) for c in ("type", "partie"))


def judge(answer, hits, generate_fn=cr.generate):
    return generate_fn(JUDGE.format(context=cr.contexte(hits), answer=answer), model=JUDGE_MODEL).upper().startswith("OUI")


def recherche(db, golden, qvecs):
    ins = [(g, q) for g, q in zip(golden, qvecs) if g["attendu"]]
    res = {}
    for strat in ("taille", "structure"):
        res[f"rappel@{K} {strat}"] = round(sum(recall(cr.search(db, g["question"], K, strat, qvec=q), g["attendu"])
                                              for g, q in ins) / len(ins), 3)
    res[f"rappel@{K} structure+filtres attendus"] = round(sum(recall(cr.search(
        db, g["question"], K, filtres=g["filtres"], par_contrat=2 if len(g["attendu"]) > 1 else None, qvec=q),
        g["attendu"]) for g, q in ins) / len(ins), 3)
    return res


def complet(db, golden, answer_fn, judge_fn):
    rows = [answer_fn(g["question"]) for g in golden]
    ins = [(g, r) for g, r in zip(golden, rows) if g["attendu"]]
    outs = [r for g, r in zip(golden, rows) if not g["attendu"]]
    fid = [judge_fn(r["answer"], r["hits"]) for g, r in ins if not r["refus"]]
    return rows, {
        "filtres_corrects": round(sum(filtres_ok(r["filtres"], g["filtres"]) for g, r in zip(golden, rows)) / len(rows), 3),
        f"rappel@{K} pipeline": round(sum(recall(r["hits"], g["attendu"]) for g, r in ins) / len(ins), 3),
        "fidelite": round(sum(fid) / len(fid), 3) if fid else None,
        "refus_corrects": round(sum(r["refus"] for r in outs) / len(outs), 3),
        "faux_refus": round(sum(r["refus"] for g, r in ins) / len(ins), 3),
    }


if __name__ == "__main__":
    golden = json.load(open(os.path.join(os.path.dirname(__file__), "golden.json"), encoding="utf-8"))
    db = cr.connect()
    qvecs = cr.embed([g["question"] for g in golden], kind="query")
    res = recherche(db, golden, qvecs)
    if "--recherche" not in sys.argv:
        rows, res2 = complet(db, golden, lambda q: cr.answer(db, q), judge)
        for g, r in zip(golden, rows):
            print(f"[{'REFUS' if r['refus'] else 'ok':5}] {g['question']}  filtres={ {k: v for k, v in r['filtres'].items() if v} }")
            print("       ", r["answer"].replace("\n", "\n        "))
        res.update(res2)
    print(json.dumps(res, ensure_ascii=False))
