# 13. `80_logging.tf` : journalisation de l'usage et de la sécurité

> Ce fichier décide **quels journaux on garde, où, combien de temps et qui peut les lire**. Il crée aussi une alerte
> sur les blocages Model Armor. Bases Terraform : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Gemini Enterprise produit plusieurs journaux : l'**audit** (qui a modifié quoi), l'**usage** (qui a demandé quoi,
quelles sources, quelles réponses ont été bloquées) et, en option, le **texte complet** des questions et réponses.
Par défaut, Google les range tous dans le bucket `_Default` du projet, lisible par beaucoup de monde et conservé
30 jours.

Ce fichier **range** chaque famille dans un **bucket dédié en UE**, avec une **durée de conservation par finalité**.
Il **retire** les contenus sensibles du bucket par défaut, **réserve** la lecture à l'équipe sécurité et **alerte**
en cas de pic de blocages, sans journaliser le contenu filtré. Le guide explique le pourquoi au
[§10.4 du README](../../docs/00-socle-securite.md#104-les-journaux-disponibles--ce-quon-capture-où-combien-de-temps).

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `locals` (filtres) | locals | Écrit une fois les 3 filtres de journaux réutilisés plus bas |
| `google_logging_project_bucket_config.security` | resource | Bucket « sécurité » en UE, 365 jours, interrogeable en SQL |
| `google_logging_project_bucket_config.usage` | resource | Bucket « usage » en UE, 90 jours, interrogeable en SQL |
| `google_logging_project_sink.security` | resource | Envoie l'audit et les décisions Model Armor vers le bucket sécurité |
| `google_logging_project_sink.usage` | resource | Envoie l'activité des utilisateurs vers le bucket usage |
| `google_logging_project_exclusion.sensitive_from_default` | resource | Retire les contenus sensibles du bucket `_Default` |
| `locals` (`log_buckets`) | locals | Petit annuaire des deux buckets |
| `google_logging_log_view_iam_member.security_reads` | resource | Donne la lecture des deux buckets à l'équipe sécurité, et à elle seule |
| `google_logging_linked_dataset.usage` | resource (optionnelle) | Expose le bucket usage dans BigQuery, sans copie |
| `google_logging_metric.policy_violations` | resource | Compte les réponses bloquées par la politique |
| `google_monitoring_alert_policy.policy_violations` | resource | Alerte si plus de 20 blocages en 10 minutes |

Les **notions Cloud Logging** à connaître :

| Notion | Explication simple |
|---|---|
| **Journal (log)** | Une suite d'entrées horodatées ; chaque entrée a un `logName` (son « nom de famille ») |
| **Bucket de logs** | Un **lieu de stockage** de journaux, avec une localisation et une durée de conservation. Chaque projet a `_Required` (audit d'administration, 400 jours, non modifiable) et `_Default` (le reste, 30 jours) |
| **Sink (routeur)** | Une **règle d'aiguillage** : « les entrées qui correspondent à ce filtre vont aussi vers cette destination » |
| **Exclusion** | Une règle qui **empêche** certaines entrées d'être stockées dans `_Default` |
| **Vue (log view)** | Une « fenêtre » sur un bucket. Chaque bucket a la vue `_AllLogs`. On donne les droits **sur une vue** |
| **Log Analytics** | Permet d'interroger un bucket **en SQL**, directement dans la console |
| **Métrique de logs** | Un compteur alimenté par les entrées qui correspondent à un filtre ; on peut alerter dessus |

---

## 3. Le code expliqué, bloc par bloc

### 3.1 Les filtres réutilisables (`locals`)

```hcl
locals {
  usage_log_filter = <<-EOT
    logName="projects/${var.project_id}/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity"
    OR logName=~"projects/${var.project_id}/logs/discoveryengine.googleapis.com%2Fgen_ai\."
  EOT
```

- `<<-EOT … EOT` : un texte sur plusieurs lignes, un « heredoc » (voir [00-bases §12.3](00-bases-terraform.md#123-texte-sur-plusieurs-lignes-heredoc)).
- **Syntaxe des filtres Cloud Logging :**
  - `logName="…"` : égalité exacte.
  - `logName=~"…"` : **expression régulière** (« contient ce motif »).
  - `OR` / `AND` combinent les conditions ; deux conditions sur deux lignes sans opérateur valent `AND`.
- `%2F` est le caractère `/` encodé : le vrai nom est `discoveryengine.googleapis.com/gemini_enterprise_user_activity`.
- Le filtre capte le **journal d'usage** et tous les journaux `gen_ai.*` (texte des prompts `gen_ai.user.message` et
  des réponses `gen_ai.choice`, produits seulement si `log_prompts_responses = true`). `\.` désigne un point littéral
  dans l'expression régulière.
- Avec `project_id = "acme-gemini-enterprise-prd"`, la 1re ligne devient
  `logName="projects/acme-gemini-enterprise-prd/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity"`.

```hcl
  armor_content_filter = "jsonPayload.@type=\"type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry\""
```

- Le filtre des **décisions Model Armor avec contenu** (produites seulement si `log_screened_content = true`).
- `\"` : un guillemet **à l'intérieur** d'une chaîne Terraform. Le filtre réel est
  `jsonPayload.@type="type.googleapis.com/…SanitizeOperationLogEntry"`.

```hcl
  security_log_filter = <<-EOT
    (logName:"cloudaudit.googleapis.com" AND protoPayload.serviceName=("discoveryengine.googleapis.com" OR "modelarmor.googleapis.com" OR "cloudkms.googleapis.com" OR "secretmanager.googleapis.com" OR "dlp.googleapis.com" OR "cloudresourcemanager.googleapis.com" OR "iam.googleapis.com"))
    OR ${local.armor_content_filter}
  EOT
}
```

- `logName:"cloudaudit.googleapis.com"` : `:` signifie « **contient** ». On prend donc tous les journaux d'audit
  (administration **et** accès aux données).
- `protoPayload.serviceName=("a" OR "b" …)` : uniquement les services du socle (Gemini Enterprise, Model Armor, KMS,
  Secret Manager, DLP, droits du projet, IAM).
- `OR ${local.armor_content_filter}` : on **réutilise** le filtre précédent. Un `local` peut en utiliser un autre.

### 3.2 Les deux buckets

```hcl
resource "google_logging_project_bucket_config" "security" {
  project          = var.project_id
  location         = var.ge_location
  bucket_id        = "ge-security"
  description      = "Gemini Enterprise : audit et décisions Model Armor."
  retention_days   = var.security_log_retention_days
  locked           = var.lock_security_logs
  enable_analytics = true
}
```

| Argument | Rôle | Pourquoi |
|---|---|---|
| `location = var.ge_location` | `eu` : journaux stockés dans l'UE | Même résidence que les données de l'app |
| `bucket_id = "ge-security"` | Nom du bucket | Nom parlant, utilisé dans Logs Explorer |
| `retention_days` | 365 par défaut | Preuve d'audit et enquête sur un an (à valider avec le DPO) |
| `locked` | `false` par défaut | `true` = **personne** ne peut réduire la rétention ni supprimer le bucket. Intégrité des preuves en production. **Irréversible** |
| `enable_analytics = true` | Active Log Analytics (SQL) | Enquêter sans copier les logs ailleurs. **Ne peut plus être désactivé** |

```hcl
resource "google_logging_project_bucket_config" "usage" {
  project          = var.project_id
  location         = var.ge_location
  bucket_id        = "ge-usage"
  description      = "Gemini Enterprise : activité des utilisateurs (peut contenir des questions)."
  retention_days   = var.usage_log_retention_days
  enable_analytics = true
}
```

- Même principe, **90 jours** (minimisation RGPD : ces journaux contiennent des questions de collaborateurs).
- Pas de `locked` : on doit pouvoir **réduire** la durée si le DPO le demande.

### 3.3 Les sinks (aiguillages)

```hcl
resource "google_logging_project_sink" "security" {
  name        = "ge-security-logs"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.security.id}"
  filter      = local.security_log_filter
}
```

- `destination` : vers où envoyer. Pour un bucket de logs, le format est `logging.googleapis.com/<id du bucket>`.
  L'`id` du bucket (`projects/…/locations/eu/buckets/ge-security`) vient de la ressource créée juste au-dessus. Cette
  **référence** crée aussi la dépendance : bucket d'abord, sink ensuite (voir [00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on)).
- `filter` : seules les entrées qui correspondent sont envoyées.
- Un sink **copie** : les journaux d'audit d'administration restent aussi dans `_Required` (règle Google).

```hcl
resource "google_logging_project_sink" "usage" {
  name        = "ge-usage-logs"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.usage.id}"
  filter      = local.usage_log_filter
}
```

Même principe pour l'usage.

### 3.4 L'exclusion du bucket par défaut

```hcl
resource "google_logging_project_exclusion" "sensitive_from_default" {
  name        = "ge-sensitive-content"
  description = "Questions/réponses Gemini Enterprise et contenus Model Armor : uniquement dans les buckets dédiés."
  filter      = "(${trimspace(local.usage_log_filter)}) OR ${local.armor_content_filter}"
}
```

- Une **exclusion de projet** empêche les entrées correspondantes d'être stockées dans `_Default`. Les **sinks**
  dédiés les reçoivent quand même : elles ne vont **que** dans les buckets protégés.
- `trimspace(...)` retire les espaces et retours à la ligne en début et en fin du heredoc avant de l'entourer de
  parenthèses.
- **Pourquoi :** `_Default` est lisible par de nombreux rôles (`logging.viewer`, `owner`, `editor`…). Les questions
  des collaborateurs ne doivent pas y traîner.

### 3.5 Qui peut lire

```hcl
locals {
  log_buckets = {
    security = google_logging_project_bucket_config.security.bucket_id
    usage    = google_logging_project_bucket_config.usage.bucket_id
  }
}
```

Un petit annuaire `nom court → bucket_id`, utilisé dans la boucle suivante et dans [`outputs.tf`](../outputs.tf).

```hcl
resource "google_logging_log_view_iam_member" "security_reads" {
  for_each = { for pair in setproduct(keys(local.log_buckets), var.security_groups) : "${pair[0]}|${pair[1]}" => pair }
  parent   = "projects/${var.project_id}"
  location = var.ge_location
  bucket   = local.log_buckets[each.value[0]]
  name     = "_AllLogs"
  role     = "roles/logging.viewAccessor"
  member   = each.value[1]
}
```

- `setproduct(keys(local.log_buckets), var.security_groups)` forme **toutes les combinaisons** bucket × groupe
  (voir [00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)). Avec
  `security_groups = ["group:securite-ia@acme.example"]`, cela donne :
  ```
  [["security", "group:securite-ia@acme.example"], ["usage", "group:securite-ia@acme.example"]]
  ```
- La boucle `for` transforme cette liste en map à clés stables, ce que `for_each` exige :
  ```
  {
    "security|group:securite-ia@acme.example" = ["security", "group:securite-ia@acme.example"]
    "usage|group:securite-ia@acme.example"    = ["usage", "group:securite-ia@acme.example"]
  }
  ```
- `each.value[0]` = `"security"` ou `"usage"` ; `local.log_buckets[...]` donne le vrai `bucket_id`.
- `name = "_AllLogs"` : la vue créée automatiquement avec chaque bucket.
- `roles/logging.viewAccessor` sur **cette vue** : lire **ce bucket** uniquement, sans aucun autre droit sur
  le projet. C'est le moindre privilège.

### 3.6 Option : lien BigQuery

```hcl
resource "google_logging_linked_dataset" "usage" {
  count       = var.link_logs_to_bigquery ? 1 : 0
  link_id     = "ge_usage_logs"
  parent      = "projects/${var.project_id}"
  location    = var.ge_location
  bucket      = google_logging_project_bucket_config.usage.bucket_id
  description = "Lecture SQL des journaux d'usage Gemini Enterprise."
}
```

- `count = condition ? 1 : 0` : la ressource n'existe que si l'option est activée (voir [00-bases §8.1](00-bases-terraform.md#81-count--0-ou-n-exemplaires-souvent-pour-optionnel)).
- Un **dataset lié** fait apparaître le bucket dans BigQuery, **en lecture seule et sans copie**, ce qui permet de
  brancher Looker Studio. Il exige `enable_analytics = true` sur le bucket (c'est le cas).
- Les droits BigQuery sur ce dataset sont à donner **explicitement** et avec parcimonie.

### 3.7 L'alerte sur les blocages

```hcl
resource "google_logging_metric" "policy_violations" {
  name   = "ge_policy_violations"
  filter = "logName=\"projects/${var.project_id}/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity\" AND \"CUSTOMER_POLICY_VIOLATION\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.apis]
}
```

- Une **métrique de logs** compte les entrées qui correspondent au filtre.
- `"CUSTOMER_POLICY_VIOLATION"` **seul, entre guillemets**, est une **recherche plein texte** : l'entrée doit contenir
  ce mot n'importe où. Quand Model Armor (ou une phrase interdite) bloque une réponse, Gemini Enterprise l'indique avec
  ce motif dans le journal d'usage.
- `DELTA` + `INT64` : un **compteur** d'événements (combien pendant chaque intervalle).
- **L'intérêt :** on détecte les attaques **sans** activer la journalisation du contenu Model Armor
  (`log_screened_content`), que Google déconseille.

```hcl
resource "google_monitoring_alert_policy" "policy_violations" {
  display_name = "Gemini Enterprise : pic de requêtes bloquées par la politique"
  combiner     = "OR"
  conditions {
    display_name = "Plus de 20 blocages en 10 minutes"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.policy_violations.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 20
      duration        = "0s"
      aggregations {
        alignment_period     = "600s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  notification_channels = google_monitoring_notification_channel.security[*].id
  documentation {
    mime_type = "text/markdown"
    content   = "Pic de requêtes bloquées (Model Armor / politique). Enquête : bucket ge-usage, filtre \"CUSTOMER_POLICY_VIOLATION\", regrouper par utilisateur. Voir guide §10.5."
  }
}
```

- `metric.type="logging.googleapis.com/user/ge_policy_violations"` : les métriques de logs créées par vous sont
  publiées sous `logging.googleapis.com/user/<nom>`.
- `aggregations` : on **additionne** (`ALIGN_SUM`) les blocages sur des fenêtres de **10 minutes** (`600s`), tous
  utilisateurs confondus (`REDUCE_SUM`).
- `comparison = "COMPARISON_GT"` + `threshold_value = 20` : alerte si **plus de 20**. `duration = "0s"` : dès la
  première fenêtre au-dessus du seuil.
- `google_monitoring_notification_channel.security[*].id` : l'expression `[*]` (« splat ») prend l'`id` de **tous**
  les exemplaires. Le canal e-mail est défini dans [`70_detection.tf`](../70_detection.tf) avec `count` : liste vide si
  `alert_email` est vide (l'alerte existe alors sans e-mail).
- `documentation` : le texte affiché dans l'alerte, c'est-à-dire la marche à suivre.

---

## 4. Ce que Terraform crée concrètement

Avec l'exemple `terraform.tfvars.example` (un groupe sécurité, options par défaut) :

| Ressource | Nombre |
|---|---|
| Buckets de logs (`ge-security`, `ge-usage`) | 2 |
| Sinks | 2 |
| Exclusion | 1 |
| Droits de lecture (2 buckets × 1 groupe) | 2 |
| Dataset BigQuery lié | 0 (option désactivée) |
| Métrique + alerte | 2 |
| **Total** | **9** |

Dans la console : *Logging → Stockage des journaux* montre les deux buckets. *Logging → Routeur de journaux* montre
les sinks et l'exclusion. *Monitoring → Alertes* montre l'alerte.

---

## 5. Dépendances avec les autres fichiers

| Vient d'ailleurs | Fichier |
|---|---|
| `var.project_id`, `var.ge_location`, `var.security_groups`, `var.security_log_retention_days`, `var.usage_log_retention_days`, `var.lock_security_logs`, `var.link_logs_to_bigquery` | [`variables.tf`](../variables.tf) ([02-variables.md](02-variables.md)) |
| `google_project_service.apis` (API Logging et Monitoring) | [`00_foundation.tf`](../00_foundation.tf) ([03-foundation.md](03-foundation.md)) |
| `google_monitoring_notification_channel.security` (e-mail) | [`70_detection.tf`](../70_detection.tf) ([10-detection.md](10-detection.md)) |
| **Production des journaux d'usage** : observabilité activée par `engine_settings` (`enable_observability`, `log_prompts_responses`) | [`50_app.tf`](../50_app.tf) ([08-app.md](08-app.md)) |
| **Production des journaux d'accès aux données** : `google_project_iam_audit_config` | [`70_detection.tf`](../70_detection.tf) |
| **Production des contenus Model Armor** : `log_sanitize_operations = var.log_screened_content` | [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) ([06-ai-guardrails.md](06-ai-guardrails.md)) |

| Utilisé ailleurs | Fichier |
|---|---|
| `local.log_buckets` → sortie `log_buckets` | [`outputs.tf`](../outputs.tf) ([11-outputs.md](11-outputs.md)) |

> À retenir : **ce fichier range les journaux, il ne les crée pas.** Ce sont les réglages des autres fichiers qui
> décident s'ils existent.

---

## 6. Pour reproduire / adapter

**Modèle : isoler un type de journal sensible dans un bucket dédié, lisible par un seul groupe.**

```hcl
# 1. Le bucket (localisation, durée, SQL)
resource "google_logging_project_bucket_config" "mon_bucket" {
  project          = var.project_id
  location         = "eu"
  bucket_id        = "mon-bucket"
  retention_days   = 90
  enable_analytics = true
}

# 2. L'aiguillage : quelles entrées y vont
resource "google_logging_project_sink" "mon_sink" {
  name        = "mon-sink"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.mon_bucket.id}"
  filter      = "logName=\"projects/${var.project_id}/logs/MON_JOURNAL\""   # tester le filtre dans Logs Explorer d'abord
}

# 3. Les retirer du bucket par défaut (si sensibles)
resource "google_logging_project_exclusion" "mon_exclusion" {
  name   = "mon-exclusion"
  filter = "logName=\"projects/${var.project_id}/logs/MON_JOURNAL\""
}

# 4. Qui peut lire (sur la vue du bucket uniquement)
resource "google_logging_log_view_iam_member" "lecteurs" {
  parent   = "projects/${var.project_id}"
  location = "eu"
  bucket   = google_logging_project_bucket_config.mon_bucket.bucket_id
  name     = "_AllLogs"
  role     = "roles/logging.viewAccessor"
  member   = "group:mon-equipe@entreprise.com"
}

# 5. (option) Compter et alerter
resource "google_logging_metric" "mon_compteur" {
  name   = "mon_compteur"
  filter = "logName=\"projects/${var.project_id}/logs/MON_JOURNAL\" AND \"MOT_CLE\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}
```

Étapes :
1. **Trouver le journal** dans *Logs Explorer* et noter son `logName`.
2. **Écrire et tester le filtre** dans Logs Explorer avant de le mettre dans Terraform.
3. Choisir **localisation** et **durée** avec le DPO (finalité → durée).
4. Ajouter bucket, sink, exclusion et droit de lecture (modèle ci-dessus).
5. `terraform plan`, puis `apply`. Vérifier dans *Routeur de journaux* que le sink reçoit des entrées.

Documentation des ressources :
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_project_bucket_config
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_project_sink
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_project_exclusion
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_log_view_iam
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_linked_dataset
- https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_metric

---

## 7. Pièges et bonnes pratiques

- **Ce fichier ne produit aucun journal** : sans `enable_observability = true` (ou avec `false`), le bucket `ge-usage`
  reste vide. Vérifiez la production avant de conclure qu'« il n'y a rien ».
- **`enable_analytics` et `locked` sont à sens unique** : on ne peut pas désactiver Log Analytics, ni déverrouiller un
  bucket. Activez `lock_security_logs` seulement en production, une fois la durée validée.
- **La rétention a un coût** : au-delà de 30 jours, le stockage des logs est facturé. Les journaux d'usage peuvent être
  volumineux, encore plus avec `log_prompts_responses = true`.
- **Testez l'exclusion** : après un premier usage, cherchez `gemini_enterprise_user_activity` dans le bucket `_Default`.
  Vous ne devez **rien** trouver.
- **Les noms de champs** (`skipped_reasons`, `authentication_info`…) sont **à confirmer** sur les premières entrées
  réelles. La recherche plein texte (`"CUSTOMER_POLICY_VIOLATION"`) fonctionne quelle que soit la structure. Si un
  blocage de recette n'incrémente pas la métrique, activez temporairement `log_screened_content` pour diagnostiquer.
- **RGPD** : ces journaux sont des **données personnelles de salariés**. Il faut une finalité écrite, l'information
  des collaborateurs, le registre des traitements et, si besoin, la consultation du CSE. **Ne jamais** élargir les
  lecteurs sans décision.
- **Ne donnez pas `roles/logging.viewer` à large échelle** en pensant protéger les questions : c'est justement pour
  cela que l'exclusion existe. Gardez les contenus hors de `_Default`.
- **Plusieurs projets ?** En entreprise, on centralise souvent les journaux de sécurité dans un **projet de
  journalisation** dédié, via un sink au niveau dossier ou organisation. Le même modèle s'applique, avec une
  destination dans l'autre projet.
