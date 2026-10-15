"""Agent TRADUCTION : traduit un texte dans les langues des pays Acme, en respectant le glossaire.

Deux outils :
  - glossaire : les termes imposés pour une langue, et les marques à ne jamais traduire ;
  - verifier_traduction : contrôle automatique (marques conservées, longueur cohérente).
"""
import re

from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun

LANGUES = {"fr": "français", "en": "anglais", "es": "espagnol", "it": "italien", "de": "allemand",
           "nl": "néerlandais", "pt": "portugais", "pl": "polonais"}

# Marques Acme : identiques dans toutes les langues.
MARQUES = ["Acme", "Quechua", "Forclaz", "Simond", "Kalenji", "Kiprun", "Domyos", "Kipsta", "Rockrider",
           "Van Rysel", "Btwin", "Nabaiji", "Olaian", "Tribord", "Itiwit", "Subea", "Wedze", "Inesis", "Artengo",
           "Solognac", "Caperlan"]

# ponytail: glossaire en dur pour le tutoriel ; en vrai, le glossaire de l'équipe localisation (fichier ou API).
GLOSSAIRE = {
    "retrait en magasin": {"en": "in-store pickup", "es": "recogida en tienda", "it": "ritiro in negozio",
                           "de": "Abholung im Geschäft", "nl": "afhalen in de winkel", "pt": "levantamento na loja",
                           "pl": "odbiór w sklepie"},
    "retour gratuit": {"en": "free returns", "es": "devolución gratuita", "it": "reso gratuito",
                       "de": "kostenlose Rücksendung", "nl": "gratis retourneren", "pt": "devolução gratuita",
                       "pl": "darmowy zwrot"},
    "atelier": {"en": "workshop", "es": "taller", "it": "laboratorio", "de": "Werkstatt", "nl": "werkplaats",
                "pt": "oficina", "pl": "warsztat"},
    "seconde vie": {"en": "second life", "es": "segunda vida", "it": "seconda vita", "de": "Second Life",
                    "nl": "tweede leven", "pt": "segunda vida", "pl": "drugie życie"},
}


def glossaire(langue_cible: str) -> dict:
    """Termes imposés et marques à conserver, pour traduire vers une langue.

    Args:
        langue_cible: Code de langue : fr, en, es, it, de, nl, pt ou pl.
    """
    code = langue_cible.strip().lower()[:2]
    if code not in LANGUES:
        return {"status": "error", "error_message": f"Langue non prise en charge. Langues : {', '.join(LANGUES)}."}
    termes = {fr: t[code] for fr, t in GLOSSAIRE.items() if code in t}
    return {"status": "success", "langue": LANGUES[code], "termes_imposes": termes, "marques_a_ne_pas_traduire": MARQUES}


def verifier_traduction(texte_source: str, traduction: str) -> dict:
    """Contrôle une traduction : marques Acme conservées et longueur cohérente.

    Args:
        texte_source: Le texte d'origine.
        traduction: Le texte traduit.
    """
    manquantes = [m for m in MARQUES if re.search(rf"\b{re.escape(m)}\b", texte_source, re.I)
                  and not re.search(rf"\b{re.escape(m)}\b", traduction, re.I)]
    ratio = round(len(traduction) / max(len(texte_source), 1), 2)
    problemes = [f"marque absente de la traduction : {m}" for m in manquantes]
    if not 0.5 <= ratio <= 2:
        problemes.append(f"longueur anormale (rapport {ratio}) : phrase oubliée ou ajoutée ?")
    return {"status": "success", "conforme": not problemes, "problemes": problemes, "rapport_longueur": ratio}


root_agent = Agent(
    name="traduction_agent",
    model=commun.modele(),
    description="Traduit un texte en anglais, espagnol, italien, allemand, néerlandais, portugais ou polonais, en respectant le glossaire et les marques Acme.",
    instruction=(
        "Tu es le traducteur des équipes Acme. Pour chaque demande : "
        "1) si la langue cible manque, demande-la ; 2) appelle glossaire pour cette langue ; s'il renvoie une erreur, "
        "ne traduis pas : dis que la langue n'est pas prise en charge et donne la liste des langues ; "
        "3) traduis fidèlement, avec les termes imposés, sans traduire les marques ; "
        "4) appelle verifier_traduction ; si elle n'est pas conforme, corrige puis vérifie à nouveau. "
        "Réponds avec la traduction seule, puis une ligne « Contrôle : conforme » (ou les corrections faites)."
    ),
    tools=[glossaire, verifier_traduction],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
