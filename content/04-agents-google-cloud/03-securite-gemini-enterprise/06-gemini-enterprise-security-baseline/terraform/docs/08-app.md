# 08. `50_app.tf` : l'application Gemini Enterprise et son assistant

> Ce fichier crée l'app Gemini Enterprise, son assistant protégé par Model Armor, et applique par l'API REST les
> réglages que le provider ne sait pas encore gérer. Bases Terraform : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

C'est le cœur visible du projet : l'**application** que les collaborateurs ouvrent dans leur navigateur. Le fichier
crée l'app (le « moteur » de recherche et de chat), lui rattache les sources de données des connecteurs, puis crée
son **assistant** (le chat IA) en le branchant sur les filtres Model Armor. Enfin, il applique trois réglages
absents du provider Terraform (durée de conservation des conversations, observabilité, Agent Gateway) par un appel
direct à l'API Google.

---

## 2. Vue d'ensemble

| Bloc (adresse) | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_discovery_engine_search_engine.app` | `resource` | L'app Gemini Enterprise elle-même, avec ses sources et ses fonctionnalités. |
| `google_discovery_engine_assistant.default` | `resource` | L'assistant (chat) de l'app : langue, consignes, filtres Model Armor, phrases interdites, recherche web. |
| `local.engine_settings` | `locals` | Le contenu JSON des réglages non gérés par le provider. |
| `terraform_data.engine_settings` | `resource` | Envoie ces réglages à l'API REST avec `curl`, à chaque changement. |

---

## 3. Le code expliqué, bloc par bloc

### 3.1 L'app : `google_discovery_engine_search_engine.app`

**Vocabulaire.** Dans l'API Google, Gemini Enterprise s'appelle encore « Discovery Engine » (ancien nom :
Agentspace). Une app y est un **engine** (moteur). Les sources de données y sont des **data stores** (magasins de
données). Les apps sont rangées dans une **collection** ; la collection par défaut s'appelle `default_collection`.

```hcl
resource "google_discovery_engine_search_engine" "app" {
  location          = var.ge_location
  collection_id     = "default_collection"
  engine_id         = var.app_id
  display_name      = var.app_display_name
  industry_vertical = "GENERIC"
  app_type          = "APP_TYPE_INTRANET" # = une app Gemini Enterprise
```

| Ligne | Ce qu'elle fait | D'où vient la valeur / pourquoi |
|---|---|---|
| `location = var.ge_location` | Multi-région de l'app. | Variable, défaut `"eu"` : données en Union européenne (README §9.1). **Immuable** : la changer recrée l'app. |
| `collection_id = "default_collection"` | Collection où ranger l'app. | Valeur fixe de Google. |
| `engine_id = var.app_id` | Identifiant technique de l'app (apparaît dans les URL). | Variable, défaut `"assistant-ia"`. |
| `display_name = var.app_display_name` | Nom affiché aux utilisateurs. | Variable, défaut `"Assistant IA"`. |
| `industry_vertical = "GENERIC"` | Secteur métier de l'app. | `GENERIC` = usage général (pas « santé » ni « média »). |
| `app_type = "APP_TYPE_INTRANET"` | Type d'app. | C'est **cette valeur** qui fait de l'engine une app **Gemini Enterprise** (et pas un simple moteur de recherche de site web). |

```hcl
  data_store_ids    = concat(local.connector_data_store_ids, var.extra_data_store_ids)
  kms_key_name      = var.enable_cmek ? google_kms_crypto_key.ge[0].id : null
  features          = var.features
```

- **`data_store_ids`** : la liste des sources rattachées à l'app. On la construit avec **`concat`**, qui colle deux
  listes bout à bout ([00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)) :
  - `local.connector_data_store_ids` : les data stores créés par les connecteurs, calculés dans
    [`40_connectors.tf`](../40_connectors.tf) (voir [07-connectors.md](07-connectors.md)) ;
  - `var.extra_data_store_ids` : des data stores créés à la main dans la console (défaut `[]`).

  Exemple concret : si les connecteurs produisent `["sharepoint_file"]` et que `extra_data_store_ids` vaut
  `["intranet-rh"]`, alors `concat(...)` donne `["sharepoint_file", "intranet-rh"]`.
  Avec le `terraform.tfvars.example`, `extra_data_store_ids` n'est pas renseigné, donc vaut `[]`.

  Comme cette ligne **utilise** un attribut des connecteurs, Terraform crée les connecteurs **avant** l'app
  (dépendance implicite, [00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on)).

- **`kms_key_name`** : la clé de chiffrement CMEK (Customer-Managed Encryption Key : une clé que Acme possède
  dans Cloud KMS, au lieu d'une clé gérée par Google). C'est une **condition ternaire**
  ([00-bases §12.1](00-bases-terraform.md#121-condition-ternaire)) :
  - si `var.enable_cmek` vaut `true` (défaut), on prend `google_kms_crypto_key.ge[0].id` (le `[0]` car la clé est
    créée avec `count`, voir [05-data-protection.md](05-data-protection.md)) ;
  - sinon `null`, ce qui veut dire « ne pas renseigner cet argument » (Google chiffre alors avec ses propres clés).

- **`features`** : une map « nom de fonctionnalité → état ». La valeur vient de `var.features`
  ([`variables.tf`](../variables.tf)). Par défaut :

  ```hcl
  "disable-agent-sharing"                = "FEATURE_STATE_ON"  # pas de partage d'agents maison
  "skill-sharing-without-admin-approval" = "FEATURE_STATE_OFF" # partage de skills = validation admin
  "session-sharing"                      = "FEATURE_STATE_OFF" # pas de partage de conversations
  "feedback"                             = "FEATURE_STATE_ON"  # retours utilisateurs
  ```

  Pourquoi (README §9.3) : un agent ou une conversation partagés peuvent diffuser des consignes inadaptées ou des
  informations que le destinataire n'a pas le droit de voir. On rouvre le partage quand la gouvernance est définie.

```hcl
  common_config {
    company_name = var.company_name
  }
```

- **`common_config`** est un **sous-bloc** ([00-bases §5](00-bases-terraform.md#5-la-syntaxe--des-blocs)).
  `company_name` donne le nom de l'entreprise à l'IA, pour contextualiser ses réponses. Variable, défaut
  `"Acme"`.

```hcl
  search_engine_config {
    search_tier                = "SEARCH_TIER_ENTERPRISE"
    search_add_ons             = ["SEARCH_ADD_ON_LLM"]
    required_subscription_tier = "SUBSCRIPTION_TIER_ENTERPRISE"
  }
```

- `search_tier = "SEARCH_TIER_ENTERPRISE"` : niveau « entreprise » de la recherche (fonctions avancées).
- `search_add_ons = ["SEARCH_ADD_ON_LLM"]` : active l'option « LLM » (grand modèle de langage), c'est-à-dire les
  réponses générées par l'IA et pas seulement une liste de résultats. C'est une **liste**, même avec un seul élément.
- `required_subscription_tier = "SUBSCRIPTION_TIER_ENTERPRISE"` : l'édition de licence Gemini Enterprise exigée des
  utilisateurs (ici, « Enterprise »). Elle doit correspondre aux licences achetées.

```hcl
  depends_on = [google_discovery_engine_cmek_config.ge]
}
```

- **`depends_on`** ([00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on)) :
  force Terraform à créer l'enregistrement CMEK (`google_discovery_engine_cmek_config.ge`, dans
  [`20_data_protection.tf`](../20_data_protection.tf)) **avant** l'app. Rien dans les arguments ne le laisse deviner,
  mais Google l'exige : une app créée avant l'enregistrement de la clé reste chiffrée par Google, définitivement.
- On peut écrire `depends_on` vers une ressource qui a `count = 0` (CMEK désactivé) : la liste est alors simplement
  vide, sans erreur.

### 3.2 L'assistant : `google_discovery_engine_assistant.default`

L'**assistant** est la partie « chat » de l'app : il reçoit les questions, interroge les sources et rédige les
réponses. Chaque app en a un, nommé `default_assistant`.

```hcl
resource "google_discovery_engine_assistant" "default" {
  location           = var.ge_location
  collection_id      = "default_collection"
  engine_id          = google_discovery_engine_search_engine.app.engine_id
  assistant_id       = "default_assistant"
  display_name       = "${var.app_display_name} - assistant"
  web_grounding_type = var.web_grounding
```

- `location` et `collection_id` : les mêmes que l'app (l'assistant vit **dans** l'app).
- `engine_id = google_discovery_engine_search_engine.app.engine_id` : une **référence** à l'app
  ([00-bases §7](00-bases-terraform.md#7-les-références--relier-les-blocs-entre-eux)). Résultat : `"assistant-ia"`.
  Comme on utilise un attribut de l'app, Terraform crée l'app d'abord (pas besoin de `depends_on`).
- `assistant_id = "default_assistant"` : identifiant fixe attendu par Gemini Enterprise.
- `display_name = "${var.app_display_name} - assistant"` : **interpolation** (`${...}` insère une valeur dans un
  texte). Avec la valeur par défaut : `"Assistant IA - assistant"`.
- `web_grounding_type = var.web_grounding` : la **recherche web** (« grounding » = appuyer les réponses sur des
  sources). Défaut `"WEB_GROUNDING_TYPE_DISABLED"` : pas de recherche web publique. Pourquoi (README §9.2) : des
  fragments de questions confidentielles partiraient vers un moteur public, et la recherche Google est
  **incompatible avec la résidence UE et CMEK**. Si le métier en a besoin : `WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH`.

```hcl
  generation_config {
    default_language = "fr"
    system_instruction {
      additional_system_instruction = "Réponds à partir des données de l'entreprise et cite tes sources. Ne demande jamais de mot de passe, de numéro de sécurité sociale ou de coordonnées bancaires."
    }
  }
```

- `generation_config` : comment l'IA rédige.
- `default_language = "fr"` : langue par défaut des réponses.
- `system_instruction` → `additional_system_instruction` : une **consigne système**, ajoutée à celles de Google, que
  l'IA lit avant chaque question. Ici : citer ses sources et ne jamais réclamer de données sensibles. C'est une
  défense **en complément** de Model Armor, pas un remplacement (une consigne peut être contournée, un filtre non).

```hcl
  customer_policy {
    model_armor_config {
      user_prompt_template = google_model_armor_template.shield["ge-prompt-shield"].id
      response_template    = google_model_armor_template.shield["ge-response-shield"].id
      failure_mode         = "FAIL_CLOSED" # Model Armor indisponible => refus, jamais de réponse non filtrée
    }
```

- `customer_policy` : la politique de sécurité propre à l'entreprise.
- `model_armor_config` branche les **templates Model Armor** (Model Armor = le service Google qui filtre les
  questions et réponses : injection de prompt, données sensibles, liens malveillants…) créés dans
  [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) (voir [06-ai-guardrails.md](06-ai-guardrails.md)).
  - `user_prompt_template` : le template appliqué aux **questions**. La notation `shield["ge-prompt-shield"]` vient
    du `for_each` de la ressource `shield`
    ([00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set)).
  - `response_template` : le template appliqué aux **réponses**.
  - `failure_mode = "FAIL_CLOSED"` : si Model Armor ne répond pas (panne, droit manquant), l'assistant **refuse**
    au lieu de répondre sans filtre. L'autre valeur (`FAIL_OPEN`) privilégierait la disponibilité. Choix assumé
    (README §8.5 et §15) : la sécurité passe avant la disponibilité.

```hcl
    dynamic "banned_phrases" {
      for_each = var.banned_phrases
      content {
        phrase            = banned_phrases.value
        match_type        = "WORD_BOUNDARY_STRING_MATCH"
        ignore_diacritics = true
      }
    }
  }
```

- **`dynamic "banned_phrases"`** génère **un sous-bloc `banned_phrases` par élément** de la liste
  `var.banned_phrases` ([00-bases §10](00-bases-terraform.md#10-les-blocs-imbriqués-optionnels-ou-répétés--dynamic)).
  Dans `content`, l'élément en cours s'appelle `banned_phrases.value` (même nom que le bloc).
- `phrase` : l'expression que l'assistant ne doit jamais produire (par exemple un nom de code de projet secret).
- `match_type = "WORD_BOUNDARY_STRING_MATCH"` : on cherche l'expression comme **mot entier**. la phrase
  « Atlas » bloquera « projet Atlas » mais pas « Atlassian ».
- `ignore_diacritics = true` : les accents sont ignorés. « élève » et « eleve » sont traités pareil.

Exemple concret. Avec `banned_phrases = ["nom de code projet confidentiel"]`, Terraform génère :

```hcl
banned_phrases {
  phrase            = "nom de code projet confidentiel"
  match_type        = "WORD_BOUNDARY_STRING_MATCH"
  ignore_diacritics = true
}
```

Avec le `terraform.tfvars.example`, la ligne `banned_phrases` est en commentaire : la liste vaut `[]` (défaut), donc
**aucun** bloc n'est généré. C'est tout l'intérêt de `dynamic` : un bloc écrit à la main ne pourrait pas
« disparaître ».

```hcl
  depends_on = [google_project_iam_member.ge_uses_armor]
}
```

- Force la création du droit « Gemini Enterprise peut appeler Model Armor » (`roles/modelarmor.user`, dans
  [`30_ai_guardrails.tf`](../30_ai_guardrails.tf)) **avant** l'assistant. Sans ce droit, et avec `FAIL_CLOSED`,
  l'assistant refuserait tout.

### 3.3 Les réglages calculés : `locals { engine_settings }`

**Le problème.** Trois réglages de l'app existent dans l'API Google, mais **pas encore** dans le provider Terraform
(version `~> 8.4`) :
- la **durée de conservation** des conversations (README §6.3 : minimisation RGPD, 30 jours au lieu de 60) ;
- l'**observabilité** (traces techniques, **sans** le contenu des questions, README §9.4) ;
- le rattachement à l'**Agent Gateway** (option, voir [09-advanced.md](09-advanced.md)).

On prépare donc leur contenu JSON dans une valeur locale
([00-bases §6.4](00-bases-terraform.md#64-locals--les-valeurs-calculées)), puis on l'envoie à l'API (§3.4).

```hcl
locals {
  engine_settings = merge(
    {
      sessionConfig       = { sessionTtl = { days = var.session_ttl_days } }
      observabilityConfig = { observabilityEnabled = var.enable_observability, sensitiveLoggingEnabled = var.enable_observability && var.log_prompts_responses }
    },
    var.enable_agent_gateway ? {
      agentGatewaySetting = { defaultEgressAgentGateway = { name = "projects/${local.project_number}/locations/${var.region}/agentGateways/${google_network_services_agent_gateway.egress[0].name}" } }
    } : {},
  )
}
```

- **`merge(map1, map2)`** fusionne deux maps en une seule
  ([00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)).
- **Première map (toujours présente)** :
  - `sessionConfig = { sessionTtl = { days = var.session_ttl_days } }` : conserver les conversations
    `session_ttl_days` jours (défaut `30`).
  - `observabilityConfig = { observabilityEnabled = var.enable_observability, sensitiveLoggingEnabled = var.enable_observability && var.log_prompts_responses }` :
    traces et **journaux d'usage** activés (défaut `true`). Le texte complet des questions et réponses
    (`sensitiveLoggingEnabled`) n'est activé que si **les deux** variables valent `true` : `&&` est le « ET » logique,
    car la journalisation sensible n'a pas de sens sans l'observabilité. Par défaut `log_prompts_responses = false`.
    Où vont ces journaux : [13-logging.md](13-logging.md).
  - Les noms en *camelCase* (`sessionConfig`, `sessionTtl`…) sont ceux de l'**API REST** Google (ressource
    `Engine`), pas des noms Terraform. C'est pour ça qu'ils ne suivent pas le style `snake_case` habituel.
- **Deuxième map (conditionnelle)** : `var.enable_agent_gateway ? { agentGatewaySetting = … } : {}`.
  - Si l'Agent Gateway est activé : une map avec la clé `agentGatewaySetting`, qui donne le nom complet de la
    passerelle. Ce nom est construit par interpolation à partir du numéro de projet (`local.project_number`, dans
    [`00_foundation.tf`](../00_foundation.tf)), de la région et du nom de la passerelle (`egress[0]`, car créée avec
    `count`).
  - Sinon : `{}`, une map **vide**. Fusionner une map vide n'ajoute rien.
  - C'est la technique classique pour **ajouter une clé sous condition**. Terraform n'évalue la référence
    `egress[0]` que dans la branche choisie : pas d'erreur quand la passerelle n'existe pas.

**Exemple concret** avec le `terraform.tfvars.example` (donc les défauts `session_ttl_days = 30`,
`enable_observability = true`, `enable_agent_gateway = false`) :

```hcl
local.engine_settings = {
  observabilityConfig = { observabilityEnabled = true, sensitiveLoggingEnabled = false }
  sessionConfig       = { sessionTtl = { days = 30 } }
}
```

Avec `enable_agent_gateway = true`, une troisième clé s'ajoute :
`agentGatewaySetting = { defaultEgressAgentGateway = { name = "projects/123456789012/locations/europe-west1/agentGateways/assistant-ia-egress" } }`
(le numéro de projet est un exemple).

### 3.4 L'appel à l'API : `terraform_data.engine_settings`

Principe général : [00-bases §14](00-bases-terraform.md#14-quand-terraform-ne-sait-pas-faire--terraform_data--local-exec).

```hcl
resource "terraform_data" "engine_settings" {
  triggers_replace = [jsonencode(local.engine_settings), google_discovery_engine_search_engine.app.id]
```

- **`terraform_data`** : une ressource « vide », fournie par Terraform lui-même (pas par Google). Elle ne crée rien
  chez Google ; elle sert de support à une commande.
- **`triggers_replace`** : une liste de valeurs surveillées. **Si l'une change**, Terraform recrée la ressource, et
  la commande est donc **relancée**. Ici on surveille :
  - `jsonencode(local.engine_settings)` : le texte JSON des réglages. `jsonencode` transforme une valeur Terraform
    en texte JSON. Si vous passez `session_ttl_days` de 30 à 15, le texte change, donc l'appel est rejoué ;
  - `google_discovery_engine_search_engine.app.id` : l'identifiant de l'app. Si l'app est recréée, ses réglages
    sont perdus : il faut les réappliquer.

```hcl
  provisioner "local-exec" {
    command = <<-EOT
      curl -fsS -X PATCH \
        -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        -H "Content-Type: application/json" -H "X-Goog-User-Project: ${var.project_id}" \
        "https://${local.de_host}/v1/${google_discovery_engine_search_engine.app.name}?updateMask=${join(",", keys(local.engine_settings))}" \
        -d '${jsonencode(local.engine_settings)}' >/dev/null && echo "engine settings applied"
    EOT
  }
}
```

- **`provisioner "local-exec"`** : exécute une commande **sur la machine qui lance `terraform apply`** (votre poste
  ou la CI), une seule fois, à la création de la ressource.
- **`<<-EOT … EOT`** : un **heredoc**, c'est-à-dire un texte sur plusieurs lignes
  ([00-bases §12.3](00-bases-terraform.md#123-texte-sur-plusieurs-lignes--heredoc-)). Le `-` après `<<` retire
  l'indentation commune, pour que le code reste lisible.
- Les `\` en fin de ligne sont pour le **shell** : « la commande continue à la ligne suivante ».

Ligne par ligne :

| Morceau | Signification |
|---|---|
| `curl -fsS -X PATCH` | `curl` envoie une requête HTTP. `-X PATCH` = « modifier une partie » de la ressource. `-f` : échouer si Google renvoie une erreur (donc `apply` échoue aussi). `-s` : silencieux. `-S` : mais afficher les erreurs. |
| `-H "Authorization: Bearer $(gcloud auth print-access-token)"` | S'authentifier. `$(...)` est une syntaxe **du shell** (pas de Terraform) : elle exécute `gcloud auth print-access-token` et insère le jeton obtenu. Terraform ne touche qu'à `${...}`, il laisse `$(...)` intact. |
| `-H "Content-Type: application/json"` | Le corps de la requête est du JSON. |
| `-H "X-Goog-User-Project: ${var.project_id}"` | Le projet à qui facturer l'appel et décompter les quotas. Requis quand on appelle ces API avec un compte utilisateur. |
| `"https://${local.de_host}/v1/${…app.name}?updateMask=…"` | L'URL. `local.de_host` vaut `"eu-discoveryengine.googleapis.com"` (point d'accès régional, dans [`00_foundation.tf`](../00_foundation.tf)). `app.name` est le nom complet de l'app chez Google. |
| `?updateMask=${join(",", keys(local.engine_settings))}` | Le **masque de mise à jour** : la liste des champs à modifier. Sans lui, un PATCH pourrait remettre à zéro les autres champs de l'app. `keys(map)` donne la liste des clés ; `join(",", liste)` les colle avec des virgules. |
| `-d '${jsonencode(local.engine_settings)}'` | Le corps de la requête : les réglages en JSON, entre apostrophes pour le shell. |
| `>/dev/null` | Jeter la réponse de Google (longue et inutile ici). |
| `&& echo "engine settings applied"` | Si `curl` a réussi, afficher une confirmation dans la sortie de `apply`. |

**Exemple concret** avec `session_ttl_days = 30`, `enable_observability = true`, `enable_agent_gateway = false`,
`project_id = "acme-gemini-enterprise-prd"`, `app_id = "assistant-ia"` :

- `keys(local.engine_settings)` → `["observabilityConfig", "sessionConfig"]` (Terraform trie les clés par ordre
  alphabétique) ;
- `join(",", …)` → `"observabilityConfig,sessionConfig"` ;
- `jsonencode(…)` → `{"observabilityConfig":{"observabilityEnabled":true,"sensitiveLoggingEnabled":false},"sessionConfig":{"sessionTtl":{"days":30}}}`.

La commande réellement exécutée ressemble donc à ceci (le numéro de projet `123456789012` est un exemple ; le
format exact de `app.name`, numéro ou ID de projet, est à vérifier dans `terraform state show`) :

```bash
curl -fsS -X PATCH \
  -H "Authorization: Bearer ya29.xxxxx" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: acme-gemini-enterprise-prd" \
  "https://eu-discoveryengine.googleapis.com/v1/projects/123456789012/locations/eu/collections/default_collection/engines/assistant-ia?updateMask=observabilityConfig,sessionConfig" \
  -d '{"observabilityConfig":{"observabilityEnabled":true,"sensitiveLoggingEnabled":false},"sessionConfig":{"sessionTtl":{"days":30}}}' >/dev/null && echo "engine settings applied"
