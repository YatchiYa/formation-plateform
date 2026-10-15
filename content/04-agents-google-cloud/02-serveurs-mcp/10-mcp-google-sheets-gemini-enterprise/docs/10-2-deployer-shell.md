# 10-2. Tout déployer avec le script (`deployer.sh`), pas à pas

**Ce guide répond à :** comment déployer le serveur MCP et l'agent depuis un terminal Mac ou Linux, sans Docker,
une étape à la fois, en sachant à chaque fois ce qui est créé et ce qu'on doit voir ?

Équivalents : Terraform [10-3](10-3-deployer-terraform.md), console [10-4](10-4-deployer-console.md).
Branchement sur Gemini Enterprise : [10-5](10-5-gemini-enterprise-connecteur-mcp-natif.md) (connecteur) et
[10-6](10-6-agent-adk-mcp-gemini-enterprise.md) (agent).

> **Testé en vrai (14 octobre 2026)**, sur deux projets neufs (agents et app), dans cet ordre :
> `verifier`, `preparer`, `mcp`, `agent`, `agent-runtime`, `registre`, `droits-app`, `tester`, `nettoyer`.
> Résultats réels dans chaque partie.
>
> `autorisation` et `ajouter-app` demandent une app Gemini Enterprise : ils n'ont pas été lancés. Ils envoient le
> format validé au projet 09.

---

## Sommaire

