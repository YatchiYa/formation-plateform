"""Évalue un modèle sur test.jsonl : zéro exemple (zero-shot) et quelques exemples (few-shot).

Sert de LIGNE DE BASE avant réglage, puis à mesurer le modèle réglé avec EXACTEMENT le même script.

Usage :
  MODEL=gemini-2.5-flash-lite python evaluate.py               # zero-shot + few-shot (2 x 15 appels)
  MODEL=<endpoint du modèle réglé> python evaluate.py --modes zero-shot   # après réglage
"""
import argparse
import json
import sys
from collections import Counter

from common import LABELS, SYSTEM, env, from_example, generate, make_client, parse_label

SHOTS_PER_LABEL = 2


def load(path):
    with open(path, encoding="utf-8") as f:
        return [from_example(json.loads(l)) for l in f if l.strip()]


def pick_shots(train, per_label=SHOTS_PER_LABEL):
    """Les premiers exemples de chaque étiquette, toujours les mêmes (évaluation reproductible)."""
    shots, count = [], Counter()
    for ticket, label in train:
        if count[label] < per_label:
            shots.append((ticket, label))
            count[label] += 1
    return shots


def build_contents(ticket, shots):
    """Les exemples few-shot sont des tours user/model : le même format que le jeu de réglage."""
    contents = []
    for t, l in shots:
        contents += [{"role": "user", "parts": [{"text": t}]}, {"role": "model", "parts": [{"text": l}]}]
    return contents + [{"role": "user", "parts": [{"text": ticket}]}]


def score(gold, pred):
    """Exactitude, taux de réponses hors étiquettes, et rappel par étiquette."""
    n = len(gold)
    per = {l: round(sum(g == p == l for g, p in zip(gold, pred)) / max(1, gold.count(l)), 2) for l in LABELS}
    return {"exactitude": round(sum(g == p for g, p in zip(gold, pred)) / n, 3),
            "hors_etiquette": round(sum(p is None for p in pred) / n, 3),
            "rappel_par_etiquette": per}


def run(classify, test, shots, mode):
    gold, pred, tokens_in = [], [], 0
    for ticket, label in test:
        text, n_in = classify(build_contents(ticket, shots if mode == "few-shot" else []))
        gold.append(label)
        pred.append(parse_label(text))
        tokens_in += n_in
    return {**score(gold, pred), "tokens_entree_moyens": round(tokens_in / len(test)),
            "erreurs": [{"ticket": t[:80], "attendu": g, "obtenu": p}
                        for (t, _), g, p in zip(test, gold, pred) if g != p]}


def model_classifier(client, model):
    from google.genai import types

    cfg = types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0, max_output_tokens=20)

    def classify(contents):
        r = generate(client, model, contents, cfg)
        return r.text, r.usage_metadata.prompt_token_count or 0

    return classify


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes", nargs="+", default=["zero-shot", "few-shot"])
    ap.add_argument("--out", default="baseline_report.json")
    a = ap.parse_args()
    model = env("MODEL", "gemini-2.5-flash-lite")
    classify = model_classifier(make_client(), model)
    train, test = load("train.jsonl"), load("test.jsonl")
    report = {"modele": model, "exemples_test": len(test),
              **{m: run(classify, test, pick_shots(train), m) for m in a.modes}}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    for m in a.modes:
        r = report[m]
        print(f"{m:10s} exactitude={r['exactitude']:.3f} hors_etiquette={r['hors_etiquette']:.3f} "
              f"tokens_entree_moyens={r['tokens_entree_moyens']}", file=sys.stderr)


if __name__ == "__main__":
    main()
