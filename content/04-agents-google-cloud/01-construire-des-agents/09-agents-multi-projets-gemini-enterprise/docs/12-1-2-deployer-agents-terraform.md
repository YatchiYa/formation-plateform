# 12-1-2. Déployer les agents dans le projet des agents : méthode **Terraform**

**Le but :** mettre en ligne **un**, **deux** ou **tous** les agents dans le projet des agents
`aiml-gemini-ent-exp-0zga`, avec Terraform. Vous choisissez les agents dans **une ligne** du fichier de
configuration ; Terraform crée tout le reste (API, identités, droits, filtres, images, services, catalogue).

**Pas encore d'app Gemini Enterprise.** On ne fait **que** les agents ; les relier à l'app viendra plus tard
([partie 12](#12-et-après--quand-lapp-existera)).

**Les autres méthodes, même résultat :** [12-1-1 Shell](12-1-1-deployer-agents-shell.md) ·
[12-1-3 Console](12-1-3-deployer-agents-console.md).

> **Agents dans le projet de l'app (cas 12-2) ?** Identique : mettez le projet de l'app dans `PROJET_AGENTS` et
> `NUM_AGENTS`, et utilisez `config/12-2-agents-dans-projet-app.env`.

> **Testé en vrai** (10 octobre 2026, projets de test), pour **Cloud Run** (01-bis) et **Agent Runtime** (02-bis) :
> - `AGENTS="meteo"` : plan, apply, test ;
> - puis `AGENTS="meteo taille"` : seul `taille` est créé ;
> - relance sans changement : rien ne bouge ;
> - retrait de `taille` (plan) ;
> - `destroy`.
> - le 11 octobre, avec les images construites par **Cloud Build** (sans Docker) : `22 to add`, test, `7 to add`
>   pour un 2e agent, `destroy`.
>
> Dans les résultats, le projet de test est remplacé par le vôtre.

---

## Sommaire

0. [Terraform en 2 minutes](#0-terraform-en-2-minutes)
1. [Ce que Terraform crée, et où le voir](#1-ce-que-terraform-crée-et-où-le-voir)
2. [`for_each` : comment UNE ligne de configuration donne N agents](#2-for_each--comment-une-ligne-de-configuration-donne-n-agents)
3. [Préparer votre poste et le fichier de configuration](#3-préparer-votre-poste-et-le-fichier-de-configuration)
4. [Se connecter, vérifier droits et API](#4-se-connecter-vérifier-droits-et-api)
5. [Cloud Run (A2A), dossier 01-bis](#5-cloud-run-a2a-dossier-01-bis)
6. [Agent Runtime, dossier 02-bis](#6-agent-runtime-dossier-02-bis)
7. [Agent Registry : rien à faire](#7-agent-registry--rien-à-faire)
8. [Dialogflow, dossier 04-bis (option)](#8-dialogflow-dossier-04-bis-option)
9. [Ajouter, retirer, modifier un agent](#9-ajouter-retirer-modifier-un-agent)
10. [Tout supprimer](#10-tout-supprimer)
11. [Ce qui peut arriver](#11-ce-qui-peut-arriver)
12. [Et après : quand l'app existera](#12-et-après--quand-lapp-existera)

---

## 0. Terraform en 2 minutes

Terraform lit des fichiers `.tf` qui **décrivent** ce qui doit exister (« un compte de service `meteo-a2a-sa` », « un
service Cloud Run `meteo-a2a` »…), compare avec ce qui existe, et fait **seulement la différence**.

| Mot | En clair |
|---|---|
| **Ressource** | Une chose dans Google Cloud (un compte, un rôle, un service, un agent…) |
| `terraform init` | Prépare le dossier (télécharge le « provider » Google). Une fois par dossier, et par poste |
| `terraform plan` | **Montre** ce qui va être créé, modifié, supprimé. **Ne fait rien.** Toujours le lire |
| `terraform apply` | **Fait** ce que montre le plan, après votre `yes` |
| `terraform destroy` | Supprime tout ce que ce dossier a créé |
| **État** (`terraform.tfstate`) | La mémoire de Terraform : ce qu'il a créé. Ici dans `terraform.tfstate.d/scenario-12-1/`. **Ne pas supprimer** |
| **Espace de travail** (*workspace*) | Un état séparé par scénario : `scenario-12-1`, `scenario-12-2`. Choisi par le fichier de configuration |
| **Variable** | Une valeur d'entrée (`agents_project_id`, `agents`…). Ici, elles viennent du fichier de configuration |
| **Sortie** (*output*) | Une valeur affichée à la fin (`urls`, `agents`…) ; relire avec `terraform output` |

Terraform s'exécute **sur votre poste**, avec **votre** compte Google.

---

## 1. Ce que Terraform crée, et où le voir

**Trois dossiers, indépendants** : faites-en un, deux ou trois.

| Dossier | Hébergement | Créé **une fois** | Créé **par agent** | Ressources (résultats obtenus) |
|---|---|---|---|---|
| `01-bis-cloud-run-a2a/terraform` | **Cloud Run**, protocole **A2A** | 8 API, dépôt d'images `agents-a2a`, 2 filtres Model Armor `trio-a2a-*`, compte de construction `agents-a2a-build-sa` + 3 rôles | 1 image (construite par Cloud Build), 1 compte `<clé>-a2a-sa`, 3 rôles, 1 service `<clé>-a2a`, 1 entrée Agent Registry | **22** pour 1 agent, **+7** par agent en plus |
| `02-bis-agent-runtime/terraform` | **Agent Runtime** | 4 API, 2 filtres Model Armor `trio-runtime-*` | 1 compte `<clé>-agent-sa`, 5 rôles, 1 agent `<clé>-agent` (inscrit seul dans Agent Registry) | **13** pour 1 agent, **+7** par agent en plus |
| `04-bis-dialogflow/terraform` | **Dialogflow** | 1 API, 1 agent « Accueil magasin » | — | **2** |

Tous les agents (6) : **57** ressources pour Cloud Run, **48** pour Agent Runtime. (Avec une app renseignée : +1 par
agent pour Cloud Run, le droit de l'app sur chaque service ; +1 en tout pour Agent Runtime.)

**Pas besoin de Docker :** Terraform fait construire chaque image **dans Google Cloud** (Cloud Build), avec son propre
compte de construction. Votre poste envoie seulement le code des agents (quelques dizaines de Ko, filtrés par le fichier
`.gcloudignore` du projet).

**Où le voir dans la console** (projet `aiml-gemini-ent-exp-0zga` en haut, puis 🔎) :

| Quoi | 🔎 Rechercher | Puis |
|---|---|---|
| Les API | « API et services » | **API et services activés** |
| Les comptes `-a2a-sa`, `-agent-sa` | « Comptes de service » | Un clic → **Autorisations** |
| Les filtres | « Model Armor » | **Templates**, région `eu` : `trio-a2a-prompt-shield`… |
| Les images | « Artifact Registry » | Dépôt `agents-a2a` → une image par agent |
| Les agents Cloud Run | « Cloud Run » | **Services** → `meteo-a2a` → URL, **Révisions**, **Journaux**, **Sécurité** |
| Les agents Agent Runtime | « Agent Runtime » | **Déploiements** → `meteo-agent` → **Playground**, **Sessions** |
| Le catalogue | « Agent Registry » | Région `europe-west1` |
| Dialogflow | « Conversational Agents » | « Accueil magasin » → **Tester l'agent** |

---

## 2. `for_each` : comment UNE ligne de configuration donne N agents

C'est le cœur du système. Comprendre ces 3 étapes, c'est savoir **exactement** ce que Terraform va faire.

### Étape 1 : le catalogue, et votre choix

Le **catalogue** `agents/trio/catalogue.json` décrit tous les agents disponibles, chacun sous sa **clé** :

```json
{
  "meteo":  { "dossier": "meteo_agent",  "nom_affiche": "Météo & équipement", "description": "…", "competences": [ … ] },
  "taille": { "dossier": "taille_agent", "nom_affiche": "Conseil taille",     "description": "…", "competences": [ … ] },
  …
}
```

**Votre choix** est la ligne `AGENTS` du fichier de configuration. `scripts/config.sh` la transforme en variable
Terraform :

| Dans le fichier | Variable Terraform `agents` |
|---|---|
| `AGENTS="meteo"` | `["meteo"]` |
| `AGENTS="meteo taille"` | `["meteo", "taille"]` |
| `AGENTS=""` | `[]` = **tout le catalogue** |

### Étape 2 : la carte des agents à déployer

Dans `main.tf` (01-bis et 02-bis) :

```hcl
locals {
  catalogue = jsondecode(file("${local.trio_dir}/catalogue.json"))
  agents    = length(var.agents) == 0 ? local.catalogue : { for k in var.agents : k => local.catalogue[k] }
}
```

En français : « si la liste est vide, prendre tout le catalogue ; sinon, ne garder que les clés de la liste ». Avec
`AGENTS="meteo taille"`, `local.agents` vaut :

```
{
  "meteo"  = { dossier = "meteo_agent",  nom_affiche = "Météo & équipement", … }
  "taille" = { dossier = "taille_agent", nom_affiche = "Conseil taille",     … }
}
```

### Étape 3 : chaque ressource « par agent » est répétée avec `for_each`

```hcl
resource "google_service_account" "agent" {
  for_each   = local.agents                     # ← une copie de cette ressource PAR clé de la carte
  account_id = "${each.key}-a2a-sa"             # each.key   = "meteo", puis "taille"
  display_name = "Identité d'exécution de ${each.value.nom_affiche} (Cloud Run, A2A)"   # each.value = sa fiche du catalogue
}

resource "google_cloud_run_v2_service" "agent" {
  for_each        = local.agents
  name            = "${each.key}-a2a"            # meteo-a2a, taille-a2a
  …
  template { service_account = google_service_account.agent[each.key].email }   # le compte DE CET agent
}
```

| Écriture | Valeur pour l'agent `meteo` |
|---|---|
| `for_each = local.agents` | « répéter pour chaque agent choisi » |
| `each.key` | `"meteo"` |
| `each.value.nom_affiche` | `"Météo & équipement"` |
| `google_service_account.agent["meteo"]` | Le compte de `meteo` (c'est ainsi que le plan l'affiche) |

Résultat : chaque ressource a une **adresse** qui contient la clé de l'agent, par exemple
`google_cloud_run_v2_service.agent["meteo"]`. Terraform range ces adresses dans son état.

### Ce que cela garantit

| Vous faites | Terraform compare l'ancienne et la nouvelle carte | Résultat (testé) |
|---|---|---|
| Ajouter `taille` à `AGENTS` | Nouvelle clé `["taille"]` | Crée **seulement** les ressources `["taille"]` : `Plan: 7 to add, 0 to change, 0 to destroy` |
| Relancer sans rien changer | Mêmes clés, mêmes valeurs | `No changes.` |
| Retirer `taille` de `AGENTS` | Clé disparue | **Supprime** les ressources `["taille"]` : `Plan: 0 to add, 0 to change, 7 to destroy` — `(because key ["taille"] is not in for_each map)` |
| Modifier le code de `meteo` | Même clé, image (ou archive) différente | Met à jour **`["meteo"]` seulement**, sur place (même adresse, même ID) |
| Deux fois la même clé | — | Refusé : `Une clé apparaît deux fois dans agents.` |
| Une clé inconnue | — | Refusé au chargement de la configuration : `ATTENTION : agent « … » absent de agents/trio/catalogue.json` |

> ⚠ **`AGENTS` décrit ce qui doit exister, pas ce qu'il faut ajouter.** Pour ajouter `retour` à `meteo` et `taille`,
> écrivez `AGENTS="meteo taille retour"`, **pas** `AGENTS="retour"` (qui supprimerait `meteo` et `taille`). Le plan vous
> le montrerait (`destroy`) : **lisez toujours la ligne `Plan:` avant `yes`**.

**Pourquoi une image (ou une archive) par agent ?** L'image de `meteo` ne contient que le code commun et
`meteo_agent/`. Son étiquette est l'**empreinte** de ce contenu. Ajouter ou modifier `taille` ne change pas l'empreinte
de `meteo` : Terraform ne voit rien à refaire pour `meteo`.

---

## 3. Préparer votre poste et le fichier de configuration

**Outils** (une fois) :

| Outil | Mac (Homebrew) | Vérifier |
|---|---|---|
| gcloud | `brew install --cask google-cloud-sdk` | `gcloud version` |
| Terraform 1.9+ | `brew tap hashicorp/tap && brew install hashicorp/tap/terraform` | `terraform version` |
| uv (Python 3.12 à 3.14) | `brew install uv` | `uv --version` |

**Le dossier et son Python** (une fois) :

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/trio/requirements.txt
python scripts/test_trio.py                         # tests trio OK (9 scénarios, 6 agents)
```

**Le fichier de configuration** `config/12-1-agents-dans-projet-exp.env` : remplissez-le comme en
[12-1-1, partie 3](12-1-1-deployer-agents-shell.md#3-le-fichier-de-configuration--quoi-écrire-ligne-par-ligne) (le
tableau ligne par ligne y est). L'essentiel :

```bash
PROJET_APP=                 # pas encore d'app : VIDE
NUM_APP=                    # VIDE
APP_ID=                     # VIDE
GE_LOCATION=eu
PROJET_AGENTS=aiml-gemini-ent-exp-0zga
NUM_AGENTS=433175138344
REGION=europe-west1
AGENTS="meteo"              # un agent ; "meteo taille" : deux ; "" : tous
PUBLIER=non
```

**Charger** (dans chaque nouveau terminal, et après chaque modification du fichier) :

```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
```

**Résultat obtenu :**

```
== Configuration chargée : config/12-1-agents-dans-projet-exp.env
   App Gemini Enterprise : (pas encore : agents seuls)   (projet -, numéro -, eu)
   Projet des agents     : aiml-gemini-ent-exp-0zga (numéro 433175138344), région europe-west1   [même projet que l'app : non]
   Agents à déployer     : meteo
   Compte de l'app       : (aucun : pas encore d'app, aucun droit donné)
   Terraform             : espace « scenario-12-1 », publication dans l'app : non
   Dossier               : /Users/<vous>/Desktop/09-agents-multi-projets-gemini-enterprise
   OK
```

**Ce que le script donne à Terraform**, sous forme de variables d'environnement `TF_VAR_…` (Terraform les lit seul :
pas de fichier `terraform.tfvars` à écrire) :

| Variable Terraform | Vient de | Ici |
|---|---|---|
| `agents_project_id` | `PROJET_AGENTS` | `aiml-gemini-ent-exp-0zga` |
| `region` | `REGION` | `europe-west1` |
| `ge_location` | `GE_LOCATION` | `eu` (région des filtres Model Armor) |
| `agents` | `AGENTS` | `["meteo"]` |
| `ge_project_number`, `ge_project_id`, `ge_app_id` | `NUM_APP`, `PROJET_APP`, `APP_ID` (si `PUBLIER=oui`) | vides : **aucun droit** pour une app, **aucune publication** |
| *espace de travail* | le nom du fichier | `scenario-12-1` (variable `TF_WORKSPACE`) |

Vérifier : `echo $TF_VAR_agents` → `["meteo",]` (la virgule finale est normale).

---

## 4. Se connecter, vérifier droits et API

```bash
gcloud auth login
gcloud auth application-default login         # Terraform utilise CETTE connexion
gcloud projects describe $PROJET_AGENTS --format='value(projectNumber)'      # 433175138344
```

**Vos droits :** `roles/owner` sur le projet des agents, ou les rôles listés en
[12-1-1, partie 4](12-1-1-deployer-agents-shell.md#4-se-connecter-vérifier-le-projet-et-vos-droits).

**Les API :** Terraform **active lui-même** celles dont il a besoin (lignes `google_project_service…` du plan). Il en
faut **deux avant** lui, pour qu'il puisse lire le projet et activer les autres :

```bash
./scripts/verifier_api.sh $PROJET_AGENTS cloudresourcemanager.googleapis.com serviceusage.googleapis.com
```

**Résultat obtenu :** `OK cloudresourcemanager.googleapis.com`, `OK serviceusage.googleapis.com`, `rien à activer`.

| API activée par Terraform | 01-bis | 02-bis | 04-bis |
|---|---|---|---|
| `iam`, `aiplatform`, `modelarmor`, `agentregistry` | ✔ | ✔ | |
| `run`, `artifactregistry`, `logging`, `cloudbuild` | ✔ | | |
| `dialogflow` | | | ✔ |

Une API déjà active n'est pas touchée, et `destroy` ne la **désactive pas** (d'autres choses peuvent s'en servir).

---

## 5. Cloud Run (A2A), dossier 01-bis

Rien à lancer sur votre poste : les images sont construites par Cloud Build (environ 1 min 20 s par agent).

### 5.1 Un agent

Fichier : `AGENTS="meteo"`, configuration rechargée.

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
terraform init
terraform plan
```

**Résultat obtenu (plan) :**

```
  # google_agent_registry_service.agent["meteo"] will be created
  # google_artifact_registry_repository.agents will be created
  # google_cloud_run_v2_service.agent["meteo"] will be created
  # google_project_iam_member.agent["meteo roles/aiplatform.user"] will be created
  # google_project_iam_member.agent["meteo roles/logging.logWriter"] will be created
  # google_project_iam_member.armor["meteo"] will be created
  # google_project_service.agents["agentregistry.googleapis.com"] will be created
  # google_project_service.agents["aiplatform.googleapis.com"] will be created
  # google_project_iam_member.build["roles/artifactregistry.writer"] will be created
  # google_project_iam_member.build["roles/logging.logWriter"] will be created
  # google_project_iam_member.build["roles/storage.objectViewer"] will be created
  # google_project_service.agents["artifactregistry.googleapis.com"] will be created
  # google_project_service.agents["cloudbuild.googleapis.com"] will be created
  # google_project_service.agents["iam.googleapis.com"] will be created
  # google_project_service.agents["logging.googleapis.com"] will be created
  # google_project_service.agents["modelarmor.googleapis.com"] will be created
  # google_project_service.agents["run.googleapis.com"] will be created
  # google_service_account.agent["meteo"] will be created
  # google_service_account.build will be created
  # terraform_data.image["meteo"] will be created
  # module.armor[0].google_model_armor_template.shield["prompt"] will be created
  # module.armor[0].google_model_armor_template.shield["response"] will be created
Plan: 22 to add, 0 to change, 0 to destroy.
```

**Comment le lire :**
- Les lignes **avec `["meteo"]`** sont celles de l'agent (`for_each`).
- Les lignes **sans clé** sont communes : dépôt d'images, filtres Model Armor, et le **compte de construction**
  (`google_service_account.build` + ses 3 rôles `build[…]` : lire le code envoyé, ranger l'image, écrire le journal).
- `google_project_service.agents[…]` : les API (déjà actives = aucun effet).
- `terraform_data.image["meteo"]` : faire construire l'image de `meteo` par Cloud Build (`gcloud builds submit`).
- `google_agent_registry_service.agent["meteo"]` : son entrée dans le catalogue.

```bash
terraform apply          # relit le plan, demande « yes » ; 5 à 10 minutes
```

**Résultat obtenu :**

```
terraform_data.image["meteo"] (local-exec): a4437a94-…  2026-10-10T22:29:32+00:00  1M23S  gs://…  europe-west1-docker.pkg.dev/aiml-gemini-ent-exp-0zga/agents-a2a/meteo:26b7f058073c  SUCCESS
…
Apply complete! Resources: 22 added, 0 changed, 0 destroyed.

Outputs:

agent_gateway = "(agent_gateway = false)"
cards = {
  "meteo" = "{\"capabilities\":{\"streaming\":true},…,\"name\":\"meteo_agent\",…,\"url\":\"https://meteo-a2a-433175138344.europe-west1.run.app\",…}"
}
ge_agents_page = "(ge_app_id vide : agents non publiés)"
ge_service_agent = "(ge_project_number vide : aucun accès donné à Gemini Enterprise)"
urls = {
  "meteo" = "https://meteo-a2a-….a.run.app"
}
```

| Sortie | Sens |
|---|---|
| `urls` | L'adresse de chaque agent (privée) |
| `cards` | La carte A2A de chaque agent (à coller plus tard dans Gemini Enterprise) |
| `ge_service_agent`, `ge_agents_page` | Rien : pas d'app (normal) |

**Tester** (attendre 3 à 5 minutes : les rôles du nouveau compte s'appliquent) :

```bash
cd .. && ./test.sh                  # tous les agents de « urls »
./test.sh meteo                     # ou un seul (même chose ici)
```

**Résultat attendu :** `== meteo  carte : meteo_agent (A2A 0.3)`, deux questions et réponses, puis
`OK : les agents répondent en A2A v0.3, avec mémoire de conversation`.

### 5.2 Deux agents (ajouter `taille`)

Fichier : `AGENTS="meteo taille"` (**les deux** : la liste décrit ce qui doit exister), recharger, puis :

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform && terraform plan
```

**Résultat obtenu :**

```
  # google_agent_registry_service.agent["taille"] will be created
  # google_cloud_run_v2_service.agent["taille"] will be created
  # google_project_iam_member.agent["taille roles/aiplatform.user"] will be created
  # google_project_iam_member.agent["taille roles/logging.logWriter"] will be created
  # google_project_iam_member.armor["taille"] will be created
  # google_service_account.agent["taille"] will be created
  # terraform_data.image["taille"] will be created
Plan: 7 to add, 0 to change, 0 to destroy.
```

**Uniquement `["taille"]`, et `0 to change, 0 to destroy`** : `meteo` n'est pas touché. `terraform apply`, puis :

```
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.
urls = {
  "meteo" = "https://meteo-a2a-….a.run.app"
  "taille" = "https://taille-a2a-….a.run.app"
}
```

`cd .. && ./test.sh` **Résultat obtenu :**

```
== meteo  carte : meteo_agent (A2A 0.3)
   Q1 > Quel temps fait-il à Chamonix ?
   R1 < …
== taille  carte : taille_agent (A2A 0.3)
   Q1 > Je fais 98 cm de tour de poitrine, quelle taille de veste ?
   R1 < Pour votre tour de poitrine de 98 cm, je vous conseille la taille M, ou L pour plus d'aisance.
   …
OK : les agents répondent en A2A v0.3, avec mémoire de conversation
```

### 5.3 Tous les agents

`AGENTS=""`, recharger, `terraform plan` (les agents manquants : 7 lignes chacun), `terraform apply` (20 à 30 minutes
pour 6 agents depuis zéro), `cd .. && ./test.sh`.

---

## 6. Agent Runtime, dossier 02-bis

Pas d'image ici : Terraform envoie le **code** de chaque agent (son dossier + le code commun) à Agent Runtime.

### 6.1 Un agent

`AGENTS="meteo"`, configuration rechargée :

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform
terraform init
terraform plan
```

**Résultat obtenu :**

```
  # google_project_service.agents["agentregistry.googleapis.com"] will be created
  # google_project_service.agents["aiplatform.googleapis.com"] will be created
  # google_project_service.agents["iam.googleapis.com"] will be created
  # google_project_service.agents["modelarmor.googleapis.com"] will be created
  # module.agent["meteo"].data.external.source will be read during apply
  # module.agent["meteo"].google_project_iam_member.agent["roles/aiplatform.user"] will be created
  # module.agent["meteo"].google_project_iam_member.agent["roles/cloudtrace.agent"] will be created
  # module.agent["meteo"].google_project_iam_member.agent["roles/logging.logWriter"] will be created
  # module.agent["meteo"].google_project_iam_member.agent["roles/monitoring.metricWriter"] will be created
  # module.agent["meteo"].google_project_iam_member.armor will be created
  # module.agent["meteo"].google_service_account.agent will be created
  # module.agent["meteo"].google_vertex_ai_reasoning_engine.agent will be created
  # module.armor[0].google_model_armor_template.shield["prompt"] will be created
  # module.armor[0].google_model_armor_template.shield["response"] will be created
Plan: 13 to add, 0 to change, 0 to destroy.
```

**Comment le lire :** ici le `for_each` est sur un **module** (un paquet de ressources réutilisable,
`terraform/modules/adk_agent`) : `module "agent" { for_each = local.agents … }`. Tout ce qui commence par
`module.agent["meteo"]` appartient à `meteo` :
- son compte ;
- 5 rôles : Gemini, journaux, métriques, traces, Model Armor ;
- l'agent lui-même (`google_vertex_ai_reasoning_engine`) ;
- `data.external.source` : l'empaquetage de son code.

```bash
terraform apply          # yes ; 5 à 10 minutes
```

**Résultat obtenu :**

```
Apply complete! Resources: 13 added, 0 changed, 0 destroyed.

Outputs:

agents = {
  "meteo" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/2594031603923550208"
}
ge_agents_page = "(ge_app_id vide : agents non publiés)"
ge_service_agent = "(ge_project_number vide : aucun accès donné à Gemini Enterprise)"
```

`agents` donne le **nom de ressource** de chaque agent (Gemini Enterprise le demandera plus tard).

**Tester** (3 à 5 minutes après) :

```bash
cd .. && ./test.sh          # tous ; ou ./test.sh meteo
```

**Résultat obtenu :**

```
== meteo  (projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/2594031603923550208)
  -> outil : meteo({'jours': 2, 'ville': 'Chamonix'})
  -> outil : conseil_equipement({'activite': 'randonnée', 'temperature_c': 10, 'pluie_mm': 0, 'vent_kmh': 10.7})
agent : Demain à Chamonix, le temps sera couvert avec des températures comprises entre 7°C et 14°C, sans pluie et avec un vent faible de 11 km/h.
Pour une randonnée, nous vous conseillons de porter un t-shirt technique respirant et une veste légère ou softshell.
```

`-> outil` : les fonctions Python que l'agent a appelées. La question est la 1re question d'exemple du catalogue.

### 6.2 Deux agents, tous les agents

`AGENTS="meteo taille"`, recharger, `terraform plan` :

```
  # module.agent["taille"].google_project_iam_member.agent["roles/aiplatform.user"] will be created
  …
  # module.agent["taille"].google_service_account.agent will be created
  # module.agent["taille"].google_vertex_ai_reasoning_engine.agent will be created
Plan: 7 to add, 0 to change, 0 to destroy.
```

`terraform apply` → `Apply complete! Resources: 7 added, 0 changed, 0 destroyed.` et `agents` montre `meteo` et
`taille`. `./test.sh` :

```
== taille  (projects/…/reasoningEngines/2935179275696865280)
  -> outil : taille_vetement({'type_vetement': 'haut', 'mesure_cm': 98})
agent : Pour votre tour de poitrine de 98 cm, je vous conseille la taille M, ou L pour plus d'aisance.
```

Tous : `AGENTS=""`.

**Dans la console :** 🔎 « Agent Runtime » → **Déploiements** → `meteo-agent` → **Playground** (tester), **Sessions**.

---

## 7. Agent Registry : rien à faire

Les deux dossiers inscrivent les agents dans le catalogue du projet :
- **01-bis** déclare chaque agent Cloud Run avec sa carte (`google_agent_registry_service.agent["meteo"]`) ;
- **Agent Runtime** inscrit lui-même chaque agent de 02-bis.

```bash
gcloud agent-registry agents list --location=$REGION --project=$PROJET_AGENTS --format="table(displayName,agentId)"
```

**Résultat obtenu** (02-bis, `meteo` et `taille`) :

```
DISPLAY_NAME     AGENT_ID
meteo-agent      urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:2594031603923550208
taille-agent     urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:2935179275696865280
```

Avec 01-bis, en plus : `meteo_agent … agentregistry:services:meteo-a2a`. (Une ligne `Workspace Agent` est un agent de
Google : ignorez-la.)

**Dans la console :** 🔎 « Agent Registry » → `europe-west1`.

---

## 8. Dialogflow, dossier 04-bis (option)

Un agent **conversationnel construit à la souris** (pas nos agents Python). Un seul, pas de `AGENTS` ici.

```bash
cd $DOSSIER/04-bis-dialogflow/terraform && terraform init && terraform apply
cd .. && ./test.sh "Bonjour"
```

**Résultat obtenu :**

```
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
dialogflow_agent = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/agents/8396569e-3ccc-4259-82c5-226e55aac241"
intention : Default Welcome Intent
réponse   : Salutations !
```

`dialogflow_agent` est la **source de l'agent Dialogflow** (Gemini Enterprise la demandera). Construire les parcours :
🔎 « Conversational Agents » → « Accueil magasin ».

---

## 9. Ajouter, retirer, modifier un agent

| Vous voulez | Vous faites | Le plan doit montrer |
|---|---|---|
| Ajouter `retour` (pas à pas : 9.1) | `AGENTS="meteo taille retour"` (la liste complète), recharger, `plan` | Seulement `["retour"]`, `N to add, 0 to change, 0 to destroy` |
| Retirer `taille` | `AGENTS="meteo"`, recharger, `plan` | `7 to destroy`, toutes avec `["taille"]` (`because key ["taille"] is not in for_each map`) |
| Nouveau code pour `meteo` | Modifier `agents/trio/meteo_agent/agent.py`, `plan` | Cloud Run : `terraform_data.image["meteo"] must be replaced` + `…agent["meteo"] will be updated in-place`. Agent Runtime : `module.agent["meteo"]…reasoning_engine.agent will be updated in-place`. Rien pour les autres |
| Créer un tout nouvel agent | [12-3, partie 1](12-3-ajouter-des-agents-un-par-un.md#1-créer-lagent-commun-aux-3-méthodes) (`nouvel_agent.py`), puis l'ajouter à `AGENTS` | Seulement la nouvelle clé |
| Rien | `plan` | `No changes. Your infrastructure matches the configuration.` |

**Règle d'or :** lire la ligne `Plan:` **avant** de taper `yes`. Un `destroy` inattendu → répondre `no`, vérifier `AGENTS`.

### 9.1 Un nouvel agent, pas à pas (les autres sont déjà déployés)

Exemple : `meteo` et `taille` tournent déjà ; vous ajoutez le dossier `agents/trio/courriels_agent/` et son entrée dans
`catalogue.json`. **Oui, Terraform ne déploie que lui** : il compare ce qui existe avec ce qui doit exister.

1. Le fichier de configuration :
   - `AGENTS="meteo taille courriels"` : la liste **complète**, l'ancienne plus la nouvelle clé ;
   - si `AGENTS=""` (tout le catalogue), il n'y a rien à changer : la nouvelle entrée du catalogue suffit ;
   - agent OAuth : `AGENTS_OAUTH="courriels=acces-gmail"` ([12-1-8](12-1-8-agent-espace-de-travail-multi-oauth.md)).
2. Recharger, puis le plan :
   ```bash
   source scripts/config.sh config/12-1-agents-dans-projet-exp.env
   cd $DOSSIER/01-bis-cloud-run-a2a/terraform && terraform plan
   ```
3. **Attendu :**
   - seulement des lignes `["courriels"]` (7 ressources) ;
   - pour un agent OAuth, aussi ses API : `google_project_service.agents["gmail.googleapis.com"]` ;
   - `Plan: 7 to add, 0 to change, 0 to destroy` (8 avec l'API Gmail).
   - **Aucune** ligne `["meteo"]` ou `["taille"]`.
4. `terraform apply` → `yes`. Puis `terraform output cards` (la carte du nouvel agent) et, s'il a OAuth,
   `terraform output oauth`.
5. Tester (3 à 5 minutes après) : `cd .. && ./test.sh courriels`.

Agent Runtime : la même chose dans `02-bis-agent-runtime/terraform`. `terraform output agents` donne alors le chemin à
coller dans l'app.

**À ne pas faire :**
- `AGENTS="courriels"` seul : le plan **supprimerait** `meteo` et `taille`.
- `terraform apply -target=…` : inutile ici, car `for_each` isole déjà chaque agent, et `-target` peut oublier une
  ressource liée (droits, API).

**Script et Terraform ne se mélangent pas.** `deployer_shell.sh` crée `courriels-a2a-shell` ; Terraform crée
`courriels-a2a`. Ce sont deux services distincts : choisissez une méthode par agent. Avec le script, un nouvel agent
se déploie sans toucher au fichier : `./scripts/deployer_shell.sh cloudrun courriels`.

---

## 10. Tout supprimer

Dans chaque dossier utilisé (configuration chargée) :

```bash
terraform -chdir=$DOSSIER/01-bis-cloud-run-a2a/terraform destroy     # yes
terraform -chdir=$DOSSIER/02-bis-agent-runtime/terraform destroy     # yes
terraform -chdir=$DOSSIER/04-bis-dialogflow/terraform destroy        # yes, si partie 8
```

**Résultat obtenu** (`meteo` et `taille`) : `Destroy complete! Resources: 29 destroyed.` (Cloud Run : 22 + 7) et
`Destroy complete! Resources: 20 destroyed.` (Agent Runtime : 13 + 7). Les API restent activées.

**Un seul agent** : retirez-le de `AGENTS` et `terraform apply` (partie 9), pas `destroy`.

**Vérifier qu'il ne reste rien** (ni restes d'essais shell ou console) : `python scripts/nettoyer.py` (inventaire,
ne supprime rien). Après `destroy` : `Rien à nettoyer.` Si vous avez perdu l'état Terraform, le script peut aussi
supprimer ce que Terraform avait créé : `python scripts/nettoyer.py --supprimer --avec-terraform`.

---

## 11. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| Terraform demande `var.agents_project_id … Enter a value:` | Configuration pas chargée dans ce terminal (Ctrl+C pour sortir) | `source scripts/config.sh config/12-1-agents-dans-projet-exp.env` |
| Le plan veut **tout créer** alors que les agents existent | Mauvais espace de travail, autre dossier, état perdu | **Ne pas appliquer.** `echo $TF_WORKSPACE` → `scenario-12-1` ; même dossier qu'avant |
| Le plan veut **supprimer** des agents | `AGENTS` ne les contient plus | Remettre la liste complète, recharger |
| `Invalid index … The given key does not identify an element` | Clé de `AGENTS` absente du catalogue | Corriger la clé (le chargement l'a signalé : `ATTENTION : …`) |
| `construction de meteo : nouvel essai dans 40 s (droits en cours d'activation)` | Normal au tout premier `apply` : les droits du compte de construction s'appliquent | Rien : Terraform réessaie seul (4 essais) |
| `Error: local-exec provisioner error` sur `terraform_data.image[…]` | La construction a échoué 4 fois | Lire le journal : 🔎 « Cloud Build » → **Historique** (région `europe-west1`) ; corriger, puis `terraform apply` : seules les images manquantes sont refaites |
| `is tainted, so must be replaced` | Une construction a échoué au dernier `apply` | Normal : relancer `apply` |
| `Error code 13` (Agent Runtime) | Erreur interne de Google | Relancer `terraform apply` : seul l'agent manquant est recréé |
| `ÉCHEC : réponse bloquée par Model Armor` au 1er test | Rôles pas encore actifs | Attendre 2 à 5 minutes |
| Météo : « erreur 429 » | Le service météo public limite les appels | Réessayer plus tard |
| `Error acquiring the state lock` | Un autre `terraform` tourne sur le même dossier | Attendre qu'il finisse |

---

## 12. Et après : quand l'app existera

Remplissez `PROJET_APP`, `NUM_APP`, `APP_ID` dans le fichier, rechargez, `terraform plan` dans chaque dossier :

- **01-bis :** une ligne `google_cloud_run_v2_service_iam_member.ge_invokes["<clé>"]` **par agent** (le droit de l'app
  d'appeler chaque service) ;
- **02-bis :** une ligne `google_project_iam_member.ge_uses_agents_project[0]` (le droit de l'app sur le projet).

Rien n'est recréé. Puis `PUBLIER=oui` pour les ajouter à l'app :
[12-1, B5](12-1-agents-projet-exp-vers-app.md#b5-publier-dans-lapp-donner-laccès-tester-dans-le-chat).
