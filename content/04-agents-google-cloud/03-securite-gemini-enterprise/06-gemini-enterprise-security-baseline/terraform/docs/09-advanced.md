# 09. `60_advanced.tf` : Agent Gateway et VPC Service Controls (options)

> Deux protections avancées, **désactivées par défaut**, qu'on active par une simple variable sans réécrire le
> socle. Bases Terraform : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Il contient deux options de sécurité que tout le monde n'utilise pas dès le premier jour :
- l'**Agent Gateway** : un point de passage contrôlé pour les appels de Gemini Enterprise vers des agents, des outils
  MCP ou des API ;
- un **périmètre VPC Service Controls** : une « frontière » autour des API du projet, déployée en mode **observation**
  (dry-run) pour voir ce qui serait bloqué sans rien bloquer.

Chaque ressource n'existe que si sa variable est renseignée (technique du `count` à 0 ou 1). Avec les valeurs par
défaut, ce fichier ne crée **rien**.

---

## 2. Vue d'ensemble

| Bloc (adresse) | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_network_services_agent_gateway.egress` | `resource` (0 ou 1) | Passerelle de sortie qui gouverne les appels de Gemini Enterprise vers agents / MCP / API. |
| `google_access_context_manager_service_perimeter.ge` | `resource` (0 ou 1) | Périmètre VPC-SC autour du projet, en dry-run. |

---

## 3. Le code expliqué, bloc par bloc

### 3.1 L'Agent Gateway : `google_network_services_agent_gateway.egress`

**Vocabulaire.**
- Un **agent** est un programme IA qui agit (interroge une base, appelle une API…). Un **outil MCP** (Model Context
  Protocol) est un service qu'un agent peut appeler selon un protocole standard.
- **Agent Registry** est le catalogue Google des agents, outils MCP et API autorisés.
- L'**Agent Gateway** est une sorte de **pare-feu applicatif pour agents** : refus par défaut, autorisation par règle
  IAM, politiques par outil, filtrage Model Armor possible, traçabilité de chaque appel (README §11.1).

```hcl
resource "google_network_services_agent_gateway" "egress" {
  count       = var.enable_agent_gateway ? 1 : 0
  name        = "${var.app_id}-egress"
  location    = var.region
  description = "Sortie gouvernée de Gemini Enterprise vers agents / MCP / API."
```

- **`count = var.enable_agent_gateway ? 1 : 0`** : la ressource existe en **1** exemplaire si la variable vaut
  `true`, en **0** (= pas du tout) sinon. C'est la façon standard de rendre une ressource optionnelle
  ([00-bases §8.1](00-bases-terraform.md#81-count--0-ou-n-exemplaires-souvent-pour--optionnel-)). Conséquence :
  ailleurs, on y fait référence avec `[0]` (`google_network_services_agent_gateway.egress[0]`), comme dans
  [`50_app.tf`](../50_app.tf) et [`outputs.tf`](../outputs.tf).
  Avec le `terraform.tfvars.example`, `enable_agent_gateway` n'est pas renseigné : défaut `false`, donc 0.
- `name = "${var.app_id}-egress"` : interpolation. Avec `app_id = "assistant-ia"` → `"assistant-ia-egress"`.
  « egress » = « sortie ».
- `location = var.region` : défaut `"europe-west1"`. Une app en multi-région `eu` utilise une passerelle dans une
  région européenne (commentaire du fichier).
- `description` : texte libre pour les humains.

```hcl
  google_managed {
    governed_access_path = "AGENT_TO_ANYWHERE"
  }
  registries = ["//agentregistry.googleapis.com/projects/${var.project_id}/locations/global"]

  depends_on = [google_project_service.apis]
}
```

- **`google_managed { … }`** : la passerelle est **gérée par Google** (pas de machine à administrer).
  - `governed_access_path = "AGENT_TO_ANYWHERE"` : le sens du trafic gouverné. Ici : **depuis** les agents
    (Gemini Enterprise) **vers** n'importe quelle cible enregistrée. Pour Gemini Enterprise, seule la **sortie**
    a du sens (README §11.1).
- **`registries`** : la liste des registres d'agents dont la passerelle connaît les cibles. Ici, le registre
  `global` du projet. Avec `project_id = "acme-gemini-enterprise-prd"` :
  `"//agentregistry.googleapis.com/projects/acme-gemini-enterprise-prd/locations/global"`. Le `//` initial est
  le format Google des « noms complets de ressource ».
- **`depends_on = [google_project_service.apis]`** : attendre l'activation des API. Dans
  [`00_foundation.tf`](../00_foundation.tf), les API réseau et Agent Registry (`networkservices`,
  `agentregistry`…) ne sont ajoutées à la liste **que si** `enable_agent_gateway = true`.

**Le rattachement à l'app** ne se fait pas ici : il passe par la clé `agentGatewaySetting` de
`local.engine_settings`, envoyée par `curl` dans [`50_app.tf`](../50_app.tf) (voir [08-app.md](08-app.md)).

