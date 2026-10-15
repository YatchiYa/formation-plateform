# NOTE §5 - SECURE WEB PROXY (optionnel) : liste blanche des destinations Internet
# pour les charges qui sortent par VOTRE VPC (Agent Runtime avec interface PSC,
# Cloud Run avec sortie VPC, VM). Il ne s'applique PAS à Gemini Enterprise lui-même
# (SaaS Google) : là, ce sont Agent Gateway et les politiques d'org qui contrôlent la sortie.
#
# ponytail: pas d'inspection TLS (filtrage par nom d'hôte/SNI). L'inspection TLS
# exige une autorité de certification (CA Service) : à ajouter si le filtrage par URL
# complète devient obligatoire.

locals {
  swp_region = var.region
}

resource "google_compute_subnetwork" "swp_proxy_only" {
  count         = var.swp == null ? 0 : 1
  name          = "swp-proxy-only"
  region        = local.swp_region
  network       = var.swp.network
  ip_cidr_range = var.swp.proxy_only_cidr
  purpose       = "REGIONAL_MANAGED_PROXY"
  role          = "ACTIVE"
  depends_on    = [google_project_service.apis]
}

resource "google_network_security_gateway_security_policy" "swp" {
  count       = var.swp == null ? 0 : 1
  name        = "ge-egress-policy"
  location    = local.swp_region
  description = "Destinations autorisées pour les agents. Tout le reste est refusé."
  depends_on  = [google_project_service.apis]
}

resource "google_network_security_url_lists" "allowed" {
  count       = var.swp == null ? 0 : 1
  name        = "ge-allowed-hosts"
  location    = local.swp_region
  description = "Liste blanche validée par la sécurité (revue trimestrielle)."
  values      = var.swp.allowed_hosts
  depends_on  = [google_project_service.apis]
}

resource "google_network_security_gateway_security_policy_rule" "allow_listed" {
  count                   = var.swp == null ? 0 : 1
  name                    = "allow-listed-hosts"
  location                = local.swp_region
  gateway_security_policy = google_network_security_gateway_security_policy.swp[0].name
  enabled                 = true
  priority                = 100
  description             = "Seuls les hôtes de la liste blanche passent (refus implicite pour le reste)."
  session_matcher         = "inUrlList(host(), '${google_network_security_url_lists.allowed[0].id}')"
  basic_profile           = "ALLOW"
}

resource "google_network_services_gateway" "swp" {
  count                                = var.swp == null ? 0 : 1
  name                                 = "ge-secure-web-proxy"
  location                             = local.swp_region
  type                                 = "SECURE_WEB_GATEWAY"
  addresses                            = [var.swp.address]
  ports                                = [443]
  routing_mode                         = "EXPLICIT_ROUTING_MODE" # les charges utilisent HTTPS_PROXY=https://ADRESSE:443
  gateway_security_policy              = google_network_security_gateway_security_policy.swp[0].id
  network                              = var.swp.network
  subnetwork                           = var.swp.subnetwork
  delete_swg_autogen_router_on_destroy = true
  depends_on                           = [google_compute_subnetwork.swp_proxy_only]
}
