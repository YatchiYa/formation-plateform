data "google_project" "this" {}

locals {
  # Discovery Engine (= Gemini Enterprise) endpoint for the chosen multi-region.
  de_host = var.ge_location == "global" ? "discoveryengine.googleapis.com" : "${var.ge_location}-discoveryengine.googleapis.com"

  # Google-managed service agents that act on our behalf.
  sa_discoveryengine = "service-${data.google_project.this.number}@gcp-sa-discoveryengine.iam.gserviceaccount.com" # Gemini Enterprise
  sa_aiplatform      = "service-${data.google_project.this.number}@gcp-sa-aiplatform.iam.gserviceaccount.com"      # Gemini API (floor setting)
}

resource "google_project_service" "apis" {
  for_each = toset([
    "discoveryengine.googleapis.com",      # Gemini Enterprise
    "modelarmor.googleapis.com",           # Model Armor
    "aiplatform.googleapis.com",           # Agent Platform: Gemini + Agent Runtime
    "dlp.googleapis.com",                  # Sensitive Data Protection (used by Model Armor's SDP filter)
    "storage.googleapis.com",              # company documents bucket
    "cloudresourcemanager.googleapis.com", # Agent Runtime deployments
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "orgpolicy.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# Google creates service agents lazily. Force them to exist now, so the IAM
# bindings below don't fail with "service account does not exist".
resource "terraform_data" "service_agents" {
  triggers_replace = var.project_id

  provisioner "local-exec" {
    command = <<-EOT
      gcloud beta services identity create --service=discoveryengine.googleapis.com --project=${var.project_id}
      gcloud beta services identity create --service=aiplatform.googleapis.com --project=${var.project_id}
    EOT
  }

  depends_on = [google_project_service.apis]
}

# Audit logs: who asked what, what Model Armor decided (Data Access logs are off by default).
resource "google_project_iam_audit_config" "audit" {
  for_each = toset(["modelarmor.googleapis.com", "discoveryengine.googleapis.com"])
  project  = var.project_id
  service  = each.value

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}
