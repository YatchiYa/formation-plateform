"""Assistant interne RH/IT, prêt pour Cloud Run (ADK 2.10).

Le dossier qui contient ce fichier EST l'agent : `adk deploy cloud_run` le copie
tel quel et charge `root_agent`. Toutes les données sont fictives.
"""
import json
import os
import sys
import unicodedata

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

load_dotenv()  # lit un .env local s'il existe (jamais committé)

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

# Base de politiques internes FICTIVES (dans un vrai projet : Drive, Confluence, BigQuery…)
POLITIQUES = {
    "conges": "25 jours ouvrés de congés par an, à poser au moins 2 semaines à l'avance dans l'outil RH.",
    "teletravail": "Jusqu'à 2 jours de télétravail par semaine, à déclarer à son responsable le lundi.",
    "notes de frais": "Notes de frais à saisir sous 30 jours avec justificatif ; repas plafonné à 20 euros.",
    "vpn": "Le VPN se lance depuis l'application « Accès distant » ; en cas d'échec, redémarrer puis ouvrir un ticket IT.",
    "mot de passe": "Mot de passe de 14 caractères minimum, changé en libre-service sur le portail identité.",
}

_tickets: list[dict] = []


def journal(evenement: str, **champs) -> None:
    """Écrit une ligne JSON sur la sortie standard.

    Sur Cloud Run, chaque ligne JSON devient une entrée *structurée* de Cloud
    Logging : `severity` est reconnu, les autres champs sont filtrables
    (jsonPayload.evenement = "ticket_ouvert").
    """
    print(json.dumps({"severity": "INFO", "message": evenement, "evenement": evenement, **champs},
                     ensure_ascii=False), file=sys.stdout, flush=True)


def _normaliser(texte: str) -> str:
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return sans_accents.lower().strip()


def chercher_politique(sujet: str) -> dict:
    """Cherche la politique interne sur un sujet (congés, télétravail, notes de frais, VPN, mot de passe).

    Args:
        sujet: le thème de la question, en quelques mots.
    """
    cle = _normaliser(sujet)
    for nom, texte in POLITIQUES.items():
        if nom in cle or cle in nom:
            journal("politique_trouvee", sujet=nom)
            return {"trouve": True, "sujet": nom, "politique": texte}
    journal("politique_absente", sujet=cle)
    return {"trouve": False, "sujets_connus": sorted(POLITIQUES)}


def ouvrir_ticket(categorie: str, resume: str) -> dict:
    """Ouvre un ticket de support interne (catégorie « rh » ou « it »).

    Args:
        categorie: « rh » ou « it ».
        resume: une phrase qui décrit le problème.
    """
    categorie = _normaliser(categorie)
    if categorie not in ("rh", "it"):
        return {"erreur": "categorie doit valoir 'rh' ou 'it'"}
    ticket = {"id": f"TCK-{len(_tickets) + 1:04d}", "categorie": categorie, "resume": resume[:200]}
    _tickets.append(ticket)
    journal("ticket_ouvert", ticket_id=ticket["id"], categorie=categorie)
    return {"statut": "ouvert", **ticket}


root_agent = Agent(
    name="assistant_interne",
    # Réessais avec attente sur 429/503 : le quota Vertex AI est partagé par le projet
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2)),
    description="Assistant interne qui répond sur les politiques RH/IT et ouvre des tickets.",
    instruction=(
        "Tu es l'assistant interne d'une entreprise fictive. Tu réponds en français, en 3 phrases maximum. "
        "Pour toute question sur une règle interne, appelle d'abord chercher_politique et cite la règle. "
        "Si la personne signale un problème qu'elle ne peut pas résoudre seule, appelle ouvrir_ticket "
        "et donne le numéro du ticket. N'invente jamais de règle : si l'outil ne trouve rien, dis-le."
    ),
    tools=[chercher_politique, ouvrir_ticket],
)
