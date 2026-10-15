"""Crée ventes.db : une base SQLite de ventes 100 % fictive et reproductible.

    python creer_base.py            # écrit ventes.db à côté de ce fichier
"""
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

BASE = Path(__file__).with_name("ventes.db")

VILLES = ["Lyon", "Lille", "Nantes", "Bordeaux", "Marseille", "Rennes"]
SEGMENTS = ["particulier", "professionnel"]
PRODUITS = [  # (nom, catégorie, prix TTC en euros)
    ("Gourde isotherme 500 ml", "maison", 24.90),
    ("Mug céramique", "maison", 12.50),
    ("Lampe de bureau LED", "maison", 39.00),
    ("Sac à dos 20 L", "sport", 59.00),
    ("Tapis de yoga", "sport", 29.90),
    ("Corde à sauter", "sport", 9.90),
    ("Carnet A5 pointillé", "papeterie", 7.50),
    ("Stylo plume", "papeterie", 18.00),
    ("Agenda 2026", "papeterie", 14.90),
    ("Écouteurs filaires", "high-tech", 19.90),
    ("Chargeur USB-C 30 W", "high-tech", 25.00),
    ("Clavier sans fil", "high-tech", 49.00),
]
STATUTS = ["livree"] * 8 + ["annulee", "en_cours"]


def creer(chemin: Path = BASE, graine: int = 42) -> Path:
    rnd = random.Random(graine)
    chemin.unlink(missing_ok=True)
    con = sqlite3.connect(chemin)
    con.executescript("""
        CREATE TABLE clients (id INTEGER PRIMARY KEY, nom TEXT, ville TEXT,
                              segment TEXT, date_inscription TEXT);
        CREATE TABLE produits (id INTEGER PRIMARY KEY, nom TEXT, categorie TEXT,
                               prix REAL);
        CREATE TABLE commandes (id INTEGER PRIMARY KEY, client_id INTEGER
                                REFERENCES clients(id), date_commande TEXT, statut TEXT);
        CREATE TABLE lignes_commande (commande_id INTEGER REFERENCES commandes(id),
                                      produit_id INTEGER REFERENCES produits(id),
                                      quantite INTEGER, prix_unitaire REAL);
        -- Table sensible : elle existe dans la base mais l'agent ne doit JAMAIS la lire.
        CREATE TABLE comptes_internes (id INTEGER PRIMARY KEY, identifiant TEXT,
                                       mot_de_passe_hash TEXT);
    """)
    for i in range(1, 61):
        inscrit = date(2025, 1, 1) + timedelta(days=rnd.randint(0, 500))
        con.execute("INSERT INTO clients VALUES (?,?,?,?,?)",
                    (i, f"Client {i:03d}", rnd.choice(VILLES), rnd.choice(SEGMENTS),
                     inscrit.isoformat()))
    con.executemany("INSERT INTO produits VALUES (?,?,?,?)",
                    [(i, *p) for i, p in enumerate(PRODUITS, 1)])
    for c in range(1, 401):
        jour = date(2026, 1, 1) + timedelta(days=rnd.randint(0, 272))  # jusqu'à fin sept. 2026
        con.execute("INSERT INTO commandes VALUES (?,?,?,?)",
                    (c, rnd.randint(1, 60), jour.isoformat(), rnd.choice(STATUTS)))
        for pid in rnd.sample(range(1, len(PRODUITS) + 1), rnd.randint(1, 3)):
            con.execute("INSERT INTO lignes_commande VALUES (?,?,?,?)",
                        (c, pid, rnd.randint(1, 4), PRODUITS[pid - 1][2]))
    con.executemany("INSERT INTO comptes_internes VALUES (?,?,?)",
                    [(1, "admin", "fictif-hash-1"), (2, "compta", "fictif-hash-2")])
    con.commit()
    con.close()
    return chemin


if __name__ == "__main__":
    print("Base créée :", creer())
