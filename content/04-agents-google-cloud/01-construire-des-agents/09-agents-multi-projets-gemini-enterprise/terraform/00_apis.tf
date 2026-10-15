# API nécessaires de chaque côté.
resource "google_project_service" "agents" {
  provider           = google.agents
  for_each           = toset(["aiplatform.googleapis.com", "agentregistry.googleapis.com", "modelarmor.googleapis.com", "iam.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service" "ge" {
  provider           = google.ge
  for_each           = toset(["aiplatform.googleapis.com", "discoveryengine.googleapis.com", "modelarmor.googleapis.com", "iam.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

data "google_project" "agents" {
  provider = google.agents
}

data "google_project" "ge" {
  provider = google.ge
}

locals {
  # Compte de service de Gemini Enterprise (projet GE) : c'est LUI qui appelle les agents ajoutés à l'app.
  ge_service_agent = "serviceAccount:service-${data.google_project.ge.number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
  # Projet qui héberge les templates Model Armor (ex. projet 08) : les agents doivent pouvoir les appeler.
  create_armor      = var.prompt_template == ""
  prompt_template   = local.create_armor ? module.armor[0].prompt : var.prompt_template
  response_template = local.create_armor ? module.armor[0].response : var.response_template
  armor_project     = split("/", local.prompt_template)[1]
  publish           = var.ge_app_id != ""
  agent_roles       = ["roles/aiplatform.user", "roles/logging.logWriter", "roles/monitoring.metricWriter", "roles/cloudtrace.agent"]
}

# Templates Model Armor créés ici si aucun n'est fourni (même module que 01-bis / 02-bis).
module "armor" {
  count      = local.create_armor ? 1 : 0
  source     = "./modules/armor_templates"
  providers  = { google = google.agents }
  prefix     = "demo09"
  location   = var.ge_location
  depends_on = [google_project_service.agents]
}
