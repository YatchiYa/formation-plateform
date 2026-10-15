data "google_project" "this" {}

locals {
  src_dir  = abspath("${path.module}/../server")
  src_hash = sha1(join("", [for f in ["Dockerfile", "main.py", "requirements.txt"] : filesha1("${local.src_dir}/${f}")]))
  image    = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.mcp.repository_id}/${var.service_name}:${substr(local.src_hash, 0, 12)}"
  # Identité de Gemini Enterprise : c'est elle qui appelle le serveur (en-tête X-Serverless-Authorization).
  ge_service_agent = "service-${data.google_project.this.number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

# 1. APIs : Cloud Run + les API appelées AU NOM des utilisateurs (Sheets, Drive).
resource "google_project_service" "apis" {
  for_each = toset(concat(
    ["run.googleapis.com", "artifactregistry.googleapis.com", "sheets.googleapis.com", "drive.googleapis.com", "discoveryengine.googleapis.com"],
    var.register_in_agent_registry ? ["agentregistry.googleapis.com"] : [],
  ))
  service            = each.value
  disable_on_destroy = false
}

resource "terraform_data" "ge_service_agent" {
  triggers_replace = var.project_id
  provisioner "local-exec" {
    command = "gcloud beta services identity create --service=discoveryengine.googleapis.com --project=${var.project_id}"
  }
  depends_on = [google_project_service.apis]
}

# 2. Image du serveur (tag = empreinte du code : pas de changement => pas de rebuild).
resource "google_artifact_registry_repository" "mcp" {
  location      = var.region
  repository_id = "mcp-sheets"
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

# 3. Identité du service : AUCUN rôle. Il n'accède aux données qu'avec le jeton
#    de l'utilisateur, donc uniquement à ce que l'utilisateur peut déjà voir.
resource "google_service_account" "mcp" {
  account_id   = "${var.service_name}-sa"
  display_name = "MCP Google Sheets (aucun droit propre)"
}

# 4. Le service Cloud Run, PRIVÉ.
resource "google_cloud_run_v2_service" "mcp" {
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL" # Gemini Enterprise appelle depuis l'infrastructure Google ; l'IAM filtre
  deletion_protection = false

  template {
    service_account = google_service_account.mcp.email
    timeout         = "120s"
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
    containers {
      image = local.image
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
      env {
        name  = "OAUTH_CLIENT_IDS"
        value = join(",", var.oauth_client_ids)
      }
      env {
        name  = "ALLOWED_DOMAINS"
        value = join(",", var.allowed_domains)
      }
    }
  }

  depends_on = [terraform_data.image]
}

# 5. Seul Gemini Enterprise (et les testeurs listés) peut appeler le service.
resource "google_cloud_run_v2_service_iam_member" "invokers" {
  for_each   = toset(concat(["serviceAccount:${local.ge_service_agent}"], var.extra_invokers))
  name       = google_cloud_run_v2_service.mcp.name
  location   = var.region
  role       = "roles/run.invoker"
  member     = each.value
  depends_on = [terraform_data.ge_service_agent]
}

# 6. Catalogue de l'entreprise : le serveur et ses 17 outils dans Agent Registry.
resource "google_agent_registry_service" "mcp" {
  count        = var.register_in_agent_registry ? 1 : 0
  location     = var.registry_location
  service_id   = var.service_name
  display_name = "google-sheets"
  description  = "Lecture et modification native de Google Sheets au nom de l'utilisateur (OAuth Google, domaine restreint)."

  mcp_server_spec {
    type    = "TOOL_SPEC"
    content = file("${path.module}/toolspec.json") # généré par scripts/gen_toolspec.py
  }

  interfaces {
    protocol_binding = "JSONRPC"
    url              = "${google_cloud_run_v2_service.mcp.uri}/mcp"
  }

  depends_on = [google_project_service.apis]
}
