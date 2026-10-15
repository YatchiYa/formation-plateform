# 02. `variables.tf` : toutes les entrées du socle

> Ce fichier déclare les **paramètres** du socle (projet, groupes, connecteurs, filtres…) ; leurs valeurs se donnent
> dans `terraform.tfvars`. Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Il sépare **le code** (les autres fichiers `.tf`, identiques partout) de **la configuration** (ce qui change d'un
client ou d'un environnement à l'autre : projet, groupes, sources de données). Chaque `variable` est une « case à
remplir » avec un type, une valeur par défaut éventuelle et parfois une règle de validation. Les valeurs par défaut
sont **les choix de sécurité du socle** (UE, CMEK activé, conversations gardées 30 jours, recherche web désactivée,
contenu non journalisé…) : sans rien changer, on obtient la configuration sûre. Ce fichier ne crée rien dans Google
Cloud.

---

## 2. Vue d'ensemble

Le fichier est découpé en 7 sections (ses propres titres). Toutes les entrées sont des blocs `variable`.

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| **1. Projet et localisation** | | |
| `var.project_id` | variable | Projet GCP cible (**obligatoire**). |
| `var.region` | variable | Région par défaut des ressources régionales. |
| `var.ge_location` | variable | Multi-région de l'app (`eu` / `us`), validée, **immuable**. |
| `var.app_id` | variable | Identifiant technique de l'app. |
| `var.app_display_name` | variable | Nom affiché de l'app. |
| `var.company_name` | variable | Nom de l'entreprise transmis à l'app. |
| **2. Identité et accès** | | |
| `var.identity_provider` | variable | Annuaire utilisé pour la connexion (`GSUITE` / `THIRD_PARTY`). |
| `var.workforce_pool` | variable | Pool Workforce Identity Federation si `THIRD_PARTY`. |
| `var.user_groups` | variable | Groupes utilisateurs (**obligatoire**). |
| `var.admin_groups` | variable | Groupes administrateurs (**obligatoire**). |
| `var.security_groups` | variable | Groupes de l'équipe sécurité (**obligatoire**). |
| `var.viewer_groups` | variable | Groupes en lecture seule (optionnel). |
| **3. Protection des données** | | |
| `var.enable_cmek` | variable | Active le chiffrement avec les clés du client. |
| `var.kms_key_ring` | variable | Nom du trousseau de clés KMS. |
| `var.session_ttl_days` | variable | Durée de conservation des conversations. |
| **4. Connecteurs** | | |
| `var.connectors` | variable | Liste des sources de données (type complexe). |
| `var.extra_data_store_ids` | variable | Data stores créés hors Terraform à rattacher. |
| **5. Filtrage IA (Model Armor)** | | |
| `var.armor_confidence` | variable | Seuil de sensibilité des filtres. |
| `var.sdp_mode` | variable | Détection de données sensibles FR (`advanced`) ou Google (`basic`). |
| `var.dlp_location` | variable | Localisation du template DLP. |
| `var.sensitive_info_types` | variable | Types de données sensibles bloqués. |
| `var.log_screened_content` | variable | Journaliser ou non le contenu filtré. |
| `var.banned_phrases` | variable | Expressions interdites dans les réponses. |
| **6. Exposition et fonctionnalités** | | |
| `var.web_grounding` | variable | Recherche web autorisée ou non. |
| `var.features` | variable | Interrupteurs de fonctionnalités de l'app. |
| `var.enable_observability` | variable | Traces techniques sans contenu. |
| **7. Options avancées** | | |
| `var.enable_agent_gateway` | variable | Active Agent Gateway. |
| `var.vpc_sc_access_policy` | variable | Active un périmètre VPC Service Controls. |
| `var.alert_email` | variable | Adresse des alertes sécurité. |

---

## 3. Le code expliqué, bloc par bloc

### 3.0 Anatomie d'un bloc `variable`

