# 03. `00_foundation.tf` : APIs, service agents et valeurs communes

> Ce fichier prépare le projet : il lit son numéro, calcule des valeurs partagées, active les API et force la
> création des comptes techniques de Google. Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Avant de créer une app Gemini Enterprise, des clés ou des filtres, le projet doit être **prêt** : les services Google
utilisés doivent être activés, et les **service agents** doivent exister. Un **service agent** est un compte
technique géré par Google, qui agit pour un service dans votre projet (ex. le compte de Gemini Enterprise qui lit les
sources, appelle Model Armor et chiffre avec la clé KMS). Ce fichier calcule aussi, **une seule fois**, des valeurs
utilisées partout ailleurs (numéro de projet, localisation KMS, identité de Gemini Enterprise). Ainsi, la règle
« app `eu` → clé `europe` » est écrite à un seul endroit.

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `data.google_project.this` | data | Lit les informations du projet (dont son **numéro**). |
| `local.project_number` | locals | Numéro du projet, réutilisé dans les noms de service agents et d'API. |
| `local.de_host` | locals | Adresse de l'API Gemini Enterprise de la bonne multi-région. |
| `local.kms_location` | locals | Localisation KMS qui correspond à l'app (`eu` → `europe`). |
| `local.regional_kms_locations` | locals | Les 3 régions des clés exigées pour les connecteurs tiers en ingestion + CMEK. |
| `local.ge_sa` | locals | Identité IAM du service agent Gemini Enterprise. |
| `google_project_service.apis` | resource | Active les API Google nécessaires (7, ou 13 avec Agent Gateway). |
| `terraform_data.service_agents` | resource | Lance `gcloud` pour créer les service agents Discovery Engine et Model Armor. |

---

## 3. Le code expliqué, bloc par bloc

### 3.1 Commentaire d'en-tête et `data "google_project" "this"`

```hcl
# Fondations : APIs et "service agents" (comptes gérés par Google qui agissent
# pour Gemini Enterprise dans le projet).

data "google_project" "this" {}
```

