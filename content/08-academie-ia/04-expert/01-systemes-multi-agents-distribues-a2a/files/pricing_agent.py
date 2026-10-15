"""Agent « tarification » : calcule un prix avec remise sur volume (données fictives).

Lancer : uvicorn pricing_agent:app --port 8102
"""
import os

from google.adk.agents import Agent

from common import MODEL, serve

PRIX_UNITAIRE = {"CHAISE-ERGO": 189.0, "BUREAU-120": 329.0, "LAMPE-LED": 39.9}
# (quantité minimale, remise) : du palier le plus haut au plus bas
PALIERS = [(20, 0.15), (10, 0.10), (5, 0.05)]


def quote_price(sku: str, quantity: int) -> dict:
    """Calcule le prix total HT d'une commande, remise sur volume comprise.

    Args:
        sku: référence de l'article, par exemple "CHAISE-ERGO".
        quantity: nombre d'unités (entier positif).
    """
    sku = sku.strip().upper()
    if sku not in PRIX_UNITAIRE:
        return {"status": "error", "message": f"Pas de tarif pour {sku}"}
    if quantity < 1:
        return {"status": "error", "message": "La quantité doit être >= 1"}
    remise = next((r for seuil, r in PALIERS if quantity >= seuil), 0.0)
    total = round(PRIX_UNITAIRE[sku] * quantity * (1 - remise), 2)
    return {"status": "ok", "sku": sku, "quantite": quantity, "prix_unitaire_ht": PRIX_UNITAIRE[sku],
            "remise": remise, "total_ht": total}


root_agent = Agent(
    name="pricing_agent",
    model=MODEL,
    description="Calcule le prix HT d'un article pour une quantité donnée, remise sur volume comprise.",
    instruction=("Tu es le service tarification. Appelle toujours quote_price ; n'invente jamais un prix. "
                 "Réponds en une phrase : prix unitaire, remise appliquée, total HT."),
    tools=[quote_price],
)

app = serve(root_agent, port=int(os.environ.get("PRICING_PORT", 8102)))
