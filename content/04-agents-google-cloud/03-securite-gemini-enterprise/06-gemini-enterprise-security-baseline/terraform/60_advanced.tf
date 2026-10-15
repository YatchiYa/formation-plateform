# OPTIONS AVANCÉES - désactivées par défaut, activables sans réécrire le socle.

# 6.1 Agent Gateway (sortie) : point de passage contrôlé (deny par défaut, IAM,
#     Model Armor) pour les appels de Gemini Enterprise vers des agents, outils MCP
#     et API enregistrés dans Agent Registry. App 'eu' => passerelle en europe-west1,
#     registre global du projet.
resource "google_network_services_agent_gateway" "egress" {
  count       = var.enable_agent_gateway ? 1 : 0
  name        = "${var.app_id}-egress"
  location    = var.region
  description = "Sortie gouvernée de Gemini Enterprise vers agents / MCP / API."

  google_managed {
    governed_access_path = "AGENT_TO_ANYWHERE"
  }
  registries = ["//agentregistry.googleapis.com/projects/${var.project_id}/locations/global"]

  depends_on = [google_project_service.apis]
}

# 6.2 VPC Service Controls en DRY-RUN : on observe ce qui serait bloqué
#     (journaux "VPC SC dry run") avant d'enforcer. Nécessite une politique
#     d'organisation et les droits Access Context Manager.
resource "google_access_context_manager_service_perimeter" "ge" {
  count                     = var.vpc_sc_access_policy == "" ? 0 : 1
  parent                    = "accessPolicies/${var.vpc_sc_access_policy}"
  name                      = "accessPolicies/${var.vpc_sc_access_policy}/servicePerimeters/gemini_enterprise_${replace(var.project_id, "-", "_")}"
  title                     = "gemini-enterprise-${var.project_id}"
  perimeter_type            = "PERIMETER_TYPE_REGULAR"
  use_explicit_dry_run_spec = true

  spec {
    resources = ["projects/${local.project_number}"]
    restricted_services = [
      "discoveryengine.googleapis.com",
      "modelarmor.googleapis.com",
      "dlp.googleapis.com",
      "cloudkms.googleapis.com",
      "secretmanager.googleapis.com",
    ]
  }
}
