---
type: "course"
description: "Un service Terraform « managé » sur votre machine : Gitea, Atlantis, MinIO, politiques OPA, verrous et approbations, vérifié automatiquement."
tags: ["terraform", "atlantis", "opa", "gitea", "minio", "gitops"]
level: "intermediate"
duration: "2h"
usecases: ["automatisation-processus"]
date: "2026-10-05"
updated: "2026-10-14"
authors: ["Youcef"]
references:
  - title: "Gitea #39557 (règle de sortie des webhooks en v28)"
    url: https://github.com/go-gitea/gitea/issues/39557
  - title: "Atlantis"
    url: https://www.runatlantis.io/docs/
  - title: "Atlantis : configuration côté serveur"
    url: https://www.runatlantis.io/docs/server-side-repo-config
  - title: "Atlantis : politiques"
    url: https://www.runatlantis.io/docs/policy-checking
  - title: "Gitea : configuration"
    url: https://docs.gitea.com/administration/config-cheat-sheet
  - title: "Terraform : backend S3, uselockfile"
    url: https://developer.hashicorp.com/terraform/language/backend/s3
---
# Projet 07 : un « service Terraform managé » qui tourne sur votre machine

**Oui, c'est possible.** Ce projet monte en local, avec Docker, l'équivalent complet du circuit d'entreprise
**GitHub → service Terraform managé → cloud**, puis le **teste de bout en bout, automatiquement**.

| En entreprise | Ici, en local | Rôle |
|---|---|---|
| GitHub | **Gitea** | Dépôt, pull requests, revues, protection de `main`, webhooks |
| Service Terraform managé (HCP Terraform, Atlantis, plateforme interne…) | **Atlantis** | Plan automatique sur PR, politiques, verrous, apply sur approbation |
| Bucket Cloud Storage pour l'état (`backend "gcs"`) | **MinIO** (stockage compatible S3) | État distant versionné + verrouillage |
| Ressources Google Cloud | Ressources **simulées** (`terraform_data`) | Même mécanique, sans compte cloud ni coût |

> Résultat vérifié sur une installation **partant de zéro** : **24 vérifications, 0 échec**, et la simulation est
> **rejouable**. Le journal de référence est dans [`docs/execution-reference.txt`](docs/execution-reference.txt).

---

## Sommaire

