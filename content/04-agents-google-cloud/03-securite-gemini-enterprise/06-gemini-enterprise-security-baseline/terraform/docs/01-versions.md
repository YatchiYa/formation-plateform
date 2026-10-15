# 01. `versions.tf` : versions et configuration du provider Google

> Ce fichier fixe les versions de Terraform et du plugin Google, prépare l'état distant (commenté) et indique à quel
> projet Google Cloud parler. Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

C'est le « réglage de la machine » avant toute ressource. Il garantit que tout le monde (vous, un collègue, la CI)
utilise **les mêmes versions** : sans cela, un même code peut produire des résultats différents d'un poste à l'autre.
Il configure aussi le **provider Google** : le projet, la région, et le projet qui paie les appels d'API. Enfin, il
prépare le stockage de l'**état Terraform** dans un bucket chiffré, pour la production.

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `terraform` | `terraform` | Exige une version minimale de Terraform et déclare le provider `hashicorp/google` avec sa plage de versions. |
| `required_providers.google` | sous-bloc de `terraform` | Indique **d'où** télécharger le provider et **quelles versions** accepter. |
| `backend "gcs"` (commenté) | sous-bloc de `terraform` | Modèle (inactif) pour stocker l'état dans un bucket Cloud Storage. |
| `provider "google"` | `provider` | Configure le plugin Google : projet, région, projet de facturation des appels. |

---

## 3. Le code expliqué, bloc par bloc

