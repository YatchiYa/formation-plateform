"""Agent RÉDACTION : reformule un texte selon le canal (e-mail client, fiche produit, message interne, réseau social).

Deux outils :
  - charte_redactionnelle : les règles de ton et de forme du canal ;
  - analyser_texte : mesures objectives (mots, phrases, phrases trop longues), avant et après reformulation.
"""
import re

from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun

# ponytail: charte en dur pour le tutoriel ; en vrai, la lire dans le guide éditorial (source connectée).
CHARTE = {
    "email_client": {"ton": "chaleureux, vouvoiement, positif", "longueur_max_mots": 150,
                     "structure": "salutation, réponse en 1 phrase, détails, solution concrète, formule de politesse",
                     "a_eviter": ["jargon interne", "promesse de délai non garantie", "majuscules pour insister"]},
    "fiche_produit": {"ton": "clair, factuel, orienté usage sportif", "longueur_max_mots": 120,
                      "structure": "bénéfice principal, pour quel sport, caractéristiques clés, entretien",
                      "a_eviter": ["superlatifs non prouvés (le meilleur, révolutionnaire)", "comparaison avec un concurrent"]},
    "message_interne": {"ton": "direct, tutoiement possible, factuel", "longueur_max_mots": 100,
                        "structure": "contexte en 1 phrase, demande ou information, échéance, contact",
                        "a_eviter": ["acronymes non expliqués", "pièces jointes non annoncées"]},
    "reseau_social": {"ton": "enthousiaste, tutoiement, inclusif", "longueur_max_mots": 50,
                      "structure": "accroche, message, appel à l'action",
                      "a_eviter": ["plus de 2 émojis", "plus de 3 hashtags", "données personnelles"]},
}


def charte_redactionnelle(canal: str) -> dict:
    """Règles de ton et de forme Acme pour un canal.

    Args:
        canal: "email_client", "fiche_produit", "message_interne" ou "reseau_social".
    """
    regles = CHARTE.get(canal.strip().lower().replace(" ", "_").replace("-", "_"))
    if regles is None:
        return {"status": "error", "error_message": f"Canal inconnu. Canaux : {', '.join(CHARTE)}."}
    return {"status": "success", "canal": canal, **regles}


def analyser_texte(texte: str) -> dict:
    """Mesures objectives d'un texte : nombre de mots, de phrases, phrases trop longues (plus de 25 mots).

    Args:
        texte: Le texte à analyser.
    """
    phrases = [p for p in re.split(r"(?<=[.!?])\s+", texte.strip()) if re.search(r"\w", p)]
    mots_par_phrase = [len(re.findall(r"\w+(?:['’]\w+)*", p)) for p in phrases]
    total = sum(mots_par_phrase)
    moyenne = round(total / len(phrases), 1) if phrases else 0
    longues = [p for p, n in zip(phrases, mots_par_phrase) if n > 25]
    return {"status": "success", "mots": total, "phrases": len(phrases), "mots_par_phrase": moyenne,
            "phrases_trop_longues": longues, "lisible": moyenne <= 20 and not longues}


root_agent = Agent(
    name="redaction_agent",
    model=commun.modele(),
    description="Reformule et améliore un texte selon le canal (e-mail client, fiche produit, message interne, réseau social) et la charte Acme.",
    instruction=(
        "Tu es l'assistant rédaction des équipes Acme. Quand on te donne un texte à reformuler : "
        "1) si le canal n'est pas précisé, demande-le en proposant les 4 canaux ; "
        "2) appelle charte_redactionnelle pour ce canal ; 3) appelle analyser_texte sur le texte d'origine ; "
        "4) écris la nouvelle version en respectant la charte (ton, structure, longueur maximale) ; "
        "5) appelle analyser_texte sur ta version et vérifie qu'elle respecte la longueur maximale, sinon raccourcis. "
        "Réponds avec : la nouvelle version, puis une ligne « Avant : X mots, après : Y mots ». "
        "Tu n'inventes jamais de prix, de délai ou de caractéristique produit absents du texte d'origine."
    ),
    tools=[charte_redactionnelle, analyser_texte],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
