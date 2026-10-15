# 12-1. Agents dans `aiml-gemini-ent-exp-0zga`, utilisés dans l'app de `acme-gemini-prod`

**Le but :** déployer des agents dans le projet **d'expérimentation**, les tester seuls, puis les **connecter à l'app
Gemini Enterprise** `dev_gemini-entreprise-app` du projet principal.

**Trois méthodes, chacune de bout en bout** : faites-en **une**, jusqu'au test dans l'app et au nettoyage, puis passez à
la suivante si vous voulez. Les noms des ressources diffèrent d'une méthode à l'autre (suffixe `-shell`, `-console` ;
sans suffixe pour Terraform), donc elles ne se gênent pas.

| Méthode | Pour qui | Ce qui est fait à la main |
|---|---|---|
| [**A. Shell**](#méthode-a--shell-gcloud--scripts) (gcloud + scripts) | Comprendre chaque ressource, tout reproduire en copier-coller | Tout, commande par commande |
| [**B. Terraform**](#méthode-b--terraform) | La cible : reproductible, relu, défait proprement | 3 commandes par étape ; Terraform crée le reste |
| [**C. Console**](#méthode-c--console-interface) (interface) | Voir chaque écran, sans ligne de commande (sauf 2 commandes inévitables) | Tout, écran par écran |

> **Le parcours pas à pas, guide par guide :**
> 1. déployer : [12-1-1 Shell](12-1-1-deployer-agents-shell.md) · [12-1-2 Terraform](12-1-2-deployer-agents-terraform.md) · [12-1-3 Console](12-1-3-deployer-agents-console.md) ;
> 2. connecter à l'app : [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md) ;
> 3. simuler l'appel : [12-1-5](12-1-5-simuler-appel-gemini-enterprise.md) ;
> 4. la console de l'app : [12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md) ;
> 5. OAuth, identité, outils : [12-1-7](12-1-7-agents-oauth-identite-outils.md) ;
> 6. Un agent Gmail, Agenda, Drive, Sheets (sans suppression), un ou plusieurs fournisseurs OAuth : [12-1-8](12-1-8-agent-espace-de-travail-multi-oauth.md).
>
> Ce document-ci reste la vue d'ensemble (trois méthodes, de bout en bout).
>
> **Seulement déployer les agents (pas encore d'app), un, plusieurs ou tous ?** Guides pas à pas dédiés :
> [12-1-1 Shell](12-1-1-deployer-agents-shell.md) · [12-1-2 Terraform](12-1-2-deployer-agents-terraform.md) ·
> [12-1-3 Console](12-1-3-deployer-agents-console.md). Le choix des agents : ligne `AGENTS` du fichier de configuration.
>
> **6 agents, pas 3 :** le catalogue `agents/trio/catalogue.json` contient aussi **Conseil taille**, **Retours
> produits** et **Identité utilisateur**. Terraform (méthode B) déploie tout le catalogue ; les boucles shell et la console (A, C) montrent les 3
> premiers : pour les autres, ou pour **ajouter vos agents un par un**, voir [12-3](12-3-ajouter-des-agents-un-par-un.md).
>
> **Testé en vrai** (9 octobre 2026, deux projets de test jouant ces deux rôles) : méthodes A et B de bout en bout,
> jusqu'au droit de l'app vérifié. **Non testable sans votre app** : l'écran d'ajout dans l'app et la réponse dans le chat
> (étapes A6, B5, C7). Méthode C : les écrans sont décrits d'après la documentation Google ; les libellés peuvent varier
> légèrement selon la version de la console.

---

## Sommaire

0. [Ce qu'on construit, et les protocoles possibles](#0-ce-quon-construit-et-les-protocoles-possibles)
1. [Préparation commune (une fois)](#1-préparation-commune-une-fois)
2. [Méthode A : shell (gcloud + scripts)](#méthode-a--shell-gcloud--scripts)
3. [Méthode B : Terraform](#méthode-b--terraform)
4. [Méthode C : console (interface)](#méthode-c--console-interface)
5. [Ce qui peut arriver](#5-ce-qui-peut-arriver)

---

## 0. Ce qu'on construit, et les protocoles possibles

```
  aiml-gemini-ent-exp-0zga (433175138344) : LES AGENTS        acme-gemini-prod (523307489860) : L'APP
 ┌───────────────────────────────────────────────────┐       ┌──────────────────────────────────────────────┐
 │ Agent Runtime : météo, rédaction, traduction      │◀──────│ App Gemini Enterprise dev_gemini-entreprise- │
 │ Cloud Run (A2A) : les mêmes, en protocole A2A     │ appel │ app (eu)                                     │
 │ Agent Registry : les agents (catalogue)           │       │                                              │
 │ Model Armor : filtre questions et réponses        │       │ Compte de service de Gemini Enterprise :     │
 │ Un compte de service par agent                    │       │ service-100000000003@gcp-sa-discoveryengine… │
 │ IAM : UN droit donné au compte de l'app ──────────┼──────▶│                                              │
 └───────────────────────────────────────────────────┘       └──────────────────────────────────────────────┘
```

**Quels protocoles pour un agent d'un AUTRE projet que l'app ?**

| Façon d'ajouter dans l'app | Fonctionne depuis `aiml-gemini-ent-exp-0zga` ? | Droit à donner dans le projet des agents |
|---|---|---|
| **Agent Runtime** (« Vertex AI Agent Engine », l'hébergement géré de Google) | **Oui** | `roles/discoveryengine.serviceAgent` sur le **projet** |
| **A2A** (agent hébergé sur **Cloud Run**, protocole ouvert A2A v0.3) | **Oui** | `roles/run.invoker` sur **chaque service** |
| **Agent Registry** (import depuis le catalogue) | **Non** : l'app n'importe que depuis le registre de **son** projet → [12-2](12-2-agents-dans-projet-app.md) | — |
| **Dialogflow** | Non documenté par Google → [12-2](12-2-agents-dans-projet-app.md) | — |

« Vertex AI » n'est pas un mode à part : **Agent Runtime fait partie de Vertex AI** (Agent Platform). Le registre sert
quand même ici : les agents s'y inscrivent, d'autres équipes et agents les y trouvent.

---

## 1. Préparation commune (une fois)

### 1.1 Les outils sur votre poste

| Outil | Mac (Homebrew) | Vérifier |
|---|---|---|
| gcloud | `brew install --cask google-cloud-sdk` puis `gcloud components install beta` | `gcloud version` |
| Terraform 1.9+ (méthode B) | `brew tap hashicorp/tap && brew install hashicorp/tap/terraform` | `terraform version` |
| uv (Python 3.12 à 3.14) | `brew install uv` | `uv --version` |

**Pas de Docker** : les images Cloud Run sont construites **dans Google Cloud** (Cloud Build), avec gcloud seulement. Un
terminal Linux ou Mac, ou Cloud Shell, suffit.

### 1.2 Le dossier et l'environnement Python

Le dossier `09-agents-multi-projets-gemini-enterprise` est sur votre Bureau.

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/trio/requirements.txt
python scripts/test_trio.py
```

**Résultat obtenu :** `tests trio OK (9 scénarios, 6 agents)`. Votre invite affiche `(.venv)`.

### 1.3 Le fichier de configuration (le seul fichier à modifier)

Ouvrez `config/12-1-agents-dans-projet-exp.env` dans un éditeur. Il est déjà rempli avec vos projets :

```bash
PROJET_APP=acme-gemini-prod
NUM_APP=523307489860
APP_ID=dev_gemini-entreprise-app        # Gemini Enterprise > l'app > Présentation : ID de l'app
GE_LOCATION=eu
PROJET_AGENTS=aiml-gemini-ent-exp-0zga
NUM_AGENTS=433175138344
REGION=europe-west1
AGENTS=""                               # vide = tous les agents du catalogue ; ex. "meteo taille"
PUBLIER=non
AGENTS_OAUTH=""
GROUPE_UTILISATEURS=equipe-agents@acme.example
DOSSIER=~/Desktop/09-agents-multi-projets-gemini-enterprise
```

**À vérifier :** `APP_ID` est bien l'**ID** de l'app (console → 🔎 « Gemini Enterprise » → l'app → **Présentation**),
pas son nom affiché ; `GROUPE_UTILISATEURS` est le groupe Google qui testera.

**Charger la configuration** (à refaire dans **chaque nouveau terminal**, toujours seule sur sa ligne) :

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise && source .venv/bin/activate
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
```

**Résultat obtenu :**

```
== Configuration chargée : config/12-1-agents-dans-projet-exp.env
   App Gemini Enterprise : dev_gemini-entreprise-app   (projet acme-gemini-prod, numéro 523307489860, eu)
   Projet des agents     : aiml-gemini-ent-exp-0zga (numéro 433175138344), région europe-west1   [même projet que l'app : non]
   Compte de l'app       : service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
   Terraform             : espace « scenario-12-1 », publication dans l'app : non
   Dossier               : /Users/<vous>/Desktop/09-agents-multi-projets-gemini-enterprise
   OK
```

Le script donne aussi ces valeurs à gcloud (projet par défaut, point d'accès européen de Model Armor) et à Terraform.
**Ne le mettez jamais derrière un `|`** (par exemple `| grep`) : les valeurs ne resteraient pas dans le terminal.

### 1.4 Se connecter, vérifier les numéros

```bash
gcloud auth login
gcloud auth application-default login
gcloud projects describe $PROJET_APP --format='value(projectNumber)'
gcloud projects describe $PROJET_AGENTS --format='value(projectNumber)'
```

**Résultat attendu :** `523307489860` puis `433175138344`. S'ils diffèrent, corrigez le fichier de configuration et
rechargez-le.

### 1.5 Vos droits

```bash
for P in $PROJET_AGENTS $PROJET_APP; do echo "== $P"
  gcloud projects get-iam-policy $P --flatten=bindings \
    --filter="bindings.members:user:$(gcloud config get-value account 2>/dev/null)" --format="value(bindings.role)"; done
```

| Projet | Rôles nécessaires (ou `roles/owner`) |
|---|---|
| `aiml-gemini-ent-exp-0zga` | `aiplatform.admin`, `iam.serviceAccountAdmin`, `iam.serviceAccountUser`, `resourcemanager.projectIamAdmin`, `serviceusage.serviceUsageAdmin`, `modelarmor.admin`, `agentregistry.admin`, `run.admin`, `artifactregistry.admin`, `cloudbuild.builds.editor`, `storage.admin` (les deux derniers : construction des images Cloud Run par Cloud Build ; gcloud crée le bucket `gs://aiml-gemini-ent-exp-0zga_cloudbuild` à la 1re construction) |
| `acme-gemini-prod` | `discoveryengine.admin` (Gemini Enterprise Admin) |

Un rôle donné via un **groupe** n'apparaît pas dans cette commande : vérifiez alors dans la console (IAM du projet).

### 1.6 Les API : vérifier, activer seulement celles qui manquent

```bash
./scripts/verifier_api.sh $PROJET_AGENTS cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com \
  aiplatform.googleapis.com agentregistry.googleapis.com modelarmor.googleapis.com logging.googleapis.com \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
./scripts/verifier_api.sh $PROJET_APP cloudresourcemanager.googleapis.com serviceusage.googleapis.com discoveryengine.googleapis.com
```

**Résultat obtenu :**

```
OK        cloudresourcemanager.googleapis.com
OK        serviceusage.googleapis.com
…
OK        artifactregistry.googleapis.com
OK        cloudbuild.googleapis.com
rien à activer
```

S'il en manquait : `MANQUANTE …` puis `activées : …`. Cloud Build tout juste activé : la 1re construction d'image peut
répondre `PERMISSION_DENIED` ; attendez une minute et relancez.

### 1.7 Le compte de service de l'app

C'est **lui** qui appellera vos agents. Il existe déjà (l'app existe) ; on vérifie son adresse :

```bash
gcloud beta services identity create --service=discoveryengine.googleapis.com --project=$PROJET_APP
```

**Résultat obtenu :** `Service identity created: service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`
(le message dit « created » même s'il existait : rien ne change). Il doit être identique à `echo $GE_SA`.

---

## Méthode A : shell (gcloud + scripts)

Chaque ressource est créée par une commande que vous voyez. Noms : suffixe `-shell`.

### A1. Les templates Model Armor (filtre des questions et réponses)

Gemini Enterprise **ne filtre pas** les agents ajoutés : chaque agent filtre lui-même. Deux templates : questions, réponses.

```bash
for T in prompt response; do
gcloud model-armor templates create agents-$T-shield --location=$GE_LOCATION --project=$PROJET_AGENTS \
  --pi-and-jailbreak-filter-settings-enforcement=enabled --pi-and-jailbreak-filter-settings-confidence-level=medium-and-above \
  --malicious-uri-filter-settings-enforcement=enabled --basic-config-filter-enforcement=enabled \
  --rai-settings-filters='[{"filterType":"HATE_SPEECH","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"HARASSMENT","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"SEXUALLY_EXPLICIT","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"DANGEROUS","confidenceLevel":"MEDIUM_AND_ABOVE"}]' \
  --template-metadata-log-operations
done
gcloud model-armor templates list --location=$GE_LOCATION --project=$PROJET_AGENTS --format="value(name)"
```

**Résultat obtenu :**

```
Created template [agents-prompt-shield].
Created template [agents-response-shield].
projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/agents-prompt-shield
projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/agents-response-shield
```

Leurs chemins sont déjà dans `$PROMPT_TEMPLATE` et `$RESPONSE_TEMPLATE` (définis par `scripts/config.sh`). Templates
**centraux** de la sécurité : sautez la création et ajoutez `PROMPT_TEMPLATE=…` et `RESPONSE_TEMPLATE=…` au fichier de configuration.

### A2. Agent Runtime : comptes de service, déploiement, test

**Un compte de service par agent**, avec 3 rôles : appeler Gemini (`aiplatform.user`), écrire ses journaux
(`logging.logWriter`), utiliser Model Armor (`modelarmor.user`).

```bash
for K in meteo redaction traduction; do
  gcloud iam service-accounts create $K-shell-sa --project=$PROJET_AGENTS --display-name="Agent $K (Agent Runtime, méthode shell)"
  for R in aiplatform.user logging.logWriter modelarmor.user; do
    gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
      --member=serviceAccount:$K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null && echo "  $K-shell-sa : roles/$R"
  done
done
```

**Résultat obtenu :** pour chaque agent, `Created service account [meteo-shell-sa].` puis ses 3 rôles.

**Déployer les 3 agents** (le script empaquette le code de `agents/trio` et appelle l'API Agent Runtime ; 3 à 5 minutes par agent) :

```bash
for K in meteo redaction traduction; do
  DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
  python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent --nom $K-shell \
    --description "$DESC" --compte-service $K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE
done
```

**Résultat obtenu :**

```
opération : projects/100000000002/locations/europe-west1/reasoningEngines/255731011457908736/operations/2062430170119143424
  en cours… 0 s
  …
déployé : projects/100000000002/locations/europe-west1/reasoningEngines/255731011457908736
…
déployé : projects/100000000002/locations/europe-west1/reasoningEngines/7607857403140243456
…
déployé : projects/100000000002/locations/europe-west1/reasoningEngines/3342948556020383744
```

Notez les 3 noms `projects/…/reasoningEngines/…` (dans l'ordre : météo, rédaction, traduction). Les retrouver plus tard :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
  | python3 -c 'import json,sys; [print(e["displayName"], e["name"]) for e in json.load(sys.stdin).get("reasoningEngines",[])]'
```

**Attendre 5 minutes** (les droits des nouveaux comptes s'appliquent), puis **tester chaque agent seul** :

```bash
AGENT_NAME=projects/$NUM_AGENTS/locations/$REGION/reasoningEngines/ID_TRADUCTION \
  python scripts/query.py - "Traduis en espagnol : Votre tente Quechua est disponible en retrait en magasin."
```

**Résultat obtenu :**

```
  -> outil : glossaire({'langue_cible': 'es'})
  -> outil : verifier_traduction({'traduction': 'Su tienda de campaña Quechua está disponible para recogida en tienda.', …})
agent : Su tienda de campaña Quechua está disponible para recogida en tienda.

Contrôle : conforme
```

Et pour la météo (`ID_METEO`, « Je cours à Lille demain matin, quoi porter ? ») :

```
  -> outil : meteo({'ville': 'Lille', 'jours': 2})
  -> outil : conseil_equipement({'activite': 'course à pied', 'pluie_mm': 6.1, 'temperature_c': 9, 'vent_kmh': 24.5})
agent : **Météo à Lille demain :** Pluie faible prévue avec des températures fraîches (environ 9°C le matin) …
```

**Dans la console :** 🔎 « Agent Runtime » → **Déploiements** → `traduction-shell` → onglet **Playground** : même test à
la souris.

### A3. Cloud Run (A2A) : image, comptes de service, services, test

**Pas besoin de Docker** : les images sont construites **dans Google Cloud** par Cloud Build. Il faut d'abord (une fois)
un dépôt d'images et un compte de service qui construit les images (le compte par défaut de Cloud Build n'a souvent aucun
droit : `… -compute@developer.gserviceaccount.com does not have storage.objects.get access …`).

```bash
gcloud artifacts repositories create agents-shell --repository-format=docker --location=$REGION --project=$PROJET_AGENTS
gcloud iam service-accounts create agents-build-sa --project=$PROJET_AGENTS --display-name="Construction des images des agents (Cloud Build)"
for R in storage.objectViewer artifactregistry.writer logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
    --member=serviceAccount:agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null && echo "  agents-build-sa : roles/$R"
done
```

**Résultat attendu :** `Created repository [agents-shell].`, `Created service account [agents-build-sa].`, puis les
3 lignes `agents-build-sa : roles/…`. **Attendez 1 à 2 minutes** (les nouveaux droits mettent ce temps à s'appliquer).

**Les images, une par agent** (depuis le dossier du projet ; ~1 min 20 s par image) :

```bash
for K in meteo redaction traduction; do
  gcloud builds submit --region=$REGION --project=$PROJET_AGENTS \
    --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --config=01-bis-cloud-run-a2a/cloudbuild.yaml \
    --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K:v1 .
done
```

**Résultat obtenu (pour chaque agent) :**

```
Creating temporary archive of 20 file(s) totalling 61.4 KiB before compression.
Uploading tarball of [.] to [gs://aiml-gemini-ent-exp-0zga_cloudbuild/source/….tgz]
Created [https://cloudbuild.googleapis.com/v1/projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/builds/…].
…
ID  CREATE_TIME  DURATION  SOURCE  IMAGES                                                                 STATUS
…   …            …         gs://…  europe-west1-docker.pkg.dev/aiml-gemini-ent-exp-0zga/agents-shell/meteo:v1  SUCCESS
```

**À vérifier :** `SUCCESS` en fin de ligne. Seul le code des agents est envoyé (20 fichiers, filtrés par `.gcloudignore`).
`PERMISSION_DENIED` juste après la création du compte : attendez 1 à 2 minutes et relancez. **Dans la console :**
🔎 « Cloud Build » → **Historique** (région `europe-west1`) : chaque construction et son journal. Le détail commande par
commande : [12-1-1, partie 7](12-1-1-deployer-agents-shell.md#7-cloud-run-a2a--un-agent-puis-plusieurs).

**Les 3 services privés.** Pour chacun : un compte de service et ses rôles, la carte A2A et les variables
d'environnement (générées depuis `agents/trio/catalogue.json`), puis le déploiement.

```bash
for K in meteo redaction traduction; do
  gcloud iam service-accounts create $K-a2a-shell-sa --project=$PROJET_AGENTS --display-name="Agent $K (Cloud Run A2A, méthode shell)"
  for R in aiplatform.user logging.logWriter modelarmor.user; do
    gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
      --member=serviceAccount:$K-a2a-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null && echo "  $K-a2a-shell-sa : roles/$R"
  done
  URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app          # adresse connue d'avance : elle va dans la carte
  python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml
  gcloud run deploy $K-a2a-shell --image=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K:v1 --region=$REGION --project=$PROJET_AGENTS \
    --service-account=$K-a2a-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com --no-allow-unauthenticated \
    --env-vars-file=env-$K.yaml --memory=1Gi --cpu=1 --min-instances=0 --max-instances=1 --quiet
done
```

**Résultat obtenu (pour chaque agent) :**

```
Service account email: meteo-a2a-shell-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com
  meteo-a2a-shell-sa : roles/aiplatform.user
  meteo-a2a-shell-sa : roles/logging.logWriter
  meteo-a2a-shell-sa : roles/modelarmor.user
Service URL: https://meteo-a2a-shell-433175138344.europe-west1.run.app
```

**À vérifier :** `Service URL` est **exactement** l'adresse mise dans la carte (`$URL`). `--no-allow-unauthenticated` :
le service est privé (403 sans jeton).

| Variable du service (fichier `env-meteo.yaml`) | Rôle |
|---|---|
| `AGENT` | Quel agent ce service sert (`meteo_agent`) |
| `AGENT_CARD` | La carte A2A v0.3, servie sur `/.well-known/agent-card.json` |
| `GOOGLE_CLOUD_PROJECT`, `MODEL` | Projet et modèle Gemini (Vertex AI) |
| `PROMPT_TEMPLATE`, `RESPONSE_TEMPLATE` | Les templates Model Armor de A1 |

**Attendre 3 à 5 minutes**, puis tester un agent avec le protocole de Gemini Enterprise :

```bash
URL=https://traduction-a2a-shell-$NUM_AGENTS.$REGION.run.app ./01-bis-cloud-run-a2a/test.sh traduction
```

**Résultat obtenu :**

```
== traduction  carte : traduction_agent (A2A 0.3)
   Q1 > Traduis en espagnol : 'Votre tente Quechua est disponible en retrait en magasin.'
   R1 < Su tienda Quechua está disponible para recogida en tienda.  Contrôle : conforme
   Q2 > Et en italien ?
   R2 < La tua tenda Quechua è disponibile per il ritiro in negozio.  Contrôle : conforme
OK : les agents répondent en A2A v0.3, avec mémoire de conversation
```

### A4. Agent Registry (le catalogue du projet des agents)

Les agents Agent Runtime s'y sont **inscrits seuls**. Les agents Cloud Run, on les **déclare** avec leur carte :

```bash
for K in meteo redaction traduction; do
  python3 scripts/carte_a2a.py $K https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app > carte-$K.json
  NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
  gcloud agent-registry services create $K-a2a-shell --location=$REGION --project=$PROJET_AGENTS \
    --display-name="$NOM" --description="$(python3 -c "import json; print(json.load(open('carte-$K.json'))['description'])")" \
    --agent-spec-type=A2A_AGENT_CARD --agent-spec-content="$(cat carte-$K.json)"
done
gcloud agent-registry agents list --location=$REGION --project=$PROJET_AGENTS --format="table(displayName,agentId)"
```

**Résultat obtenu :**

```
Created service [meteo-a2a-shell].
Created service [redaction-a2a-shell].
Created service [traduction-a2a-shell].
DISPLAY_NAME      AGENT_ID
meteo_agent       urn:agent:projects-433175138344:…:agentregistry:services:meteo-a2a-shell
redaction_agent   urn:agent:projects-433175138344:…:agentregistry:services:redaction-a2a-shell
traduction_agent  urn:agent:projects-433175138344:…:agentregistry:services:traduction-a2a-shell
meteo-shell       urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:255731011457908736
traduction-shell  urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:3342948556020383744
redaction-shell   urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:7607857403140243456
```

Pas de `--interfaces` avec une carte A2A : l'API le refuse (l'adresse est dans la carte).

### A5. Donner à l'app le droit d'appeler les agents

```bash
# Agent Runtime : un droit sur le PROJET des agents
gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA
# Cloud Run : un droit sur CHAQUE service
for K in meteo redaction traduction; do
  gcloud run services add-iam-policy-binding $K-a2a-shell --region=$REGION --project=$PROJET_AGENTS \
    --role=roles/run.invoker --member=serviceAccount:$GE_SA
done
# Vérifier
gcloud projects get-iam-policy $PROJET_AGENTS --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
for K in meteo redaction traduction; do echo "$K-a2a-shell : $(gcloud run services get-iam-policy $K-a2a-shell --region=$REGION \
  --project=$PROJET_AGENTS --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)")"; done
```

**Résultat obtenu (vérification) :**

```
roles/discoveryengine.serviceAgent
meteo-a2a-shell : roles/run.invoker
redaction-a2a-shell : roles/run.invoker
traduction-a2a-shell : roles/run.invoker
```

### A6. Ajouter les agents dans l'app, donner l'accès, tester dans le chat

**Agent Runtime** (avec les 3 noms de ressource de A2) :

```bash
for K in meteo redaction traduction; do
  RES=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
    | python3 -c "import json,sys; print(next(e['name'] for e in json.load(sys.stdin)['reasoningEngines'] if e['displayName']=='$K-shell'))")
  NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
  DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
  ./scripts/add_agent_to_ge.sh adk "$RES" "$NOM (shell)" "$DESC"
done
```

**A2A** (avec les cartes de A4) :

```bash
for K in meteo redaction traduction; do
  NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
  ./scripts/add_agent_to_ge.sh a2a carte-$K.json "$NOM (A2A shell)"
done
./scripts/add_agent_to_ge.sh list
```

**Résultat attendu :** pour chaque agent `ajouté : projects/…/engines/dev_gemini-entreprise-app/assistants/default_assistant/agents/<ID>`
(Agent Runtime : avant, `droit accordé : …`, le droit existant déjà). `list` montre 6 agents, `adkAgentDefinition` et
`a2aAgentDefinition`.

**Donner l'accès** (console, pour chaque agent) : 🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` → **Agents** →
l'agent → onglet **Autorisations utilisateur** → **Ajouter** → `equipe-agents@acme.example` (votre
`GROUPE_UTILISATEURS`) → rôle **Agent User** → **Enregistrer**. Les membres doivent avoir une **licence** Gemini Enterprise.

**Tester dans le chat :** app → **Intégration** → lien de l'app web, avec un compte du groupe → **Agents** →
« Traduction Acme (shell) » → « Traduis en allemand : retour gratuit sur les chaussures Kiprun ».

**Résultat attendu :** « Kostenlose Rücksendung … Kiprun … — Contrôle : conforme ». Première réponse : 20 à 40 s.
Les sessions apparaissent dans **aiml-gemini-ent-exp-0zga** (Agent Runtime → l'agent → **Sessions**).

### A7. Nettoyer la méthode A

```bash
for K in meteo redaction traduction; do ./scripts/add_agent_to_ge.sh delete "$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])") (shell)"; done
for K in meteo redaction traduction; do ./scripts/add_agent_to_ge.sh delete "$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])") (A2A shell)"; done
for R in $(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
  | python3 -c 'import json,sys; [print(e["name"]) for e in json.load(sys.stdin).get("reasoningEngines",[]) if e["displayName"].endswith("-shell")]'); do
  python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --supprimer $R
done
for K in meteo redaction traduction; do
  gcloud run services delete $K-a2a-shell --region=$REGION --project=$PROJET_AGENTS --quiet
  gcloud agent-registry services delete $K-a2a-shell --location=$REGION --project=$PROJET_AGENTS --quiet
  for SA in $K-shell-sa $K-a2a-shell-sa; do
    for R in aiplatform.user logging.logWriter modelarmor.user; do
      gcloud projects remove-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
        --member=serviceAccount:$SA@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null 2>&1
    done
    gcloud iam service-accounts delete $SA@$PROJET_AGENTS.iam.gserviceaccount.com --project=$PROJET_AGENTS --quiet
  done
done
gcloud projects remove-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/discoveryengine.serviceAgent \
  --member=serviceAccount:$GE_SA >/dev/null && echo "droit de l'app retiré"
for T in agents-prompt-shield agents-response-shield; do gcloud model-armor templates delete $T --location=$GE_LOCATION --project=$PROJET_AGENTS --quiet; done
gcloud artifacts repositories delete agents-shell --location=$REGION --project=$PROJET_AGENTS --quiet
for R in storage.objectViewer artifactregistry.writer logging.logWriter; do   # le compte de construction (gardez-le si vous faites la méthode C)
  gcloud projects remove-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
    --member=serviceAccount:agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null 2>&1
done
gcloud iam service-accounts delete agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com --project=$PROJET_AGENTS --quiet
rm -f env-*.yaml carte-*.json
```

**Résultat obtenu :** `supprimé : projects/…/reasoningEngines/…` ×3, `Deleted service […]` (Cloud Run puis registre),
`deleted service account […]` ×6, `droit de l'app retiré`, `Deleted template […]` ×2, `Deleted repository [agents-shell].`,
`deleted service account [agents-build-sa@…]`. Le bucket `gs://…_cloudbuild` (créé par Google, le code envoyé aux
constructions) reste ; à la main : `gcloud storage rm -r gs://${PROJET_AGENTS}_cloudbuild`. Inventaire de ce qui reste :
`python scripts/nettoyer.py` (et `--supprimer` pour tout retirer).

> Ne retirez le droit `discoveryengine.serviceAgent` que si **aucun autre** agent Agent Runtime de ce projet n'est utilisé
> par l'app (le droit vaut pour tout le projet).

---

## Méthode B : Terraform

Terraform crée **tout** (comptes de service, droits, templates Model Armor, agents, registre, droit de l'app) à partir du
fichier de configuration. Il s'exécute **sur votre poste** : l'état (`terraform.tfstate`) est gardé dans
`terraform.tfstate.d/scenario-12-1/` du dossier Terraform ; ne le supprimez pas, sauvegardez-le.

### B1. Agent Runtime (dossier 02-bis)

```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
cd 02-bis-agent-runtime/terraform
terraform init
terraform plan
```

**Résultat obtenu (fin du plan) :** `Plan: 49 to add, 0 to change, 0 to destroy.` — dont 6
`google_vertex_ai_reasoning_engine` (les agents du catalogue : météo, rédaction, traduction, taille, retour, identite),
6 `google_service_account` (leurs identités) et
`google_project_iam_member.ge_uses_agents_project[0]` (le droit de l'app sur ce projet).

```bash
terraform apply       # taper yes ; 10 à 15 minutes
```

**Résultat obtenu :**

```
Apply complete! Resources: 49 added, 0 changed, 0 destroyed.

Outputs:

agents = {
  "identite" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/…"
  "meteo" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/5587992970264576000"
  "redaction" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/1022468848017735680"
  "retour" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/…"
  "taille" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/…"
  "traduction" = "projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines/976306951837188096"
}
ge_agents_page = "(ge_app_id vide : agents non publiés)"
ge_service_agent = "serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com"
```

`Error code 13` sur un agent ? Erreur interne de Google : **relancez `terraform apply`**, seul l'agent manquant est recréé.

**Attendre 5 minutes**, puis tester les 6 agents seuls (`./test.sh taille` : un seul) :

```bash
cd .. && ./test.sh
```

**Résultat obtenu :** pour chaque agent, les outils appelés puis la réponse (comme en A2).

### B2. Cloud Run A2A (dossier 01-bis)

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
terraform init
terraform plan        # « Plan: 63 to add » : par agent (×6) une image, un service, une identité, un droit run.invoker pour l'app, une entrée de registre…
terraform apply       # yes ; ~10 min (Cloud Build construit les images dans Google Cloud : pas de Docker)
```

**Résultat obtenu :** `Apply complete! Resources: 63 added`, puis `cards` (les cartes A2A) et `urls`.
Le plan compte 23 ressources pour un agent, +8 par agent en plus (63 pour 6). Il contient aussi le compte qui construit
les images, `google_service_account.build` (`agents-a2a-build-sa`), ses 3 rôles `google_project_iam_member.build["roles/…"]`
et l'API `google_project_service.agents["cloudbuild.googleapis.com"]`. Chaque image est construite par `gcloud builds submit`
(~1 min 20 s ; Terraform réessaie jusqu'à 4 fois si les droits tout neufs ne sont pas encore actifs). **Dans la console :**
🔎 « Cloud Build » → **Historique** (région `europe-west1`).
**Attendre 5 minutes**, puis :

```bash
cd .. && ./test.sh
```

**Résultat obtenu :** pour chaque agent `carte : … (A2A 0.3)`, deux réponses dans la même conversation, puis `OK : …`.

### B3. Agent Registry

```bash
gcloud agent-registry agents list --location=$REGION --project=$PROJET_AGENTS --format="table(displayName,agentId)"
```

**Résultat attendu :** `meteo-agent`, `redaction-agent`, `traduction-agent` (Agent Runtime, inscrits seuls) et
`meteo_agent`, `redaction_agent`, `traduction_agent` (cartes A2A déclarées par Terraform), et de même pour `taille`, `retour` et `identite`.

### B4. Le droit de l'app (déjà posé par Terraform)

```bash
gcloud projects get-iam-policy $PROJET_AGENTS --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
```

**Résultat obtenu :** `roles/discoveryengine.serviceAgent` (et `roles/run.invoker` sur chaque service `*-a2a`).

### B5. Publier dans l'app, donner l'accès, tester dans le chat

Dans `config/12-1-agents-dans-projet-exp.env`, passez `PUBLIER=non` à **`PUBLIER=oui`**, puis :

```bash
cd $DOSSIER && source scripts/config.sh config/12-1-agents-dans-projet-exp.env     # « publication dans l'app : oui »
cd 02-bis-agent-runtime/terraform && terraform plan
```

**Résultat obtenu (plan) :** `google_project_service.ge[0]` et `terraform_data.publish["meteo"]`, `["redaction"]`,
`["traduction"]`, … (un par agent, 6) à créer.

```bash
terraform apply
cd ../../01-bis-cloud-run-a2a/terraform && terraform apply
```

**Résultat attendu :** `registered Météo & équipement` (×6 noms), `Apply complete! Resources: 7 added` pour chaque dossier
(l'API Discovery Engine + 6 publications)
(les agents A2A apparaissent avec « (A2A) » dans leur nom). `terraform output ge_agents_page` donne le lien de la page
Agents de l'app.

Puis **donner l'accès** et **tester dans le chat** exactement comme en [A6](#a6-ajouter-les-agents-dans-lapp-donner-laccès-tester-dans-le-chat).

### B6. Nettoyer la méthode B

```bash
cd $DOSSIER && source scripts/config.sh config/12-1-agents-dans-projet-exp.env
terraform -chdir=01-bis-cloud-run-a2a/terraform destroy     # yes -> retire aussi les agents de l'app
terraform -chdir=02-bis-agent-runtime/terraform destroy     # yes
```

**Résultat attendu :** `Destroy complete! Resources: 70 destroyed.` et `Resources: 56 destroyed.` (avec la publication),
ou 63 et 49 sans.

---

## Méthode C : console (interface)

Tout à la souris, sauf **deux commandes** inévitables, lancées depuis **Cloud Shell** (icône `>_` de la console) : la
console n'a pas de formulaire pour envoyer du **code** à Agent Runtime, ni pour **construire une image** à partir du
dossier (on la fait construire par Cloud Build, sans Docker). Noms :
suffixe `-console`. Projet sélectionné en haut de la console : **aiml-gemini-ent-exp-0zga**, sauf mention contraire.

### C1. Les templates Model Armor

🔎 « Model Armor » → **Templates** → **Créer un template** :

| Champ | Valeur |
|---|---|
| ID du template | `console-prompt-shield` (puis un second : `console-response-shield`) |
| Région | **Multirégion** → `eu` |
| Détection des URL malveillantes | Activée |
| Injection de prompt et jailbreak | Activée, confiance **Moyenne et supérieure** |
| Protection des données sensibles | **De base**, activée |
| IA responsable | Incitation à la haine, Harcèlement, Contenu sexuel explicite, Contenu dangereux : **Moyenne et supérieure** |

**Créer**, deux fois. **Attendu :** les deux templates dans la liste, région `eu`.

### C2. Les comptes de service des agents

🔎 « Comptes de service » (IAM et administration) → **Créer un compte de service**, 6 fois :
`meteo-console-sa`, `redaction-console-sa`, `traduction-console-sa` (Agent Runtime) et `meteo-a2a-console-sa`,
`redaction-a2a-console-sa`, `traduction-a2a-console-sa` (Cloud Run).

Pour chacun : **Nom** → **Créer et continuer** → **Attribuer des rôles** : *Utilisateur Vertex AI* (Agent Platform User),
*Rédacteur de journaux* (Logs Writer), *Utilisateur Model Armor* → **OK**.

**Attendu :** les 6 comptes dans la liste ; IAM du projet : chacun avec ses 3 rôles.

### C3. Agent Runtime : déployer (1 commande), tester (console)

Cloud Shell (icône `>_`), après avoir importé le dossier (menu à trois points → **Importer**) et chargé la configuration
(partie 1.3, avec `DOSSIER=~/09-agents-multi-projets-gemini-enterprise` dans le fichier si vous êtes dans Cloud Shell) :

```bash
for K in meteo redaction traduction; do
  python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --agent ${K}_agent --nom $K-console \
    --compte-service $K-console-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --env PROMPT_TEMPLATE=projects/$PROJET_AGENTS/locations/eu/templates/console-prompt-shield \
    --env RESPONSE_TEMPLATE=projects/$PROJET_AGENTS/locations/eu/templates/console-response-shield
done
```

**Attendu :** `déployé : projects/…/reasoningEngines/…` ×3 (comme en A2).

**Tester (console) :** 🔎 « Agent Runtime » → **Déploiements** → `traduction-console` → **Playground** → « Traduis en
espagnol : Votre tente Quechua est disponible en retrait en magasin. » **Attendu :** « … recogida en tienda —
Contrôle : conforme ». Onglet **Sessions** : la conversation. Copiez le **nom de la ressource** affiché sur la page de
l'agent (`projects/…/reasoningEngines/…`).

### C4. Cloud Run A2A : image (1 commande), services (console), test

**Les images**, dans Cloud Shell, depuis le dossier du projet (`cd $DOSSIER`). Le compte de construction
`agents-build-sa` : déjà créé si vous avez fait la méthode A (`ALREADY_EXISTS` : rien à faire) ; sinon les 2 premières
commandes le créent, puis **attendez 1 à 2 minutes**.

```bash
gcloud iam service-accounts create agents-build-sa --project=$PROJET_AGENTS --display-name="Construction des images des agents (Cloud Build)"
for R in storage.objectViewer artifactregistry.writer logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
    --member=serviceAccount:agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null && echo "  agents-build-sa : roles/$R"
done
gcloud artifacts repositories create agents-console --repository-format=docker --location=$REGION --project=$PROJET_AGENTS
for K in meteo redaction traduction; do
  gcloud builds submit --region=$REGION --project=$PROJET_AGENTS \
    --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --config=01-bis-cloud-run-a2a/cloudbuild.yaml \
    --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-console/$K:v1 .
done
for K in meteo redaction traduction; do python3 scripts/carte_a2a.py $K https://$K-a2a-console-$NUM_AGENTS.$REGION.run.app; echo; done
```

**Attendu :** pour chaque agent, une ligne qui finit par `…/agents-console/meteo:v1  SUCCESS` (~1 min 20 s par image).
Les constructions et leurs journaux : 🔎 « Cloud Build » → **Historique** (région `europe-west1`).
La dernière commande affiche les **3 cartes** : gardez-les (copier-coller) pour les étapes suivantes.

**Les services** : 🔎 « Cloud Run » → **Déployer un conteneur** (ou **Créer un service**), 3 fois :

| Champ | Valeur (exemple : météo) |
|---|---|
| URL de l'image du conteneur | **Sélectionner** → `agents-console` → `meteo` → `v1` (l'image de **cet** agent) |
| Nom du service | `meteo-a2a-console` |
| Région | `europe-west1` |
| Authentification | **Exiger l'authentification** |
| Conteneur → Variables et secrets | `AGENT` = `meteo_agent` ; `AGENT_CARD` = la carte affichée ci-dessus (tout le JSON) ; `GOOGLE_CLOUD_PROJECT` = `aiml-gemini-ent-exp-0zga` ; `MODEL` = `gemini-3.5-flash` ; `PROMPT_TEMPLATE` = `projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/console-prompt-shield` ; `RESPONSE_TEMPLATE` = `…/console-response-shield` |
| Conteneur → Ressources | Mémoire 1 Gio, 1 processeur |
| Sécurité → Compte de service | `meteo-a2a-console-sa` |
| Scaling | Minimum 0, **maximum 1** |

**Créer.** **Attendu :** coche verte, et l'URL `https://meteo-a2a-console-433175138344.europe-west1.run.app` parmi les
URL du service (c'est celle de la carte).

**Tester** (Cloud Shell, 3 à 5 minutes après) :
`URL=https://traduction-a2a-console-$NUM_AGENTS.$REGION.run.app ./01-bis-cloud-run-a2a/test.sh traduction` →
**Attendu :** `OK : les agents répondent en A2A v0.3, avec mémoire de conversation`.

### C5. Agent Registry

Les agents Agent Runtime y sont déjà. Pour les agents Cloud Run : 🔎 « Agent Registry » → région `europe-west1` →
**Enregistrer** → type **Agent** → **Nom** (`meteo-a2a-console`), **Nom à afficher**, **Description**, spécification
**Carte d'agent A2A** : coller la carte → **Enregistrer**. **Attendu :** les 6 agents dans la liste.

### C6. Donner à l'app le droit d'appeler les agents

1. **Agent Runtime, sur le projet :** 🔎 « IAM » → **Accorder l'accès** → *Nouveaux comptes principaux* :
   `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` → rôle **Agent de service Discovery Engine**
   (*Discovery Engine Service Agent*) → **Enregistrer**.
   Si la console refuse ce rôle d'« agent de service », passez la commande de [A5](#a5-donner-à-lapp-le-droit-dappeler-les-agents) (première ligne) dans Cloud Shell.
2. **Cloud Run, sur chaque service :** 🔎 « Cloud Run » → `meteo-a2a-console` → onglet **Sécurité** (ou **Autorisations**)
   → **Ajouter un compte principal** → le même compte → rôle **Demandeur Cloud Run** (*Cloud Run Invoker*) →
   **Enregistrer**. Idem pour les deux autres services.

**Attendu :** IAM du projet (case *Inclure les attributions de rôles fournies par Google* cochée) : le compte avec
*Discovery Engine Service Agent* ; chaque service : le compte avec *Cloud Run Invoker*.

### C7. Ajouter dans l'app, donner l'accès, tester dans le chat

Sélectionnez le projet **acme-gemini-prod** → 🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` →
**Agents** → **+ Ajouter un agent** :

- **Agent personnalisé via Agent Runtime** → **Ajouter** → **Nom de l'agent** (`Traduction Acme (console)`),
  **Décrivez votre agent** (la description de `agents/trio/catalogue.json`), **Chemin de ressource Agent Runtime**
  (copié en C3) → **Créer**. Idem pour météo et rédaction.
- **Agent personnalisé via A2A** → **Ajouter** → coller **la carte** (JSON) → **Prévisualiser les détails de l'agent**
  (nom, description, compétences) → **Suivant** → *Authentification* : **ignorer** → **Terminer**. Idem pour les deux autres.

Puis, pour chaque agent : **Autorisations utilisateur** → **Ajouter** → le groupe → **Agent User** → **Enregistrer**, et
le **test dans le chat** de [A6](#a6-ajouter-les-agents-dans-lapp-donner-laccès-tester-dans-le-chat).

### C8. Nettoyer la méthode C

Dans l'app : chaque agent « (console) » → **Supprimer**. Projet des agents : Agent Runtime → chaque agent `-console` →
**Supprimer** ; Cloud Run → chaque service `-console` → **Supprimer** ; Agent Registry → les 3 entrées → **Supprimer** ;
Comptes de service → les 6 `-console-sa` → **Supprimer** ; Model Armor → les 2 templates `console-*` → **Supprimer** ;
Artifact Registry → `agents-console` → **Supprimer** ; Comptes de service → `agents-build-sa` → **Supprimer**
(si la méthode A ne s'en sert plus). IAM : retirer le rôle *Discovery Engine Service Agent* du compte de
l'app si plus aucun agent Agent Runtime de ce projet n'est utilisé.

---

## 5. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `MANQUANT : …` ou `À CORRIGER` au chargement de la configuration | Valeur vide ou incohérente dans le fichier | Corriger le fichier, recharger |
| Commandes avec `--project=` vide | Configuration non chargée dans ce terminal | `source scripts/config.sh config/12-1-agents-dans-projet-exp.env` |
| `PERMISSION_DENIED` | Un rôle manque | Partie 1.5 |
| Toutes les réponses : « … filtrée par Model Armor » juste après le déploiement | Droit `modelarmor.user` du nouveau compte pas encore actif | Attendre 2 à 5 minutes, retester |
| `Error code 13` (Agent Runtime) | Erreur interne de Google | Relancer la commande (ou `terraform apply`) |
| `PERMISSION_DENIED` à `gcloud builds submit` juste après avoir activé Cloud Build ou créé `agents-build-sa` | Droits tout neufs, pas encore actifs | Attendre 1 à 2 minutes, relancer |
| `… does not have storage.objects.get access to the Google Cloud Storage object` | Compte de construction absent, ou `--service-account` oublié (le compte par défaut de Cloud Build n'a pas de droits) | Créer `agents-build-sa` (A3) et garder `--service-account=…` |
| Construction `FAILURE` | Erreur dans l'image | Ouvrir le lien du journal affiché par gcloud ; console : 🔎 « Cloud Build » → **Historique** (région `europe-west1`) |
| `ÉCHEC : 403` dans `test.sh` (Cloud Run) | Votre compte n'a pas `run.invoker` sur le service | Être propriétaire du projet, ou se donner ce rôle sur le service |
| Agent absent du chat | Pas d'**Agent User** pour le groupe, ou pas de licence | A6, « Donner l'accès » |
| « L'agent n'a pas pu répondre » dans le chat | Droit de l'app absent (A5 / B4 / C6), ou donné à une autre adresse (`NUM_APP` faux) | Vérifier avec la commande de A5 ; attendre 2 à 3 minutes après l'ajout d'un droit |
| Ajout refusé : région | Agent hors `europe-*` | `REGION=europe-west1` |
| Carte A2A refusée à la prévisualisation | JSON tronqué | Recopier la carte complète (`carte-*.json` ou `terraform output -json cards`) |

Journaux : console → 🔎 « Journaux » (projet des agents), ou
`gcloud logging read 'resource.type="cloud_run_revision" AND severity>=WARNING' --project=$PROJET_AGENTS --freshness=30m --limit=10`.

**Suite :** les agents **dans le projet de l'app** (et les modes Agent Registry, Dialogflow) :
[12-2](12-2-agents-dans-projet-app.md).
