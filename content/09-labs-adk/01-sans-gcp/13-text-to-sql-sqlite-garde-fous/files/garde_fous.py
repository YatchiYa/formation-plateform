"""Garde-fous SQL : tout ce qui se passe entre le SQL écrit par le modèle et la base.

Quatre couches, de la plus simple à la plus solide :
  1. contrôle du texte : une seule requête, qui commence par SELECT ou WITH ;
  2. autorisateur SQLite : seules la lecture et les tables de la liste blanche passent
     (vérifié par SQLite lui-même pendant la compilation, pas par une regex) ;
  3. connexion ouverte en lecture seule (mode=ro) ;
  4. LIMIT forcé + délai maximal d'exécution.
"""
import re
import sqlite3
import time
from pathlib import Path

TABLES_AUTORISEES = {"clients", "produits", "commandes", "lignes_commande"}
LIMITE_LIGNES = 50
DELAI_MAX_S = 2.0
FONCTIONS_INTERDITES = {"load_extension", "readfile", "writefile", "edit"}

# Actions SQLite autorisées pendant la compilation d'une requête de lecture.
# Les CTE récursives (WITH RECURSIVE) sont exclues : inutiles pour du reporting,
# et leurs noms apparaîtraient comme des « tables » inconnues.
_ACTIONS_LECTURE = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}
_COMMENTAIRES = re.compile(r"(--[^\n]*)|(/\*.*?\*/)", re.S)


class RequeteRefusee(Exception):
    """La requête ne passe pas les garde-fous ; le message est destiné au modèle."""


def _autorisateur(action, arg1, arg2, _db, _trigger):
    if action not in _ACTIONS_LECTURE:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_READ and arg1 not in TABLES_AUTORISEES:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or "").lower() in FONCTIONS_INTERDITES:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def connecter(chemin: Path) -> sqlite3.Connection:
    """Connexion en lecture seule (mode=ro), surveillée par l'autorisateur."""
    con = sqlite3.connect(f"file:{chemin}?mode=ro", uri=True, check_same_thread=False)
    con.set_authorizer(_autorisateur)
    return con


def valider_sql(con: sqlite3.Connection, sql: str) -> str:
    """Valide SANS exécuter et renvoie la requête nettoyée, ou lève RequeteRefusee."""
    propre = _COMMENTAIRES.sub(" ", sql).strip().rstrip(";").strip()
    if not propre:
        raise RequeteRefusee("Requête vide.")
    # Limite connue : refuse aussi un ';' dans une chaîne ('a;b') ; acceptable pour du reporting.
    if ";" in propre:
        raise RequeteRefusee("Une seule requête à la fois (pas de point-virgule).")
    if not re.match(r"(?is)^(select|with)\b", propre):
        raise RequeteRefusee("Seules les requêtes SELECT (ou WITH ... SELECT) sont permises.")
    try:  # EXPLAIN compile la requête (autorisateur compris) sans lire les données.
        con.execute("EXPLAIN " + propre).fetchall()
    except sqlite3.DatabaseError as e:
        if "not authorized" in str(e) or "prohibited" in str(e):
            raise RequeteRefusee(
                "Accès refusé : seules les tables " + ", ".join(sorted(TABLES_AUTORISEES))
                + " sont lisibles, en lecture seule.") from None
        raise RequeteRefusee(f"SQL invalide : {e}") from None
    return propre


def executer(con: sqlite3.Connection, sql: str, limite: int = LIMITE_LIGNES) -> dict:
    """Valide, force le LIMIT, exécute avec un délai maximal, renvoie un résultat sérialisable."""
    propre = valider_sql(con, sql)
    # limite + 1 pour savoir si le résultat a été tronqué.
    finale = f"SELECT * FROM ({propre}) LIMIT {limite + 1}"
    fin = time.monotonic() + DELAI_MAX_S
    con.set_progress_handler(lambda: int(time.monotonic() > fin), 10_000)
    try:
        cur = con.execute(finale)
        lignes = cur.fetchall()
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e):
            raise RequeteRefusee(f"Requête trop longue (> {DELAI_MAX_S} s).") from None
        raise RequeteRefusee(f"Erreur d'exécution : {e}") from None
    finally:
        con.set_progress_handler(None, 0)
    colonnes = [d[0] for d in cur.description]
    return {"sql_execute": propre, "colonnes": colonnes,
            "lignes": [list(l) for l in lignes[:limite]],
            "nb_lignes": min(len(lignes), limite), "tronque": len(lignes) > limite}


def schema(chemin: Path) -> str:
    """Le schéma des SEULES tables autorisées, lu côté code par une connexion sans autorisateur."""
    con = sqlite3.connect(f"file:{chemin}?mode=ro", uri=True)
    try:
        return "\n".join(
            f"{t}(" + ", ".join(f"{c[1]} {c[2]}" for c in con.execute(f"PRAGMA table_info({t})"))
            + ")" for t in sorted(TABLES_AUTORISEES))
    finally:
        con.close()
