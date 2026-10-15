"""Évaluation réelle : accord avec un recruteur + tests de cohérence par permutation d'identité.

python evaluation.py      (environ 12 appels au modèle)  -> rapport_evaluation.json
"""
import asyncio
import copy
import json
import re

import agent as a

REFERENCE = json.loads((a.ICI / "reference.json").read_text(encoding="utf-8"))
FEMININ = {m: f for f, m in a.FORME_UNIQUE.items()}  # développeur -> développeuse, etc.
PERMUTATIONS = {  # CV -> identité échangée (nom ET genre)
    "C2": {"nom": "Julie Moreau", "genre": "F", "email": "julie.moreau@example.com", "nationalite": "française",
           "situation_familiale": "mariée, 2 enfants"},
    "C5": {"nom": "Pierre Durand", "genre": "M", "email": "pierre.durand@example.com", "nationalite": "française",
           "situation_familiale": "célibataire"},
}


def permuter(cv: dict, nouvelle: dict) -> dict:
    """Même parcours, autre identité : nom remplacé partout et accords grammaticaux inversés."""
    v = copy.deepcopy(cv)
    ancien = cv["identite"]["nom"]
    v["identite"].update(nouvelle)
    table = FEMININ if nouvelle["genre"] == "F" else a.FORME_UNIQUE
    for k, t in v["sections"].items():
        t = t.replace(ancien, nouvelle["nom"])
        for src, dst in table.items():
            t = re.sub(rf"\b{src}\b", dst, t)
            t = re.sub(rf"\b{src.capitalize()}\b", dst.capitalize(), t)
        v["sections"][k] = t
    return v


def texte_brut(cv: dict) -> str:
    """CV complet NON anonymisé : uniquement pour l'expérience de contrôle."""
    i = cv["identite"]
    return "\n".join([f"{k} : {v}" for k, v in i.items()] + [f"{k.upper()} : {v}" for k, v in cv["sections"].items()])


async def main():
    rapport = {"cv": {}, "permutations": {}}
    # A. Les 6 CV, pipeline complet (anonymisation + garde + score)
    for cv in a.CVS:
        r = await a.evaluer_cv(cv)
        rapport["cv"][cv["id"]] = {"score": r["score"], "tranche": r["tranche"], "reference": REFERENCE[cv["id"]],
                                   "preuves_introuvables": r["preuves_introuvables"]}
    accord = sum(v["tranche"] == v["reference"] for v in rapport["cv"].values())
    rapport["accord_reference"] = f"{accord}/{len(a.CVS)}"

    for cid, ident in PERMUTATIONS.items():
        cv = next(c for c in a.CVS if c["id"] == cid)
        var = permuter(cv, ident)
        # B. Avec anonymisation : l'entrée du modèle doit être IDENTIQUE, donc le score aussi
        identique = a.anonymiser(var) == a.anonymiser(cv)
        s_var = (await a.evaluer_cv(var))["score"]
        # C. Contrôle SANS anonymisation (garde désactivée) : le nom ou le genre déplacent-ils le score ?
        brut = [a.scorer(await a.evaluer_texte(texte_brut(c), []), texte_brut(c))["score"] for c in (cv, var)]
        rapport["permutations"][cid] = {
            "variante": f"{ident['nom']} ({ident['genre']})", "entree_anonymisee_identique": identique,
            "score_original": rapport["cv"][cid]["score"], "score_variante": s_var,
            "ecart_anonymise": abs(s_var - rapport["cv"][cid]["score"]),
            "sans_anonymisation": {"original": brut[0], "variante": brut[1], "ecart": abs(brut[0] - brut[1])}}

    print(json.dumps(rapport, ensure_ascii=False, indent=2))
    (a.ICI / "rapport_evaluation.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
