"""Petite API REST RH fictive (FastAPI) : annuaire, soldes de congés, demandes.

Lancer :  uvicorn api_rh:app --port 8077
Doc interactive : http://127.0.0.1:8077/docs

Toutes les données sont fictives et vivent en mémoire (perdues au redémarrage).
L'identité de l'appelant arrive dans l'en-tête X-Utilisateur. Dans une vraie API,
ce serait un jeton (OAuth, JWT) vérifié par une passerelle ; le principe est le même :
c'est l'API qui décide des droits, jamais le modèle.
"""
import copy
from datetime import date, timedelta
from typing import Literal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="API RH (fictive)")

_EMPLOYES = {
    "E001": {"nom": "Camille Martin", "service": "Comptabilité", "manager": "E004"},
    "E002": {"nom": "Karim Benali", "service": "Comptabilité", "manager": "E004"},
    "E003": {"nom": "Lucie Moreau", "service": "Marketing", "manager": "E005"},
    "E004": {"nom": "Sophie Durand", "service": "Comptabilité", "manager": None},
    "E005": {"nom": "Hugo Lefèvre", "service": "Marketing", "manager": None},
}
_SOLDES = {
    "E001": {"conges_payes": 18, "rtt": 4},
    "E002": {"conges_payes": 7, "rtt": 9},
    "E003": {"conges_payes": 22, "rtt": 2},
    "E004": {"conges_payes": 12, "rtt": 6},
    "E005": {"conges_payes": 25, "rtt": 0},
}
EMPLOYES, SOLDES, DEMANDES = {}, {}, {}


def reset():
    """Remet les données d'exemple (utile pour les tests)."""
    EMPLOYES.clear(); EMPLOYES.update(copy.deepcopy(_EMPLOYES))
    SOLDES.clear(); SOLDES.update(copy.deepcopy(_SOLDES))
    DEMANDES.clear()


reset()


def _verifier_acces(utilisateur: str, employe_id: str):
    if employe_id not in EMPLOYES:
        raise HTTPException(404, f"Employé {employe_id} inconnu")
    if utilisateur != employe_id and EMPLOYES[employe_id]["manager"] != utilisateur:
        raise HTTPException(403, "Accès refusé : vous n'êtes ni l'employé ni son manager")


def jours_ouvres(debut: date, fin: date) -> int:
    """Nombre de jours du lundi au vendredi entre debut et fin inclus (jours fériés ignorés)."""
    return sum((debut + timedelta(d)).weekday() < 5 for d in range((fin - debut).days + 1))


@app.get("/sante")
def sante():
    return {"ok": True}


@app.get("/employes")
def chercher(nom: str):
    n = nom.lower()
    return {"resultats": [{"employe_id": k, "nom": v["nom"], "service": v["service"]}
                          for k, v in EMPLOYES.items() if n in v["nom"].lower()]}


@app.get("/employes/{employe_id}/soldes")
def soldes(employe_id: str, x_utilisateur: str = Header()):
    _verifier_acces(x_utilisateur, employe_id)
    return {"employe_id": employe_id, "unite": "jours", **SOLDES[employe_id]}


@app.get("/employes/{employe_id}/demandes")
def demandes(employe_id: str, x_utilisateur: str = Header()):
    _verifier_acces(x_utilisateur, employe_id)
    return {"demandes": [d for d in DEMANDES.values() if d["employe_id"] == employe_id]}


class NouvelleDemande(BaseModel):
    employe_id: str = Field(pattern=r"^E\d{3}$")
    type_conge: Literal["conges_payes", "rtt"]
    date_debut: date
    date_fin: date


@app.post("/demandes", status_code=201)
def creer(d: NouvelleDemande, x_utilisateur: str = Header()):
    _verifier_acces(x_utilisateur, d.employe_id)
    if d.date_fin < d.date_debut:
        raise HTTPException(422, "date_fin est avant date_debut")
    nb = jours_ouvres(d.date_debut, d.date_fin)
    if nb == 0:
        raise HTTPException(422, "Aucun jour ouvré sur cette période")
    if SOLDES[d.employe_id][d.type_conge] < nb:
        raise HTTPException(409, f"Solde insuffisant : {nb} jours demandés, "
                                 f"{SOLDES[d.employe_id][d.type_conge]} disponibles")
    SOLDES[d.employe_id][d.type_conge] -= nb
    demande_id = f"D{len(DEMANDES) + 1:04d}"
    DEMANDES[demande_id] = {"demande_id": demande_id, "statut": "en_attente", "jours": nb,
                            **d.model_dump(mode="json")}
    return DEMANDES[demande_id]


@app.post("/demandes/{demande_id}/annulation")
def annuler(demande_id: str, x_utilisateur: str = Header()):
    d = DEMANDES.get(demande_id)
    if not d:
        raise HTTPException(404, f"Demande {demande_id} inconnue")
    _verifier_acces(x_utilisateur, d["employe_id"])
    if d["statut"] == "annulee":
        raise HTTPException(409, "Demande déjà annulée")
    d["statut"] = "annulee"
    SOLDES[d["employe_id"]][d["type_conge"]] += d["jours"]
    return d
