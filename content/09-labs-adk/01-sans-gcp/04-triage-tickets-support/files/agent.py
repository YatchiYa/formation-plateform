"""Triage de tickets de support : un routeur + trois spécialistes (Google ADK 2.10, clé d'API).

Le routeur ne répond jamais lui-même : il transfère (transfer_to_agent) au bon sous-agent.
Chaque spécialiste consulte au besoin son outil métier, puis appelle enregistrer_triage
(priorité + réponse proposée) qui écrit le résultat dans l'état de session.
Données 100 % fictives.
"""
import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import ToolContext

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

PRIORITES = {
    "P1": "bloquant : service inaccessible, paiement en double, faille ou piratage de compte",
    "P2": "gênant mais contournable : fonction dégradée, facture erronée, accès perdu pour une personne",
    "P3": "question ou demande simple : information, modification non urgente",
}
REGLE_PRIORITE = "\n".join(f"- {p} = {d}" for p, d in PRIORITES.items())

FACTURES = {"F-2026-0412": {"montant": 49.0, "statut": "payée", "prelevements": 2},
            "F-2026-0398": {"montant": 19.0, "statut": "impayée", "prelevements": 0}}
SERVICES = {"application web": "opérationnel", "api": "dégradé (latence élevée depuis 9 h)",
            "synchronisation mobile": "opérationnel", "export pdf": "en panne"}


def enregistrer_triage(priorite: str, resume: str, reponse_proposee: str, tool_context: ToolContext) -> dict:
    """Enregistre le triage du ticket. À appeler UNE fois, en dernier.

    Args:
        priorite: "P1", "P2" ou "P3".
        resume: le problème en une phrase.
        reponse_proposee: brouillon de réponse au client (3 phrases max), relu par un humain avant envoi.
    """
    if priorite not in PRIORITES:
        return {"erreur": f"Priorité invalide : {priorite}. Valeurs : P1, P2, P3."}
    tool_context.state["triage"] = {"equipe": tool_context.agent_name, "priorite": priorite,
                                    "resume": resume, "reponse_proposee": reponse_proposee}
    tool_context.actions.skip_summarization = True  # fin du tour : pas d'appel modèle de plus
    return tool_context.state["triage"]


def consulter_facture(numero: str) -> dict:
    """Retrouve une facture (montant, statut, nombre de prélèvements).

    Args:
        numero: par exemple "F-2026-0412".
    """
    return FACTURES.get(numero.upper(), {"erreur": "Facture introuvable."})


def etat_des_services() -> dict:
    """Donne l'état actuel de chaque service de la plateforme."""
    return SERVICES


def specialiste(nom, domaine, outils):
    return Agent(
        name=nom, model=MODEL,
        description=f"Spécialiste {domaine}.",
        instruction=(f"Tu es le spécialiste {domaine} du support. Tu traites le ticket transmis.\n"
                     "Si un outil métier aide (numéro de facture, service cité), appelle-le d'abord.\n"
                     f"Puis appelle enregistrer_triage. Priorités :\n{REGLE_PRIORITE}\n"
                     "La réponse proposée est en français, vouvoie le client et ne promet rien que les outils ne confirment pas."),
        tools=[*outils, enregistrer_triage],
        disallow_transfer_to_parent=True, disallow_transfer_to_peers=True,  # pas de ping-pong entre agents
    )


facturation = specialiste("facturation", "facturation (factures, paiements, remboursements, abonnements, TVA)",
                          [consulter_facture])
technique = specialiste("technique", "technique (bugs, pannes, lenteurs, API, application mobile, exports)",
                        [etat_des_services])
compte = specialiste("compte", "compte utilisateur (connexion, mot de passe, double authentification, "
                     "e-mail, droits des membres, suppression de compte, données personnelles)", [])

root_agent = Agent(
    name="routeur_support",
    model=MODEL,
    description="Reçoit les tickets et les transfère à l'équipe compétente.",
    instruction=("Tu tries les tickets du support. Tu ne réponds JAMAIS toi-même au client : "
                 "transfère immédiatement le ticket au sous-agent compétent (facturation, technique ou compte). "
                 "En cas de doute, choisis l'équipe qui peut résoudre la CAUSE du problème "
                 "(ex. « je ne peux plus me connecter depuis ma carte expirée » -> facturation)."),
    sub_agents=[facturation, technique, compte],
)
