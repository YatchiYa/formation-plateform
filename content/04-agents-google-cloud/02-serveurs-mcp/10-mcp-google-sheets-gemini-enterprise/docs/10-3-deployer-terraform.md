# 10-3. Tout déployer avec Terraform

**Ce guide répond à :** comment créer le serveur MCP, l'agent (A2A et/ou Agent Runtime), leurs droits et l'entrée
Agent Registry avec Terraform ? Que montre le plan ? Comment ajouter Agent Runtime ou l'app plus tard ?

Même résultat que le script ([10-2](10-2-deployer-shell.md)). Choisissez **l'un ou l'autre** pour un même projet :
les noms de ressources sont les mêmes.

> **Testé en vrai (14 octobre 2026)** sur un projet neuf (`second-project`), avec l'app (`main-project`) et Agent
> Runtime :
> - `terraform apply` → `Apply complete!` ;
> - `./scripts/deployer.sh tester` : 403 sans jeton, 17 outils sur le vrai classeur, agent A2A et agent Agent
>   Runtime qui répondent avec le vrai Gemini ;
> - relancé, `terraform plan` → `No changes. Your infrastructure matches the configuration.`
>
> **Deux corrections trouvées pendant ce test réel**, faites dans le code :
> - le numéro du projet est maintenant **donné** (`NUM_PROJET`), et non plus lu ;
> - une commande à lancer avant Terraform (partie 2.1 bis).

---

## 1. Ce que Terraform crée

| # | Ressource | Rôle |
|---|---|---|
| 1 | `google_project_service.apis[…]` | Les API (Cloud Run, Cloud Build, Artifact Registry, IAM, Logging, Sheets, Drive, Vertex AI, Agent Registry) |
| 2 | `google_service_account.build` + 3 rôles | Le compte qui construit les images |
| 2 | `google_service_account.mcp` | Le compte du serveur MCP : **aucun rôle** |
| 2 | `google_service_account.agent` + 2 rôles | Le compte de l'agent (Gemini, journaux) |
| 3 | `google_artifact_registry_repository.images` | Le dépôt d'images `sheets-mcp` |
| 3 | `terraform_data.image["mcp_server"]`, `["agent"]` | Les images, construites par **Cloud Build** (`gcloud builds submit`), étiquetées par l'empreinte du code |
| 4 | `google_cloud_run_v2_service.mcp` | Le serveur MCP, **privé** |
| 5 | `google_cloud_run_v2_service.agent[0]` | L'agent A2A (`deploy_agent_cloudrun = true`, par défaut) |
| 6 | `google_vertex_ai_reasoning_engine.agent[0]` | L'agent sur Agent Runtime (`deploy_agent_runtime = true`) |
| 7 | `google_cloud_run_v2_service_iam_member.mcp[…]` | Qui peut appeler le serveur MCP : le compte de l'agent, et le compte de l'app (si `ge_project_number`) |
| 7 | `google_cloud_run_v2_service_iam_member.agent[0]` | L'app peut appeler l'agent A2A |
| 7 | `google_project_iam_member.ge_runtime[0]` | L'app peut appeler l'agent Agent Runtime |
| 8 | `google_agent_registry_service.mcp[0]` | Le serveur et ses 17 outils dans Agent Registry |

**L'étiquette d'image est l'empreinte du code.** Code inchangé : même image, rien à refaire. Si `agent/` change,
seule l'image de l'agent est reconstruite, et le serveur MCP ne bouge pas.

## 2. Pas à pas

### 2.1 La configuration

`config/10-mcp.env`, avec `OAUTH_CLIENT_IDS` rempli (client OAuth : [10-5, étape 1](10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-1--le-client-oauth-console-projet-des-agents)).
Terraform lit les variables `TF_VAR_*` calculées par `config.sh` : il n'y a pas de `terraform.tfvars` à écrire.
```bash
source scripts/config.sh config/10-mcp.env
python3 scripts/gen_toolspec.py         # terraform/toolspec.json (liste des outils pour Agent Registry)
```

