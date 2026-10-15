"""Orchestrateur : découvre les agents du registre, puis leur délègue en A2A.

Lancer (après les deux spécialistes) : uvicorn orchestrator:app --port 8100
"""
import json
import os
from pathlib import Path

import httpx
from fastapi.openapi.models import HTTPBearer
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.auth.auth_credential import (AuthCredential, AuthCredentialTypes, HttpAuth,
                                             HttpCredentials)
from google.adk.tools.agent_tool import AgentTool

from common import CARD_PATH, MODEL, a2a_token, serve

REGISTRY = Path(os.environ.get("A2A_REGISTRY", Path(__file__).with_name("registry.json")))
CALL_TIMEOUT = float(os.environ.get("A2A_TIMEOUT", 30))  # délai max d'un appel à un agent distant


def discover(registry_path: Path = REGISTRY, timeout: float = 2.0) -> tuple[list[dict], list[str]]:
    """Lit le registre et récupère l'Agent Card de chaque agent joignable.

    Retourne (agents_disponibles, noms_indisponibles). Un agent qui ne répond pas
    en `timeout` secondes est écarté : l'orchestrateur démarre quand même.
    """
    found, missing = [], []
    for entry in json.loads(registry_path.read_text(encoding="utf-8"))["agents"]:
        url = entry["url"].rstrip("/") + CARD_PATH
        try:
            card = httpx.get(url, timeout=timeout).raise_for_status().json()
            found.append({"name": card["name"], "description": card.get("description", ""),
                          "skills": [s.get("name") for s in card.get("skills", [])], "card_url": url})
        except (httpx.HTTPError, ValueError, KeyError):
            missing.append(entry["name"])
    return found, missing


def bearer_auth(token: str):
    """Schéma + identifiant : ADK ajoute « Authorization: Bearer … » à chaque appel A2A."""
    cred = AuthCredential(auth_type=AuthCredentialTypes.HTTP,
                          http=HttpAuth(scheme="bearer", credentials=HttpCredentials(token=token)))
    return HTTPBearer(), cred


def build_orchestrator(found: list[dict], missing: list[str], token: str) -> Agent:
    scheme, cred = bearer_auth(token)
    remotes = [RemoteA2aAgent(name=a["name"], description=a["description"], agent_card=a["card_url"],
                              timeout=CALL_TIMEOUT, auth_scheme=scheme, auth_credential=cred)
               for a in found]
    catalogue = "\n".join(f"- {a['name']} : {a['description']}" for a in found) or "- (aucun)"
    absent = ", ".join(missing) or "aucun"
    return Agent(
        name="orchestrator",
        model=MODEL,
        description="Répond aux demandes de devis en combinant stock et tarification.",
        instruction=(
            "Tu es l'orchestrateur des devis. Agents disponibles :\n" + catalogue +
            f"\nAgents indisponibles en ce moment : {absent}.\n"
            "Pour une demande de devis : interroge le stock ET le prix (outils séparés), puis rédige "
            "une réponse unique en français avec la disponibilité et le total HT. "
            "Transmets à chaque agent une demande autonome et précise (référence, quantité). "
            "Si un agent est indisponible ou renvoie une erreur, dis-le clairement et donne "
            "uniquement l'information obtenue. N'invente jamais un stock ni un prix."),
        tools=[AgentTool(agent=r) for r in remotes],  # l'orchestrateur garde la main et combine
    )


found, missing = discover()
root_agent = build_orchestrator(found, missing, a2a_token())
app = serve(root_agent, port=int(os.environ.get("ORCH_PORT", 8100)))
