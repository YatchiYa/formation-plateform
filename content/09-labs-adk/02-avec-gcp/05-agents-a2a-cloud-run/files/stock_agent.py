"""Agent « stock » exposé en A2A. Il ne connaît que l'entrepôt (données fictives).

Local : uvicorn stock_agent:app --port 8001
Cloud Run : PUBLIC_URL=https://<service>-<numéro>.<région>.run.app (l'URL annoncée dans la carte A2A)
"""
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "http://localhost:8001")

STOCK = {  # référence -> (désignation, quantité disponible, prix unitaire HT en euros)
    "VIS-M6": ("Vis inox M6 x 20", 1200, 0.08),
    "ECR-M6": ("Écrou inox M6", 300, 0.05),
    "RON-M6": ("Rondelle plate M6", 0, 0.02),
}


def verifier_stock(reference: str) -> dict:
    """Donne la quantité disponible et le prix unitaire d'une référence.

    Args:
        reference: la référence article, par exemple « VIS-M6 ».
    """
    ref = reference.strip().upper()
    if ref not in STOCK:
        return {"trouve": False, "references_connues": sorted(STOCK)}
    nom, qte, prix = STOCK[ref]
    return {"trouve": True, "reference": ref, "designation": nom, "disponible": qte, "prix_unitaire_ht": prix}


def modele(nom: str = MODEL) -> Gemini:
    # Réessais avec attente sur 429/503 : le quota Vertex AI est partagé par le projet
    return Gemini(model=nom, retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2))


root_agent = Agent(
    name="agent_stock",
    model=modele(),
    description="Connaît le stock de l'entrepôt : disponibilité et prix unitaire d'une référence.",
    instruction=("Tu gères le stock d'un entrepôt fictif. Utilise verifier_stock pour toute question. "
                 "Réponds en une phrase, en français, avec la référence, la quantité disponible et le prix unitaire."),
    tools=[verifier_stock],
)

_u = urlparse(PUBLIC_URL)
# La carte A2A (/.well-known/agent-card.json) annonce cette URL : elle doit être celle que voient les clients.
app = to_a2a(root_agent, host=_u.hostname, port=_u.port or (443 if _u.scheme == "https" else 80),
             protocol=_u.scheme)
