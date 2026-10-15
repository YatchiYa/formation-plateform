"""Catalogue FICTIF (compagnies, hôtels et prix inventés pour le lab)."""

TRANSPORTS = [  # prix aller-retour par voyageur
    {"id": "T1", "mode": "avion", "compagnie": "AirExemple", "origine": "Lyon", "destination": "Lisbonne", "duree_h": 2.3, "prix_eur": 189},
    {"id": "T2", "mode": "avion low-cost", "compagnie": "VolMini", "origine": "Lyon", "destination": "Lisbonne", "duree_h": 2.4, "prix_eur": 96},
    {"id": "T3", "mode": "train + avion", "compagnie": "RailAir Démo", "origine": "Lyon", "destination": "Lisbonne", "duree_h": 6.5, "prix_eur": 140},
    {"id": "T4", "mode": "train", "compagnie": "RailFictif", "origine": "Lyon", "destination": "Marseille", "duree_h": 1.7, "prix_eur": 70},
]

HEBERGEMENTS = [  # prix par nuit pour la chambre
    {"id": "H1", "nom": "Hôtel Azulejo (fictif)", "ville": "Lisbonne", "quartier": "Baixa", "prix_nuit": 145, "note": 8.9},
    {"id": "H2", "nom": "Casa do Tejo (fictive)", "ville": "Lisbonne", "quartier": "Alfama", "prix_nuit": 98, "note": 8.4},
    {"id": "H3", "nom": "Auberge Miradouro (fictive)", "ville": "Lisbonne", "quartier": "Bairro Alto", "prix_nuit": 62, "note": 7.6},
    {"id": "H4", "nom": "Hôtel du Vieux-Port (fictif)", "ville": "Marseille", "quartier": "Vieux-Port", "prix_nuit": 120, "note": 8.1},
]

ACTIVITES = [  # prix par voyageur
    {"id": "A1", "nom": "Visite guidée de l'Alfama", "ville": "Lisbonne", "categorie": "culture", "duree_h": 3, "prix_eur": 25},
    {"id": "A2", "nom": "Atelier pastel de nata", "ville": "Lisbonne", "categorie": "gastronomie", "duree_h": 2, "prix_eur": 45},
    {"id": "A3", "nom": "Excursion à Sintra", "ville": "Lisbonne", "categorie": "culture", "duree_h": 8, "prix_eur": 79},
    {"id": "A4", "nom": "Soirée fado", "ville": "Lisbonne", "categorie": "musique", "duree_h": 2.5, "prix_eur": 38},
    {"id": "A5", "nom": "Surf à Carcavelos (initiation)", "ville": "Lisbonne", "categorie": "sport", "duree_h": 3, "prix_eur": 55},
    {"id": "A6", "nom": "Musée des Azulejos", "ville": "Lisbonne", "categorie": "culture", "duree_h": 2, "prix_eur": 8},
]
