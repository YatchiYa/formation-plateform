"""Banc d'essai : qualité (15 questions notées automatiquement) et latence, modèle par modèle.

python bench.py --modeles gemma-4-26b-a4b-it,gemma-4-31b-it,gemini-3.5-flash
LLM_FOURNISSEUR=ollama python bench.py --modeles gemma4:e2b          # même code, en local
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

from client_llm import ClientLLM

SYSTEME = ("Tu es un assistant interne d'entreprise. Réponds en français, de façon brève et exacte, "
           "en respectant strictement le format demandé.")
NOMBRE = re.compile(r"-?\d+(?:[   ]\d{3})*(?:[.,]\d+)?")


def nombres(texte: str) -> list[float]:
    return [float(re.sub(r"[   ]", "", n).replace(",", ".")) for n in NOMBRE.findall(texte)]


def _egal(a, b) -> bool:
    if isinstance(b, (int, float)):
        return isinstance(a, (int, float)) and abs(a - b) < 0.01
    return str(a).strip().lower() == str(b).strip().lower()


def noter(q: dict, texte: str) -> bool:
    """Note une réponse sans LLM-juge : règles déterministes selon le type de question."""
    if q["type"] == "contient":
        return any(re.search(rf"(?<!\w){re.escape(a)}(?!\w)", texte, re.I) for a in q["attendu"])
    if q["type"] == "nombre":
        return any(abs(n - q["attendu"]) < 0.01 for n in nombres(texte))
    if q["type"] == "regex":
        return re.search(q["attendu"], texte) is not None
    if q["type"] == "json":
        bloc = re.search(r"\{.*\}", texte, re.DOTALL)
        try:
            obj = json.loads(bloc.group(0)) if bloc else None
        except json.JSONDecodeError:
            return False
        return isinstance(obj, dict) and all(_egal(obj.get(k), v) for k, v in q["attendu"].items())
    raise ValueError(q["type"])


def evaluer(client: ClientLLM, modele: str, questions: list[dict]) -> dict:
    lignes = []
    for q in questions:
        r = client.discuter(modele, q["question"], SYSTEME)
        lignes.append({"id": q["id"], "ok": noter(q, r.texte), "latence_s": round(r.latence_s, 2),
                       "jetons": r.jetons_sortie, "reponse": r.texte[:200]})
        print(f"  {modele:22} {q['id']} {'OK ' if lignes[-1]['ok'] else 'KO '} {r.latence_s:5.2f} s  {r.texte[:60]!r}")
    latences = [l["latence_s"] for l in lignes]
    return {"modele": modele, "score": sum(l["ok"] for l in lignes), "total": len(lignes),
            "latence_mediane_s": round(statistics.median(latences), 2), "latence_max_s": max(latences),
            "details": lignes}


def tableau(resultats: list[dict]) -> str:
    out = ["| Modèle | Score | Latence médiane | Latence max |", "| --- | --- | --- | --- |"]
    out += [f"| {r['modele']} | {r['score']}/{r['total']} | {r['latence_mediane_s']} s | {r['latence_max_s']} s |"
            for r in resultats]
    return "\n".join(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modeles", default="gemma-4-26b-a4b-it,gemini-3.5-flash")
    p.add_argument("--fournisseur", default=None, help="gemini, vertex, ollama, llamacpp, lmstudio")
    p.add_argument("--limite", type=int, default=15)
    p.add_argument("--sortie", default="resultats.json")
    a = p.parse_args()
    questions = json.loads(Path(__file__).with_name("questions.json").read_text(encoding="utf-8"))[: a.limite]
    client = ClientLLM.depuis_env(a.fournisseur)
    resultats = [evaluer(client, m.strip(), questions) for m in a.modeles.split(",")]
    Path(a.sortie).write_text(json.dumps(resultats, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n" + tableau(resultats))