```

Avec `enable_agent_gateway = true`, le masque devient `agentGatewaySetting,observabilityConfig,sessionConfig` et le
JSON contient en plus la clé `agentGatewaySetting`.

**Pourquoi ce contournement, et ses limites.** C'est la seule façon d'appliquer ces réglages depuis le code tant que
le provider ne les gère pas. Mais Terraform ne sait **pas lire** leur valeur réelle :
- si quelqu'un change la durée de conservation dans la console, `terraform plan` ne le verra **pas** (pas de
  détection de dérive) ;
- supprimer ce bloc ne remet **pas** les réglages à leur valeur Google : il ne se passe rien chez Google ;
- la commande exige `curl` et `gcloud` (connecté) sur la machine qui lance `apply`.

Dès que le provider ajoutera ces arguments à `google_discovery_engine_search_engine`, il faudra les y déplacer et
supprimer ce bloc.

---

## 4. Ce que Terraform crée concrètement

Avec le `terraform.tfvars.example`, **3 ressources** :
1. **une app** Gemini Enterprise `assistant-ia`, en UE, chiffrée par la clé CMEK, avec les data stores des
   connecteurs et les 4 réglages de fonctionnalités ;
2. **un assistant** `default_assistant`, en français, branché sur les deux templates Model Armor en `FAIL_CLOSED`,
   sans recherche web et sans phrase interdite (liste vide) ;
3. **une ressource `terraform_data`**, qui ne crée rien chez Google mais lance une fois l'appel `curl` : conservation
   30 jours, observabilité sans contenu.

---

## 5. Dépendances avec les autres fichiers

| Ce fichier utilise… | …défini dans | Fiche |
|---|---|---|
| `var.ge_location`, `var.app_id`, `var.features`, `var.web_grounding`, `var.banned_phrases`, `var.session_ttl_days`… | [`variables.tf`](../variables.tf) | [02-variables.md](02-variables.md) |
| `local.project_number`, `local.de_host` | [`00_foundation.tf`](../00_foundation.tf) | [03-foundation.md](03-foundation.md) |
| `google_kms_crypto_key.ge`, `google_discovery_engine_cmek_config.ge` | [`20_data_protection.tf`](../20_data_protection.tf) | [05-data-protection.md](05-data-protection.md) |
| `google_model_armor_template.shield`, `google_project_iam_member.ge_uses_armor` | [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) | [06-ai-guardrails.md](06-ai-guardrails.md) |
| `local.connector_data_store_ids` | [`40_connectors.tf`](../40_connectors.tf) | [07-connectors.md](07-connectors.md) |
| `google_network_services_agent_gateway.egress` | [`60_advanced.tf`](../60_advanced.tf) | [09-advanced.md](09-advanced.md) |

Dans l'autre sens : [`70_detection.tf`](../70_detection.tf) surveille les modifications de l'assistant
([10-detection.md](10-detection.md)) et [`outputs.tf`](../outputs.tf) affiche `data_store_ids`
([11-outputs.md](11-outputs.md)).

---

## 6. Pour reproduire / adapter

**Besoin type : appliquer un réglage d'API que le provider Terraform ne supporte pas encore.**

```hcl
# 1. Le corps de la requête, avec les noms de champs de l'API REST (camelCase).
locals {
  mes_reglages = merge(
    { champToujoursPresent = { sousChamp = var.ma_valeur } },   # toujours envoyé
    var.mon_option ? { champOptionnel = { actif = true } } : {}, # ajouté seulement si l'option est vraie
  )
}

