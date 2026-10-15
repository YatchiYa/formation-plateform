# 11. Chez Acme : créer des agents dans un projet, les utiliser dans l'app Gemini Enterprise

**Pour qui :** vous avez accès à des projets Google Cloud **déjà créés** (facturation configurée, région `eu`), dont
`aiml-gemini-entreprise-ldbr`, qui héberge l'app Gemini Enterprise. Vous voulez **créer des agents dans un de vos projets**
et **les utiliser dans l'app**.

**Comment lire ce guide :** chaque étape donne la commande à copier, le **résultat obtenu** lors d'une exécution réelle
(identifiants remplacés par vos variables), et ce qu'il faut y vérifier. Exécutez les étapes **dans l'ordre**, depuis
**votre poste**, dans le dossier copié sur votre Bureau.

> Version générale, avec création des projets et explications détaillées de chaque sortie :
> [docs/10](10-rejouer-le-flux-complet.md). Ce guide-ci part de **vos** projets existants.

```
  PROJET X : vos agents (un de vos projets)                PROJET A : aiml-gemini-entreprise-ldbr
 ┌──────────────────────────────────────────────┐        ┌──────────────────────────────────────────┐
 │ Agent Runtime : meteo-agent, redaction-agent,│ appel  │ App Gemini Enterprise (eu)               │
 │                 traduction-agent             │◀───────│  └─ Agents : Météo, Rédaction, Traduction│
 │ (option) Cloud Run A2A : meteo-a2a, …        │        │                                          │
 │ Agent Registry : les agents, inscrits seuls  │        │ Compte de service de Gemini Enterprise : │
 │ Comptes de service : un par agent            │        │ service-NUM_A@gcp-sa-discoveryengine…    │
 │ IAM : 1 droit donné au compte de l'app ──────┼───────▶│                                          │
 └──────────────────────────────────────────────┘        └──────────────────────────────────────────┘
```

### Ce qui se fait sur chaque projet