0. [Avant de commencer](#0-avant-de-commencer)
1. [La configuration](#1-la-configuration)
2. [`verifier` : lecture seule](#2-verifier--lecture-seule)
3. [`preparer` : API et comptes](#3-preparer--api-et-comptes)
4. [`mcp` : le serveur MCP](#4-mcp--le-serveur-mcp)
5. [`agent` et `agent-runtime` : l'agent](#5-agent-et-agent-runtime--lagent)
6. [`registre` : Agent Registry](#6-registre--agent-registry)
7. [`fiche` : ce qu'on saisit dans Gemini Enterprise](#7-fiche--ce-quon-saisit-dans-gemini-enterprise)
8. [`droits-app`, `autorisation`, `ajouter-app` : côté app](#8-droits-app-autorisation-ajouter-app--côté-app)
9. [`tester`](#9-tester)
10. [`nettoyer`](#10-nettoyer)
11. [Les mêmes étapes, commande par commande](#11-les-mêmes-étapes-commande-par-commande)

---

## 0. Avant de commencer

| Il faut | Comment vérifier |
|---|---|
| `gcloud` connecté | `gcloud auth login` puis `gcloud auth list` (une étoile sur votre compte) |
| Le projet des agents **avec facturation** | `./scripts/deployer.sh verifier` (partie 2) |
| Vos droits | `verifier` les liste ; à défaut, demander les rôles affichés |
| Le **client OAuth** déjà créé (son ID) | [10-5, étape 1](10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-1--le-client-oauth-console-projet-des-agents) : le serveur refuse de démarrer sans |
| Python 3 | `python3 --version` (pour la fiche et Agent Runtime : bibliothèque standard seulement) |

## 1. La configuration

Ouvrez `config/10-mcp.env`. Les valeurs du projet des agents Acme y sont déjà ; l'app peut rester vide.

| Ligne | Valeur | Où la trouver |
|---|---|---|
| `PROJET` / `NUM_PROJET` | `aiml-gemini-ent-exp-0zga` / `433175138344` | Console → sélecteur de projet |
| `REGION` | `europe-west1` | App en `eu` → région `europe-*` |
| `OAUTH_CLIENT_IDS` | `…apps.googleusercontent.com` | Le client OAuth créé en 10-5, étape 1 |
| `ALLOWED_DOMAINS` | `acme.example` | Les comptes acceptés |
| `PROJET_APP`, `NUM_APP`, `APP_ID` | vide pour l'instant | Seulement pour les actions « côté app » |

Puis, dans le terminal, **dans le dossier du projet 10** :
```bash
source scripts/config.sh config/10-mcp.env
```
**Résultat obtenu :**
```
== Configuration chargée : config/10-mcp.env
   Projet (MCP + agent)  : aiml-gemini-ent-exp-0zga (n° 433175138344), région europe-west1
   Serveur MCP           : https://sheets-mcp-433175138344.europe-west1.run.app/mcp
   Agent A2A             : https://sheets-agent-433175138344.europe-west1.run.app
   App Gemini Enterprise : (pas encore)
   Clients OAuth acceptés: (AUCUN : le serveur MCP refusera de démarrer ; docs/10-5, étape 1)
   Domaines acceptés     : acme.example
```
Les adresses sont **connues d'avance** : Cloud Run les forme avec le numéro du projet et la région.

**Sans toucher au fichier** (par exemple pour les valeurs de prod de l'app), donnez-les devant la commande :
```bash
PROJET_APP=acme-gemini-prod NUM_APP=523307489860 APP_ID=gemini-enterprise-app \
  source scripts/config.sh config/10-mcp.env
```

## 2. `verifier` : lecture seule

```bash
./scripts/deployer.sh verifier
```
Ne change **rien**. Il vérifie :
- le compte connecté ;
- la **facturation** du projet ;
- les API ;
- vos droits (en comptant ceux reçus par un groupe) ;
- ce qui est déjà déployé.

**Résultat obtenu** (projet de test, facturation fermée) :
```
== Facturation de second-pr-511015 : DÉSACTIVÉE (False)
   !! Sans facturation : Cloud Run, Cloud Build, Vertex AI et Agent Runtime refusent.
== API
   OK       run
   …
== Vos droits sur second-pr-511015 (groupes compris)
   OK       activer les API
   OK       créer les comptes de service
   …
   OK       Agent Registry (facultatif)
== Déjà là
   (pas de service sheets-mcp)
   (pas de service sheets-agent)
   Agent Runtime : (aucun)
!! OAUTH_CLIENT_IDS vide : créez le client OAuth (docs/10-5, étape 1) avant « mcp ».
```
Une ligne `MANQUANT … -> demander roles/…` dit précisément quel rôle demander.

## 3. `preparer` : API et comptes

```bash
./scripts/deployer.sh preparer
```
| Créé | Pourquoi |
|---|---|
| API : Cloud Run, Cloud Build, Artifact Registry, IAM, Logging, **Sheets**, **Drive**, Vertex AI (+ Agent Registry si autorisé) | Sheets et Drive sont appelées **au nom des utilisateurs** ; leurs quotas comptent sur ce projet |
| `sheets-build-sa` + `storage.objectViewer`, `artifactregistry.writer`, `logging.logWriter` | Cloud Build construit les images avec ce compte (le compte par défaut n'a souvent pas ces droits, vu au projet 09) |
| `sheets-mcp-sa`, **sans aucun rôle** | Le serveur n'agit qu'avec le jeton de l'utilisateur |
| `sheets-agent-sa` + `aiplatform.user`, `logging.logWriter` | L'agent appelle Gemini et écrit ses journaux |

**Résultat obtenu** (projet neuf, extrait) :
```
▶ gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com run.googleapis.com … --project=second-project-511608
Operation "operations/acf.p2-872505552973-…" finished successfully.
▶ gcloud iam service-accounts create sheets-build-sa …
  sheets-build-sa : roles/storage.objectViewer
  sheets-build-sa : roles/artifactregistry.writer
  sheets-build-sa : roles/logging.logWriter
▶ gcloud iam service-accounts create sheets-mcp-sa …
▶ gcloud iam service-accounts create sheets-agent-sa …
  sheets-agent-sa : roles/aiplatform.user
  sheets-agent-sa : roles/logging.logWriter
Prêt. Attendez 1 à 2 minutes (droits des nouveaux comptes), puis : ./scripts/deployer.sh mcp
``` Relancer est sans danger : vous verrez `compte … : existe déjà`.

## 4. `mcp` : le serveur MCP

> **Sheets et Slides.** `./scripts/deployer.sh mcp` construit **une** image et déploie **deux** services :
> `sheets-mcp` et `slides-mcp` (variable `PRODUIT`). `./scripts/deployer.sh mcp sheets` : seulement Sheets.
> Slides : [10-13](10-13-serveur-mcp-google-slides.md). Ci-dessous, l'exemple de Sheets.

```bash
./scripts/deployer.sh mcp
```
Le script lance :
```bash
gcloud artifacts repositories create sheets-mcp --repository-format=docker --location=europe-west1 …   # 1re fois
gcloud builds submit mcp_server --config=cloudbuild.yaml --substitutions=_IMAGE=europe-west1-docker.pkg.dev/…/sheets-mcp/sheets-mcp:<date> \
  --region=europe-west1 --project=… --service-account=projects/…/serviceAccounts/sheets-build-sa@…
gcloud run deploy sheets-mcp --image=<la même image> --region=europe-west1 --project=… --service-account=sheets-mcp-sa@… \
  --no-allow-unauthenticated --env-vars-file=<OAUTH_CLIENT_IDS, ALLOWED_DOMAINS> \
  --memory=512Mi --cpu=1 --min-instances=0 --max-instances=5 --timeout=120 --quiet
```
- `gcloud builds submit mcp_server` : le dossier est envoyé à **Cloud Build**, qui construit l'image avec le
  `Dockerfile`, comme au projet 09. Vous n'avez pas besoin de Docker sur votre poste. `cloudbuild.yaml` envoie les
  journaux vers Cloud Logging, ce qui est obligatoire avec un compte de construction dédié.
- `--no-allow-unauthenticated` : le service est **privé**. Il faut `roles/run.invoker` pour l'appeler.
- Les variables passent par un fichier (`--env-vars-file`), parce que `OAUTH_CLIENT_IDS` peut contenir des virgules.

**Résultat obtenu** (2 minutes en tout ; construction : 39 s) :
```
ID                                    CREATE_TIME                DURATION  …  IMAGES                                                                       STATUS
043e5fa0-…                            2026-10-14T08:09:41+00:00  39S       …  europe-west1-docker.pkg.dev/second-project-511608/sheets-mcp/sheets-mcp:…   SUCCESS
Service [sheets-mcp] revision [sheets-mcp-00001-brp] has been deployed and is serving 100 percent of traffic.
Service URL: https://sheets-mcp-872505552973.europe-west1.run.app
Serveur MCP : https://sheets-mcp-872505552973.europe-west1.run.app/mcp (privé : sans droit run.invoker, Cloud Run répond 403).
```
Chez Acme, l'adresse sera `https://sheets-mcp-433175138344.europe-west1.run.app/mcp`.
Le premier déploiement crée aussi le dépôt d'images `sheets-mcp` (Artifact Registry).

**Vérifier tout de suite :**
```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST $MCP_URL     # 403 attendu : privé
```

**Changer les clients OAuth acceptés** (par exemple pour ajouter celui de l'agent) : modifiez `OAUTH_CLIENT_IDS`,
rechargez la configuration, relancez `mcp`. Cela crée une nouvelle révision, à la même adresse.

## 5. `agent` et `agent-runtime` : l'agent

**Sur Cloud Run (A2A) :**
```bash
./scripts/deployer.sh agent
```
- Cloud Build construit l'image de `agent/` ;
- le service `sheets-agent` reçoit ses variables : `MCP_URL`, `AGENT_URL`, `AUTH_ID`, `MODEL`, `GOOGLE_CLOUD_PROJECT` ;
- le script donne ensuite à `sheets-agent-sa` le droit **d'appeler le serveur MCP** (`run.invoker` sur `sheets-mcp`).

**Résultat obtenu** (construction : 1 min 06) :
```
… europe-west1-docker.pkg.dev/second-project-511608/sheets-mcp/sheets-agent:…  SUCCESS
Service URL: https://sheets-agent-872505552973.europe-west1.run.app
  serviceAccount:sheets-agent-sa@second-project-511608.iam.gserviceaccount.com : roles/run.invoker sur sheets-mcp
Agent A2A : https://sheets-agent-872505552973.europe-west1.run.app   carte : ./scripts/deployer.sh fiche
```
Au 1er essai, le conteneur ne démarrait pas : `ImportError: cannot import name 'McpToolset'`. `google-adk`
n'installe pas le client `mcp` tout seul. Il est maintenant dans `agent/requirements.txt`. Si vous voyez
« container failed to start », lisez les journaux du service (Cloud Run → `sheets-agent` → **Logs**).

**Sur Agent Runtime :**
```bash
./scripts/deployer.sh agent-runtime
```
- Envoie le code de `agent/` à Agent Runtime (pas d'image), avec le même compte `sheets-agent-sa` ;
- `AUTH_ID=acces-sheets-runtime` : sur Agent Runtime, l'autorisation contient en plus la portée `cloud-platform`
  ([10-6](10-6-agent-adk-mcp-gemini-enterprise.md)).

**Résultat obtenu** (3 min 40) :
```
opération : projects/100000000004/locations/europe-west1/reasoningEngines/3950050498366668800/operations/…
  en cours… 0 s
  …
  en cours… 220 s
déployé : projects/100000000004/locations/europe-west1/reasoningEngines/3950050498366668800
```
C'est le chemin à coller dans l'app.

Pas de doublon : relancé, le script affiche `déjà déployé : …`. Pour une nouvelle version : `nettoyer`, puis relancer.

## 6. `registre` : Agent Registry

```bash
./scripts/deployer.sh registre
```
1. `scripts/gen_toolspec.py` fabrique `terraform/toolspec.json`, la liste des 17 outils, **depuis le code**.
   **Résultat obtenu :** `terraform/toolspec.json : 17 outils, 6917 octets (maximum Agent Registry : 10 Ko)`.
2. `gcloud agent-registry services create sheets-mcp --mcp-server-spec-type=tool-spec --interfaces=url=$MCP_URL,protocolBinding=jsonrpc …`.
3. La liste des serveurs MCP du registre.

**Résultat obtenu :**
```
Created service [sheets-mcp].
DISPLAY_NAME         NAME
Google Sheets (MCP)  agentregistry-00000000-0000-0000-54c7-0952cef8d6eb
```
Au 1er essai, Agent Registry a refusé : `invalid MCP tool spec content: tools.0: inputSchema is required`. Le schéma
des paramètres est maintenant inclus, en compact, sous la limite de 10 Ko.

Détails : [10-7](10-7-agent-registry-mcp.md). Si l'organisation bloque Agent Registry, l'étape est **facultative**.

## 7. `fiche` : ce qu'on saisit dans Gemini Enterprise

```bash
./scripts/deployer.sh fiche
```
Affiche, pour chaque modalité, **tous** les champs de la console :
- le connecteur natif (URL, OAuth, PKCE, portées, domaines de sortie, droit) ;
- l'agent A2A (la carte sur une ligne, l'autorisation) ;
- l'agent Agent Runtime (le chemin, l'autorisation avec `cloud-platform`).

Elle ne crée rien.

**Résultat obtenu** (extrait) :
```
================ Modalité 1 : connecteur natif « Custom MCP Server » (docs/10-5) ================
Console : Gemini Enterprise → Data stores → Create data store → « Custom MCP Server » → Add MCP server
     Authentication        : OAuth 2.0
     MCP Server URL        : https://sheets-mcp-433175138344.europe-west1.run.app/mcp
     Authorization URL     : https://accounts.google.com/o/oauth2/v2/auth
     Auth URL parameters   : access_type=offline&prompt=consent&hd=acme.example
     Token URL             : https://oauth2.googleapis.com/token
     Enable PKCE           : coché
     Scopes                : openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly
     …
================ Modalité 2 : agent A2A sur Cloud Run (docs/10-6) ================
  1. Carte, TOUTE la ligne :
     {"protocolVersion": "0.3", "name": "sheets_agent", …}
  2. Nom : Assistant Google Sheets (A2A)
  3. Authentication (ne PAS cliquer Skip) :
     Nom de l'autorisation : acces-sheets
     Authorization URL     : https://accounts.google.com/o/oauth2/auth?client_id=…&access_type=offline&prompt=consent
     …
```

## 8. `droits-app`, `autorisation`, `ajouter-app` : côté app

Ces actions demandent les valeurs de l'app : `NUM_APP`, et pour les deux dernières `PROJET_APP` et `APP_ID`.

| Action | Fait | Confirmation |
|---|---|---|
| `droits-app` | Affiche le plan, puis donne au compte de l'app : ① `run.invoker` sur `sheets-mcp` (et `sheets-agent` s'il existe), ② `discoveryengine.serviceAgent` sur le projet (si un agent Agent Runtime existe) | Taper l'ID du projet (ou `--oui`) |
| `autorisation client_secret.json [a2a\|runtime]` | Crée l'autorisation OAuth de l'agent dans l'app, avec le nom affiché « Google Sheets » et les bonnes portées | – |
| `ajouter-app [a2a\|runtime]` | Ajoute l'agent à l'app **avec** son autorisation, les questions proposées et la langue `fr`. Ne crée pas de doublon | – |

**Résultat obtenu** (`droits-app --oui`, compte d'un **autre** projet, celui de l'app) :
```
Plan, pour le compte de l'app service-100000000005@gcp-sa-discoveryengine.iam.gserviceaccount.com :
  ① roles/run.invoker sur sheets-mcp        (connecteur « Custom MCP Server »)
  ① roles/run.invoker sur sheets-agent      (agent A2A)
  ② roles/discoveryengine.serviceAgent sur le projet second-project-511608 (agent Agent Runtime)
  serviceAccount:service-100000000005@… : roles/run.invoker sur sheets-mcp
  serviceAccount:service-100000000005@… : roles/run.invoker sur sheets-agent
  service-100000000005 : roles/discoveryengine.serviceAgent
```
Le compte de l'app n'existe qu'une fois **Gemini Enterprise activé** dans le projet de l'app. C'est le cas chez
Acme. Sur un projet de test : `gcloud services enable discoveryengine.googleapis.com` puis
`gcloud beta services identity create --service=discoveryengine.googleapis.com --project=<projet de l'app>`.

Le connecteur natif (chemin 1) n'a **pas d'API publique** : il se crée dans la console ([10-5](10-5-gemini-enterprise-connecteur-mcp-natif.md)).

## 9. `tester`

```bash
export USER_TOKEN=<jeton utilisateur avec la portée Sheets>   # 10-8, partie 2
export SPREADSHEET_ID=<classeur que ce compte peut modifier>
./scripts/deployer.sh tester
```
Le script fait 4 tests :
1. **Sans jeton**, il vérifie que Cloud Run répond `403`.
2. **Le serveur MCP** est appelé **avec les deux en-têtes** du connecteur, et les 17 outils sont lancés sur le vrai
   classeur (`tests/test_reel.py`).
3. **L'agent A2A** reçoit une question, comme le ferait Gemini Enterprise.
4. **L'agent Agent Runtime** reçoit une question, avec le jeton dans `authorizations`.

Le serveur doit accepter le client OAuth qui a émis le jeton de test ([10-8](10-8-tester-simuler-verifier.md)).

**Résultat obtenu** (Cloud Run, 14 octobre 2026) :
```
== 1. Sans aucun jeton : Cloud Run doit refuser (403)
   403
== 2. Le serveur MCP, comme le connecteur de Gemini Enterprise (2 en-têtes), les 17 outils sur le vrai classeur
tools/list : 17 outils
whoami                : sheets-utilisateur-test@second-project-511608.iam.gserviceaccount.com
…
batch_update (tri)    : [['Vélo', 299, 358.8], ['Tente', 149, 178.8], ['Sac', 39, 46.8]]
…
delete_sheet          : test-mcp-101100-r (classeur rendu intact)
OK : test réel terminé
== 3. L'agent A2A, comme Gemini Enterprise
état : completed
Le classeur se nomme « MCP Sheets - test Acme (projet 10) ». Liste des onglets : Untitled.
3 premières lignes : Produit, Prix, Stock / Vélo, 299, 12 / Tente, 149, 30
== 4. L'agent Agent Runtime, comme Gemini Enterprise
Le stock du Vélo est de 12 unités (au prix de 299 €).
```
L'écriture par l'agent, sur plusieurs tours de conversation : [10-8, partie 4](10-8-tester-simuler-verifier.md#4-sur-cloud-run--comme-gemini-enterprise).

## 10. `nettoyer`

```bash
./scripts/deployer.sh nettoyer
```
1. Affiche l'**inventaire** : services, agent Agent Runtime, entrée Agent Registry, comptes.
2. Demande de taper l'ID du projet.
3. Supprime tout (y compris le dépôt d'images sheets-mcp), en retirant d'abord les rôles des comptes et le
   droit ② du compte de l'app.

**Résultat obtenu** (extrait) :
```
▶ gcloud run services delete sheets-mcp … Deleted service [sheets-mcp].
▶ gcloud run services delete sheets-agent … Deleted service [sheets-agent].
▶ … deployer_agent_runtime.py --supprimer projects/100000000004/…/reasoningEngines/3950050498366668800
supprimé : projects/100000000004/locations/europe-west1/reasoningEngines/3950050498366668800
▶ gcloud agent-registry services delete sheets-mcp … Deleted service [sheets-mcp].
  retiré : roles/aiplatform.user de sheets-agent-sa@…
  …
deleted service account [sheets-build-sa@…]
Deleted repository [sheets-mcp].
Terminé.
```

Les agents et le connecteur **ajoutés dans l'app** se retirent dans la console de l'app ([10-9](10-9-securite-exploitation-depannage.md)).

## 11. Les mêmes étapes, commande par commande

Pour voir chaque commande sans le script (configuration chargée) :
```bash
# preparer
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com iam.googleapis.com \
  logging.googleapis.com sheets.googleapis.com drive.googleapis.com aiplatform.googleapis.com --project=$PROJET
gcloud iam service-accounts create sheets-build-sa --project=$PROJET
for r in storage.objectViewer artifactregistry.writer logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJET --role=roles/$r --member=serviceAccount:$BUILD_SA --condition=None; done
gcloud iam service-accounts create sheets-mcp-sa --project=$PROJET
gcloud iam service-accounts create sheets-agent-sa --project=$PROJET
for r in aiplatform.user logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJET --role=roles/$r --member=serviceAccount:$AGENT_SA --condition=None; done

# mcp (image construite par Cloud Build, puis service)
gcloud artifacts repositories create sheets-mcp --repository-format=docker --location=$REGION --project=$PROJET
IMG=$REGION-docker.pkg.dev/$PROJET/sheets-mcp
gcloud builds submit mcp_server --config=cloudbuild.yaml --substitutions=_IMAGE=$IMG/sheets-mcp:v1 \
  --region=$REGION --project=$PROJET --service-account=projects/$PROJET/serviceAccounts/$BUILD_SA
printf 'OAUTH_CLIENT_IDS: "%s"\nALLOWED_DOMAINS: "%s"\n' "$OAUTH_CLIENT_IDS" "$ALLOWED_DOMAINS" > env-mcp.yaml
gcloud run deploy sheets-mcp --image=$IMG/sheets-mcp:v1 --region=$REGION --project=$PROJET --service-account=$MCP_SA \
  --no-allow-unauthenticated --env-vars-file=env-mcp.yaml

# agent (A2A)
gcloud builds submit agent --config=cloudbuild.yaml --substitutions=_IMAGE=$IMG/sheets-agent:v1 \
  --region=$REGION --project=$PROJET --service-account=projects/$PROJET/serviceAccounts/$BUILD_SA
printf 'MCP_URL: "%s"\nAGENT_URL: "%s"\nAUTH_ID: "%s"\nMODEL: "%s"\nGOOGLE_CLOUD_PROJECT: "%s"\n' \
  "$MCP_URL" "$AGENT_URL" "$AUTH_ID" "$MODEL" "$PROJET" > env-agent.yaml
gcloud run deploy sheets-agent --image=$IMG/sheets-agent:v1 --region=$REGION --project=$PROJET --service-account=$AGENT_SA \
  --no-allow-unauthenticated --env-vars-file=env-agent.yaml --max-instances=1 --memory=1Gi --timeout=300
gcloud run services add-iam-policy-binding sheets-mcp --region=$REGION --project=$PROJET \
  --role=roles/run.invoker --member=serviceAccount:$AGENT_SA

# la carte de l'agent (à coller dans l'app)
python3 agent/carte.py $AGENT_URL
```
