"""Distillation : un grand modèle (le « professeur ») fabrique et étiquette 100 tickets fictifs.

Étape 1 : le professeur rédige des tickets variés pour chaque catégorie.
Étape 2 : le professeur ré-étiquette chaque lot SANS connaître la catégorie demandée.
On ne garde que les tickets où les deux étapes sont d'accord (contrôle qualité).
Sortie : tickets_distilles.jsonl, train.jsonl, validation.jsonl, test.jsonl

Usage : python distill.py            (≈ 10 appels au modèle professeur)
"""
import json
import random
import re
import sys

from pydantic import BaseModel

from common import LABELS, env, generate, make_client, parse_label, to_example

TEACHER = env("TEACHER_MODEL", "gemini-3.8-flash")
PER_LABEL = 20          # 5 étiquettes x 20 = 100 exemples
EXTRA = 4               # marge : certains tickets seront rejetés
SEED = 42

DESCRIPTIONS = {
    "facturation": "facture, prélèvement, montant incorrect, TVA, remboursement, moyen de paiement",
    "acces_compte": "mot de passe, connexion impossible, double authentification, compte bloqué, invitation d'un collègue",
    "bug_technique": "erreur à l'écran, lenteur, export qui échoue, synchronisation, plantage de l'application",
    "demande_fonctionnalite": "suggestion d'amélioration, fonction manquante, intégration souhaitée, idée de nouveau rapport",
    "resiliation": "arrêter l'abonnement, ne pas renouveler, supprimer le compte, passer à une offre gratuite pour partir",
}


class Ticket(BaseModel):
    texte: str


class Etiquette(BaseModel):
    id: int
    label: str


def norm(t: str) -> str:
    return re.sub(r"\W+", " ", t.lower()).strip()


def generate_tickets(client, label: str, n: int) -> list[str]:
    from google.genai import types

    prompt = (
        f"Rédige {n} tickets de support client FICTIFS, en français, pour un logiciel de gestion en ligne. "
        f"Catégorie : {label} ({DESCRIPTIONS[label]}). Varie le ton (poli, pressé, agacé), la longueur "
        "(1 à 4 phrases), les fautes de frappe occasionnelles. Pas de nom réel, pas d'e-mail, pas de numéro réel. "
        "Ne cite jamais le nom de la catégorie."
    )
    cfg = types.GenerateContentConfig(response_mime_type="application/json",
                                      response_schema=list[Ticket], temperature=1.0)
    r = generate(client, TEACHER, prompt, cfg)
    return [t.texte.strip() for t in r.parsed if t.texte.strip()]


def relabel(client, tickets: list[str]) -> list[str | None]:
    """Le professeur classe à l'aveugle : c'est son étiquette qui sera apprise par l'élève."""
    from google.genai import types

    lignes = "\n".join(f"{i}. {t}" for i, t in enumerate(tickets))
    prompt = (f"Classe chaque ticket dans une étiquette parmi : {', '.join(LABELS)}.\n"
              f"Renvoie une entrée par ticket (id = numéro du ticket).\n\n{lignes}")
    cfg = types.GenerateContentConfig(response_mime_type="application/json",
                                      response_schema=list[Etiquette], temperature=0)
    r = generate(client, TEACHER, prompt, cfg)
    out = [None] * len(tickets)
    for e in r.parsed:
        if 0 <= e.id < len(tickets):
            out[e.id] = parse_label(e.label)
    return out


def stratified_split(rows: list[dict], ratios=(0.7, 0.15, 0.15), seed=SEED):
    """Découpe train/validation/test en gardant la même proportion de chaque étiquette."""
    rng = random.Random(seed)
    parts = ([], [], [])
    for label in LABELS:
        group = [r for r in rows if r["label"] == label]
        rng.shuffle(group)
        n_train = round(len(group) * ratios[0])
        n_val = round(len(group) * ratios[1])
        parts[0].extend(group[:n_train])
        parts[1].extend(group[n_train:n_train + n_val])
        parts[2].extend(group[n_train + n_val:])
    for p in parts:
        rng.shuffle(p)
    return parts


def write_jsonl(path: str, rows: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(to_example(r["ticket"], r["label"]), ensure_ascii=False) + "\n")


def main():
    client = make_client()
    kept, rejected, seen = [], 0, set()
    for label in LABELS:
        tickets = generate_tickets(client, label, PER_LABEL + EXTRA)
        labels = relabel(client, tickets)
        n = 0
        for t, l in zip(tickets, labels):
            if n >= PER_LABEL:
                break
            if l != label or norm(t) in seen:
                rejected += 1
                continue
            seen.add(norm(t))
            kept.append({"ticket": t, "label": label, "teacher": TEACHER})
            n += 1
        print(f"{label:24s} générés={len(tickets):2d} gardés={n:2d}", file=sys.stderr)

    with open("tickets_distilles.jsonl", "w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    train, val, test = stratified_split(kept)
    write_jsonl("train.jsonl", train)
    write_jsonl("validation.jsonl", val)
    write_jsonl("test.jsonl", test)
    print(json.dumps({"total": len(kept), "rejetes": rejected, "train": len(train),
                      "validation": len(val), "test": len(test)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
