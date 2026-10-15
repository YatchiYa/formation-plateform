"""Serveur MCP (stdio) qui expose une base SQLite de commandes fictives.

    python commandes_server.py            # démarre le serveur (normalement lancé par l'agent)
    python commandes_server.py --reset    # recrée la base d'exemple

SDK `mcp` 2.x : la classe s'appelle MCPServer (anciennement FastMCP en 1.x).
"""
import os
import re
import sqlite3
import sys
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

DB = Path(os.environ.get("COMMANDES_DB", Path(__file__).with_name("commandes.db")))
MAX_LIGNES = 50

mcp = MCPServer("commandes", instructions="Base de commandes d'une boutique de vélos fictive.")


def creer_base(chemin: Path = DB) -> None:
    """Crée une petite base d'exemple, entièrement fictive."""
    chemin.unlink(missing_ok=True)
    c = sqlite3.connect(chemin)
    c.executescript("""
    CREATE TABLE clients (id INTEGER PRIMARY KEY, nom TEXT, ville TEXT, segment TEXT);
    CREATE TABLE produits (id INTEGER PRIMARY KEY, libelle TEXT, categorie TEXT, prix_ttc REAL);
    CREATE TABLE commandes (id INTEGER PRIMARY KEY, client_id INTEGER REFERENCES clients(id),
        produit_id INTEGER REFERENCES produits(id), quantite INTEGER, date_commande TEXT, statut TEXT);
    INSERT INTO clients VALUES (1,'Cyclo Rapide SARL','Lyon','pro'), (2,'Camille Martin','Grenoble','particulier'),
        (3,'Atelier du Rhône','Villeurbanne','pro'), (4,'Sacha Bernard','Annecy','particulier');
    INSERT INTO produits VALUES (1,'Chambre à air 28 pouces','entretien',8.5), (2,'Kit de nettoyage','entretien',24.9),
        (3,'Roue arrière renforcée','pieces',129.0), (4,'Cadre sur mesure acier','sur-mesure',890.0),
        (5,'Éclairage USB','accessoires',39.9);
    INSERT INTO commandes VALUES
        (101,1,1,40,'2026-09-03','livree'), (102,1,2,10,'2026-09-18','livree'), (103,2,5,1,'2026-09-21','livree'),
        (104,3,3,4,'2026-09-25','expediee'), (105,4,4,1,'2026-09-28','livree'), (106,2,3,1,'2026-10-02','en_preparation'),
        (107,3,2,6,'2026-10-06','en_preparation'), (108,1,5,12,'2026-10-09','expediee');
    """)
    c.commit()
    c.close()


def _lecture_seule() -> sqlite3.Connection:
    if not DB.exists():
        creer_base()
    # mode=ro : même si une requête d'écriture passait le filtre, SQLite la refuserait.
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def lister_tables() -> dict:
    """Liste les tables de la base et leurs colonnes (nom et type)."""
    with _lecture_seule() as c:
        tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        return {t: [f"{col[1]} {col[2]}" for col in c.execute(f"PRAGMA table_info({t})")] for t in tables}


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def executer_select(sql: str) -> dict:
    """Exécute UNE requête SQL SELECT (SQLite) en lecture seule et renvoie au plus 50 lignes.

    Args:
        sql: une requête SELECT ou WITH ... SELECT. Toute autre instruction est refusée.
    """
    requete = sql.strip().rstrip(";")
    if ";" in requete or not re.match(r"(?is)^\s*(select|with)\b", requete):
        return {"erreur": "Seules les requêtes SELECT uniques sont autorisées."}
    try:
        with _lecture_seule() as c:
            cur = c.execute(requete)
            lignes = cur.fetchmany(MAX_LIGNES + 1)
            return {"colonnes": [d[0] for d in cur.description], "lignes": lignes[:MAX_LIGNES],
                    "tronque": len(lignes) > MAX_LIGNES}
    except sqlite3.Error as e:
        return {"erreur": f"SQLite : {e}"}  # renvoyée au modèle, qui peut corriger sa requête


@mcp.tool(annotations=ToolAnnotations(destructive_hint=True))
def annuler_commande(commande_id: int) -> dict:
    """Annule une commande (écriture). Exposé par le serveur, mais filtré côté agent."""
    with sqlite3.connect(DB) as c:
        n = c.execute("UPDATE commandes SET statut='annulee' WHERE id=?", (commande_id,)).rowcount
    return {"commande_id": commande_id, "annulee": bool(n)}


if __name__ == "__main__":
    if "--reset" in sys.argv:
        creer_base()
        print(f"Base recréée : {DB}")
    else:
        mcp.run()  # transport stdio par défaut
