"""Explorer l'Agent Registry d'un projet (le sien ou celui d'une autre équipe).

À quoi sert ce script
  Liste ce qu'un projet a déclaré dans son Agent Registry (le catalogue des agents) : agents, serveurs MCP,
  endpoints. Pour chaque agent, il dit comment l'ajouter à Gemini Enterprise avec scripts/add_agent_to_ge.sh :
  « adk <nom de ressource> » (agent Agent Runtime) ou « a2a <URL de la carte> » (agent A2A).

Quand l'utiliser
  - docs/04, partie 2 (lire l'entrée de registre d'un agent qu'une équipe veut ajouter) ;
  - docs/09 et docs/10 (trouver les agents d'une équipe) ;
  - docs/05 (erreur « 'stock-agent' absent de l'Agent Registry »).

Prérequis
  - Dans le dossier du projet, venv activé (source .venv/bin/activate) : il faut le paquet google-adk.
  - Identifiants Python : gcloud auth application-default login (une fois).
  - Droit nécessaire sur le projet ciblé : roles/agentregistry.viewer
    (API agentregistry.googleapis.com activée).
  - Aucune variable de configuration lue : projet et région sont des arguments.

Utilisation
  python scripts/registry.py PROJET [REGION] [RECHERCHE]

    python scripts/registry.py PROJET [REGION]          # agents, serveurs MCP, endpoints
    python scripts/registry.py PROJET REGION "stock"    # recherche sémantique
    python scripts/registry.py acme-agents-supply europe-west1
    python scripts/registry.py $PROJET_AGENTS $REGION

  PROJET     ID du projet dont on lit le registre (obligatoire)
  REGION     région du registre, défaut europe-west1
  RECHERCHE  texte libre : recherche sémantique parmi les agents (n'affiche alors que les agents)

Ce qu'il lit / ce qu'il crée
  LECTURE SEULE : lit le registre du projet, ne crée, ne modifie et ne supprime rien. Relançable à volonté.

Résultat attendu
  == 2 agent(s) dans PROJET/europe-west1
  - stock-agent: Donne le stock d'un article…
      ajout : adk  projects/123/locations/europe-west1/reasoningEngines/456
  - pricing-a2a: Prix et promotions…
      ajout : a2a  https://pricing-a2a-123.europe-west1.run.app/…/.well-known/agent-card.json
              [carte A2A dans le registre]
  == 0 serveur(s) MCP
  == 0 endpoint(s)
  Pour chaque agent, affiche comment l'ajouter avec add_agent_to_ge.sh (adk <ressource> ou a2a <URL>).

Erreurs fréquentes et que faire
  - IndexError : PROJET manquant.
  - 403 / PERMISSION_DENIED : pas de roles/agentregistry.viewer sur ce projet, ou API non activée.
  - « == 0 agent(s) » alors qu'il en existe : mauvaise région (le registre est régional) ou mauvais projet.
  - « a2a  (URL absente : demander la carte d'agent à l'équipe) » : l'entrée n'a pas d'adresse ; demander la
    carte A2A à l'équipe (docs/04, partie 7).
  - DefaultCredentialsError : gcloud auth application-default login.
"""
import sys

from google.adk.integrations.agent_registry import AgentRegistry

project = sys.argv[1]
region = sys.argv[2] if len(sys.argv) > 2 else "europe-west1"
query = sys.argv[3] if len(sys.argv) > 3 else ""
registry = AgentRegistry(project_id=project, location=region)


def how_to_add(a: dict) -> str:
    """Ce qu'il faut donner à add_agent_to_ge.sh pour cette entrée du registre."""
    # agentId est une URN à segments séparés par « : », par exemple
    #   urn:agent:projects-123:projects:123:locations:europe-west1:aiplatform:reasoningEngines:456
    # index("projects", 3) saute « projects-123 » (l'éditeur) pour trouver le vrai segment « projects ».
    parts = a.get("agentId", "").split(":")
    if "reasoningEngines" in parts:  # agent Agent Runtime : ajout par nom de ressource (le segment « aiplatform » est ignoré)
        i = parts.index("projects", 3)
        return (f"adk  projects/{parts[i + 1]}/locations/{parts[parts.index('locations', i) + 1]}"
                f"/reasoningEngines/{parts[parts.index('reasoningEngines') + 1]}")
    # Sinon (agent A2A) : la 1re URL trouvée, déclarée sous « protocols » ou directement sous « interfaces ».
    urls = [i.get("url") for p in [*a.get("protocols", []), {"interfaces": a.get("interfaces", [])}]
            for i in p.get("interfaces", []) if i.get("url")]
    card = "carte A2A dans le registre" if a.get("card", {}).get("type") == "A2A_AGENT_CARD" else "pas de carte A2A"
    if not urls:
        return f"a2a  (URL absente : demander la carte d'agent à l'équipe)  [{card}]"
    return f"a2a  {urls[0].rstrip('/')}/.well-known/agent-card.json  [{card}]"  # chemin standard de la carte A2A


agents = (registry.search_agents(search_string=query, search_type="SEMANTIC") if query else registry.list_agents()).get("agents", [])
print(f"\n== {len(agents)} agent(s) dans {project}/{region}")
for a in agents:
    print(f"- {a.get('displayName')}: {a.get('description', '')[:80]}\n    ajout : {how_to_add(a)}")

# Inventaire complet seulement sans recherche : la recherche sémantique ne porte que sur les agents.
if not query:
    servers = registry.list_mcp_servers().get("mcpServers", [])
    print(f"\n== {len(servers)} serveur(s) MCP")
    for s in servers:
        print(f"- {s.get('displayName')}: {s.get('name')}")
    endpoints = registry.list_endpoints().get("endpoints", [])
    print(f"\n== {len(endpoints)} endpoint(s)")
    for e in endpoints:
        print(f"- {e.get('displayName')}: {e.get('name')}")
