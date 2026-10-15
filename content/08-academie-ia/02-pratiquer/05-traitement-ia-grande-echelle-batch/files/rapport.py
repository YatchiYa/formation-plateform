"""Rapport final : rapport.csv, statistiques, coût estimé et contrôle qualité par échantillonnage.

Usage : python rapport.py [--avis avis.csv] [--resultats resultats.jsonl] [--echantillon 20]
Prix : PRICE_IN_PER_M / PRICE_OUT_PER_M en dollars par million de jetons (voir .env.example).
"""
import argparse
import csv
import json
import os
import random
from collections import Counter

from dotenv import load_dotenv

load_dotenv()


def charger(avis_csv: str, resultats_jsonl: str):
    with open(avis_csv, newline="", encoding="utf-8") as f:
        avis = {a["id"]: a for a in csv.DictReader(f)}
    classes, tokens_in, tokens_out = {}, 0, 0
    with open(resultats_jsonl, encoding="utf-8") as f:
        for ligne in f:
            try:
                lot = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            tokens_in += lot["tokens_in"]
            tokens_out += lot["tokens_out"]
            for r in lot["resultats"]:
                classes[r["id"]] = r  # idempotent : un id vu deux fois garde une seule ligne
    return avis, classes, tokens_in, tokens_out


def incoherent(note: int, sentiment: str) -> bool:
    """Contrôle automatique gratuit : une note de 1-2 étoiles classée positive (ou 5 classée négative)."""
    return (note <= 2 and sentiment == "positif") or (note >= 5 and sentiment == "negatif")


def statistiques(avis: dict, classes: dict) -> dict:
    lignes = [{**avis[i], **classes[i]} for i in avis if i in classes]
    n = len(lignes) or 1
    return {
        "avis_total": len(avis),
        "avis_classes": len(lignes),
        "manquants": sorted(set(avis) - set(classes)),
        "sentiments": Counter(l["sentiment"] for l in lignes),
        "categories": Counter(l["categorie"] for l in lignes),
        "a_recontacter": sum(l["a_recontacter"] for l in lignes),
        "incoherences_note": [l["id"] for l in lignes if incoherent(int(l["note"]), l["sentiment"])],
        "accord_sentiment": sum(l["sentiment"] == l["sentiment_attendu"] for l in lignes) / n,
        "accord_categorie": sum(l["categorie"] == l["categorie_attendue"] for l in lignes) / n,
        "lignes": lignes,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--avis", default="avis.csv")
    ap.add_argument("--resultats", default="resultats.jsonl")
    ap.add_argument("--echantillon", type=int, default=20)
    a = ap.parse_args()
    avis, classes, t_in, t_out = charger(a.avis, a.resultats)
    s = statistiques(avis, classes)

    champs = ["id", "produit", "note", "texte", "sentiment", "categorie", "a_recontacter"]
    with open("rapport.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        w.writerows(s["lignes"])

    # Échantillon aléatoire (graine fixe) à faire relire par un humain
    ech = random.Random(0).sample(s["lignes"], min(a.echantillon, len(s["lignes"])))
    with open("echantillon_controle.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=champs + ["verdict_humain"], extrasaction="ignore")
        w.writeheader()
        w.writerows({**l, "verdict_humain": ""} for l in ech)
    accord_ech = sum(l["sentiment"] == l["sentiment_attendu"] for l in ech) / (len(ech) or 1)

    prix_in = float(os.environ.get("PRICE_IN_PER_M", "0.10"))
    prix_out = float(os.environ.get("PRICE_OUT_PER_M", "0.40"))
    cout = t_in / 1e6 * prix_in + t_out / 1e6 * prix_out

    m = s["manquants"]
    print(f"Avis classés : {s['avis_classes']}/{s['avis_total']}  (manquants : {len(m)} {m[:5]})")
    print("Sentiments  :", dict(s["sentiments"]))
    print("Catégories  :", dict(s["categories"]))
    print(f"À recontacter : {s['a_recontacter']}")
    print(f"Incohérences note/sentiment : {len(s['incoherences_note'])} {s['incoherences_note'][:10]}")
    print(f"Accord avec les réponses attendues : sentiment {s['accord_sentiment']:.0%}, "
          f"catégorie {s['accord_categorie']:.0%} ; sur l'échantillon de {len(ech)} : {accord_ech:.0%}")
    print(f"Jetons : {t_in} en entrée, {t_out} en sortie ; coût estimé au tarif standard {cout:.4f} $ "
          f"(au tarif Batch, moitié prix : {cout / 2:.4f} $)")
    print("Fichiers : rapport.csv, echantillon_controle.csv")


if __name__ == "__main__":
    main()
