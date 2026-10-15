"""Agent ADK qui consomme deux serveurs MCP locaux (stdio) : SQLite de commandes + fichiers en lecture seule."""
import os
import sys
from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

ICI = Path(__file__).resolve().parent


def serveur(script: str, **env: str) -> StdioConnectionParams:
    """Paramètres pour lancer un serveur MCP Python comme sous-processus (même interpréteur)."""
    return StdioConnectionParams(
        # env : ajouté aux seules variables « sûres » (PATH, HOME...) ; la clé d'API n'est PAS transmise.
        server_params=StdioServerParameters(command=sys.executable, args=[str(ICI / script)], env=env),
        timeout=20,  # secondes pour démarrer le serveur et répondre
    )


commandes = McpToolset(
    connection_params=serveur("commandes_server.py",
                              COMMANDES_DB=os.environ.get("COMMANDES_DB", str(ICI / "commandes.db"))),
    tool_filter=["lister_tables", "executer_select"],  # annuler_commande n'est PAS exposé au modèle
)

fichiers = McpToolset(
    connection_params=serveur("fichiers_server.py", DOCS_ROOT=os.environ.get("DOCS_ROOT", str(ICI / "docs"))),
    tool_name_prefix="docs",  # les outils deviennent docs_lister_documents, docs_lire_document
)

root_agent = Agent(
    name="analyste_commandes",
    model=os.environ.get("MODEL", "gemini-3.5-flash"),
    description="Répond aux questions sur les commandes en croisant la base et les règles internes.",
    instruction="""Tu es l'analyste des commandes d'une boutique de vélos. Réponds en français.
- Pour les chiffres : appelle d'abord lister_tables pour connaître le schéma, puis executer_select.
  N'invente jamais un chiffre : chaque nombre cité vient d'une requête.
- Pour les règles (retours, livraison, promotions) : docs_lister_documents puis docs_lire_document.
- Tu ne peux rien modifier. Si on te demande une action (annuler, rembourser), explique ce que
  disent les règles et indique qu'un humain doit la faire.
- Termine par une ligne « Sources : » listant les tables et documents utilisés.""",
    tools=[commandes, fichiers],
)
