"""Évaluation : 10 scénarios de rappel entre sessions, dans 3 configurations de contexte.

  sans_memoire        nouvelle session, aucun souvenir
  historique_complet  on recolle toute la session 1 dans le contexte (la solution « naïve »)
  memoire             nouvelle session + faits rappelés par similarité depuis SQLite

Usage : python eval_rappel.py [scenarios.json] [eval.db] [resultats.json]"""
import json
import os
import re
import sys

import assistant
import memoire


def passes(answer: str, q: dict) -> bool:
    ok = all(re.search(p, answer, re.I) for p in q.get("expect", []))
    return ok and not any(re.search(p, answer, re.I) for p in q.get("forbid", []))


def fact_recalled(recalled, q) -> bool | None:
    """Le bon fait était-il parmi les k rappelés ? (None si le scénario n'attend aucun fait)"""
    if not q.get("fait"):
        return None
    return any(re.search(q["fait"], t, re.I) for _, _, t in recalled)


def session_1(c, mem, scenarios):
    """Première session de chaque utilisateur : l'assistant répond ET apprend.
    Renvoie la transcription intégrale de chaque session (pour le mode historique_complet)."""
    transcripts = {}
    for user, messages in scenarios["session_1"].items():
        a = assistant.Assistant(c, mem, user)
        transcripts[user] = []
        for m in messages:
            answer = a.chat(m)
            transcripts[user] += [("user", m), ("model", answer)]
            print(f"  [{user}] {m[:60]!r} -> {a.last['memory_ops']}")
        print(f"  [{user}] résumé glissant en fin de session : {a.conv.summary[:200]!r}")
    return transcripts


def run(c, mem, scenarios, transcripts, mode: str):
    rows = []
    for q in scenarios["questions"]:
        a = assistant.Assistant(c, mem if mode == "memoire" else None, q["user"], max_turns=10_000)
        if mode == "historique_complet":
            a.conv.turns = list(transcripts[q["user"]])  # toute la session 1, mot pour mot
        ans = a.chat(q["q"], learn=False)
        rows.append({"id": q["id"], "ok": passes(ans, q), "fait_rappele": fact_recalled(a.last["recalled"], q),
                     "prompt_tokens": a.last["prompt_tokens"], "reponse": ans})
    return rows


def main(path="scenarios.json", db="eval.db", out="resultats_eval.json"):
    from google import genai
    if os.path.exists(db):
        os.remove(db)  # évaluation reproductible : on repart d'une mémoire vide
    c = genai.Client()
    mem = memoire.Memory(db, memoire.gemini_embedder(c))
    scenarios = json.load(open(path, encoding="utf-8"))

    print("== Session 1 : l'assistant apprend")
    transcripts = session_1(c, mem, scenarios)
    for user in scenarios["session_1"]:
        print(f"  faits stockés pour {user} :", [t for _, t in mem.all(user)])

    results = {}
    for mode in ["sans_memoire", "historique_complet", "memoire"]:
        rows = run(c, mem, scenarios, transcripts, mode)
        results[mode] = rows
        hits = [r["fait_rappele"] for r in rows if r["fait_rappele"] is not None]
        print(f"\n== {mode} : {sum(r['ok'] for r in rows)}/{len(rows)} réussis, "
              f"tokens d'entrée moyens {sum(r['prompt_tokens'] for r in rows) / len(rows):.0f}"
              + (f", bon fait rappelé {sum(hits)}/{len(hits)}" if mode == "memoire" else ""))
        for r in rows:
            print(f"  {'OK ' if r['ok'] else 'KO '} #{r['id']:<2} {r['reponse'][:110]!r}")
    json.dump(results, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return results


if __name__ == "__main__":
    main(*sys.argv[1:])
