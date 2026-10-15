"""Évalue la recherche : rappel@k sur requetes_eval.json, embeddings contre BM25 (mots-clés).

Usage :  python evaluer.py [k]        (l'index doit exister : python moteur.py indexer)
Coût : 2 appels d'embeddings (28 requêtes, par lots de 20).
"""
import json
import re
import sys

import numpy as np
from rank_bm25 import BM25Okapi

import moteur


def rappel_at_k(trouves: list, pertinents: list, k: int) -> float:
    """Part des produits pertinents présents dans les k premiers résultats."""
    return len(set(trouves[:k]) & set(pertinents)) / len(pertinents)


def mots(texte):
    return re.findall(r"\w+", texte.lower())


def main(k=5):
    vecteurs, produits = moteur.charger_index()
    ids = [p["id"] for p in produits]
    with open("requetes_eval.json", encoding="utf-8") as f:
        jeu = json.load(f)

    embed = moteur.embedder_gemini()
    requetes = embed([moteur.texte_requete(q["requete"]) for q in jeu])
    bm25 = BM25Okapi([mots(moteur.texte_document(p)) for p in produits])

    lignes = []
    for q, vq in zip(jeu, requetes):
        sem = [ids[i] for i, _ in moteur.top_k(vecteurs, vq, k)]
        mc = [ids[i] for i in np.argsort(-bm25.get_scores(mots(q["requete"])))[:k]]
        lignes.append((q, rappel_at_k(sem, q["pertinents"], k), rappel_at_k(mc, q["pertinents"], k), sem))

    print(f"{'langue':<7}{'n':>3}   rappel@{k} embeddings   rappel@{k} BM25")
    for langue in ["fr", "en", "es", "de", "toutes"]:
        sel = [l for l in lignes if langue == "toutes" or l[0]["langue"] == langue]
        print(f"{langue:<7}{len(sel):>3}   {np.mean([l[1] for l in sel]):>17.2f}   {np.mean([l[2] for l in sel]):>13.2f}")

    # Effet de la dimension : troncature des vecteurs 768 (propriété Matryoshka), sans nouvel appel
    for d in (128, 256, 768):
        v, r = moteur.normaliser(vecteurs[:, :d]), moteur.normaliser(requetes[:, :d])
        score = np.mean([rappel_at_k([ids[i] for i, _ in moteur.top_k(v, rq, k)], q["pertinents"], k)
                         for q, rq in zip(jeu, r)])
        print(f"dimension {d:>4} : rappel@{k} = {score:.2f}")

    echecs = [l for l in lignes if l[1] < 1]
    print(f"\nRequêtes imparfaites ({len(echecs)}) :")
    for q, r, _, sem in echecs:
        print(f"  {r:.2f}  « {q['requete']} »  attendu {q['pertinents']}  obtenu {sem}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
