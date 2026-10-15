# 10-7. Chemin 4 : déclarer le serveur MCP dans Agent Registry

**Ce guide répond à :** à quoi sert Agent Registry pour un serveur MCP ? Comment y déclarer `sheets-mcp` et ses 17
outils, par script, Terraform ou console ? Comment un agent ADK le retrouve-t-il par son nom ?

> **Testé en vrai (14 octobre 2026) :** `./scripts/deployer.sh registre` a créé « Google Sheets (MCP) », et la liste
> du registre montre les 17 outils avec leurs annotations. Au 1er essai, Agent Registry a exigé le schéma des
> paramètres (`inputSchema`) de chaque outil : c'est corrigé dans `gen_toolspec.py`.

---

> **Deux entrées :** « Google Sheets (MCP) » (17 outils) et « Google Slides (MCP) » (20 outils), depuis `terraform/toolspec-sheets.json` et `toolspec-slides.json`. Les exemples ci-dessous parlent de Sheets ; Slides est identique.

## 1. À quoi ça sert

Agent Registry est le **catalogue** des agents et des serveurs MCP de l'organisation. Y déclarer `sheets-mcp`, c'est :
- **le rendre visible** : console → Agent Registry → onglet **MCP servers**, avec la description et les outils ;
- **gouverner** : savoir quels outils existent, lesquels sont en lecture seule ou destructifs ;
- **le retrouver par son nom** depuis un agent ADK, sans écrire son URL en dur : si l'URL change, on met le registre à
  jour, pas les agents.

Le registre ne remplace **ni** le connecteur (10-5) **ni** l'agent (10-6) : il les accompagne.

## 2. Pourquoi une liste d'outils (`toolspec.json`)

Une déclaration manuelle enregistre l'URL, mais Agent Registry n'interroge **pas** le serveur. Pour que les outils
soient visibles, il faut les fournir : c'est `terraform/toolspec.json`. Il est **généré depuis le code**, donc il ne
peut pas diverger :
```bash
python3 scripts/gen_toolspec.py
```
**Résultat obtenu :** `terraform/toolspec.json : 17 outils, 6917 octets (maximum Agent Registry : 10 Ko)`.

Format (extrait) :
```json
{"tools":[{"name":"read_range","description":"Lit les valeurs d'une plage (liste de lignes).",
  "inputSchema":{"properties":{"spreadsheet_id":{"type":"string"},"range_a1":{"type":"string"},"render":{"enum":[…],"type":"string"}},
                 "required":["spreadsheet_id","range_a1"],"type":"object"},
  "annotations":{"title":"Lire une plage","readOnlyHint":true}}, …]}
```
Le bouton **Import tools** de la console ne marche que pour un serveur **public**. Le nôtre est privé, d'où ce
fichier.

## 3. Déclarer

**Script :** `./scripts/deployer.sh registre`. Il lance :
```bash
gcloud agent-registry services create sheets-mcp --location=europe-west1 --project=$PROJET \
  --display-name="Google Sheets (MCP)" --description="Lecture et modification de Google Sheets au nom de l'utilisateur…" \
  --mcp-server-spec-type=tool-spec --mcp-server-spec-content="$(cat terraform/toolspec.json)" \
  --interfaces="url=$MCP_URL,protocolBinding=jsonrpc"
gcloud agent-registry mcp-servers list --location=europe-west1 --project=$PROJET
```
**Terraform :** `google_agent_registry_service.mcp` (`register_in_agent_registry = true`, par défaut).

**Console :** Agent Registry → `europe-west1` → **MCP servers** → **Add MCP server** :
- nom, description ;
- endpoint `…/mcp` ;
- collez `toolspec.json` ;
- **Next** → cochez les outils → **Save**.

**Région :** une région (`europe-west1`) ou `global`. La déclaration manuelle n'est **pas** possible en `eu` ni en
`us` (documentation Google).

**Droit :** `roles/agentregistry.editor` sur le projet. `./scripts/deployer.sh verifier` le contrôle.

**Déclaration automatique :** `gcloud run deploy … --functional-type=mcp-server` déclare un service Cloud Run tout
seul, dans le même projet. Nous déclarons à la main, pour publier la liste des outils d'un serveur privé et garder
une déclaration relisible.

## 4. Un agent ADK qui retrouve le serveur par son nom

Le projet 04 le fait (`04-mcp-server-cloud-run-registry/agent/shop_agent/agent.py`) :
```python
from google.adk.integrations.agent_registry import AgentRegistry
registry = AgentRegistry(project_id=PROJET, location="europe-west1", header_provider=entetes)
serveur = next(s for s in registry.list_mcp_servers().get("mcpServers", []) if s.get("displayName") == "Google Sheets (MCP)")
outils = registry.get_mcp_toolset(serveur["name"])
```
Notre agent (10-6) garde une URL fixe (`MCP_URL`) : c'est plus simple, et il n'a pas de dépendance au registre au
démarrage. Passez au registre quand plusieurs agents partagent le serveur.

## 4 bis. La découverte par Agent Gateway (vue dans la console Acme)

La console Gemini Enterprise de Acme montre, dans la section **« MCP servers »** de l'app :
- « *MCP servers from your project's configured Agent Gateway registries, or a custom …* » ;
- le bandeau « *Configure Agent Gateway to discover and use MCP servers from your …* ».

Autrement dit, quand une **Agent Gateway** est configurée pour l'app et reliée à des registres, les serveurs MCP
**déclarés dans Agent Registry** (comme `sheets-mcp`, partie 3) apparaissent directement dans cette liste. Il n'y a
alors plus besoin de les saisir à la main.

Ce qui reste pareil :
- le serveur est privé : le compte de l'app doit avoir `run.invoker` (10-5, étape 3) ;
- le jeton de l'utilisateur doit venir d'un client OAuth accepté par le serveur.

**Statut :** vu dans la console, **pas encore testé** (il faut une app et une Agent Gateway). Le chemin manuel
« Custom MCP Server » (10-5) marche sans gateway. Référence : [Route Gemini Enterprise traffic through Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-ge-deploy).

## 5. Si ça bloque

| Symptôme | Cause → solution |
|---|---|
| `PERMISSION_DENIED` à la création | `roles/agentregistry.editor` manquant, ou l'API `agentregistry.googleapis.com` bloquée par l'organisation (l'étape est facultative) |
| `INVALID_ARGUMENT` sur la location | `eu` ou `us` : prendre `europe-west1` (`REGISTRE_LOCATION`) |
| `invalid MCP tool spec content: tools.0: inputSchema is required` | Ancien `gen_toolspec.py` : prendre la version actuelle (schémas inclus) |
| Aucun outil affiché | `toolspec.json` absent ou vide : `python3 scripts/gen_toolspec.py`, puis supprimer et redéclarer |
| Taille refusée | Plus de 10 Ko : raccourcir les descriptions (le script s'arrête de lui-même au-delà) |

**Source :** [Register MCP servers](https://docs.cloud.google.com/agent-registry/register-mcp-servers).
