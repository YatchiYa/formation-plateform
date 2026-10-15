data "external" "carte" { # la carte vient de agent/carte.py : une seule définition, pour le script et Terraform
  count   = var.deploy_agent_cloudrun ? 1 : 0
  program = ["python3", "${local.racine}/agent/carte.py", "--terraform"]
  query   = { url = local.agent_url }
}

output "mcp_url" {
  description = "Adresse du serveur MCP Sheets (privé) : à mettre dans le connecteur « Custom MCP Server » (docs/10-5)."
  value       = local.mcp_url == "" ? "(Sheets pas déployé : produits_mcp)" : local.mcp_url
}
output "mcp_urls" {
  description = "Adresse de chaque serveur MCP (Sheets, Slides) : un connecteur « Custom MCP Server » par serveur."
  value       = local.produits
}
output "agent_url" {
  value = var.deploy_agent_cloudrun ? local.agent_url : "(deploy_agent_cloudrun = false)"
}
output "carte_a2a" {
  description = "La carte à coller dans Gemini Enterprise (Custom agent via A2A), sur une ligne."
  value       = var.deploy_agent_cloudrun ? data.external.carte[0].result.carte : ""
}
output "agent_runtime" {
  description = "Chemin à coller dans Gemini Enterprise (Custom agent via Agent Runtime)."
  value       = var.deploy_agent_runtime ? google_vertex_ai_reasoning_engine.agent[0].id : "(deploy_agent_runtime = false)"
}
output "autorisations_attendues" {
  value = { a2a = var.auth_id, agent_runtime = "${var.auth_id}-runtime" }
}
output "ge_service_agent" {
  value = local.ge_sa == "" ? "(ge_project_number vide : aucun droit donné à Gemini Enterprise)" : trimprefix(local.ge_sa, "serviceAccount:")
}
output "domaines_de_sortie_a_autoriser" {
  description = "Politique d'organisation du projet de l'app (connecteur natif) : domaines de sortie autorisés."
  value       = concat([for p in keys(local.produits) : "${p}-mcp-${local.num}.${var.region}.run.app"], ["accounts.google.com", "oauth2.googleapis.com"])
}
