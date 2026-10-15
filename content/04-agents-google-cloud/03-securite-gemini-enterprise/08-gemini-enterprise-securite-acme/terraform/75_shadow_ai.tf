# NOTE §2 - SHADOW AI : empêcher, puis détecter, les agents/IA hors gouvernance.
#
#  Empêcher (politiques d'organisation posées sur le projet) :
#   - Cloud Run joignable uniquement en interne / via un load balancer.
#   - Aucun droit IAM pour allUsers / des comptes hors Acme.
#   - Ressources uniquement en UE.
#  Détecter (journaux d'audit, toujours actifs) :
#   - Un service rendu public, un agent créé hors Terraform -> alerte.
#  Inventorier : scripts/shadow_ai_inventory.sh (Cloud Asset Inventory).

resource "google_project_service" "orgpolicy" {
  count              = var.enforce_org_policies ? 1 : 0
  service            = "orgpolicy.googleapis.com"
  disable_on_destroy = false
}

locals {
  org_policies = var.enforce_org_policies ? merge(
    {
      "run.allowedIngress"    = ["internal-and-cloud-load-balancing"]
      "gcp.resourceLocations" = ["in:eu-locations"]
    },
    var.workspace_customer_id != "" ? { "iam.allowedPolicyMemberDomains" = [var.workspace_customer_id] } : {},
  ) : {}
}

resource "google_org_policy_policy" "guardrails" {
  for_each = local.org_policies
  name     = "projects/${var.project_id}/policies/${each.key}"
  parent   = "projects/${var.project_id}"

  spec {
    rules {
      values {
        allowed_values = each.value
      }
    }
  }
  depends_on = [google_project_service.orgpolicy]
}

# Détection : quelqu'un ouvre un service à Internet, ou crée un agent/serveur
# hors du circuit (les changements Terraform alertent aussi : c'est voulu, on
# vérifie que la PR existe).
resource "google_logging_metric" "shadow_ai" {
  name   = "ge_shadow_ai_signals"
  filter = <<-EOT
    logName:"cloudaudit.googleapis.com%2Factivity"
    (
      (protoPayload.methodName=~"SetIamPolicy" AND protoPayload.serviceName="run.googleapis.com"
        AND (protoPayload.request.policy.bindings.members:"allUsers" OR protoPayload.request.policy.bindings.members:"allAuthenticatedUsers"))
      OR (protoPayload.serviceName="aiplatform.googleapis.com" AND protoPayload.methodName=~"ReasoningEngineService.(Create|Update)ReasoningEngine")
      OR (protoPayload.serviceName="agentregistry.googleapis.com" AND protoPayload.methodName=~"(Create|Update|Delete)")
    )
  EOT
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.apis]
}

resource "google_monitoring_alert_policy" "shadow_ai" {
  display_name = "IA : service public, agent ou outil créé / modifié"
  combiner     = "OR"
  conditions {
    display_name = "Au moins un signal en 5 minutes"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.shadow_ai.name}\""
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
    content   = "Un agent, un outil ou un service exposé a été créé/modifié. Vérifier : PR Terraform associée ? enregistré dans Agent Registry ? identité dédiée ? Sinon : traiter comme Shadow AI (guide 08, docs/04)."
  }
}
