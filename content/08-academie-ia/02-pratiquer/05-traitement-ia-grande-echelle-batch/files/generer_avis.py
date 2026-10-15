"""Génère des avis clients FICTIFS (aucune donnée réelle) dans avis.csv.

Chaque avis est construit à partir d'un modèle de phrase dont on connaît le sentiment et la
catégorie : ces « réponses attendues » servent plus tard au contrôle qualité.
Usage : python generer_avis.py [--n 200] [--graine 42]
"""
import argparse
import csv
import random

PRODUITS = ["casque audio Kappa", "grille-pain Nimbus", "sac à dos Trek 30", "ventilateur Lumo",
            "moulin à café Moka+", "clavier Orion", "thermos Iso 750", "haut-parleur Pulse"]  # noms masculins : « le {p} »

# (sentiment, catégorie, note possible, phrases)
MODELES = [
    ("positif", "qualite_produit", [4, 5], [
        "Le {p} est solide et très agréable à utiliser, je recommande.",
        "Excellent {p}, finitions impeccables, il fait exactement ce qui est annoncé.",
        "Très content du {p}, la qualité est au rendez-vous pour ce prix.",
    ]),
    ("negatif", "qualite_produit", [1, 2], [
        "Le {p} est tombé en panne au bout de deux semaines, très déçu.",
        "Plastique fragile, le {p} s'est fissuré dès la première utilisation.",
        "Le {p} ne tient pas ses promesses, la batterie ne dure pas une heure.",
    ]),
    ("positif", "livraison", [4, 5], [
        "Livraison du {p} en 24 h, colis parfaitement emballé.",
        "Reçu le {p} avant la date prévue, rien à redire sur l'expédition.",
    ]),
    ("negatif", "livraison", [1, 2], [
        "Commande du {p} reçue avec dix jours de retard et un carton écrasé.",
        "Le suivi indique livré mais je n'ai jamais reçu mon {p}.",
        "Colis du {p} perdu par le transporteur, toujours pas de nouvelles.",
    ]),
    ("negatif", "service_client", [1, 2], [
        "Trois e-mails au service client à propos du {p}, aucune réponse. Je veux être remboursé.",
        "Le conseiller m'a raccroché au nez quand j'ai signalé le défaut du {p}.",
    ]),
    ("positif", "service_client", [4, 5], [
        "Mon {p} avait un défaut, le service client l'a remplacé en deux jours. Bravo.",
        "Conseillère très patiente, elle m'a aidé à configurer le {p}.",
    ]),
    ("negatif", "prix", [2, 3], [
        "Le {p} est correct mais beaucoup trop cher pour ce qu'il offre.",
        "J'ai vu le même {p} 30 % moins cher ailleurs une semaine après mon achat.",
    ]),
    ("neutre", "qualite_produit", [3], [
        "Le {p} fait le travail, sans plus. Ni bon ni mauvais.",
        "{p} conforme à la description. Rien de particulier à signaler.",
    ]),
    ("neutre", "site_web", [3], [
        "Le site est un peu lent pour commander le {p}, mais on finit par y arriver.",
    ]),
    ("negatif", "site_web", [1, 2], [
        "Impossible de payer mon {p} sur le site, la page de paiement plante à chaque fois.",
    ]),
    # Cas difficiles : ironie et avis mitigé, pour voir comment le modèle s'en sort
    ("negatif", "livraison", [1], [
        "Génial, mon {p} est arrivé avec trois semaines de retard. Vraiment bravo.",
    ]),
    ("neutre", "prix", [3], [
        "Le {p} est très bien fait, mais le prix est franchement élevé.",
    ]),
]


def generer(n: int, graine: int) -> list[dict]:
    rnd = random.Random(graine)  # même graine => mêmes avis : le lab est reproductible
    avis = []
    for i in range(1, n + 1):
        sentiment, categorie, notes, phrases = rnd.choice(MODELES)
        produit = rnd.choice(PRODUITS)
        avis.append({
            "id": f"A{i:04d}",
            "produit": produit,
            "note": rnd.choice(notes),
            "texte": rnd.choice(phrases).format(p=produit),
            "sentiment_attendu": sentiment,
            "categorie_attendue": categorie,
        })
    return avis


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--graine", type=int, default=42)
    ap.add_argument("--sortie", default="avis.csv")
    a = ap.parse_args()
    lignes = generer(a.n, a.graine)
    with open(a.sortie, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0]))
        w.writeheader()
        w.writerows(lignes)
    print(f"{len(lignes)} avis écrits dans {a.sortie}")
