# ÉQUIPE MAGASINS, projet "GE" : l'orchestrateur, qui appelle l'agent stock d'un AUTRE projet.
module "orchestrator" {
  source    = "./modules/adk_agent"
  providers = { google = google.ge }

  project = var.ge_project_id

  name              = "assistant-magasin"
  description       = "Aide les vendeurs ; délègue les questions de stock à l'agent de l'équipe Supply."
  source_dir        = abspath("${path.module}/../agents/orchestrator")
  entrypoint_module = "orchestrator_agent.agent"
  region            = var.region
  armor_project     = local.armor_project
  roles             = local.agent_roles
  env = merge(
    {
      MODEL             = var.model
      PROMPT_TEMPLATE   = local.prompt_template
      RESPONSE_TEMPLATE = local.response_template
      AGENTS_PROJECT    = var.agents_project_id
      REGISTRY_LOCATION = var.region # Agent Runtime s'enregistre dans le registre de SA région
    },
    var.discover_via_registry ? {} : { STOCK_AGENT = module.stock_agent.name },
  )

  depends_on = [google_project_service.ge]
}

# ---- Les DEUX droits cross-project de l'orchestrateur, donnés par le projet agents ----

# 1. Appeler CET agent, et seulement lui (droit posé sur l'agent, pas sur le projet).
#    aiplatform.viewer contient reasoningEngines.get + reasoningEngines.query, rien de plus.
resource "google_vertex_ai_reasoning_engine_iam_member" "orchestrator_calls_stock" {
  provider         = google.agents
  project          = var.agents_project_id
  region           = var.region
  reasoning_engine = module.stock_agent.engine_id
  role             = "roles/aiplatform.viewer"
  member           = module.orchestrator.service_account
}

# 2. Lire le catalogue du projet agents pour y TROUVER l'agent (inutile si discover_via_registry = false).
resource "google_project_iam_member" "orchestrator_reads_registry" {
  count    = var.discover_via_registry ? 1 : 0
  provider = google.agents
  project  = var.agents_project_id
  role     = "roles/agentregistry.viewer"
  member   = module.orchestrator.service_account
}
