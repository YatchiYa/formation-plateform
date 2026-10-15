"""Mesure la qualité de l'extraction : compare sortie/*.json à la vérité connue des factures générées.

    python evaluer.py            # après python factures.py
"""
import json, sys
from pathlib import Path
from generer_factures import FACTURES

sortie = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("sortie")
ok = total = 0
for numero, fournisseur, d, e, lignes, taux, triche in FACTURES:
    ht = round(sum(q * pu for _, q, pu in lignes), 2)
    attendu = {"numero": numero, "fournisseur": fournisseur, "date_facture": d, "date_echeance": e,
               "total_ht": triche.get("total_ht", ht), "taux_tva": taux,
               "montant_tva": triche.get("tva", round(ht * taux / 100, 2)), "nb_lignes": len(lignes)}
    lu = json.loads((sortie / f"{numero}.json").read_text())
    lu["nb_lignes"] = len(lu["lignes"])
    for champ, valeur in attendu.items():
        total += 1
        ok += lu[champ] == valeur
        if lu[champ] != valeur:
            print("ÉCART", numero, champ, lu[champ], "attendu", valeur)
print(f"champs exacts : {ok}/{total}")