1. [Architecture](#1-architecture)
2. [Prérequis](#2-prérequis)
3. [Démarrage en 3 commandes](#3-démarrage-en-3-commandes)
4. [Ce que fait l'installation, étape par étape](#4-ce-que-fait-linstallation-étape-par-étape)
5. [La simulation automatique : 3 scénarios](#5-la-simulation-automatique--3-scénarios)
6. [Refaire le parcours à la main, dans le navigateur](#6-refaire-le-parcours-à-la-main-dans-le-navigateur)
7. [Comprendre chaque fichier de configuration](#7-comprendre-chaque-fichier-de-configuration)
8. [Les pièges rencontrés pendant la mise au point, et leurs solutions](#8-les-pièges-rencontrés-pendant-la-mise-au-point-et-leurs-solutions)
9. [Passer au réel : GitHub + Google Cloud](#9-passer-au-réel--github--google-cloud)
10. [Aide-mémoire des commandes Atlantis](#10-aide-mémoire-des-commandes-atlantis)
11. [Dépannage](#11-dépannage)
12. [Nettoyage](#12-nettoyage)

---

## 1. Architecture

```
  Navigateur / scripts (votre machine)
        │ localhost:3000          │ localhost:4141           │ localhost:9001
        ▼                         ▼                          ▼
 ┌──────────────┐  webhook  ┌──────────────┐  état S3   ┌──────────────┐
 │    Gitea     │ ────────▶ │   Atlantis   │ ─────────▶ │    MinIO     │
 │  (≈ GitHub)  │ ◀──────── │ (≈ service   │  + verrou  │ (≈ Cloud     │
 │ acme/infra-  │ commentai-│   managé)    │  .tflock   │   Storage)   │
 │    demo      │ res, clone│ terraform +  │            │ bucket       │
 └──────────────┘           │ conftest     │            │ tfstate      │
                            └──────────────┘            └──────────────┘
          réseau Docker privé « tfsvc_default » : gitea:3000, atlantis:4141, minio:9000
```

**Les personnages** (comptes Gitea créés automatiquement) :

| Compte | Joue le rôle de |
|---|---|
| `alice` | Développeuse : ouvre les PR, commente `atlantis apply` |
| `bob` | Équipe sécurité : relit, approuve, et seul propriétaire des politiques |
| `atlantis-bot` | Compte de service du service Terraform (il commente dans les PR) |
| `platform-admin` | Équipe plateforme : administre Gitea et le dépôt |

**Le circuit :** PR ouverte → Gitea envoie un webhook → Atlantis clone la branche, lance `terraform init` +
`plan` → contrôle les politiques (Conftest) → publie plan et résultat dans la PR → l'apply n'est accepté que si la
PR est **approuvée** et que les **politiques passent** → l'état est écrit dans MinIO, sous verrou.

---

## 2. Prérequis

- **Docker** et **Docker Compose v2** (`docker compose version`)
- **Python 3**, **git**, **curl** (déjà présents sur la plupart des Linux)
- Accès Internet pour télécharger 3 images : `gitea/gitea`, `ghcr.io/runatlantis/atlantis`, `minio/minio`
  (environ 1 Go). L'image Atlantis embarque déjà Terraform et Conftest.
- Ports libres : **3000** (Gitea), **4141** (Atlantis), **9000/9001** (MinIO). Ils sont modifiables dans `.env`.

Versions testées : Gitea 28.0, Atlantis 0.48.0 (Terraform 1.16.3, Conftest 0.70), MinIO 2025-09.

---

## 3. Démarrage en 3 commandes

```bash
cd 07-terraform-service-local
./scripts/setup.sh              # installe et configure tout (environ 1 à 2 min, plus le téléchargement des images)
python3 scripts/scenario.py     # simule le circuit complet et vérifie chaque étape (environ 3 à 5 min)
```

Puis ouvrez :
- **Gitea** : http://localhost:3000 (`alice`, mot de passe dans `.env` : `ALICE_PASSWORD`) → *acme/infra-demo → Pull requests*
- **Atlantis** : http://localhost:4141 (verrous en cours, historique)
- **Console MinIO** : http://localhost:9001 (`MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` de `.env`) → bucket `tfstate`

Pour tout supprimer : `./scripts/teardown.sh`.

---

## 4. Ce que fait l'installation, étape par étape

Fichier : [`scripts/setup.sh`](scripts/setup.sh). Il peut être relancé sans risque (idempotent).

| # | Étape | Comment | Pourquoi |
|---|---|---|---|
| 1 | **Secrets** | Génère `.env` (mots de passe et secret du webhook aléatoires) | Aucun secret dans le code ; `.env` est ignoré par git |
| 2 | **Gitea + MinIO** | `docker compose up -d gitea minio`, puis attente de l'état *healthy* | Atlantis a besoin des deux pour démarrer |
| 3 | **Utilisateurs** | `gitea admin user create` (dans le conteneur) | Les 4 personnages |
| 4 | **Jetons d'API** | `gitea admin user generate-access-token`, enregistrés dans `.env` | Atlantis s'authentifie auprès de Gitea avec le jeton d'`atlantis-bot` |
| 5 | **Organisation et dépôt** | API Gitea : org `acme`, dépôt **privé** `infra-demo`, collaborateurs en écriture | Comme une organisation GitHub |
| 6 | **Contenu initial** | `git push` du dossier [`infra-repo/`](infra-repo/) sur `main` | Le code Terraform géré par le service |
| 7 | **Protection de `main`** | Pas de push direct, **1 approbation requise**, approbations invalidées si le code change | Toute modification passe par une PR relue |
| 8 | **Webhook** | Gitea → `http://atlantis:4141/events`, signé par un secret | Gitea prévient Atlantis à chaque PR ou commentaire |
| 9 | **Bucket d'état** | `mc mb tfstate` + **versioning** | Comme un bucket GCS d'état en production |
| 10 | **Atlantis** | `docker compose up -d atlantis`, attente de `/healthz` | Le service démarre avec sa configuration serveur |

**Vérifier à la main :**
```bash
docker compose ps                                   # 3 services "Up (healthy)"
curl -s localhost:4141/healthz                      # {"status":"ok"}
docker compose logs atlantis | grep "Atlantis started"
```

---

## 5. La simulation automatique : 3 scénarios

Fichier : [`scripts/scenario.py`](scripts/scenario.py). Il joue les personnages via l'API Gitea, attend les
réponses d'Atlantis dans les PR, et **vérifie chaque résultat** : il s'arrête à la première anomalie.

### Scénario 1 : un changement conforme, de bout en bout

| Étape | Action | Résultat vérifié |
|---|---|---|
| 02 | alice crée une branche avec un nouveau bucket (UE, labels complets) dans `envs/dev` | branche poussée |
| 03 | alice ouvre la PR | **Atlantis planifie tout seul** : « Plan: 2 to add » publié dans la PR |
| 04 | — | **Politiques : 3 tests, 3 passed** |
| 05 | alice commente `atlantis apply -p dev` **sans approbation** | **refusé** : « Pull request must be approved… » |
| 06 | bob approuve la PR | revue *Approved* |
| 07 | alice recommente `atlantis apply -p dev` | **Apply complete! Resources: 2 added** |
| 08 | — | l'état `dev/terraform.tfstate` dans MinIO contient la ressource ; plus de verrou |
| 09 | alice libère le verrou (`atlantis unlock`) et fusionne | PR fusionnée : `main` = ce qui est déployé |

### Scénario 2 : un changement non conforme est arrêté

| Étape | Action | Résultat vérifié |
|---|---|---|
| 10 | alice propose un bucket en **us-central1**, **sans** label `cost_center`, en prod | plan calculé, mais **Policy Check Failed** : « localisation 'us-central1' interdite (UE uniquement) » et « label obligatoire 'cost_center' manquant » |
| 11 | bob approuve quand même, alice tente l'apply | **refusé** : « All policies must pass for project before running apply » ; PR fermée ; **l'état prod ne contient rien** |

> C'est le point clé d'un service managé : **une approbation humaine ne suffit pas à contourner une règle de
> l'entreprise**. Seul `bob`, propriétaire des politiques, pourrait accorder une dérogation tracée
> (`atlantis approve_policies`).

### Scénario 3 : deux PR sur le même projet → verrou

| Étape | Action | Résultat vérifié |
|---|---|---|
| 12 | deux PR modifient `envs/dev` | la 1re planifie et **verrouille** le projet ; la 2e est refusée : « locked by an unapplied plan from pull #… » |
| 13 | la 1re est abandonnée (`atlantis unlock` + fermeture) | la 2e peut planifier |

> Le verrou garantit que **le plan approuvé est celui qui sera appliqué** : personne ne peut modifier la même
> infrastructure entre-temps.

Extrait du journal de référence ([complet ici](docs/execution-reference.txt)) :
```
[07] alice relance « atlantis apply -p dev » → Atlantis applique LE plan approuvé
     ✔ Apply réussi :
       │ Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
[10] alice propose un bucket en us-central1, sans label cost_center, dans envs/prod
     ✔ …mais les politiques ÉCHOUENT :
       │ FAIL - … : label obligatoire 'cost_center' manquant
       │ FAIL - … : localisation 'us-central1' interdite (UE uniquement)
━━━ BILAN : toutes les vérifications sont passées ━━━
```

---

## 6. Refaire le parcours à la main, dans le navigateur

Le meilleur moyen de comprendre est de faire le scénario 1 vous-même :

1. **Connexion** : http://localhost:3000 avec `alice` (mot de passe : `grep ALICE_PASSWORD .env`).
2. **Modifier le code** : *acme/infra-demo* → dossier `envs/dev` → **Nouveau fichier** `photos.tf` :
   ```hcl
   module "photos" {
     source   = "../../modules/gcs_bucket_sim"
     name     = "acme-dev-photos"
     location = "EU"
     labels   = { owner = "media-team", env = "dev", cost_center = "cc-2002" }
   }
   ```
   Choisissez **« Créer une nouvelle branche pour ce commit et démarrer une PR »**.
3. **Ouvrir la PR** : en quelques secondes, `atlantis-bot` commente le **plan** puis le **résultat des politiques**.
4. **Tenter l'apply** : commentez `atlantis apply -p dev` → refus (pas d'approbation).
5. **Approuver** : déconnectez-vous, connectez-vous en `bob`, ouvrez la PR → **Fichiers modifiés → Revue → Approuver**.
6. **Appliquer** : en `alice`, commentez `atlantis apply -p dev` → « Apply complete! ».
7. **Voir l'état** : console MinIO (http://localhost:9001) → `tfstate/dev/terraform.tfstate` → onglet **Versions**
   (chaque apply crée une version : c'est votre sauvegarde).
8. **Voir les verrous** : http://localhost:4141 → liste des verrous. Puis `atlantis unlock` et **Fusionner**.

**Variante « politique » :** refaites l'étape 2 avec `location = "us-east1"` : Atlantis affichera
**Policy Check Failed** avec le motif exact.

> Les liens publiés par Gitea pointent vers `http://gitea:3000/…` (adresse interne au réseau Docker). Pour les
> ouvrir tels quels depuis le navigateur, ajoutez `127.0.0.1 gitea` à `/etc/hosts`, ou remplacez `gitea` par
> `localhost` dans l'URL.

---

## 7. Comprendre chaque fichier de configuration

### 7.1 [`docker-compose.yml`](docker-compose.yml) : les 3 services

| Réglage | Rôle |
|---|---|
| `GITEA__security__INSTALL_LOCK` | Pas d'assistant d'installation web : tout est scripté |
| `GITEA__server__ROOT_URL=http://gitea:3000/` + `PUBLIC_URL_DETECTION=never` | Les URL de clonage envoyées à Atlantis utilisent le nom **joignable depuis le réseau Docker** (voir §8) |
| `GITEA__security__ALLOWED_HOST_LIST=private` | Autorise les webhooks vers des **adresses privées** uniquement (portée minimale pour joindre `atlantis`) |
| `ATLANTIS_REPO_ALLOWLIST` | Atlantis n'accepte que les dépôts de l'organisation `acme` |
| `ATLANTIS_GITEA_WEBHOOK_SECRET` | Atlantis rejette tout webhook non signé par Gitea |
| `ATLANTIS_REPO_CONFIG=/config/repos.yaml` | Les **règles du service**, côté serveur |
| `ATLANTIS_ENABLE_POLICY_CHECKS` | Active le contrôle des politiques sur chaque plan |
| `ATLANTIS_DEFAULT_TF_VERSION` + `ATLANTIS_TF_DOWNLOAD=false` | Version de Terraform **figée** (celle de l'image) : aucun téléchargement pendant un run |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Identifiants du backend d'état (MinIO). En production GCP : **aucune clé**, identité attachée (§9) |

### 7.2 [`atlantis/repos.yaml`](atlantis/repos.yaml) : la politique du service (côté serveur)

```yaml
repos:
  - id: /.*/
    apply_requirements: [approved, mergeable]   # pas d'apply sans PR approuvée et fusionnable
    allow_custom_workflows: false               # un dépôt ne peut pas injecter ses propres commandes
    policy_check: true                          # politiques obligatoires
policies:
  owners: { users: [bob] }                      # seule la sécurité peut accorder une dérogation
  policy_sets:
    - { name: socle-entreprise, path: /policies, source: local }
```
**Pourquoi côté serveur :** si ces règles étaient dans le dépôt, une PR pourrait les assouplir. Ici, elles
s'imposent à tous les dépôts.

### 7.3 [`infra-repo/atlantis.yaml`](infra-repo/atlantis.yaml) : la configuration côté dépôt

Elle déclare les **projets** (`dev` = `envs/dev`, `prod` = `envs/prod`) et **quand planifier**
(`when_modified` : les `.tf` du dossier et des modules). Chaque projet a son état et son verrou.

### 7.4 [`policies/baseline.rego`](policies/baseline.rego) : les règles de l'entreprise

Écrites en **Rego** (langage d'OPA), évaluées par **Conftest** sur le **plan JSON** :
1. localisation **UE uniquement** ;
2. labels obligatoires `owner`, `env`, `cost_center` ;
3. pas de bucket public.

Chaque règle `deny` renvoie un **message clair**, affiché dans la PR.

### 7.5 [`infra-repo/envs/*/main.tf`](infra-repo/envs/dev/main.tf) : le backend d'état

```hcl
backend "s3" {
  bucket       = "tfstate"
  key          = "dev/terraform.tfstate"     # un état par environnement
  endpoints    = { s3 = "http://minio:9000" }
  use_lockfile = true                          # verrou natif (fichier .tflock), Terraform >= 1.10
  ...
}
```
En production sur Google Cloud : `backend "gcs" { bucket = "acme-tfstate-prod", prefix = "dev" }`. Le verrou est
natif, l'objet `.tflock` étant créé par écriture conditionnelle.

### 7.6 [`infra-repo/modules/gcs_bucket_sim`](infra-repo/modules/gcs_bucket_sim/main.tf) : la ressource simulée

`terraform_data` enregistre la configuration d'un bucket (nom, localisation, labels, public) **sans appeler de
cloud**. Pour passer en réel, on remplace ce bloc par `google_storage_bucket` avec les mêmes variables. Les
politiques, les PR, les verrous et l'état fonctionnent à l'identique.

---

## 8. Les pièges rencontrés pendant la mise au point, et leurs solutions

Ces problèmes sont apparus réellement pendant les tests. Ils sont corrigés dans les fichiers, mais les connaître
vous fera gagner des heures.

| Symptôme | Cause | Solution appliquée |
|---|---|---|
| Atlantis ne réagit à aucune PR ; journal Gitea : `denied by egress policy` | **Gitea ≥ 28** bloque les webhooks vers les adresses privées ; le réglage a migré de `[webhook]` vers **`[security] ALLOWED_HOST_LIST`** | `GITEA__security__ALLOWED_HOST_LIST: "private"` (et l'ancien réglage, gardé pour les versions antérieures) |
| Atlantis répond « This repo is not allowlisted » | Gitea ≥ 1.24 construit ses URL à partir de **l'hôte de la requête** (`localhost`) au lieu de `ROOT_URL` : Atlantis reçoit `localhost`, qui ne correspond pas à la liste blanche (et n'est pas joignable depuis son conteneur) | `GITEA__server__PUBLIC_URL_DETECTION: "never"` |
| Le verrou d'une PR fermée bloque les autres PR | Avec **Gitea**, Atlantis 0.48 reçoit la fermeture d'une PR comme un événement « other » et **ne libère pas** le verrou (avec GitHub, c'est automatique) | Commenter **`atlantis unlock`** avant de fermer ou fusionner une PR (fait par le scénario). En cas d'oubli : bouton *Unlock* sur http://localhost:4141 |
| Le plan annonce « 2 to add » au lieu de 1 | Le bucket initial de `main` n'avait jamais été appliqué en dev : le premier apply l'inclut | Comportement normal : le plan montre **tout** l'écart entre code et réalité |
| Le commentaire de plan est replié (« Superseded ») | Atlantis masque son commentaire précédent quand il publie le résultat des politiques (`HIDE_PREV_PLAN_COMMENTS`) | Normal : dépliez le commentaire pour voir le plan |

---

## 9. Passer au réel : GitHub + Google Cloud

La mécanique reste la même ; seules les briques changent.

| Brique | Local | Réel |
|---|---|---|
| Dépôt | Gitea | **GitHub** : flags `ATLANTIS_GH_USER`/`ATLANTIS_GH_TOKEN` ou, mieux, une **GitHub App** (`ATLANTIS_GH_APP_ID`, clé privée, `ATLANTIS_GH_WEBHOOK_SECRET`) ; branche `main` protégée + CODEOWNERS |
| Hébergement d'Atlantis | Docker local | **Cloud Run** ou **GKE**, derrière HTTPS (et IAP pour l'interface) ; disque persistant pour `/atlantis-data` (ou base Redis pour les verrous) |
| Identité vers Google Cloud | — | **Compte de service attaché** à Atlantis (Workload Identity sur GKE, compte de service Cloud Run) ; **aucune clé JSON** ; droits limités aux dossiers gérés ; idéalement un compte par projet Atlantis via `impersonate_service_account` |
| État | MinIO (`backend "s3"`) | **`backend "gcs"`** : bucket versionné, CMEK, accès réservé au compte d'Atlantis |
| Ressources | `terraform_data` | `google_*` (provider `hashicorp/google`) |
| Politiques | Conftest local | Mêmes fichiers Rego, versionnés dans un dépôt « policies » relu par la sécurité |
| Secrets | `.env` | **Secret Manager** (jeton GitHub, secret du webhook), injectés dans Cloud Run ou GKE |

**Exemple : Atlantis sur Cloud Run** (extrait, à adapter) :
```bash
gcloud run deploy atlantis --image ghcr.io/runatlantis/atlantis:latest --region europe-west1 \
  --service-account atlantis-runner@acme-iac.iam.gserviceaccount.com \
  --set-secrets ATLANTIS_GH_TOKEN=atlantis-gh-token:latest,ATLANTIS_GH_WEBHOOK_SECRET=atlantis-webhook:latest \
  --set-env-vars ATLANTIS_REPO_ALLOWLIST=github.com/acme/*,ATLANTIS_ATLANTIS_URL=https://atlantis.acme.example \
  --min-instances 1 --max-instances 1     # Atlantis garde ses verrous localement : une seule instance
```
> Atlantis est **mono-instance** par défaut (verrous dans une base locale BoltDB). Pour la haute disponibilité :
> backend de verrous **Redis** (`ATLANTIS_LOCKING_DB_TYPE=redis`) et stockage partagé. C'est l'une des raisons
> pour lesquelles les grandes entreprises choisissent souvent un service managé (HCP Terraform, Spacelift…) ou une
> plateforme interne.

Et avec **Gemini Enterprise** : le dépôt `infra-gemini-enterprise` (chapitre 26 du guide Terraform) se branche
exactement comme `infra-demo`. Atlantis planifie `envs/recette` et `envs/prod`, la politique vérifie par exemple
« localisation eu », « Model Armor en FAIL_CLOSED », « connecteurs en FEDERATED », et l'image Atlantis doit
contenir `gcloud` et `curl` pour les réglages REST du socle (image personnalisée `FROM ghcr.io/runatlantis/atlantis`).

---

## 10. Aide-mémoire des commandes Atlantis

À écrire en **commentaire** de la PR :

| Commande | Effet |
|---|---|
| `atlantis plan` / `atlantis plan -p dev` | (Re)planifier tous les projets / le projet `dev` |
| `atlantis apply -p dev` | Appliquer le plan approuvé du projet `dev` |
| `atlantis unlock` | Abandonner les plans et libérer les verrous de la PR |
| `atlantis approve_policies` | Dérogation aux politiques (propriétaires des politiques uniquement : `bob`) |
| `atlantis import -p dev ADRESSE ID` | Importer une ressource existante dans l'état |
| `atlantis state rm -p dev ADRESSE` | Retirer une ressource de l'état sans la détruire |
| `atlantis help` | Aide |

---

## 11. Dépannage

| Symptôme | Où regarder | Solution |
|---|---|---|
| Aucun commentaire d'Atlantis | `docker compose logs gitea \| grep -i deliver` | Voir §8 (règle de sortie Gitea) ; vérifier le secret du webhook |
| « not allowlisted » | `curl -s -H "Authorization: token $ALICE_TOKEN" localhost:3000/api/v1/repos/acme/infra-demo \| grep clone_url` | `clone_url` doit commencer par `http://gitea:3000` (§8) |
| « locked by an unapplied plan » | http://localhost:4141 | `atlantis unlock` sur la PR qui tient le verrou, ou bouton *Unlock* |
| Erreur `init` sur le backend | `docker compose logs atlantis` | MinIO démarré ? bucket `tfstate` créé ? identifiants `.env` |
| Diagnostic détaillé | `ATLANTIS_LOG_LEVEL=debug docker compose up -d atlantis` | Puis `docker compose logs -f atlantis` |
| Rejouer un scénario interrompu | — | Relancer `python3 scripts/scenario.py` : il supprime les verrous résiduels au démarrage |

---

## 12. Nettoyage

```bash
./scripts/teardown.sh      # supprime conteneurs, volumes (dépôts, états, verrous) et .env
```

---

## Fichiers

```
07-terraform-service-local/
├── docker-compose.yml          ← Gitea + MinIO + Atlantis
├── atlantis/repos.yaml         ← règles du service (côté serveur)
├── policies/baseline.rego      ← politiques de l'entreprise (Conftest / OPA)
├── infra-repo/                 ← contenu du dépôt acme/infra-demo poussé dans Gitea
│   ├── atlantis.yaml           ← projets dev / prod
│   ├── envs/dev/main.tf · envs/prod/main.tf   ← backend d'état + modules
│   └── modules/gcs_bucket_sim/ ← « bucket GCS » simulé
├── scripts/
│   ├── setup.sh                ← installation complète (idempotente)
│   ├── scenario.py             ← simulation pas à pas avec vérifications
│   └── teardown.sh             ← tout supprimer
└── docs/execution-reference.txt← journal d'une exécution réussie depuis zéro
```

**Sources :** [Atlantis](https://www.runatlantis.io/docs/) ·
[Atlantis : configuration côté serveur](https://www.runatlantis.io/docs/server-side-repo-config) ·
[Atlantis : politiques](https://www.runatlantis.io/docs/policy-checking) ·
[Gitea : configuration](https://docs.gitea.com/administration/config-cheat-sheet) ·
[Gitea #39557 (règle de sortie des webhooks en v28)](https://github.com/go-gitea/gitea/issues/39557) ·
[Terraform : backend S3, `use_lockfile`](https://developer.hashicorp.com/terraform/language/backend/s3)
