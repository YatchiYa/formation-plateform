# 12-1-1. Déployer les agents dans le projet des agents : méthode **shell** (commandes)

**Le but :** mettre en ligne **un**, **deux** ou **tous** les agents dans le projet des agents
`aiml-gemini-ent-exp-0zga`, les tester, et savoir où les voir dans la console Google Cloud.

**Pas encore d'app Gemini Enterprise.** On ne fait **que** les agents. Les relier à une app viendra plus tard
([12-1, A5 et A6](12-1-agents-projet-exp-vers-app.md#a5-donner-à-lapp-le-droit-dappeler-les-agents)).

**Les autres méthodes, même résultat :** [12-1-2 Terraform](12-1-2-deployer-agents-terraform.md) ·
[12-1-3 Console](12-1-3-deployer-agents-console.md).

> **Agents dans le projet de l'app (cas 12-2) ?** Tout est identique : mettez le projet de l'app dans `PROJET_AGENTS`
> et `NUM_AGENTS`, et utilisez `config/12-2-agents-dans-projet-app.env`.

> **Testé en vrai** (10 octobre 2026, projet de test) : toutes les commandes de ce guide, dans l'ordre, pour l'agent
> `meteo`, puis pour un 2e agent `taille` ajouté ensuite. Cloud Run, Agent Runtime, Agent Registry, tests, puis
> nettoyage. Le 11 octobre : construction des images par **Cloud Build**, sans Docker sur le poste (compte
> `agents-build-sa`), service déployé depuis cette image et testé. Dans les résultats, le nom et le numéro du projet de test sont remplacés par les vôtres.

---

## Sommaire

0. [Les mots à connaître](#0-les-mots-à-connaître)
1. [Ce que vous allez créer, et où le voir](#1-ce-que-vous-allez-créer-et-où-le-voir)
2. [Préparer votre poste (une fois)](#2-préparer-votre-poste-une-fois)
3. [Le fichier de configuration : quoi écrire, ligne par ligne](#3-le-fichier-de-configuration--quoi-écrire-ligne-par-ligne)
4. [Se connecter, vérifier le projet et vos droits](#4-se-connecter-vérifier-le-projet-et-vos-droits)
5. [Vérifier et activer les API](#5-vérifier-et-activer-les-api)
6. [Model Armor : le filtre de sécurité (une fois)](#6-model-armor--le-filtre-de-sécurité-une-fois) — **avant :** [deux façons de faire, avec ou sans script](#deux-façons-de-faire-les-parties-6-à-9)
7. [Cloud Run (A2A) : un agent, puis plusieurs](#7-cloud-run-a2a--un-agent-puis-plusieurs)
8. [Agent Runtime : un agent, puis plusieurs](#8-agent-runtime--un-agent-puis-plusieurs)
9. [Agent Registry : le catalogue des agents](#9-agent-registry--le-catalogue-des-agents)
10. [Dialogflow : un agent conversationnel sans code (option)](#10-dialogflow--un-agent-conversationnel-sans-code-option)
11. [Vérification finale](#11-vérification-finale)
12. [Ajouter un agent plus tard, en retirer un](#12-ajouter-un-agent-plus-tard-en-retirer-un)
13. [Tout nettoyer](#13-tout-nettoyer)
14. [Ce qui peut arriver](#14-ce-qui-peut-arriver)

---

## 0. Les mots à connaître

| Mot | En clair |
|---|---|
| **Projet** | L'espace Google Cloud où tout est créé et facturé. Ici : `aiml-gemini-ent-exp-0zga` (numéro `433175138344`). |
| **Agent** | Un programme Python (dossier `agents/trio/<clé>_agent/`) qui répond aux questions avec Gemini et ses **outils** (des fonctions Python). |
| **Clé d'un agent** | Son nom court : `meteo`, `redaction`, `traduction`, `taille`, `retour`, `identite`. Liste complète : `agents/trio/catalogue.json`. |
| **Cloud Run** | Le service Google qui fait tourner un **conteneur** (une image) et lui donne une adresse `https://…run.app`. |
| **A2A** | *Agent-to-Agent* : le protocole ouvert que parlent nos agents sur Cloud Run (celui que Gemini Enterprise utilise). |
| **Carte d'agent** | Un petit JSON qui décrit l'agent : nom, description, adresse, compétences. Servie par l'agent sur `/.well-known/agent-card.json`. |
| **Image** | Le paquet « code + Python + bibliothèques » que Cloud Run fait tourner. Rangée dans **Artifact Registry**. |
| **Agent Runtime** | L'hébergement **géré** d'agents de Google (dans Vertex AI). On lui envoie le code ; il gère tout, sessions comprises. |
| **Agent Registry** | Le **catalogue** des agents du projet : qui existe, où, ce qu'il sait faire. |
| **Dialogflow** | Un agent **conversationnel** construit à la souris (sans Python). |
| **Model Armor** | Le filtre de sécurité : bloque injections, contenus dangereux, liens malveillants, dans les questions **et** les réponses. |
| **Compte de service** | L'identité d'un agent (comme un compte utilisateur, mais pour un programme). Un par agent. |
| **Rôle** | Un droit donné à un compte : `roles/aiplatform.user` = « peut appeler Gemini ». |
| **API** | Un service Google à **activer** dans le projet avant de s'en servir (Cloud Run, Vertex AI…). |

---

## 1. Ce que vous allez créer, et où le voir

```
 Votre poste                          Projet des agents aiml-gemini-ent-exp-0zga
 ┌───────────────────┐               ┌───────────────────────────────────────────────────────────────┐
 │ agents/trio/      │  image        │ Artifact Registry  agents-shell/meteo:v1                       │
 │   meteo_agent/    │ ────────────▶ │ Cloud Run          meteo-a2a-shell   (privé, protocole A2A)    │
 │   taille_agent/   │               │   identité         meteo-a2a-shell-sa                          │
 │   commun.py       │  code         │ Agent Runtime      meteo-shell       (hébergement géré)        │
 │ config/…env       │ ────────────▶ │   identité         meteo-shell-sa                              │
 └───────────────────┘               │ Agent Registry     les agents ci-dessus (catalogue)            │
                                     │ Model Armor        agents-prompt-shield, agents-response-shield│
                                     └───────────────────────────────────────────────────────────────┘
```

**Deux façons d'héberger un agent.** Faites l'une, l'autre ou les deux (les noms ne se gênent pas) :

| | **Cloud Run (A2A)** | **Agent Runtime** |
|---|---|---|
| C'est quoi | Votre conteneur, sur l'hébergement « serveur » de Google | L'hébergement d'agents géré par Google |
| Ce qui est créé **par agent** | Une image, un compte de service + 3 rôles, un service Cloud Run, une entrée Agent Registry | Un compte de service + 3 rôles, un agent Agent Runtime (inscrit **seul** dans Agent Registry) |
| Nom (agent `meteo`) | `meteo-a2a-shell` | `meteo-shell` |
| Pour Gemini Enterprise, plus tard | Mode « Agent personnalisé via A2A » | Mode « Agent personnalisé via Agent Runtime » |
| Durée de déploiement | 3 à 5 min (construction de l'image) | 3 à 5 min |

**Où le voir dans la console** ([console.cloud.google.com](https://console.cloud.google.com), projet
`aiml-gemini-ent-exp-0zga` choisi en haut) : tapez le nom dans la barre de recherche 🔎.

| Quoi | 🔎 Rechercher | Puis |
|---|---|---|
| Les API activées | « API et services » | **API et services activés** |
| Les comptes de service | « Comptes de service » | La liste ; un clic → onglet **Autorisations** |
| Les rôles donnés | « IAM » | Filtrer sur le nom du compte |
| Les filtres Model Armor | « Model Armor » | **Templates**, région `eu` |
| Les constructions d'images | « Cloud Build » | **Historique**, région `europe-west1` : chaque construction et son journal |
| Les images | « Artifact Registry » | Dépôt `agents-shell` → une image par agent |
| Les agents Cloud Run | « Cloud Run » | **Services** → `meteo-a2a-shell` → URL, **Révisions**, **Journaux**, **Sécurité** |
| Les agents Agent Runtime | « Agent Runtime » | **Déploiements** → `meteo-shell` → **Playground** (tester), **Sessions**, **Journaux** |
| Le catalogue | « Agent Registry » | Région `europe-west1` → la liste des agents |
| Dialogflow | « Conversational Agents » | L'agent → **Tester l'agent** |
| Les erreurs | « Journaux » (Logs Explorer) | Filtrer par service |

---

## 2. Préparer votre poste (une fois)

| Outil | Installer (Mac, Homebrew) | Vérifier |
|---|---|---|
| gcloud (la ligne de commande Google Cloud) | `brew install --cask google-cloud-sdk` puis `gcloud components install beta` | `gcloud version` |
| uv (Python 3.12 à 3.14) | `brew install uv` | `uv --version` |

**Pas besoin de Docker.** Les images des agents sont construites **dans Google Cloud** (Cloud Build) : votre poste
envoie seulement le code (quelques dizaines de Ko). Tout se fait depuis un terminal Linux ou Mac, ou depuis Cloud
Shell (le terminal intégré à la console). Sur Linux, gcloud s'installe avec le guide officiel « Install the gcloud
CLI » (paquet `google-cloud-cli`) ; uv avec `curl -LsSf https://astral.sh/uv/install.sh | sh`.

Le dossier du projet et son Python :

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/trio/requirements.txt
python scripts/test_trio.py
```

**Résultat obtenu :** `tests trio OK (9 scénarios, 6 agents)`. Votre invite commence par `(.venv)` : c'est le Python
du projet. Dans **chaque nouveau terminal**, refaites `cd …` et `source .venv/bin/activate`.

**Quelle version de Python ?** **3.12, 3.13 ou 3.14** (testé : 3.12 et 3.14.6, tests et serveur A2A compris).
`-p '>=3.12'` prend celle **déjà installée** sur votre poste, sans rien télécharger. Les apostrophes sont nécessaires
(sinon le terminal lit `>` comme une redirection). Les agents déployés, eux, tournent toujours en Python 3.12 (image
Cloud Run, Agent Runtime) : votre version locale n'y change rien.

**Mac Acme : `Failed building wheel for watchdog` (`unknown architecture arm64e.x1-macos`)**

`google-adk` demande le paquet `watchdog`. Pour Python 3.14 sur Mac, il n'existe pas en version déjà compilée, et sa
compilation échoue avec les outils du poste. On ne peut rien y changer, mais on n'en a **pas besoin** : il ne sert qu'à
`adk web`. Installez la liste prête, **sans `watchdog`** (mêmes paquets, versions figées, tous déjà compilés pour Mac et
Python 3.14 : rien n'est construit) :

```bash
rm -rf .venv
python3 -m venv .venv && source .venv/bin/activate
pip install --no-deps -r agents/trio/requirements-poste.txt
python scripts/test_trio.py
```

**Résultat obtenu** (Python 3.14, `python -m venv`, `pip`) : `tests trio OK (9 scénarios, 6 agents)`. Les scripts, le
serveur A2A et `adk run` fonctionnent ; seul `adk web` a besoin de `watchdog`. Pour tester un agent sur le poste, à la
place de `adk web` :

```bash
cd agents/trio && PROMPT_TEMPLATE= RESPONSE_TEMPLATE= LOCAL_DEV=1 adk run taille_agent
```

**Résultat obtenu :** `Running agent taille_agent, type exit to exit.`, puis vous tapez votre question ; réponse
`[taille_agent]: Pour votre tour de poitrine de 98 cm, je vous conseille une veste en taille M…`. `exit` pour quitter.
Le déploiement n'est pas concerné : Cloud Run et Agent Runtime utilisent `requirements.txt` dans Google Cloud.

**Si l'installation ne démarre pas, ou bloque (réseau d'entreprise) :**

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `uv venv` reste bloqué, ou `Downloading cpython-3.12…` sans fin | Il cherche à **télécharger** un Python (ancienne commande `-p 3.12`, alors que vous avez 3.14), et le réseau le bloque | `uv venv -p '>=3.12' .venv` (prend votre Python) ; ou sans uv : `python3 -m venv .venv` |
| `invalid peer certificate: UnknownIssuer`, `certificate verify failed` | Le proxy de l'entreprise inspecte le trafic (certificat interne) | `uv pip install --native-tls -r agents/trio/requirements.txt` (utilise les certificats du système) ; ou `export UV_NATIVE_TLS=1` |
| `Failed to fetch …` / délai dépassé vers `pypi.org` | Accès direct à PyPI interdit, miroir interne obligatoire | `uv pip install --index-url <URL du miroir PyPI interne> -r agents/trio/requirements.txt` (demander l'URL à l'équipe poste de travail / Artifactory) ; ou `export UV_INDEX_URL=…` |
| `Building wheel for … failed` | Pas de paquet tout prêt pour votre version de Python ou votre machine | Essayer `uv venv -p 3.12 .venv` si 3.12 est installé (`brew install python@3.12`), puis réinstaller |
| `command not found: uv` | uv absent | `brew install uv`, ou sans uv : `python3 -m venv .venv && source .venv/bin/activate && pip install -r agents/trio/requirements.txt` |

L'erreur exacte est la dernière ligne rouge affichée : elle dit laquelle de ces situations est la vôtre.

---

## 3. Le fichier de configuration : quoi écrire, ligne par ligne

Toutes les commandes lisent leurs valeurs dans **un seul fichier** : `config/12-1-agents-dans-projet-exp.env`.
Ouvrez-le dans un éditeur (VS Code, TextEdit…) et remplissez-le **ainsi** :

```bash
# Projet de l'app Gemini Enterprise : PAS ENCORE D'APP -> on laisse vide
PROJET_APP=
NUM_APP=
APP_ID=
GE_LOCATION=eu

# Projet des agents
PROJET_AGENTS=aiml-gemini-ent-exp-0zga
NUM_AGENTS=433175138344
REGION=europe-west1

# Les agents à déployer
AGENTS="meteo"

PUBLIER=non
AGENTS_OAUTH=""
GROUPE_UTILISATEURS=
DOSSIER=~/Desktop/09-agents-multi-projets-gemini-enterprise
```

| Ligne | Ce que c'est | Où le trouver | Ici |
|---|---|---|---|
| `PROJET_APP`, `NUM_APP`, `APP_ID` | Le projet et l'app Gemini Enterprise | — | **Vides** (pas encore d'app) |
| `GE_LOCATION` | Où vivent les filtres Model Armor (et plus tard l'app) : `eu`, `us` ou `global` | — | `eu` |
| `PROJET_AGENTS` | L'**ID** du projet des agents (pas son nom affiché) | Console → sélecteur de projet en haut → colonne **ID** | `aiml-gemini-ent-exp-0zga` |
| `NUM_AGENTS` | Son **numéro** | Même écran, colonne **Numéro**, ou **Accueil** → *Informations sur le projet* | `433175138344` |
| `REGION` | Où tournent les agents. Doit aller avec `GE_LOCATION` : `eu` → `europe-…` | — | `europe-west1` |
| `AGENTS` | **Quels agents** déployer : leurs clés, séparées par des espaces. **Vide = tous** | `agents/trio/catalogue.json` | `"meteo"` (un seul) |
| `PUBLIER` | Ajouter les agents à l'app ? | — | `non` (pas d'app) |
| `AGENTS_OAUTH` | Agents qui agissent avec le compte de l'utilisateur ([12-3, partie C](12-3-ajouter-des-agents-un-par-un.md#7-partie-c--outils-avec-le-compte-de-lutilisateur-oauth)) | — | `""` |
| `GROUPE_UTILISATEURS` | Le groupe qui utilisera les agents dans l'app | — | vide pour l'instant |
| `DOSSIER` | Où est le dossier sur votre poste | — | le chemin du dossier |

**Exemples pour `AGENTS` :**

| Vous voulez | Écrivez |
|---|---|
| un seul agent | `AGENTS="meteo"` |
| deux agents | `AGENTS="meteo taille"` |
| certains | `AGENTS="meteo traduction retour"` |
| tous les agents du catalogue | `AGENTS=""` |

**Charger la configuration dans le terminal** (à refaire dans chaque nouveau terminal, et après chaque modification du
fichier) :

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

**À vérifier :** la dernière ligne est `OK`, et « Agents à déployer » montre vos agents. Sinon le script dit quoi
corriger, par exemple `ATTENTION : agent « metoe » absent de agents/trio/catalogue.json` (faute de frappe).

**Ce que fait ce script :** il crée dans le terminal des **variables** (`$PROJET_AGENTS`, `$REGION`,
`$AGENTS_LISTE`…) que les commandes suivantes utilisent. `$AGENTS_LISTE` = vos agents (ou tous si `AGENTS` est vide).
**Toujours avec `source`**, jamais derrière un `|` : sinon les variables disparaissent.

---

## 4. Se connecter, vérifier le projet et vos droits

```bash
gcloud auth login                        # ouvre le navigateur : votre compte Google
gcloud auth application-default login    # une 2e fois : pour les scripts Python
gcloud projects describe $PROJET_AGENTS --format='value(projectNumber)'
```

**Résultat attendu :** `433175138344`. Un autre numéro → corriger `NUM_AGENTS`, recharger (`source …`).

**Vos droits** sur le projet des agents :

```bash
gcloud projects get-iam-policy $PROJET_AGENTS --flatten=bindings \
  --filter="bindings.members:user:$(gcloud config get-value account 2>/dev/null)" --format="value(bindings.role)"
```

Il faut `roles/owner`, ou ces rôles : `aiplatform.admin`, `run.admin`, `artifactregistry.admin`,
`iam.serviceAccountAdmin`, `iam.serviceAccountUser`, `resourcemanager.projectIamAdmin`,
`serviceusage.serviceUsageAdmin`, `modelarmor.admin`, `agentregistry.admin`, `cloudbuild.builds.editor`,
`storage.admin` (+ `dialogflow.admin` pour la partie 10).
Un rôle reçu via un **groupe** n'apparaît pas ici : vérifiez dans la console (🔎 « IAM »).

**La vraie vérification (recommandée) :** ce script demande à Google, permission par permission, ce que **vous**
pouvez faire. Il compte aussi les rôles reçus par un groupe et les rôles propres à l'organisation. Lecture seule :

```bash
./scripts/verifier_droits.sh
```

**Résultat obtenu :**

```
== Vos droits sur aiml-gemini-ent-exp-0zga (rôles directs, de groupe et personnalisés compris)
  OK        Activer les API (12-1-1 partie 5)
  OK        Créer les comptes de service des agents
  …
  OK        Déclarer les agents Cloud Run dans Agent Registry (partie 9)
  OK        Agent Dialogflow (partie 10, option)

Tout est en place.
```

Une ligne `MANQUANT` donne le rôle à demander (ex. `→ demander roles/agentregistry.admin`). Pour une étape
optionnelle (Agent Registry, Dialogflow), on peut aussi simplement la passer.

---

## 5. Vérifier et activer les API

Une **API** doit être activée dans le projet avant qu'on s'en serve. Ce script **vérifie** chacune et **active
seulement** celles qui manquent :

```bash
./scripts/verifier_api.sh $PROJET_AGENTS cloudresourcemanager.googleapis.com serviceusage.googleapis.com iam.googleapis.com \
  aiplatform.googleapis.com agentregistry.googleapis.com modelarmor.googleapis.com logging.googleapis.com \
  run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

**Résultat obtenu :**

```
OK        cloudresourcemanager.googleapis.com
OK        serviceusage.googleapis.com
OK        iam.googleapis.com
OK        aiplatform.googleapis.com
OK        agentregistry.googleapis.com
OK        modelarmor.googleapis.com
OK        logging.googleapis.com
OK        run.googleapis.com
OK        artifactregistry.googleapis.com
OK        cloudbuild.googleapis.com
rien à activer
```

S'il en manque : `MANQUANTE cloudbuild.googleapis.com` puis `activées : cloudbuild.googleapis.com` (1 à 2 minutes).
Une API **tout juste activée** peut refuser la première commande (`PERMISSION_DENIED`) : attendez 1 minute et relancez.

| API | À quoi elle sert ici | Nécessaire pour |
|---|---|---|
| `cloudresourcemanager`, `serviceusage` | Lire le projet, activer les autres API | Tout |
| `iam` | Créer les comptes de service, donner des rôles | Tout |
| `aiplatform` | Gemini (le modèle) et Agent Runtime | Tout |
| `modelarmor` | Le filtre de sécurité | Tout |
| `logging` | Les journaux | Tout |
| `agentregistry` | Le catalogue des agents | Agent Registry |
| `run` | Cloud Run | Cloud Run |
| `artifactregistry` | Ranger les images | Cloud Run |
| `cloudbuild` | Construire les images dans Google Cloud (pas de Docker sur votre poste) | Cloud Run |
| `dialogflow` | Dialogflow | Partie 10 seulement |

**Dans la console :** 🔎 « API et services » → **API et services activés** : elles sont dans la liste.

---

## Deux façons de faire les parties 6 à 9

Tout ce qui suit lit le **fichier de configuration** (partie 3) : les agents à déployer sont ceux de la ligne `AGENTS`.

| | **Façon 1 : le script** (le plus simple) | **Façon 2 : les commandes une à une** |
|---|---|---|
| Ce que vous tapez | **Une** commande par étape | Les blocs de commandes ci-dessous |
| Les agents | Ceux de `AGENTS` (ou la clé donnée : `… cloudrun taille`) | Vous les nommez vous-même avec `K=…` dans le terminal |
| Ce que vous voyez | Chaque commande lancée, précédée de `▶` | Les commandes que vous collez |
| Relancer | Sans danger : ce qui existe est gardé, rien n'est créé deux fois | À vous de ne pas recréer |

**Façon 1**, configuration chargée (`source scripts/config.sh …`), dans le dossier du projet :

```bash
./scripts/deployer_shell.sh preparer      # partie 6 et 7.1, une fois : filtres, dépôt d'images, compte de construction
./scripts/deployer_shell.sh cloudrun      # partie 7 : chaque agent de AGENTS sur Cloud Run (image, compte, service)
./scripts/deployer_shell.sh runtime       # partie 8 : chaque agent de AGENTS sur Agent Runtime
./scripts/deployer_shell.sh registre      # partie 9 : déclarer les agents Cloud Run dans Agent Registry
./scripts/deployer_shell.sh tester        # 3 à 5 minutes après : tester tout ce qui est déployé
./scripts/deployer_shell.sh carte         # TOUT ce qu'il faut coller dans Gemini Enterprise : carte-K.json, chemin Agent Runtime…
```

Un seul agent sans toucher au fichier : ajoutez sa clé, ex. `./scripts/deployer_shell.sh cloudrun taille`.

**`carte`** écrit `carte-<clé>.json` (agents Cloud Run, au format Google) et affiche la **fiche** de chaque agent
déployé : nom, description, carte sur une ligne, chemin Agent Runtime, étape Authentification, questions proposées,
droits de l'app. Ne crée rien chez Google. Agents avec OAuth (`oauth`, puis `carte` avec `CLIENT_ID=…`) :
[12-1-8, partie 4 bis](12-1-8-agent-espace-de-travail-multi-oauth.md#4-bis-la-voie-scriptée-de-bout-en-bout).

**Résultat obtenu** (`cloudrun taille`, extrait) :

```
== taille (Cloud Run)   image europe-west1-docker.pkg.dev/aiml-gemini-ent-exp-0zga/agents-shell/taille:v1   adresse https://taille-a2a-shell-433175138344.europe-west1.run.app
-- 1/3 l'image, construite par Cloud Build (environ 1 min 20 s)
▶ gcloud builds submit --region=europe-west1 --project=aiml-gemini-ent-exp-0zga --service-account=… --config=01-bis-cloud-run-a2a/cloudbuild.yaml --substitutions=_AGENT_DIR=taille_agent,_IMAGE=… .
85d9aa15-…  2026-10-11T10:39:13+00:00  1M23S  gs://…  europe-west1-docker.pkg.dev/…/agents-shell/taille:v1  SUCCESS
-- 2/3 son compte de service et ses 3 rôles (Gemini, journaux, Model Armor)
▶ gcloud iam service-accounts create taille-a2a-shell-sa --project=aiml-gemini-ent-exp-0zga --display-name=Agent taille (Cloud Run A2A, méthode shell)
  taille-a2a-shell-sa : roles/aiplatform.user
  taille-a2a-shell-sa : roles/logging.logWriter
  taille-a2a-shell-sa : roles/modelarmor.user
-- 3/3 le service Cloud Run (privé)
▶ gcloud run deploy taille-a2a-shell --image=… --no-allow-unauthenticated --env-vars-file=env-taille.yaml …
Service URL: https://taille-a2a-shell-433175138344.europe-west1.run.app

Attendez 3 à 5 minutes (droits des nouveaux comptes), puis : ./scripts/deployer_shell.sh tester taille
```

Et `tester taille` : `OK : les agents répondent en A2A v0.3, avec mémoire de conversation` (Cloud Run), puis
`-> outil : taille_vetement({'mesure_cm': 98, 'type_vetement': 'haut'})` et la réponse (Agent Runtime).
Relancé une 2e fois : `compte … : existe déjà`, `déjà déployé`, `déjà déclaré` : rien n'est recréé.

Ensuite, la carte de chaque agent pour Gemini Enterprise : [7.6](#76-la-carte-de-lagent-pour-gemini-enterprise).
**Les parties 6 à 9 ci-dessous détaillent ce que fait le script** (façon 2) : à lire pour comprendre, ou à suivre à
la main.

---

## 6. Model Armor : le filtre de sécurité (une fois)

Deux **templates** (modèles de filtre) : un pour les questions, un pour les réponses. Tous les agents les partagent :
on les crée **une fois**, quel que soit le nombre d'agents.

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

**`for T in prompt response; do … done`** est une **boucle** : la commande est lancée deux fois, avec `T=prompt` puis
`T=response`. Elle crée donc `agents-prompt-shield` et `agents-response-shield`.

**Résultat obtenu :**

```
Created template [agents-prompt-shield].
Created template [agents-response-shield].
projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/agents-prompt-shield
projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/agents-response-shield
```

Leurs chemins sont déjà dans `$PROMPT_TEMPLATE` et `$RESPONSE_TEMPLATE` (le script de configuration les a calculés).
Déjà créés (`ALREADY_EXISTS`) ? Rien à faire, passez à la suite.

**Dans la console :** 🔎 « Model Armor » → **Templates** → les deux, région `eu`.

---

## 7. Cloud Run (A2A) : un agent, puis plusieurs

### 7.1 Le dépôt d'images et le compte qui construit (une fois)

Une **image** est le paquet « code + Python + bibliothèques » que Cloud Run fait tourner. On la fait construire par
**Cloud Build**, un service de Google : votre poste envoie le code, Google construit l'image et la range dans un
**dépôt** (Artifact Registry). Il faut donc, une fois :

```bash
gcloud artifacts repositories create agents-shell --repository-format=docker --location=$REGION --project=$PROJET_AGENTS
gcloud iam service-accounts create agents-build-sa --project=$PROJET_AGENTS --display-name="Construction des images des agents (Cloud Build)"
for R in storage.objectViewer artifactregistry.writer logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
    --member=serviceAccount:agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null && echo "  agents-build-sa : roles/$R"
done
```

| Ligne | Ce qu'elle fait |
|---|---|
| `repositories create agents-shell` | Le **dépôt** où ranger les images (`--repository-format=docker` est le format standard des images, pas besoin du logiciel Docker) |
| `service-accounts create agents-build-sa` | Le **compte** qui construit les images. Pourquoi un compte à nous : celui que Cloud Build utilise par défaut n'a souvent aucun droit (vérifié : `… does not have storage.objects.get access`) |
| `storage.objectViewer` | Lire le code que vous envoyez |
| `artifactregistry.writer` | Ranger l'image dans le dépôt |
| `logging.logWriter` | Écrire le journal de construction |

**Résultat obtenu :**

```
Created repository [agents-shell].
Created service account [agents-build-sa].
  agents-build-sa : roles/storage.objectViewer
  agents-build-sa : roles/artifactregistry.writer
  agents-build-sa : roles/logging.logWriter
```

**Attendez 1 à 2 minutes** avant la première construction : les droits d'un compte neuf mettent ce temps à s'appliquer.

### 7.2 Déployer UN agent

Dans le dossier du projet (`cd $DOSSIER`), en changeant seulement la 1re ligne si vous voulez un autre agent :

```bash
K=meteo                                                                    # ← la clé de l'agent
IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K:v1             # où ranger son image
SA=$K-a2a-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com                  # son identité
URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app                       # son adresse, connue d'avance
```

**Où les mettre ?** Nulle part dans un fichier : **copiez-collez ces 4 lignes dans le terminal**, comme les commandes
précédentes, puis Entrée. Elles ne créent rien : elles **nomment** les choses, et les commandes suivantes s'en servent
(`$IMAGE`, `$SA`, `$URL`). Elles disparaissent si vous ouvrez un nouveau terminal : recollez-les alors.

**Vérifiez avant de continuer :**

```bash
echo "K=$K  IMAGE=$IMAGE  URL=$URL"
```

**Attendu :** `K=meteo  IMAGE=europe-west1-docker.pkg.dev/aiml-gemini-ent-exp-0zga/agents-shell/meteo:v1  URL=https://meteo-a2a-shell-433175138344.europe-west1.run.app`.
Si `IMAGE=` est vide, les 4 lignes n'ont pas été collées dans ce terminal (sinon : `invalid image name ""` à l'étape a).

**a) L'image de l'agent**, construite par Cloud Build (code commun + le dossier de CET agent seulement) :

```bash
gcloud builds submit --region=$REGION --project=$PROJET_AGENTS \
  --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
  --config=01-bis-cloud-run-a2a/cloudbuild.yaml --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$IMAGE .
```

| Morceau | Sens |
|---|---|
| `gcloud builds submit … .` | Envoie le dossier courant (le **point** final) à Cloud Build. Le fichier `.gcloudignore` du projet filtre : seul le code des agents part, jamais `.venv` ni l'état Terraform |
| `--region=$REGION` | La construction a lieu en Europe (`europe-west1`) |
| `--service-account=…agents-build-sa…` | Construire avec **notre** compte (7.1) |
| `--config=01-bis-cloud-run-a2a/cloudbuild.yaml` | La recette de construction (elle utilise `01-bis-cloud-run-a2a/Dockerfile`) |
| `_AGENT_DIR=meteo_agent` | Ne mettre **que** cet agent dans l'image |
| `_IMAGE=$IMAGE` | Le nom de l'image, dans le dépôt `agents-shell` |

**Résultat obtenu** (environ 1 min 20 s) :

```
Creating temporary archive of 20 file(s) totalling 61.4 KiB before compression.
Uploading tarball of [.] to [gs://aiml-gemini-ent-exp-0zga_cloudbuild/source/….tgz]
Created [https://cloudbuild.googleapis.com/v1/projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/builds/1092987d-…].
Logs are available at [ https://console.cloud.google.com/cloud-build/builds;region=europe-west1/1092987d-…?project=433175138344 ].
…
ID          CREATE_TIME                DURATION  SOURCE   IMAGES                                                                    STATUS
1092987d-…  2026-10-10T22:22:46+00:00  1M21S     gs://…   europe-west1-docker.pkg.dev/aiml-gemini-ent-exp-0zga/agents-shell/meteo:v1  SUCCESS
```

**À vérifier :** le dernier mot est **`SUCCESS`**. `20 file(s) totalling 61.4 KiB` : seul le code est envoyé.
`FAILURE` : ouvrez le lien `Logs are available at` (ou 🔎 « Cloud Build » → **Historique**) pour lire l'erreur.

**b) Son compte de service et ses 3 rôles :**

```bash
gcloud iam service-accounts create $K-a2a-shell-sa --project=$PROJET_AGENTS --display-name="Agent $K (Cloud Run A2A, méthode shell)"
for R in aiplatform.user logging.logWriter modelarmor.user; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R --member=serviceAccount:$SA >/dev/null \
    && echo "  $K-a2a-shell-sa : roles/$R"
done
```

| Rôle | Pourquoi |
|---|---|
| `aiplatform.user` | Appeler Gemini |
| `logging.logWriter` | Écrire ses journaux |
| `modelarmor.user` | Utiliser les filtres de la partie 6 |

**Résultat obtenu :**

```
Created service account [meteo-a2a-shell-sa].
  meteo-a2a-shell-sa : roles/aiplatform.user
  meteo-a2a-shell-sa : roles/logging.logWriter
  meteo-a2a-shell-sa : roles/modelarmor.user
```

**c) Ses réglages, puis le service :**

```bash
python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml
gcloud run deploy $K-a2a-shell --image=$IMAGE --region=$REGION --project=$PROJET_AGENTS \
  --service-account=$SA --no-allow-unauthenticated --env-vars-file=env-$K.yaml \
  --memory=1Gi --cpu=1 --min-instances=0 --max-instances=1 --quiet
```

La 1re ligne écrit `env-meteo.yaml`, les **variables d'environnement** du service :

| Variable | Valeur | Rôle |
|---|---|---|
| `AGENT` | `meteo_agent` | Quel agent ce service fait tourner |
| `AGENT_CARD` | la carte A2A (JSON), avec `$URL` | Ce que l'agent montre de lui-même |
| `GOOGLE_CLOUD_PROJECT` | `aiml-gemini-ent-exp-0zga` | Où appeler Gemini |
| `MODEL` | `gemini-3.5-flash` | Le modèle |
| `PROMPT_TEMPLATE`, `RESPONSE_TEMPLATE` | les chemins de la partie 6 | Les filtres Model Armor |

| Option de `gcloud run deploy` | Sens |
|---|---|
| `--no-allow-unauthenticated` | **Privé** : seuls les comptes autorisés peuvent l'appeler (vous, et plus tard l'app) |
| `--min-instances=0` | S'éteint quand personne ne l'utilise (rien à payer) ; la 1re réponse prend alors ~20 s |
| `--max-instances=1` | Une seule copie : la mémoire des conversations est dans le conteneur |

**Résultat obtenu :**

```
Deploying container to Cloud Run service [meteo-a2a-shell] in project [aiml-gemini-ent-exp-0zga] region [europe-west1]
Deploying new service...
Creating Revision...done
Routing traffic.....done
Done.
Service [meteo-a2a-shell] revision [meteo-a2a-shell-00001-8xs] has been deployed and is serving 100 percent of traffic.
Service URL: https://meteo-a2a-shell-433175138344.europe-west1.run.app
```

**À vérifier :** `Service URL` est **exactement** `$URL` (la carte de l'agent contient cette adresse).

### 7.3 Tester l'agent

**Attendez 3 à 5 minutes** (les rôles du nouveau compte mettent ce temps à s'appliquer), puis :

```bash
URL=$URL ./01-bis-cloud-run-a2a/test.sh $K
```

Le script parle à l'agent **comme le fera Gemini Enterprise** (protocole A2A) : il lit sa carte, pose une question,
puis une 2e dans la même conversation.

**Résultat obtenu** (agent `taille`) :

```
== taille  carte : taille_agent (A2A 0.3)
   Q1 > Je fais 98 cm de tour de poitrine, quelle taille de veste ?
   R1 < Pour votre tour de poitrine de 98 cm, je vous conseille la taille M (ou L pour plus d'aisance).
        L'essai en magasin reste cependant le moyen le plus sûr de trouver la coupe idéale pour votre veste.
   Q2 > Peux-tu résumer ta réponse en une phrase ?
   R2 < Pour un tour de poitrine de 98 cm, je vous conseille la taille M ou L (pour plus d'aisance), sachant que l'essai en magasin reste le plus sûr.

OK : les agents répondent en A2A v0.3, avec mémoire de conversation
```

**Dans la console :** 🔎 « Cloud Run » → **Services** → `meteo-a2a-shell` :
- l'**URL** en haut ;
- **Révisions** : la version en ligne ;
- **Journaux** : chaque appel ;
- **Sécurité** : l'authentification **requise** ;
- **Modifier et déployer une nouvelle révision** → **Variables et secrets** : les variables du tableau ci-dessus.

### 7.4 Plusieurs agents

**Façon 1, un par un :** refaites **7.2 et 7.3** en changeant seulement `K=…` (ex. `K=taille`). Les étapes 6 et 7.1 ne
se refont pas.

**Façon 2, d'un coup :** mettez les clés dans le fichier de configuration (ex. `AGENTS="meteo taille retour"`),
rechargez-le (`source scripts/config.sh …`), puis :

```bash
for K in $(echo $AGENTS_LISTE); do
  IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K:v1
  SA=$K-a2a-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
  URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app
  gcloud builds submit --region=$REGION --project=$PROJET_AGENTS \
    --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --config=01-bis-cloud-run-a2a/cloudbuild.yaml --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$IMAGE .
  gcloud iam service-accounts create $K-a2a-shell-sa --project=$PROJET_AGENTS --display-name="Agent $K (Cloud Run A2A, méthode shell)"
  for R in aiplatform.user logging.logWriter modelarmor.user; do
    gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R --member=serviceAccount:$SA >/dev/null \
      && echo "  $K-a2a-shell-sa : roles/$R"
  done
  python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml
  gcloud run deploy $K-a2a-shell --image=$IMAGE --region=$REGION --project=$PROJET_AGENTS \
    --service-account=$SA --no-allow-unauthenticated --env-vars-file=env-$K.yaml \
    --memory=1Gi --cpu=1 --min-instances=0 --max-instances=1 --quiet
done
```

**Comment lire cette boucle :** `for K in meteo taille retour; do … done` lance le bloc **une fois par agent**, avec
`K` qui vaut `meteo`, puis `taille`, puis `retour`. `$(echo $AGENTS_LISTE)` donne la liste de votre fichier (cette
écriture marche dans bash et dans zsh, le terminal des Mac).

**Un agent déjà déployé dans la liste ?** La création de son compte dit `already exists` (sans effet). Le reste
redéploie la même version : sans danger, mais inutile. Mettez plutôt **seulement les nouveaux** dans la liste.

Puis tester **tous** les agents :

```bash
for K in $(echo $AGENTS_LISTE); do URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app ./01-bis-cloud-run-a2a/test.sh $K; done
```

**Tous les agents du catalogue :** `AGENTS=""`, recharger, même boucle (6 agents : 20 à 30 minutes).

### 7.5 Nouvelle version du code d'un agent

Modifiez `agents/trio/meteo_agent/agent.py`, puis refaites **7.2 a)** avec `:v2` au lieu de `:v1` et **7.2 c)**
(seulement la commande `gcloud run deploy`). La même adresse sert la nouvelle version. Les autres agents ne sont pas
touchés : chacun a sa propre image.

### 7.6 La carte de l'agent (pour Gemini Enterprise)

La **carte** est ce que vous collerez dans Gemini Enterprise (**Agents** → **+ Ajouter un agent** → **Agent
personnalisé via A2A**) : un JSON qui dit le nom, la description, l'**adresse** et les compétences de l'agent. Elle
sert aussi à déclarer l'agent dans Agent Registry (partie 9).

**L'écrire dans un fichier**, dans le dossier du projet (configuration chargée) :

```bash
K=meteo
python3 scripts/carte_a2a.py $K https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app > carte-$K.json
python3 -m json.tool --no-ensure-ascii carte-$K.json        # l'afficher, lisible
```

**Résultat obtenu :**

```json
{
    "protocolVersion": "0.3",
    "name": "meteo_agent",
    "description": "Météo réelle d'une ville (jusqu'à 7 jours) et équipement conseillé pour faire du sport dehors.",
    "url": "https://meteo-a2a-shell-433175138344.europe-west1.run.app",
    "preferredTransport": "JSONRPC",
    "version": "1.0.0",
    "capabilities": { "streaming": true },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        { "id": "meteo", "name": "Météo d'une ville", "description": "…", "tags": ["météo", "prévisions"],
          "examples": ["Quel temps à Chamonix demain ?"] },
        { "id": "equipement", "name": "Quoi porter", "description": "…", "tags": ["équipement", "sport"],
          "examples": ["Je cours à Lille demain matin, quoi porter ?"] }
    ]
}
```

| Champ | Sens |
|---|---|
| `protocolVersion: "0.3"` | La version d'A2A que Gemini Enterprise attend |
| `url` | L'adresse du service : **exactement** la `Service URL` de 7.2 c) |
| `name`, `description` | Ce que l'app affiche ; viennent de `agents/trio/catalogue.json` |
| `skills` | Les compétences et leurs exemples de questions |

**À coller dans Gemini Enterprise :** tout le contenu de `carte-meteo.json` (`cat carte-meteo.json` : une seule ligne,
plus facile à copier sans rien couper).

**La vérifier sur l'agent en ligne** (c'est la même, servie par l'agent lui-même) :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app/.well-known/agent-card.json | python3 -m json.tool --no-ensure-ascii
```

**Résultat obtenu :** les mêmes champs, plus un champ `supportedInterfaces` ajouté par la bibliothèque A2A (sans effet).
Pour Gemini Enterprise, utilisez `carte-meteo.json` : c'est exactement le format de la documentation Google.

**Pour l'ajouter à l'app plus tard** (quand elle existera), il faudra aussi donner à l'app le droit d'appeler ce
service (`roles/run.invoker`), puis la coller : [12-1, A5 et A6](12-1-agents-projet-exp-vers-app.md#a5-donner-à-lapp-le-droit-dappeler-les-agents).
Ou, en une commande : `./scripts/add_agent_to_ge.sh a2a carte-meteo.json "Météo & équipement (A2A shell)"` (le script
donne aussi ce droit).

---

## 8. Agent Runtime : un agent, puis plusieurs

Ici, pas d'image : on envoie le **code** à Google, qui l'installe et le fait tourner.

### 8.1 Déployer UN agent

```bash
K=meteo                                                          # ← la clé de l'agent
SA=$K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
gcloud iam service-accounts create $K-shell-sa --project=$PROJET_AGENTS --display-name="Agent $K (Agent Runtime, méthode shell)"
for R in aiplatform.user logging.logWriter modelarmor.user; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R --member=serviceAccount:$SA >/dev/null \
    && echo "  $K-shell-sa : roles/$R"
done
DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent --nom $K-shell \
  --description "$DESC" --compte-service $SA \
  --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE
```

| Morceau | Sens |
|---|---|
| `DESC=$(python3 …)` | Lit la description de l'agent dans le catalogue |
| `--agent meteo_agent` | Le dossier de l'agent (son point d'entrée : `meteo_agent/agent.py`, objet `agent_runtime_app`) |
| `--nom meteo-shell` | Son nom dans Agent Runtime et dans Agent Registry |
| `--compte-service` | Son identité |
| `--env PROMPT_TEMPLATE=…` | Ses filtres Model Armor |

**Résultat obtenu :**

```
Created service account [meteo-shell-sa].
  meteo-shell-sa : roles/aiplatform.user
  meteo-shell-sa : roles/logging.logWriter
  meteo-shell-sa : roles/modelarmor.user
opération : projects/100000000002/locations/europe-west1/reasoningEngines/5685752748113395712/operations/4990073393119232000
  en cours… 0 s
  …
déployé : projects/100000000002/locations/europe-west1/reasoningEngines/5685752748113395712
```

**Notez** le nom après `déployé :` : c'est le **nom de ressource** de l'agent (Gemini Enterprise le demandera).

### 8.2 Tester l'agent

**Attendez 3 à 5 minutes**, puis :

```bash
AGENT_NAME=projects/$NUM_AGENTS/locations/$REGION/reasoningEngines/5685752748113395712 \
  python scripts/query.py - "Je cours à Lille demain matin, quoi porter ?"
```

(Remplacez le nombre par **votre** nom de ressource.) **Résultat obtenu** (agent `taille`, « Mon pied mesure 27 cm,
quelle pointure pour courir ? ») :

```
  -> outil : pointure({'longueur_pied_cm': 27, 'activite': 'course'})
agent : Pour la course à pied avec un pied de 27 cm, je vous conseille une pointure **42 EUR** (une marge est ajoutée car le pied gonfle).
N'oubliez pas que l'essai en magasin reste le moyen le plus sûr de trouver chaussure à votre pied !
```

La ligne `-> outil :` montre l'outil Python que l'agent a appelé, avec ses arguments.

**Retrouver le nom de ressource plus tard :**

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
  | python3 -c 'import json,sys; [print(e["displayName"], e["name"]) for e in json.load(sys.stdin).get("reasoningEngines",[])]'
```

**Dans la console :** 🔎 « Agent Runtime » → **Déploiements** → `meteo-shell` :
- **Playground** : tester à la souris ;
- **Sessions** : les conversations ;
- **Journaux** ;
- le **nom de ressource** en haut.

### 8.3 Plusieurs agents

**Un par un :** refaites 8.1 et 8.2 avec un autre `K`. **D'un coup**, avec la liste du fichier :

```bash
for K in $(echo $AGENTS_LISTE); do
  SA=$K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
  gcloud iam service-accounts create $K-shell-sa --project=$PROJET_AGENTS --display-name="Agent $K (Agent Runtime, méthode shell)"
  for R in aiplatform.user logging.logWriter modelarmor.user; do
    gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R --member=serviceAccount:$SA >/dev/null \
      && echo "  $K-shell-sa : roles/$R"
  done
  DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
  python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent --nom $K-shell \
    --description "$DESC" --compte-service $SA \
    --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE
done
```

Un agent déjà déployé (même nom) n'est **pas** recréé : le script répond `existe déjà : projects/…` et passe. Pour une nouvelle version : le supprimer d'abord ([13](#13-tout-nettoyer) ou `python scripts/nettoyer.py --agent <clé> --types runtime --supprimer`), puis relancer.
Pour une nouvelle version du code d'un agent : supprimez l'ancien ([13](#13-tout-nettoyer)) puis redéployez, ou
utilisez Terraform ([12-1-2](12-1-2-deployer-agents-terraform.md)), qui met à jour sur place.

---

## 9. Agent Registry : le catalogue des agents

- **Agents Agent Runtime :** inscrits **automatiquement**. Rien à faire.
- **Agents Cloud Run :** on les **déclare** avec leur carte. Pour un agent :

```bash
K=meteo
python3 scripts/carte_a2a.py $K https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app > carte-$K.json
NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
gcloud agent-registry services create $K-a2a-shell --location=$REGION --project=$PROJET_AGENTS \
  --display-name="$NOM" --description="$(python3 -c "import json; print(json.load(open('carte-$K.json'))['description'])")" \
  --agent-spec-type=A2A_AGENT_CARD --agent-spec-content="$(cat carte-$K.json)"
```

**Résultat obtenu :** `Created service [meteo-a2a-shell].` Pour plusieurs : même bloc dans
`for K in $(echo $AGENTS_LISTE); do … done`, ou en changeant `K`.

**Voir le catalogue :**

```bash
gcloud agent-registry agents list --location=$REGION --project=$PROJET_AGENTS --format="table(displayName,agentId)"
```

**Résultat obtenu** (après `meteo` et `taille`, Cloud Run et Agent Runtime) :

```
DISPLAY_NAME     AGENT_ID
meteo_agent      urn:agent:projects-433175138344:…:agentregistry:services:meteo-a2a-shell
taille_agent     urn:agent:projects-433175138344:…:agentregistry:services:taille-a2a-shell
meteo-shell      urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:5685752748113395712
taille-shell     urn:agent:projects-433175138344:…:aiplatform:reasoningEngines:8117696546893463552
```

Les lignes `agentregistry:services` sont les agents Cloud Run (déclarés) ; `aiplatform:reasoningEngines`, ceux d'Agent
Runtime (inscrits seuls). Une ligne `Workspace Agent` peut apparaître : c'est un agent de Google, ignorez-la.

**Dans la console :** 🔎 « Agent Registry » → région `europe-west1` → la liste ; un clic → la carte et les compétences.

---

## 10. Dialogflow : un agent conversationnel sans code (option)

**C'est quoi, et faut-il le faire ?**
- Dialogflow (« Conversational Agents » dans la console) est **un autre type d'agent**, qui n'a **rien à voir avec
  nos agents Python** (météo, taille…).
- Il se construit **à la souris** :
  - des **intentions** : « l'utilisateur veut un horaire » → telle réponse ;
  - des **pages** : un parcours guidé, étape par étape ;
  - ou un **playbook** génératif : des consignes en langage naturel.
- Utile pour un parcours guidé : accueil en magasin, orientation, FAQ.
- **Optionnel :** si vous n'en avez pas besoin, passez à la partie 11.

**Ce qu'on fait ici :**
1. créer un agent Dialogflow **vide** ;
2. vérifier qu'il répond ;
3. noter son nom, que Gemini Enterprise demandera plus tard.

Son contenu se construit ensuite dans la console.

### 10.1 Activer l'API (une fois)

```bash
./scripts/verifier_api.sh $PROJET_AGENTS dialogflow.googleapis.com
```

**Attendu :** `OK dialogflow.googleapis.com` (ou `activées : dialogflow.googleapis.com`).

### 10.2 Créer l'agent

```bash
curl -s -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  -H "x-goog-user-project: $PROJET_AGENTS" \
  "https://$REGION-dialogflow.googleapis.com/v3/projects/$PROJET_AGENTS/locations/$REGION/agents" \
  -d '{"displayName":"Accueil magasin (shell)","defaultLanguageCode":"fr","timeZone":"Europe/Paris","description":"Accueil et orientation en magasin"}' \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])' | tee agent-dialogflow.txt
```

| Morceau | Sens |
|---|---|
| `curl -s -X POST …/agents` | Demande à l'API Dialogflow de **créer** un agent (il n'y a pas de commande `gcloud` pour cela) |
| `-H "Authorization: Bearer …"` | Votre jeton de connexion (gcloud) |
| `-d '{…}'` | Ce qu'on crée : nom affiché `Accueil magasin (shell)`, langue `fr`, fuseau `Europe/Paris` |
| `python3 -c … ["name"]` | Garde seulement le **nom** de l'agent dans la réponse |
| `tee agent-dialogflow.txt` | L'affiche **et** l'écrit dans le fichier `agent-dialogflow.txt` (pour la suite) |

**Résultat obtenu :**

```
projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/agents/02d61b82-3c96-4564-82f2-9aa73a455dcd
```

Cette ligne est la **source de l'agent Dialogflow** : c'est ce que Gemini Enterprise demandera (**Agent personnalisé
via Dialogflow** → *Source de l'agent Dialogflow*). Elle est gardée dans `agent-dialogflow.txt`.

### 10.3 Vérifier qu'il répond

```bash
AGENT=$(cat agent-dialogflow.txt) ./04-bis-dialogflow/test.sh "Bonjour"
```

(`AGENT=$(cat agent-dialogflow.txt)` donne au script le nom écrit à l'étape d'avant.) **Résultat obtenu :**

```
  agent pas encore prêt, nouvel essai dans 5 s…
intention : Default Welcome Intent
réponse   : Bonjour !
```

- La ligne « pas encore prêt » est normale juste après la création : un agent neuf répond `404` pendant quelques
  secondes (vérifié : 404 tout de suite, réponse 5 s plus tard). Le script réessaie seul.
- `Default Welcome Intent` : l'intention d'accueil que Dialogflow met dans tout agent neuf ; la réponse varie
  (« Bonjour ! », « Salutations ! »…).
- `ÉCHEC : l'agent … ne répond pas` : l'agent n'existe plus (supprimé ?) ou mauvais nom dans `agent-dialogflow.txt`.
  Vérifiez la liste :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "x-goog-user-project: $PROJET_AGENTS" \
  "https://$REGION-dialogflow.googleapis.com/v3/projects/$PROJET_AGENTS/locations/$REGION/agents" \
  | python3 -c 'import json,sys; [print(a["displayName"], a["name"]) for a in json.load(sys.stdin).get("agents",[])]'
```

### 10.4 Lui donner un contenu (console)

🔎 « Conversational Agents » → choisir le projet → région `europe-west1` → **Accueil magasin (shell)**. Puis :
- **Flux** et **Pages** : un parcours (ex. « Horaires », « Retours », « Parler à un conseiller ») ;
- ou **Playbooks** : des consignes en langage naturel (« Tu accueilles les clients du magasin… »).

À droite, **Tester l'agent** : posez une question, voyez la réponse.

### 10.5 Plus tard, dans Gemini Enterprise

1. L'app → **Agents** → **+ Ajouter un agent** → **Agent personnalisé via Dialogflow**.
2. Remplir :
   - **Nom** : `Accueil magasin` ;
   - **Description** : une phrase ;
   - **Source de l'agent Dialogflow** : le contenu de `agent-dialogflow.txt`.
3. **Créer**.

Détails : [12-2, A6](12-2-agents-dans-projet-app.md#a6-mode-dialogflow-option). Dialogflow dans un autre projet que l'app
n'est pas documenté par Google : pour ce mode, l'agent Dialogflow se crée de préférence dans le projet de l'app (12-2).

**Supprimer l'agent Dialogflow :** `python scripts/nettoyer.py --types dialogflow --supprimer` (il est reconnu à son nom
« Accueil magasin… »), ou :

```bash
curl -s -X DELETE -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "x-goog-user-project: $PROJET_AGENTS" \
  "https://$REGION-dialogflow.googleapis.com/v3/$(cat agent-dialogflow.txt)" && rm agent-dialogflow.txt
```

---

## 11. Vérification finale

```bash
gcloud run services list --region=$REGION --project=$PROJET_AGENTS --format="table(metadata.name,status.url)"
gcloud iam service-accounts list --project=$PROJET_AGENTS --format="value(email)" | grep shell
gcloud agent-registry agents list --location=$REGION --project=$PROJET_AGENTS --format="table(displayName,agentId)"
```

**Résultat obtenu** (`meteo` et `taille`) :

```
NAME              URL
meteo-a2a-shell   https://meteo-a2a-shell-…-ew.a.run.app
taille-a2a-shell  https://taille-a2a-shell-…-ew.a.run.app
```

(Cloud Run affiche ici une 2e forme d'adresse, `…-ew.a.run.app` : les deux mènent au même service.)

| Vérifier | Attendu |
|---|---|
| Un service Cloud Run par agent | `<clé>-a2a-shell` |
| Deux comptes par agent | `<clé>-a2a-shell-sa` (Cloud Run), `<clé>-shell-sa` (Agent Runtime) |
| Le catalogue | Une ligne par agent et par hébergement |
| Les tests | `OK : …` (Cloud Run), une réponse avec `-> outil` (Agent Runtime) |

---

## 12. Ajouter un agent plus tard, en retirer un

- **Ajouter** un agent existant du catalogue (ex. `retour`) : `K=retour`, puis 7.2, 7.3, 8.1, 8.2, 9. Rien d'autre ne
  bouge.
- **Créer** un tout nouvel agent : [12-3, partie 1](12-3-ajouter-des-agents-un-par-un.md#1-créer-lagent-commun-aux-3-méthodes)
  (`python scripts/nouvel_agent.py …`), puis comme ci-dessus.
- **Retirer** un agent : le bloc de [13](#13-tout-nettoyer) avec ce seul `K`.

---

## 13. Tout nettoyer

> **Plus simple : le script de nettoyage.** Il fait l'inventaire de tout ce que les guides créent (Cloud Run, Agent
> Runtime, Agent Registry, Dialogflow, comptes de service et leurs rôles, images, filtres Model Armor) et ne supprime
> qu'après confirmation :
>
> ```bash
> python scripts/nettoyer.py                         # INVENTAIRE : liste, ne supprime rien
> python scripts/nettoyer.py --agent meteo           # seulement ce qui appartient à meteo
> python scripts/nettoyer.py --supprimer             # supprime (tapez l'ID du projet pour confirmer)
> ```
>
> Ce que Terraform a créé est **ignoré** (marqué `[terraform]`) : supprimez-le avec `terraform destroy`. Testé en vrai :
> 8 types supprimés, rôles des comptes compris.

**À la main**, voici ce que fait le script.

**Un agent** (mettez sa clé dans `K`) :

```bash
K=meteo
R=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
  | python3 -c "import json,sys; print(next((e['name'] for e in json.load(sys.stdin).get('reasoningEngines',[]) if e['displayName']=='$K-shell'), ''))")
[ -n "$R" ] && python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --supprimer $R
gcloud agent-registry services delete $K-a2a-shell --location=$REGION --project=$PROJET_AGENTS --quiet
gcloud run services delete $K-a2a-shell --region=$REGION --project=$PROJET_AGENTS --quiet
for SA in $K-shell-sa $K-a2a-shell-sa; do
  for R in aiplatform.user logging.logWriter modelarmor.user; do
    gcloud projects remove-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
      --member=serviceAccount:$SA@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null 2>&1
  done
  gcloud iam service-accounts delete $SA@$PROJET_AGENTS.iam.gserviceaccount.com --project=$PROJET_AGENTS --quiet
done
gcloud artifacts docker images delete $REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K --delete-tags --quiet
rm -f env-$K.yaml carte-$K.json
```

**Résultat obtenu :**

```
supprimé : projects/100000000002/locations/europe-west1/reasoningEngines/5685752748113395712
Deleted service [meteo-a2a-shell].
Deleted service [meteo-a2a-shell].
deleted service account [meteo-shell-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com]
deleted service account [meteo-a2a-shell-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com]
```

(`Deleted service` deux fois : l'entrée du catalogue, puis le service Cloud Run.) **Plusieurs agents :** même bloc
dans `for K in $(echo $AGENTS_LISTE); do … done` (sans la ligne `K=meteo`).

**Ce qui est commun** (seulement quand **plus aucun** agent ne s'en sert) :

```bash
for T in agents-prompt-shield agents-response-shield; do gcloud model-armor templates delete $T --location=$GE_LOCATION --project=$PROJET_AGENTS --quiet; done
gcloud artifacts repositories delete agents-shell --location=$REGION --project=$PROJET_AGENTS --quiet
for R in storage.objectViewer artifactregistry.writer logging.logWriter; do
  gcloud projects remove-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R \
    --member=serviceAccount:agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com >/dev/null 2>&1
done
gcloud iam service-accounts delete agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com --project=$PROJET_AGENTS --quiet
curl -s -X DELETE -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "x-goog-user-project: $PROJET_AGENTS" \
  "https://$REGION-dialogflow.googleapis.com/v3/$(cat agent-dialogflow.txt)" && rm -f agent-dialogflow.txt   # si partie 10
```

**Résultat obtenu :** `Deleted template [agents-prompt-shield].`, `Deleted template [agents-response-shield].`,
`Deleted repository [agents-shell].`

---

## 14. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `MANQUANT : …` ou `ATTENTION : …` au chargement de la configuration | Valeur vide, faute de frappe dans `AGENTS` | Corriger le fichier, recharger |
| Une commande contient `--project=` vide | Configuration pas chargée dans **ce** terminal | `source scripts/config.sh config/12-1-agents-dans-projet-exp.env` |
| `PERMISSION_DENIED` | Un rôle vous manque | Partie 4 |
| `PERMISSION_DENIED` à `gcloud builds submit` | API Cloud Build ou compte `agents-build-sa` tout neufs : droits pas encore actifs | Attendre 1 à 2 minutes, relancer |
| `does not have storage.objects.get access` | Construction lancée sans `--service-account=…agents-build-sa…`, ou ce compte n'a pas ses 3 rôles | Refaire 7.1 ; garder l'option `--service-account` |
| `STATUS … FAILURE` (Cloud Build) | Erreur pendant la construction | Le lien `Logs are available at`, ou 🔎 « Cloud Build » → **Historique** → la construction → journal |
| `Service account … does not exist` juste après `Created service account […]` | Un compte tout neuf met quelques secondes à être visible pour IAM : le rôle n'a pas été donné | Attendre 10 s et relancer **la boucle des rôles** (ou, avec le script, relancer la même commande : il réessaie seul et ne recrée rien) |
| `invalid build: invalid image name ""` | Les 4 lignes de 7.2 (`K=…`, `IMAGE=…`, `SA=…`, `URL=…`) n'ont pas été collées dans **ce** terminal | Les coller, vérifier avec `echo $IMAGE`, relancer |
| `Creating temporary archive of …` avec des centaines de fichiers | Commande lancée hors du dossier du projet | `cd $DOSSIER` puis relancer (le point final = le dossier courant) |
| `already exists` | Déjà créé (compte, template, dépôt) | Rien à faire |
| `ÉCHEC : réponse bloquée par Model Armor` juste après le déploiement | Rôles du nouveau compte pas encore actifs | Attendre 2 à 5 minutes, retester |
| `ÉCHEC : 403` dans `test.sh` | Votre compte n'a pas le droit d'appeler le service | Être propriétaire du projet, ou `roles/run.invoker` sur le service |
| `Error code 13` (Agent Runtime) | Erreur interne de Google | Relancer la commande |
| Météo : « service météo indisponible (erreur 429) » | Le service météo public gratuit limite les appels | Réessayer quelques minutes plus tard : l'agent le dit lui-même, rien de cassé |
| `Service URL` différente de `$URL` | `NUM_AGENTS` faux | Corriger, recharger, redéployer |

Journaux : 🔎 « Journaux », ou
`gcloud logging read 'resource.type="cloud_run_revision" AND severity>=WARNING' --project=$PROJET_AGENTS --freshness=30m --limit=10`.

**Et après :** l'app Gemini Enterprise existe ? Remplissez `PROJET_APP`, `NUM_APP`, `APP_ID` dans le fichier, rechargez,
puis [12-1, A5 (droits) et A6 (ajout dans l'app)](12-1-agents-projet-exp-vers-app.md#a5-donner-à-lapp-le-droit-dappeler-les-agents).
