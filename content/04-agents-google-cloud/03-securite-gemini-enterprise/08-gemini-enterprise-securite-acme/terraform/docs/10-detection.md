# 10. `70_detection.tf` : journaux d'audit et alertes de sécurité

> Active les journaux d'audit utiles, crée un canal d'alerte e-mail et déclenche une alerte dès qu'un garde-fou est
> modifié. Bases Terraform : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Protéger ne suffit pas : il faut **voir** quand quelqu'un touche aux protections. Ce fichier active les journaux
d'accès aux données (désactivés par défaut chez Google) pour trois services sensibles. Il crée ensuite une
**métrique** qui compte les modifications de garde-fous dans les journaux, et une **alerte** qui envoie un e-mail à
l'équipe sécurité dès que ce compteur dépasse zéro. Une seconde alerte optionnelle surveille les pics de requêtes
bloquées par Model Armor.

---

## 2. Vue d'ensemble

| Bloc (adresse) | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_project_iam_audit_config.audit` | `resource` (`for_each`, 3) | Active les journaux « Data Access » (lecture et écriture) de 3 services. |
| `google_monitoring_notification_channel.security` | `resource` (0 ou 1) | Le canal e-mail de l'équipe sécurité. |
| `google_logging_metric.security_changes` | `resource` | Compte les entrées de journal qui modifient un garde-fou. |
| `google_monitoring_alert_policy.security_changes` | `resource` | Alerte dès que ce compteur dépasse 0 en 5 minutes. |
| `google_logging_metric.armor_matches` | `resource` (0 ou 1) | Compte les blocages Model Armor (seulement si le contenu est journalisé). |
| `google_monitoring_alert_policy.armor_spike` | `resource` (0 ou 1) | Alerte si plus de 20 blocages en 10 minutes. |

---

## 3. Le code expliqué, bloc par bloc

**Vocabulaire.**
- **Cloud Logging** : le service qui stocke les journaux (logs) de Google Cloud.
- **Journaux d'audit** (*audit logs*) : qui a fait quoi, quand. Deux familles utiles ici :
  - **Admin Activity** (activité d'administration) : les modifications de configuration. **Toujours actifs**,
    gratuits, sans contenu utilisateur ;
  - **Data Access** (accès aux données) : les lectures et écritures de données. **Désactivés par défaut**, il faut les
    activer service par service.
- **Cloud Monitoring** : le service des métriques et des alertes.
- **Métrique basée sur les journaux** (*log-based metric*) : un compteur qui augmente de 1 à chaque entrée de journal
  correspondant à un filtre.

### 3.1 Les journaux d'audit : `google_project_iam_audit_config.audit`

```hcl
resource "google_project_iam_audit_config" "audit" {
  for_each = toset(["discoveryengine.googleapis.com", "modelarmor.googleapis.com", "secretmanager.googleapis.com"])
  project  = var.project_id
  service  = each.value
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}
```

- **`for_each = toset([...])`** : crée **un exemplaire par élément** de la liste
  ([00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set)).
  `toset` transforme la liste en ensemble (obligatoire : `for_each` n'accepte pas une liste simple). On obtient 3
  ressources, d'adresses :
  - `google_project_iam_audit_config.audit["discoveryengine.googleapis.com"]` (Gemini Enterprise : qui utilise
    l'app) ;
  - `google_project_iam_audit_config.audit["modelarmor.googleapis.com"]` (les appels de filtrage) ;
  - `google_project_iam_audit_config.audit["secretmanager.googleapis.com"]` (**chaque lecture** d'un secret de
    connecteur).
- `project = var.project_id` : le projet concerné.
- `service = each.value` : le service en cours (`each.value` = l'élément de l'ensemble).
- Deux sous-blocs **`audit_log_config`** : on active `DATA_READ` (lectures) **et** `DATA_WRITE` (écritures). Le bloc
  est simplement écrit deux fois : quand le nombre de blocs est fixe, pas besoin de `dynamic`.

**Pourquoi pas Cloud KMS ?** (commentaire du fichier et guide du socle (docs/00) §10.1) : chaque déchiffrement serait journalisé, soit
des millions de lignes sans valeur. Les opérations importantes sur les clés (désactivation, destruction) sont déjà
dans les journaux **Admin Activity**, toujours actifs.

### 3.2 Le canal d'alerte : `google_monitoring_notification_channel.security`

```hcl
resource "google_monitoring_notification_channel" "security" {
  count        = var.alert_email == "" ? 0 : 1
  display_name = "Équipe sécurité IA"
  type         = "email"
  labels       = { email_address = var.alert_email }
}
```

- **`count = var.alert_email == "" ? 0 : 1`** : pas d'adresse → pas de canal
  ([00-bases §8.1](00-bases-terraform.md#81-count--0-ou-n-exemplaires-souvent-pour-optionnel)). Avec le
  `terraform.tfvars.example`, `alert_email = "securite-ia@acme.example"`, donc **1** canal.
- `display_name` : le nom affiché dans Cloud Monitoring.
- `type = "email"` : un canal de type e-mail (il existe aussi SMS, Slack, PagerDuty…).
- `labels = { email_address = var.alert_email }` : les paramètres du canal. Pour un e-mail, un seul : l'adresse.

### 3.3 La métrique « garde-fou modifié » : `google_logging_metric.security_changes`

```hcl
resource "google_logging_metric" "security_changes" {
  name   = "ge_security_config_changes"
  filter = <<-EOT
    logName:"cloudaudit.googleapis.com%2Factivity"
    (
      (protoPayload.serviceName="modelarmor.googleapis.com" AND protoPayload.methodName=~"(UpdateTemplate|DeleteTemplate|UpdateFloorSetting)")
      OR (protoPayload.serviceName="cloudkms.googleapis.com" AND protoPayload.methodName=~"(DestroyCryptoKeyVersion|UpdateCryptoKeyVersion|UpdateCryptoKeyPrimaryVersion)")
      OR (protoPayload.serviceName="discoveryengine.googleapis.com" AND protoPayload.methodName=~"(UpdateAssistant|DeleteEngine|UpdateAclConfig|CmekConfig)")
      OR (protoPayload.methodName=~"SetIamPolicy" AND protoPayload.serviceName=("cloudresourcemanager.googleapis.com" OR "cloudkms.googleapis.com" OR "secretmanager.googleapis.com"))
    )
  EOT
```

- `name = "ge_security_config_changes"` : le nom de la métrique. Cloud Monitoring la publiera sous le type
  `logging.googleapis.com/user/ge_security_config_changes` (le préfixe `user/` signale une métrique créée par vous).
- `filter = <<-EOT … EOT` : le filtre, écrit sur plusieurs lignes grâce à un **heredoc**
  ([00-bases §12.3](00-bases-terraform.md#123-texte-sur-plusieurs-lignes-heredoc)). Attention : ce texte n'est
  **pas** du Terraform, c'est le **langage de requête de Cloud Logging** (le même que dans Logs Explorer).

**Le filtre, ligne par ligne :**

| Ligne | Signification |
|---|---|
| `logName:"cloudaudit.googleapis.com%2Factivity"` | Ne garder que les journaux **Admin Activity**. `logName` vaut par exemple `projects/mon-projet/logs/cloudaudit.googleapis.com%2Factivity`. L'opérateur **`:`** veut dire « contient » (pas « égal »), donc pas besoin d'écrire le début. `%2F` est le caractère `/` encodé, tel qu'il apparaît dans le nom du journal. |
| *(passage à la ligne)* | Deux conditions écrites l'une après l'autre sont reliées par un **ET implicite**. L'entrée doit donc être un journal d'activité **ET** satisfaire le bloc entre parenthèses. |
| `(` … `)` | Regroupe quatre cas reliés par `OR` (OU) : il suffit qu'un seul soit vrai. |
| `protoPayload.serviceName="modelarmor.googleapis.com"` | `protoPayload` est le contenu de l'entrée d'audit. `serviceName` = le service appelé. `=` = égal exactement. |
| `AND protoPayload.methodName=~"(UpdateTemplate\|DeleteTemplate\|UpdateFloorSetting)"` | `methodName` = l'opération appelée. **`=~`** = « correspond à l'**expression régulière** ». `(A\|B\|C)` = A **ou** B **ou** C. Cas 1 : un template Model Armor modifié ou supprimé, ou le plancher modifié. |
| `OR (… "cloudkms.googleapis.com" AND … "(DestroyCryptoKeyVersion\|UpdateCryptoKeyVersion\|UpdateCryptoKeyPrimaryVersion)")` | Cas 2 : une version de clé KMS détruite, modifiée (par exemple désactivée) ou une autre version rendue primaire. |
| `OR (… "discoveryengine.googleapis.com" AND … "(UpdateAssistant\|DeleteEngine\|UpdateAclConfig\|CmekConfig)")` | Cas 3 : l'assistant modifié, l'app supprimée, la configuration d'identité modifiée, ou toute opération dont le nom contient `CmekConfig`. |
| `OR (protoPayload.methodName=~"SetIamPolicy" AND protoPayload.serviceName=("…resourcemanager…" OR "…kms…" OR "…secretmanager…"))` | Cas 4 : un **droit IAM** modifié (`SetIamPolicy`) sur le projet, une clé ou un secret. `=~` (expression régulière) attrape aussi les noms longs comme `google.iam.v1.IAMPolicy.SetIamPolicy`. `serviceName=("a" OR "b")` est un raccourci pour `serviceName="a" OR serviceName="b"`. |

Une expression régulière sans `^` ni `$` cherche le motif **n'importe où** dans le texte. Comme les noms de méthode
réels sont souvent longs (par exemple `google.cloud.discoveryengine.v1.AssistantService.UpdateAssistant`),
`=~"UpdateAssistant"` les trouve quand même.

```hcl
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.apis]
}
```

- `metric_descriptor` : la forme de la métrique.
  - `metric_kind = "DELTA"` : chaque point mesure « combien **pendant** l'intervalle » (et non un total cumulé).
  - `value_type = "INT64"` : un nombre entier. Ici : le nombre d'entrées de journal correspondantes.
- `depends_on = [google_project_service.apis]` : attendre que les API Logging et Monitoring soient activées
  ([`00_foundation.tf`](../00_foundation.tf)).

### 3.4 L'alerte : `google_monitoring_alert_policy.security_changes`

```hcl
resource "google_monitoring_alert_policy" "security_changes" {
  display_name = "Gemini Enterprise : modification d'un garde-fou de sécurité"
  combiner     = "OR"
  conditions {
    display_name = "Au moins une modification en 5 minutes"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.security_changes.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
```

- `display_name` : le titre de l'alerte (objet de l'e-mail).
- `combiner = "OR"` : comment combiner plusieurs conditions. Il n'y en a qu'une, donc `OR` ou `AND` revient au même ;
  l'argument est obligatoire.
- `conditions { … }` : la condition qui déclenche l'alerte.
  - **`condition_threshold`** : une condition à **seuil** (« si la valeur dépasse X »).
  - `filter` : quelle métrique surveiller. Les `\"` sont des guillemets **échappés** : ils font partie du texte, au
    lieu de fermer la chaîne Terraform. Le résultat est :
    `metric.type="logging.googleapis.com/user/ge_security_config_changes"`. Utiliser `.name` (et non écrire le nom
    en dur) crée une dépendance : Terraform crée la métrique **avant** l'alerte.
  - `comparison = "COMPARISON_GT"` : « strictement supérieur à » (GT = *greater than*).
  - `threshold_value = 0` : le seuil. Donc : **dès qu'il y a au moins 1 modification**.
  - `duration = "0s"` : pendant combien de temps la condition doit rester vraie avant d'alerter. `0s` = tout de
    suite.

```hcl
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
```

**Les agrégations, simplement.** Une métrique peut produire plusieurs « séries » (une par combinaison d'étiquettes,
par exemple une par ressource). Monitoring les ramène à un seul chiffre en deux étapes :
1. `alignment_period = "300s"` + `per_series_aligner = "ALIGN_SUM"` : dans **chaque** série, on découpe le temps en
   tranches de 5 minutes et on **additionne** les points de chaque tranche ;
2. `cross_series_reducer = "REDUCE_SUM"` : on **additionne toutes les séries** entre elles.

Résultat : « nombre total de modifications de garde-fous sur les 5 dernières minutes ». Exemple : 2 changements
de template et 1 changement IAM en 5 minutes → 3, et 3 > 0 → alerte.

```hcl
  notification_channels = google_monitoring_notification_channel.security[*].id
  documentation {
    mime_type = "text/markdown"
    content   = "Un garde-fou (Model Armor, clé KMS, droits, assistant) a été modifié. Vérifier qu'il s'agit d'un changement validé (PR Terraform). Sinon : procédure d'incident du guide."
  }
}
```

- **`notification_channels = google_monitoring_notification_channel.security[*].id`** : l'expression **splat**
  `[*]`. Elle signifie « l'attribut `id` de **tous** les exemplaires », sous forme de liste. C'est la façon propre de
  lire une ressource créée avec `count` sans savoir s'il y en a 0 ou 1 :
  - avec `alert_email = "securite-ia@acme.example"` (1 canal) →
    `["projects/acme-gemini-enterprise-prd/notificationChannels/1234567890"]` (numéro d'exemple) ;
  - avec `alert_email = ""` (0 canal) → `[]` : l'alerte existe mais **n'envoie rien** (visible seulement dans la
    console).

  `[*].id` équivaut à `[for c in google_monitoring_notification_channel.security : c.id]`
  ([00-bases §12.2](00-bases-terraform.md#122-boucles-for-transformer-une-liste-ou-une-map)). Écrire
  `security[0].id` planterait quand il n'y a pas de canal.
- `documentation` : le texte joint à l'alerte, en Markdown. Il dit au destinataire **quoi faire** (guide du socle (docs/00) §10.3).

### 3.5 Option : pic de blocages Model Armor

Ces deux ressources n'existent que si `var.log_screened_content = true`, c'est-à-dire si Model Armor journalise le
**contenu** filtré. Défaut : `false`, car Google le déconseille pour Gemini Enterprise (les questions des
utilisateurs deviendraient lisibles dans les journaux). Sans ces journaux, il n'y a rien à compter.

```hcl
resource "google_logging_metric" "armor_matches" {
  count  = var.log_screened_content ? 1 : 0
  name   = "ge_model_armor_matches"
  filter = <<-EOT
    jsonPayload.@type="type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry"
    jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}
```

- `count = var.log_screened_content ? 1 : 0` : 1 si l'option est activée, 0 sinon.
- Le filtre, ligne par ligne :
  - `jsonPayload.@type="…SanitizeOperationLogEntry"` : ne garder que les journaux d'**opérations de filtrage** Model
    Armor (`jsonPayload` = le contenu d'un journal structuré ; `@type` = son type) ;
  - `jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"` : et seulement celles où **un filtre a trouvé
    quelque chose** (= requête ou réponse bloquée ou signalée).
  - Les deux lignes sont reliées par un **ET implicite**.
- `metric_descriptor` : comme en 3.3.

```hcl
resource "google_monitoring_alert_policy" "armor_spike" {
  count        = var.log_screened_content ? 1 : 0
  display_name = "Gemini Enterprise : pic de requêtes bloquées"
  combiner     = "OR"
  conditions {
    display_name = "Plus de 20 blocages en 10 minutes"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.armor_matches[0].name}\""
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
}
```

- Même structure que 3.4, avec trois différences :
  - même `count` que la métrique : l'une ne va pas sans l'autre ;
  - `armor_matches[0].name` : `[0]` car la métrique est créée avec `count`. Ici on **peut** écrire `[0]`, parce que
    l'alerte n'existe que si la métrique existe (même condition) ;
  - seuil `20` sur `600s` (10 minutes) : quelques blocages isolés sont normaux ; plus de 20 en 10 minutes ressemble à
    une **attaque** (tentatives répétées d'injection de prompt) ou à un filtre mal réglé.

---

## 4. Ce que Terraform crée concrètement

Avec le `terraform.tfvars.example` (`alert_email` renseigné, `log_screened_content` absent donc `false`) :
**6 ressources**
- 3 configurations d'audit (Gemini Enterprise, Model Armor, Secret Manager : lectures et écritures journalisées) ;
- 1 canal e-mail vers `securite-ia@acme.example` ;
- 1 métrique `ge_security_config_changes` ;
- 1 alerte « modification d'un garde-fou de sécurité ».

La métrique et l'alerte « pic de blocages » ne sont **pas** créées (0 + 0).

---

## 5. Dépendances avec les autres fichiers

| Lien | Fichier | Fiche |
|---|---|---|
| Utilise `var.project_id`, `var.alert_email`, `var.log_screened_content` | [`variables.tf`](../variables.tf) | [02-variables.md](02-variables.md) |
| Attend `google_project_service.apis` | [`00_foundation.tf`](../00_foundation.tf) | [03-foundation.md](03-foundation.md) |
| Surveille les droits IAM créés par | [`10_identity_access.tf`](../10_identity_access.tf), [`20_data_protection.tf`](../20_data_protection.tf) | [04-identity-access.md](04-identity-access.md), [05-data-protection.md](05-data-protection.md) |
| Surveille les templates et le plancher Model Armor ; `log_screened_content` y règle aussi la journalisation du contenu | [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) | [06-ai-guardrails.md](06-ai-guardrails.md) |
| Surveille l'assistant et l'app | [`50_app.tf`](../50_app.tf) | [08-app.md](08-app.md) |

---

## 6. Pour reproduire / adapter

**Besoin type : créer une alerte sur un autre événement d'audit** (exemple : quelqu'un supprime un secret).

```hcl
# 1. Compter les entrées de journal qui correspondent à l'événement.
resource "google_logging_metric" "secret_deleted" {
  name   = "secret_deleted"                                   # lettres, chiffres, _ : sera "user/secret_deleted"
  filter = <<-EOT
    logName:"cloudaudit.googleapis.com%2Factivity"
    protoPayload.serviceName="secretmanager.googleapis.com"
    protoPayload.methodName=~"DeleteSecret"
  EOT
  metric_descriptor {
    metric_kind = "DELTA"                                     # "combien pendant l'intervalle"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.apis]
}

# 2. Alerter dès que le compteur dépasse le seuil.
resource "google_monitoring_alert_policy" "secret_deleted" {
  display_name = "Secret supprimé"
  combiner     = "OR"
  conditions {
    display_name = "Au moins une suppression en 5 minutes"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.secret_deleted.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0                                     # seuil
      duration        = "0s"                                  # alerter tout de suite
      aggregations {
        alignment_period     = "300s"                         # fenêtre de 5 minutes
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  notification_channels = google_monitoring_notification_channel.security[*].id   # réutiliser le canal existant
  documentation {
    mime_type = "text/markdown"
    content   = "Un secret a été supprimé. Vérifier la PR correspondante."
  }
}
```

1. **Trouver l'événement réel** : faire l'action une fois en recette, puis la chercher dans **Logs Explorer**. Noter
   `protoPayload.serviceName` et `protoPayload.methodName` exacts.
2. **Tester le filtre** dans Logs Explorer : il doit afficher l'entrée, et seulement les entrées voulues.
3. Copier le filtre dans `google_logging_metric` :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/logging_metric
4. Créer l'alerte :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/monitoring_alert_policy
   (canal : https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/monitoring_notification_channel)
5. Si l'événement est dans les journaux **Data Access**, vérifier que l'audit du service est activé
   (https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam, section `google_project_iam_audit_config`)
   et utiliser `cloudaudit.googleapis.com%2Fdata_access` au lieu de `%2Factivity`.
6. `apply`, refaire l'action en recette, vérifier la réception de l'e-mail.

---

## 7. Pièges et bonnes pratiques

- **Les noms de méthodes sont à valider** (guide du socle (docs/00) §16) : ils viennent de la documentation, pas encore de journaux
  réels. Après le premier changement observé, comparez avec Logs Explorer et ajustez le filtre. Les cas utilisent
  `=~` (contient / expression régulière) plutôt que `=` (égalité exacte) pour tolérer les noms de méthodes longs.
- **Les changements faits par Terraform déclenchent aussi l'alerte.** C'est **voulu** : une modification légitime
  passe par une PR, et l'alerte sert de confirmation. Une alerte **sans PR correspondante** = incident.
- **Une métrique basée sur les journaux ne compte qu'à partir de sa création** : elle ne voit pas le passé.
- **`google_project_iam_audit_config` fait autorité pour son service** : il remplace la configuration d'audit
  existante de ce service (par exemple des exemptions ajoutées à la main). Ne gérez l'audit d'un service qu'à un seul
  endroit.
- **Les journaux Data Access ont un coût** (volume ingéré dans Cloud Logging). D'où l'exclusion de Cloud KMS.
- **Sans `alert_email`, les alertes existent mais ne préviennent personne.** Renseignez toujours une boîte suivie
  (liste de diffusion de l'équipe, pas une personne).
- **Échapper les guillemets** dans un `filter` sur une seule ligne (`\"`). Dans un heredoc `<<-EOT`, pas besoin :
  c'est pour ça que les filtres longs y sont écrits.
- **Activer `log_screened_content` est un choix vie privée**, pas technique : à décider avec le DPO (guide du socle (docs/00) §15).
