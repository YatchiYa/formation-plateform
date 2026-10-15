# 02-bis : les 3 agents du trio sur Agent Runtime (hébergement géré par Google), prêts pour Gemini Enterprise.
#
#   3 agents Agent Runtime (un par agent : identité, journaux, sessions gérées)
#     -> inscrits AUTOMATIQUEMENT dans l'Agent Registry du projet agents (rien à écrire pour ça)
#     -> droit d'appel pour Gemini Enterprise si l'app est dans un autre projet (ge_project_number)
#     -> ajoutés à l'app Gemini Enterprise par leur nom de ressource (si ge_app_id est renseigné)

locals {
  trio_dir = abspath("${path.module}/../../agents/trio")
  # Les agents à déployer : ceux de var.agents (clés du catalogue), ou TOUT le catalogue si la liste est vide.
  # Chaque ressource « par agent » fait for_each sur cette carte : une clé = un agent = ses propres ressources.
  catalogue = jsondecode(file("${local.trio_dir}/catalogue.json"))
  agents    = { for k in(length(var.agents) == 0 ? keys(local.catalogue) : var.agents) : k => local.catalogue[k] }

  create_armor      = var.prompt_template == ""
  prompt_template   = local.create_armor ? module.armor[0].prompt : var.prompt_template
  response_template = local.create_armor ? module.armor[0].response : var.response_template

  # Le compte de Gemini Enterprise : c'est LUI qui appelle les agents. Il appartient au projet de l'app (numéro).
  grant_ge         = var.ge_project_number != ""
  publish          = var.ge_app_id != ""
  cross_project    = local.grant_ge && var.ge_project_number != data.google_project.agents.number
  ge_service_agent = "serviceAccount:service-${var.ge_project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

data "google_project" "agents" {
  provider = google.agents
}

# 1. API -----------------------------------------------------------------------
resource "google_project_service" "agents" {
  provider = google.agents
  for_each = toset(concat(["aiplatform.googleapis.com", "agentregistry.googleapis.com", "modelarmor.googleapis.com", "iam.googleapis.com"], var.model_api_key_secret == "" ? [] : ["secretmanager.googleapis.com"],
    # Agents OAuth (oauth_agents) : les API Google qu'ils appellent avec le jeton de l'utilisateur (docs/12-1-8).
  flatten([for k, a in local.agents : try(a.oauth.apis, []) if contains(keys(var.oauth_agents), k)])))
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service" "ge" {
  count              = local.publish ? 1 : 0
  provider           = google.ge
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false
}

# 2. Model Armor : templates fournis (projet 08) ou créés ici --------------------
module "armor" {
  count      = local.create_armor ? 1 : 0
  source     = "../../terraform/modules/armor_templates"
  providers  = { google = google.agents }
  prefix     = "trio-runtime"
  location   = var.ge_location
  depends_on = [google_project_service.agents]
}

# 3. Les 3 agents : même module que l'agent stock du projet 09 --------------------
module "agent" {
  for_each  = local.agents
  source    = "../../terraform/modules/adk_agent"
  providers = { google = google.agents }

  project = var.agents_project_id

  name        = "${each.key}-agent" # nom affiché dans Agent Runtime ET dans Agent Registry
  description = each.value.description
  source_dir  = local.trio_dir
  # Seulement le code de CET agent : ajouter ou modifier un autre agent ne redéploie pas celui-ci.
  source_include    = ["commun.py", "requirements.txt", each.value.dossier]
  entrypoint_module = "${each.value.dossier}.agent"
  region            = var.region
  armor_project     = split("/", local.prompt_template)[1]
  roles             = ["roles/aiplatform.user", "roles/logging.logWriter", "roles/monitoring.metricWriter", "roles/cloudtrace.agent"]
  env = merge({
    MODEL             = var.model
    PROMPT_TEMPLATE   = local.prompt_template
    RESPONSE_TEMPLATE = local.response_template
  }, contains(keys(var.oauth_agents), each.key) ? { AUTH_ID = var.oauth_agents[each.key], GE_ENGINE = var.ge_engine } : {})
  # Clé d'API du modèle (optionnelle), lue dans Secret Manager.
  secret_env = var.model_api_key_secret == "" ? {} : { (var.model_api_key_type == "gemini" ? "GEMINI_API_KEY" : "VERTEX_API_KEY") = var.model_api_key_secret }

  depends_on = [google_project_service.agents]
}

# 4. Autre projet seulement : Gemini Enterprise reçoit le droit d'utiliser les agents du projet agents.
#    Même projet : rien à faire, Google l'a déjà donné.
resource "google_project_iam_member" "ge_uses_agents_project" {
  count    = local.cross_project ? 1 : 0
  provider = google.agents
  project  = var.agents_project_id
  role     = "roles/discoveryengine.serviceAgent"
  member   = local.ge_service_agent
}

# 5. Publication dans l'app Gemini Enterprise (par nom de ressource, comme dans la console) --
resource "terraform_data" "publish" {
  for_each = { for k, a in local.agents : k => a if local.publish }
  input = {
    project_id   = var.ge_project_id
    host         = var.ge_location == "global" ? "discoveryengine.googleapis.com" : "${var.ge_location}-discoveryengine.googleapis.com"
    parent       = "projects/${var.ge_project_id}/locations/${var.ge_location}/collections/default_collection/engines/${var.ge_app_id}/assistants/default_assistant"
    agent        = module.agent[each.key].name
    display_name = each.value.nom_affiche
    description  = each.value.description
    # Autorisation OAuth de l'agent (oauth_agents), créée avant dans l'app : docs/12-3, partie C.
    # Plusieurs fournisseurs : "acces-google,acces-atlassian" (Agent Runtime seulement, docs/12-1-8).
    authorization = contains(keys(var.oauth_agents), each.key) ? join(",", [for id in split(",", var.oauth_agents[each.key]) : "projects/${var.ge_project_number}/locations/${var.ge_location}/authorizations/${id}"]) : ""
  }

  provisioner "local-exec" {
    command     = "${path.module}/../../scripts/register_agent.sh create"
    environment = { for k, v in self.input : upper(k) => v }
  }

  provisioner "local-exec" {
    when        = destroy
    command     = "${path.module}/../../scripts/register_agent.sh delete"
    environment = { for k, v in self.input : upper(k) => v }
  }

  lifecycle {
    precondition {
      condition     = length(distinct([for a in values(local.agents) : a.nom_affiche])) == length(local.agents)
      error_message = "Deux agents du catalogue ont le même nom_affiche : ils s'écraseraient dans Gemini Enterprise."
    }
    precondition {
      condition     = var.ge_project_id != "" && var.ge_project_number != ""
      error_message = "Pour publier (ge_app_id), renseigner aussi ge_project_id et ge_project_number."
    }
  }

  depends_on = [google_project_iam_member.ge_uses_agents_project, google_project_service.ge]
}
