"""Agent SPÉCIALISTE, publié par l'équipe « Supply » dans SON projet GCP (projet agents).

Il ne sait faire qu'une chose : dire le stock d'un produit par magasin.
D'autres équipes le réutilisent sans copier son code :
  - dans Gemini Enterprise (ajouté à l'app depuis un autre projet) ;
  - depuis un autre agent (l'orchestrateur), qui le trouve dans Agent Registry.
"""
import os

from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.integrations.model_armor import ModelArmorConfig, ModelArmorPlugin
from google.adk.models import Gemini

# ponytail: stock en dur pour la démo ; brancher l'API stock réelle (derrière Agent Gateway).
STOCK = {
    "8771234": {"produit": "Tente 2 secondes 2 places", "lille": 12, "lyon": 0, "paris-la-defense": 4},
    "8559876": {"produit": "Gourde inox 1 L", "lille": 140, "lyon": 85, "paris-la-defense": 0},
}


def get_store_stock(sku: str, store: str = "") -> dict:
    """Stock d'un produit, dans un magasin ou dans tous les magasins.

    Args:
        sku: Code article Acme, ex. "8771234".
        store: Magasin (lille, lyon, paris-la-defense). Vide = tous les magasins.
    """
    item = STOCK.get(sku.strip())
    if item is None:
        return {"status": "error", "error_message": f"Article {sku} inconnu."}
    stores = {k: v for k, v in item.items() if k != "produit"}
    if store:
        key = store.strip().lower()
        if key not in stores:
            return {"status": "error", "error_message": f"Magasin {store} inconnu. Connus : {', '.join(stores)}."}
        stores = {key: stores[key]}
    return {"status": "success", "produit": item["produit"], "stock": stores}


root_agent = Agent(
    name="stock_agent",
    model=Gemini(model=os.getenv("MODEL", "gemini-3.5-flash"), client_kwargs={"enterprise": True, "location": "global"}),
    description="Donne le stock d'un article Acme par magasin, à partir de son code article (SKU).",
    instruction=(
        "Tu réponds uniquement aux questions de stock. Appelle toujours get_store_stock. "
        "Donne le nom du produit et le stock par magasin. Dis clairement si un magasin est en rupture."
    ),
    tools=[get_store_stock],
)

plugins = []
if os.getenv("PROMPT_TEMPLATE"):
    plugins.append(ModelArmorPlugin(config=ModelArmorConfig(
        prompt_template_name=os.environ["PROMPT_TEMPLATE"],
        response_template_name=os.environ["RESPONSE_TEMPLATE"],
        block_on_screening_failure=True,
    )))
elif os.getenv("LOCAL_DEV") != "1":  # Gemini Enterprise ne filtre pas les agents personnalisés : l'agent le fait
    raise RuntimeError("PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants (LOCAL_DEV=1 pour un essai local).")

app = App(name="stock_agent", root_agent=root_agent, plugins=plugins)
agent_runtime_app = AdkApp(app=app)


if __name__ == "__main__":
    assert get_store_stock("8771234", "Lyon") == {"status": "success", "produit": "Tente 2 secondes 2 places", "stock": {"lyon": 0}}
    assert get_store_stock("0000000")["status"] == "error"
    assert get_store_stock("8559876", "marseille")["status"] == "error"
    print("stock_agent OK")
