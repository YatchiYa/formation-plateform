"""Génère 4 factures PDF FICTIVES dans factures/ (dont 3 avec une anomalie volontaire).

    python generer_factures.py
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DOSSIER = Path(__file__).with_name("factures")

# (numéro, fournisseur, date, échéance, lignes [(désignation, qté, PU HT)], taux TVA, triche)
# « triche » fausse volontairement un total imprimé pour tester les contrôles.
FACTURES = [
    ("F-2026-0412", "Papeterie des Canuts", "2026-09-30", "2026-10-30",
     [("Ramettes papier A4", 20, 4.50), ("Classeurs à levier", 15, 3.20)], 20.0, {}),
    ("F-2026-0413", "Imprimerie Bellecour", "2026-10-01", "2026-10-31",
     [("Flyers A5 (lot de 500)", 4, 38.00), ("Affiches A2", 10, 6.50)], 20.0, {"total_ht": 237.00}),
    ("F-2026-0414", "Traiteur de la Croix-Rousse", "2026-10-03", "2026-11-02",
     [("Plateaux repas", 12, 14.00)], 10.0, {"tva": 33.60}),
    ("F-2026-0415", "Nettoyage Confluence", "2026-08-20", "2026-09-19",
     [("Entretien des locaux (août)", 1, 480.00)], 20.0, {}),
]


def dessiner(chemin: Path, numero, fournisseur, date, echeance, lignes, taux, triche) -> None:
    ht = round(sum(q * pu for _, q, pu in lignes), 2)
    ht_imprime = triche.get("total_ht", ht)
    tva = triche.get("tva", round(ht * taux / 100, 2))
    ttc = round(ht_imprime + tva, 2)
    c = canvas.Canvas(str(chemin), pagesize=A4)
    y = 800
    def ligne(texte, x=50, taille=10):
        nonlocal y
        c.setFont("Helvetica", taille)
        c.drawString(x, y, texte)
        y -= 18
    ligne(fournisseur, taille=16)
    ligne("12 rue Imaginaire, 69000 Lyon - SIRET 000 000 000 00000 (fictif)")
    y -= 10
    ligne(f"FACTURE N° {numero}", taille=14)
    ligne(f"Date de facture : {date}")
    ligne(f"Date d'échéance : {echeance}")
    ligne("Client : Atelier Formation (fictif)")
    y -= 10
    ligne("Désignation                                  Qté     PU HT     Montant HT")
    for designation, q, pu in lignes:
        ligne(f"{designation:<42} {q:>5} {pu:>9.2f} {q * pu:>12.2f}")
    y -= 10
    ligne(f"Total HT : {ht_imprime:.2f} EUR", x=330)
    ligne(f"TVA {taux:g} % : {tva:.2f} EUR", x=330)
    ligne(f"Total TTC : {ttc:.2f} EUR", x=330, taille=12)
    c.save()


if __name__ == "__main__":
    DOSSIER.mkdir(exist_ok=True)
    for f in FACTURES:
        dessiner(DOSSIER / f"{f[0]}.pdf", *f)
        print("écrit", DOSSIER / f"{f[0]}.pdf")
