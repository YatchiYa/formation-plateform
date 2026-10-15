# 06. Un agent qui appelle un autre agent (créé sur Vertex AI / Agent Runtime)

**Pour qui :** développeurs d'agents, architectes.

---

## 1. Trois modèles

| | A. Appel par l'API Agent Runtime (outil) | B. A2A via Agent Registry (`RemoteA2aAgent`) | C. Sous-agent dans le même code |
|---|---|---|---|
| **Principe** | L'orchestrateur a un outil qui interroge l'agent distant (`runtimes.get(...).async_stream_query`) | L'orchestrateur charge l'agent distant comme **sous-agent** à partir de sa carte A2A trouvée dans le registre | Les deux agents sont dans le même déploiement |
| **L'agent appelé doit…** | être un agent Agent Runtime (n'importe quel `AdkApp`) | **parler A2A** (Agent Runtime A2A, ou Cloud Run `to_a2a`) | être dans le même dépôt |
| **Cross-project** | Oui | Oui | Non |
| **Droits** | `roles/aiplatform.viewer` **sur l'agent appelé** | Selon l'hébergement (`run.invoker`, ou fournisseur d'authentification lié dans le registre) | Aucun |
| **Qui garde la main** | L'orchestrateur (l'agent distant est un outil) | L'agent distant prend la conversation pendant sa tâche | — |
| **Quand l'utiliser** | **Par défaut** entre équipes : simple, marche avec tout agent Agent Runtime existant | Agents d'éditeurs différents, autres frameworks, interopérabilité | Même équipe, même cycle de vie |

**Ce projet implémente A** (avec découverte par le registre), car c'est celui qui fonctionne avec les agents ADK déjà
déployés par les équipes, sans leur demander de changer de protocole.

---

## 2. Modèle A, le code (`agents/orchestrator/orchestrator_agent/agent.py`)

### 2.1 Trouver l'agent dans le registre de l'autre équipe

```python
@functools.cache                          # une seule recherche par démarrage
def stock_agent_name() -> str:
    if os.getenv("STOCK_AGENT"):          # repli : nom passé en dur par Terraform
        return os.environ["STOCK_AGENT"]
    agents = AgentRegistry(project_id=AGENTS_PROJECT, location=REGISTRY_LOCATION).list_agents().get("agents", [])
    match = next((a for a in agents if a.get("displayName") == "stock-agent"), None)
    return urn_to_resource(match["agentId"])
```

Un agent Agent Runtime s'enregistre **automatiquement** dans le registre de son projet. Son identifiant est un **URN** :

```
urn:agent:projects-123:projects:123:locations:europe-west1:reasoningEngines:456
                                  ↓ urn_to_resource()
projects/123/locations/europe-west1/reasoningEngines/456
```

**Pourquoi passer par le registre :** l'équipe Supply peut redéployer ou recréer son agent (nouvel ID) sans que l'équipe
Magasins change une ligne. Et un agent absent du registre n'est pas utilisable : la gouvernance est appliquée par construction.

### 2.2 L'appeler

```python
async def ask_stock_agent(question: str, tool_context: ToolContext) -> dict:
    name = stock_agent_name()
    _, project, _, location, *_ = name.split("/")
    remote = agentplatform.Client(project=project, location=location).runtimes.get(name=name)
    session = await remote.async_create_session(user_id=tool_context.user_id)
    async for event in remote.async_stream_query(user_id=tool_context.user_id, session_id=session["id"], message=question):
        ...                                   # on garde le texte des réponses
    return {"status": "success", "answer": ...}
```

- L'appel part avec **l'identité de l'orchestrateur** (son compte de service sur Agent Runtime).
- L'**utilisateur final** est transmis (`user_id`) : l'agent appelé le voit dans ses journaux (traçabilité), mais il
  **n'agit pas avec ses droits**. Si l'agent appelé doit accéder à des données **au nom de l'utilisateur**, il faut OAuth
  (ressource d'autorisation Gemini Enterprise), pas ce modèle.
- Erreur (droit manquant, agent supprimé) → l'outil renvoie `status: error`, l'orchestrateur l'explique au lieu de planter.

### 2.3 Les droits (`terraform/20_orchestrator.tf`)

```hcl
# Posé SUR l'agent stock, dans le projet agents : appeler CET agent, et seulement lui.
resource "google_vertex_ai_reasoning_engine_iam_member" "orchestrator_calls_stock" {
  provider         = google.agents
  reasoning_engine = module.stock_agent.name
  role             = "roles/aiplatform.viewer"     # contient reasoningEngines.get + .query
  member           = module.orchestrator.service_account
}

# Lire le registre du projet agents (pour la découverte).
resource "google_project_iam_member" "orchestrator_reads_registry" {
  provider = google.agents
  role     = "roles/agentregistry.viewer"
  member   = module.orchestrator.service_account
}
```

**Pourquoi un droit sur l'agent et pas sur le projet :** `aiplatform.user` sur le projet permettrait d'appeler (et de
modifier, supprimer, créer) **tous** les agents de l'équipe Supply. Ici, l'orchestrateur ne peut **qu'interroger** `stock-agent`.

### 2.4 Le prouver

```bash
python scripts/test_agents.py                          # hors ligne : découverte, URN, appel, échec propre
python scripts/query.py orchestrator "Il reste des tentes 8771234 à Lyon ?"
#   -> outil : ask_stock_agent(...)
# Preuve négative : retirer le droit sur l'agent (en recette) -> l'orchestrateur répond « Agent stock indisponible : 403 »
```

---

## 3. Modèle B, A2A par le registre (variante)

Si l'agent appelé parle A2A et que sa carte est dans le registre, ADK le transforme en sous-agent en une ligne :

```python
from google.adk.integrations.agent_registry import AgentRegistry

registry = AgentRegistry(project_id="acme-agents-supply", location="europe-west1")
stock = registry.get_remote_a2a_agent("projects/…/locations/europe-west1/agents/stock-agent")   # -> RemoteA2aAgent
root_agent = Agent(name="assistant_magasin", ..., sub_agents=[stock])
```

- L'**authentification** est résolue depuis les **liaisons** (*bindings*) du registre, qui associent un agent source, une
  cible, et un fournisseur d'authentification (`google_agent_registry_binding` en Terraform).
- Rendre un agent ADK compatible A2A : sur Cloud Run, `google.adk.a2a.utils.agent_to_a2a.to_a2a(root_agent)` ; sur Agent
  Runtime, le modèle `agentplatform.frameworks.a2a.A2aAgent`.
- À choisir quand les agents viennent d'éditeurs ou de frameworks différents.

---

## 4. Bonnes pratiques entre agents

| Pratique | Pourquoi |
|---|---|
| **Une identité par agent**, droits **sur l'agent appelé** uniquement | Un orchestrateur compromis ne compromet pas tout le projet d'en face |
| Model Armor **dans chaque agent** | La réponse d'un agent est une entrée pour l'autre : une injection peut se propager |
| L'agent appelé reste **spécialisé** et **en lecture** | Les actions qui modifient restent avec confirmation humaine (`require_confirmation`) |
| **Descriptions précises** | Le modèle choisit l'outil ou l'agent sur la description |
| Délai et erreurs gérés dans l'outil | Un agent lent ou absent ne doit pas bloquer la conversation |
| Sortie par **Agent Gateway** quand elle est en place | Les appels inter-agents sont journalisés et soumis aux politiques |
| **Éviter les cycles** (A appelle B qui appelle A) | Coûts et boucles infinies |
