"""Agent Retours produits : un produit peut-il être retourné ou échangé, dans quel délai, comment.

Un outil : regles_retour, qui applique les règles de retour à une situation (catégorie, jours depuis l'achat, état).
"""
from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun

# ponytail: règles de DÉMONSTRATION ; à remplacer par la politique de retour officielle (source connectée ou API).
DELAI_JOURS = {"standard": 365, "electronique": 30, "personnalise": 0, "hygiene": 0}
CATEGORIES = {
    "standard": ["textile", "chaussures", "camping", "vélo", "velo", "sport"],
    "electronique": ["montre", "gps", "cardio", "électronique", "electronique", "trottinette électrique"],
    "personnalise": ["personnalisé", "personnalise", "floqué", "floque"],
    "hygiene": ["maillot de bain", "sous-vêtement", "sous-vetement", "protège-dents", "protege-dents"],
}


def regles_retour(categorie_produit: str, jours_depuis_achat: int, etat: str = "neuf") -> dict:
    """Peut-on retourner ce produit ? Délai restant et procédure.

    Args:
        categorie_produit: Type de produit, ex. "chaussures", "montre GPS", "maillot de bain", "maillot floqué".
        jours_depuis_achat: Nombre de jours depuis l'achat.
        etat: "neuf" (avec étiquettes), "utilisé" ou "défectueux".
    """
    texte = categorie_produit.strip().lower()
    famille = next((f for f, mots in CATEGORIES.items() if any(m in texte for m in mots)), "standard")
    if etat.strip().lower().startswith("défect") or etat.strip().lower().startswith("defect"):
        return {"status": "success", "retour_possible": True, "motif": "produit défectueux : garantie légale",
                "procedure": "atelier ou service client, avec la preuve d'achat"}
    delai = DELAI_JOURS[famille]
    if delai == 0:
        return {"status": "success", "retour_possible": False, "famille": famille,
                "motif": "produit personnalisé ou d'hygiène : ni repris ni échangé (sauf défaut)"}
    if jours_depuis_achat > delai:
        return {"status": "success", "retour_possible": False, "famille": famille, "delai_jours": delai,
                "motif": f"délai de {delai} jours dépassé"}
    return {"status": "success", "retour_possible": True, "famille": famille, "delai_jours": delai,
            "jours_restants": delai - jours_depuis_achat,
            "procedure": "en magasin ou par colis, avec la preuve d'achat (ticket ou compte client)"}


root_agent = Agent(
    name="retour_agent",
    model=commun.modele(),
    description="Dit si un produit peut être retourné ou échangé, avec quel délai et comment, selon les règles de retour.",
    instruction=(
        "Tu réponds aux questions de retour et d'échange. Appelle toujours regles_retour ; s'il manque la date "
        "d'achat ou l'état du produit, demande-les. Dis clairement oui ou non, le délai restant et la procédure. "
        "Ne promets jamais un remboursement : renvoie vers le magasin pour la décision finale."
    ),
    tools=[regles_retour],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
