# 12-2. Agents dans le projet de l'app `acme-gemini-prod` : Agent Runtime, A2A, Agent Registry, Dialogflow

**Le but :**
1. déployer un, plusieurs ou tous les agents **dans le même projet** que l'app Gemini Enterprise
   `dev_gemini-entreprise-app` ;
2. les tester seuls ;
3. les **ajouter à l'app** de 4 façons :
   - **Agent Runtime** ;
   - **A2A** (Cloud Run) ;
   - **Agent Registry** (import par une passerelle) ;
   - **Dialogflow** ;
4. tester dans le chat.

**Trois méthodes, chacune de bout en bout.** Faites-en **une**, jusqu'au nettoyage, puis une autre si vous voulez :

| Méthode | Pour qui | Aller à |
|---|---|---|
| **A. Shell** | Voir et comprendre chaque commande | [Méthode A](#méthode-a--shell) |
| **B. Terraform** | Reproductible, recommandé pour la durée | [Méthode B](#méthode-b--terraform) |
| **C. Console** | Tout à la souris (sauf 2 commandes inévitables) | [Méthode C](#méthode-c--console) |

> **Testé en vrai** (9 et 10 octobre 2026, projets de test jouant ces rôles) :
> - Agent Runtime, Cloud Run A2A, registre, droits, tests, avec un ou plusieurs agents ;
> - Agent Gateway et droit `iap.egressor` (script et Terraform) ;
> - agent Dialogflow (API et Terraform) ;
> - nettoyage.
>
> **Non testable sans votre app :**
> - l'ajout dans l'app ;
> - la liaison de la passerelle ;
> - l'import depuis le registre ;
> - les réponses dans le chat.
>
> Ces étapes suivent la documentation Google.

---

## Sommaire

0. [Ce qu'on construit](#0-ce-quon-construit)
1. [Préparation (une fois, toutes méthodes)](#1-préparation-une-fois-toutes-méthodes)
2. [Méthode A : shell](#méthode-a--shell)
3. [Méthode B : Terraform](#méthode-b--terraform)
4. [Méthode C : console](#méthode-c--console)
5. [Ce qui peut arriver](#5-ce-qui-peut-arriver)

---

## 0. Ce qu'on construit

```
  acme-gemini-prod (523307489860) : L'APP ET LES AGENTS, DANS LE MÊME PROJET
 ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
 │ App Gemini Enterprise dev_gemini-entreprise-app (eu)                                         │
 │   Agents ajoutés par :  ① Agent Runtime   ② A2A   ③ Agent Registry   ④ Dialogflow            │
 │        │                     │               │                  │                            │
 │        ▼                     ▼               ▼                  ▼                            │
 │  Agent Runtime         Cloud Run (A2A)   Agent Registry ◀── Agent Gateway    Dialogflow CX   │
 │  <clé>-…  (vos agents) <clé>-a2a-…       (le catalogue)    « ge-egress »     « Accueil       │
 │                                                            (tout le trafic     magasin »     │
 │                                                             de l'app y passe)                │
 │ Le compte de l'app (c'est LUI qui appelle les agents) :                                      │
 │   service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com                        │
 └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

| Façon d'ajouter dans l'app | Ce qu'il faut | Droit à donner au compte de l'app |
|---|---|---|
| ① **Agent Runtime** | L'agent déployé | **Aucun** : dans le projet de l'app, Google l'a déjà donné |
| ② **A2A** | Un service Cloud Run privé + sa carte | **Demandeur Cloud Run** (`roles/run.invoker`) sur **chaque service** |
| ③ **Agent Registry** | L'agent dans le registre du projet + une **Agent Gateway** reliée à l'app | `run.invoker` (service) + **IAP-secured Egressor** (`roles/iap.egressor`) sur l'entrée du registre |
| ④ **Dialogflow** | Un agent Dialogflow CX | Aucun |

> ⚠ **Le mode ③ change toute l'app.** Une fois la passerelle reliée, **tout** le trafic de l'app (modèle compris)
> passe par elle, et ce qui n'est pas autorisé est bloqué. À décider avec la sécurité, à faire **en dernier**, et
> réversible (on retire la liaison).

**Les mots** (agent, clé, A2A, carte, Agent Runtime, Agent Registry, compte de service, rôle, API) :
[12-1-1, partie 0](12-1-1-deployer-agents-shell.md#0-les-mots-à-connaître).

---

## 1. Préparation (une fois, toutes méthodes)

### 1.1 Les outils

| Outil | Mac (Homebrew) | Vérifier |
|---|---|---|
| gcloud | `brew install --cask google-cloud-sdk` puis `gcloud components install beta` | `gcloud version` |
| Terraform 1.9+ (méthode B) | `brew tap hashicorp/tap && brew install hashicorp/tap/terraform` | `terraform version` |
| uv (Python 3.12 à 3.14) | `brew install uv` | `uv --version` |

**Pas de Docker** : les images Cloud Run sont construites **dans Google Cloud** (Cloud Build), avec gcloud seulement. Un
terminal Linux ou Mac, ou Cloud Shell, suffit.

### 1.2 Le dossier et son Python

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/trio/requirements.txt
python scripts/test_trio.py
```

**Résultat obtenu :** `tests trio OK (9 scénarios, 6 agents)`. L'invite commence par `(.venv)`.

### 1.3 Le fichier de configuration

Ouvrez `config/12-2-agents-dans-projet-app.env`. Il est déjà rempli ; vérifiez chaque ligne :

```bash
PROJET_APP=acme-gemini-prod
NUM_APP=523307489860
APP_ID=dev_gemini-entreprise-app
GE_LOCATION=eu
PROJET_AGENTS=acme-gemini-prod      # le MÊME projet que l'app
NUM_AGENTS=523307489860
REGION=europe-west1
AGENTS=""
PUBLIER=non
AGENT_GATEWAY=non
AGENTS_OAUTH=""
GROUPE_UTILISATEURS=equipe-agents@acme.example
DOSSIER=~/Desktop/09-agents-multi-projets-gemini-enterprise
```

| Ligne | Ce que c'est | Où le trouver |
|---|---|---|
| `PROJET_APP`, `PROJET_AGENTS` | L'**ID** du projet (le même ici) | Console → sélecteur de projet → colonne **ID** |
| `NUM_APP`, `NUM_AGENTS` | Son **numéro** (le même) | Même écran, colonne **Numéro** |
| `APP_ID` | L'**ID** de l'app (pas son nom affiché) | 🔎 « Gemini Enterprise » → l'app → **Présentation** |
| `GE_LOCATION` | Localisation de l'app | Même écran : `eu` |
| `REGION` | Où tournent les agents : `europe-…` pour une app `eu` | — |
| `AGENTS` | **Quels agents** : clés séparées par des espaces ; **vide = tous** (6) | `agents/trio/catalogue.json` |
| `PUBLIER` | Terraform ajoute-t-il les agents à l'app ? `non` d'abord, `oui` à l'étape B3 | — |
| `AGENT_GATEWAY` | Terraform crée-t-il la passerelle du mode ③ ? `non`, puis `oui` à l'étape B4 | — |
| `GROUPE_UTILISATEURS` | Le groupe Google qui utilisera les agents | Votre admin Google Workspace |

**Exemples pour `AGENTS` :** `"meteo"` (un agent) · `"meteo taille"` (deux) · `""` (tous).

**Charger la configuration** (dans chaque nouveau terminal, et après chaque modification du fichier) :

```bash
source scripts/config.sh config/12-2-agents-dans-projet-app.env
```

**Résultat attendu :**

```
== Configuration chargée : config/12-2-agents-dans-projet-app.env
   App Gemini Enterprise : dev_gemini-entreprise-app   (projet acme-gemini-prod, numéro 523307489860, eu)
   Projet des agents     : acme-gemini-prod (numéro 523307489860), région europe-west1   [même projet que l'app : oui]
   Agents à déployer     : meteo redaction traduction taille retour identite
   Compte de l'app       : service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
   Terraform             : espace « scenario-12-2 », publication dans l'app : non
   Dossier               : /Users/<vous>/Desktop/09-agents-multi-projets-gemini-enterprise
   OK
```

**À vérifier :** `[même projet que l'app : oui]`, vos agents, et `OK`. **Toujours avec `source`**, jamais derrière un `|`.

### 1.4 Se connecter, vérifier le numéro

```bash
gcloud auth login
gcloud auth application-default login
gcloud projects describe $PROJET_APP --format='value(projectNumber)'
```

**Résultat attendu :** `523307489860`.

### 1.5 Vos droits sur `acme-gemini-prod`

```bash
gcloud projects get-iam-policy $PROJET_APP --flatten=bindings \
  --filter="bindings.members:user:$(gcloud config get-value account 2>/dev/null)" --format="value(bindings.role)"
```

Il faut `roles/owner`, ou :
- **agents :** `aiplatform.admin`, `run.admin`, `artifactregistry.admin`, `cloudbuild.builds.editor`, `storage.admin`
  (construction des images par Cloud Build), `iam.serviceAccountAdmin`,
  `iam.serviceAccountUser`, `resourcemanager.projectIamAdmin`, `serviceusage.serviceUsageAdmin`, `modelarmor.admin`,
  `agentregistry.admin` ;
- **app :** `discoveryengine.admin` ;
- **mode ③ :** `networkservices.admin`, `iap.admin` ;
- **mode ④ :** `dialogflow.admin`.

Un rôle reçu par un groupe n'apparaît pas ici : vérifiez dans 🔎 « IAM ».

### 1.6 Les API

```bash
./scripts/verifier_api.sh $PROJET_APP cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com \
  aiplatform.googleapis.com agentregistry.googleapis.com modelarmor.googleapis.com logging.googleapis.com \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com discoveryengine.googleapis.com dialogflow.googleapis.com \
  networkservices.googleapis.com iap.googleapis.com
```

**Résultat attendu :** une ligne `OK` par API (ou `MANQUANTE …`, puis `activées : …`), et `rien à activer`.

| API | Pour |
|---|---|
| `cloudresourcemanager`, `serviceusage`, `iam`, `aiplatform`, `modelarmor`, `logging` | Tout |
| `agentregistry` | Le catalogue, mode ③ |
| `run`, `artifactregistry`, `cloudbuild` | Cloud Run (②, ③) ; `cloudbuild` construit les images dans Google Cloud (tout juste activée : attendre une minute avant la 1re construction) |
| `discoveryengine` | L'app Gemini Enterprise |
| `dialogflow` | Mode ④ |
| `networkservices`, `iap` | Mode ③ (passerelle, droit de passage) |

**Dans la console :** 🔎 « API et services » → **API et services activés**.

### 1.7 Le compte de l'app et son droit sur le projet

```bash
gcloud beta services identity create --service=discoveryengine.googleapis.com --project=$PROJET_APP
gcloud projects get-iam-policy $PROJET_APP --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
```

**Résultat attendu :**
1. `Service identity created: service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`. Google dit
   « created » même si le compte existait déjà : rien ne change.
2. `roles/discoveryengine.serviceAgent`. C'est ce droit qui permet à l'app d'appeler les agents Agent Runtime **du
   même projet** : vous n'avez rien à donner. S'il manque : [partie 5](#5-ce-qui-peut-arriver).

---

## Méthode A : shell

Chaque ressource est créée par une commande que vous voyez. Les noms finissent par `-shell`. Configuration 12-2 chargée.

### A1. Déployer et tester les agents

Suivez **[12-1-1](12-1-1-deployer-agents-shell.md)** des parties **5 à 9**, sans rien changer aux commandes :
- **5** : les API (déjà fait en 1.6, sans effet) ;
- **6** : Model Armor ;
- **7** : Cloud Run, un agent puis plusieurs ;
- **8** : Agent Runtime ;
- **9** : Agent Registry.

Avec la configuration 12-2 chargée, `$PROJET_AGENTS` vaut `acme-gemini-prod` : tout est créé **dans le
projet de l'app**.

**À la fin de A1, vous avez**, pour chaque agent `K` choisi :

| Quoi | Nom | Vérifier |
|---|---|---|
| Service Cloud Run privé | `K-a2a-shell`, URL `https://K-a2a-shell-523307489860.europe-west1.run.app` | `./01-bis-cloud-run-a2a/test.sh` → `OK` |
| Agent Agent Runtime | `K-shell` (nom de ressource `projects/100000000003/locations/europe-west1/reasoningEngines/…`) | `python scripts/query.py` → une réponse |
| Entrées du registre | `K-a2a-shell` (Cloud Run) et `K-shell` (Agent Runtime) | `gcloud agent-registry agents list …` |
| Cartes | `carte-K.json` (dans le dossier) | `ls carte-*.json` |

### A2. Donner à l'app le droit d'appeler les services Cloud Run

Agent Runtime : **rien** (1.7). Cloud Run : un droit **par service** :

```bash
for K in $(echo $AGENTS_LISTE); do
  gcloud run services add-iam-policy-binding $K-a2a-shell --region=$REGION --project=$PROJET_APP \
    --role=roles/run.invoker --member=serviceAccount:$GE_SA >/dev/null && echo "$K-a2a-shell : run.invoker pour l'app"
done
```

**Résultat attendu :** une ligne `meteo-a2a-shell : run.invoker pour l'app` par agent. (`for K in …; do … done` répète la
commande pour chaque agent de `AGENTS`. Un seul agent : remplacez par `K=meteo` et la commande seule.)

**Vérifier :**

```bash
for K in $(echo $AGENTS_LISTE); do echo "$K-a2a-shell : $(gcloud run services get-iam-policy $K-a2a-shell --region=$REGION \
  --project=$PROJET_APP --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)")"; done
```

**Attendu :** `meteo-a2a-shell : roles/run.invoker` pour chaque agent. **Dans la console :** 🔎 « Cloud Run » → le
service → **Sécurité** → le compte de l'app avec *Demandeur Cloud Run*.

### A3. Ajouter les agents dans l'app (Agent Runtime et A2A)

**① Agent Runtime**, un agent par commande :

```bash
for K in $(echo $AGENTS_LISTE); do
  RES=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_APP/locations/$REGION/reasoningEngines" \
    | python3 -c "import json,sys; print(next(e['name'] for e in json.load(sys.stdin)['reasoningEngines'] if e['displayName']=='$K-shell'))")
  NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
  DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
  ./scripts/add_agent_to_ge.sh adk "$RES" "$NOM (shell)" "$DESC"
done
```

| Ligne | Ce qu'elle fait |
|---|---|
| `RES=…` | Retrouve le nom de ressource de l'agent `K-shell` |
| `NOM=…`, `DESC=…` | Lisent son nom affiché et sa description dans le catalogue |
| `add_agent_to_ge.sh adk …` | L'ajoute à l'app (même projet : aucun droit à poser, il ajoute seulement) |

**Résultat attendu :** `ajouté : projects/…/engines/dev_gemini-entreprise-app/assistants/default_assistant/agents/<ID>`
par agent.

**② A2A**, avec les cartes de A1 :

```bash
for K in $(echo $AGENTS_LISTE); do
  NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
  ./scripts/add_agent_to_ge.sh a2a carte-$K.json "$NOM (A2A shell)"
done
./scripts/add_agent_to_ge.sh list
```

**Résultat attendu :** `droit accordé : …` (déjà fait en A2, sans effet), `ajouté : …` par agent, puis la liste :

```
Météo & équipement (shell)          adkAgentDefinition     <ID>
Météo & équipement (A2A shell)      a2aAgentDefinition     <ID>
…
```

Chaque agent est une **entrée séparée** dans l'app.

### A4. Donner l'accès, tester dans le chat

**Pour chaque agent** (console) : 🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` → **Agents** → l'agent →
onglet **Autorisations utilisateur** → **Ajouter** → `equipe-agents@acme.example` → rôle **Agent User** →
**Enregistrer**. Les membres du groupe doivent avoir une **licence** Gemini Enterprise.

**Tester :** l'app → **Intégration** → le **lien de l'app web**, avec un compte du groupe → **Agents** →
« Traduction Acme (shell) » → « Traduis en allemand : retour gratuit sur les chaussures Kiprun ».
**Attendu :** une traduction allemande, puis `Contrôle : conforme`. La 1re réponse peut prendre 20 à 40 s (l'agent
démarre).

### A5. Mode Agent Registry (option, en dernier)

Les entrées du registre existent déjà (A1). Il reste 4 étapes.

**1. Créer la passerelle** (une fois) :

```bash
cat > ge-egress.yaml <<FIN
name: ge-egress
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
- //agentregistry.googleapis.com/projects/$PROJET_APP/locations/$REGION
FIN
gcloud network-services agent-gateways import ge-egress --location=$REGION --source=ge-egress.yaml --project=$PROJET_APP
gcloud network-services agent-gateways list --location=$REGION --project=$PROJET_APP
```

Le fichier `ge-egress.yaml` décrit la passerelle : gérée par Google, ouverte vers **le registre de ce projet**.
**Résultat attendu :** `ge-egress` dans la liste (`projects/…/locations/europe-west1/agentGateways/ge-egress`).

**2. Le droit de passage**, pour le compte de l'app, sur chaque entrée du registre :

```bash
for K in $(echo $AGENTS_LISTE); do ./scripts/autoriser_passerelle.sh $K-a2a-shell; done
```

**Résultat obtenu :**

```
ajouter : roles/iap.egressor pour serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com sur projects/acme-gemini-prod/locations/europe-west1/iap_web/agentRegistry/agents/agentregistry-00000000-…
```

**3. Relier la passerelle à l'app** (console, **décision sécurité**) : 🔎 « Gemini Enterprise » →
`dev_gemini-entreprise-app` → **Sécurité** → **Configuration** → *Agent Gateway* →
`projects/acme-gemini-prod/locations/europe-west1/agentGateways/ge-egress` → **Enregistrer**.

**4. Importer :** l'app → **Agents** → **+ Ajouter un agent** → **Agents depuis Agent Registry** → choisir l'agent →
**Ajouter un agent** → vérifier → **Suivant** → **Terminer**. Puis **Agent User** et test (A4).

**Revenir en arrière :** retirer la liaison (étape 3, laisser vide → **Enregistrer**), puis :

```bash
for K in $(echo $AGENTS_LISTE); do ./scripts/autoriser_passerelle.sh $K-a2a-shell retirer; done
gcloud network-services agent-gateways delete ge-egress --location=$REGION --project=$PROJET_APP --quiet
```

### A6. Mode Dialogflow (option)

**1. Créer l'agent :**

```bash
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  -H "x-goog-user-project: $PROJET_APP" \
  "https://$REGION-dialogflow.googleapis.com/v3/projects/$PROJET_APP/locations/$REGION/agents" \
  -d '{"displayName":"Accueil magasin (shell)","defaultLanguageCode":"fr","timeZone":"Europe/Paris","description":"Accueil et orientation en magasin"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])' | tee agent-dialogflow.txt
```

**Résultat obtenu :** `projects/acme-gemini-prod/locations/europe-west1/agents/8396569e-3ccc-4259-82c5-226e55aac241`.
C'est la **source de l'agent Dialogflow**, gardée dans `agent-dialogflow.txt`.

**2. Le tester seul :**

```bash
AGENT=$(cat agent-dialogflow.txt) ./04-bis-dialogflow/test.sh "Bonjour"
```

**Résultat obtenu :**

```
intention : Default Welcome Intent
réponse   : Salutations !
```

Construisez ensuite le parcours (flux, pages, ou *playbook* génératif) : 🔎 « Conversational Agents » → l'agent.

**3. L'ajouter dans l'app :**
1. L'app → **Agents** → **+ Ajouter un agent** → **Agent personnalisé via Dialogflow**.
2. Remplir :
   - **Nom de votre agent** : `Accueil magasin` ;
   - **Décrivez votre agent** : une phrase ;
   - **Source de l'agent Dialogflow** : le contenu de `agent-dialogflow.txt`.
3. **Créer**.
4. **Agent User** pour le groupe, puis test dans le chat : « Bonjour ».

### A7. Nettoyer la méthode A

1. **Dans l'app** (console) :
   - retirer la liaison de la passerelle, si faite ;
   - supprimer les agents ajoutés : `./scripts/add_agent_to_ge.sh list`, puis
     `./scripts/add_agent_to_ge.sh delete "<nom affiché>"` pour chacun.
2. **Passerelle et droits de passage :** « Revenir en arrière » de A5.
3. **Tout le reste**, avec le script de nettoyage. Il fait l'inventaire : services, agents, registre, Dialogflow,
   comptes et leurs rôles, images, filtres. Il ne supprime qu'après confirmation :
   ```bash
   python scripts/nettoyer.py                 # inventaire : vérifier la liste
   python scripts/nettoyer.py --supprimer     # tapez l'ID du projet pour confirmer
   rm -f env-*.yaml carte-*.json agent-dialogflow.txt ge-egress.yaml
   ```
   Il ne touche **jamais** au droit `discoveryengine.serviceAgent` du compte de l'app : dans le projet de l'app, ce droit
   appartient à Google.

---

## Méthode B : Terraform

Terraform crée tout à partir du fichier de configuration (agents choisis par `AGENTS`). L'état est gardé dans
`terraform.tfstate.d/scenario-12-2/` de chaque dossier : séparé de celui de 12-1, à ne pas supprimer.

**Comprendre `AGENTS` et `for_each`, lire un plan :** [12-1-2, parties 0 et 2](12-1-2-deployer-agents-terraform.md#2-for_each--comment-une-ligne-de-configuration-donne-n-agents).
**L'essentiel :** `AGENTS` dit **ce qui doit exister**. Ajouter une clé crée cet agent ; retirer une clé le supprime.
Lisez toujours la ligne `Plan:` avant `yes`.

### B1. Agent Runtime (dossier 02-bis)

Configuration 12-2 chargée (`PUBLIER=non`) :

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform
terraform init
terraform plan
```

**Résultat attendu :**

| `AGENTS` | Ligne `Plan:` |
|---|---|
| `"meteo"` | `13 to add, 0 to change, 0 to destroy` |
| `"meteo taille"` | `20 to add` (13 + 7) |
| `""` (6 agents) | `48 to add` |

Pas de ligne `ge_uses_agents_project` : même projet, le droit de l'app existe déjà (1.7).

```bash
terraform apply       # yes ; 5 à 10 minutes
cd .. && ./test.sh    # 3 à 5 minutes après ; ./test.sh meteo pour un seul
```

**Résultat attendu :** `Apply complete!`, la sortie `agents = { "meteo" = "projects/acme-gemini-prod/locations/europe-west1/reasoningEngines/…", … }`,
puis pour chaque agent les outils appelés (`-> outil : …`) et la réponse.

### B2. Cloud Run A2A (dossier 01-bis)

Pas de Docker : Terraform fait construire les images par Cloud Build.

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
terraform init
terraform plan
```

**Résultat attendu :**

| `AGENTS` | Ligne `Plan:` |
|---|---|
| `"meteo"` | `23 to add` |
| chaque agent en plus | `+8` |
| `""` (6 agents) | `63 to add` |

Une fois pour tous : le compte qui construit les images, `google_service_account.build` (`agents-a2a-build-sa`), ses
3 rôles `google_project_iam_member.build["roles/…"]` et l'API `google_project_service.agents["cloudbuild.googleapis.com"]`.
Par agent :
- son image (`terraform_data.image["<clé>"]` : `gcloud builds submit`, ~1 min 20 s) ;
- son compte et ses rôles ;
- son service ;
- son entrée dans le registre ;
- `google_cloud_run_v2_service_iam_member.ge_invokes["<clé>"]` : le droit de l'app d'appeler ce service.

```bash
terraform apply       # yes ; 5 à 10 minutes (images construites par Cloud Build)
cd .. && ./test.sh    # 3 à 5 minutes après
```

**Résultat attendu :** `Apply complete!`, `urls = { … }`, puis pour chaque agent deux réponses et
`OK : les agents répondent en A2A v0.3, avec mémoire de conversation`. Les constructions d'images et leurs journaux :
🔎 « Cloud Build » → **Historique** (région `europe-west1`). `PERMISSION_DENIED` pendant une construction : Terraform
réessaie jusqu'à 4 fois ; sinon attendez 1 à 2 minutes et relancez `terraform apply`.

### B3. Ajouter les agents dans l'app (Agent Runtime et A2A), donner l'accès, tester

Dans le fichier : `PUBLIER=non` → **`PUBLIER=oui`**. Puis :

```bash
cd $DOSSIER && source scripts/config.sh config/12-2-agents-dans-projet-app.env     # « publication dans l'app : oui »
terraform -chdir=02-bis-agent-runtime/terraform plan
```

**Résultat attendu :** `google_project_service.ge[0]` et une ligne `terraform_data.publish["<clé>"]` par agent, rien
d'autre : `Plan: 7 to add` avec 6 agents (1 + 6). Puis :

```bash
terraform -chdir=02-bis-agent-runtime/terraform apply
terraform -chdir=01-bis-cloud-run-a2a/terraform apply
```

**Résultat attendu :** une ligne `registered <nom de l'agent>` par agent, et `Apply complete! Resources: 7 added` dans
chaque dossier. Les agents A2A ont « (A2A) » dans leur nom. `terraform -chdir=01-bis-cloud-run-a2a/terraform output
ge_agents_page` : le lien de la page Agents de l'app.

**Donner l'accès et tester :** exactement [A4](#a4-donner-laccès-tester-dans-le-chat).

### B4. Mode Agent Registry par Terraform (option, en dernier)

Dans le fichier : `AGENT_GATEWAY=oui`. Recharger, puis :

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform && terraform plan
```

**Résultat obtenu :**

```
  # google_iap_agent_registry_agent_iam_member.ge_passe["meteo"] will be created
  …                                                 (une ligne ge_passe par agent)
  # google_network_services_agent_gateway.ge[0] will be created
  # google_project_service.gateway["iap.googleapis.com"] will be created
  # google_project_service.gateway["networkservices.googleapis.com"] will be created
```

`terraform apply`, puis `terraform output agent_gateway` donne la passerelle. **Relier** et **importer** : étapes 3
et 4 de [A5](#a5-mode-agent-registry-option-en-dernier) (console).

Terraform **refuse** cette option si les agents ne sont pas dans le projet de l'app
(`agent_gateway : les agents doivent être dans le projet de l'app…`) : c'est la règle de Google.

### B5. Mode Dialogflow (dossier 04-bis)

```bash
cd $DOSSIER/04-bis-dialogflow/terraform && terraform init && terraform apply
cd .. && ./test.sh "Bonjour"
```

**Résultat obtenu :**

```
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
dialogflow_agent = "projects/acme-gemini-prod/locations/europe-west1/agents/8396569e-3ccc-4259-82c5-226e55aac241"
intention : Default Welcome Intent
réponse   : Salutations !
```

Ajouter dans l'app : étape 3 de [A6](#a6-mode-dialogflow-option), avec la valeur de `dialogflow_agent`.

### B6. Ajouter, retirer un agent plus tard

Dans le fichier : modifier `AGENTS` (la liste **complète** de ce qui doit exister), recharger, `terraform plan`
dans 02-bis et 01-bis :
- **ajout** : seulement des lignes `["<nouvelle clé>"]`, `0 to change, 0 to destroy` ;
- **retrait** : seulement des `destroy` pour cette clé. Avec `PUBLIER=oui`, l'agent est aussi retiré de l'app.

Puis `apply`. Nouvel agent : [12-3](12-3-ajouter-des-agents-un-par-un.md).

### B7. Nettoyer la méthode B

Dans l'app : retirer la liaison de la passerelle (si faite) et l'agent Dialogflow ajouté à la main. Puis :

```bash
cd $DOSSIER && source scripts/config.sh config/12-2-agents-dans-projet-app.env
terraform -chdir=04-bis-dialogflow/terraform destroy        # yes ; Resources: 2 destroyed
terraform -chdir=01-bis-cloud-run-a2a/terraform destroy     # yes ; retire aussi passerelle, droits de passage, publications
terraform -chdir=02-bis-agent-runtime/terraform destroy     # yes
python scripts/nettoyer.py                                  # vérifier : « Rien à nettoyer. »
```

`destroy` de 01-bis : 63 ressources avec 6 agents (70 avec `PUBLIER=oui`) ; 02-bis : 48 (55 avec `PUBLIER=oui`). Le
bucket `gs://acme-gemini-prod_cloudbuild` (créé par Google pour les constructions) reste : à la main,
`gcloud storage rm -r gs://${PROJET_AGENTS}_cloudbuild`.

---

## Méthode C : console

Projet **acme-gemini-prod** sélectionné en haut de la console, pour **toutes** les étapes.

### C1. Déployer et tester les agents

Suivez **[12-1-3](12-1-3-deployer-agents-console.md)**, parties **1 à 7**, dans ce projet. Les noms finissent par
`-console`. À la fin, pour chaque agent :
- un service Cloud Run `K-a2a-console` testé ;
- un agent Agent Runtime `K-console` testé dans le **Playground** (nom de ressource copié) ;
- leurs entrées dans Agent Registry ;
- la **carte** de chaque agent Cloud Run (copiée en 12-1-3, 5.2).

### C2. Donner à l'app le droit d'appeler les services Cloud Run

Agent Runtime : **rien**. Vérification : 🔎 « IAM » → cocher **Inclure les attributions de rôles fournies par Google**
→ `service-100000000003@gcp-sa-discoveryengine…` a **Discovery Engine Service Agent**.

Cloud Run, **pour chaque service** :
1. 🔎 « Cloud Run » → `meteo-a2a-console` → onglet **Sécurité** (ou **Autorisations**).
2. **Ajouter un compte principal** → `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
3. Rôle **Demandeur Cloud Run** (*Cloud Run Invoker*) → **Enregistrer**.

### C3. Ajouter les agents dans l'app (Agent Runtime et A2A)

🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` → **Agents** → **+ Ajouter un agent**, **une fois par agent** :

- **① Agent personnalisé via Agent Runtime** → **Ajouter**, puis remplir :
  - **Nom de l'agent** : `Météo & équipement (console)` ;
  - **Décrivez votre agent** : la description de `agents/trio/catalogue.json` ;
  - **Chemin de ressource Agent Runtime** : le nom de ressource copié en C1.

  → **Créer**.
- **② Agent personnalisé via A2A** → **Ajouter** → coller **la carte** (JSON) → **Prévisualiser les détails de
  l'agent** (vérifier nom, description, compétences) → **Suivant** → *Authentification* : **Ignorer et terminer**.

### C4. Donner l'accès, tester dans le chat

Exactement [A4](#a4-donner-laccès-tester-dans-le-chat).

### C5. Mode Agent Registry (option, en dernier)

1. **La passerelle :** la console n'a pas toujours d'écran de création. Dans Cloud Shell, l'étape 1 de
   [A5](#a5-mode-agent-registry-option-en-dernier).
2. **Le droit de passage, pour chaque entrée :**
   1. 🔎 « Agent Registry » → région `europe-west1` → l'entrée (`meteo-a2a-console`) → **Autorisations**.
   2. **Ajouter un compte principal** → `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
   3. Rôle **IAP-secured Egressor** → **Enregistrer**.
3. **Relier** et **importer :** étapes 3 et 4 de [A5](#a5-mode-agent-registry-option-en-dernier).

### C6. Mode Dialogflow (option)

1. 🔎 « Conversational Agents » → **Créer un agent** → **Créer de toutes pièces**. Remplir :
   - **Nom** : `Accueil magasin` ;
   - **Région** : `europe-west1` ;
   - **Langue** : `fr` ;
   - **Fuseau** : `Europe/Paris`.

   → **Créer**.
2. **Tester seul :** panneau **Tester l'agent** → « Bonjour ». **Attendu :** une salutation.
3. **Source de l'agent :** **Paramètres de l'agent** → copier `projects/…/locations/europe-west1/agents/…`.
4. **Ajouter dans l'app :** étape 3 de [A6](#a6-mode-dialogflow-option).

### C7. Nettoyer la méthode C

1. **Dans l'app :**
   - retirer la liaison de la passerelle ;
   - supprimer les agents ajoutés : **Agents** → l'agent → **Supprimer**.
2. **Passerelle :** Cloud Shell,
   `gcloud network-services agent-gateways delete ge-egress --location=europe-west1 --project=acme-gemini-prod`.
3. **Le reste :** à la souris comme en [12-1-3, partie 10](12-1-3-deployer-agents-console.md#10-ajouter-un-agent-plus-tard-en-retirer-un-tout-supprimer),
   ou en une fois dans Cloud Shell : `python3 scripts/nettoyer.py`, puis `--supprimer`.

Ne retirez **jamais** *Discovery Engine Service Agent* au compte de l'app.

---

## 5. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `[même projet que l'app : non]` au chargement | `PROJET_AGENTS` différent de `PROJET_APP` | Mettre le même ID, recharger |
| `roles/discoveryengine.serviceAgent` absent (1.7) | Compte de l'app jamais créé, ou droit retiré | `gcloud beta services identity create …` (1.7), puis `gcloud projects add-iam-policy-binding $PROJET_APP --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA --condition=None` |
| `ajouté` ne s'affiche pas, `PERMISSION_DENIED` (A3) | Pas Gemini Enterprise Admin | Rôle `discoveryengine.admin` sur le projet |
| Agent absent du chat | Pas d'**Agent User** pour le groupe, ou pas de licence | A4 |
| « L'agent n'a pas pu répondre » (A2A) | Droit `run.invoker` manquant sur ce service | A2 / C2 ; attendre 2 à 3 minutes après l'ajout |
| Tout le chat est bloqué après la liaison de la passerelle | Droit `iap.egressor` manquant, ou passerelle mal configurée | Retirer la liaison (app → Sécurité → Configuration) ; vérifier A5 étape 2 |
| L'agent n'est pas dans « Agents depuis Agent Registry » | Registre d'une autre région, ou passerelle non reliée | Entrées en `europe-west1` ; étape 3 de A5 |
| `agent_gateway : les agents doivent être dans le projet de l'app` (Terraform) | Option activée avec la configuration 12-1 | Utiliser `config/12-2-…env` |
| L'agent Dialogflow ne répond pas dans l'app | Agent sans contenu, ou autre région | Le tester seul (A6 étape 2) ; région `europe-west1` |
| `PERMISSION_DENIED` à la construction d'une image, juste après avoir activé Cloud Build ou créé le compte de construction | Droits tout neufs, pas encore actifs | Attendre 1 à 2 minutes, relancer |
| `… does not have storage.objects.get access to the Google Cloud Storage object` | Compte de construction `agents-build-sa` absent, ou `--service-account` oublié | [12-1-1, partie 7](12-1-1-deployer-agents-shell.md#7-cloud-run-a2a--un-agent-puis-plusieurs) |
| Construction `FAILURE` | Erreur dans l'image | Lien du journal affiché par gcloud ; 🔎 « Cloud Build » → **Historique** (région `europe-west1`) |
| `ÉCHEC : réponse bloquée par Model Armor` juste après le déploiement | Rôles des nouveaux comptes pas encore actifs | Attendre 2 à 5 minutes |
| Autres erreurs de déploiement | — | [12-1-1, partie 14](12-1-1-deployer-agents-shell.md#14-ce-qui-peut-arriver), [12-1-2, partie 11](12-1-2-deployer-agents-terraform.md#11-ce-qui-peut-arriver) |
