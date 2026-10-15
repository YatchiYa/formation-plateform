output "stock_agent" {
  description = "Nom de ressource de l'agent spécialiste (projet agents)."
  value       = module.stock_agent.name
}

output "orchestrator" {
  value = module.orchestrator.name
}

output "ge_agents_page" {
  description = "Console : agents de l'app (droits utilisateurs : onglet Autorisations utilisateur de chaque agent)."
  value       = local.publish ? "https://console.cloud.google.com/gemini-enterprise/locations/${var.ge_location}/engines/${var.ge_app_id}/agents?project=${var.ge_project_id}" : "(ge_app_id vide : agents non publiés)"
}
