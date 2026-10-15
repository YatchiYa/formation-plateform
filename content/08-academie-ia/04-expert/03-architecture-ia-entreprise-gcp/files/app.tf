# ---------------------------------------------------------------------------
# 5. L'assistant : Cloud Run privé, exposé seulement par un load balancer + IAP
# ---------------------------------------------------------------------------
locals {
  with_lb = var.app_domain != ""
}

resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  name     = "${var.prefix}-assistant"
  location = var.region

  # Aucun accès direct par l'URL run.app : seulement via le load balancer interne/externe.
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  deletion_protection = false # lab uniquement

  template {
    service_account = google_service_account.app.email

    scaling {
      max_instance_count = 5 # plafonne aussi la dépense
    }

    # Sortie VPC directe : tout le trafic sortant passe par le VPC privé (et donc PSC).
    vpc_access {
      egress = "ALL_TRAFFIC"
      network_interfaces {
        network    = google_compute_network.vpc.id
        subnetwork = google_compute_subnetwork.app.id
      }
    }

    containers {
      image = var.app_image
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "MODEL_ARMOR_TEMPLATE"
        value = google_model_armor_template.assistant.id
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# IAP appelle Cloud Run avec son agent de service : il doit être invocateur.
resource "google_cloud_run_v2_service_iam_member" "iap_invoker" {
  count    = local.with_lb ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = local.iap_agent
}

resource "google_compute_region_network_endpoint_group" "app" {
  count                 = local.with_lb ? 1 : 0
  project               = var.project_id
  name                  = "${var.prefix}-neg"
  region                = var.region
  network_endpoint_type = "SERVERLESS"

  cloud_run {
    service = google_cloud_run_v2_service.app.name
  }
}

resource "google_compute_backend_service" "app" {
  count                 = local.with_lb ? 1 : 0
  project               = var.project_id
  name                  = "${var.prefix}-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  protocol              = "HTTPS"

  backend {
    group = google_compute_region_network_endpoint_group.app[0].id
  }

  # IAP : identité Google obligatoire avant d'atteindre Cloud Run (client OAuth géré par Google).
  iap {
    enabled = true
  }

  log_config {
    enable = true
  }
}

resource "google_iap_web_backend_service_iam_member" "users" {
  for_each            = local.with_lb ? toset(var.iap_members) : toset([])
  project             = var.project_id
  web_backend_service = google_compute_backend_service.app[0].name
  role                = "roles/iap.httpsResourceAccessor"
  member              = each.value
}

resource "google_compute_url_map" "app" {
  count           = local.with_lb ? 1 : 0
  project         = var.project_id
  name            = "${var.prefix}-urlmap"
  default_service = google_compute_backend_service.app[0].id
}

resource "google_compute_managed_ssl_certificate" "app" {
  count   = local.with_lb ? 1 : 0
  project = var.project_id
  name    = "${var.prefix}-cert"

  managed {
    domains = [var.app_domain]
  }
}

resource "google_compute_target_https_proxy" "app" {
  count            = local.with_lb ? 1 : 0
  project          = var.project_id
  name             = "${var.prefix}-https-proxy"
  url_map          = google_compute_url_map.app[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.app[0].id]
}

resource "google_compute_global_address" "lb" {
  count   = local.with_lb ? 1 : 0
  project = var.project_id
  name    = "${var.prefix}-lb-ip"
}

resource "google_compute_global_forwarding_rule" "https" {
  count                 = local.with_lb ? 1 : 0
  project               = var.project_id
  name                  = "${var.prefix}-https"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  target                = google_compute_target_https_proxy.app[0].id
  ip_address            = google_compute_global_address.lb[0].id
  port_range            = "443"
}
