# Detection: a spike of Model Armor matches = someone probing the assistant
# (jailbreak attempts, data exfiltration tests...). Alert the security team.

resource "google_logging_metric" "model_armor_matches" {
  name        = "model_armor_matches"
  description = "Prompts/responses where a Model Armor filter matched."
  filter      = <<-EOT
    jsonPayload.@type="type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry"
    jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }

  depends_on = [google_project_service.apis]
}

resource "google_monitoring_notification_channel" "security" {
  count        = var.alert_email == "" ? 0 : 1
  display_name = "AI security team"
  type         = "email"
  labels       = { email_address = var.alert_email }
}

resource "google_monitoring_alert_policy" "model_armor_spike" {
  display_name = "Model Armor: spike of blocked AI interactions"
  combiner     = "OR"

  conditions {
    display_name = "More than ${var.alert_threshold} matches in 10 min"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.model_armor_matches.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = var.alert_threshold
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
    content   = "Possible attack on the AI assistant. Open Logs Explorer with `jsonPayload.@type=\"type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry\"` and check which filter matched and for which user."
  }
}
