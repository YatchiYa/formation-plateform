# 10. Rejouer tout le flux, commande par commande, avec les résultats attendus

**Pour qui :** toute personne qui veut refaire **tout le parcours** de bout en bout, sur son poste ou dans Cloud Shell,
avec deux projets Google Cloud (deux projets de test neufs, ou les projets Acme), et **comprendre chaque retour**.

**Ce que vous aurez à la fin :**

| # | Résultat | Où |
|---|---|---|
| 1 | 6 agents (météo, rédaction, traduction, taille, retour, identité) sur **Agent Runtime** | Projet X |
| 2 | Les mêmes 6 agents sur **Cloud Run**, en **A2A** | Projet X |
| 3 | Les agents inscrits dans **Agent Registry** | Projet X |
| 4 | Le droit d'appel donné au **compte de Gemini Enterprise** du projet A, et prouvé avec le **simulateur** | X ← A |
| 5 | Un **agent qui appelle un agent d'un autre projet** : l'orchestrateur (projet A) trouve et appelle l'agent stock (projet X) | A → X |
| 6 | (Si vous avez l'app) les agents publiés dans **Gemini Enterprise** | A |
| 7 | Tout supprimé proprement | X, A |

> **Ce guide a été exécuté en entier** le 8 octobre 2026 sur deux vrais projets. Chaque bloc « Résultat obtenu » est la
> sortie réelle, avec les identifiants remplacés par ceux de vos variables. Les problèmes rencontrés pendant cette
> exécution sont dans la [partie 13](#13-ce-qui-peut-arriver-constaté-en-vrai), avec leur solution.
>
> **Depuis, le catalogue `agents/trio/catalogue.json` compte 6 agents** (ajout de taille, retour, identite) : Terraform
> les déploie tous. Les nombres de ressources ci-dessous sont ceux à 6 agents ; certaines sorties (tests, registre)
> ne montrent encore que les 3 premiers. Ajouter un agent : [docs/12-3](12-3-ajouter-des-agents-un-par-un.md).

---

## Sommaire

0. [Les deux projets, et les variables](#0-les-deux-projets-et-les-variables)
1. [La carte : dossiers, fichiers, ressources, identités](#1-la-carte--dossiers-fichiers-ressources-identités)
2. [Outils et connexion](#2-outils-et-connexion)
3. [(Option) Créer deux projets neufs](#3-option-créer-deux-projets-neufs)
4. [Activer les API de départ](#4-activer-les-api-de-départ)
5. [Tester les agents sur votre poste](#5-tester-les-agents-sur-votre-poste)
6. [Projet A : le compte de Gemini Enterprise et le simulateur](#6-projet-a--le-compte-de-gemini-enterprise-et-le-simulateur)
7. [Projet X : déployer sur Agent Runtime (02-bis)](#7-projet-x--déployer-sur-agent-runtime-02-bis)
8. [Projet X : déployer sur Cloud Run en A2A (01-bis)](#8-projet-x--déployer-sur-cloud-run-en-a2a-01-bis)
9. [Prouver l'accès de Gemini Enterprise avec le simulateur](#9-prouver-laccès-de-gemini-enterprise-avec-le-simulateur)
10. [Un agent qui appelle un agent d'un autre projet (A → X)](#10-un-agent-qui-appelle-un-agent-dun-autre-projet-a--x)
11. [(Option) Utiliser une clé d'API pour le modèle](#11-option-utiliser-une-clé-dapi-pour-le-modèle)
12. [(Si vous avez l'app) Publier dans Gemini Enterprise et tester dans le chat](#12-si-vous-avez-lapp-publier-dans-gemini-enterprise-et-tester-dans-le-chat)
13. [Ce qui peut arriver (constaté en vrai)](#13-ce-qui-peut-arriver-constaté-en-vrai)
14. [Tout supprimer](#14-tout-supprimer)
15. [Annexe : lire les sorties (champs, identifiants, URL)](#15-annexe--lire-les-sorties-champs-identifiants-url)

---

## 0. Les deux projets, et les variables

| Rôle | Variable | Chez Acme | Pour un essai |
|---|---|---|---|
| **Projet A** : l'app Gemini Enterprise. Son **compte de service** appelle les agents. Il héberge aussi l'orchestrateur de la partie 10 | `PROJET_A`, `NUM_A` | `aiml-gemini-entreprise-ldbr`, `98547854221` | Un projet de test (partie 3) |
| **Projet X** : là où une équipe déploie ses agents | `PROJET_X` | Le projet de l'équipe | Un deuxième projet de test |

> **Attention, projet A Acme :** les parties 6 à 9 n'y créent rien d'autre que le compte simulateur. La partie 10, elle,
> **déploie un agent (l'orchestrateur) dans le projet A**. Sur `aiml-gemini-entreprise-ldbr`, faites-la seulement si
> l'équipe Gemini Enterprise est d'accord ; sinon, utilisez un projet de test comme A.

**Ouvrez un terminal (votre poste ou Cloud Shell) et collez ce bloc, adapté.** Toutes les commandes du guide l'utilisent.

```bash
export PROJET_A=aiml-gemini-entreprise-ldbr        # projet de l'app Gemini Enterprise (A)
export NUM_A=98547854221                            # son NUMÉRO (à vérifier, voir ci-dessous)
export PROJET_X=mon-projet-agents                   # projet des agents (X) : à remplacer
export REGION=europe-west1                          # app en multi-région eu => agents en europe-*
export GE_LOCATION=eu
export GE_SA=service-$NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com   # compte de Gemini Enterprise
export SIMU=ge-simulateur@$PROJET_A.iam.gserviceaccount.com                  # compte simulateur (partie 6)
export DOSSIER=~/09-agents-multi-projets-gemini-enterprise                   # où se trouve le dossier 09
```

**Vérifier le numéro du projet A** (le compte de Gemini Enterprise en dépend) :

```bash
gcloud projects describe $PROJET_A --format='value(projectNumber)'
```

**Résultat attendu :** le même nombre que `NUM_A`. S'il diffère, corrigez `NUM_A` et relancez le bloc `export`. (Un
numéro de projet compte en général 12 chiffres.)

> Les variables disparaissent quand on ferme le terminal. **Après chaque reconnexion, recollez le bloc `export`.**

---

## 1. La carte : dossiers, fichiers, ressources, identités

### 1.1 Les dossiers et fichiers utilisés

```
09-agents-multi-projets-gemini-enterprise/
├── agents/trio/                     LES 6 AGENTS (code unique, utilisé par 01-bis et 02-bis)
│   ├── commun.py                    accès au modèle (identité Vertex AI ou clé d'API) + Model Armor
│   ├── catalogue.json               noms affichés, descriptions, compétences A2A (lu par Terraform)
│   ├── requirements.txt             dépendances (ADK 2.10, Agent Platform 2.2, Model Armor)
│   └── meteo_agent/ redaction_agent/ traduction_agent/ …   un dossier par agent (agent.py)
├── agents/specialist/stock_agent/   agent STOCK (partie 10, projet X)
├── agents/orchestrator/             agent ORCHESTRATEUR (partie 10, projet A) : trouve et appelle l'agent stock
├── 02-bis-agent-runtime/            Terraform + test.sh : les agents sur Agent Runtime
├── 01-bis-cloud-run-a2a/            Dockerfile + cloudbuild.yaml (construction dans Google Cloud) + main.py (serveur A2A) + Terraform + test.sh : les agents sur Cloud Run
├── terraform/                       Terraform de la partie 10 (stock dans X, orchestrateur dans A, droits entre les deux)
│   └── modules/adk_agent, armor_templates   modules partagés (un agent Agent Runtime ; une paire de templates Model Armor)
└── scripts/
    ├── test_trio.py                 tests hors ligne des agents du trio
    ├── test_agents.py               tests hors ligne de l'agent stock et de l'orchestrateur
    ├── query.py                     interroger un agent Agent Runtime (comme le ferait une application)
    ├── registry.py                  lire l'Agent Registry d'un projet, et dire comment ajouter chaque agent
    ├── simuler_gemini_enterprise.sh appeler un agent avec les mêmes droits que Gemini Enterprise
    ├── add_agent_to_ge.sh           ajouter un agent existant à l'app (ADK ou A2A)
    └── register_agent.sh            utilisé par Terraform pour publier dans l'app
```

### 1.2 Ce que chaque étape crée

| Partie | Projet | Ressources créées | Nombre (Terraform) |
|---|---|---|---|
| 6 | A | Identité de Gemini Enterprise (si absente), compte `ge-simulateur` | — (gcloud) |
| 7 | X | 6 agents Agent Runtime, 6 comptes de service, leurs rôles, 2 templates Model Armor, le droit de Gemini Enterprise, API | 49 |
| 8 | X | 1 dépôt d'images, 1 image par agent, 6 services Cloud Run privés, 6 comptes de service, rôles, 2 templates Model Armor, 6 entrées Agent Registry, 6 droits `run.invoker` pour Gemini Enterprise, API | 59 |
| 10 | X et A | Agent stock (X), orchestrateur (A), 2 comptes de service, 2 templates Model Armor (X), le droit de l'orchestrateur **sur l'agent stock seulement**, le droit de lire le registre de X, API | 26 |

### 1.3 Les identités (qui appelle qui)

| Identité | Adresse | Sert à |
|---|---|---|
| Vous | votre compte | Lancer Terraform et les tests (Terraform agit avec **vos** droits) |
| Compte de Gemini Enterprise | `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` | Appeler les agents depuis l'app |
| Simulateur | `ge-simulateur@PROJET_A.iam.gserviceaccount.com` | Prouver l'accès avec les **mêmes** droits que Gemini Enterprise |
| Agent Runtime | `meteo-agent-sa@PROJET_X…`, `redaction-agent-sa@…`, `traduction-agent-sa@…` | Faire tourner chaque agent (Gemini, journaux, Model Armor) |
| Cloud Run | `meteo-a2a-sa@PROJET_X…`, etc. | Idem, pour les services Cloud Run |
| Partie 10 | `stock-agent-sa@PROJET_X…`, `assistant-magasin-sa@PROJET_A…` | L'agent stock ; l'orchestrateur, qui appelle l'agent stock |

---

## 2. Outils et connexion

**Le plus simple : Cloud Shell** (console Google Cloud → icône `>_` en haut à droite) : tout est installé. Sur un poste :
gcloud, Terraform 1.9+, Python 3.12 avec `uv`. **Pas besoin de Docker** : les images de la partie 8 sont construites
dans Google Cloud (Cloud Build).

```bash
gcloud version | head -1 ; terraform version | head -1 ; uv --version
```

**Résultat obtenu :**

```
Google Cloud SDK 587.0.0
Terraform v1.16.0
uv 0.8.x
```

Si `uv` manque : `pip install --user uv`, puis ouvrir un nouveau terminal.

**Connexion (deux connexions différentes, les deux sont nécessaires) :**

```bash
gcloud auth login                         # pour gcloud (et Cloud Build)
gcloud auth application-default login     # pour Terraform et les scripts Python
gcloud config set project $PROJET_X
```

**Résultat attendu :** le navigateur s'ouvre deux fois ; à la fin `Credentials saved to file: [.../application_default_credentials.json]`
puis `Updated property [core/project]`.

**Mettre le dossier 09 dans le terminal** (Cloud Shell : menu à trois points → **Importer**, puis décompresser ; ou `git clone`) :

```bash
cd $DOSSIER && ls
```

**Résultat attendu :** `01-bis-cloud-run-a2a  02-bis-agent-runtime  agents  docs  scripts  terraform …`

---

## 3. (Option) Créer deux projets neufs

Pour refaire tout l'essai sans toucher aux projets existants. Il faut le droit de créer des projets et un compte de
facturation.

```bash
gcloud billing accounts list                                   # repérer l'ID : XXXXXX-XXXXXX-XXXXXX
export BILLING=XXXXXX-XXXXXX-XXXXXX
export PROJET_A=essai-ge-app-$RANDOM PROJET_X=essai-ge-agents-$RANDOM
for P in $PROJET_A $PROJET_X; do
  gcloud projects create $P --name="$P"                        # ajouter --folder=ID ou --organization=ID chez Acme
  gcloud billing projects link $P --billing-account=$BILLING
done
export NUM_A=$(gcloud projects describe $PROJET_A --format='value(projectNumber)')
export GE_SA=service-$NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com SIMU=ge-simulateur@$PROJET_A.iam.gserviceaccount.com
echo "A=$PROJET_A ($NUM_A)  X=$PROJET_X"
```

**Résultat attendu :** `Create in progress for [...]`, puis `billingEnabled: true` pour chaque projet, puis la ligne `A=... X=...`.

---

## 4. Activer les API de départ

Terraform lit le numéro du projet avant tout le reste : ces deux API doivent être actives **avant** son premier lancement.
Les autres (Agent Platform, Cloud Run, Model Armor, Agent Registry, IAM…) sont activées par Terraform.

```bash
for P in $PROJET_A $PROJET_X; do
  gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com --project=$P
done
```

**Résultat obtenu :**

```
Operation "operations/acat.p2-111122223333-eab204d8-…" finished successfully.
Operation "operations/acat.p2-98547854221-a52458d4-…" finished successfully.
```

`p2-<nombre>` est le numéro du projet concerné : une ligne par projet.

---

## 5. Tester les agents sur votre poste

**Pourquoi :** si un agent ne marche pas ici, il ne marchera pas déployé. On isole les problèmes d'agent des problèmes de droits.

```bash
cd $DOSSIER
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/orchestrator/requirements.txt      # mêmes dépendances que agents/trio
python scripts/test_trio.py
python scripts/test_agents.py
```

**Résultat obtenu :**

```
tests trio OK (9 scénarios, 6 agents)
tests agents OK (5 scénarios)
```

(Un avertissement `[EXPERIMENTAL] feature FeatureName.PLUGGABLE_AUTH is enabled` peut s'afficher : sans effet.)

**Les agents en vrai** (vrai Gemini via Vertex AI, votre identité, aucune clé) :

```bash
export LOCAL_DEV=1 GOOGLE_CLOUD_PROJECT=$PROJET_X
gcloud services enable aiplatform.googleapis.com --project=$PROJET_X
adk web --port 8080 agents/trio          # Cloud Shell : bouton « Aperçu sur le Web » > port 8080
```

Choisir `traduction_agent` en haut à gauche et écrire « Traduis en espagnol : Votre tente Quechua est disponible en
retrait en magasin. »

**Résultat obtenu :** outils `glossaire` puis `verifier_traduction`, réponse « Tu tienda de campaña Quechua está
disponible para recogida en tienda. — Contrôle : conforme ». `Ctrl+C` pour arrêter.

`LOCAL_DEV=1` autorise l'agent à tourner sans template Model Armor, **en local seulement**. Déployé, il refuse de démarrer sans.

---

## 6. Projet A : le compte de Gemini Enterprise et le simulateur

**6.1 Le compte de Gemini Enterprise.** Il existe dès qu'une app Gemini Enterprise existe dans le projet. Dans un projet
de test sans app, on le crée (les droits de la partie 7 ne peuvent pas être donnés à un compte qui n'existe pas) :

```bash
gcloud services enable discoveryengine.googleapis.com --project=$PROJET_A
gcloud beta services identity create --service=discoveryengine.googleapis.com --project=$PROJET_A
```

**Résultat obtenu :**

```
Operation "operations/acat.p2-98547854221-…" finished successfully.
Service identity created: service-100000000001@gcp-sa-discoveryengine.iam.gserviceaccount.com
```

L'adresse affichée doit être **exactement** `$GE_SA` (`echo $GE_SA`). Sinon, `NUM_A` est faux.

**6.2 Le simulateur.** On ne peut pas emprunter le compte de Gemini Enterprise. Le simulateur est un compte de service du
projet A, à qui l'on donnera (partie 9) exactement les mêmes droits.

```bash
cd $DOSSIER && export GE_PROJECT=$PROJET_A
./scripts/simuler_gemini_enterprise.sh preparer
```

**Résultat obtenu :**

```
Created service account [ge-simulateur].
Service account email: ge-simulateur@<PROJET_A>.iam.gserviceaccount.com
Updated IAM policy for serviceAccount [ge-simulateur@<PROJET_A>.iam.gserviceaccount.com].
simulateur prêt : ge-simulateur@<PROJET_A>.iam.gserviceaccount.com
Les jetons peuvent mettre 1 à 2 minutes à fonctionner après la création.
```

La 3e ligne : vous avez reçu le rôle *Créateur de jetons* **sur ce compte seulement**, ce qui permet au script de parler
« en son nom ».

---

## 7. Projet X : déployer sur Agent Runtime (02-bis)

**7.1 Configurer**

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

**Résultat attendu :** le fichier, avec vos valeurs **réelles** (pas `$PROJET_X`). Les guillemets autour de `EOF` sont
volontairement absents : ils permettent au terminal de remplacer les variables.

| Ligne | Effet |
|---|---|
| `agents_project_id` | Où sont créés les agents |
| `ge_project_number` | Terraform donne au compte de Gemini Enterprise de ce projet le droit d'appeler les agents. **Aucun accès au projet A n'est demandé** |
| (absents) `ge_project_id`, `ge_app_id` | Pas de publication dans l'app : c'est la partie 12 |
| (absents) `prompt_template`, `response_template` | Terraform crée une paire de templates Model Armor dans X |

**7.2 Déployer**

```bash
terraform init
terraform plan        # lire la fin : « Plan: 49 to add, 0 to change, 0 to destroy. »
terraform apply       # taper yes ; 10 à 15 minutes
cp terraform.tfstate ~/sauvegarde-02bis.tfstate     # Terraform est lancé EN LOCAL : sauvegarder l'état
```

**Résultat obtenu (fin de `apply`) :**

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

| Sortie | Ce que c'est |
|---|---|
| `agents` | Le **nom de ressource** de chaque agent. C'est ce qu'on donne à Gemini Enterprise (mode « Agent Runtime ») et à `query.py` |
| `ge_service_agent` | Le compte qui a reçu le droit d'appel. Doit être `$GE_SA` |
| `ge_agents_page` | Lien vers la page Agents de l'app, quand on publie (partie 12) |

> **Constaté :** une fois sur trois agents, la création a échoué avec `Error code 13` (erreur interne de Google, alors que
> 5 agents étaient construits en même temps dans le projet). **Relancer `terraform apply`** : il ne recrée que l'agent
> manquant (`Resources: 1 added`). Pour l'éviter : un déploiement à la fois.

**7.3 Attendre 5 minutes, puis tester.** Juste après le premier `apply`, les droits des nouveaux comptes mettent quelques
minutes à s'appliquer (voir [partie 13](#13-ce-qui-peut-arriver-constaté-en-vrai)).

```bash
cd $DOSSIER/02-bis-agent-runtime && source ../.venv/bin/activate && ./test.sh
```

**Résultat obtenu :**

```
== meteo  (projects/<PROJET_X>/locations/europe-west1/reasoningEngines/5587992970264576000)
  -> outil : meteo({'ville': 'Lille', 'jours': 2})
  -> outil : conseil_equipement({'temperature_c': 10, 'vent_kmh': 27, 'activite': 'course à pied', 'pluie_mm': 8.6})
agent : Demain matin à Lille, de la pluie faible est prévue avec environ 10°C et du vent à 27 km/h.
Pour votre course, portez un t-shirt technique respirant sous une veste imperméable et respirante. …

== redaction  (projects/<PROJET_X>/locations/europe-west1/reasoningEngines/1022468848017735680)
  -> outil : charte_redactionnelle({'canal': 'email_client'})
  -> outil : analyser_texte({'texte': 'ton velo est pret passe avant samedi'})
  -> outil : analyser_texte({'texte': "Bonjour,\n\nBonne nouvelle : votre vélo est prêt ! …"})
agent : Bonjour, … Avant : 7 mots, après : 27 mots

== traduction  (projects/<PROJET_X>/locations/europe-west1/reasoningEngines/976306951837188096)
  -> outil : glossaire({'langue_cible': 'es'})
  -> outil : verifier_traduction({…})
agent : Su tienda de campaña Quechua está disponible para recogida en tienda.  Contrôle : conforme
```

**Comment lire :** chaque `-> outil` est un appel de fonction Python par l'agent, avec ses paramètres. Les bons outils,
dans le bon ordre = l'agent suit ses consignes. Les données météo sont **réelles** (elles changent d'un jour à l'autre).

**7.4 Vérifier Agent Registry** (un agent Agent Runtime s'y inscrit seul)

```bash
gcloud agent-registry agents list --location=$REGION --project=$PROJET_X --format="table(displayName,agentId)"
```

**Résultat obtenu :**

```
DISPLAY_NAME      AGENT_ID
meteo-agent       urn:agent:projects-111122223333:projects:111122223333:locations:europe-west1:aiplatform:reasoningEngines:5587992970264576000
redaction-agent   urn:agent:projects-111122223333:projects:111122223333:locations:europe-west1:aiplatform:reasoningEngines:1022468848017735680
traduction-agent  urn:agent:projects-111122223333:projects:111122223333:locations:europe-west1:aiplatform:reasoningEngines:976306951837188096
```

(Une ligne `Workspace Agent` peut aussi apparaître : c'est un agent de Google, présent dans tous les registres.)
Lecture de l'URN : [annexe](#15-annexe--lire-les-sorties-champs-identifiants-url).

**7.5 Inspecter (facultatif)**

```bash
# les agents Agent Runtime du projet, par l'API
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_X/locations/$REGION/reasoningEngines" \
  | python3 -c 'import json,sys; [print(e["displayName"], e["name"]) for e in json.load(sys.stdin).get("reasoningEngines",[])]'
# le droit de Gemini Enterprise sur le projet X
gcloud projects get-iam-policy $PROJET_X --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
```

**Résultat obtenu :** les agents, un par ligne (`meteo-agent projects/…`), puis `roles/discoveryengine.serviceAgent`.

**Dans la console :** 🔎 « Agent Runtime » (menu *Agent Platform*) → **Déploiements** → `meteo-agent` → onglets
**Playground**, **Sessions**, **Journaux**.

---

## 8. Projet X : déployer sur Cloud Run en A2A (01-bis)

**8.1 Configurer et déployer** (sans Docker : les images sont construites dans Google Cloud par Cloud Build ; vos
rôles sur le projet X doivent inclure *Cloud Build Editor*, *Service Account User* et *Storage Admin*, ou *Owner*)

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
cat > terraform.tfvars <<EOF
agents_project_id = "$PROJET_X"
ge_project_number = "$NUM_A"
region            = "$REGION"
ge_location       = "$GE_LOCATION"
EOF
terraform init
terraform plan        # « Plan: 63 to add » (6 agents : 23 pour le 1er, +8 par agent en plus)
terraform apply       # yes ; ~10 min (Cloud Build construit une image par agent, ~1 min 20 s chacune, puis 6 services)
cp terraform.tfstate ~/sauvegarde-01bis.tfstate
```

**Résultat obtenu (fin de `apply`) :**

```
Apply complete! Resources: 63 added, 0 changed, 0 destroyed.

Outputs:

cards = {
  "meteo" = "{\"capabilities\":{\"streaming\":true},…,\"protocolVersion\":\"0.3\",…,\"url\":\"https://meteo-a2a-111122223333.europe-west1.run.app\",\"version\":\"1.0.0\"}"
  "redaction" = "{…}"
  "traduction" = "{…}"
  …                       (une ligne par agent : 6 au total)
}
ge_agents_page = "(ge_app_id vide : agents non publiés)"
ge_service_agent = "serviceAccount:service-100000000001@gcp-sa-discoveryengine.iam.gserviceaccount.com"
urls = {
  "meteo" = "https://meteo-a2a-xxxxxxxxxx-ew.a.run.app"
  "redaction" = "https://redaction-a2a-xxxxxxxxxx-ew.a.run.app"
  "traduction" = "https://traduction-a2a-xxxxxxxxxx-ew.a.run.app"
  …
}
```

| Sortie | Ce que c'est |
|---|---|
| `cards` | La **carte A2A v0.3** de chaque agent : ce qu'on colle dans Gemini Enterprise (mode « A2A ») |
| `urls` | L'adresse de chaque service. Cloud Run donne **deux** adresses au même service : celle-ci (`…-xxxxxxxxxx-ew.a.run.app`) et `https://meteo-a2a-NUM_X.europe-west1.run.app` (celle des cartes). Les deux fonctionnent ; Terraform a vérifié que la seconde existe |
| `ge_service_agent` | Le compte qui a reçu `run.invoker` sur chaque service |

**8.2 Le service est privé**

```bash
curl -s -o /dev/null -w "%{http_code}\n" $(terraform output -json urls | python3 -c 'import json,sys; print(json.load(sys.stdin)["meteo"])')
```

**Résultat obtenu :** `403`. Sans jeton, personne n'entre : c'est voulu.

**8.3 Attendre 5 minutes, puis tester avec le protocole de Gemini Enterprise**

```bash
cd $DOSSIER/01-bis-cloud-run-a2a && ./test.sh
```

**Résultat obtenu :**

```
== meteo  carte : meteo_agent (A2A 0.3)
   Q1 > Quel temps fait-il à Chamonix ?
   R1 < À Chamonix, le temps est actuellement brumeux (8°C, ressenti 7°C) avec d'importantes averses prévues (25 mm).
   Q2 > Et pour y randonner, quoi porter ?
   R2 < Pour votre randonnée, le temps prévu est très humide avec de fortes pluies (25 mm) et une température fraîche de 8°C.
== redaction  carte : redaction_agent (A2A 0.3)
   …
== traduction  carte : traduction_agent (A2A 0.3)
   Q1 > Traduis en espagnol : 'Votre tente Quechua est disponible en retrait en magasin.'
   R1 < Tu tienda de campaña Quechua está disponible para recogida en tienda.
   Q2 > Et en italien ?
   R2 < La tua tenda Quechua è disponibile per il ritiro in negozio.
OK : les agents répondent en A2A v0.3, avec mémoire de conversation
```

**Comment lire :** `carte : … (A2A 0.3)` = la carte servie annonce la version exigée par Gemini Enterprise. **Q2 sans
répéter le sujet** (« y randonner », « en italien ») et R2 qui reste sur le sujet = la conversation est gardée.

> **Constaté :** lancé tout de suite après le premier `apply`, toutes les réponses étaient « Désolé, je ne peux pas traiter
> cette demande : elle a été filtrée par Model Armor. » Les journaux montraient `403 Permission
> 'modelarmor.templates.useToSanitizeUserPrompt' denied` : le droit venait d'être donné. **Quelques minutes plus tard, tout
> passait.** `test.sh` s'arrête maintenant avec un message clair dans ce cas.

**8.4 Agent Registry** (Terraform y a déclaré une carte par agent)

```bash
gcloud agent-registry services list --location=$REGION --project=$PROJET_X --format="table(displayName,name)"
```

**Résultat obtenu :**

```
DISPLAY_NAME               NAME
Traduction Acme       projects/<PROJET_X>/locations/europe-west1/services/traduction-a2a
Rédaction & reformulation  projects/<PROJET_X>/locations/europe-west1/services/redaction-a2a
Météo & équipement         projects/<PROJET_X>/locations/europe-west1/services/meteo-a2a
```

Sans `--format`, la commande affiche aussi `agentSpec.content` (la carte complète) et `registryResource` (l'entrée
« agent » créée à partir du service : `projects/NUM_X/locations/europe-west1/agents/agentregistry-…`).

**8.5 Vue d'ensemble du registre, avec le moyen d'ajouter chaque agent**

```bash
cd $DOSSIER && python scripts/registry.py $PROJET_X $REGION
```

**Résultat obtenu (extrait) :**

```
== 7 agent(s) dans <PROJET_X>/europe-west1
- meteo_agent: Météo réelle d'une ville (jusqu'à 7 jours) et équipement conseillé pour faire du
    ajout : a2a  https://meteo-a2a-111122223333.europe-west1.run.app/.well-known/agent-card.json  [carte A2A dans le registre]
- traduction-agent: Traduit un texte en 7 langues européennes en respectant le glossaire et les marq
    ajout : adk  projects/111122223333/locations/europe-west1/reasoningEngines/976306951837188096
```

Les agents Cloud Run apparaissent sous le **nom de leur carte** (`meteo_agent`), les agents Agent Runtime sous leur
**nom affiché** (`meteo-agent`). La ligne `ajout :` est exactement ce qu'il faut passer à `scripts/add_agent_to_ge.sh`.

---

## 9. Prouver l'accès de Gemini Enterprise avec le simulateur

**Pourquoi :** c'est la preuve, **avant** toute publication, que le compte d'un autre projet (A) peut appeler les agents de X
avec le droit prévu, par le même chemin que Gemini Enterprise (API Agent Runtime ; en-tête `X-Serverless-Authorization`
pour Cloud Run).

```bash
cd $DOSSIER && export GE_PROJECT=$PROJET_A
export RT=$(terraform -chdir=02-bis-agent-runtime/terraform output -json agents | python3 -c 'import json,sys; print(json.load(sys.stdin)["traduction"])')
export URL=$(terraform -chdir=01-bis-cloud-run-a2a/terraform output -json urls | python3 -c 'import json,sys; print(json.load(sys.stdin)["traduction"])')
```

**9.1 Sans droit : doit être refusé**

```bash
./scripts/simuler_gemini_enterprise.sh runtime $RT "Traduis en italien : retrait en magasin"
./scripts/simuler_gemini_enterprise.sh a2a $URL "Traduis en anglais : retour gratuit"
```

**Résultat obtenu :**

```
REFUSÉ (403) : le compte de Gemini Enterprise n'a pas roles/discoveryengine.serviceAgent sur le projet de l'agent.
REFUSÉ (403) : le compte de Gemini Enterprise n'a pas roles/run.invoker sur ce service.
```

**9.2 Donner au simulateur les mêmes droits que Gemini Enterprise**

```bash
gcloud projects add-iam-policy-binding $PROJET_X --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$SIMU
gcloud run services add-iam-policy-binding traduction-a2a --region=$REGION --project=$PROJET_X \
  --role=roles/run.invoker --member=serviceAccount:$SIMU
```

**Résultat attendu :** `Updated IAM policy for project [...]` puis `Updated IAM policy for service [traduction-a2a]`.

**9.3 Attendre 2 à 3 minutes, puis relancer les commandes de 9.1**

**Résultat obtenu (accepté après 90 secondes) :**

```
ACCEPTÉ (Agent Runtime) : ritiro in negozio  Contrôle : conforme
ACCEPTÉ (A2A v0.3) : free returns  Contrôle : conforme
```

Pour voir que le droit vaut **par service** : `./scripts/simuler_gemini_enterprise.sh a2a <URL de meteo> "Météo à Lille ?"`
reste `REFUSÉ` (le simulateur n'a de droit que sur `traduction-a2a`).

**9.4 Retirer les droits du simulateur** (il ne sert qu'au test)

```bash
gcloud projects remove-iam-policy-binding $PROJET_X --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$SIMU
gcloud run services remove-iam-policy-binding traduction-a2a --region=$REGION --project=$PROJET_X \
  --role=roles/run.invoker --member=serviceAccount:$SIMU
```

---

## 10. Un agent qui appelle un agent d'un autre projet (A → X)

**Le scénario :** l'équipe Supply publie un agent **stock** dans le projet X. L'équipe Magasins a un **orchestrateur**
(« assistant magasin ») dans le projet A. Pour une question de stock, l'orchestrateur :

1. **trouve** l'agent stock dans l'Agent Registry du projet X, par son nom `stock-agent` (aucun identifiant écrit en dur) ;
2. **l'appelle** par l'API Agent Runtime, avec sa propre identité.

Deux droits, donnés **par le projet X** à l'identité de l'orchestrateur : `roles/aiplatform.viewer` **sur l'agent stock
seulement**, et `roles/agentregistry.viewer` sur le projet X (pour lire le registre).

**10.1 Configurer et déployer** (Terraform du dossier `terraform/` ; un déploiement à la fois)

```bash
cd $DOSSIER/terraform
cat > terraform.tfvars <<EOF
agents_project_id = "$PROJET_X"
ge_project_id     = "$PROJET_A"
region            = "$REGION"
ge_location       = "$GE_LOCATION"
EOF
terraform init
terraform plan        # « Plan: 26 to add » ; repérer les 2 droits :
                      #   google_vertex_ai_reasoning_engine_iam_member.orchestrator_calls_stock
                      #   google_project_iam_member.orchestrator_reads_registry[0]
terraform apply       # yes ; 10 à 15 min
cp terraform.tfstate ~/sauvegarde-09.tfstate
```

**Résultat obtenu :**

```
Apply complete! Resources: 26 added, 0 changed, 0 destroyed.

Outputs:

ge_agents_page = "(ge_app_id vide : agents non publiés)"
orchestrator = "projects/<PROJET_A>/locations/europe-west1/reasoningEngines/7589843004630761472"
stock_agent = "projects/<PROJET_X>/locations/europe-west1/reasoningEngines/2978860673645150208"
```

L'orchestrateur est dans **A**, l'agent stock dans **X** : c'est bien un appel entre deux projets.

**10.2 L'agent stock, seul**

```bash
cd $DOSSIER && python scripts/query.py stock_agent "Stock de 8771234 à Lyon ?"
```

**Résultat obtenu :**

```
  -> outil : get_store_stock({'sku': '8771234', 'store': 'lyon'})
agent : Le produit **Tente 2 secondes 2 places** (SKU: 8771234) est en **rupture de stock** dans le magasin de **lyon** (stock : 0).
```

**10.3 L'orchestrateur (projet A) qui appelle l'agent stock (projet X)**

```bash
python scripts/query.py orchestrator "Il reste des tentes 8771234 à Lyon ?"
```

**Résultat obtenu :**

```
  -> outil : ask_stock_agent({'question': "Est-ce qu'il reste des tentes avec le code article 8771234 à Lyon ?"})
agent : Non, la **Tente 2 secondes 2 places** (code article **8771234**) est actuellement en **rupture de stock** dans le magasin de **Lyon** (0 article disponible).

Si besoin, sachez qu'il en reste dans d'autres magasins :
*   **Lille** : 12 en stock
*   **Paris-La-Défense** : 4 en stock
```

**Comment lire :** l'orchestrateur n'a qu'un outil, `ask_stock_agent`. Les chiffres de Lyon, Lille et Paris viennent de
l'agent stock du projet X : l'appel entre projets a fonctionné (découverte dans le registre, puis appel).

**10.4 La preuve que le droit compte** : retirer le droit de l'orchestrateur sur l'agent stock, reposer la question, remettre le droit.

```bash
cd $DOSSIER/terraform
terraform destroy -target=google_vertex_ai_reasoning_engine_iam_member.orchestrator_calls_stock   # yes
sleep 120 && cd .. && python scripts/query.py orchestrator "Il reste des tentes 8771234 à Lyon ?"
cd terraform && terraform apply                                                                     # yes : le droit revient
```

**Résultat obtenu (sans le droit) :**

```
  -> outil : ask_stock_agent({'question': "Est-ce qu'il reste des tentes avec le code article 8771234 dans les magasins de Lyon ?"})
agent : Malheureusement, je ne parviens pas à joindre l'outil de suivi des stocks pour le moment en raison d'un problème
technique (l'agent de l'équipe Supply est indisponible). …
```

L'orchestrateur essaie, reçoit un refus (403) et l'explique au lieu de planter ou d'inventer un stock. Après `apply`,
la question de 10.3 refonctionne.

> **Constaté et corrigé :** au premier essai, l'orchestrateur trouvait l'agent mais ne pouvait pas l'appeler. Les URN
> réelles d'Agent Registry contiennent un segment `aiplatform` (`…:europe-west1:aiplatform:reasoningEngines:ID`) que le
> code n'attendait pas. La conversion gère maintenant les deux formats (test ajouté dans `scripts/test_agents.py`).

---

## 11. (Option) Utiliser une clé d'API pour le modèle

Par défaut, les agents appellent Gemini via **Vertex AI avec leur identité** : aucune clé. Si votre équipe utilise une clé :

| Variable lue par l'agent | Type de clé |
|---|---|
| `GEMINI_API_KEY` | Clé Google AI Studio (API Gemini) |
| `VERTEX_API_KEY` | Clé d'API Vertex AI (mode express) |

**En local :**

```bash
export GEMINI_API_KEY="votre-clé"        # ou VERTEX_API_KEY
adk web --port 8080 agents/trio
```

**Vérifié :** avec une fausse clé, l'agent appelle bien `generativelanguage.googleapis.com` et Google répond
`400 API key not valid` : la clé est utilisée. Avec une vraie clé, l'agent répond normalement.

**Déployé** : la clé est rangée dans Secret Manager, jamais dans un fichier.

```bash
gcloud services enable secretmanager.googleapis.com --project=$PROJET_X
printf '%s' "votre-clé" | gcloud secrets create gemini-api-key --data-file=- --project=$PROJET_X
# dans 02-bis-agent-runtime/terraform/terraform.tfvars (ou 01-bis-…) :
#   model_api_key_secret = "gemini-api-key"
#   model_api_key_type   = "gemini"          # ou vertex
terraform apply
```

**Résultat attendu de `terraform plan` :** 6 ressources `google_secret_manager_secret_iam_member` (chaque agent peut lire
**ce** secret) et la variable `GEMINI_API_KEY` ajoutée aux agents, lue dans le secret.

---

## 12. (Si vous avez l'app) Publier dans Gemini Enterprise et tester dans le chat

Il faut une app Gemini Enterprise dans le projet A (compte d'organisation, licences) et le rôle *Gemini Enterprise Admin*.
**ID de l'app :** console → 🔎 « Gemini Enterprise » → l'app → **Présentation**.

**Option 1 : en ligne de commande** (le plus simple entre deux projets)

```bash
cd $DOSSIER && export GE_PROJECT=$PROJET_A GE_APP=ID_DE_L_APP GE_LOCATION=$GE_LOCATION
# Agent Runtime (ressource de la partie 7)
./scripts/add_agent_to_ge.sh adk $RT "Traduction Acme" "Traduit un texte en 7 langues européennes en respectant le glossaire et les marques Acme."
# A2A (carte de la partie 8, enregistrée en fichier)
terraform -chdir=01-bis-cloud-run-a2a/terraform output -json cards | python3 -c 'import json,sys; print(json.load(sys.stdin)["traduction"])' > carte-traduction.json
./scripts/add_agent_to_ge.sh a2a carte-traduction.json "Traduction Acme (A2A)"
./scripts/add_agent_to_ge.sh list
```

**Résultat attendu :** `ajouté : projects/…/agents/…` pour chacun, puis la liste avec les deux agents et leur type
(`adkAgentDefinition`, `a2aAgentDefinition`).

**Option 2 : par Terraform**, si les agents sont **dans le projet de l'app** : ajouter `ge_project_id = "$PROJET_A"` et
`ge_app_id = "ID_DE_L_APP"` dans `terraform.tfvars`, puis `terraform apply` (`registered …` ×6, `Resources: 7 added`).

**Option 3 : dans la console** : [docs/09, partie 2](09-connecter-a-gemini-enterprise.md#partie-2--chaque-mode-pas-à-pas).

**Ensuite, pour chaque agent :** app → **Agents** → l'agent → **Autorisations utilisateur** → **Ajouter** → un groupe → rôle
**Agent User** → Enregistrer. Puis, avec un compte du groupe : lien de l'app web → **Agents** → l'agent → « Traduis en
allemand : retour gratuit sur les chaussures Kiprun ».

**Résultat attendu :** « Kostenlose Rücksendung … Kiprun … — Contrôle : conforme ». C'est **le seul point de ce guide qui
n'a pas pu être exécuté** lors de l'essai (pas d'app Gemini Enterprise sur les projets de test).

---

## 13. Ce qui peut arriver (constaté en vrai)

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `403 Cloud Resource Manager API has not been used` au `plan` | API de départ inactive | Partie 4 |
| `Error creating service account … IAM API has not been used` | API IAM inactive (corrigé : Terraform l'active) | Mettre à jour le dossier ; ou `gcloud services enable iam.googleapis.com` |
| Toutes les réponses : « … filtrée par Model Armor » juste après le premier `apply` | Le droit `modelarmor.user` du nouvel agent n'est pas encore actif (journaux : `403 … modelarmor.templates.useToSanitizeUserPrompt`) | Attendre 2 à 5 minutes, relancer le test |
| `Error code 13` à la création d'un agent Agent Runtime | Erreur interne de Google (plusieurs agents construits en même temps) | Relancer `terraform apply` ; un déploiement à la fois |
| Une erreur `404` isolée sur la carte A2A, aucun 404 dans les journaux Cloud Run | Erreur passagère avant le conteneur | `test.sh` réessaie seul ; sinon relancer |
| Simulateur `REFUSÉ` juste après avoir donné le droit | Propagation IAM (constaté : refusé à 60 s, accepté à 90 s) | Attendre 2 à 3 minutes |
| L'orchestrateur répond « agent stock indisponible » | Droit `aiplatform.viewer` sur l'agent stock absent, ou ancienne version du code (format d'URN) | Vérifier `terraform plan` (droit présent) ; mettre à jour le dossier |
| `No API key was provided` en local | ADK antérieur à 2.10 | `pip show google-adk` ; réinstaller (partie 5) |
| `default credentials were not found` | Pas de connexion `application-default` | Partie 2 |
| `Destroy … contains child resources: sessions` | Ancienne version du module (corrigé : `deletion_policy = "FORCE"`) | Mettre à jour le dossier, `terraform apply`, puis `destroy` |
| `PERMISSION_DENIED` pendant la construction des images (partie 8) juste après le 1er `apply` | API Cloud Build ou compte de construction `agents-a2a-build-sa` tout neufs : droits pas encore actifs | Terraform réessaie seul (4 fois) ; sinon attendre 1 à 2 minutes et relancer `terraform apply` |
| Construction `FAILURE` (partie 8) | Erreur dans la construction de l'image | Ouvrir le lien du journal affiché par gcloud ; console : 🔎 « Cloud Build » → **Historique** (région `europe-west1`) |
| Variables vides (`--project=` sans valeur) | Terminal rouvert | Recoller le bloc `export` de la partie 0 |

**Lire les journaux d'un agent :**

```bash
# Cloud Run
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="meteo-a2a" AND severity>=WARNING' \
  --project=$PROJET_X --freshness=30m --limit=10 --format="value(timestamp,severity,textPayload)"
# Agent Runtime
gcloud logging read 'resource.type="aiplatform.googleapis.com/ReasoningEngine" AND severity>=ERROR' \
  --project=$PROJET_X --freshness=1h --limit=10 --format="value(timestamp,resource.labels.reasoning_engine_id,textPayload)"
```

---

## 14. Tout supprimer

**Dans cet ordre, un à la fois** (Terraform retire aussi les agents de l'app s'ils y ont été publiés par Terraform) :

```bash
cd $DOSSIER
terraform -chdir=terraform destroy                   # yes -> Destroy complete! Resources: 26 destroyed.
terraform -chdir=02-bis-agent-runtime/terraform destroy   # yes -> Resources: 49 destroyed.
terraform -chdir=01-bis-cloud-run-a2a/terraform destroy   # yes -> Resources: 63 destroyed.
gcloud iam service-accounts delete $SIMU --project=$PROJET_A --quiet
```

**Résultat obtenu :** les trois `Destroy complete!` avec 26, 49 et 63 ressources, puis `deleted service account [ge-simulateur@…]`.

**Vérifier qu'il ne reste rien :**

```bash
gcloud run services list --project=$PROJET_X --region=$REGION
for P in $PROJET_X $PROJET_A; do
  curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    "https://$REGION-aiplatform.googleapis.com/v1/projects/$P/locations/$REGION/reasoningEngines" \
    | python3 -c 'import json,sys; print("agents Agent Runtime :", [e["displayName"] for e in json.load(sys.stdin).get("reasoningEngines",[])])'
done
```

**Résultat obtenu :** aucun service, puis `agents Agent Runtime : []` deux fois. Les API restent activées (sans coût).

Projets de test de la partie 3 : `gcloud projects delete $PROJET_X` et `gcloud projects delete $PROJET_A` (suppression
définitive après 30 jours).

---

## 15. Annexe : lire les sorties (champs, identifiants, URL)

### Identifiants

| Exemple | Ce que c'est |
|---|---|
| `projects/<PROJET_X>/locations/europe-west1/reasoningEngines/976306951837188096` | **Nom de ressource** d'un agent Agent Runtime : projet, région, identifiant. On peut écrire le projet par son ID ou par son numéro |
| `urn:agent:projects-NUM:projects:NUM:locations:europe-west1:aiplatform:reasoningEngines:ID` | **URN Agent Registry** d'un agent Agent Runtime : éditeur (`projects-NUM`), puis l'emplacement de la ressource. Se convertit en nom de ressource (`scripts/registry.py` le fait) |
| `urn:agent:…:locations:europe-west1:agentregistry:services:meteo-a2a` | URN d'un agent **déclaré** (Cloud Run / A2A) dans le registre |
| `projects/<PROJET_X>/locations/europe-west1/services/meteo-a2a` | L'entrée **service** du registre (ce que Terraform crée en partie 8) |
| `projects/NUM/locations/europe-west1/agents/agentregistry-00000000-…` | L'entrée **agent** que le registre dérive du service (`registryResource`) |
| `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` | Compte de service de Gemini Enterprise du projet A (« agent de service » géré par Google) |
| `operations/acat.p2-NUM-…` | Opération d'activation d'API ; `NUM` = numéro du projet concerné |

### La carte A2A (sortie `cards`, et `agentSpec.content` dans le registre)

| Champ | Rôle |
|---|---|
| `protocolVersion: "0.3"` | Version du protocole A2A exigée par Gemini Enterprise |
| `url` | Où envoyer les messages : l'URL Cloud Run **par défaut** (`…-NUM_X.europe-west1.run.app`) |
| `name`, `description` | Identité de l'agent ; la description sert au modèle pour choisir l'agent |
| `skills` | Compétences : `id`, `name`, `description`, `tags`, `examples` (affichées dans la prévisualisation) |
| `capabilities.streaming: true` | L'agent accepte `message/stream` (utilisé par Gemini Enterprise) |
| `preferredTransport: JSONRPC` | Les appels sont en JSON-RPC (`message/send`, `message/stream`) |

### Les deux adresses d'un service Cloud Run

| Adresse | D'où elle vient |
|---|---|
| `https://SERVICE-NUM_X.europe-west1.run.app` | Adresse **déterministe** (projet + région) : celle des cartes, calculée avant la création et vérifiée ensuite par Terraform |
| `https://SERVICE-xxxxxxxxxx-ew.a.run.app` | Adresse historique, renvoyée par `terraform output urls` |

Les deux mènent au même service ; un jeton d'identité vaut pour l'une ou l'autre.

### Les pages utiles de la console

| Page | Lien |
|---|---|
| Services Cloud Run du projet X | `https://console.cloud.google.com/run?project=PROJET_X` |
| Droits (IAM) d'un projet | `https://console.cloud.google.com/iam-admin/iam?project=PROJET_X` (cocher *Inclure les attributions de rôles fournies par Google* pour voir le compte de Gemini Enterprise) |
| Journaux | `https://console.cloud.google.com/logs/query?project=PROJET_X` |
| Secret Manager | `https://console.cloud.google.com/security/secret-manager?project=PROJET_X` |
| API activées | `https://console.cloud.google.com/apis/dashboard?project=PROJET_X` |
| Agent Runtime, Agent Registry, Model Armor, Gemini Enterprise | Barre de recherche de la console : « Agent Runtime », « Agent Registry », « Model Armor », « Gemini Enterprise » (leurs adresses changent selon les versions de la console) |

### Les appels réseau, pour comprendre

| Qui | Vers | Comment |
|---|---|---|
| `query.py`, le simulateur (`runtime`), Gemini Enterprise | Agent Runtime | `POST https://europe-west1-aiplatform.googleapis.com/v1/<ressource>:query` (`create_session`) puis `:streamQuery` (`stream_query`), avec un jeton d'accès |
| `test.sh` (01-bis), le simulateur (`a2a`), Gemini Enterprise | Cloud Run | `POST https://<service>/` en JSON-RPC A2A v0.3, avec un jeton OIDC (`Authorization` ou `X-Serverless-Authorization`) |
| L'orchestrateur | Agent Registry de X, puis l'agent stock | `list_agents` (droit `agentregistry.viewer`), puis l'API Agent Runtime (droit `aiplatform.viewer` sur l'agent) |
| Chaque agent | Gemini | Vertex AI avec son identité (`aiplatform.googleapis.com`), ou l'API Gemini avec une clé (`generativelanguage.googleapis.com`) |
| Chaque agent | Model Armor | `modelarmor.eu.rep.googleapis.com` (point d'accès de la localisation des templates) |