### 3.1 Le bloc `terraform` : les versions

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }
```

- `terraform { … }` : bloc de réglages de **Terraform lui-même**, pas de Google Cloud. Il ne crée rien. Voir
  [00-bases §5](00-bases-terraform.md#5-la-syntaxe--des-blocs).
- `required_version = ">= 1.9"` : Terraform **refuse de démarrer** si votre version est plus ancienne que 1.9.
  - Pourquoi : éviter qu'un poste avec un vieux Terraform interprète le code différemment. Le fichier ne dit pas
    pourquoi 1.9 précisément (version minimale retenue par l'équipe, **à vérifier** si vous voulez la baisser).
  - Vérifier sa version : `terraform version`.
- `required_providers { … }` : la liste des **providers** (plugins) dont le projet a besoin. Un provider est le
  plugin qui sait parler à une API, ici celle de Google Cloud. Voir
  [00-bases §13](00-bases-terraform.md#13-les--providers--et-la-doc).
- `google = { … }` : le **nom local** du provider. C'est ce nom qu'on retrouve dans `provider "google"` plus bas et
  dans le préfixe des ressources (`google_kms_key_ring`, `google_project_service`…).
- `source = "hashicorp/google"` : **où** `terraform init` télécharge le plugin. Forme complète :
  `registry.terraform.io/hashicorp/google`.
- `version = "~> 8.4"` : **quelles versions** sont acceptées. L'opérateur `~>` (« pessimiste ») autorise seulement le
  **dernier chiffre écrit** à augmenter :
  - `~> 8.4` accepte `8.4`, `8.5`, `8.12`… mais **pas** `9.0` ;
  - `~> 8.4.0` n'accepterait que `8.4.x`.
  - Pourquoi : on prend les correctifs et nouveautés de la version 8, mais on refuse une version majeure 9 qui
    pourrait casser le code. Le README indique que le socle a été validé avec la 8.4.

> **Le fichier `.terraform.lock.hcl`** (créé par `terraform init`) note la version **exacte** téléchargée (ici
> `8.5.0`) et son empreinte. Il se committe : ainsi tout le monde utilise exactement la même version. Pour monter de
> version dans la plage autorisée : `terraform init -upgrade`.

### 3.2 Le bloc `backend "gcs"` (commenté) : où stocker l'état

```hcl
  # Production : état distant chiffré, versionné, accès restreint à l'équipe plateforme.
  # backend "gcs" {
  #   bucket = "acme-tfstate-gemini-enterprise"
  #   prefix = "security-baseline"
  # }
}
```

- Toutes ces lignes commencent par `#` : ce sont des **commentaires**. Terraform les ignore. Le bloc est donc
  **inactif** : l'état est stocké **localement**, dans `terraform.tfstate` à côté des fichiers. Voir
  [00-bases §3](00-bases-terraform.md#3-létat--state-).
- `backend "gcs"` : dit à Terraform de ranger l'état dans un **bucket Cloud Storage** (GCS = Google Cloud Storage).
- `bucket` : le nom du bucket (il doit exister **avant** `terraform init` ; Terraform ne le crée pas).
- `prefix` : le « dossier » dans le bucket. Utile pour ranger plusieurs projets Terraform dans un même bucket.
- Pourquoi c'est prévu pour la production : l'état contient des identifiants de ressources et parfois des valeurs
  sensibles. Le commentaire du code résume les exigences : **chiffré, versionné** (on peut revenir à un état
  précédent), **accès restreint** à l'équipe plateforme. En équipe, un état partagé évite aussi que deux personnes
  aient chacune « leur » vision de l'infrastructure.
- L'accolade `}` finale ferme le bloc `terraform` ouvert en 3.1.

### 3.3 Le bloc `provider "google"` : à qui et comment parler

```hcl
provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true # requis par les API Discovery Engine (connecteurs)
}
```

- `provider "google"` : configure le plugin déclaré en 3.1. Ces réglages s'appliquent **par défaut** à toutes les
  ressources `google_*` du dossier.
- `project = var.project_id` : le **projet Google Cloud** par défaut. Un projet est le « conteneur » qui regroupe des
  ressources, des droits et une facturation. Valeur : la variable `project_id` de
  [`variables.tf`](../variables.tf) (ex. `"acme-gemini-enterprise-prd"` dans `terraform.tfvars.example`).
  - Conséquence : une ressource qui n'a pas d'argument `project` (ex. `google_discovery_engine_acl_config` dans
    `10_identity_access.tf`) est créée dans ce projet. `data "google_project" "this" {}` lit aussi ce projet.
- `region = var.region` : la **région** par défaut (défaut : `"europe-west1"`, en Belgique). Utilisée par les
  ressources régionales qui ne précisent pas leur région.
- `billing_project = var.project_id` : le projet auquel Google **attribue les quotas et la facturation** des appels
  d'API faits par Terraform. Ici, le même projet.
- `user_project_override = true` : demande au provider d'**envoyer `billing_project`** avec chaque requête (en-tête
  HTTP `X-Goog-User-Project`).
  - Pourquoi : quand vous déployez avec **votre compte utilisateur** (`gcloud auth application-default login`),
    certaines API, dont **Discovery Engine** (l'API de Gemini Enterprise, utilisée par les connecteurs), refusent les
    appels qui ne précisent pas de « projet de quota ». Le commentaire du code le rappelle.
  - Condition : le compte qui déploie doit avoir la permission `serviceusage.services.use` sur ce projet (incluse
    dans les rôles Owner/Editor ; **à vérifier** si vous utilisez des rôles plus fins).

Ce que `var.` signifie : voir [00-bases §6.3](00-bases-terraform.md#63-variable--les-entrées) et
[§7](00-bases-terraform.md#7-les-références--relier-les-blocs-entre-eux).

---

## 4. Ce que Terraform crée concrètement

**Rien dans Google Cloud.** Ce fichier ne contient ni `resource` ni `data`.

Effets concrets :
- `terraform init` télécharge le provider `hashicorp/google` (version 8.x) dans le dossier caché `.terraform/` et
  écrit/lit `.terraform.lock.hcl` ;
- toutes les commandes échouent tout de suite si Terraform est plus ancien que 1.9 ;
- toutes les ressources `google_*` utilisent par défaut le projet `project_id` et la région `region`.

Nombre de ressources créées par ce fichier : **0**.

---

## 5. Dépendances avec les autres fichiers

| Valeur utilisée ici | Vient de |
|---|---|
| `var.project_id` (2 fois) | [`variables.tf`](../variables.tf), section 1, voir [02-variables.md](02-variables.md) |
| `var.region` | [`variables.tf`](../variables.tf), section 1 |

| Qui utilise ce fichier | Comment |
|---|---|
| **Tous** les fichiers `.tf` qui déclarent des ressources `google_*` | Ils passent par ce provider (projet, région, facturation par défaut). |
| [`00_foundation.tf`](../00_foundation.tf) | `data "google_project" "this" {}` lit le projet configuré ici. Voir [03-foundation.md](03-foundation.md). |
| [`10_identity_access.tf`](../10_identity_access.tf) | `google_discovery_engine_acl_config` n'a pas d'argument `project` : il hérite de celui du provider. Voir [04-identity-access.md](04-identity-access.md). |
| [`40_connectors.tf`](../40_connectors.tf) | Les connecteurs Discovery Engine ont besoin de `user_project_override`. |

---

## 6. Pour reproduire / adapter

Modèle générique à copier dans un nouveau dossier Terraform :

```hcl
terraform {
  # Version minimale de Terraform acceptée (vérifiez la vôtre avec `terraform version`).
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google" # registry.terraform.io/hashicorp/google
      version = "~> 8.4"           # 8.x à partir de 8.4, jamais 9.0
    }
  }

  # À décommenter quand le bucket existe (il n'est PAS créé par Terraform).
  # Pas de variables possibles ici : valeurs écrites en dur, ou `terraform init -backend-config=...`.
  # backend "gcs" {
  #   bucket = "MON-BUCKET-TFSTATE"
  #   prefix = "mon-projet"
  # }
}

provider "google" {
  project = var.project_id # projet par défaut de toutes les ressources google_*
  region  = var.region     # région par défaut

  # Utile si vous déployez avec votre compte utilisateur et qu'une API exige un "projet de quota".
  billing_project       = var.project_id
  user_project_override = true
}
```

Étapes :

1. Copiez le modèle dans `versions.tf` et déclarez `project_id` et `region` dans `variables.tf` (voir
   [02-variables.md](02-variables.md)).
2. Choisissez la plage de versions du provider : regardez la dernière version sur
   `https://registry.terraform.io/providers/hashicorp/google/latest` et notez `~> MAJEURE.MINEURE`.
3. Connectez-vous : `gcloud auth login` **et** `gcloud auth application-default login` (c'est ce second login que
   Terraform utilise).
4. Lancez `terraform init` : le provider est téléchargé et `.terraform.lock.hcl` est créé. Committez ce fichier.
5. Pour la production : créez un bucket (versionné, accès restreint), décommentez `backend "gcs"`, puis relancez
   `terraform init` (Terraform propose de migrer l'état local vers le bucket).

Documentation :
- Configuration du provider (`project`, `region`, `billing_project`, `user_project_override`) :
  `https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/provider_reference`
- Backend GCS : `https://developer.hashicorp.com/terraform/language/backend/gcs`
- Contraintes de version (`~>`, `>=`) : `https://developer.hashicorp.com/terraform/language/expressions/version-constraints`

---

## 7. Pièges et bonnes pratiques

- **Le bloc `backend` n'accepte pas de variables.** `bucket = var.bucket` provoque une erreur. Écrivez la valeur en
  dur ou passez-la avec `terraform init -backend-config="bucket=..."`.
- **Ne committez jamais `terraform.tfstate`**, mais **committez** `.terraform.lock.hcl`.
- **Changer de backend** (local → GCS) exige `terraform init` à nouveau. Lisez bien la question de migration.
- **Ne mettez pas `version = ">= 8.4"`** : cela autoriserait un futur 9.0 incompatible. Préférez `~>`.
- **Erreur « quota project » / « requires a quota project »** sur Discovery Engine : vérifiez que
  `user_project_override = true` et `billing_project` sont bien présents.
- **Le projet par défaut s'applique partout.** Si une ressource doit aller dans un autre projet, renseignez son
  argument `project` explicitement.
- **Pas d'identifiants dans ce fichier** (pas de `credentials = "clé.json"`) : utilisez
  `gcloud auth application-default login` en local, et l'identité du compte de service en CI.
