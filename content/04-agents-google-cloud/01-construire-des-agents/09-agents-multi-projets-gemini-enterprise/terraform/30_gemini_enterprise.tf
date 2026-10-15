# PUBLICATION DANS GEMINI ENTERPRISE (app du projet GE).

# Cas cross-project : l'agent stock vit dans le projet agents. Le compte de service de
# Gemini Enterprise (projet GE) doit y recevoir le rôle "Discovery Engine Service Agent"
# (doc Google : Configure cross-project ADK agent access).
#
# Même droit pour chaque projet qui héberge un agent publié (agent stock + agents externes),
# sauf le projet GE lui-même.
locals {
  agent_projects = setsubtract(toset(concat(
    var.publish_specialist_in_ge ? [var.agents_project_id] : [],
    [for a in var.external_adk_agents : split("/", a.engine)[1]],
  )), [var.ge_project_id, tostring(data.google_project.ge.number)])
}

resource "google_project_iam_member" "ge_uses_agents_project" {
  for_each = local.publish ? local.agent_projects : toset([])
  provider = google.ge
  project  = each.value
  role     = "roles/discoveryengine.serviceAgent"
  member   = local.ge_service_agent
}

locals {
  assistant = "projects/${var.ge_project_id}/locations/${var.ge_location}/collections/default_collection/engines/${var.ge_app_id}/assistants/default_assistant"
  published = merge(
    {
      orchestrator = {
        agent        = module.orchestrator.name
        display_name = "Assistant magasin"
        description  = "Conseils produit et stock en magasin (avec l'agent Supply)."
      }
    },
    { for k, a in var.external_adk_agents : "ext-${k}" => { agent = a.engine, display_name = a.display_name, description = a.description } },
    var.publish_specialist_in_ge ? {
      stock = {
        agent        = module.stock_agent.name
        display_name = "Stock magasin (Supply)"
        description  = "Stock d'un article par magasin, à partir du code article."
      }
    } : {},
  )
}

# Pas encore de ressource Terraform pour les agents d'une app : API REST (v1alpha), via script.
resource "terraform_data" "publish" {
  for_each = local.publish ? local.published : {}
  input = {
    project_id   = var.ge_project_id
    host         = var.ge_location == "global" ? "discoveryengine.googleapis.com" : "${var.ge_location}-discoveryengine.googleapis.com"
    parent       = local.assistant
    agent        = each.value.agent
    display_name = each.value.display_name
    description  = each.value.description
  }

  provisioner "local-exec" {
    command     = "${path.module}/../scripts/register_agent.sh create"
    environment = { for k, v in self.input : upper(k) => v }
  }

  provisioner "local-exec" {
    when        = destroy
    command     = "${path.module}/../scripts/register_agent.sh delete"
    environment = { for k, v in self.input : upper(k) => v }
  }

  depends_on = [google_project_iam_member.ge_uses_agents_project]
}
