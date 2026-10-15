# ÉQUIPE SUPPLY, projet "agents" : l'agent spécialiste.
# Déployé sur Agent Runtime => enregistré AUTOMATIQUEMENT dans l'Agent Registry du projet
# (région de l'agent), sous son nom affiché "stock-agent". Rien à écrire pour ça.
module "stock_agent" {
  source    = "./modules/adk_agent"
  providers = { google = google.agents }

  project = var.agents_project_id

  name              = "stock-agent"
  description       = "Donne le stock d'un article Acme par magasin (code article / SKU)."
  source_dir        = abspath("${path.module}/../agents/specialist")
  entrypoint_module = "stock_agent.agent"
  region            = var.region
  armor_project     = local.armor_project
  roles             = local.agent_roles
  env = {
    MODEL             = var.model
    PROMPT_TEMPLATE   = local.prompt_template
    RESPONSE_TEMPLATE = local.response_template
  }

  depends_on = [google_project_service.agents]
}
