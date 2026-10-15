"""Agent « stock » : répond sur la disponibilité des articles (données fictives).

Lancer : uvicorn stock_agent:app --port 8101
"""
import os

from google.adk.agents import Agent

from common import MODEL, serve

# Inventaire fictif : référence -> quantités par entrepôt
STOCK = {
    "CHAISE-ERGO": {"nom": "Chaise ergonomique", "lyon": 12, "lille": 0},
    "BUREAU-120": {"nom": "Bureau 120 cm", "lyon": 3, "lille": 5},
    "LAMPE-LED": {"nom": "Lampe LED", "lyon": 0, "lille": 0},
}


def check_stock(sku: str) -> dict:
    """Retourne le stock disponible d'un article, par entrepôt.

    Args:
        sku: référence de l'article, par exemple "CHAISE-ERGO".
    """
    item = STOCK.get(sku.strip().upper())
    if item is None:
        return {"status": "error", "message": f"Référence inconnue : {sku}",
                "references_connues": sorted(STOCK)}
    entrepots = {k: v for k, v in item.items() if k != "nom"}
    return {"status": "ok", "sku": sku.upper(), "nom": item["nom"],
            "par_entrepot": entrepots, "total": sum(entrepots.values())}


root_agent = Agent(
    name="stock_agent",
    model=MODEL,
    description="Donne le stock disponible d'un article (par entrepôt) à partir de sa référence.",
    instruction=("Tu es le service stock. Pour toute question de disponibilité, appelle check_stock. "
                 "Réponds en une phrase avec le total et le détail par entrepôt. "
                 "Tu ne donnes jamais de prix."),
    tools=[check_stock],
)

app = serve(root_agent, port=int(os.environ.get("STOCK_PORT", 8101)))