- Les deux premières lignes sont des commentaires (`#`).
- `data "google_project" "this" {}` : une **source de données**. Elle **lit** un projet existant, elle ne crée rien
  (voir [00-bases §6.2](00-bases-terraform.md#62-data--ce-que-terraform-lit)).
  - `google_project` : le type ; `this` : le nom local (convention pour « le projet courant »).
  - `{}` vide : aucun argument, donc le provider lit **le projet configuré dans `versions.tf`**
    (`project = var.project_id`, voir [01-versions.md](01-versions.md)).
  - Pourquoi : on a besoin du **numéro** du projet (ex. `123456789012`), alors que la variable fournit seulement son
    **ID** (`acme-gemini-enterprise-prd`). Les noms des service agents utilisent le numéro.
  - Lecture de l'attribut : `data.google_project.this.number`.

### 3.2 Le bloc `locals` : les valeurs calculées partagées

```hcl
locals {
  project_number = data.google_project.this.number
  de_host        = "${var.ge_location}-discoveryengine.googleapis.com"
  kms_location   = var.ge_location == "eu" ? "europe" : "us" # multi-région KMS correspondante
```

Un bloc `locals` donne un nom à des expressions ; on les lit avec `local.<nom>` (voir
[00-bases §6.4](00-bases-terraform.md#64-locals--les-valeurs-calculées)). Valeurs ci-dessous avec les valeurs par
défaut (`ge_location = "eu"`) ; le numéro de projet `123456789012` est fictif.

- `project_number = data.google_project.this.number` : copie le numéro lu en 3.1 sous un nom court.
  → `"123456789012"`.
- `de_host = "${var.ge_location}-discoveryengine.googleapis.com"` : **interpolation** : `${…}` insère une valeur dans
  un texte (voir [00-bases §7](00-bases-terraform.md#7-les-références--relier-les-blocs-entre-eux)).
  → `"eu-discoveryengine.googleapis.com"`.
  - Pourquoi : une app `eu` se pilote via l'adresse d'API **régionale** `eu-…`. Elle sert aux appels `curl` de
    [`50_app.tf`](../50_app.tf) (réglages que le provider ne sait pas encore faire).
- `kms_location = var.ge_location == "eu" ? "europe" : "us"` : **condition ternaire** `condition ? si_vrai : si_faux`
  (voir [00-bases §12.1](00-bases-terraform.md#121-condition-ternaire)). `==` compare deux valeurs.
  → `"eu" == "eu"` est vrai, donc `"europe"`.
  - Pourquoi : Gemini Enterprise appelle sa multi-région `eu`, mais Cloud KMS appelle la sienne `europe`. Une app
    `eu` exige une clé en `europe` ([README §6.1](../../README.md#61-cmek--chiffrement-avec-les-clés-de-acme)).
  - Le « sinon » donne `"us"` : c'est sûr, car `ge_location` est validée à `eu` ou `us` seulement
    (voir [02-variables.md](02-variables.md)).

```hcl
  # Clés régionales exigées par les connecteurs TIERS en mode ingestion + CMEK.
  regional_kms_locations = var.ge_location == "eu" ? ["europe-west1", "europe-west4", "europe-north1"] : ["us-east1", "us-central1", "us-west1"]
```

- Même ternaire, mais chaque branche est une **liste**.
  → `["europe-west1", "europe-west4", "europe-north1"]` (Belgique, Pays-Bas, Finlande).
- Pourquoi : selon la documentation Google reprise dans le README, les connecteurs **tiers** (SharePoint, Jira…) en
  mode **ingestion** avec CMEK exigent en plus des clés **régionales** dans ces trois régions.
- Utilisée dans [`20_data_protection.tf`](../20_data_protection.tf) : `for_each` crée un trousseau et une clé par
  région.

```hcl
  # Identité de Gemini Enterprise : lit les sources, appelle Model Armor, chiffre avec KMS.
  ge_sa = "serviceAccount:service-${local.project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}
```

- `ge_sa` (*Gemini Enterprise service account*) : l'adresse du **service agent Discovery Engine** (Discovery Engine =
  le nom technique de l'API de Gemini Enterprise), écrite au format **membre IAM** (`serviceAccount:` + e-mail).
  → `"serviceAccount:service-123456789012@gcp-sa-discoveryengine.iam.gserviceaccount.com"`.
- Un local peut utiliser un autre local (`local.project_number`) : Terraform calcule l'ordre tout seul.
- Pourquoi un local : ce compte reçoit plusieurs droits dans plusieurs fichiers (utiliser la clé KMS, lire les
  secrets, appeler Model Armor). On écrit son adresse **une seule fois**, sans faute de frappe possible.
- La `}` ferme le bloc `locals`.

### 3.3 `google_project_service.apis` : activer les API

Une **API** est un service Google qu'on appelle par programme (Gemini Enterprise, KMS…). Dans un projet, chaque API
doit être **activée** avant usage, sinon les appels échouent avec « API has not been used in project… ».

```hcl
resource "google_project_service" "apis" {
  for_each = toset(concat(
    [
      "discoveryengine.googleapis.com", # Gemini Enterprise
      "modelarmor.googleapis.com",      # filtrage IA
      "dlp.googleapis.com",             # détecteurs de données sensibles (FR)
      "cloudkms.googleapis.com",        # CMEK
      "secretmanager.googleapis.com",   # secrets des connecteurs
      "logging.googleapis.com",
      "monitoring.googleapis.com",
    ],
    var.enable_agent_gateway ? ["networkservices.googleapis.com", "networksecurity.googleapis.com", "agentregistry.googleapis.com", "certificatemanager.googleapis.com", "compute.googleapis.com", "iap.googleapis.com"] : [],
    var.vpc_sc_access_policy != "" ? ["accesscontextmanager.googleapis.com"] : [],
  ))
```

Lisons l'expression `for_each` de l'intérieur vers l'extérieur :

1. **Première liste** : 7 API toujours nécessaires (Gemini Enterprise, Model Armor, DLP, KMS, Secret Manager,
   journaux, supervision). Chaque commentaire dit à quoi elle sert.
2. **Seconde liste** : `var.enable_agent_gateway ? [6 API] : []`. Ternaire : si Agent Gateway est activé, 6 API
   réseau/sécurité de plus ; sinon une liste **vide**. Défaut : `false`, donc `[]`.
3. `concat(liste1, liste2)` : colle les deux listes (voir
   [00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)). Avec les valeurs d'exemple :
   7 + 0 = 7 éléments.
4. `toset(…)` : transforme la liste en **set** (ensemble sans doublon, sans ordre). `for_each` n'accepte qu'un set ou
   une map, pas une liste.
5. `for_each = …` : crée **une ressource par élément** (voir
   [00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set)). Avec un set,
   `each.key` et `each.value` valent tous les deux l'élément en cours (ex. `"cloudkms.googleapis.com"`).

Résultat : 7 ressources, d'adresses `google_project_service.apis["discoveryengine.googleapis.com"]`,
`google_project_service.apis["modelarmor.googleapis.com"]`, etc.

Pourquoi `for_each` plutôt que 7 blocs : un seul bloc à maintenir, et chaque API a une **clé stable** (son nom).
Ajouter ou retirer une API ne touche pas aux autres.

```hcl
  service            = each.value
  disable_on_destroy = false
}
```

- `service = each.value` : le nom de l'API à activer pour cet exemplaire.
- `disable_on_destroy = false` : si Terraform détruit cette ressource (`terraform destroy`, ou retrait d'une API de
  la liste), il **n'éteint pas** l'API dans le projet.
  - Pourquoi : d'autres outils ou équipes peuvent utiliser la même API dans le projet. Couper `logging` ou `cloudkms`
    par erreur casserait bien plus que ce socle.
- Pas d'argument `project` : c'est le projet du provider (`var.project_id`).

### 3.4 `terraform_data.service_agents` : forcer la création des service agents

```hcl
# Les service agents sont créés "à la demande" par Google : on force leur création
# pour que les droits IAM ci-dessous puissent leur être attribués.
resource "terraform_data" "service_agents" {
  triggers_replace = var.project_id
```

- Le problème : Google crée un service agent **au premier usage** du service. Or on veut lui donner des droits
  (ex. utiliser la clé KMS) **avant** ce premier usage. Donner un rôle à un compte qui n'existe pas encore échoue.
- `terraform_data` : une ressource « vide » intégrée à Terraform (pas au provider Google). Elle sert de support pour
  lancer une commande. Voir [00-bases §14](00-bases-terraform.md#14-quand-terraform-ne-sait-pas-faire--terraform_data--local-exec).
- `triggers_replace = var.project_id` : si cette valeur change, la ressource est recréée et la commande relancée.
  Ici : seulement si l'on change de projet. Sinon, la commande ne tourne **qu'une fois**, au premier `apply`.

```hcl
  provisioner "local-exec" {
    command = <<-EOT
      gcloud beta services identity create --service=discoveryengine.googleapis.com --project=${var.project_id}
      gcloud beta services identity create --service=modelarmor.googleapis.com --project=${var.project_id}
    EOT
  }
```

- `provisioner "local-exec"` : exécute `command` **sur la machine qui lance `terraform apply`** (votre poste ou la
  CI), pas chez Google.
- `<<-EOT … EOT` : un **heredoc**, texte sur plusieurs lignes (voir
  [00-bases §12.3](00-bases-terraform.md#123-texte-sur-plusieurs-lignes--heredoc-)). Le `-` retire l'indentation
  commune. On peut y interpoler des valeurs : `${var.project_id}` devient
  `acme-gemini-enterprise-prd`.
- `gcloud beta services identity create --service=X` : demande à Google de **créer maintenant** le service agent du
  service X. Deux commandes :
  - Discovery Engine → `service-<n°>@gcp-sa-discoveryengine.iam.gserviceaccount.com` (c'est `local.ge_sa`) ;
  - Model Armor → `service-<n°>@gcp-sa-modelarmor.iam.gserviceaccount.com` (utilisé dans
    [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) pour lire le template DLP).
- Si le compte existe déjà, la commande le renvoie simplement (comportement attendu de `identity create`, **à
  vérifier** sur votre version de `gcloud`).

```hcl
  depends_on = [google_project_service.apis]
}
```

- `depends_on` : force l'ordre (voir [00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on)).
  La commande ne fait référence à aucune ressource, donc Terraform ne devinerait pas qu'il faut d'abord activer les
  API. Or on ne peut pas créer le service agent d'une API désactivée.
- Référencer `google_project_service.apis` (sans clé entre crochets) = attendre **tous** ses exemplaires.

---

## 4. Ce que Terraform crée concrètement

Avec `terraform.tfvars.example` (Agent Gateway non activé) :

| Dans Google Cloud | Nombre |
|---|---|
| API activées dans le projet (visibles dans *API et services → API activées*) | **7** ressources `google_project_service` |
| Service agents Discovery Engine et Model Armor (visibles dans *IAM*, case « Inclure les attributions de rôles fournies par Google ») | créés par **1** ressource `terraform_data` |
| Lecture du projet | 1 `data` (ne crée rien) |

Total : **8 ressources** dans l'état Terraform. Avec `enable_agent_gateway = true` : 13 API, donc 14 ressources.

Les `locals` ne créent rien : ce sont des calculs.

---

## 5. Dépendances avec les autres fichiers

**Ce que ce fichier utilise :**

| Valeur | Vient de |
|---|---|
| `var.project_id`, `var.ge_location`, `var.enable_agent_gateway` | [`variables.tf`](../variables.tf), voir [02-variables.md](02-variables.md) |
| Projet lu par `data.google_project.this` | provider configuré dans [`versions.tf`](../versions.tf), voir [01-versions.md](01-versions.md) |

**Qui utilise ce fichier :**

| Valeur de ce fichier | Utilisée dans |
|---|---|
| `google_project_service.apis` (via `depends_on`) | [`10_identity_access.tf`](../10_identity_access.tf), [`20_data_protection.tf`](../20_data_protection.tf), [`30_ai_guardrails.tf`](../30_ai_guardrails.tf), [`60_advanced.tf`](../60_advanced.tf), [`70_detection.tf`](../70_detection.tf), et `terraform_data.service_agents` ci-dessus |
| `terraform_data.service_agents` (via `depends_on`) | [`20_data_protection.tf`](../20_data_protection.tf) (droits sur la clé et les secrets), [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) (droits DLP de Model Armor, droit de Gemini Enterprise sur Model Armor) |
| `local.project_number` | [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) (adresse du service agent Model Armor), [`50_app.tf`](../50_app.tf) (nom de l'Agent Gateway), [`60_advanced.tf`](../60_advanced.tf) (périmètre VPC-SC) |
| `local.de_host` | [`50_app.tf`](../50_app.tf) (appel `curl` de l'API) |
| `local.kms_location` | [`20_data_protection.tf`](../20_data_protection.tf) (trousseau principal) |
| `local.regional_kms_locations` | [`20_data_protection.tf`](../20_data_protection.tf) (clés régionales) |
| `local.ge_sa` | [`20_data_protection.tf`](../20_data_protection.tf) (clé KMS, secrets), [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) (Model Armor) |

Fiches liées : [05-data-protection.md](05-data-protection.md), [06-ai-guardrails.md](06-ai-guardrails.md),
[08-app.md](08-app.md), [09-advanced.md](09-advanced.md).

---

## 6. Pour reproduire / adapter

Modèle générique « fondations d'un projet » :

```hcl
# Lire le projet courant (pour obtenir son NUMÉRO).
data "google_project" "this" {}

locals {
  project_number = data.google_project.this.number

  # Traduire une localisation d'un service vers celle d'un autre (règle écrite UNE fois).
  kms_location = var.location == "eu" ? "europe" : "us"

  # Adresse IAM d'un service agent : "serviceAccount:service-<NUMÉRO>@gcp-sa-<SERVICE>.iam.gserviceaccount.com"
  mon_sa = "serviceAccount:service-${local.project_number}@gcp-sa-MONSERVICE.iam.gserviceaccount.com"
}

# Activer les API : toujours + optionnelles.
resource "google_project_service" "apis" {
  for_each = toset(concat(
    ["monservice.googleapis.com", "cloudkms.googleapis.com"], # toujours
    var.enable_option ? ["option.googleapis.com"] : [],       # seulement si l'option est activée
  ))
  service            = each.value
  disable_on_destroy = false # ne jamais couper une API partagée avec d'autres
}

# Forcer la création des service agents AVANT de leur donner des droits.
resource "terraform_data" "service_agents" {
  triggers_replace = var.project_id # relancer seulement si le projet change
  provisioner "local-exec" {
    command = <<-EOT
      gcloud beta services identity create --service=monservice.googleapis.com --project=${var.project_id}
    EOT
  }
  depends_on = [google_project_service.apis]
}

# Ailleurs : toute ressource qui donne un droit au service agent
#   depends_on = [terraform_data.service_agents]
```

Étapes :

1. Listez les services utilisés et trouvez leur nom d'API (`gcloud services list --available | grep <mot>`).
2. Pour chaque service qui agira « pour vous » (chiffrer, lire une source…), trouvez l'adresse de son service agent
   dans sa documentation Google (format `service-<n°>@gcp-sa-<service>.iam.gserviceaccount.com`).
3. Mettez les valeurs dérivées dans `locals` (localisations, adresses) au lieu de les répéter.
4. Ajoutez `depends_on = [google_project_service.apis]` aux ressources qui n'ont aucune référence directe aux API, et
   `depends_on = [terraform_data.service_agents]` à celles qui donnent un droit à un service agent.
5. `terraform plan` : vérifiez le nombre d'API (`+ google_project_service.apis["…"]`).

Documentation :
- `https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_service`
- `https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/project`
- `terraform_data` (intégré à Terraform, hors provider Google) :
  `https://developer.hashicorp.com/terraform/language/resources/terraform-data`
- `local-exec` : `https://developer.hashicorp.com/terraform/language/resources/provisioners/local-exec`

---

## 7. Pièges et bonnes pratiques

- **`gcloud` doit être installé et connecté** sur la machine qui lance `apply` (poste ou CI), avec le composant
  `beta`. Sinon `terraform_data.service_agents` échoue.
- **`local-exec` ne s'exécute qu'à la création.** Si quelqu'un supprime un service agent à la main, Terraform ne le
  voit pas. Pour relancer : `terraform apply -replace=terraform_data.service_agents`.
- **Gardez `disable_on_destroy = false`** sur des API partagées. Sinon, un `destroy` peut casser d'autres
  applications du projet.
- **Propagation** : juste après activation d'une API ou création d'un compte, Google peut mettre 1 à 2 minutes à
  tout propager. Une erreur au premier `apply` se règle souvent en relançant `apply`.
- **Ne pas confondre ID et numéro du projet** : l'ID est choisi (`acme-…-prd`), le numéro est attribué par
  Google (`123456789012`). Les service agents utilisent le **numéro**.
- **Ne changez pas `ge_location` en cours de route** : `kms_location`, `regional_kms_locations` et `de_host` en
  dépendent, et changer ces valeurs recrée des clés et l'app.
- **`toset` retire les doublons** : une API listée deux fois ne crée pas d'erreur, mais rangez quand même la liste.