Rappel détaillé : [00-bases §6.3](00-bases-terraform.md#63-variable--les-entrées). En bref :

| Élément | Rôle | Si absent |
|---|---|---|
| `variable "nom"` | Déclare l'entrée. On la lit ailleurs avec `var.nom`. | — |
| `description` | Texte d'aide (affiché par `terraform plan` quand la valeur manque). | Pas d'aide : à éviter. |
| `type` | Type attendu (`string`, `number`, `bool`, `list(string)`, `map(string)`, `map(object({…}))`). Terraform refuse une valeur du mauvais type. | Tout type accepté : à éviter. |
| `default` | Valeur utilisée si `terraform.tfvars` ne la donne pas. | Variable **obligatoire** : `plan` s'arrête et la demande. |
| `validation { condition, error_message }` | Règle métier : si `condition` est fausse, Terraform refuse avec `error_message`. | Aucune vérification. |

Où donner les valeurs : `terraform.tfvars` (copié depuis `terraform.tfvars.example`). Les lignes `# ====` du fichier
sont de simples commentaires qui servent de titres.

---

### 3.1 Section 1 : Projet et localisation

```hcl
# =============================================================================
# 1. Projet et localisation
# =============================================================================
variable "project_id" {
  description = "Projet GCP (dans l'organisation Google Workspace du client)."
  type        = string
}

variable "region" {
  description = "Région par défaut des ressources régionales (Agent Gateway...)."
  type        = string
  default     = "europe-west1"
}
```

- **`project_id`** : chaîne (`string`), **sans `default`**, donc **obligatoire**. C'est l'ID du projet (ex.
  `"acme-gemini-enterprise-prd"`), pas son numéro.
  - Pourquoi « dans l'organisation » : les connecteurs Google Workspace exigent un projet rattaché à l'organisation
    de l'entreprise.
  - Utilisée dans : [`versions.tf`](../versions.tf), [`00_foundation.tf`](../00_foundation.tf),
    [`10_identity_access.tf`](../10_identity_access.tf), [`30_ai_guardrails.tf`](../30_ai_guardrails.tf),
    [`50_app.tf`](../50_app.tf), [`60_advanced.tf`](../60_advanced.tf), [`70_detection.tf`](../70_detection.tf),
    [`outputs.tf`](../outputs.tf).
- **`region`** : défaut `"europe-west1"` (Belgique, UE). Une **région** est un lieu physique précis (un groupe de
  centres de données).
  - Utilisée dans : [`versions.tf`](../versions.tf) (région par défaut du provider), [`50_app.tf`](../50_app.tf) et
    [`60_advanced.tf`](../60_advanced.tf) (Agent Gateway).

```hcl
variable "ge_location" {
  description = "Multi-région de l'app Gemini Enterprise. 'eu' pour un client français : résidence UE, et CMEK impossible en 'global'. IMMUABLE."
  type        = string
  default     = "eu"
  validation {
    condition     = contains(["eu", "us"], var.ge_location)
    error_message = "Utilisez 'eu' ou 'us' : CMEK et Access Transparency ne sont pas supportés en 'global'."
  }
}
```

- **`ge_location`** : où vit l'app Gemini Enterprise. `eu` est une **multi-région** (plusieurs régions de l'UE
  regroupées), contrairement à `region` qui désigne un seul lieu.
