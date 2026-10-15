# COUCHE 6 - AUDIT ET DÉTECTION

# 6.1 Journaux d'accès aux données (désactivés par défaut chez Google).
#     Pas de DATA_READ sur Cloud KMS : chaque déchiffrement serait journalisé (volume énorme).
resource "google_project_iam_audit_config" "audit" {
  # Projet 08 (note §4) : + aiplatform (agents, appels Gemini) et agentregistry.
  for_each = toset(["discoveryengine.googleapis.com", "modelarmor.googleapis.com", "secretmanager.googleapis.com", "aiplatform.googleapis.com", "agentregistry.googleapis.com"])
  project  = var.project_id
  service  = each.value
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_monitoring_notification_channel" "security" {
  count        = var.alert_email == "" ? 0 : 1
  display_name = "Équipe sécurité IA"
  type         = "email"
  labels       = { email_address = var.alert_email }
}

# 6.2 Alerte : toute modification d'un garde-fou (filtres, plancher, clés, droits).
#     Basée sur les journaux d'activité d'administration (toujours actifs, sans contenu
#     utilisateur). Les changements faits par Terraform alertent aussi : c'est voulu.
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
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.apis]
}

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
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }
  notification_channels = google_monitoring_notification_channel.security[*].id
  documentation {
    mime_type = "text/markdown"
    content   = "Un garde-fou (Model Armor, clé KMS, droits, assistant) a été modifié. Vérifier qu'il s'agit d'un changement validé (PR Terraform). Sinon : procédure d'incident du guide."
  }
}

# 6.3 Pic de blocages Model Armor : uniquement si la journalisation du contenu est activée.
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
