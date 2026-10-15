# ---------------------------------------------------------------------------
# 4. VPC Service Controls : un périmètre autour de Vertex AI et du stockage
#    (nécessite une organisation ; désactivé si access_policy_id = null)
# ---------------------------------------------------------------------------
locals {
  restricted_services = [
    "aiplatform.googleapis.com",
    "storage.googleapis.com",
    "modelarmor.googleapis.com",
    "cloudkms.googleapis.com",
  ]
  perimeter_config = {
    resources           = ["projects/${local.number}"]
    restricted_services = local.restricted_services
  }
}

resource "google_access_context_manager_service_perimeter" "ai" {
  count = var.access_policy_id == null ? 0 : 1

  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/${replace(var.prefix, "-", "_")}"
  title  = "${var.prefix} - plateforme IA"

  # Mode test : la configuration est dans "spec" et ne bloque rien, elle journalise.
  use_explicit_dry_run_spec = var.vpcsc_dry_run

  dynamic "spec" {
    for_each = var.vpcsc_dry_run ? [local.perimeter_config] : []
    content {
      resources           = spec.value.resources
      restricted_services = spec.value.restricted_services
      vpc_accessible_services {
        enable_restriction = true
        allowed_services   = ["RESTRICTED-SERVICES"]
      }
    }
  }

  dynamic "status" {
    for_each = var.vpcsc_dry_run ? [] : [local.perimeter_config]
    content {
      resources           = status.value.resources
      restricted_services = status.value.restricted_services
      vpc_accessible_services {
        enable_restriction = true
        allowed_services   = ["RESTRICTED-SERVICES"]
      }
    }
  }
}
