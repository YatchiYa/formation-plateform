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

# 6.1 bis Autorisations de la passerelle. Agent Gateway REFUSE tout par défaut :
#     chaque serveur MCP enregistré dans Agent Registry doit autoriser explicitement
#     qui peut le joindre via la passerelle (rôle IAP "egressor").
#     Appelants : Gemini Enterprise (son compte de service) et l'agent exemple s'il est déployé.
locals {
  gateway_callers = concat(
    [local.ge_sa], # [à confirmer en recette] identité présentée par GE à la passerelle
    var.deploy_secure_agent ? ["serviceAccount:${google_service_account.secure_agent[0].email}"] : [],
  )
  gateway_grants = var.enable_agent_gateway ? {
    for pair in setproduct(var.agent_gateway_allowed_mcp_servers, local.gateway_callers) :
    "${pair[0]}|${pair[1]}" => { mcp_server_id = pair[0], member = pair[1] }
  } : {}
}

resource "google_iap_agent_registry_mcp_server_iam_member" "egress" {
  for_each      = local.gateway_grants
  project       = var.project_id
  location      = "global"
  mcp_server_id = each.value.mcp_server_id
  role          = "roles/iap.egressor"
  member        = each.value.member
}

# 6.2 VPC Service Controls en DRY-RUN : on observe ce qui serait bloqué
#     (journaux "VPC SC dry run") avant d'enforcer. Nécessite une politique
#     d'organisation et les droits Access Context Manager.
locals {
  vpc_sc_services = [
    "discoveryengine.googleapis.com",
    "aiplatform.googleapis.com",    # projet 08 : agents personnalisés, Agent Runtime, appels Gemini
    "agentregistry.googleapis.com", # projet 08 : catalogue des agents et outils
    "modelarmor.googleapis.com",
    "dlp.googleapis.com",
    "cloudkms.googleapis.com",
    "secretmanager.googleapis.com",
  ]
}

resource "google_access_context_manager_service_perimeter" "ge" {
  count                     = var.vpc_sc_access_policy == "" ? 0 : 1
  parent                    = "accessPolicies/${var.vpc_sc_access_policy}"
  name                      = "accessPolicies/${var.vpc_sc_access_policy}/servicePerimeters/gemini_enterprise_${replace(var.project_id, "-", "_")}"
  title                     = "gemini-enterprise-${var.project_id}"
  perimeter_type            = "PERIMETER_TYPE_REGULAR"
  use_explicit_dry_run_spec = true

  # Ce que le périmètre BLOQUE (vide tant que vpc_sc_enforce = false).
  dynamic "status" {
    for_each = var.vpc_sc_enforce ? [1] : []
    content {
      resources           = ["projects/${local.project_number}"]
      access_levels       = google_access_context_manager_access_level.corporate[*].name # accès depuis le réseau Acme
      restricted_services = local.vpc_sc_services
    }
  }

  # Ce que le périmètre OBSERVE (dry-run) : toujours actif, pour tester une évolution avant de l'appliquer.
  spec {
    resources           = ["projects/${local.project_number}"]
    access_levels       = google_access_context_manager_access_level.corporate[*].name # accès depuis le réseau Acme
    restricted_services = local.vpc_sc_services
  }
}

# 6.3 (projet 08, note §7) Niveau d'accès : la console et l'app ne sont joignables
#     que depuis les IP de sortie Acme. Sans lui, un périmètre enforcé bloque
#     aussi les utilisateurs légitimes (l'interface GE passe par discoveryengine).
resource "google_access_context_manager_access_level" "corporate" {
  count  = var.vpc_sc_access_policy != "" && length(var.corporate_ip_ranges) > 0 ? 1 : 0
  parent = "accessPolicies/${var.vpc_sc_access_policy}"
  name   = "accessPolicies/${var.vpc_sc_access_policy}/accessLevels/acme_corporate_${replace(var.project_id, "-", "_")}"
  title  = "acme-corporate-${var.project_id}"

  basic {
    conditions {
      ip_subnetworks = var.corporate_ip_ranges
    }
  }
}
