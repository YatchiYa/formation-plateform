# 06. `30_ai_guardrails.tf` : filtrage IA avec Model Armor et DLP

> Ce fichier crée les filtres qui analysent chaque question et chaque réponse de l'assistant (injection, liens
> malveillants, contenus toxiques, données sensibles françaises), plus un « plancher » de sécurité non contournable.
> Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Un assistant IA peut être manipulé (« ignore tes instructions… »), relayer un lien de phishing, produire un contenu
toxique ou recopier un IBAN trouvé dans un document. Ce fichier installe **Model Armor**, un service Google qui
analyse le texte **avant** qu'il arrive au modèle (la question) et **avant** qu'il arrive à l'utilisateur (la
réponse), et bloque ce qui est dangereux. Comme Model Armor est un classifieur **indépendant** du modèle, on ne peut
pas le « convaincre » de laisser passer. Un **plancher** (floor setting) empêche ensuite quiconque d'affaiblir ces
filtres. Le « pourquoi » complet : [guide du socle (docs/00) §8](../../docs/00-socle-securite.md#8-couche-4--filtrage-ia-avec-model-armor).

**Vocabulaire Google Cloud :**

| Terme | En clair |
|---|---|
| **Model Armor** | Service Google qui « filtre » les textes envoyés à une IA et produits par elle. Il analyse et oublie (pas de stockage). |
| **Template Model Armor** | Une configuration de filtres réutilisable (quels filtres, quels seuils, bloquer ou observer). |
| **DLP / Sensitive Data Protection (SDP)** | Service Google de détection de données sensibles (n° de carte, IBAN…). Model Armor s'en sert pour son filtre « données sensibles ». |
| **infoType** | Un **type** de donnée sensible que DLP sait reconnaître, désigné par un nom fixe : `FRANCE_NIR`, `IBAN_CODE`… |
| **Inspect template** (DLP) | La liste des infoTypes à rechercher et le niveau de certitude exigé. |
| **Floor setting** (plancher) | Le minimum de sécurité imposé à **tous** les templates du projet. |
| **Service agent** | Compte technique géré par Google qui agit pour un service dans votre projet (ici, celui de Model Armor et celui de Gemini Enterprise). |
| **IAM** | Le système de droits : « tel compte a tel rôle sur telle ressource ». |

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_data_loss_prevention_inspect_template.fr` | `resource` (avec `count`) | Liste des données sensibles françaises / UE et secrets techniques à détecter. |
| `google_project_iam_member.armor_reads_dlp` | `resource` (avec `for_each`) | Autorise le service agent Model Armor à utiliser le template DLP. |
| `google_model_armor_template.shield` | `resource` (avec `for_each`) | Deux templates de filtres : `ge-prompt-shield` (questions) et `ge-response-shield` (réponses). |
| `google_project_iam_member.ge_uses_armor` | `resource` | Autorise Gemini Enterprise à appeler Model Armor. |
| `google_model_armor_floorsetting.project` | `resource` | Plancher : aucun template du projet ne peut être moins strict que ce minimum. |

---

## 3. Le code expliqué, bloc par bloc

Valeurs d'exemple (défauts de `variables.tf`, que `terraform.tfvars.example` ne change pas) :

```hcl
project_id           = "acme-gemini-enterprise-prd"
ge_location          = "eu"
app_id               = "assistant-ia"
sdp_mode             = "advanced"
dlp_location         = "europe"
armor_confidence     = "MEDIUM_AND_ABOVE"
log_screened_content = false
sensitive_info_types = [
  "FRANCE_NIR", "FRANCE_CNI", "FRANCE_PASSPORT", "FRANCE_TAX_IDENTIFICATION_NUMBER",
  "IBAN_CODE", "CREDIT_CARD_NUMBER",
  "GCP_CREDENTIALS", "GCP_API_KEY", "AUTH_TOKEN", "AWS_CREDENTIALS", "ENCRYPTION_KEY",
]
```

Et depuis [`00_foundation.tf`](../00_foundation.tf) : `local.project_number` (ici le numéro fictif `123456789012`)
et `local.ge_sa` (le service agent de Gemini Enterprise, voir [03-foundation.md](03-foundation.md)).

### 3.1 Le template DLP « données sensibles FR »

```hcl
# COUCHE 3 - FILTRAGE IA : Model Armor sur chaque question et chaque réponse.

# 3.1 Détecteurs de données sensibles adaptés à la France (mode advanced).
resource "google_data_loss_prevention_inspect_template" "fr" {
  count        = var.sdp_mode == "advanced" ? 1 : 0
  parent       = "projects/${var.project_id}/locations/${var.dlp_location}"
  template_id  = "ge-donnees-sensibles-fr"
  display_name = "Gemini Enterprise - données sensibles FR/UE"
  description  = "Identifiants français, données bancaires, secrets techniques."
```

- `count = var.sdp_mode == "advanced" ? 1 : 0` : **`count`** fixe le nombre d'exemplaires ; le **ternaire**
  `condition ? A : B` vaut 1 si le mode est `advanced`, 0 sinon. Avec l'exemple : 1 template. On le référence avec
  `[0]`. Voir [00-bases §8](00-bases-terraform.md#8-créer-plusieurs-exemplaires--count-et-for_each) et
  [§12.1](00-bases-terraform.md#121-condition-ternaire).
- Pourquoi deux modes : le mode `basic` de Model Armor utilise les détecteurs **par défaut** de Google, **orientés
  États-Unis** (n° de sécurité sociale US…). Il ne détecte ni le NIR ni l'IBAN. Le mode `advanced` utilise **notre**
  liste ([guide du socle (docs/00) §8.2](../../docs/00-socle-securite.md#82-les-templates-filtre-par-filtre)).
- `parent = "projects/${var.project_id}/locations/${var.dlp_location}"` : où ranger le template. `${...}` est une
  **interpolation**. Résultat : `projects/acme-gemini-enterprise-prd/locations/europe`. L'emplacement `europe`
  avec un template Model Armor `eu` est **à vérifier** en recette ; repli : `dlp_location = "global"`
  ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- `template_id` : nom technique fixe. Identifiant final (`.id`) :
  `projects/acme-gemini-enterprise-prd/locations/europe/inspectTemplates/ge-donnees-sensibles-fr`.
- `display_name`, `description` : textes lisibles dans la console.

```hcl
  inspect_config {
    min_likelihood = "LIKELY" # évite les faux positifs sur des nombres quelconques
    dynamic "info_types" {
      for_each = var.sensitive_info_types
      content {
        name = info_types.value
      }
    }
  }
  depends_on = [google_project_service.apis]
}
```

- `inspect_config` : **sous-bloc** (bloc imbriqué) qui décrit quoi chercher.
- `min_likelihood = "LIKELY"` : DLP donne un niveau de certitude à chaque détection (`VERY_UNLIKELY`, `UNLIKELY`,
  `POSSIBLE`, `LIKELY`, `VERY_LIKELY`). On ne garde que `LIKELY` et au-dessus : une suite de chiffres quelconque ne
  sera pas prise pour un NIR.
- `dynamic "info_types"` : **bloc dynamique**. L'API attend un sous-bloc `info_types { name = "..." }` **par type**.
  Plutôt que de l'écrire 11 fois, `dynamic` le génère :
  - `for_each = var.sensitive_info_types` : la liste des 11 types ;
  - dans `content`, l'élément en cours s'appelle **comme le bloc** : `info_types.value`.

  Avec l'exemple, c'est équivalent à :
  ```hcl
  info_types { name = "FRANCE_NIR" }
  info_types { name = "FRANCE_CNI" }
  info_types { name = "FRANCE_PASSPORT" }
  # ... jusqu'à
  info_types { name = "ENCRYPTION_KEY" }
  ```
  Voir [00-bases §10](00-bases-terraform.md#10-les-blocs-imbriqués-optionnels-ou-répétés--dynamic).
  Pourquoi ces types-là (et pourquoi **pas** les e-mails ni les téléphones) : [guide du socle (docs/00) §8.3](../../docs/00-socle-securite.md#83-les-données-sensibles-détectées-france--ue).
- `depends_on = [google_project_service.apis]` : l'API `dlp.googleapis.com` doit être activée avant
  ([`00_foundation.tf`](../00_foundation.tf)). Voir [00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on).

### 3.2 Model Armor a le droit de lire le template DLP

```hcl
# Le service agent Model Armor lit le template DLP.
resource "google_project_iam_member" "armor_reads_dlp" {
  for_each   = var.sdp_mode == "advanced" ? toset(["roles/dlp.user", "roles/dlp.reader"]) : toset([])
  project    = var.project_id
  role       = each.value
  member     = "serviceAccount:service-${local.project_number}@gcp-sa-modelarmor.iam.gserviceaccount.com"
  depends_on = [terraform_data.service_agents]
}
```

- `for_each` : crée **un exemplaire par élément**. `toset([...])` transforme la liste en **ensemble** (set), le type
  accepté par `for_each`. Le ternaire renvoie les 2 rôles en mode `advanced`, un ensemble vide sinon. Avec l'exemple :
  2 droits, d'adresses `google_project_iam_member.armor_reads_dlp["roles/dlp.user"]` et `["roles/dlp.reader"]`.
  Voir [00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set).
- `role = each.value` : l'élément en cours (pour un set, `each.key` = `each.value`).
- `member` : l'adresse du **service agent Model Armor**, construite avec le numéro du projet :
  `serviceAccount:service-123456789012@gcp-sa-modelarmor.iam.gserviceaccount.com`. C'est ce compte qui, au moment du
  filtrage, appelle DLP avec notre template.
- `project` : les rôles sont donnés **au niveau du projet** (le template DLP n'a pas de droits propres).
- `depends_on = [terraform_data.service_agents]` : force la création préalable du service agent Model Armor
  ([`00_foundation.tf`](../00_foundation.tf)). Sinon IAM refuse un compte qui n'existe pas encore.
- `google_project_iam_member` **ajoute** un droit sans toucher aux autres (à préférer à `_iam_policy`, qui écrase tout).

### 3.3 Les deux templates Model Armor

Le bloc est long ; on le découpe en morceaux consécutifs.

```hcl
# 3.2 Deux templates : un pour les questions (entrée), un pour les réponses (sortie).
resource "google_model_armor_template" "shield" {
  for_each    = toset(["ge-prompt-shield", "ge-response-shield"])
  location    = var.ge_location # app 'eu' => templates 'eu'
  template_id = each.value
  labels      = { app = var.app_id, owner = "security" }
```

- `for_each = toset([...])` : **deux** templates avec la même configuration, un par nom. Adresses :
  `google_model_armor_template.shield["ge-prompt-shield"]` et `google_model_armor_template.shield["ge-response-shield"]`.
- Pourquoi deux : filtrer seulement les questions laisse passer une réponse qui recopierait un IBAN trouvé dans un
  document ; filtrer seulement les réponses laisse passer les tentatives de manipulation ([guide du socle (docs/00) §8.1](../../docs/00-socle-securite.md#81-le-principe)).
  Les deux ont ici le même contenu, mais restent séparés pour pouvoir les régler différemment plus tard.
- `location = var.ge_location` : `"eu"`. Règle Google : une app `eu` exige des templates `eu`.
- `template_id = each.value` : `"ge-prompt-shield"` puis `"ge-response-shield"`.
- `labels` : étiquettes ; `app = var.app_id` donne `app = "assistant-ia"`.

```hcl
  filter_config {
    # Injection de prompt / jailbreak : "ignore tes instructions...".
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = var.armor_confidence
    }
    # Liens de phishing / malware connus (256 premières URL).
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
```

- `filter_config` : le sous-bloc qui contient tous les filtres.
- `pi_and_jailbreak_filter_settings` : détecte l'**injection de prompt** (instructions cachées, y compris dans un
  document) et le **jailbreak** (contourner les règles). `filter_enforcement = "ENABLED"` l'active.
- `confidence_level = var.armor_confidence` : seuil de déclenchement, `"MEDIUM_AND_ABOVE"` par défaut. Les valeurs
  possibles : `LOW_AND_ABOVE` (bloque au moindre doute), `MEDIUM_AND_ABOVE` (équilibre), `HIGH` (seulement les cas
  quasi certains). Pourquoi l'équilibre : un outil qui bloque à tort pousse les gens vers des IA grand public non
  maîtrisées ([guide du socle (docs/00) §8.2](../../docs/00-socle-securite.md#82-les-templates-filtre-par-filtre)).
- `malicious_uri_filter_settings` : bloque les liens de phishing ou de malware connus.

```hcl
    # IA responsable : haine, harcèlement, sexuel explicite, dangereux.
    rai_settings {
      dynamic "rai_filters" {
        for_each = ["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"]
        content {
          filter_type      = rai_filters.value
          confidence_level = var.armor_confidence
        }
      }
    }
```

- `rai_settings` (RAI = *Responsible AI*, IA responsable) : filtres de contenus toxiques.
- `dynamic "rai_filters"` : génère un sous-bloc `rai_filters` par catégorie. Ici `for_each` reçoit directement une
  **liste** écrite en dur (un `dynamic` accepte une liste, contrairement au `for_each` d'une ressource). Résultat :
  ```hcl
  rai_filters {
    filter_type      = "HATE_SPEECH"
    confidence_level = "MEDIUM_AND_ABOVE"
  }
  rai_filters {
    filter_type      = "HARASSMENT"
    confidence_level = "MEDIUM_AND_ABOVE"
  }
  # ... idem pour "SEXUALLY_EXPLICIT" et "DANGEROUS"
  ```

```hcl
    # Données sensibles : détecteurs FR (advanced) ou détecteurs Google par défaut (basic).
    sdp_settings {
      dynamic "advanced_config" {
        for_each = var.sdp_mode == "advanced" ? [1] : []
        content {
          inspect_template = google_data_loss_prevention_inspect_template.fr[0].id
        }
      }
      dynamic "basic_config" {
        for_each = var.sdp_mode == "basic" ? [1] : []
        content {
          filter_enforcement = "ENABLED"
        }
      }
    }
  }
```

- `sdp_settings` : le filtre « données sensibles » (SDP = *Sensitive Data Protection*). Il accepte **soit**
  `advanced_config`, **soit** `basic_config`.
- **Bloc conditionnel** avec `dynamic` : `for_each = condition ? [1] : []` veut dire « générer le bloc **une fois** si
  la condition est vraie, **zéro fois** sinon ». La valeur `1` ne sert à rien d'autre qu'à avoir une liste d'un
  élément. Voir [00-bases §10](00-bases-terraform.md#10-les-blocs-imbriqués-optionnels-ou-répétés--dynamic).
- Avec l'exemple (`sdp_mode = "advanced"`), seul `advanced_config` existe :
  ```hcl
  sdp_settings {
    advanced_config {
      inspect_template = "projects/acme-gemini-enterprise-prd/locations/europe/inspectTemplates/ge-donnees-sensibles-fr"
    }
  }
  ```
- `inspect_template = google_data_loss_prevention_inspect_template.fr[0].id` : référence au template DLP du §3.1.
  `[0]` car il a un `count`. Cette référence n'est évaluée que si le bloc existe, c'est-à-dire en mode `advanced`,
  justement quand `[0]` existe.
- La dernière `}` ferme `filter_config`.

```hcl
  template_metadata {
    enforcement_type        = "INSPECT_AND_BLOCK"
    log_template_operations = true                     # QUI modifie les filtres : toujours tracé
    log_sanitize_operations = var.log_screened_content # le CONTENU filtré : non par défaut (RGPD)
    multi_language_detection {
      enable_multi_language_detection = true # français testé par Google
    }
  }

  depends_on = [google_project_service.apis, google_project_iam_member.armor_reads_dlp]
}
```

- `template_metadata` : le **comportement** du template et sa journalisation ([guide du socle (docs/00) §8.4](../../docs/00-socle-securite.md#84-métadonnées-du-template--comportement-et-journalisation)).
- `enforcement_type = "INSPECT_AND_BLOCK"` : on **bloque** (l'autre valeur, `INSPECT_ONLY`, se contente d'observer).
- `log_template_operations = true` : chaque **modification** du template (qui, quand) est journalisée.
- `log_sanitize_operations = var.log_screened_content` : journaliser le **contenu** filtré (les questions des
  collaborateurs). `false` par défaut : Google le déconseille pour Gemini Enterprise, et c'est un sujet RGPD / vie
  privée à trancher avec le DPO.
- `multi_language_detection` : active la détection dans d'autres langues que l'anglais (le français est testé par
  Google).
- `depends_on` : l'API Model Armor doit être active **et** Model Armor doit déjà pouvoir lire le template DLP. Ce
  second lien n'apparaît dans aucun attribut, d'où `depends_on`. En mode `basic`, `armor_reads_dlp` est vide : la
  dépendance ne gêne pas.

### 3.4 Gemini Enterprise a le droit d'appeler Model Armor

```hcl
# 3.3 Gemini Enterprise est autorisé à appeler Model Armor.
resource "google_project_iam_member" "ge_uses_armor" {
  project    = var.project_id
  role       = "roles/modelarmor.user"
  member     = local.ge_sa
  depends_on = [terraform_data.service_agents]
}
```

- Ressource simple (ni `count` ni `for_each`) : toujours créée.
- `role = "roles/modelarmor.user"` : droit d'**utiliser** les templates (analyser un texte), pas de les modifier.
- `member = local.ge_sa` : le service agent de Gemini Enterprise
  (`serviceAccount:service-123456789012@gcp-sa-discoveryengine.iam.gserviceaccount.com`).
- `depends_on` : même raison qu'au §3.2.
- L'assistant ([`50_app.tf`](../50_app.tf)) dépend de ce droit : sans lui, avec `FAIL_CLOSED`, il refuserait toutes
  les questions.

### 3.5 Le plancher (floor setting)

```hcl
# 3.4 Plancher (floor setting) : personne ne peut créer ou modifier un template
#     moins strict que ce minimum, même un administrateur pressé.
resource "google_model_armor_floorsetting" "project" {
  parent                           = "projects/${var.project_id}"
  location                         = "global"
  enable_floor_setting_enforcement = true
```

- `parent = "projects/${var.project_id}"` : le plancher s'applique au **projet**.
- `location = "global"` : le plancher est un réglage global du projet (même si les templates sont en `eu`).
- `enable_floor_setting_enforcement = true` : le plancher est **appliqué** : toute création ou modification de
  template **moins strict** est refusée.

```hcl
  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "HIGH" # minimum absolu ; les templates sont plus stricts (MEDIUM)
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    rai_settings {
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = "HIGH"
      }
    }
  }
