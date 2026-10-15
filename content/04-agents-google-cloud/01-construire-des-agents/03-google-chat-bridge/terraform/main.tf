locals {
  name    = "chat-bridge"
  src_dir = abspath("${path.module}/..")

  src_hash = sha1(join("", [for f in ["Dockerfile", "main.py", "requirements.txt"] : filesha1("${local.src_dir}/${f}")]))
  image    = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}/${local.name}:${substr(local.src_hash, 0, 12)}"

  # The identity Google Chat (Workspace add-ons) uses to call HTTP endpoints.
  # It is also shown in the console: Chat API > Configuration.
  addons_sa = "service-${data.google_project.this.number}@gcp-sa-gsuiteaddons.iam.gserviceaccount.com"
}

data "google_project" "this" {}

resource "google_project_service" "apis" {
  for_each = toset([
    "chat.googleapis.com",
    "gsuiteaddons.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = local.name
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "terraform_data" "image" {
  triggers_replace = local.image

  provisioner "local-exec" {
    working_dir = local.src_dir
    command     = <<-EOT
      set -e
      gcloud auth configure-docker ${var.region}-docker.pkg.dev --quiet
      docker build --platform linux/amd64 -t ${local.image} .
      docker push ${local.image}
    EOT
  }
}

# The bridge's own identity: it only needs to call the agent.
resource "google_service_account" "bridge" {
  account_id   = "${local.name}-sa"
  display_name = "Google Chat -> Agent Runtime bridge"
}

resource "google_project_iam_member" "bridge_calls_agent" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.bridge.email}"
}

resource "google_cloud_run_v2_service" "bridge" {
  name                = local.name
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.bridge.email
    timeout         = "60s"

    containers {
      image = local.image
      env {
        name  = "AGENT_NAME"
        value = var.agent_resource_name
      }
    }
  }

  depends_on = [terraform_data.image, google_project_iam_member.bridge_calls_agent]
}

# Only Google Chat may call the bridge (plus project owners, for testing).
resource "google_cloud_run_v2_service_iam_member" "chat_invoker" {
  name     = google_cloud_run_v2_service.bridge.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${local.addons_sa}"
}