### 2.1 bis Une commande, une seule fois, avant Terraform

```bash
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com --project=$PROJET
```
Terraform gère les API et les rôles du projet **à travers** ces deux API. Sur un projet neuf où elles sont
inactives, il ne peut même pas les activer lui-même.

**Constaté en vrai le 14 octobre 2026**, sur un projet neuf, sans cette commande :
`Error 403: Cloud Resource Manager API has not been used in project … or it is disabled` sur chaque API et chaque
rôle. `./scripts/deployer.sh preparer` l'active aussi. Sur les projets Acme, elle est très probablement déjà
active : la commande ne change alors rien.

### 2.2 Le plan

```bash
cd terraform
terraform init
terraform plan
```
**Résultat obtenu** (projet de test, sans app, sans Agent Runtime) : `Plan: 24 to add, 0 to change, 0 to destroy.` Avec la version actuelle, qui active aussi Cloud Resource Manager, comptez **une ressource de plus** dans chaque cas (25, 27, 29).

**Résultat obtenu** avec l'app (`NUM_APP` rempli) et Agent Runtime (`TF_VAR_deploy_agent_runtime=true`) :
```
  # google_agent_registry_service.mcp[0] will be created
  # google_artifact_registry_repository.images will be created
  # google_cloud_run_v2_service.agent[0] will be created
  # google_cloud_run_v2_service.mcp will be created
  # google_cloud_run_v2_service_iam_member.agent[0] will be created
  # google_cloud_run_v2_service_iam_member.mcp["serviceAccount:service-<NUM_APP>@gcp-sa-discoveryengine.iam.gserviceaccount.com"] will be created
  # google_cloud_run_v2_service_iam_member.mcp["serviceAccount:sheets-agent-sa@<PROJET>.iam.gserviceaccount.com"] will be created
  # google_project_iam_member.agent["roles/aiplatform.user"] will be created
  # google_project_iam_member.agent["roles/logging.logWriter"] will be created
  # google_project_iam_member.build["roles/artifactregistry.writer"] will be created
  # google_project_iam_member.build["roles/logging.logWriter"] will be created
  # google_project_iam_member.build["roles/storage.objectViewer"] will be created
  # google_project_iam_member.ge_runtime[0] will be created
  # google_project_service.apis["agentregistry.googleapis.com"] will be created
  # … (8 autres API)
  # google_service_account.agent will be created
  # google_service_account.build will be created
  # google_service_account.mcp will be created
  # google_vertex_ai_reasoning_engine.agent[0] will be created
  # terraform_data.image["agent"] will be created
  # terraform_data.image["mcp_server"] will be created
Plan: 28 to add, 0 to change, 0 to destroy.
```