```

- Même structure que `filter_config` des templates, mais ce sont des **minimums** :
  - injection/jailbreak obligatoirement actif, au moins au seuil `HIGH` ;
  - filtre de liens malveillants obligatoire ;
  - catégorie `DANGEROUS` obligatoire, au moins au seuil `HIGH`.
- Ici `rai_filters` est écrit **en dur** (un seul bloc), sans `dynamic` : quand il n'y a qu'un élément fixe, c'est
  plus lisible.
- Le plancher est **volontairement moins strict** que les templates : `HIGH` (ne bloque que le quasi certain) contre
  `MEDIUM_AND_ABOVE`. Il fixe le minimum absolu ; les templates portent la politique réelle
  ([guide du socle (docs/00) §8.6](../../docs/00-socle-securite.md#86-le-plancher-floor-setting--la-sécurité-quon-ne-peut-pas-affaiblir)).

```hcl
  floor_setting_metadata {
    multi_language_detection {
      enable_multi_language_detection = true
    }
  }

  depends_on = [google_project_service.apis]
}
```

- `floor_setting_metadata.multi_language_detection` : le plancher exige aussi la détection multilingue.
- `depends_on` : l'API Model Armor doit être active.

---

## 4. Ce que Terraform crée concrètement

Avec les valeurs d'exemple (`sdp_mode = "advanced"`) :

| Ce qui apparaît dans Google Cloud | Nombre |
|---|---|
| Template DLP `ge-donnees-sensibles-fr` (11 types de données, dans `europe`) | 1 |
| Rôles `roles/dlp.user` et `roles/dlp.reader` pour le service agent Model Armor | 2 |
| Templates Model Armor `ge-prompt-shield` et `ge-response-shield` (dans `eu`) | 2 |
| Rôle `roles/modelarmor.user` pour le service agent Gemini Enterprise | 1 |
| Plancher Model Armor du projet | 1 |
| **Total** | **7** |

Avec `sdp_mode = "basic"` : 4 ressources (pas de template DLP, pas de droits DLP ; les templates utilisent
`basic_config`).

Dans la console : *Sécurité → Model Armor* (templates et onglet *Floor settings*), *Sensitive Data Protection →
Configuration → Templates*. Les templates **ne filtrent rien tout seuls** : ils sont branchés sur l'assistant dans
[`50_app.tf`](../50_app.tf).

---

## 5. Dépendances avec les autres fichiers

**Ce fichier utilise :**

| Valeur | Vient de |
|---|---|
| `var.project_id`, `var.ge_location`, `var.app_id`, `var.sdp_mode`, `var.dlp_location`, `var.sensitive_info_types`, `var.armor_confidence`, `var.log_screened_content` | [`variables.tf`](../variables.tf) ([02-variables.md](02-variables.md)) |
| `local.project_number`, `local.ge_sa`, `google_project_service.apis`, `terraform_data.service_agents` | [`00_foundation.tf`](../00_foundation.tf) ([03-foundation.md](03-foundation.md)) |

**Ce fichier est utilisé par :**

| Valeur | Utilisée dans |
|---|---|
| `google_model_armor_template.shield["ge-prompt-shield"].id` et `["ge-response-shield"].id` | `model_armor_config` de l'assistant, avec `failure_mode = "FAIL_CLOSED"` ([`50_app.tf`](../50_app.tf), [08-app.md](08-app.md)) |
| `google_project_iam_member.ge_uses_armor` | `depends_on` de l'assistant ([`50_app.tf`](../50_app.tf)) |
| `google_model_armor_template.shield` | sortie `model_armor_templates` ([`outputs.tf`](../outputs.tf), [11-outputs.md](11-outputs.md)) |
| `var.log_screened_content` (même variable) | métrique et alerte « pic de blocages », créées seulement si `true` ([`70_detection.tf`](../70_detection.tf), [10-detection.md](10-detection.md)) |

L'alerte « garde-fou modifié » de [`70_detection.tf`](../70_detection.tf) surveille `UpdateTemplate`, `DeleteTemplate`
et `UpdateFloorSetting`.

---

## 6. Pour reproduire / adapter

**Besoin type : ajouter un filtre Model Armor pour une autre application IA** (un agent maison, une autre app).

```hcl
# Template de filtres pour une autre application.
resource "google_model_armor_template" "mon_app" {
  location    = "eu"                         # même emplacement que l'app qui l'utilise
  template_id = "mon-app-shield"
  labels      = { app = "mon-app", owner = "security" }

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE" # >= au plancher (HIGH), sinon refusé
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    rai_settings {
      dynamic "rai_filters" {
        for_each = ["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"]
        content {
          filter_type      = rai_filters.value
          confidence_level = "MEDIUM_AND_ABOVE"
        }
      }
    }
    sdp_settings {
      advanced_config {
        # Réutiliser le template DLP existant (ou en créer un autre)
        inspect_template = google_data_loss_prevention_inspect_template.fr[0].id
      }
    }
  }

  template_metadata {
    enforcement_type        = "INSPECT_AND_BLOCK"  # "INSPECT_ONLY" pour une phase d'observation
    log_template_operations = true
    log_sanitize_operations = false                # contenu non journalisé (RGPD)
    multi_language_detection {
      enable_multi_language_detection = true
    }
  }
}

