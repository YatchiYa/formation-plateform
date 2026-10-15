# JOURNALISATION - ce qu'on capture, où on le garde, combien de temps, qui le lit.
#
#  Famille                       Contenu                                   Destination           Rétention
#  ----------------------------- ----------------------------------------- --------------------- ---------
#  Audit (admin + accès données) qui a fait quoi : config, droits, clés      bucket ge-security    365 j
#  Model Armor (si activé)       contenu filtré + verdict                   bucket ge-security    365 j
#  Usage Gemini Enterprise       qui a demandé quoi, sources, blocages      bucket ge-usage        90 j
#  Prompts/réponses (option)     texte complet                              bucket ge-usage        90 j
#
# Les journaux d'usage contiennent des questions : ils sont EXCLUS du bucket par
# défaut (_Default, lu par beaucoup de monde) et ne vont que dans ge-usage,
# lisible par l'équipe sécurité seulement.

locals {
  usage_log_filter = <<-EOT
    logName="projects/${var.project_id}/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity"
    OR logName=~"projects/${var.project_id}/logs/discoveryengine.googleapis.com%2Fgen_ai\."
  EOT

  armor_content_filter = "jsonPayload.@type=\"type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry\""

  security_log_filter = <<-EOT
    (logName:"cloudaudit.googleapis.com" AND protoPayload.serviceName=("discoveryengine.googleapis.com" OR "modelarmor.googleapis.com" OR "cloudkms.googleapis.com" OR "secretmanager.googleapis.com" OR "dlp.googleapis.com" OR "cloudresourcemanager.googleapis.com" OR "iam.googleapis.com"))
    OR ${local.armor_content_filter}
  EOT
}

# 8.1 Deux buckets de logs en UE, avec Log Analytics (requêtes SQL dans la console).
resource "google_logging_project_bucket_config" "security" {
  project          = var.project_id
  location         = var.ge_location
  bucket_id        = "ge-security"
  description      = "Gemini Enterprise : audit et décisions Model Armor."
  retention_days   = var.security_log_retention_days
  locked           = var.lock_security_logs
  enable_analytics = true
}

resource "google_logging_project_bucket_config" "usage" {
  project          = var.project_id
  location         = var.ge_location
  bucket_id        = "ge-usage"
  description      = "Gemini Enterprise : activité des utilisateurs (peut contenir des questions)."
  retention_days   = var.usage_log_retention_days
  enable_analytics = true
}

# 8.2 Routage : chaque famille vers son bucket.
resource "google_logging_project_sink" "security" {
  name        = "ge-security-logs"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.security.id}"
  filter      = local.security_log_filter
}

resource "google_logging_project_sink" "usage" {
  name        = "ge-usage-logs"
  destination = "logging.googleapis.com/${google_logging_project_bucket_config.usage.id}"
  filter      = local.usage_log_filter
}

# 8.3 Les contenus sensibles ne restent PAS dans le bucket par défaut.
resource "google_logging_project_exclusion" "sensitive_from_default" {
  name        = "ge-sensitive-content"
  description = "Questions/réponses Gemini Enterprise et contenus Model Armor : uniquement dans les buckets dédiés."
  filter      = "(${trimspace(local.usage_log_filter)}) OR ${local.armor_content_filter}"
}

# 8.4 Seule l'équipe sécurité lit les buckets dédiés (vue _AllLogs de chaque bucket).
locals {
  log_buckets = {
    security = google_logging_project_bucket_config.security.bucket_id
    usage    = google_logging_project_bucket_config.usage.bucket_id
  }
}

resource "google_logging_log_view_iam_member" "security_reads" {
  for_each = { for pair in setproduct(keys(local.log_buckets), var.security_groups) : "${pair[0]}|${pair[1]}" => pair }
  parent   = "projects/${var.project_id}"
  location = var.ge_location
  bucket   = local.log_buckets[each.value[0]]
  name     = "_AllLogs"
  role     = "roles/logging.viewAccessor"
  member   = each.value[1]
}

# 8.5 Option : tableaux de bord BigQuery / Looker Studio, sans copie des données.
resource "google_logging_linked_dataset" "usage" {
  count       = var.link_logs_to_bigquery ? 1 : 0
  link_id     = "ge_usage_logs"
  parent      = "projects/${var.project_id}"
  location    = var.ge_location
  bucket      = google_logging_project_bucket_config.usage.bucket_id
  description = "Lecture SQL des journaux d'usage Gemini Enterprise."
}

# 8.6 Détection des blocages Model Armor SANS journaliser le contenu filtré :
#     une réponse bloquée apparaît dans les journaux d'usage avec CUSTOMER_POLICY_VIOLATION.
resource "google_logging_metric" "policy_violations" {
  name   = "ge_policy_violations"
  filter = "logName=\"projects/${var.project_id}/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity\" AND \"CUSTOMER_POLICY_VIOLATION\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.apis]
}

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