### 3.2 Le périmètre VPC-SC : `google_access_context_manager_service_perimeter.ge`

**Vocabulaire.**
- **VPC Service Controls (VPC-SC)** : un **périmètre** autour d'API Google. Même avec des identifiants volés, on ne
  peut pas appeler ces API depuis l'extérieur du périmètre, ni copier les données vers un projet hors périmètre.
- **Access Context Manager** : le service, au niveau de l'**organisation** Google Cloud, qui gère ces périmètres.
- **Access policy** (politique d'accès) : le conteneur de tous les périmètres de l'organisation. Elle a un **ID
  numérique**.
- **Dry-run** : mode « à blanc ». Rien n'est bloqué ; les violations sont seulement **journalisées** (journaux
  « VPC SC dry run »).

```hcl
resource "google_access_context_manager_service_perimeter" "ge" {
  count                     = var.vpc_sc_access_policy == "" ? 0 : 1
  parent                    = "accessPolicies/${var.vpc_sc_access_policy}"
  name                      = "accessPolicies/${var.vpc_sc_access_policy}/servicePerimeters/gemini_enterprise_${replace(var.project_id, "-", "_")}"
  title                     = "gemini-enterprise-${var.project_id}"
  perimeter_type            = "PERIMETER_TYPE_REGULAR"
  use_explicit_dry_run_spec = true
```

- **`count = var.vpc_sc_access_policy == "" ? 0 : 1`** : ici la condition est « la variable est-elle vide ? ».
  Vide (défaut) → 0 périmètre. Renseignée (par exemple `"123456789"`) → 1 périmètre. Une variable texte vide sert
  donc d'interrupteur, et sa valeur sert en même temps de paramètre.
- `parent = "accessPolicies/${var.vpc_sc_access_policy}"` : la politique d'accès de l'organisation qui contiendra le
  périmètre. Par exemple `"accessPolicies/123456789"`.
- **`name`** : le nom complet du périmètre. Google impose que la dernière partie ne contienne que des **lettres,
  chiffres et tirets bas** (`_`), pas de tiret (`-`). Or un ID de projet contient des tirets. D'où
  **`replace(texte, "-", "_")`**, qui remplace chaque `-` par `_`
  ([00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)).

  Exemple concret avec `project_id = "acme-gemini-enterprise-prd"` et `vpc_sc_access_policy = "123456789"` :
  - `replace("acme-gemini-enterprise-prd", "-", "_")` → `"acme_gemini_enterprise_prd"` ;
  - `name` → `"accessPolicies/123456789/servicePerimeters/gemini_enterprise_acme_gemini_enterprise_prd"`.
- `title = "gemini-enterprise-${var.project_id}"` : le titre lisible, affiché dans la console. Les tirets y sont
  autorisés → `"gemini-enterprise-acme-gemini-enterprise-prd"`.
- `perimeter_type = "PERIMETER_TYPE_REGULAR"` : un périmètre normal. (L'autre type, « bridge », sert seulement à
  relier deux périmètres.)
- **`use_explicit_dry_run_spec = true`** : la configuration écrite dans le bloc **`spec`** ci-dessous est la
  configuration **dry-run**. La configuration **appliquée** (qui bloque) irait dans un bloc `status`, absent ici :
  donc **rien n'est bloqué**.

```hcl
  spec {
    resources = ["projects/${local.project_number}"]
    restricted_services = [
      "discoveryengine.googleapis.com",
      "modelarmor.googleapis.com",
      "dlp.googleapis.com",
      "cloudkms.googleapis.com",
      "secretmanager.googleapis.com",
    ]
  }
}
```

- **`spec`** : le contenu du périmètre en mode dry-run.
  - `resources` : les projets **à l'intérieur** du périmètre. VPC-SC exige le **numéro** de projet (pas son ID),
    d'où `local.project_number` (lu dans [`00_foundation.tf`](../00_foundation.tf)). Exemple :
    `["projects/123456789012"]`.
  - `restricted_services` : les API protégées par le périmètre. Ce sont exactement les services sensibles du socle :
    Gemini Enterprise (`discoveryengine`), Model Armor, DLP, Cloud KMS (clés) et Secret Manager (secrets).

**Pourquoi le dry-run** (README §11.2) : un périmètre mal réglé peut couper l'accès à l'app. On observe donc 2 à 4
semaines les journaux « VPC SC dry run », on ajuste, puis on passe en mode actif.

**Passer en mode actif (plus tard)** : copier le contenu de `spec` dans un bloc `status` (même syntaxe). Les
détails sont dans la page de la ressource (lien §6). À faire seulement après analyse des journaux et ajout des
règles d'entrée.

---

## 4. Ce que Terraform crée concrètement

Avec le `terraform.tfvars.example` : **rien** (0 ressource). `enable_agent_gateway` vaut `false` et
`vpc_sc_access_policy` vaut `""` par défaut.

Si on active les deux :
- `enable_agent_gateway = true` → **1 passerelle** `assistant-ia-egress` en `europe-west1` + les API réseau activées
  (dans `00_foundation.tf`) + le rattachement à l'app (dans `50_app.tf`) ;
