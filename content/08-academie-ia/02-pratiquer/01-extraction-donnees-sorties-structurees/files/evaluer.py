"""Compare les extractions au jeu annoté et calcule la précision par champ.

Lancer :  python evaluer.py jeu_annote.jsonl resultats.jsonl
"""
import json
import re
import sys
import unicodedata
from collections import defaultdict


def norm(v):
    """Rend deux valeurs comparables : casse, accents, ponctuation, ordre des listes."""
    if isinstance(v, str):
        v = unicodedata.normalize("NFKD", v).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]", "", v.lower())
    if isinstance(v, list):
        return sorted((norm(x) for x in v), key=repr)
    if isinstance(v, dict):
        return tuple(sorted((k, norm(x)) for k, x in v.items()))
    return v


def projeter(predit, attendu):
    """Ne garde dans les objets prédits que les clés annotées (ex. pas le texte libre `tache`)."""
    if isinstance(attendu, list) and attendu and isinstance(attendu[0], dict) and isinstance(predit, list):
        cles = attendu[0].keys()
        return [{k: p.get(k) for k in cles} for p in predit if isinstance(p, dict)]
    return predit


def evaluer(annotes: list[dict], resultats: dict[str, dict]):
    """Renvoie {(type, champ): [corrects, total]} et la liste des erreurs."""
    scores, erreurs = defaultdict(lambda: [0, 0]), []
    for doc in annotes:
        donnees = (resultats.get(doc["id"]) or {}).get("donnees") or {}
        for champ, attendu in doc["attendu"].items():
            predit = projeter(donnees.get(champ), attendu)
            ok = norm(predit) == norm(attendu)
            s = scores[(doc["type"], champ)]
            s[0] += ok
            s[1] += 1
            if not ok:
                erreurs.append((doc["id"], champ, attendu, predit))
    return scores, erreurs


def revue_utile(annotes, resultats):
    """Les documents envoyés en revue humaine sont-ils ceux qui contiennent des erreurs ?"""
    _, erreurs = evaluer(annotes, resultats)
    faux = {e[0] for e in erreurs}
    revue = {i for i, r in resultats.items() if r.get("a_revoir")}
    return {"docs_avec_erreur": len(faux), "envoyes_en_revue": len(revue),
            "erreurs_attrapees": len(faux & revue), "erreurs_manquees": sorted(faux - revue)}


def main(chemin_annote, chemin_resultats):
    with open(chemin_annote, encoding="utf-8") as f:
        annotes = [json.loads(l) for l in f if l.strip()]
    with open(chemin_resultats, encoding="utf-8") as f:
        resultats = {r["id"]: r for r in map(json.loads, f) if r}
    scores, erreurs = evaluer(annotes, resultats)

    print(f"{'type':13} {'champ':18} précision")
    for (t, champ), (ok, n) in sorted(scores.items()):
        print(f"{t:13} {champ:18} {ok}/{n}  {ok / n:.0%}")
    ok, n = sum(s[0] for s in scores.values()), sum(s[1] for s in scores.values())
    print(f"\nTOTAL : {ok}/{n} champs corrects ({ok / n:.1%})")
    print("\nErreurs :")
    for doc_id, champ, attendu, predit in erreurs:
        print(f"  {doc_id} {champ}: attendu={attendu!r} obtenu={predit!r}")
    print("\nRevue humaine :", revue_utile(annotes, resultats))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "jeu_annote.jsonl",
         sys.argv[2] if len(sys.argv) > 2 else "resultats.jsonl")
