locals {
  de_host  = var.ge_location == "global" ? "discoveryengine.googleapis.com" : "${var.ge_location}-discoveryengine.googleapis.com"
  ge_agent = "service-${var.project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
  bucket   = "${var.project_id}-${var.prefix}-depots"
  # Import « FULL » : ce qui n'est plus dans le bucket est retiré du data store (vérifié) ; l'inchangé reste.
  import_body = jsonencode({
    gcsSource          = { inputUris = ["gs://${local.bucket}/*"], dataSchema = "content" }
    reconciliationMode = "FULL"
  })
}

resource "google_project_service" "apis" {
  for_each           = toset(["discoveryengine.googleapis.com", "storage.googleapis.com", "cloudscheduler.googleapis.com", "secretmanager.googleapis.com", "iam.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

# Google crée ses agents de service à la demande : on force celui de Gemini Enterprise (droits sur le bucket).
resource "terraform_data" "service_agent" {
  triggers_replace = var.project_id
  provisioner "local-exec" {
    command = "gcloud beta services identity create --service=discoveryengine.googleapis.com --project=${var.project_id}"
  }
  depends_on = [google_project_service.apis]
}

# Son rôle standard : Google ne l'accorde pas toujours quand l'agent est créé à la main. Sans lui, l'import GCS
# échoue (vérifié) : « …@gcp-sa-discoveryengine… does not have storage.buckets.create » (bucket temporaire d'import).
resource "google_project_iam_member" "ge_agent" {
  project    = var.project_id
  role       = "roles/discoveryengine.serviceAgent"
  member     = "serviceAccount:${local.ge_agent}"
  depends_on = [terraform_data.service_agent]
}

# --- Fichiers déposés : bucket -> data store, resynchro planifiée --------------------------------
resource "google_storage_bucket" "depots" {
  count                       = var.depots ? 1 : 0
  name                        = local.bucket
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # kit d'apprentissage : à retirer en production
  depends_on                  = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "ge_reads" {
  count      = var.depots ? 1 : 0
  bucket     = google_storage_bucket.depots[0].name
  role       = "roles/storage.objectViewer"
  member     = "serviceAccount:${local.ge_agent}"
  depends_on = [terraform_data.service_agent]
}

resource "google_discovery_engine_data_store" "depots" {
  count             = var.depots ? 1 : 0
  location          = var.ge_location
  data_store_id     = "${var.prefix}-depots"
  display_name      = "Fichiers déposés"
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED" # fichiers non structurés : PDF, DOCX, PPTX, HTML, TXT…
  solution_types    = ["SOLUTION_TYPE_SEARCH"]
  # Déclaré explicitement : l'API en renvoie un par défaut ; non déclaré, Terraform veut le retirer, ce qui force
  # la RECRÉATION du data store (vérifié : tout l'index perdu, et l'ID bloqué plusieurs heures).
  document_processing_config {
    chunking_config { # obligatoire avec le layout parser (vérifié : 400 sinon)
      layout_based_chunking_config {
        chunk_size                = 500
        include_ancestor_headings = true # chaque morceau garde ses titres : meilleures réponses
      }
    }
    default_parsing_config {
      layout_parsing_config {} # comprend tableaux et titres (PDF, DOCX, PPTX)
    }
  }
  lifecycle {
    ignore_changes = [document_processing_config] # jamais de recréation sur une différence renvoyée par l'API
  }
  depends_on = [google_project_service.apis]
}

# Compte qui relance l'import (Cloud Scheduler -> API Discovery Engine, sans code).
resource "google_service_account" "sync" {
  count        = var.depots ? 1 : 0
  account_id   = "${var.prefix}-sync-sa"
  display_name = "Kit RAG GE : resynchro du bucket des dépôts"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "sync" {
  count   = var.depots ? 1 : 0
  project = var.project_id
  role    = "roles/discoveryengine.editor" # documents:import
  member  = google_service_account.sync[0].member
}

resource "google_cloud_scheduler_job" "resync" {
  count     = var.depots && var.depots_schedule != "" ? 1 : 0
  name      = "${var.prefix}-resync-depots"
  region    = var.region
  schedule  = var.depots_schedule
  time_zone = "Europe/Paris"
  http_target {
    http_method = "POST"
    uri         = "https://${local.de_host}/v1/${google_discovery_engine_data_store.depots[0].name}/branches/0/documents:import"
    headers     = { "Content-Type" = "application/json" }
    body        = base64encode(local.import_body)
    oauth_token {
      service_account_email = google_service_account.sync[0].email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
  depends_on = [google_project_iam_member.sync, google_storage_bucket_iam_member.ge_reads, google_project_iam_member.ge_agent]
}

# 1er import au déploiement (puis la planification prend le relais).
resource "terraform_data" "first_import" {
  count            = var.depots ? 1 : 0
  triggers_replace = google_discovery_engine_data_store.depots[0].name
  provisioner "local-exec" {
    command = <<-EOT
      # Bucket encore vide au 1er déploiement : l'API peut refuser l'import ; la planification le refera.
      curl -sS -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
        -H "X-Goog-User-Project: ${var.project_id}" -d '${local.import_body}' \
        "https://${local.de_host}/v1/${google_discovery_engine_data_store.depots[0].name}/branches/0/documents:import" | head -c 300 || true
    EOT
  }
  depends_on = [google_storage_bucket_iam_member.ge_reads, google_project_iam_member.ge_agent]
}