| Projet | Ce que vous y faites | Partie |
|---|---|---|
| **Votre poste** | Outils, dossier sur le Bureau, environnement Python, connexion, tests en local | 1, 2, 6 |
| **Projet X** (vos agents) | Vérifier vos droits et les API ; déployer les agents (Terraform crée leurs comptes de service **et** donne le droit d'appel au compte de Gemini Enterprise) ; tester ; vérifier le droit | 3, 4, 8, 9 |
| **Projet A** `aiml-gemini-entreprise-ldbr` | Vérifier vos droits et les API ; vérifier le compte de Gemini Enterprise ; **ajouter les agents dans l'app**, donner l'accès à un groupe, tester dans le chat | 3, 4, 7, 10 |

Rien n'est créé dans le projet A, sauf les **entrées d'agents dans l'app** (partie 10) et, en option, l'orchestrateur
(partie 13), l'entrée de registre et la passerelle (partie 17).

---

## Sommaire

0. [Vos valeurs](#0-vos-valeurs)
1. [Votre poste : outils et dossier](#1-votre-poste--outils-et-dossier)
2. [Se connecter](#2-se-connecter)
3. [Vérifier vos droits sur les deux projets](#3-vérifier-vos-droits-sur-les-deux-projets)
4. [Vérifier les API, activer celles qui manquent](#4-vérifier-les-api-activer-celles-qui-manquent)
5. [Les comptes de service : lesquels, pourquoi, qui les crée](#5-les-comptes-de-service--lesquels-pourquoi-qui-les-crée)
6. [Tester les agents sur votre poste](#6-tester-les-agents-sur-votre-poste)
7. [Projet A : vérifier le compte de Gemini Enterprise](#7-projet-a--vérifier-le-compte-de-gemini-enterprise)
8. [Projet X : déployer les agents](#8-projet-x--déployer-les-agents)
9. [Projet X : vérifier que l'app a le droit d'appeler les agents](#9-projet-x--vérifier-que-lapp-a-le-droit-dappeler-les-agents)
10. [Ajouter les agents dans l'app, donner l'accès, tester dans le chat](#10-ajouter-les-agents-dans-lapp-donner-laccès-tester-dans-le-chat)
11. [Créer votre propre agent et le mettre dans l'app](#11-créer-votre-propre-agent-et-le-mettre-dans-lapp)
12. [(Option) Les agents en A2A sur Cloud Run](#12-option-les-agents-en-a2a-sur-cloud-run)
13. [(Option) Un agent de l'app qui appelle un agent de X](#13-option-un-agent-de-lapp-qui-appelle-un-agent-de-x)
14. [(Option) Une clé d'API pour le modèle](#14-option-une-clé-dapi-pour-le-modèle)
15. [Ce qui peut arriver (constaté en vrai)](#15-ce-qui-peut-arriver-constaté-en-vrai)
16. [Tout retirer](#16-tout-retirer)
17. [Les autres modes d'ajout : Agent Registry, Dialogflow, Marketplace](#17-les-autres-modes-dajout--agent-registry-dialogflow-marketplace)

---

## 0. Vos valeurs

| Variable | Valeur | Où la trouver |
|---|---|---|
| `PROJET_A` | `aiml-gemini-entreprise-ldbr` | Projet de l'app Gemini Enterprise |
| `NUM_A` | `98547854221` (à vérifier, ci-dessous) | Numéro du projet A |
| `APP_ID` | **à compléter** | Console → 🔎 « Gemini Enterprise » → l'app → **Présentation** |
| `PROJET_X` | **à compléter** | Le projet où vous créez les agents (sélecteur de projet de la console) |
| `REGION` | `europe-west1` | App en multi-région `eu` ⇒ agents en `europe-*` |

**Ouvrez un terminal** (Mac : application *Terminal* ; Linux : votre terminal), collez ce bloc **après l'avoir complété** :

```bash
export PROJET_A=aiml-gemini-entreprise-ldbr
export NUM_A=98547854221
export APP_ID=ID_DE_L_APP                   # à remplacer
export PROJET_X=ID_DE_VOTRE_PROJET_AGENTS   # à remplacer
export REGION=europe-west1 GE_LOCATION=eu
export GE_SA=service-$NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com
export DOSSIER=~/Desktop/09-agents-multi-projets-gemini-enterprise
echo "A=$PROJET_A ($NUM_A) app=$APP_ID  X=$PROJET_X  dossier=$DOSSIER"
```

**Résultat attendu :** une ligne avec vos valeurs, sans `ID_DE_…`.

> **À chaque nouveau terminal, recollez ce bloc.** Les variables disparaissent quand le terminal se ferme ; une commande
> qui affiche `--project=` sans valeur signifie que le bloc n'a pas été collé.

---

## 1. Votre poste : outils et dossier

### 1.1 Les outils

| Outil | Mac (Homebrew) | Linux | Vérifier |
|---|---|---|---|
| gcloud | `brew install --cask google-cloud-sdk` | [guide d'installation Google](https://cloud.google.com/sdk/docs/install) | `gcloud version` |
| Terraform 1.9+ | `brew tap hashicorp/tap && brew install hashicorp/tap/terraform` | dépôt HashiCorp | `terraform version` |
| uv (gère Python 3.12 à 3.14) | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` |

Le composant `beta` de gcloud sert à la partie 7 :

```bash
gcloud components install beta --quiet      # si gcloud vient de Homebrew ou de l'installeur Google
```

**Pas de droits d'installation sur le poste ?** Faites tout dans **Cloud Shell** (console → icône `>_`) : les outils y sont
déjà, et `DOSSIER=~/09-agents-multi-projets-gemini-enterprise` (après import du dossier : menu à trois points → Importer).

### 1.2 Le dossier

Vous avez copié `09-agents-multi-projets-gemini-enterprise` sur votre Bureau.

```bash
cd $DOSSIER && ls
```

**Résultat attendu :**

```
01-bis-cloud-run-a2a  02-bis-agent-runtime  agents  docs  guide-interactif.html  portail-agents-partenaires.html  README.md  scripts  terraform  …
```

**Si le dossier contient déjà des fichiers d'une autre personne** (copie d'un poste à l'autre), supprimez-les : ils
décrivent **ses** déploiements.

```bash
find $DOSSIER -name "terraform.tfstate*" -o -name "terraform.tfvars" -o -name ".terraform" | grep -v ".venv"
```

**Résultat attendu :** rien. Sinon, ne les supprimez qu'après avoir vérifié avec leur auteur qu'ils ne servent plus.

### 1.3 L'environnement Python (une fois)

```bash
cd $DOSSIER
uv venv -p '>=3.12' .venv            # uv télécharge Python 3.12 si besoin
source .venv/bin/activate        # à refaire dans chaque nouveau terminal
uv pip install -r agents/trio/requirements.txt
```

**Résultat attendu :** `Installed … packages`. Le début de votre invite de commande affiche `(.venv)`.

---

## 2. Se connecter

```bash
gcloud auth login                         # pour gcloud
gcloud auth application-default login     # pour Terraform et les scripts Python
gcloud config set project $PROJET_X
```

**Résultat attendu :** le navigateur s'ouvre deux fois (compte Acme) ; à la fin
`Credentials saved to file: [.../application_default_credentials.json]` puis `Updated property [core/project]`.

**Vérifier le numéro du projet A :**

```bash
gcloud projects describe $PROJET_A --format='value(projectNumber)'
```

**Résultat attendu :** exactement `NUM_A`. Sinon, corrigez `NUM_A` dans le bloc de la partie 0 et recollez-le : tout le
reste en dépend (adresse du compte de Gemini Enterprise). Un numéro de projet compte en général 12 chiffres.

---

## 3. Vérifier vos droits sur les deux projets

```bash
for P in $PROJET_X $PROJET_A; do
  echo "== $P"
  gcloud projects get-iam-policy $P --flatten=bindings \
    --filter="bindings.members:user:$(gcloud config get-value account 2>/dev/null)" --format="value(bindings.role)"
done
```

**Ce qu'il faut y trouver :**

| Projet | Rôles nécessaires (ou `roles/owner`) | Pour |
|---|---|---|
| X | `roles/aiplatform.admin`, `roles/iam.serviceAccountAdmin`, `roles/iam.serviceAccountUser`, `roles/resourcemanager.projectIamAdmin`, `roles/serviceusage.serviceUsageAdmin`, `roles/modelarmor.admin`, `roles/agentregistry.admin` | Créer les agents, leurs comptes de service, leurs droits, les templates Model Armor |
| X (partie 12 seulement) | `roles/run.admin`, `roles/artifactregistry.admin`, `roles/cloudbuild.builds.editor`, `roles/storage.admin` | Cloud Run, dépôt d'images, construction des images dans Google Cloud (Cloud Build) |
| A | `roles/discoveryengine.admin` (Gemini Enterprise Admin), `roles/serviceusage.serviceUsageAdmin` | Ajouter les agents à l'app, donner l'accès aux groupes |

> Un rôle donné **à travers un groupe** n'apparaît pas dans cette commande. Vérifiez alors dans la console : IAM du projet
> (`https://console.cloud.google.com/iam-admin/iam?project=ID_DU_PROJET`), ou demandez à l'admin du projet.
> **Un rôle manque ?** Demandez-le avant de continuer : sans lui, une étape échouera avec `PERMISSION_DENIED`.

---

## 4. Vérifier les API, activer celles qui manquent

Les API sont normalement déjà actives. Ce bloc les **vérifie** et n'active **que** celles qui manquent.

```bash
verifier_api() {  # verifier_api PROJET API1 API2 …
  local P=$1; shift; local manquantes=()
  for API in "$@"; do
    if gcloud services list --enabled --project=$P --filter="config.name=$API" --format="value(config.name)" | grep -q .; then
      echo "OK        $API"
    else
      echo "MANQUANTE $API"; manquantes+=($API)
    fi
  done
  [ ${#manquantes[@]} -gt 0 ] && gcloud services enable "${manquantes[@]}" --project=$P && echo "activées : ${manquantes[*]}"
  return 0
}
echo "== Projet X ($PROJET_X)"
verifier_api $PROJET_X cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com \
  aiplatform.googleapis.com agentregistry.googleapis.com modelarmor.googleapis.com logging.googleapis.com
echo "== Projet A ($PROJET_A)"
verifier_api $PROJET_A cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com \
  discoveryengine.googleapis.com
```

**Résultat attendu :** une ligne `OK` par API ; s'il en manquait, `activées : …` à la fin du bloc du projet.

| API | Pourquoi |
|---|---|
| `cloudresourcemanager`, `serviceusage` | **Indispensables avant Terraform** : il lit le numéro du projet et l'état des API |
| `iam` | Créer les comptes de service des agents |
| `aiplatform` | Gemini (Vertex AI) et l'hébergement Agent Runtime |
| `agentregistry` | Le catalogue des agents |
| `modelarmor` | Le filtrage des questions et réponses |
| `logging` | Les journaux des agents |
| `discoveryengine` (A) | Gemini Enterprise |
| Partie 12 : `run`, `artifactregistry`, `cloudbuild` · Partie 14 : `secretmanager` | Ajoutez-les à la liste si vous faites ces parties |

Terraform redemande ces API lors du déploiement : si elles sont déjà actives, il ne change rien.

---

## 5. Les comptes de service : lesquels, pourquoi, qui les crée

Un compte de service est l'**identité d'un programme** (un agent, l'app). Chacun reçoit **seulement** les droits dont il a
besoin.

| Compte | Projet | Rôle | Créé par | Partie |
|---|---|---|---|---|
| `meteo-agent-sa`, `redaction-agent-sa`, `traduction-agent-sa` | X | Faire tourner chaque agent : `aiplatform.user`, `logging.logWriter`, `monitoring.metricWriter`, `cloudtrace.agent` sur X, `modelarmor.user` sur le projet des templates | **Terraform** | 8 |
| `service-NUM_A@gcp-sa-discoveryengine…` (compte de Gemini Enterprise) | A | **Appeler les agents** depuis l'app. Reçoit dans X : `roles/discoveryengine.serviceAgent` | **Google** (existe avec l'app) ; le droit dans X : Terraform | 7, 8, 9 |
| `meteo-a2a-sa`, … | X | Faire tourner les agents Cloud Run | Terraform | 12 (option) |
| `stock-agent-sa` (X), `assistant-magasin-sa` (A) | X, A | Agent stock ; orchestrateur qui l'appelle | Terraform | 13 (option) |
| `deployeur-agents` | X | **Lancer Terraform** à votre place, avec des droits limités | **Vous** (ci-dessous) | Option |

**Aucun de ces comptes n'a de clé.** Google signe les appels. Ne créez jamais de clé de compte de service (fichier JSON).

### 5.1 (Option) Un compte « déployeur » pour Terraform

Par défaut, Terraform agit avec **votre** compte. Si la sécurité préfère qu'il agisse avec un compte dédié (droits limités,
traçables), créez-le une fois et **empruntez-le** :

```bash
gcloud iam service-accounts create deployeur-agents --project=$PROJET_X --display-name="Terraform : déploiement des agents"
export DEPLOYEUR=deployeur-agents@$PROJET_X.iam.gserviceaccount.com
for R in aiplatform.admin iam.serviceAccountAdmin iam.serviceAccountUser resourcemanager.projectIamAdmin \
         serviceusage.serviceUsageAdmin modelarmor.admin agentregistry.admin logging.viewer; do
  gcloud projects add-iam-policy-binding $PROJET_X --condition=None --role=roles/$R --member=serviceAccount:$DEPLOYEUR >/dev/null && echo "roles/$R"
done
# vous pouvez « parler en son nom » (et seulement vous) :
gcloud iam service-accounts add-iam-policy-binding $DEPLOYEUR --project=$PROJET_X \
  --role=roles/iam.serviceAccountTokenCreator --member=user:$(gcloud config get-value account 2>/dev/null)
# Terraform l'utilisera :
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT=$DEPLOYEUR
```

**Résultat attendu :** `Created service account [deployeur-agents]`, la liste des 8 rôles, puis `Updated IAM policy for
serviceAccount […]`. Ajoutez `export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT=…` au bloc de la partie 0 si vous l'utilisez.

Pour que Terraform puisse aussi publier dans l'app (partie 10, option 1), le déployeur a besoin de
`roles/discoveryengine.admin` sur le projet A. Sinon, publiez avec votre compte (partie 10, option 2).

---

## 6. Tester les agents sur votre poste

**Pourquoi :** un agent qui échoue ici échouera dans l'app. On sépare les problèmes d'agent des problèmes de droits.

```bash
cd $DOSSIER && source .venv/bin/activate
python scripts/test_trio.py
```

**Résultat obtenu :**

```
tests trio OK (9 scénarios, 6 agents)
```

**Les agents avec le vrai Gemini** (Vertex AI dans le projet X, avec votre identité, sans clé) :

```bash
export LOCAL_DEV=1 GOOGLE_CLOUD_PROJECT=$PROJET_X
adk web --port 8080 agents/trio
```

Ouvrez `http://localhost:8080`, choisissez `traduction_agent`, écrivez « Traduis en espagnol : Votre tente Quechua est
disponible en retrait en magasin. »

**Résultat obtenu :** outils `glossaire` puis `verifier_traduction` ; réponse « Tu tienda de campaña Quechua está disponible
para recogida en tienda. — Contrôle : conforme ». Arrêter avec `Ctrl+C`.

`LOCAL_DEV=1` permet de tourner sans Model Armor **en local seulement** ; déployés, les agents refusent de démarrer sans.

---

## 7. Projet A : vérifier le compte de Gemini Enterprise

C'est **ce compte** qui appellera vos agents depuis l'app. Il existe déjà, puisque l'app existe. On affiche son adresse
pour vérifier qu'elle correspond à `NUM_A` :

```bash
gcloud beta services identity create --service=discoveryengine.googleapis.com --project=$PROJET_A
```

**Résultat obtenu :**

```
Service identity created: service-100000000001@gcp-sa-discoveryengine.iam.gserviceaccount.com
```

(Le message dit « created » même quand le compte existe déjà : il ne change rien.) **L'adresse doit être exactement
`$GE_SA`** (`echo $GE_SA`). Si elle diffère, `NUM_A` est faux : corrigez-le (partie 0) avant d'aller plus loin.

---

## 8. Projet X : déployer les agents

On déploie les 6 agents du catalogue (`agents/trio/catalogue.json`) sur **Agent Runtime** (hébergement géré par Google : rien à maintenir, sessions et journaux inclus).

### 8.1 Configurer

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform
cat > terraform.tfvars <<EOF
agents_project_id = "$PROJET_X"
ge_project_number = "$NUM_A"
region            = "$REGION"
ge_location       = "$GE_LOCATION"
EOF
cat terraform.tfvars
```

**Résultat attendu :** le fichier avec vos **vraies** valeurs (pas de `$`).

| Ligne | Effet |
|---|---|
| `agents_project_id` | Les agents sont créés dans X |
| `ge_project_number` | Terraform donne au compte de Gemini Enterprise de A le droit d'appeler les agents de X (`discoveryengine.serviceAgent` sur X) |
| Pas de `prompt_template` | Terraform crée une paire de templates Model Armor dans X. Templates centraux de la sécurité : ajoutez `prompt_template = "projects/…/locations/eu/templates/…"` et `response_template = "…"` |

### 8.2 Déployer

```bash
terraform init
terraform plan
```

**Résultat obtenu (fin du plan) :** `Plan: 49 to add, 0 to change, 0 to destroy.` Vérifiez qu'il y a **0 to destroy**.

```bash
terraform apply       # taper yes ; 10 à 15 minutes
cp terraform.tfstate ~/Desktop/sauvegarde-02bis-$(date +%Y%m%d).tfstate
```

**Résultat obtenu :**

```
Apply complete! Resources: 49 added, 0 changed, 0 destroyed.

Outputs:

agents = {
  "identite" = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/…"
  "meteo" = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/5587992970264576000"
  "redaction" = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/1022468848017735680"
  "retour" = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/…"
  "taille" = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/…"
  "traduction" = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/976306951837188096"
}
ge_agents_page = "(ge_app_id vide : agents non publiés)"
ge_service_agent = "serviceAccount:service-100000000001@gcp-sa-discoveryengine.iam.gserviceaccount.com"
```

- `agents` : le **nom de ressource** de chaque agent ; c'est ce qu'on donne à l'app (partie 10).
- `ge_service_agent` : le compte qui a reçu le droit ; doit être `$GE_SA`.
- **Terraform tourne en local** : `terraform.tfstate` (dans ce dossier) est la mémoire de ce qui a été créé. La copie sur
  le Bureau sert de sauvegarde. Ne le supprimez pas, ne le partagez pas, ne le committez pas.

> **Constaté :** `Error code 13` à la création d'un agent (erreur interne de Google). **Relancez `terraform apply`** : seul
> l'agent manquant est recréé (`Resources: 1 added`).

### 8.3 Attendre 5 minutes, puis tester

> Les sorties ci-dessous (8.3 et 8.4) viennent d'une exécution à 3 agents. Aujourd'hui, `test.sh` et la liste
> montrent les 6 agents du catalogue, un bloc par agent, sous la même forme.

Les droits des comptes tout juste créés mettent quelques minutes à s'appliquer.

```bash
cd $DOSSIER/02-bis-agent-runtime && source ../.venv/bin/activate && ./test.sh
```

**Résultat obtenu :**

```
== meteo  (projects/<PROJET_X>/locations/europe-west1/reasoningEngines/5587992970264576000)
  -> outil : meteo({'ville': 'Lille', 'jours': 2})
  -> outil : conseil_equipement({'temperature_c': 10, 'vent_kmh': 27, 'activite': 'course à pied', 'pluie_mm': 8.6})
agent : Demain matin à Lille, de la pluie faible est prévue avec environ 10°C et du vent à 27 km/h. …

== redaction  (…)
  -> outil : charte_redactionnelle({'canal': 'email_client'})
  -> outil : analyser_texte({…})
agent : Bonjour, … Avant : 7 mots, après : 27 mots

== traduction  (…)
  -> outil : glossaire({'langue_cible': 'es'})
  -> outil : verifier_traduction({…})
agent : Su tienda de campaña Quechua está disponible para recogida en tienda.  Contrôle : conforme
```

**À vérifier :** chaque agent appelle ses outils (`-> outil`) puis répond. Si toutes les réponses sont « … filtrée par
Model Armor », attendez encore quelques minutes ([partie 15](#15-ce-qui-peut-arriver-constaté-en-vrai)).

### 8.4 Agent Registry

```bash
gcloud agent-registry agents list --location=$REGION --project=$PROJET_X --format="table(displayName,agentId)"
```

**Résultat obtenu :**

```
DISPLAY_NAME      AGENT_ID
meteo-agent       urn:agent:projects-NUM_X:projects:NUM_X:locations:europe-west1:aiplatform:reasoningEngines:5587992970264576000
redaction-agent   urn:agent:projects-NUM_X:projects:NUM_X:locations:europe-west1:aiplatform:reasoningEngines:1022468848017735680
traduction-agent  urn:agent:projects-NUM_X:projects:NUM_X:locations:europe-west1:aiplatform:reasoningEngines:976306951837188096
```

Les agents Agent Runtime s'inscrivent **seuls**. (Une ligne `Workspace Agent` peut apparaître : agent de Google.)

### 8.5 Le droit de Gemini Enterprise sur X (vérifié aussi en partie 9)

```bash
gcloud projects get-iam-policy $PROJET_X --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
```

**Résultat obtenu :** `roles/discoveryengine.serviceAgent`

---

## 9. Projet X : vérifier que l'app a le droit d'appeler les agents

Sans ce droit, l'agent s'ajoute dans l'app mais **ne répond jamais**. Terraform l'a donné (partie 8) ; vérifiez-le avant
d'aller dans l'app.

```bash
gcloud projects get-iam-policy $PROJET_X --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
```

**Résultat obtenu :** `roles/discoveryengine.serviceAgent`

**Rien ne s'affiche ?** `ge_project_number` est faux dans `terraform.tfvars` : corrigez-le et relancez `terraform apply`.
Ou donnez le droit à la main :

```bash
gcloud projects add-iam-policy-binding $PROJET_X --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA
```

Agents Cloud Run (partie 12) : le droit est `roles/run.invoker`, **sur chaque service** :

```bash
for S in meteo-a2a redaction-a2a traduction-a2a; do
  echo "$S : $(gcloud run services get-iam-policy $S --region=$REGION --project=$PROJET_X --flatten=bindings \
    --filter="bindings.members:$GE_SA" --format="value(bindings.role)")"
done
```

**Résultat obtenu :** `meteo-a2a : roles/run.invoker` (et de même pour les deux autres).

---

## 10. Ajouter les agents dans l'app, donner l'accès, tester dans le chat

Il faut le rôle **Gemini Enterprise Admin** sur `aiml-gemini-entreprise-ldbr` et l'**ID de l'app** (`APP_ID`).

### Option 1 : par Terraform (si vous avez les droits sur les deux projets)

Ajoutez deux lignes à `02-bis-agent-runtime/terraform/terraform.tfvars`, puis relancez :

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform
cat >> terraform.tfvars <<EOF
ge_project_id     = "$PROJET_A"
ge_app_id         = "$APP_ID"
EOF
terraform plan        # « Plan: 7 to add » : l'API Discovery Engine (déjà active : rien ne change) + 6 publications
terraform apply       # yes
```

**Résultat attendu :** `registered Météo & équipement`, `registered Rédaction & reformulation`, `registered Traduction
Acme`, … (un par agent), puis `Apply complete! Resources: 7 added`. `terraform output ge_agents_page` donne le lien de la page Agents de
l'app. Avec cette option, `terraform destroy` retirera aussi les agents de l'app.

### Option 2 : par le script (votre compte, sans toucher au Terraform)

```bash
cd $DOSSIER && export GE_PROJECT=$PROJET_A GE_APP=$APP_ID GE_LOCATION=$GE_LOCATION
terraform -chdir=02-bis-agent-runtime/terraform output -json agents > /tmp/agents.json
for K in meteo redaction traduction; do
  RES=$(python3 -c "import json; print(json.load(open('/tmp/agents.json'))['$K'])")
  NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
  DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
  ./scripts/add_agent_to_ge.sh adk "$RES" "$NOM" "$DESC"
done
./scripts/add_agent_to_ge.sh list
```

**Résultat attendu :** pour chaque agent, `droit accordé : …` (le droit existe déjà : rien ne change) puis
`ajouté : projects/…/collections/default_collection/engines/<APP_ID>/assistants/default_assistant/agents/<ID>`. La liste
finale montre les 3 agents, type `adkAgentDefinition`.

### Option 3 : dans la console

Console → 🔎 « Gemini Enterprise » → l'app → **Agents** → **+ Ajouter un agent** → **Agent personnalisé via Agent Runtime**
→ **Nom de l'agent**, **Décrivez votre agent** (depuis `agents/trio/catalogue.json`), **Chemin de ressource Agent Runtime**
(depuis `terraform output agents`) → **Créer**. Détail de chaque champ : [docs/09, 2.1](09-connecter-a-gemini-enterprise.md#21-agent-personnalisé-via-agent-runtime).

### Donner l'accès

Pour chaque agent : app → **Agents** → l'agent → onglet **Autorisations utilisateur** → **Ajouter** → un **groupe Google**
(ex. votre équipe) → rôle **Agent User** → **Enregistrer**. Les membres du groupe doivent avoir une **licence** Gemini
Enterprise.

### Tester dans le chat

Ouvrez l'app web (app → **Intégration** → lien de l'app web) avec un compte du groupe → **Agents** → **Traduction
Acme** → « Traduis en allemand : retour gratuit sur les chaussures Kiprun ».

**Résultat attendu :** « Kostenlose Rücksendung … Kiprun … — Contrôle : conforme ». La première réponse peut prendre 20 à
40 secondes (démarrage de l'agent). Les sessions apparaissent dans le **projet X** (console → 🔎 « Agent Runtime » →
l'agent → **Sessions**).

> **Point à constater au premier passage :** l'ajout dans l'app et la réponse dans le chat sont la seule partie que l'essai
> n'a pas pu exécuter (pas d'app Gemini Enterprise sur les projets de test). Tout ce qui précède a été exécuté en vrai, y
> compris l'appel des agents de X par un compte du projet A muni de ce même droit.

---

## 11. Créer votre propre agent et le mettre dans l'app

**11.1 Le code** (exemple : un agent « stock rayon »)

```bash
cd $DOSSIER/agents/trio
mkdir rayon_agent && echo "from . import agent" > rayon_agent/__init__.py
```

Créez `rayon_agent/agent.py` (dans votre éditeur) :

```python
from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun


def stock_rayon(sku: str) -> dict:
    """Stock en rayon d'un article Acme.

    Args:
        sku: Code article, ex. "8771234".
    """
    return {"status": "success", "sku": sku, "stock": 12}   # à remplacer par l'appel réel


root_agent = Agent(
    name="rayon_agent",                     # = nom du dossier
    model=commun.modele(),                  # Gemini via Vertex AI (ou clé d'API, partie 14)
    description="Donne le stock en rayon d'un article Acme à partir de son code.",
    instruction="Appelle toujours stock_rayon ; ne devine jamais un stock.",
    tools=[stock_rayon],
)

app = commun.app_securisee(root_agent)      # ajoute Model Armor
agent_runtime_app = AdkApp(app=app)         # point d'entrée Agent Runtime
```

**11.2 Le déclarer** dans `agents/trio/catalogue.json` : ajoutez cette entrée **dans les accolades principales**, après la
dernière entrée et une virgule. La clé (`rayon`) devient le nom de l'agent dans Google Cloud : minuscules et chiffres, 2 à 15 caractères.

```json
"rayon": {
  "dossier": "rayon_agent",
  "nom_affiche": "Stock rayon",
  "description": "Donne le stock en rayon d'un article Acme à partir de son code.",
  "competences": [{"id": "stock", "name": "Stock rayon", "description": "Stock d'un article en rayon.",
                   "tags": ["stock"], "examples": ["Stock de 8771234 ?"]}]
}
```

```bash
cd $DOSSIER && python3 -m json.tool agents/trio/catalogue.json > /dev/null && echo "catalogue OK"
LOCAL_DEV=1 GOOGLE_CLOUD_PROJECT=$PROJET_X adk web --port 8080 agents/trio      # tester rayon_agent, puis Ctrl+C
```

**11.3 Le déployer**

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform && terraform plan && terraform apply
```

**Résultat attendu :** le plan crée `module.agent["rayon"]` et ne touche pas aux autres agents (chacun n'emporte que son
propre dossier). Avec l'option 1 de la partie 10, l'agent est aussi publié dans l'app. Sinon :
`./scripts/add_agent_to_ge.sh adk <ressource de rayon> "Stock rayon" "<description>"`. Puis **Agent User** pour le groupe.
Plus court (squelette par `scripts/nouvel_agent.py`), et pour Cloud Run ou la console : [docs/12-3](12-3-ajouter-des-agents-un-par-un.md).

---

## 12. (Option) Les agents en A2A sur Cloud Run

À choisir si l'agent doit aussi être appelé hors de Google (protocole ouvert A2A). **Pas besoin de Docker** : les images
sont construites dans Google Cloud (Cloud Build). Il faut les rôles de la partie 3 pour la partie 12 (`run.admin`,
`artifactregistry.admin`, `cloudbuild.builds.editor`, `storage.admin`) sur X, et les API `run`, `artifactregistry`,
`cloudbuild` (ajoutez-les à la partie 4). Terraform crée lui-même le compte qui construit les images
(`agents-a2a-build-sa`, 3 rôles).

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
cat > terraform.tfvars <<EOF
agents_project_id = "$PROJET_X"
ge_project_number = "$NUM_A"
region            = "$REGION"
ge_location       = "$GE_LOCATION"
EOF
terraform init && terraform plan       # « Plan: 63 to add » (6 agents : 23 pour le 1er, +8 par agent en plus)
terraform apply                        # ~10 min ; Cloud Build construit une image par agent (~1 min 20 s chacune)
```

**Résultat obtenu :** `Apply complete! Resources: 63 added`, puis les sorties `cards` (cartes A2A v0.3) et `urls` (une par
agent). Ouvrir une URL dans le navigateur donne **403** : le service est privé, c'est voulu.

**Attendre 5 minutes**, puis :

```bash
cd $DOSSIER/01-bis-cloud-run-a2a && ./test.sh
```

**Résultat obtenu :** pour chaque agent `carte : … (A2A 0.3)`, deux réponses dans la même conversation, puis
`OK : les agents répondent en A2A v0.3, avec mémoire de conversation`.

**Mettre un agent A2A dans l'app :**

```bash
cd $DOSSIER && export GE_PROJECT=$PROJET_A GE_APP=$APP_ID GE_LOCATION=$GE_LOCATION
terraform -chdir=01-bis-cloud-run-a2a/terraform output -json cards | python3 -c 'import json,sys; print(json.load(sys.stdin)["traduction"])' > carte-traduction.json
./scripts/add_agent_to_ge.sh a2a carte-traduction.json "Traduction Acme (A2A)"
```

Chaque construction d'image est visible dans la console : 🔎 « Cloud Build » → **Historique** (région `europe-west1`),
avec son journal. Un `PERMISSION_DENIED` pendant la construction juste après le 1er `apply` (droits du compte de
construction tout neufs) : Terraform réessaie seul ; sinon attendez 1 à 2 minutes et relancez `terraform apply`.

---

## 13. (Option) Un agent de l'app qui appelle un agent de X

**Attention :** cette partie **déploie un agent (l'orchestrateur) dans `aiml-gemini-entreprise-ldbr`**. Ne la faites que si
l'équipe Gemini Enterprise est d'accord. Elle montre le modèle « un agent appelle l'agent d'une autre équipe » : l'agent
stock (X) et l'orchestrateur (A), qui le **trouve** dans le registre de X puis l'**appelle**.

```bash
cd $DOSSIER/terraform
cat > terraform.tfvars <<EOF
agents_project_id = "$PROJET_X"
ge_project_id     = "$PROJET_A"
region            = "$REGION"
ge_location       = "$GE_LOCATION"
EOF
terraform init && terraform plan       # « Plan: 26 to add »
terraform apply
cd $DOSSIER && python scripts/query.py orchestrator "Il reste des tentes 8771234 à Lyon ?"
```

**Résultat obtenu :**

```
  -> outil : ask_stock_agent({'question': "Est-ce qu'il reste des tentes avec le code article 8771234 à Lyon ?"})
agent : Non, la **Tente 2 secondes 2 places** (code article **8771234**) est actuellement en **rupture de stock** dans le
magasin de **Lyon** (0 article disponible). … **Lille** : 12 en stock · **Paris-La-Défense** : 4 en stock
```

Les chiffres viennent de l'agent stock du projet X : l'appel entre projets fonctionne. Sans le droit de l'orchestrateur
sur l'agent stock, il répond que l'agent est indisponible (testé). Détail : [docs/10, partie 10](10-rejouer-le-flux-complet.md#10-un-agent-qui-appelle-un-agent-dun-autre-projet-a--x).

---

## 14. (Option) Une clé d'API pour le modèle

Par défaut, aucune clé : Vertex AI avec l'identité de l'agent. Pour utiliser une clé (Google AI Studio : `gemini` ; Vertex
AI : `vertex`), rangez-la dans Secret Manager du projet X :

```bash
gcloud services enable secretmanager.googleapis.com --project=$PROJET_X
printf '%s' "VOTRE_CLE" | gcloud secrets create gemini-api-key --data-file=- --project=$PROJET_X
cd $DOSSIER/02-bis-agent-runtime/terraform
cat >> terraform.tfvars <<EOF
model_api_key_secret = "gemini-api-key"
model_api_key_type   = "gemini"
EOF
terraform plan && terraform apply
```

**Résultat attendu du plan :** 6 `google_secret_manager_secret_iam_member` (un par agent : chaque agent peut lire **ce** secret) et la
variable `GEMINI_API_KEY` ajoutée aux agents. En local : `export GEMINI_API_KEY=…` avant `adk web`.

---

## 15. Ce qui peut arriver (constaté en vrai)

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `--project=` vide, `ID_DE_…` dans une commande | Bloc de la partie 0 non collé dans ce terminal | Le recoller |
| `(.venv)` absent, `ModuleNotFoundError` | Environnement Python non activé | `source $DOSSIER/.venv/bin/activate` |
| `PERMISSION_DENIED` | Un rôle manque | Partie 3 |
| `403 Cloud Resource Manager API has not been used` | API de départ inactive | Partie 4 |
| Toutes les réponses : « … filtrée par Model Armor » juste après le premier `apply` | Le droit `modelarmor.user` du nouvel agent n'est pas encore actif | Attendre 2 à 5 minutes, relancer le test |
| `Error code 13` à la création d'un agent | Erreur interne de Google | Relancer `terraform apply` |
| Partie 12 : `PERMISSION_DENIED` pendant la construction des images | API Cloud Build ou compte de construction tout neufs | Attendre 1 à 2 minutes, relancer `terraform apply` |
| Partie 12 : construction `FAILURE` | Erreur dans l'image | Ouvrir le lien du journal affiché ; console : 🔎 « Cloud Build » → **Historique** (région `europe-west1`) |
| `gcloud beta` : composant absent | gcloud installé sans `beta` | `gcloud components install beta` |
| `Error acquiring the state lock` / ressources « already exist » | Deux exécutions en même temps, ou état perdu | Un seul terminal par dossier ; restaurer la sauvegarde de `terraform.tfstate` |
| Agent absent du chat | Pas d'**Agent User** pour le groupe, ou pas de licence | Partie 10, « Donner l'accès » |
| « L'agent n'a pas pu répondre » dans le chat | Droit `discoveryengine.serviceAgent` absent sur X, ou `NUM_A` faux | Partie 9 ; attendre 2 à 3 minutes après avoir donné le droit |

**Journaux d'un agent Agent Runtime :**

```bash
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND severity>=WARNING' \
  --project=$PROJET_X --freshness=1h --limit=10 --format="value(timestamp,resource.labels.reasoning_engine_id,textPayload)"
```

---

## 16. Tout retirer

**Un dossier à la fois**, dans cet ordre (ne lancez que ceux que vous avez déployés) :

```bash
cd $DOSSIER
terraform -chdir=terraform destroy                        # partie 13 -> Resources: 26 destroyed
terraform -chdir=01-bis-cloud-run-a2a/terraform destroy   # partie 12 -> Resources: 63 destroyed
terraform -chdir=02-bis-agent-runtime/terraform destroy   # partie 8  -> Resources: 49 destroyed (56 avec la publication)
```

Avec l'option 1 de la partie 10, `destroy` retire aussi les agents de l'app. Avec l'option 2 ou 3, retirez-les d'abord :
`./scripts/add_agent_to_ge.sh delete "Traduction Acme"` (une fois par agent), ou app → **Agents** → l'agent → **Supprimer**.


**Vérifier qu'il ne reste rien dans X :**

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_X/locations/$REGION/reasoningEngines" \
  | python3 -c 'import json,sys; print("agents Agent Runtime :", [e["displayName"] for e in json.load(sys.stdin).get("reasoningEngines",[])])'
```

**Résultat obtenu :** `agents Agent Runtime : []`

Pour lire les identifiants, les URN du registre, les cartes A2A et les adresses : [docs/10, annexe](10-rejouer-le-flux-complet.md#15-annexe--lire-les-sorties-champs-identifiants-url).

---

## 17. Les autres modes d'ajout : Agent Registry, Dialogflow, Marketplace

Dans l'app, **+ Ajouter un agent** propose 5 modes. Les parties 10 et 12 couvrent les deux qui fonctionnent **depuis un
autre projet** (Agent Runtime, A2A). Voici les trois autres, appliqués à `aiml-gemini-entreprise-ldbr`.

| Mode | Agent dans un autre projet que l'app ? | Testé dans ce guide |
|---|---|---|
| Agent personnalisé via **Agent Runtime** | Oui | Oui (parties 8 à 10, sauf l'écran final de l'app) |
| Agent personnalisé via **A2A** | Oui | Oui (partie 12, sauf l'écran final de l'app) |
| Agents depuis **Agent Registry** | Non : le registre doit être celui **du projet de l'app**, relié à son Agent Gateway | Étape 1 (déclaration dans le registre de l'app) : oui. Étapes 2 à 5 : à constater |
| Agent personnalisé via **Dialogflow** | Non documenté par Google | À constater |
| Agents via **Marketplace** | — (agent d'éditeur) | — |

### 17.1 Agents depuis Agent Registry

**Le principe :** l'app ne prend des agents que dans **son** registre (projet A, `europe-west1`), et tout son trafic passe
alors par une **Agent Gateway** qui refuse ce qui n'est pas autorisé. Un agent de X y entre par une **déclaration** de sa
carte A2A dans le registre de A.

**Étape 1. Déclarer l'agent de X dans le registre de A** (carte de la partie 12) :

```bash
cd $DOSSIER
terraform -chdir=01-bis-cloud-run-a2a/terraform output -json cards | python3 -c 'import json,sys; print(json.load(sys.stdin)["traduction"])' > carte-traduction.json
gcloud services enable agentregistry.googleapis.com --project=$PROJET_A
gcloud agent-registry services create traduction-equipe-x --location=$REGION --project=$PROJET_A \
  --display-name="Traduction (équipe X)" --description="Traduit un texte en 7 langues en respectant le glossaire Acme." \
  --agent-spec-type=A2A_AGENT_CARD --agent-spec-content="$(cat carte-traduction.json)"
gcloud agent-registry services list --location=$REGION --project=$PROJET_A --format="table(displayName,name,registryResource)"
```

**Résultat obtenu :**

```
Created service [traduction-equipe-x].
DISPLAY_NAME           NAME                                                                                     REGISTRY_RESOURCE
Traduction (équipe X)  projects/aiml-gemini-entreprise-ldbr/locations/europe-west1/services/traduction-equipe-x  projects/100000000001/locations/europe-west1/agents/agentregistry-00000000-…
```

Ne mettez pas `--interfaces` : avec une carte A2A, l'API le refuse (l'adresse est déjà dans la carte).

**Étape 2. Créer l'Agent Gateway du projet A** (une fois ; en `europe-west1` pour une app `eu`) :

```bash
gcloud services enable networkservices.googleapis.com iap.googleapis.com --project=$PROJET_A
cat > ge-egress.yaml <<FIN
name: ge-egress
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
- //agentregistry.googleapis.com/projects/$PROJET_A/locations/$REGION
FIN
gcloud network-services agent-gateways import ge-egress --location=$REGION --source=ge-egress.yaml --project=$PROJET_A
```

**Étape 3. Autoriser le passage**, pour le compte de Gemini Enterprise : `roles/iap.egressor` sur l'entrée du registre
(console → 🔎 « Agent Registry » → `traduction-equipe-x` → **Autorisations** → **Ajouter un compte principal** → `$GE_SA`
→ rôle **IAP-secured Egressor**), et `roles/run.invoker` sur le service Cloud Run de X (déjà posé par la partie 12).

**Étape 4. Relier la passerelle à l'app** : console → Gemini Enterprise → l'app → **Sécurité** → **Configuration** →
*Agent Gateway* : `projects/aiml-gemini-entreprise-ldbr/locations/europe-west1/agentGateways/ge-egress` → **Enregistrer**.

> **À décider avec la sécurité avant de le faire :** à partir de là, **tout** le trafic de l'app (y compris vers le modèle)
> passe par la passerelle. Un droit `iap.egressor` manquant bloque le chat. Pour revenir en arrière : retirer la liaison.

**Étape 5. Importer** : l'app → **Agents** → **+ Ajouter un agent** → **Agents depuis Agent Registry** → choisir
« Traduction (équipe X) » → **Ajouter un agent** → vérifier → **Suivant** → identifiants si demandés → **Terminer**. Puis
**Agent User** pour le groupe (partie 10).

**Retirer la déclaration :** `gcloud agent-registry services delete traduction-equipe-x --location=$REGION --project=$PROJET_A`

### 17.2 Agent personnalisé via Dialogflow

Pour un agent conversationnel **Dialogflow CX** (flux, pages, intentions), sans code Python.

1. **Créer l'agent** : console du projet (de préférence **A**, voir ci-dessous) → 🔎 « Conversational Agents » →
   **Créer un agent** → région `eu` ou `europe-west1` → construire et tester l'agent dans le simulateur de Dialogflow.
2. **Noter sa ressource** : paramètres de l'agent → `projects/PROJET/locations/LOCATION/agents/ID_AGENT`.
3. **L'ajouter** : l'app → **Agents** → **+ Ajouter un agent** → **Agent personnalisé via Dialogflow** → **Ajouter** →
   **Nom de votre agent**, **Décrivez votre agent**, **Source de l'agent Dialogflow** (la ressource) → **Créer**.
4. **Agent User** pour le groupe, puis test dans le chat (partie 10).

**Agent Dialogflow dans un autre projet que l'app :** Google ne documente pas le droit à donner. Créez de préférence
l'agent Dialogflow **dans le projet de l'app**. Pour un autre projet, piste à valider : donner `roles/dialogflow.client`
au compte de Gemini Enterprise dans ce projet :

```bash
gcloud projects add-iam-policy-binding $PROJET_X --condition=None --role=roles/dialogflow.client --member=serviceAccount:$GE_SA
```

### 17.3 Agents via Marketplace

Pour un agent d'éditeur **acheté** (service achats) sur Google Cloud Marketplace : l'app → **Agents** → **+ Ajouter un
agent** → **Agents via Marketplace** → choisir l'agent → **Suivant** → vérifier → **Suivant** → identifiants de l'éditeur →
**Terminer**. L'agent tourne chez l'éditeur : avis de la sécurité et du DPO avant l'achat.
