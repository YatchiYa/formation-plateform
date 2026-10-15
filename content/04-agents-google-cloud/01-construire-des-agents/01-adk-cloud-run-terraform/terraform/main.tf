locals {
  src_dir = abspath("${path.module}/..")

  # Hash of everything that goes into the image. Code change => new hash => new
  # image tag => new Cloud Run revision. No change => nothing rebuilt.
  src_files = concat(["Dockerfile", "main.py", "requirements.txt"], sort(tolist(fileset(local.src_dir, "agents/**/*.py"))))
  src_hash  = sha1(join("", [for f in local.src_files : filesha1("${local.src_dir}/${f}")]))

  registry = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agents.repository_id}"
  image    = "${local.registry}/${var.service_name}:${substr(local.src_hash, 0, 12)}"
}

# 1. APIs ---------------------------------------------------------------------
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",              # Cloud Run
    "artifactregistry.googleapis.com", # stores the container image
    "aiplatform.googleapis.com",       # Gemini models (Agent Platform)
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "telemetry.googleapis.com", # OpenTelemetry ingestion
  ])
  service            = each.value
  disable_on_destroy = false # never switch APIs off on destroy: other things may use them
}

# 2. Where the image lives ----------------------------------------------------
resource "google_artifact_registry_repository" "agents" {
  location      = var.region
  repository_id = "agents"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# 3. Build & push the image ---------------------------------------------------
# Terraform is not a build tool, but for learning one `terraform apply` doing
# everything is nice. In CI you'd build with Cloud Build / GitHub Actions and
# pass the image tag in as a variable instead.
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

  depends_on = [google_artifact_registry_repository.agents]
}

# 4. Identity the agent runs as (least privilege) -----------------------------
resource "google_service_account" "agent" {
  account_id   = "${var.service_name}-sa"
  display_name = "Runtime identity for ${var.service_name}"
}

resource "google_project_iam_member" "agent" {
  for_each = toset([
    "roles/aiplatform.user",         # call Gemini
    "roles/logging.logWriter",       # write logs
    "roles/monitoring.metricWriter", # write metrics
    "roles/cloudtrace.agent",        # write traces
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.agent.email}"
}

# 5. The Cloud Run service ----------------------------------------------------
resource "google_cloud_run_v2_service" "agent" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false # learning project: let `terraform destroy` work

  template {
    service_account = google_service_account.agent.email

    scaling {
      min_instance_count = 0 # scale to zero = pay nothing when idle
      # ponytail: 1 instance because sessions are in memory; use a DB session
      # service (see README "Sessions") before raising this.
      max_instance_count = 1
    }

    containers {
      image = local.image

      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "MODEL"
        value = var.model
      }
      env {
        name  = "SERVE_WEB_UI"
        value = tostring(var.serve_web_ui)
      }
      env {
        name  = "OTEL_TO_CLOUD"
        value = "true"
      }
    }
  }

  depends_on = [terraform_data.image, google_project_iam_member.agent]
}

# 6. Who may call it ----------------------------------------------------------
# Private by default: only principals with roles/run.invoker (you, as project
# owner) can call it, using an identity token.
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.public ? 1 : 0
  name     = google_cloud_run_v2_service.agent.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
