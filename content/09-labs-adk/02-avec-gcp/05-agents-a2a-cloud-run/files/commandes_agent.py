"""Agent « commandes » : prépare un devis et délègue la question du stock à l'agent distant, en A2A.

Local : STOCK_URL=http://localhost:8001 uvicorn commandes_agent:app --port 8002
Cloud Run : STOCK_URL=https://lab-a2a-stock-<numéro>.<région>.run.app ; chaque appel porte un jeton
d'identité Google dont l'audience est STOCK_URL (le service stock est privé).
"""
import os
import time
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool

from stock_agent import modele

load_dotenv()

STOCK_URL = os.environ.get("STOCK_URL", "http://localhost:8001").rstrip("/")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:8002")
TVA = 0.20


class JetonIdentite(httpx.Auth):
    """Ajoute « Authorization: Bearer <jeton d'identité> » à chaque requête vers un service Cloud Run privé.

    Sur Cloud Run, fetch_id_token interroge le serveur de métadonnées : le jeton est celui du compte
    de service du service appelant. Aucune clé, aucun secret à stocker.
    """

    def __init__(self, audience: str):
        self.audience, self._jeton, self._expire = audience, None, 0.0

    def auth_flow(self, request):
        if time.time() > self._expire:
            import google.auth.transport.requests
            from google.oauth2 import id_token
            # Limite connue : appel bloquant (≈ 1 fois par heure grâce au cache), à rendre asynchrone si besoin
            self._jeton = id_token.fetch_id_token(google.auth.transport.requests.Request(), self.audience)
            self._expire = time.time() + 45 * 60  # les jetons d'identité vivent 1 h
        request.headers["Authorization"] = f"Bearer {self._jeton}"
        yield request


def client_http(url: str) -> httpx.AsyncClient:
    """Sans authentification en local (http), avec jeton d'identité vers https (Cloud Run)."""
    auth = JetonIdentite(url) if url.startswith("https://") else None
    return httpx.AsyncClient(auth=auth, timeout=120)


def calculer_devis(quantite: int, prix_unitaire_ht: float) -> dict:
    """Calcule un devis HT, TVA et TTC pour une quantité et un prix unitaire.

    Args:
        quantite: nombre d'unités commandées.
        prix_unitaire_ht: prix d'une unité, hors taxes, en euros.
    """
    if quantite <= 0 or prix_unitaire_ht < 0:
        return {"erreur": "quantité > 0 et prix >= 0 attendus"}
    ht = round(quantite * prix_unitaire_ht, 2)
    return {"total_ht": ht, "tva": round(ht * TVA, 2), "total_ttc": round(ht * (1 + TVA), 2)}


agent_stock_distant = RemoteA2aAgent(
    name="agent_stock",
    description="Agent distant (A2A) qui connaît la disponibilité et le prix unitaire des références.",
    agent_card=f"{STOCK_URL}/.well-known/agent-card.json",
    httpx_client=client_http(STOCK_URL),
)

root_agent = Agent(
    name="agent_commandes",
    model=modele(),
    description="Prépare des devis de commande en vérifiant le stock auprès de l'agent stock.",
    instruction=(
        "Tu prépares des devis pour une entreprise fictive, en français. "
        "Pour connaître la disponibilité et le prix unitaire d'une référence, appelle l'outil agent_stock (un agent distant). "
        "Ensuite, si la quantité demandée est disponible, appelle calculer_devis et donne HT, TVA et TTC ; "
        "sinon, indique la quantité disponible et propose une livraison partielle. N'invente aucun prix."
    ),
    # AgentTool : l'agent distant est appelé comme un outil, puis agent_commandes reprend la main
    tools=[calculer_devis, AgentTool(agent=agent_stock_distant)],
)

_u = urlparse(PUBLIC_URL)
app = to_a2a(root_agent, host=_u.hostname, port=_u.port or (443 if _u.scheme == "https" else 80),
             protocol=_u.scheme)