- `vpc_sc_access_policy = "<id>"` → **1 périmètre** en dry-run autour du projet, qui protège 5 API, sans rien
  bloquer.

---

## 5. Dépendances avec les autres fichiers

| Lien | Fichier | Fiche |
|---|---|---|
| Utilise `var.enable_agent_gateway`, `var.region`, `var.app_id`, `var.vpc_sc_access_policy`, `var.project_id` | [`variables.tf`](../variables.tf) | [02-variables.md](02-variables.md) |
| Utilise `google_project_service.apis` et `local.project_number` | [`00_foundation.tf`](../00_foundation.tf) | [03-foundation.md](03-foundation.md) |
| La passerelle est rattachée à l'app par `local.engine_settings` | [`50_app.tf`](../50_app.tf) | [08-app.md](08-app.md) |
| L'ID de la passerelle est affiché par l'output `agent_gateway` | [`outputs.tf`](../outputs.tf) | [11-outputs.md](11-outputs.md) |

---

## 6. Pour reproduire / adapter

**Besoin type : ajouter une ressource optionnelle, activable par une variable.**

```hcl
# variables.tf : l'interrupteur
variable "enable_mon_option" {
  description = "Active mon option (désactivée par défaut)."
  type        = bool
  default     = false
}

# 60_advanced.tf : la ressource, présente 0 ou 1 fois
resource "google_xxx" "mon_option" {
  count = var.enable_mon_option ? 1 : 0          # ou : var.mon_id == "" ? 0 : 1
  name  = "${var.app_id}-mon-option"
  # ...
  depends_on = [google_project_service.apis]     # si une API doit être activée avant
}

# Partout ailleurs : toujours avec [0], et toujours sous la même condition
# valeur = var.enable_mon_option ? google_xxx.mon_option[0].id : null
```

Variante : un **périmètre VPC-SC en dry-run** pour un autre projet.

```hcl
resource "google_access_context_manager_service_perimeter" "autre" {
  parent                    = "accessPolicies/${var.vpc_sc_access_policy}"
  name                      = "accessPolicies/${var.vpc_sc_access_policy}/servicePerimeters/${replace(var.autre_projet, "-", "_")}" # pas de "-"
  title                     = "perimetre-${var.autre_projet}"
  perimeter_type            = "PERIMETER_TYPE_REGULAR"
  use_explicit_dry_run_spec = true      # observer d'abord
  spec {
    resources           = ["projects/${var.autre_projet_numero}"]   # NUMÉRO de projet
    restricted_services = ["storage.googleapis.com"]                # API à protéger
  }
}
```

1. Lire la doc de la ressource :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/network_services_agent_gateway
   et https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/access_context_manager_service_perimeter
2. Créer la variable interrupteur avec un défaut « désactivé ».
3. Ajouter `count = condition ? 1 : 0` et des références en `[0]` partout, protégées par la même condition.
4. Activer les API nécessaires seulement si l'option est active (comme dans `00_foundation.tf`).
5. `terraform plan` avec l'option à `false` (rien ne doit changer), puis à `true`.

---

## 7. Pièges et bonnes pratiques

- **Agent Gateway sans agent personnalisé = inutile.** S'il n'y a ni agent maison ni outil MCP, il n'y a rien à
  gouverner. Elle devient indispensable dès qu'on ajoute un agent (par exemple Databricks, README §7.4) ou un serveur
  MCP : ce sont justement les flux que le Model Armor de l'assistant **ne filtre pas**.
- **Après activation de la passerelle**, il faut encore importer dans Agent Registry les agents, MCP et API
  autorisés (refus par défaut), et attendre jusqu'à 15 minutes que les politiques s'appliquent.
- **VPC-SC bloque l'interface web** en mode actif tant qu'on n'a pas créé de **règles d'entrée** (*access levels* :
  plages IP de l'entreprise, appareils gérés…). Ne jamais passer en actif sans elles.
- **VPC-SC doit précéder les connecteurs** : appliquer un périmètre sur un projet qui a déjà des data stores n'est
  pas supporté (README §11.2). En production, déployez le périmètre **avant** de créer les connecteurs.
- **Droits au niveau organisation** : créer un périmètre exige des droits Access Context Manager sur l'organisation
  (pas seulement sur le projet). Sans eux, `apply` échoue avec une erreur 403.
- **API Access Context Manager** : comme le provider utilise `user_project_override = true`
  ([`versions.tf`](../versions.tf)), les appels VPC-SC sont facturés au projet, qui doit donc avoir l'API
  `accesscontextmanager.googleapis.com` activée. C'est fait automatiquement dans
  [`00_foundation.tf`](../00_foundation.tf) dès que `vpc_sc_access_policy` est renseigné.
- **Le nom du périmètre est figé** : changer `project_id` change `name`, donc recrée le périmètre.
- Activez ces options **en recette d'abord**, puis en production, comme tout changement de sécurité.
