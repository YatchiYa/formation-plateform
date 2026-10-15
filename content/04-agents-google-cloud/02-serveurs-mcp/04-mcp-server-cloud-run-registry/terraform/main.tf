locals {
  src_dir  = abspath("${path.module}/../server")
  src_hash = sha1(join("", [for f in ["Dockerfile", "main.py", "requirements.txt"] : filesha1("${local.src_dir}/${f}")]))
  image    = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.mcp.repository_id}/${var.service_name}:${substr(local.src_hash, 0, 12)}"
}

# 1. APIs ---------------------------------------------------------------------
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "agentregistry.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# 2. Image: build & push (same pattern as project 01) -------------------------
resource "google_artifact_registry_repository" "mcp" {
  location      = var.region
  repository_id = "mcp-servers"
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

# 3. Identity of the server: it calls nothing on GCP, so it gets NO roles. ----
resource "google_service_account" "mcp" {
  account_id   = "${var.service_name}-mcp"
  display_name = "Runtime identity for the ${var.service_name} MCP server"
}

# 4. The MCP server on Cloud Run (private) ------------------------------------
resource "google_cloud_run_v2_service" "mcp" {
  name                = var.service_name
  location            = var.region
  deletion_protection = false

  template {
    service_account = google_service_account.mcp.email

    scaling {
      min_instance_count = 0
      max_instance_count = 5 # fine: the server is stateless (stateless_http=True)
    }

    containers {
      image = local.image
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
    }
  }

  depends_on = [terraform_data.image]
}

# 5. Who may call it ----------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "invokers" {
  for_each = toset(var.invokers)
  name     = google_cloud_run_v2_service.mcp.name
  location = var.region
  role     = "roles/run.invoker"
  member   = each.value
}
