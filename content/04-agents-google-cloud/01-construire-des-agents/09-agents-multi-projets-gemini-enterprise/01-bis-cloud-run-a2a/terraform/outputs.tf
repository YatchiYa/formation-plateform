output "urls" {
  description = "URL A2A de chaque agent (privée : jeton d'identité obligatoire)."
  value       = { for k, s in google_cloud_run_v2_service.agent : k => s.uri }
}

output "cards" {
  description = "Cartes A2A v0.3, à coller dans Gemini Enterprise (Ajouter un agent > via A2A) si vous publiez à la main."
  value       = local.card
}

output "ge_service_agent" {
  description = "Compte de Gemini Enterprise qui appelle les agents (rôle run.invoker sur chaque service)."
  value       = local.grant_ge ? local.ge_service_agent : "(ge_project_number vide : aucun accès donné à Gemini Enterprise)"
}

output "ge_agents_page" {
  value = local.publish ? "https://console.cloud.google.com/gemini-enterprise/locations/${var.ge_location}/engines/${var.ge_app_id}/agents?project=${var.ge_project_id}" : "(ge_app_id vide : agents non publiés)"
}

output "agent_gateway" {
  description = "Passerelle à relier à l'app (console : app > Sécurité > Configuration > Agent Gateway)."
  value       = var.agent_gateway ? google_network_services_agent_gateway.ge[0].id : "(agent_gateway = false)"
}

output "oauth" {
  description = "Agents OAuth : autorisation(s) attendue(s) dans l'app et portées à demander (docs/12-1-8)."
  value = { for k, a in local.agents : k => {
    autorisations = var.oauth_agents[k]
    portees       = join(" ", try(a.oauth.portees, []))
  } if contains(keys(var.oauth_agents), k) }
}
