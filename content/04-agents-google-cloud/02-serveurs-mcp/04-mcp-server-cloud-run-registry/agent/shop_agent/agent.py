"""An ADK agent that finds its tools through Agent Registry instead of a hard-coded URL.

It asks the registry for the MCP server called "product-catalog", gets its URL,
and connects with a Google identity token (the Cloud Run service is private).
"""
import os
import subprocess

import google.auth.transport.requests
import google.oauth2.id_token
from google.adk.agents import Agent
from google.adk.integrations.agent_registry import AgentRegistry
from google.adk.models import Gemini

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
DISPLAY_NAME = os.getenv("MCP_SERVER_DISPLAY_NAME", "product-catalog")


def identity_token_header(_context) -> dict:
    """Called by ADK before each MCP connection: Cloud Run needs a Google identity token."""
    try:
        # Works where the code runs as a service account (Cloud Run, Agent Runtime, GCE).
        token = google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), audience)
    except Exception:
        # Local dev with your user account (gcloud auth login).
        token = subprocess.check_output(["gcloud", "auth", "print-identity-token"], text=True).strip()
    return {"Authorization": f"Bearer {token}"}


registry = AgentRegistry(
    project_id=PROJECT,
    location=os.getenv("REGISTRY_LOCATION", "global"),
    header_provider=identity_token_header,
)

# 1. Discover: find the MCP server by its display name.
servers = registry.list_mcp_servers().get("mcpServers", [])
server = next((s for s in servers if s.get("displayName") == DISPLAY_NAME), None)
if server is None:
    raise RuntimeError(f"MCP server '{DISPLAY_NAME}' not found in Agent Registry ({PROJECT}).")

# 2. Its URL (https://...run.app/mcp). The token audience is the base URL, without /mcp.
endpoint = next(i["url"] for p in [server, *server.get("protocols", [])] for i in p.get("interfaces", []))
audience = endpoint.removesuffix("/mcp")

# 3. Turn the registry entry into ADK tools (one per MCP tool).
catalog_tools = registry.get_mcp_toolset(server["name"])

root_agent = Agent(
    name="shop_agent",
    model=Gemini(
        model=os.getenv("MODEL", "gemini-3.5-flash"),
        client_kwargs={"enterprise": True, "location": "global"},
    ),
    description="Answers questions about company products: availability, stock and prices.",
    instruction=(
        "You help employees with product questions. Use the catalog tools: search products "
        "by name or category, then check stock with the SKU. Always give the SKU, price and stock. "
        "Say clearly when a product is out of stock."
    ),
    tools=[catalog_tools],
)
