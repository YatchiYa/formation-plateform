"""Les outils que le modèle peut appeler : schémas, validation, appels HTTP à l'API RH."""
import os
import re
from datetime import date

import httpx
from google.genai import types

API_URL = os.environ.get("RH_API_URL", "http://127.0.0.1:8077")
# Timeout explicite : sans lui, un appel bloqué fige tout l'assistant.
http = httpx.Client(base_url=API_URL, timeout=httpx.Timeout(5.0, connect=2.0))

ID_EMPLOYE = re.compile(r"^E\d{3}$")
ID_DEMANDE = re.compile(r"^D\d{4}$")
TYPES_CONGE = ("conges_payes", "rtt")


# --- 1. Les déclarations : c'est tout ce que le modèle voit ------------------
DECLARATIONS = [
    types.FunctionDeclaration(
        name="chercher_employe",
        description="Cherche un employé dans l'annuaire par son nom ou une partie du nom. "
                    "Renvoie son identifiant (ex. E002). À appeler AVANT tout autre outil "
                    "quand l'utilisateur donne un nom au lieu d'un identifiant.",
        parameters_json_schema={
            "type": "object",
            "properties": {"nom": {"type": "string", "description": "Ex. « Benali »"}},
            "required": ["nom"]}),
    types.FunctionDeclaration(
        name="consulter_solde",
        description="Donne le solde de congés payés et de RTT (en jours) d'un employé.",
        parameters_json_schema={
            "type": "object",
            "properties": {"employe_id": {"type": "string", "description": "Ex. E001"}},
            "required": ["employe_id"]}),
    types.FunctionDeclaration(
        name="lister_demandes",
        description="Liste les demandes de congés d'un employé, avec leur statut.",
        parameters_json_schema={
            "type": "object",
            "properties": {"employe_id": {"type": "string", "description": "Ex. E001"}},
            "required": ["employe_id"]}),
    types.FunctionDeclaration(
        name="creer_demande_conges",
        description="Crée une demande de congés et débite le solde. Appelle-le directement : "
                    "l'application demande elle-même la confirmation. Dates au format AAAA-MM-JJ.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "employe_id": {"type": "string", "description": "Ex. E001"},
                "type_conge": {"type": "string", "enum": list(TYPES_CONGE)},
                "date_debut": {"type": "string", "description": "AAAA-MM-JJ"},
                "date_fin": {"type": "string", "description": "AAAA-MM-JJ, incluse"}},
            "required": ["employe_id", "type_conge", "date_debut", "date_fin"]}),
    types.FunctionDeclaration(
        name="annuler_demande",
        description="Annule une demande de congés (ex. D0001) et recrédite le solde. "
                    "Appelle-le directement : l'application demande elle-même la confirmation.",
        parameters_json_schema={
            "type": "object",
            "properties": {"demande_id": {"type": "string", "description": "Ex. D0001"}},
            "required": ["demande_id"]}),
]
SENSIBLES = {"creer_demande_conges", "annuler_demande"}


# --- 2. La validation : le schéma guide, le code garantit --------------------
def valider(nom: str, args: dict) -> dict:
    """Renvoie des arguments propres ou lève ValueError avec un message utile au modèle."""
    args = dict(args or {})
    attendus = {d.name: d.parameters_json_schema for d in DECLARATIONS}
    if nom not in attendus:
        raise ValueError(f"Outil inconnu : {nom}")
    schema = attendus[nom]
    inconnus = set(args) - set(schema["properties"])
    if inconnus:
        raise ValueError(f"Arguments non prévus : {sorted(inconnus)}")
    manquants = [k for k in schema["required"] if not str(args.get(k, "")).strip()]
    if manquants:
        raise ValueError(f"Arguments manquants : {manquants}")
    if "employe_id" in args:
        args["employe_id"] = str(args["employe_id"]).strip().upper()
        if not ID_EMPLOYE.match(args["employe_id"]):
            raise ValueError("employe_id doit ressembler à E001 (utilisez chercher_employe)")
    if "demande_id" in args and not ID_DEMANDE.match(str(args["demande_id"])):
        raise ValueError("demande_id doit ressembler à D0001")
    if "nom" in args and not 2 <= len(args["nom"]) <= 60:
        raise ValueError("nom doit faire entre 2 et 60 caractères")
    if nom == "creer_demande_conges":
        if args["type_conge"] not in TYPES_CONGE:
            raise ValueError(f"type_conge doit valoir {TYPES_CONGE}")
        try:
            debut, fin = date.fromisoformat(args["date_debut"]), date.fromisoformat(args["date_fin"])
        except ValueError:
            raise ValueError("Dates attendues au format AAAA-MM-JJ") from None
        if fin < debut:
            raise ValueError("date_fin est avant date_debut")
        if (fin - debut).days > 31:
            raise ValueError("Une demande ne peut pas dépasser 31 jours calendaires")
        if debut < date.today():
            raise ValueError("Impossible de poser un congé dans le passé")
    return args


# --- 3. Les appels HTTP : jamais d'exception vers le modèle, un dict d'erreur ---
def _appel(utilisateur: str, methode: str, chemin: str, **kw) -> dict:
    try:
        r = http.request(methode, chemin, headers={"X-Utilisateur": utilisateur}, **kw)
    except httpx.TimeoutException:
        return {"erreur": "L'API RH n'a pas répondu à temps, réessayez plus tard."}
    except httpx.HTTPError as e:
        return {"erreur": f"API RH injoignable ({type(e).__name__})."}
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text[:200]
        return {"erreur": detail, "code_http": r.status_code}
    return r.json()


def chercher_employe(utilisateur: str, nom: str) -> dict:
    return _appel(utilisateur, "GET", "/employes", params={"nom": nom})


def consulter_solde(utilisateur: str, employe_id: str) -> dict:
    return _appel(utilisateur, "GET", f"/employes/{employe_id}/soldes")


def lister_demandes(utilisateur: str, employe_id: str) -> dict:
    return _appel(utilisateur, "GET", f"/employes/{employe_id}/demandes")


def creer_demande_conges(utilisateur: str, employe_id: str, type_conge: str,
                         date_debut: str, date_fin: str) -> dict:
    return _appel(utilisateur, "POST", "/demandes", json={
        "employe_id": employe_id, "type_conge": type_conge,
        "date_debut": date_debut, "date_fin": date_fin})


def annuler_demande(utilisateur: str, demande_id: str) -> dict:
    return _appel(utilisateur, "POST", f"/demandes/{demande_id}/annulation")


OUTILS = {f.__name__: f for f in (chercher_employe, consulter_solde, lister_demandes,
                                   creer_demande_conges, annuler_demande)}
