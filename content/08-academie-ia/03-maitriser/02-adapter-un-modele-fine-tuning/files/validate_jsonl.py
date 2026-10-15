"""Valide des fichiers JSONL au format du réglage supervisé Gemini (Vertex AI) AVANT de payer un job.

Usage : python validate_jsonl.py train.jsonl validation.jsonl [test.jsonl]
Code de sortie 1 s'il y a une erreur (utilisable en CI).
"""
import json
import sys
from collections import Counter

from common import LABELS

MAX_TOKENS_PER_EXAMPLE = 131_072   # limite documentée (entrée + sortie) pour Gemini 2.5 / 3.x
ROLES = {"user", "model"}


def estimate_tokens(text: str) -> int:
    # Limite connue : ~4 caractères par token, approximation ; client.models.count_tokens pour le chiffre exact
    return len(text) // 4 + 1


def check_example(ex, labels=LABELS) -> list[str]:
    """Liste des problèmes d'UNE ligne (vide = ligne valide)."""
    if not isinstance(ex, dict):
        return ["la ligne n'est pas un objet JSON"]
    errs = []
    unknown = set(ex) - {"systemInstruction", "contents", "tools"}
    if unknown:
        errs.append(f"champs inconnus : {sorted(unknown)}")
    si = ex.get("systemInstruction")
    if si is not None:
        parts = si.get("parts") if isinstance(si, dict) else None
        if not parts or not all(isinstance(p, dict) and set(p) == {"text"} for p in parts):
            errs.append("systemInstruction.parts doit contenir uniquement des {\"text\": ...}")
    contents = ex.get("contents")
    if not isinstance(contents, list) or not contents:
        return errs + ["contents manquant ou vide"]
    total = sum(estimate_tokens(p.get("text", "")) for p in (si or {}).get("parts", []) if isinstance(p, dict))
    for i, c in enumerate(contents):
        if not isinstance(c, dict) or c.get("role") not in ROLES:
            errs.append(f"contents[{i}].role doit être 'user' ou 'model'")
            continue
        parts = c.get("parts")
        if not isinstance(parts, list) or not parts:
            errs.append(f"contents[{i}].parts vide")
            continue
        for p in parts:
            if not isinstance(p, dict) or not (p.get("text") or "").strip() and "fileData" not in p:
                errs.append(f"contents[{i}] contient une part vide")
            else:
                total += estimate_tokens(p.get("text", ""))
        if i and contents[i - 1].get("role") == c.get("role"):
            errs.append(f"contents[{i}] : deux messages '{c['role']}' d'affilée")
    if contents[-1].get("role") != "model":
        errs.append("le dernier message doit être la réponse attendue (role 'model')")
    elif labels:
        answer = contents[-1].get("parts", [{}])[0].get("text", "")
        if answer not in labels:
            errs.append(f"réponse attendue hors étiquettes : {answer!r}")
    if total > MAX_TOKENS_PER_EXAMPLE:
        errs.append(f"≈{total} tokens > {MAX_TOKENS_PER_EXAMPLE}")
    return errs


def validate_file(path: str, labels=LABELS):
    """Renvoie (erreurs, statistiques, ensemble des entrées utilisateur)."""
    errors, counts, inputs, tokens = [], Counter(), set(), 0
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if not line.strip():
                errors.append(f"{path}:{n} ligne vide")
                continue
            try:
                ex = json.loads(line)
            except json.JSONDecodeError as e:
                errors.append(f"{path}:{n} JSON invalide ({e.msg})")
                continue
            errs = check_example(ex, labels)
            errors += [f"{path}:{n} {e}" for e in errs]
            if not errs:
                user = ex["contents"][0]["parts"][0]["text"]
                if user in inputs:
                    errors.append(f"{path}:{n} doublon")
                inputs.add(user)
                counts[ex["contents"][-1]["parts"][0]["text"]] += 1
                msgs = ex["contents"] + [ex.get("systemInstruction") or {"parts": []}]
                tokens += sum(estimate_tokens(p.get("text", "")) for c in msgs for p in c["parts"])
    return errors, {"exemples": sum(counts.values()), "par_etiquette": dict(counts), "tokens_estimes": tokens}, inputs


def main(paths: list[str]) -> int:
    all_errors, seen = [], {}
    for p in paths:
        errors, stats, inputs = validate_file(p)
        print(f"{p}: {json.dumps(stats, ensure_ascii=False)}")
        all_errors += errors
        for other, other_inputs in seen.items():
            leak = inputs & other_inputs
            if leak:
                all_errors.append(f"fuite : {len(leak)} ticket(s) à la fois dans {other} et {p}")
        seen[p] = inputs
    for e in all_errors:
        print("ERREUR", e)
    print("OK : format valide" if not all_errors else f"{len(all_errors)} erreur(s)")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["train.jsonl", "validation.jsonl", "test.jsonl"]))
