# ---------------------------------------------------------------------------
# 1. API activées et identités (moindre privilège)
# ---------------------------------------------------------------------------
data "google_project" "this" {
  project_id = var.project_id
}

locals {
  services = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "compute.googleapis.com",
    "dns.googleapis.com",
    "cloudkms.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "iap.googleapis.com",
    "modelarmor.googleapis.com",
    "accesscontextmanager.googleapis.com",
    "billingbudgets.googleapis.com",
  ]
  number = data.google_project.this.number

  # Agents de service Google : ce sont eux qui chiffrent avec la clé CMEK.
  vertex_agent  = "serviceAccount:service-${local.number}@gcp-sa-aiplatform.iam.gserviceaccount.com"
  storage_agent = "serviceAccount:service-${local.number}@gs-project-accounts.iam.gserviceaccount.com"
  iap_agent     = "serviceAccount:service-${local.number}@gcp-sa-iap.iam.gserviceaccount.com"
}

resource "google_project_service" "apis" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false # ne coupe pas une API utilisée par d'autres
}

# Une identité par charge de travail, jamais le compte Compute par défaut.
resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${var.prefix}-app"
  display_name = "Assistant interne (Cloud Run)"
  description  = "Appelle Vertex AI et lit le bucket de connaissances. Aucune clé téléchargée."
}

# Rôles prédéfinis minimaux, au niveau projet. Jamais roles/editor ni roles/owner.
resource "google_project_iam_member" "app_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/modelarmor.user",
  ])
  project = var.project_id
  role    = each.value
  member  = google_service_account.app.member
}

# Lecture du seul bucket de connaissances, pas de tous les buckets du projet.
resource "google_storage_bucket_iam_member" "app_reads_kb" {
  bucket = google_storage_bucket.kb.name
  role   = "roles/storage.objectViewer"
  member = google_service_account.app.member
}

resource "google_project_iam_member" "dev_vertex" {
  for_each = toset(var.app_invokers)
  project  = var.project_id
  role     = "roles/aiplatform.user"
  member   = each.value
}
