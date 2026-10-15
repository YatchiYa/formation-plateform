"""Agent Conseil taille : la bonne taille de vêtement ou de chaussure à partir des mesures du client.

Deux outils :
  - taille_vetement : taille (XS à 3XL) à partir du tour de poitrine, ou du tour de taille pour un bas ;
  - pointure : pointure européenne à partir de la longueur du pied.
"""
from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun

# ponytail: guide générique pour la démo ; en vrai, le guide des tailles de chaque marque (source connectée ou API).
HAUT = [("XS", 84), ("S", 92), ("M", 100), ("L", 108), ("XL", 116), ("XXL", 124), ("3XL", 132)]   # tour de poitrine max (cm)
BAS = [("XS", 70), ("S", 78), ("M", 86), ("L", 94), ("XL", 102), ("XXL", 110), ("3XL", 118)]      # tour de taille max (cm)


def taille_vetement(type_vetement: str, mesure_cm: float) -> dict:
    """Taille de vêtement conseillée.

    Args:
        type_vetement: "haut" (t-shirt, veste, polaire : tour de poitrine) ou "bas" (pantalon, short : tour de taille).
        mesure_cm: Le tour de poitrine (haut) ou de taille (bas), en centimètres.
    """
    guide = {"haut": HAUT, "bas": BAS}.get(type_vetement.strip().lower())
    if guide is None:
        return {"status": "error", "error_message": "type_vetement doit valoir « haut » ou « bas »."}
    if not 50 <= mesure_cm <= 160:
        return {"status": "error", "error_message": "Mesure hors limites (50 à 160 cm) : vérifier l'unité."}
    for i, (taille, maxi) in enumerate(guide):
        if mesure_cm <= maxi:
            entre_deux = i + 1 < len(guide) and maxi - mesure_cm <= 2
            return {"status": "success", "taille": taille, "mesure_cm": mesure_cm,
                    "conseil": f"entre {taille} et {guide[i + 1][0]} : {guide[i + 1][0]} pour plus d'aisance" if entre_deux else ""}
    return {"status": "success", "taille": guide[-1][0], "mesure_cm": mesure_cm, "conseil": "au-delà du guide : essayer en magasin"}


def pointure(longueur_pied_cm: float, activite: str = "") -> dict:
    """Pointure européenne conseillée à partir de la longueur du pied.

    Args:
        longueur_pied_cm: Longueur du pied, talon contre un mur, en centimètres.
        activite: "course", "randonnée" ou autre ; pour la course et la randonnée on ajoute une marge.
    """
    if not 15 <= longueur_pied_cm <= 35:
        return {"status": "error", "error_message": "Longueur hors limites (15 à 35 cm)."}
    marge = 1.0 if activite.strip().lower() in ("course", "course à pied", "running", "randonnée", "rando") else 0.5
    taille = round((longueur_pied_cm + marge) * 1.5)
    return {"status": "success", "pointure_eu": taille, "marge_cm": marge,
            "conseil": "le pied gonfle à l'effort : prendre la pointure du soir" if marge == 1.0 else ""}


root_agent = Agent(
    name="taille_agent",
    model=commun.modele(),
    description="Conseille la bonne taille de vêtement ou de chaussure à partir des mesures du client.",
    instruction=(
        "Tu conseilles la taille des vêtements et chaussures. Pour un vêtement, appelle taille_vetement ; pour une "
        "chaussure, appelle pointure. S'il manque une mesure, demande-la et explique comment la prendre "
        "(mètre ruban sous les bras pour la poitrine, au nombril pour la taille ; talon contre un mur pour le pied). "
        "Réponds en 3 lignes maximum. Rappelle que l'essai en magasin reste le plus sûr."
    ),
    tools=[taille_vetement, pointure],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
