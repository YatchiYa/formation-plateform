"""Évaluation chiffrée sur golden.json.

  python eval.py --calibrer   # sans appel au modèle de génération : choisit le seuil
  python eval.py              # agent ADK : rappel@k, fidélité, refus corrects, faux refus
  python eval.py --chaine     # même chose avec la chaîne simple (sans agent)
"""
import asyncio
import json
import os
import sys

import faq_rag

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "gemini-3.5-flash-lite")
JUDGE = """Tu es un évaluateur strict. Voici des entrées de FAQ puis une réponse du service client.
Réponds OUI si TOUTES les affirmations de la réponse sont soutenues par les entrées, sinon NON.
Un seul mot.

Entrées :
{context}

Réponse : {answer}"""


def retrieval(index, golden, k=faq_rag.K):
    """Un seul appel d'embedding pour toutes les questions. Renvoie (hits, meilleur score) par question."""
    qvecs = index.embed_fn([g["question"] for g in golden], kind="query")
    return [index.search(g["question"], k, qvec=q) for g, q in zip(golden, qvecs)]


def calibrer(golden, all_hits):
    """Seuil qui sépare le mieux les questions couvertes (meilleur score haut) des autres."""
    best = [(h[0]["score"], bool(g["attendu"])) for g, h in zip(golden, all_hits)]
    scores = sorted({s for s, _ in best})
    candidats = [round((a + b) / 2, 3) for a, b in zip(scores, scores[1:])] or scores  # milieux : une marge des deux côtés
    acc = lambda t: sum((s >= t) == couverte for s, couverte in best) / len(best)
    seuil = max(candidats, key=lambda t: (acc(t), -t))  # à précision égale, le plus bas (moins de faux refus)
    return seuil, acc(seuil), sorted(best, reverse=True)


def recall(hits, attendu):
    return sum(a in {h["id"] for h in hits} for a in attendu) / len(attendu)


def judge(answer, ids, index, generate_fn=faq_rag.generate):
    context = "\n".join(f"[{i}] {index.by_id[i]['question']} {index.by_id[i]['reponse']}" for i in ids)
    return generate_fn(JUDGE.format(context=context, answer=answer), model=JUDGE_MODEL).upper().startswith("OUI")


def evaluate(golden, all_hits, answers, judge_fn):
    ins = [i for i, g in enumerate(golden) if g["attendu"]]
    outs = [i for i, g in enumerate(golden) if not g["attendu"]]
    answered = [i for i in ins if not answers[i]["refus"]]
    fid = []
    for i in answered:
        answers[i]["fidele"] = judge_fn(answers[i]["answer"], answers[i]["ids"])
        fid.append(answers[i]["fidele"])
    return {
        "rappel@k": round(sum(recall(all_hits[i], golden[i]["attendu"]) for i in ins) / len(ins), 3),
        "fidelite": round(sum(fid) / len(fid), 3) if fid else None,
        "refus_corrects": round(sum(answers[i]["refus"] for i in outs) / len(outs), 3),
        "faux_refus": round(sum(answers[i]["refus"] for i in ins) / len(ins), 3),
    }


async def main(mode):
    golden = json.load(open(os.path.join(os.path.dirname(__file__), "golden.json"), encoding="utf-8"))
    index = faq_rag.FAQIndex()
    all_hits = retrieval(index, golden)
    if mode == "--calibrer":
        seuil, acc, best = calibrer(golden, all_hits)
        for s, couverte in best:
            print(f"  {s:.3f}  {'couverte' if couverte else 'HORS PÉRIMÈTRE'}")
        print(f"seuil conseillé : {seuil:.3f} (questions bien triées : {acc:.0%})")
        return
    if mode == "--chaine":
        answers = [faq_rag.repondre(index, g["question"]) for g in golden]
    else:
        import agent
        answers = [await agent.ask(g["question"]) for g in golden]
    res = evaluate(golden, all_hits, answers, lambda ans, ids: judge(ans, ids, index))
    for g, a in zip(golden, answers):
        tag = "REFUS" if a["refus"] else ("ok" if a.get("fidele") else "NON FIDÈLE")
        print(f"[{tag}] {g['question']}\n        -> {a['answer']}")
    print(json.dumps({"mode": mode or "agent", "seuil": faq_rag.SEUIL, **res}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else ""))
