# 08. Tutoriel complet : 3 agents utiles, 2 hébergements, même projet ou autre projet

**Pour qui :** les équipes qui veulent construire de **vrais** agents (avec des outils) et les rendre utilisables dans
Gemini Enterprise, en **code** (Terraform), de façon reproductible.
**Résultat :** trois agents dans le chat Gemini Enterprise, déployés au choix sur **Cloud Run (A2A)** ou sur
**Agent Runtime**, dans le projet de l'app ou dans un autre projet, inscrits dans **Agent Registry**.

> Les tutoriels [02](02-tuto-meme-projet.md) et [03](03-tuto-autre-projet.md) font la même chose **à la main, dans la
> console**, avec un seul agent. Celui-ci est la version **industrialisée** : trois agents, tout en Terraform, testé à
> chaque étape. Ce document contient les étapes **communes** ; chaque hébergement a ensuite son pas à pas.

---

## Sommaire

1. [Les 3 agents](#1-les-3-agents)
2. [Choisir : Cloud Run + A2A ou Agent Runtime ? Même projet ou autre projet ?](#2-choisir)
3. [Prérequis (une fois)](#3-prérequis-une-fois)
4. [Tester les agents sur votre poste](#4-tester-les-agents-sur-votre-poste)
5. [Déployer : la suite dans 01-bis ou 02-bis](#5-déployer)
6. [Ce qui est vérifié](#6-ce-qui-est-vérifié)

---

## 1. Les 3 agents

Le code est dans `agents/trio/`, **une seule fois** : les deux hébergements déploient exactement les mêmes fichiers.

| Agent | Ce qu'il fait | Outils (code Python) | Exemple |
|---|---|---|---|
| **Météo & équipement** (`meteo_agent`) | Météo **réelle** d'une ville (jusqu'à 7 jours) et quoi porter pour faire du sport | `meteo` (API Open-Meteo, gratuite, sans clé) ; `conseil_equipement` (règle des 3 couches, alertes vent / pluie / chaleur) | « Je cours à Lille demain matin, quoi porter ? » |
| **Rédaction & reformulation** (`redaction_agent`) | Reformule un texte selon le canal et la charte | `charte_redactionnelle` (ton, structure, longueur par canal) ; `analyser_texte` (mots, phrases, phrases trop longues, avant / après) | « Reformule pour un e-mail client : … » |
| **Traduction Acme** (`traduction_agent`) | Traduit en 7 langues en respectant le glossaire | `glossaire` (termes imposés, marques à ne pas traduire) ; `verifier_traduction` (marques conservées, longueur cohérente) | « Traduis en espagnol : Votre tente Quechua … » |

```
agents/trio/
├── commun.py            accès au modèle Gemini (identité Vertex AI, ou clé d'API) + plugin Model Armor (obligatoire hors local)
├── catalogue.json       noms affichés, descriptions, compétences A2A : lu par Terraform (01-bis et 02-bis)
├── requirements.txt
├── meteo_agent/         agent.py : root_agent (l'agent), app (agent + Model Armor), agent_runtime_app (Agent Runtime)
├── redaction_agent/
└── traduction_agent/
```

> Le catalogue contient aussi **Conseil taille** (`taille_agent`), **Retours produits** (`retour_agent`) et **Identité
> utilisateur** (`identite_agent`) : Terraform (01-bis, 02-bis) déploie **toutes** les entrées du catalogue, soit 6 agents.
> Ajouter le vôtre : [docs/12-3](12-3-ajouter-des-agents-un-par-un.md).

**Pourquoi un agent = des outils + des consignes :** l'outil fait ce qu'un modèle fait mal (données réelles, calculs,
règles exactes) ; le modèle fait ce qu'un outil fait mal (comprendre la demande, rédiger). Chaque consigne dit **quand**
appeler chaque outil. C'est ce qui rend l'agent fiable.

**Accès au modèle : identité (par défaut) ou clé d'API.** `commun.py` choisit selon l'environnement :

| Variable | Accès | Quand |
|---|---|---|
| *(aucune)* | Vertex AI avec l'identité de l'agent (la vôtre en local) | **Recommandé** : aucun secret à gérer |
| `GEMINI_API_KEY` | API Gemini, clé Google AI Studio | Équipe qui a déjà une clé AI Studio |
| `VERTEX_API_KEY` | Vertex AI, clé d'API (mode express) | Clé Vertex AI fournie par l'équipe cloud |

Déployé, la clé n'est jamais en clair : on la range dans **Secret Manager**, puis on renseigne `model_api_key_secret`
(et `model_api_key_type`) dans `terraform.tfvars`. Chaque agent ne peut lire que ce secret.

```bash
printf '%s' "VOTRE_CLE" | gcloud secrets create gemini-api-key --data-file=- --project=PROJET_DES_AGENTS
# terraform.tfvars : model_api_key_secret = "gemini-api-key"   model_api_key_type = "gemini"
```

**Pourquoi Model Armor est dans l'agent :** Gemini Enterprise ne filtre pas les agents qu'on lui ajoute (Agent Runtime
comme A2A). Chaque agent filtre donc lui-même questions et réponses, et **refuse de démarrer** sans template (sauf en
local, avec `LOCAL_DEV=1`).

---

## 2. Choisir

### Hébergement

| | [01-bis : Cloud Run + A2A](../01-bis-cloud-run-a2a/README.md) | [02-bis : Agent Runtime](../02-bis-agent-runtime/README.md) |
|---|---|---|
| Qui héberge | Vous : un conteneur Cloud Run par agent | Google : hébergement géré |
| Protocole vers Gemini Enterprise | **A2A v0.3** (standard ouvert, tout framework) | API Agent Runtime (ADK) |
| Ajout dans l'app | *Agent personnalisé via A2A* : carte d'agent JSON | *Agent personnalisé via Agent Runtime* : nom de ressource |
| Agent Registry | Déclaré par Terraform (carte A2A) | **Automatique** |
| Sessions, journaux, playground | Journaux Cloud Run ; sessions en mémoire (1 instance) | Sessions gérées, onglets Playground / Journaux / Sessions |
| Docker sur le poste | **Non** : les images sont construites dans Google Cloud (Cloud Build) | Non |
| Durée du premier déploiement | ~10 min | ~10 à 15 min |
| Quand | Agent appelé aussi hors Google (A2A), contrôle du conteneur, équipe habituée à Cloud Run | **Par défaut** pour un agent ADK |

Les deux peuvent coexister : les noms affichés diffèrent (« … (A2A) » pour Cloud Run).

### Même projet ou autre projet

**Les deux fonctionnent avec le même code, et ont été testés entre deux vrais projets.** Dans `terraform.tfvars` :

```hcl
agents_project_id = "equipe-pricing-prod"   # le projet qui héberge les agents (le vôtre, ou celui de l'app)
ge_project_number = "98547854221"          # le NUMÉRO du projet de l'app, donné par l'admin Gemini Enterprise
```

Une équipe n'a besoin d'**aucun droit** sur le projet de l'app : Terraform ne s'en sert que pour publier, si l'on renseigne
`ge_project_id` et `ge_app_id` (admin, ou tout dans le projet de l'app). Le pas à pas entre projets, avec le rôle de
chacun : [docs/09, partie 3](09-connecter-a-gemini-enterprise.md#partie-3--le-pas-à-pas-entre-projets).

| Droit | Même projet | Autre projet | Posé par |
|---|---|---|---|
| Gemini Enterprise appelle un agent **Agent Runtime** | Aucun (déjà donné par Google) | `roles/discoveryengine.serviceAgent` sur le projet des agents | Terraform 02-bis |
| Gemini Enterprise appelle un agent **Cloud Run (A2A)** | `roles/run.invoker` **sur chaque service** | Idem | Terraform 01-bis |
| L'agent utilise Gemini, écrit ses journaux | Rôles sur **son** projet, identité dédiée par agent | Idem | Terraform |
| L'agent utilise les templates Model Armor | `roles/modelarmor.user` sur le projet des templates | Idem | Terraform |

Détail et règle générale : [05 – droits et régions](05-droits-et-regions.md).

---

## 3. Prérequis (une fois)

### 3.1 Les outils

Le plus simple : **Cloud Shell** (console Google Cloud, icône `>_`), où tout est installé. Sur un poste :

| Outil | Version | Vérifier |
|---|---|---|
| gcloud | récente | `gcloud version` |
| Terraform | 1.9 ou plus | `terraform version` |
| Python | 3.12 (via `uv`) | `uv --version` |

### 3.2 Se connecter

```bash
gcloud auth login                         # pour gcloud (et Cloud Build, qui construit les images de 01-bis)
gcloud auth application-default login     # pour Terraform et les tests Python
gcloud config set project aiml-gemini-entreprise-ldbr
```

### 3.3 Les projets

| Cas | Projets |
|---|---|
| Même projet | Un projet : celui de l'app Gemini Enterprise (`aiml-gemini-entreprise-ldbr` dans ce guide) |
| Autre projet | Le projet de l'app (A, `aiml-gemini-entreprise-ldbr`) **et** le projet des agents (B, `acme-agents-demo`), même organisation, facturation active |

Dans **chaque** projet, activer les deux API dont Terraform a besoin **avant** son premier lancement (Terraform lit le
numéro du projet, ce qui exige ces API ; sans elles : `403 Cloud Resource Manager API has not been used`) :

```bash
for P in aiml-gemini-entreprise-ldbr acme-agents-demo; do      # un seul projet ? une seule valeur
  gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com --project=$P
done
```

Les autres API (Cloud Run, Agent Platform, Model Armor, Agent Registry…) sont activées par Terraform.

### 3.4 Vos droits

| Où | Démo | Acme (moindre privilège) |
|---|---|---|
| Projet des agents | *Owner* | *Cloud Run Admin* (01-bis), *Artifact Registry Admin* (01-bis), *Cloud Build Editor*, *Storage Admin* et *Service Account User* (01-bis : construction des images par Cloud Build), *Agent Platform Admin*, *Service Account Admin*, *Project IAM Admin*, *Service Usage Admin*, *Model Armor Admin*, *Agent Registry Admin* |
| Projet de l'app | *Owner* | *Gemini Enterprise Admin*, *Service Usage Admin* ; *Project IAM Admin* si templates Model Armor ici |

En CI, c'est le compte de service de la CI qui a ces rôles.

### 3.5 L'app Gemini Enterprise

- **Elle existe** (projets 06 / 08) : noter son **ID** (Gemini Enterprise → l'app → **Présentation**) et sa
  **localisation** (`eu`).
- **Sinon** : la créer ([tutoriel 02, étape 1](02-tuto-meme-projet.md#1-prérequis--lapp-gemini-enterprise)), en `eu`.
  Gemini Enterprise demande un compte d'**organisation** (Workspace / Cloud Identity), pas un Gmail.
- **Pas encore d'app ?** Vous pouvez tout faire sauf la publication : laissez `ge_project_number` vide. Les agents sont
  déployés, inscrits dans Agent Registry et testés ; on renseignera `ge_project_number` (et, pour publier soi-même,
  `ge_project_id` + `ge_app_id`) puis on relancera `terraform apply`.

### 3.6 Model Armor

| Situation | Que mettre dans `terraform.tfvars` |
|---|---|
| Templates centraux du projet 08 (cible Acme) | `prompt_template` et `response_template` : `terraform -chdir=../08-…/terraform output model_armor_templates` |
| Pas encore de templates (démo, nouveau projet) | Rien : Terraform crée une paire de templates dans le projet des agents, dans la localisation de l'app (`eu`) |

---

## 4. Tester les agents sur votre poste

**Pourquoi d'abord en local :** si un agent ne marche pas ici, il ne marchera pas dans Gemini Enterprise. On sépare les
problèmes d'agent des problèmes de droits.

```bash
cd 09-agents-multi-projets-gemini-enterprise
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/trio/requirements.txt

# 1. Tests hors ligne : outils, Model Armor obligatoire, points d'entrée (aucun appel Google ni Internet)
python scripts/test_trio.py                     # -> tests trio OK (9 scénarios, 6 agents)

# 2. Les agents en vrai (Gemini via Vertex AI, votre identité, sans clé d'API)
export LOCAL_DEV=1 GOOGLE_CLOUD_PROJECT=acme-agents-demo
adk web --port 8080 agents/trio                 # Cloud Shell : Aperçu sur le Web > port 8080
```

Dans l'interface, choisir l'agent en haut à gauche :

| Agent | Question | Attendu |
|---|---|---|
| `meteo_agent` | « Je cours à Lille demain matin, quoi porter ? » | Outils `meteo` puis `conseil_equipement` ; météo réelle ; 3 couches ou veste imperméable selon la météo |
| `redaction_agent` | « Reformule pour un e-mail client : ton velo est pret passe avant samedi » | `charte_redactionnelle`, `analyser_texte` (×2) ; vouvoiement ; ligne « Avant : X mots, après : Y mots » |
| `redaction_agent` | « Reformule ce texte : … » (sans canal) | Il **demande** le canal |
| `traduction_agent` | « Traduis en espagnol : Votre tente Quechua est disponible en retrait en magasin. » | `glossaire`, `verifier_traduction` ; « Quechua » non traduit ; « recogida en tienda » ; « Contrôle : conforme » |
| `traduction_agent` | « Traduis en japonais : bonjour » | Refus poli : langue non prise en charge, liste des langues |

`Ctrl+C` pour arrêter.

> `No API key was provided` : le modèle part vers l'API Gemini au lieu de Vertex AI. Vérifier que `google-adk` est bien
> en **2.10** dans le venv (`pip show google-adk`). `default credentials were not found` : refaire l'étape 3.2.

---

## 5. Déployer

| Hébergement | Pas à pas |
|---|---|
| Cloud Run + A2A | [01-bis-cloud-run-a2a/README.md](../01-bis-cloud-run-a2a/README.md) |
| Agent Runtime | [02-bis-agent-runtime/README.md](../02-bis-agent-runtime/README.md) |

Les deux suivent le même plan : **configurer** (`terraform.tfvars`) → **déployer** (`terraform apply`) → **tester** sans
Gemini Enterprise (`./test.sh`) → **vérifier** Agent Registry → **publier** dans l'app → **donner l'accès** → **tester dans
le chat** → **nettoyer**.

**Tout rejouer d'un coup, commande par commande, avec la sortie attendue de chaque commande** (projet X, projet A,
simulateur, appel agent → agent entre projets) : [docs/10](10-rejouer-le-flux-complet.md).

**Connecter à Gemini Enterprise** (tous les modes de la fenêtre *Ajouter un agent*, procédure entre projets, simulateur,
fiche de demande) : [docs/09](09-connecter-a-gemini-enterprise.md).

---

## 6. Ce qui est vérifié

**Déployé de bout en bout sur un vrai projet Google Cloud** (octobre 2026, même projet, sans app Gemini Enterprise :
la publication dans l'app demande un compte d'organisation), puis entièrement supprimé avec `terraform destroy`.

| Vérifié | Résultat |
|---|---|
| Les 6 outils, Model Armor obligatoire, points d'entrée (`scripts/test_trio.py`) | OK, hors ligne |
| `adk web agents/trio` : 3 agents listés et exécutés, vrai Gemini, vraie météo, refus attendus | OK |
| 01-bis : `terraform apply` (28 ressources), URL des services = URL des cartes (postcondition) | OK |
| 01-bis : `./test.sh` sur Cloud Run, **A2A v0.3** (`message/send`, 2e tour dans la même conversation), Model Armor actif | OK, 3 agents |
| 01-bis : le conteneur en `message/stream` (streaming, utilisé par Gemini Enterprise) | OK (même image, en local) |
| Model Armor en vrai : une injection (« Ignore toutes tes instructions… ») est bloquée, une demande normale passe | OK |
| Agent Registry : les 3 cartes A2A déclarées (01-bis) **et** les 3 agents Agent Runtime inscrits **automatiquement** (02-bis) | OK |
| 02-bis : `terraform apply` (26 ressources), `./test.sh` sur Agent Runtime, outils appelés dans l'ordre prévu | OK, 3 agents |
| `terraform destroy` des deux piles, y compris des agents qui ont des sessions | OK |
| **Agent → agent entre deux projets** : l'orchestrateur (A) trouve l'agent stock dans le registre de X et l'appelle ; sans son droit, il est refusé | OK (après correction du format d'URN, voir docs/10 §10) |
| Clé d'API pour le modèle (`GEMINI_API_KEY`) : la clé est bien envoyée à l'API Gemini | OK (fausse clé refusée par Google) ; câblage Secret Manager vérifié par `terraform plan` |
| **Entre deux projets** (agents dans le projet B, app dans le projet A) : Terraform de l'équipe sans aucun droit sur A ; droit posé au **vrai** compte de Gemini Enterprise de A | OK, 01-bis et 02-bis |
| Simulateur Gemini Enterprise ([docs/09](09-connecter-a-gemini-enterprise.md#étape-4--léquipe-vérifie-avec-le-simulateur-optionnel)) : **refusé** sans droit, **accepté** avec le droit, A2A (en-tête `X-Serverless-Authorization`) et Agent Runtime | OK ; un service sans droit reste refusé |
| Format de la carte A2A, en-tête d'authentification Cloud Run, rôle `run.invoker` | Conformes à la documentation Gemini Enterprise |

**Défauts trouvés par le déploiement réel, et corrigés** (ils auraient bloqué n'importe qui suivant le tutoriel) :

| Défaut | Correction |
|---|---|
| `plan` échoue : API Resource Manager désactivée sur un projet neuf | Étape 3.3 de ce document |
| Création des identités : API IAM désactivée | Terraform active `iam.googleapis.com` (01-bis, 02-bis, `terraform/`) |
| Agent Registry refuse `interfaces` avec une carte A2A | Bloc retiré : l'URL est dans la carte (01-bis, doc 04) |
| Module `adk_agent` : sortie `name` = ID seul, au lieu de `projects/…/reasoningEngines/ID` | Sortie `name` = chemin complet, `engine_id` = ID seul |
| `scripts/query.py` et l'orchestrateur : client Agent Platform détruit avant l'appel (`AssertionError` aiohttp) | Référence au client gardée |
| `terraform destroy` refusé : l'agent a des sessions | `deletion_policy = "FORCE"` dans le module |
| Construction des images (Cloud Build, 01-bis) : `…-compute@developer.gserviceaccount.com does not have storage.objects.get access` (le compte par défaut de Cloud Build n'a aucun droit) | Compte de construction dédié (`agents-a2a-build-sa` dans Terraform, `agents-build-sa` à la main) avec 3 rôles ; plus besoin de Docker sur le poste |

| Reste à constater dans une app Gemini Enterprise Acme | Si ce n'est pas le cas |
|---|---|
| Publication par l'API (`register_agent.sh`) et réponse dans le chat | Ajout par la console (étape 7 de 01-bis, 6 de 02-bis) ; dépannage de chaque README |
| Libellés exacts des menus de la console | Ils changent souvent ; les commandes et Terraform, eux, sont stables |
