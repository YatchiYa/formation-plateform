# ---------------------------------------------------------------------------
# 2. Réseau privé : pas d'IP publique, API Google via Private Service Connect
# ---------------------------------------------------------------------------
resource "google_compute_network" "vpc" {
  project                 = var.project_id
  name                    = "${var.prefix}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "app" {
  project                  = var.project_id
  name                     = "${var.prefix}-${var.region}"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = var.subnet_cidr
  private_ip_google_access = true

  log_config {
    aggregation_interval = "INTERVAL_5_MIN"
    flow_sampling        = 0.5
  }
}

# Point d'accès PSC : une IP interne qui représente les API Google.
# "vpc-sc" = seulement les API compatibles VPC Service Controls (restricted).
resource "google_compute_global_address" "psc" {
  project      = var.project_id
  name         = "${replace(var.prefix, "-", "")}psc"
  purpose      = "PRIVATE_SERVICE_CONNECT"
  address_type = "INTERNAL"
  address      = var.psc_ip
  network      = google_compute_network.vpc.id
}

resource "google_compute_global_forwarding_rule" "psc" {
  project               = var.project_id
  name                  = "${replace(var.prefix, "-", "")}psc" # lettres et chiffres uniquement
  target                = "vpc-sc"
  network               = google_compute_network.vpc.id
  ip_address            = google_compute_global_address.psc.id
  load_balancing_scheme = ""
}

# DNS privé : *.googleapis.com résout vers l'IP PSC, donc le trafic ne sort pas.
resource "google_dns_managed_zone" "googleapis" {
  project     = var.project_id
  name        = "${var.prefix}-googleapis"
  dns_name    = "googleapis.com."
  description = "API Google via Private Service Connect"
  visibility  = "private"

  private_visibility_config {
    networks {
      network_url = google_compute_network.vpc.id
    }
  }
}

resource "google_dns_record_set" "googleapis_a" {
  project      = var.project_id
  managed_zone = google_dns_managed_zone.googleapis.name
  name         = "googleapis.com."
  type         = "A"
  ttl          = 300
  rrdatas      = [var.psc_ip]
}

resource "google_dns_record_set" "googleapis_wildcard" {
  project      = var.project_id
  managed_zone = google_dns_managed_zone.googleapis.name
  name         = "*.googleapis.com."
  type         = "CNAME"
  ttl          = 300
  rrdatas      = ["googleapis.com."]
}

# Sortie : tout est refusé, sauf HTTPS vers le point PSC.
resource "google_compute_firewall" "deny_egress" {
  project            = var.project_id
  name               = "${var.prefix}-deny-all-egress"
  network            = google_compute_network.vpc.id
  direction          = "EGRESS"
  priority           = 65000
  destination_ranges = ["0.0.0.0/0"]

  deny {
    protocol = "all"
  }
}

resource "google_compute_firewall" "allow_psc" {
  project            = var.project_id
  name               = "${var.prefix}-allow-psc-egress"
  network            = google_compute_network.vpc.id
  direction          = "EGRESS"
  priority           = 1000
  destination_ranges = ["${var.psc_ip}/32"]

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }
}