# 2. Une ressource "support" qui relance la commande quand les réglages changent.
resource "terraform_data" "mes_reglages" {
  triggers_replace = [
    jsonencode(local.mes_reglages),    # rejouer si le contenu change
    google_xxx.ma_ressource.id,        # rejouer si la ressource cible est recréée
  ]

  provisioner "local-exec" {
    command = <<-EOT
      curl -fsS -X PATCH \
        -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        -H "Content-Type: application/json" -H "X-Goog-User-Project: ${var.project_id}" \
        "https://<service>.googleapis.com/v1/${google_xxx.ma_ressource.name}?updateMask=${join(",", keys(local.mes_reglages))}" \
        -d '${jsonencode(local.mes_reglages)}' >/dev/null && echo "réglages appliqués"
    EOT
  }
}
```

1. **Vérifier d'abord** que l'argument n'existe vraiment pas dans le provider : page de la ressource, par exemple
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_search_engine
   (et https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_assistant).
   Si l'argument existe, utilisez-le : c'est toujours mieux.
2. Trouver dans la **référence REST** de l'API Google le nom exact des champs (camelCase) et le verbe (`PATCH`
   + `updateMask` pour une mise à jour partielle).
3. Tester l'appel `curl` **à la main** une fois, dans un terminal, avant de le mettre dans Terraform.
4. Mettre le corps dans un `locals`, la commande dans un `terraform_data` avec `triggers_replace`.
5. `terraform plan` doit montrer `terraform_data.mes_reglages` à créer ; après `apply`, vérifier le réglage dans la
   console ou avec un `curl` en `GET`.
6. Ajouter un commentaire « à supprimer quand le provider supportera X ».

---

## 7. Pièges et bonnes pratiques

- **Modifier `data_store_ids` peut recréer l'app** (bug connu du provider, README §16). Ajouter un connecteur ajoute
  un data store, donc change cette liste. Lisez le `plan` : si l'app est en `-/+` (détruite puis recréée), arrêtez.
  Idéalement, déclarez les connecteurs **avant** le lancement aux utilisateurs.
- **`location` et `engine_id` sont immuables** : les changer recrée l'app (conversations et réglages perdus).
- **`local-exec` exige `gcloud` et `curl`** sur la machine qui lance `apply`, et un `gcloud auth login` valide.
  Le jeton vient du compte **gcloud**, qui peut être différent du compte utilisé par Terraform (ADC,
  `gcloud auth application-default login`) : en CI, les deux doivent être configurés.
- **Pas de détection de dérive** sur les réglages envoyés par `curl` : une modification dans la console reste
  invisible pour Terraform. Pour forcer une réapplication : `terraform apply -replace=terraform_data.engine_settings`.
- **Si `curl` échoue, l'`apply` échoue** (grâce à `-f`) : lisez le message d'erreur HTTP (droit manquant, champ
  inconnu…). Si l'API renomme un champ, l'appel cassera : c'est voulu, mieux vaut une erreur qu'un réglage ignoré.
- **Apostrophes** : le JSON est entouré de `'…'` pour le shell. Une valeur contenant une apostrophe casserait la
  commande. Ici les valeurs sont des nombres et des booléens, donc sans risque.
- **`FAIL_CLOSED` + droit IAM manquant = tout est bloqué.** Juste après `apply`, attendez 1 à 2 minutes (propagation
  IAM) avant de conclure à une panne.
- **`banned_phrases` n'est pas un secret** : la liste est en clair dans le code et dans l'état Terraform. N'y mettez
  pas d'information plus sensible que le nom de code lui-même.
- Toute modification de l'assistant déclenche l'alerte « garde-fou modifié » ([10-detection.md](10-detection.md)) :
  c'est normal et voulu.
