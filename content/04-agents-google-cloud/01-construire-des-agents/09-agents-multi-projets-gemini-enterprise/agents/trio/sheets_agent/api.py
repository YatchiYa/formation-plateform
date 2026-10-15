"""Appels aux API Google avec le jeton de L'UTILISATEUR : erreurs lisibles pour le modèle, nouvelles tentatives
sur les quotas (429) et pannes passagères (5xx)."""
import functools
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import commun

REESSAYER = {429, 500, 502, 503, 504}


class Refus(Exception):
    """Erreur à renvoyer telle quelle au modèle."""


def appel(url: str, jeton: str, corps: dict | None = None, methode: str | None = None, brut: bool = False):
    req = urllib.request.Request(url, json.dumps(corps).encode() if corps is not None else None,
                                 {"Authorization": f"Bearer {jeton}", "Content-Type": "application/json"}, method=methode)
    for essai in range(4):   # 0,5 s, 1 s, 2 s : absorbe le quota Sheets (60 requêtes/min/utilisateur)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode(errors="replace") if brut else json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in REESSAYER and essai < 3:
                time.sleep(0.5 * 2 ** essai)
                continue
            # 401 : jeton expiré ; 403 : portée absente, API non activée, ou accès bloqué par l'admin ; 400 : requête invalide.
            raise Refus(f"refus ({e.code}) : {e.read().decode(errors='replace')[:500]}")
        except (urllib.error.URLError, TimeoutError) as e:
            if essai < 3:
                time.sleep(0.5 * 2 ** essai)
                continue
            raise Refus(f"service Google injoignable : {e}")


def jeton(tool_context) -> str:
    j = commun.jeton_utilisateur(tool_context)
    if not j:
        raise Refus("Pas de jeton Google : autorisation non configurée sur cet agent (AUTH_ID), ou l'utilisateur n'a "
                    "pas encore cliqué sur « Autoriser » dans Gemini Enterprise (docs/12-1-8).")
    return j


def outil(f):
    """Erreurs (Refus) -> {"status": "error"} pour le modèle, au lieu d'une exception. Un outil peut imposer son
    propre status (ex. « confirmation_requise »)."""
    @functools.wraps(f)   # garde nom, description et paramètres : c'est ce que lit le modèle
    def g(*a, **k):
        try:
            return {"status": "success", **f(*a, **k)}
        except Refus as e:
            return {"status": "error", "error_message": str(e)}
    return g


def q(params: dict) -> str:
    return urllib.parse.urlencode(params, doseq=True)


def id_fichier(lien_ou_id: str) -> str:
    """Id d'un fichier à partir de son lien (…/d/<id>/…) ou de l'id lui-même."""
    m = re.search(r"/d/([\w-]+)", lien_ou_id)
    return m.group(1) if m else lien_ou_id.strip()