- `validation` : première apparition dans ce fichier.
  - `condition = contains(["eu", "us"], var.ge_location)` : la fonction `contains(liste, x)` renvoie `true` si `x`
    est dans la liste (voir [00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)). Avec la valeur
    par défaut : `contains(["eu","us"], "eu")` → `true`, donc accepté. Avec `"global"` → `false`, donc
    `terraform plan` s'arrête et affiche `error_message`.
  - Pourquoi : Google n'autorise **pas CMEK** (et pas Access Transparency) pour une app `global`. La validation
    empêche une erreur qui ne se verrait qu'au déploiement. Voir le
    [README §6.1](../../README.md#61-cmek--chiffrement-avec-les-clés-de-acme).
- **IMMUABLE** : changer cette valeur après le premier `apply` recrée l'app et ses connecteurs (perte de
  l'historique). Choisir une fois pour toutes.
- Utilisée dans : [`00_foundation.tf`](../00_foundation.tf) (calcul de `kms_location`, `de_host`…),
  [`10_identity_access.tf`](../10_identity_access.tf), [`20_data_protection.tf`](../20_data_protection.tf),
  [`30_ai_guardrails.tf`](../30_ai_guardrails.tf), [`40_connectors.tf`](../40_connectors.tf),
  [`50_app.tf`](../50_app.tf), [`outputs.tf`](../outputs.tf).

```hcl
variable "app_id" {
  type    = string
  default = "assistant-ia"
}

variable "app_display_name" {
  type    = string
  default = "Assistant IA"
}

variable "company_name" {
  type    = string
  default = "Acme"
}
```

Ces trois variables n'ont **pas de `description`** (elles sont simples, mais c'est une bonne pratique d'en mettre).

- **`app_id`** : identifiant technique de l'app (`engine_id`), utilisé aussi pour nommer d'autres objets (labels
  Model Armor, nom de l'Agent Gateway `"${var.app_id}-egress"`, URL de console en sortie). Utilisée dans :
  [`30_ai_guardrails.tf`](../30_ai_guardrails.tf), [`50_app.tf`](../50_app.tf),
  [`60_advanced.tf`](../60_advanced.tf), [`outputs.tf`](../outputs.tf). Changer cet ID recrée l'app.
- **`app_display_name`** : nom lisible de l'app ; l'assistant s'appelle `"${var.app_display_name} - assistant"`.
  Utilisée dans : [`50_app.tf`](../50_app.tf).
- **`company_name`** : nom de l'entreprise transmis à l'app (`company_name` dans `50_app.tf`). Utilisée dans :
  [`50_app.tf`](../50_app.tf).

---

### 3.2 Section 2 : Identité et accès (groupes uniquement)

```hcl
# =============================================================================
# 2. Identité et accès (groupes uniquement)
# =============================================================================
variable "identity_provider" {
  description = "GSUITE (Google Workspace / Cloud Identity) ou THIRD_PARTY (Entra ID via Workforce Identity Federation)."
  type        = string
  default     = "GSUITE"
  validation {
    condition     = contains(["GSUITE", "THIRD_PARTY"], var.identity_provider)
    error_message = "identity_provider doit valoir GSUITE ou THIRD_PARTY."
  }
}

variable "workforce_pool" {
  description = "Si THIRD_PARTY : 'locations/global/workforcePools/POOL_ID'."
  type        = string
  default     = ""
}
```

- **`identity_provider`** : quel annuaire authentifie les collaborateurs. `GSUITE` = comptes Google Workspace /
  Cloud Identity ; `THIRD_PARTY` = annuaire externe (ex. Microsoft Entra ID) via *Workforce Identity Federation*
  (mécanisme Google qui fait confiance à un annuaire externe). Choix structurant : voir
  [README §5.1](../../README.md#51-connexion-avec-le-compte-dentreprise-sso). Utilisée dans :
  [`10_identity_access.tf`](../10_identity_access.tf).
- **`workforce_pool`** : chemin du pool de fédération. Défaut `""` (chaîne vide) = « non utilisé ». À remplir
  seulement si `THIRD_PARTY`. Utilisée dans : [`10_identity_access.tf`](../10_identity_access.tf).

```hcl
variable "user_groups" {
  description = "Groupes autorisés à utiliser l'app (rôle agentspaceUser)."
  type        = list(string)
}

variable "admin_groups" {
  description = "Administrateurs Gemini Enterprise (rôle agentspaceAdmin). Petit groupe."
  type        = list(string)
}

variable "security_groups" {
  description = "Équipe sécurité : SEULE à gérer Model Armor, les clés KMS et à lire les journaux privés."
  type        = list(string)
}

variable "viewer_groups" {
  description = "Lecture seule + analytics (pilotage, DPO). Optionnel."
  type        = list(string)
  default     = []
}
```

- `type = list(string)` : une **liste de chaînes**. Chaque chaîne est un « membre IAM » avec son préfixe, par
  exemple `"group:gemini-utilisateurs@acme.example"`. IAM (*Identity and Access Management*) est le système de
  droits de Google Cloud ; un **rôle** est un paquet de permissions.
- **`user_groups`**, **`admin_groups`**, **`security_groups`** : **obligatoires** (pas de `default`). On force ainsi
  la personne qui déploie à décider explicitement qui utilise, qui administre, et qui garde les clés de la sécurité.
- **`viewer_groups`** : optionnel, défaut `[]` (liste vide = aucun groupe lecteur).
- Pourquoi des **groupes** et pas des personnes : arrivées et départs gérés dans l'annuaire, revue d'accès simple.
  Pourquoi un groupe **sécurité séparé** : les admins de l'app ne doivent pas pouvoir désactiver leur propre
  sécurité. Voir [README §5.2](../../README.md#52-rôles-attribués-à-des-groupes) et
  [04-identity-access.md](04-identity-access.md).
- Utilisées dans : [`10_identity_access.tf`](../10_identity_access.tf) (les 4).
- Exemple (`terraform.tfvars.example`) : `user_groups = ["group:gemini-utilisateurs@acme.example"]`.

---

### 3.3 Section 3 : Protection des données

```hcl
# =============================================================================
# 3. Protection des données
# =============================================================================
variable "enable_cmek" {
  description = "Chiffrement avec les clés du client (Cloud KMS). Doit être activé AVANT la création de l'app."
  type        = bool
  default     = true
}

variable "kms_key_ring" {
  type    = string
  default = "gemini-enterprise"
}

variable "session_ttl_days" {
  description = "Durée de conservation des conversations (défaut Google : 60 jours). Minimisation RGPD."
  type        = number
  default     = 30
}
```

- **`enable_cmek`** : `bool` (vrai/faux), défaut `true`. CMEK = les données stockées sont chiffrées avec **une clé du
  client** dans Cloud KMS (le coffre de clés de Google Cloud). « AVANT la création de l'app » : une app créée sans
  CMEK reste chiffrée par Google ; l'activer après coup ne la rechiffre pas. Utilisée dans :
  [`20_data_protection.tf`](../20_data_protection.tf) (sert de `count`/`for_each` pour créer ou non les clés),
  [`40_connectors.tf`](../40_connectors.tf), [`50_app.tf`](../50_app.tf), [`outputs.tf`](../outputs.tf).
- **`kms_key_ring`** : nom du **trousseau** (*key ring*, le dossier qui contient les clés). Pas de description.
  Utilisée dans : [`20_data_protection.tf`](../20_data_protection.tf).
- **`session_ttl_days`** : `number`, défaut `30` (Google : 60). Minimisation RGPD, durée à valider avec le DPO.
  Utilisée dans : [`50_app.tf`](../50_app.tf) (appel d'API `sessionConfig`). Voir
  [README §6.3](../../README.md#63-minimisation--conservation-des-conversations).

---

### 3.4 Section 4 : Connecteurs (générique : une entrée = une source)

```hcl
# =============================================================================
# 4. Connecteurs (générique : une entrée = une source)
# =============================================================================
variable "connectors" {
  description = "Sources de données. Voir terraform.tfvars.example et le guide (section Connecteurs)."
  type = map(object({
    data_source      = string # google_drive, sharepoint, github, jira, bigquery...
    display_name     = string
    modes            = optional(list(string), ["FEDERATED"]) # FEDERATED = pas de copie, droits de la source
    params           = optional(map(string), {})             # paramètres non secrets
    secret_params    = optional(map(string), {})             # clé du paramètre => ID du secret Secret Manager
    entities         = optional(list(object({ name = string, params = optional(string) })), [])
    refresh_interval = optional(string, "86400s")
    static_ip        = optional(bool, false) # IP sortantes fixes à autoriser côté SaaS (IMMUABLE)
  }))
  default = {}
}
```

C'est la variable la plus complexe du projet. Lisons le type **de l'extérieur vers l'intérieur** :

1. `map( … )` : une **map**, c'est-à-dire un dictionnaire `clé = valeur`. La **clé** est un nom court que vous
   choisissez (`gdrive`, `sharepoint`…). Elle devient l'ID de collection du connecteur (`collection_id = each.key`
   dans `40_connectors.tf`), donc elle doit être **stable**.
2. `object({ … })` : chaque **valeur** est un **objet**, c'est-à-dire un ensemble de champs nommés, chacun avec son
   type.
3. Les champs :

| Champ | Type | Obligatoire ? | Défaut | Signification |
|---|---|---|---|---|
| `data_source` | `string` | **oui** | — | Type de source Google : `google_drive`, `sharepoint`, `github`, `jira`, `bigquery`… |
| `display_name` | `string` | **oui** | — | Nom affiché dans la console. |
| `modes` | `list(string)` | non | `["FEDERATED"]` | Mode du connecteur. `FEDERATED` = interrogation en direct, **sans copie**, avec les droits de la source. `DATA_INGESTION` = copie indexée chez Google. |
| `params` | `map(string)` | non | `{}` | Paramètres **non secrets** (URL d'instance, ID de tenant…). |
| `secret_params` | `map(string)` | non | `{}` | `nom du paramètre => NOM du secret` dans Secret Manager. **Jamais la valeur du secret.** |
| `entities` | `list(object({ name = string, params = optional(string) }))` | non | `[]` | Les types d'objets à connecter (ex. `file`, `issue`). Chaque entité a un `name` obligatoire et des `params` optionnels (texte). |
| `refresh_interval` | `string` | non | `"86400s"` | Fréquence de synchronisation (86 400 s = 24 h). |
| `static_ip` | `bool` | non | `false` | Le connecteur appelle la source depuis des **IP fixes**, à autoriser côté SaaS. **Immuable.** |

4. `optional(TYPE, DÉFAUT)` : le champ peut être **omis** ; Terraform le remplit alors avec `DÉFAUT`. Sans second
   argument (comme `params = optional(string)` dans `entities`), le champ omis vaut `null` (« pas de valeur »).
5. `default = {}` : sans connecteur déclaré, la map est vide et aucun connecteur n'est créé.

**Exemple : ce que vous écrivez** (extrait de `terraform.tfvars.example`) :

```hcl
connectors = {
  gdrive = {
    data_source  = "google_drive"
    display_name = "Google Drive"
  }
  sharepoint = {
    data_source  = "sharepoint" # [à confirmer] la doc montre aussi "sharepoint_federated_search"
    display_name = "SharePoint"
    params = {
      instance_uri = "https://acme.sharepoint.com"
      tenant_id    = "00000000-0000-0000-0000-000000000000"
    }
    secret_params = {
      client_id     = "sharepoint-client-id"
      client_secret = "sharepoint-client-secret"
    }
    entities  = [{ name = "file" }]
    static_ip = true
  }
}
```

**Ce que Terraform en fait** (les champs omis sont complétés) :

```hcl
{
  gdrive = {
    data_source      = "google_drive"
    display_name     = "Google Drive"
    modes            = ["FEDERATED"]   # défaut
    params           = {}              # défaut
    secret_params    = {}              # défaut
    entities         = []              # défaut
    refresh_interval = "86400s"        # défaut
    static_ip        = false           # défaut
  }
  sharepoint = {
    data_source      = "sharepoint"
    display_name     = "SharePoint"
    modes            = ["FEDERATED"]   # défaut
    params           = { instance_uri = "https://acme.sharepoint.com", tenant_id = "0000…" }
    secret_params    = { client_id = "sharepoint-client-id", client_secret = "sharepoint-client-secret" }
    entities         = [{ name = "file", params = null }]   # params omis => null
    refresh_interval = "86400s"        # défaut
    static_ip        = true
  }
}
```

Pourquoi ce choix de conception :
- **Un seul modèle pour toutes les sources** : ajouter une source = ajouter une entrée, sans toucher au code
  ([README §7.1](../../README.md#71-le-principe--un-modèle-générique)).
- **`FEDERATED` par défaut** : la décision de sécurité la plus importante, rien n'est copié et les droits de la
  source s'appliquent ([README §7.2](../../README.md#72-fédéré-ou-ingestion--la-décision-de-sécurité-la-plus-importante)).
- **Secrets séparés des paramètres** : `secret_params` ne contient que des **noms** ; le code les transforme en
  références Secret Manager (`…/versions/latest`).

Utilisée dans :
- [`40_connectors.tf`](../40_connectors.tf) : `for_each = var.connectors`, un connecteur par entrée (tous les champs) ;
- [`20_data_protection.tf`](../20_data_protection.tf) : lit `secret_params` de tous les connecteurs pour retrouver
  les secrets et donner le droit de lecture à Gemini Enterprise ;
- [`outputs.tf`](../outputs.tf) : `static_ip` pour afficher les IP à autoriser.

```hcl
variable "extra_data_store_ids" {
  description = "Data stores créés hors Terraform (console) à rattacher à l'app."
  type        = list(string)
  default     = []
}
```

- **`extra_data_store_ids`** : liste d'IDs de *data stores* (les « bases » qu'un connecteur crée et que l'app
  interroge) créés à la main dans la console. Ils sont ajoutés à ceux des connecteurs Terraform. Utilisée dans :
  [`50_app.tf`](../50_app.tf) (`data_store_ids = concat(local.connector_data_store_ids, var.extra_data_store_ids)`).

---

### 3.5 Section 5 : Filtrage IA (Model Armor)

Model Armor est un « pare-feu » pour le texte : il analyse chaque question et chaque réponse. Voir
[README §8](../../README.md#8-couche-4--filtrage-ia-avec-model-armor).

```hcl
# =============================================================================
# 5. Filtrage IA (Model Armor)
# =============================================================================
variable "armor_confidence" {
  description = "Seuil des filtres injection/jailbreak et contenus : LOW_AND_ABOVE (strict), MEDIUM_AND_ABOVE (équilibré), HIGH."
  type        = string
  default     = "MEDIUM_AND_ABOVE"
  validation {
    condition     = contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH"], var.armor_confidence)
    error_message = "armor_confidence doit valoir LOW_AND_ABOVE, MEDIUM_AND_ABOVE ou HIGH."
  }
}

variable "sdp_mode" {
  description = "advanced = détecteurs FR/UE (NIR, CNI, IBAN...) via un template DLP ; basic = détecteurs Google par défaut (orientés US)."
  type        = string
  default     = "advanced"
  validation {
    # Une faute de frappe désactiverait silencieusement la détection des données sensibles.
    condition     = contains(["advanced", "basic"], var.sdp_mode)
    error_message = "sdp_mode doit valoir advanced ou basic."
  }
}

variable "dlp_location" {
  description = "Localisation du template DLP (à valider en recette avec un template Model Armor 'eu')."
  type        = string
  default     = "europe"
}
```

- **`armor_confidence`** : seuil de blocage. `MEDIUM_AND_ABOVE` = équilibre : bloque les attaques sans gêner les
  questions normales. Trop strict, l'outil pousse vers des IA grand public non maîtrisées. Utilisée dans :
  [`30_ai_guardrails.tf`](../30_ai_guardrails.tf).
- **`sdp_mode`** : `advanced` utilise un template DLP (*Data Loss Prevention*, le service Google de détection de
  données sensibles) avec les détecteurs français ; `basic` utilise les détecteurs Google par défaut, orientés
  États-Unis (ni NIR ni IBAN). Utilisée dans : [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) (crée ou non le
  template DLP).
- **`dlp_location`** : où créer le template DLP. Point **à valider en recette** (README §16). Utilisée dans :
  [`30_ai_guardrails.tf`](../30_ai_guardrails.tf).

```hcl
variable "sensitive_info_types" {
  description = "Types de données bloqués dans les prompts et réponses (mode advanced)."
  type        = list(string)
  default = [
    "FRANCE_NIR", "FRANCE_CNI", "FRANCE_PASSPORT", "FRANCE_TAX_IDENTIFICATION_NUMBER",
    "IBAN_CODE", "CREDIT_CARD_NUMBER",
    "GCP_CREDENTIALS", "GCP_API_KEY", "AUTH_TOKEN", "AWS_CREDENTIALS", "ENCRYPTION_KEY",
  ]
}
```

- **`sensitive_info_types`** : liste de 11 « infoTypes » DLP (noms de détecteurs Google). Une liste peut s'écrire
  sur plusieurs lignes ; la virgule finale est permise.
  - Identité française (NIR = n° de sécurité sociale, CNI, passeport, n° fiscal), bancaire (IBAN, carte) et secrets
    techniques (identifiants GCP/AWS, jetons, clés).
  - Volontairement absents : e-mails, téléphones, noms (omniprésents dans le travail normal). Voir
    [README §8.3](../../README.md#83-les-données-sensibles-détectées-france--ue).
  - Utilisée dans : [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) (un bloc `info_types` par élément, seulement
    en mode `advanced`).

```hcl
variable "log_screened_content" {
  description = "Journaliser le CONTENU filtré par Model Armor. Google le déconseille pour Gemini Enterprise (prompts lisibles dans les logs)."
  type        = bool
  default     = false
}

variable "banned_phrases" {
  description = "Expressions que l'assistant ne doit jamais produire (noms de code de projets confidentiels...)."
  type        = list(string)
  default     = []
}
```

- **`log_screened_content`** : défaut `false` : on trace **qui modifie** les filtres, pas **ce que** les
  collaborateurs écrivent (vie privée). À `true`, les questions apparaissent dans les journaux et une alerte « pic de
  blocages » devient possible. Utilisée dans : [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) et
  [`70_detection.tf`](../70_detection.tf) (crée ou non la métrique et l'alerte). Voir
  [README §8.4](../../README.md#84-métadonnées-du-template--comportement-et-journalisation).
- **`banned_phrases`** : défaut vide. Ex. un nom de code de projet confidentiel. Utilisée dans :
  [`50_app.tf`](../50_app.tf) (un bloc dynamique par expression).

---

### 3.6 Section 6 : Exposition et fonctionnalités

```hcl
# =============================================================================
# 6. Exposition et fonctionnalités
# =============================================================================
variable "web_grounding" {
  description = "WEB_GROUNDING_TYPE_DISABLED (défaut) | WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH. Google Search grounding est incompatible avec résidence des données et CMEK."
  type        = string
  default     = "WEB_GROUNDING_TYPE_DISABLED"
  validation {
    condition     = contains(["WEB_GROUNDING_TYPE_DISABLED", "WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH", "WEB_GROUNDING_TYPE_GOOGLE_SEARCH"], var.web_grounding)
    error_message = "Valeur de web_grounding inconnue."
  }
}
```

- **`web_grounding`** : l'assistant peut-il chercher sur le web ? Défaut : **non**. Sinon, des fragments de questions
  partiraient vers un moteur public ; et la recherche Google standard est incompatible avec la résidence UE et CMEK.
  Utilisée dans : [`50_app.tf`](../50_app.tf). Voir
  [README §9.2](../../README.md#92-pas-de-recherche-web-publique).

```hcl
variable "features" {
  description = "Fonctionnalités de l'app (clés de l'API Engine.features)."
  type        = map(string)
  default = {
    "disable-agent-sharing"                = "FEATURE_STATE_ON"  # pas de partage d'agents maison tant que la gouvernance n'est pas définie
    "skill-sharing-without-admin-approval" = "FEATURE_STATE_OFF" # partage de skills = validation admin
    "session-sharing"                      = "FEATURE_STATE_OFF" # une conversation (souvent confidentielle) ne se partage pas
    "feedback"                             = "FEATURE_STATE_ON"  # retours utilisateurs pour le pilotage
  }
}
```

- **`features`** : `map(string)`, c'est-à-dire un dictionnaire `"nom-de-fonctionnalité" = "état"`. Les clés
  contiennent des tirets, d'où les guillemets autour.
  - Attention à la lecture : `"disable-agent-sharing" = "FEATURE_STATE_ON"` signifie « la **désactivation** du
    partage d'agents est **active** », donc le partage est coupé.
  - **Si vous donnez `features` dans `terraform.tfvars`, la map entière remplace le défaut** (pas de fusion) :
    recopiez les 4 clés.
  - Utilisée dans : [`50_app.tf`](../50_app.tf). Voir
    [README §9.3](../../README.md#93-fonctionnalités-et-partages).

```hcl
variable "enable_observability" {
  description = "Traces OpenTelemetry de l'app (SANS le contenu des prompts)."
  type        = bool
  default     = true
}
```

- **`enable_observability`** : traces techniques (performances, erreurs) au format OpenTelemetry (standard ouvert de
  traces). Le contenu reste exclu (`sensitiveLoggingEnabled = false` est écrit en dur dans `50_app.tf`). Utilisée
  dans : [`50_app.tf`](../50_app.tf).

---

### 3.7 Section 7 : Options avancées (désactivées par défaut)

```hcl
# =============================================================================
# 7. Options avancées (désactivées par défaut)
# =============================================================================
variable "enable_agent_gateway" {
  description = "Agent Gateway en sortie (AGENT_TO_ANYWHERE). Utile dès qu'il y a des agents personnalisés / outils MCP."
  type        = bool
  default     = false
}

variable "vpc_sc_access_policy" {
  description = "ID numérique de la politique Access Context Manager de l'organisation. Vide = pas de périmètre VPC-SC."
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Boîte de l'équipe sécurité pour les alertes."
  type        = string
  default     = ""
}
```

- **`enable_agent_gateway`** : `false` par défaut. Agent Gateway est le point de passage contrôlé des appels des
  agents vers des outils/API. Sans agent personnalisé ni outil MCP, rien à gouverner. Utilisée dans :
  [`00_foundation.tf`](../00_foundation.tf) (active 6 API en plus), [`50_app.tf`](../50_app.tf),
  [`60_advanced.tf`](../60_advanced.tf), [`outputs.tf`](../outputs.tf).
- **`vpc_sc_access_policy`** : chaîne vide = **option désactivée**. Le code teste
  `var.vpc_sc_access_policy == "" ? 0 : 1`. VPC Service Controls crée un périmètre autour des API du projet contre
  l'exfiltration. Utilisée dans : [`60_advanced.tf`](../60_advanced.tf).
- **`alert_email`** : même convention : vide = pas de canal e-mail d'alerte. Utilisée dans :
  [`70_detection.tf`](../70_detection.tf). Fourni dans l'exemple (`"securite-ia@acme.example"`).

> **Convention du fichier :** une chaîne vide `""` ou une liste vide `[]` veut dire « fonctionnalité non utilisée ».
> Le code la transforme en `count = 0` (voir [00-bases §8.1](00-bases-terraform.md#81-count--0-ou-n-exemplaires-souvent-pour--optionnel-)).

---

### 3.8 Section 8 : Journalisation (usage et sécurité)

```hcl
variable "log_prompts_responses" {
  description = "Journaliser le TEXTE complet des questions et réponses (gen_ai.user.message / gen_ai.choice). Données personnelles : décision DPO/CSE."
  type        = bool
  default     = false
}
```

- **Rôle :** active la journalisation du **texte exact** des questions et réponses. `false` par défaut : ce sont des
  données personnelles de salariés. À activer seulement sur décision du DPO (et du CSE si besoin).
- **Utilisée par :** [`50_app.tf`](../50_app.tf) (`sensitiveLoggingEnabled`), voir [08-app.md](08-app.md).

```hcl
variable "security_log_retention_days" {
  description = "Conservation des journaux de sécurité (audit, Model Armor) dans le bucket dédié."
  type        = number
  default     = 365
}

variable "usage_log_retention_days" {
  description = "Conservation des journaux d'usage (activité des utilisateurs, peut contenir des questions). Minimisation RGPD."
  type        = number
  default     = 90
}
```

- **Rôle :** durée de conservation **par finalité** : 1 an pour la preuve d'audit, 90 jours pour l'usage.
- **Utilisées par :** [`80_logging.tf`](../80_logging.tf) (`retention_days` des deux buckets).

```hcl
variable "lock_security_logs" {
  description = "Verrouiller le bucket de sécurité (personne ne peut réduire la rétention ni le supprimer). IRRÉVERSIBLE."
  type        = bool
  default     = false
}
```

- **Rôle :** rend le bucket de sécurité **inaltérable** (intégrité des preuves). **Irréversible** : à activer en
  production une fois la durée validée.
- **Utilisée par :** [`80_logging.tf`](../80_logging.tf) (`locked`).

```hcl
variable "link_logs_to_bigquery" {
  description = "Exposer les buckets de logs dans BigQuery (dataset lié, lecture seule, sans copie) pour des tableaux de bord."
  type        = bool
  default     = false
}
```

- **Rôle :** crée un dataset BigQuery **lié** au bucket d'usage (lecture seule, sans copie) pour Looker Studio.
- **Utilisée par :** [`80_logging.tf`](../80_logging.tf) (`google_logging_linked_dataset`, avec `count`).

Fiche détaillée : [13-logging.md](13-logging.md).

## 4. Ce que Terraform crée concrètement

**Rien.** Les variables ne sont que des entrées. Avec `terraform.tfvars.example` copié en `terraform.tfvars` :

- 4 valeurs obligatoires fournies : `project_id`, `user_groups`, `admin_groups`, `security_groups` ;
- 2 valeurs optionnelles fournies : `viewer_groups`, `alert_email` ;
- `connectors` : 5 entrées actives (`gdrive`, `gcalendar`, `sharepoint`, `teams`, `github`) ; `gmail` et `jira`
  sont commentés ;
- toutes les autres variables prennent leur valeur par défaut (UE, CMEK activé, 30 jours, pas de web, options
  avancées désactivées).

Pour voir la valeur finale d'une variable : `terraform console`, puis `var.connectors["gdrive"]`.

---

## 5. Dépendances avec les autres fichiers

Ce fichier ne dépend de rien. Les valeurs viennent de [`terraform.tfvars.example`](../terraform.tfvars.example)
(copié en `terraform.tfvars`, voir [12-tfvars.md](12-tfvars.md)).

| Fichier | Variables utilisées | Fiche |
|---|---|---|
| [`versions.tf`](../versions.tf) | `project_id`, `region` | [01-versions.md](01-versions.md) |
| [`00_foundation.tf`](../00_foundation.tf) | `project_id`, `ge_location`, `enable_agent_gateway` | [03-foundation.md](03-foundation.md) |
| [`10_identity_access.tf`](../10_identity_access.tf) | `project_id`, `ge_location`, `identity_provider`, `workforce_pool`, `user_groups`, `admin_groups`, `security_groups`, `viewer_groups` | [04-identity-access.md](04-identity-access.md) |
| [`20_data_protection.tf`](../20_data_protection.tf) | `ge_location`, `enable_cmek`, `kms_key_ring`, `connectors` | [05-data-protection.md](05-data-protection.md) |
| [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) | `project_id`, `ge_location`, `app_id`, `armor_confidence`, `sdp_mode`, `dlp_location`, `sensitive_info_types`, `log_screened_content` | [06-ai-guardrails.md](06-ai-guardrails.md) |
| [`40_connectors.tf`](../40_connectors.tf) | `ge_location`, `connectors`, `enable_cmek` | [07-connectors.md](07-connectors.md) |
| [`50_app.tf`](../50_app.tf) | `project_id`, `region`, `ge_location`, `app_id`, `app_display_name`, `company_name`, `enable_cmek`, `session_ttl_days`, `extra_data_store_ids`, `banned_phrases`, `web_grounding`, `features`, `enable_observability`, `enable_agent_gateway` | [08-app.md](08-app.md) |
| [`60_advanced.tf`](../60_advanced.tf) | `project_id`, `region`, `app_id`, `enable_agent_gateway`, `vpc_sc_access_policy` | [09-advanced.md](09-advanced.md) |
| [`70_detection.tf`](../70_detection.tf) | `project_id`, `log_screened_content`, `alert_email` | [10-detection.md](10-detection.md) |
| [`outputs.tf`](../outputs.tf) | `project_id`, `ge_location`, `app_id`, `enable_cmek`, `connectors`, `enable_agent_gateway` | [11-outputs.md](11-outputs.md) |

---

## 6. Pour reproduire / adapter

Modèle avec les cas les plus courants :

```hcl
# --- Obligatoire : pas de default ---
variable "project_id" {
  description = "Projet GCP cible."
  type        = string
}

# --- Optionnelle, avec un défaut SÛR ---
variable "retention_days" {
  description = "Durée de conservation (jours)."
  type        = number
  default     = 30
  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 365
    error_message = "Entre 1 et 365 jours."
  }
}

# --- Liste fermée de valeurs (énumération) ---
variable "mode" {
  description = "basic ou advanced."
  type        = string
  default     = "advanced"
  validation {
    condition     = contains(["basic", "advanced"], var.mode)
    error_message = "Valeurs possibles : basic, advanced."
  }
}

# --- Option désactivable : "" = désactivée ---
variable "alert_email" {
  description = "Adresse des alertes. Vide = pas d'alerte."
  type        = string
  default     = ""
}

# --- Collection d'objets, champs optionnels avec défauts ---
variable "sources" {
  description = "Une entrée = une source. La clé sert d'identifiant stable."
  type = map(object({
    kind     = string                              # obligatoire
    label    = string                              # obligatoire
    options  = optional(map(string), {})           # optionnel, défaut {}
    enabled  = optional(bool, true)                # optionnel, défaut true
    children = optional(list(object({
      name   = string
      params = optional(string)                    # optionnel, défaut null
    })), [])
  }))
  default = {}
}
```

Étapes :

1. Listez ce qui **change** entre environnements ou clients : ce sont vos variables. Le reste reste écrit en dur.
2. Pour chaque variable : `description` claire, `type` précis, et un `default` **sûr** (ou pas de défaut si la
   personne doit choisir).
3. Ajoutez une `validation` dès qu'une valeur fausse ne serait détectée qu'au déploiement (localisations, énumérations).
4. Pour une liste d'éléments similaires, préférez `map(object({…}))` à `list(object({…}))` : la clé sert à
   `for_each` (voir [00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set)).
5. Fournissez un `terraform.tfvars.example` commenté ; ne committez jamais le vrai `terraform.tfvars`.
6. Vérifiez avec `terraform validate`, puis `terraform console` (`var.sources`) pour voir les défauts appliqués.

Les valeurs possibles d'un argument (ex. `web_grounding_type`, `idp_type`) sont dans la page de la ressource qui
l'utilise : `https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/<type sans "google_">`.
Syntaxe des variables : `https://developer.hashicorp.com/terraform/language/values/variables`.

---

## 7. Pièges et bonnes pratiques

- **Variables obligatoires** (`project_id`, `user_groups`, `admin_groups`, `security_groups`) : si elles manquent
  dans `terraform.tfvars`, `plan` les demande de façon interactive (et échoue en CI).
- **Préfixe des membres IAM** : écrivez `"group:nom@domaine"`, pas seulement l'adresse. Sans préfixe, l'attribution
  du rôle échoue.
- **Une map ou une liste donnée dans `tfvars` remplace entièrement le défaut** (`features`,
  `sensitive_info_types`) : il n'y a pas de fusion. Recopiez les éléments à garder.
- **Validez les variables à liste fermée** : `identity_provider`, `armor_confidence`, `sdp_mode` et `web_grounding`
  ont un bloc `validation { condition = contains([...], var.x) }`. Sans lui, une faute de frappe ne serait détectée
  qu'à l'appel Google, voire pas du tout : avec `sdp_mode = "avanced"`, ni le mode `advanced` ni le mode `basic` ne
  s'appliqueraient dans `30_ai_guardrails.tf`, et le filtre de données sensibles disparaîtrait **sans erreur**.
  Testez : `terraform plan -var sdp_mode=avanced` → refusé avec le message de la validation.
- **Valeurs immuables** : `ge_location`, `app_id`, la **clé** d'un connecteur et `static_ip`. Les modifier recrée la
  ressource. Lisez le `plan` (`-/+`).
- **Renommer la clé d'un connecteur** (`gdrive` → `drive`) = détruire puis recréer le connecteur.
- **Jamais de secret dans `params`** : seulement dans `secret_params`, et seulement le **nom** du secret.
- **`enable_cmek`** : décidez avant le premier `apply`. L'activer plus tard ne rechiffre pas l'app existante.
- Ajoutez une `description` aux variables qui n'en ont pas (`app_id`, `app_display_name`, `company_name`,
  `kms_key_ring`).