# Le compte qui appelle Model Armor pour cette app.
resource "google_project_iam_member" "mon_app_uses_armor" {
  project = var.project_id
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:mon-agent@mon-projet.iam.gserviceaccount.com"
}
```

**Étapes :**

1. Choisir l'emplacement du template : le même que l'application qui l'appellera.
2. Écrire le template : https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/model_armor_template
3. Pour des données sensibles spécifiques, créer ou réutiliser un template DLP :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/data_loss_prevention_inspect_template
   (liste des infoTypes : doc Google « InfoType detector reference »). Penser aux rôles `dlp.user` / `dlp.reader` du
   service agent Model Armor.
4. Donner `roles/modelarmor.user` au compte de l'application :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam
5. **Brancher** le template dans l'application (pour un agent maison : appel à l'API Model Armor depuis son code).
6. Vérifier la compatibilité avec le plancher :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/model_armor_floorsetting —
   puis tester avec des questions pièges (injection, faux IBAN) en recette.

---

## 7. Pièges et bonnes pratiques

- **Le plancher refuse tout template moins strict.** Exemple : un template avec le filtre injection désactivé, ou
  sans la catégorie `DANGEROUS`, sera rejeté par l'API. Gardez les templates **au moins aussi stricts** que le plancher
  (`MEDIUM_AND_ABOVE` et `LOW_AND_ABOVE` sont plus stricts que `HIGH`).
- **Pour durcir le plancher**, vérifiez d'abord que **tous** les templates existants du projet le respectent.
- **Emplacement du template DLP à valider** : `europe` avec un template Model Armor `eu` n'est pas documenté par
  Google. Repli : `dlp_location = "global"`, ou `sdp_mode = "basic"` temporairement ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- **Le mode `basic` est orienté États-Unis** : il ne voit ni NIR, ni CNI, ni IBAN. Ne l'utilisez qu'en repli
  temporaire.
- **Pourquoi `sdp_mode` est validé** dans `variables.tf` : sans validation, une faute de frappe (`"advance"`)
  supprimerait **à la fois** `advanced_config` et `basic_config`, donc le filtre de données sensibles, **sans
  erreur**. La validation la refuse dès le `plan`. `armor_confidence` est validé de la même façon. Leçon générale :
  validez toute variable qui pilote un bloc `dynamic` conditionnel.
- **`min_likelihood` trop bas** (`POSSIBLE`) : beaucoup de faux positifs sur les nombres. Trop haut (`VERY_LIKELY`) :
  des fuites. `LIKELY` est le compromis retenu.
- **Ne pas bloquer les e-mails et téléphones** : l'outil deviendrait inutilisable ; ils restent protégés par les
  droits d'accès ([guide du socle (docs/00) §8.3](../../docs/00-socle-securite.md#83-les-données-sensibles-détectées-france--ue)).
- **`log_sanitize_operations = true` met les questions des salariés dans les journaux** : décision DPO / CSE. Sans
  cela, l'alerte « pic de blocages » de `70_detection.tf` n'existe pas (compromis assumé, [guide du socle (docs/00) §15](../../docs/00-socle-securite.md#15-compromis-assumés)).
- **Model Armor ne filtre pas les agents personnalisés** (ADK, A2A, Dialogflow) branchés sur Gemini Enterprise : ils
  doivent se filtrer eux-mêmes ([guide du socle (docs/00) §8.1](../../docs/00-socle-securite.md#81-le-principe)).
- **Tout changement de ce fichier** passe par une PR validée par l'équipe sécurité ([guide du socle (docs/00) §14.1](../../docs/00-socle-securite.md#141-tout-changement-passe-par-le-code)).