| Options | Plan obtenu |
|---|---|
| Sans app, sans Agent Runtime | 24 to add |
| Avec app (`NUM_APP`) | 26 to add (+2 droits pour l'app) |
| Avec app et Agent Runtime | 28 to add (+ l'agent et le droit ②) |
| `OAUTH_CLIENT_IDS` vide | `Error: Resource precondition failed` … `oauth_client_ids est vide : le serveur MCP refuserait de démarrer` |

### 2.3 Appliquer

```bash
terraform apply        # relit le plan, demande « yes » ; 6 à 10 min (15 à 20 avec Agent Runtime)
```
**Attendu :**
- des lignes `terraform_data.image["mcp_server"] (local-exec): … SUCCESS` ;
- `Apply complete! Resources: 24 added` ;
- puis les sorties :

**Résultat obtenu** (sorties, projet de test) :
```
agent_runtime = "projects/second-project-511608/locations/europe-west1/reasoningEngines/2125248224351485952"
agent_url = "https://sheets-agent-872505552973.europe-west1.run.app"
autorisations_attendues = { "a2a" = "acces-sheets", "agent_runtime" = "acces-sheets-runtime" }
carte_a2a = "{\"protocolVersion\": \"0.3\", \"name\": \"sheets_agent\", …}"
domaines_de_sortie_a_autoriser = ["sheets-mcp-872505552973.europe-west1.run.app", "accounts.google.com", "oauth2.googleapis.com"]
ge_service_agent = "service-100000000005@gcp-sa-discoveryengine.iam.gserviceaccount.com"
mcp_url = "https://sheets-mcp-872505552973.europe-west1.run.app/mcp"
```

| Sortie | Pour |
|---|---|
| `mcp_url` | Le connecteur « Custom MCP Server » (10-5) |
| `carte_a2a` | La carte à coller (Custom agent via A2A), sur une ligne : vient de `agent/carte.py` |
| `agent_runtime` | Le chemin à coller (Custom agent via Agent Runtime) |
| `autorisations_attendues` | Les ID d'autorisation que l'agent attend : `acces-sheets` (A2A) et `acces-sheets-runtime` |
| `ge_service_agent` | Le compte de l'app qui a reçu les droits |
| `domaines_de_sortie_a_autoriser` | Pour la politique d'organisation du connecteur natif (10-5, étape 2) |

```bash
terraform output -raw carte_a2a      # la carte, prête à copier
```

### 2.4 Plus tard : ajouter Agent Runtime, ou l'app

| Vous voulez | Vous faites | Le plan doit montrer |
|---|---|---|
| Ajouter l'agent Agent Runtime | `export TF_VAR_deploy_agent_runtime=true`, `plan` | `+ google_vertex_ai_reasoning_engine.agent[0]` (+ `ge_runtime[0]` si l'app est connue). **Rien d'autre** |
| Donner les droits à l'app | `NUM_APP` dans le fichier, recharger, `plan` | 2 ou 3 droits `…iam_member…` en plus, 0 à détruire |
| Accepter un autre client OAuth | `OAUTH_CLIENT_IDS="a,b"`, recharger, `plan` | `google_cloud_run_v2_service.mcp will be updated in-place` (nouvelle révision, même adresse) |
| Nouveau code du serveur | Modifier `mcp_server/main.py`, `plan` | `terraform_data.image["mcp_server"] must be replaced` + `…service.mcp will be updated in-place` |
| Seulement Sheets (sans Slides) | `export TF_VAR_produits_mcp='["sheets"]'` | Pas de `…mcp["slides"]` |
| Ajouter Slides à un déploiement Sheets existant | `produits_mcp` par défaut (`["sheets","slides"]`), `plan` | `…mcp[0] has moved to …mcp["sheets"]`, puis seulement des créations `["slides"]` : **rien n'est détruit** (testé, [10-13](10-13-serveur-mcp-google-slides.md#4-déployer)) |
| Pas d'Agent Registry (bloqué par l'organisation) | `export TF_VAR_register_in_agent_registry=false` | L'entrée du registre n'est pas créée |

**Lisez toujours la ligne `Plan:` avant de taper `yes`.** Si un `destroy` apparaît sans raison, répondez `no`.

## 3. Côté app, après `apply`

Terraform ne crée **pas** le connecteur natif : Google ne publie pas d'API pour cela. Il ne crée pas non plus
l'autorisation OAuth, parce que le secret ne doit pas entrer dans l'état Terraform. Faites ensuite :
- connecteur : [10-5](10-5-gemini-enterprise-connecteur-mcp-natif.md) ;
- agent : [10-6](10-6-agent-adk-mcp-gemini-enterprise.md). Ou par script :
  `./scripts/deployer.sh autorisation …` puis `ajouter-app`.

## 4. Supprimer

```bash
terraform destroy       # relit la liste, demande « yes »
```
L'agent Agent Runtime est supprimé avec ses sessions (`deletion_policy = "FORCE"`). Les API restent actives
(`disable_on_destroy = false`), pour ne pas casser d'autres usages du projet.
