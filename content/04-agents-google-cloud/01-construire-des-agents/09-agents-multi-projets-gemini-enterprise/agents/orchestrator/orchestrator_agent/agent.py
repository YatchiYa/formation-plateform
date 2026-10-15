"""Agent ORCHESTRATEUR, dans le projet Gemini Enterprise (équipe « Magasins »).

Il répond aux vendeurs. Pour le stock, il ne réinvente rien : il délègue à l'agent
spécialiste d'une AUTRE équipe, dans un AUTRE projet GCP.

  1. Découverte : il cherche « stock-agent » dans l'Agent Registry du projet agents
     (aucune URL ni ID en dur ; l'équipe Supply peut redéployer sans prévenir).
  2. Appel : il interroge l'agent sur Agent Runtime avec sa propre identité
     (rôle aiplatform.viewer sur CET agent uniquement, accordé par Terraform).
"""
import functools
import os

import agentplatform
from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.integrations.model_armor import ModelArmorConfig, ModelArmorPlugin
from google.adk.models import Gemini
from google.adk.tools.tool_context import ToolContext

AGENTS_PROJECT = os.getenv("AGENTS_PROJECT", "")
REGISTRY_LOCATION = os.getenv("REGISTRY_LOCATION", "europe-west1")
STOCK_AGENT_DISPLAY_NAME = os.getenv("STOCK_AGENT_DISPLAY_NAME", "stock-agent")


def urn_to_resource(urn: str) -> str:
    """URN Agent Registry d'un agent Agent Runtime -> nom de ressource appelable.

    urn:agent:projects-123:projects:123:locations:europe-west1:aiplatform:reasoningEngines:456   (format réel, 2026)
    urn:agent:projects-123:projects:123:locations:europe-west1:reasoningEngines:456              (format sans « aiplatform »)
      -> projects/123/locations/europe-west1/reasoningEngines/456
    """
    parts = urn.split(":")
    if "reasoningEngines" not in parts:
        raise ValueError(f"Pas un agent Agent Runtime : {urn}")
    i = parts.index("projects", 3)  # le 2e "projects" (le 1er est l'éditeur, "projects-123")
    project, location = parts[i + 1], parts[parts.index("locations", i) + 1]
    engine = parts[parts.index("reasoningEngines") + 1]
    return f"projects/{project}/locations/{location}/reasoningEngines/{engine}"


@functools.cache
def stock_agent_name() -> str:
    """Nom de ressource de l'agent stock : variable STOCK_AGENT, sinon Agent Registry."""
    if os.getenv("STOCK_AGENT"):
        return os.environ["STOCK_AGENT"]
    from google.adk.integrations.agent_registry import AgentRegistry  # import tardif : seulement si on découvre

    agents = AgentRegistry(project_id=AGENTS_PROJECT, location=REGISTRY_LOCATION).list_agents().get("agents", [])
    match = next((a for a in agents if a.get("displayName") == STOCK_AGENT_DISPLAY_NAME), None)
    if match is None:
        raise LookupError(f"'{STOCK_AGENT_DISPLAY_NAME}' absent de l'Agent Registry {AGENTS_PROJECT}/{REGISTRY_LOCATION}.")
    return urn_to_resource(match["agentId"])


async def ask_stock_agent(question: str, tool_context: ToolContext) -> dict:
    """Pose une question de STOCK à l'agent spécialiste de l'équipe Supply.

    Args:
        question: La question complète, avec le code article et le magasin si connus.
    """
    try:
        name = stock_agent_name()
        _, project, _, location, *_ = name.split("/")
        client = agentplatform.Client(project=project, location=location)  # référence gardée : sinon connexion fermée
        remote = client.runtimes.get(name=name)
        # Le spécialiste voit l'utilisateur final (traçabilité) ; l'autorisation, elle, est celle
        # de l'identité de l'orchestrateur. ponytail: une session par appel (sans mémoire), suffisant ici.
        session = await remote.async_create_session(user_id=tool_context.user_id)
        texts = []
        async for event in remote.async_stream_query(user_id=tool_context.user_id, session_id=session["id"], message=question):
            texts += [p["text"] for p in (event.get("content") or {}).get("parts", []) if p.get("text")]
        return {"status": "success", "answer": "\n".join(texts)}
    except Exception as e:  # l'agent explique l'échec au lieu de planter
        return {"status": "error", "error_message": f"Agent stock indisponible : {e}"}


root_agent = Agent(
    name="assistant_magasin",
    model=Gemini(model=os.getenv("MODEL", "gemini-3.5-flash"), client_kwargs={"enterprise": True, "location": "global"}),
    description="Aide les vendeurs Acme : conseils produit, et stock en magasin via l'agent de l'équipe Supply.",
    instruction=(
        "Tu aides les vendeurs en magasin. Pour toute question de stock ou de disponibilité, "
        "appelle ask_stock_agent avec une question complète (code article, magasin) et reformule sa réponse. "
        "Ne devine jamais un stock."
    ),
    tools=[ask_stock_agent],
)

plugins = []
if os.getenv("PROMPT_TEMPLATE"):
    plugins.append(ModelArmorPlugin(config=ModelArmorConfig(
        prompt_template_name=os.environ["PROMPT_TEMPLATE"],
        response_template_name=os.environ["RESPONSE_TEMPLATE"],
        block_on_screening_failure=True,
    )))
elif os.getenv("LOCAL_DEV") != "1":
    raise RuntimeError("PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants (LOCAL_DEV=1 pour un essai local).")

app = App(name="orchestrator_agent", root_agent=root_agent, plugins=plugins)
agent_runtime_app = AdkApp(app=app)
