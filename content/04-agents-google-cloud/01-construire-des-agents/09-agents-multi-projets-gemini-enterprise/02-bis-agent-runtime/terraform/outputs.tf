output "agents" {
  description = "Nom de ressource de chaque agent (à coller dans Gemini Enterprise > Ajouter un agent > via Agent Runtime)."
  value       = { for k, m in module.agent : k => m.name }
}

output "ge_service_agent" {
  description = "Compte de Gemini Enterprise qui appelle les agents."
  value       = local.grant_ge ? local.ge_service_agent : "(ge_project_number vide : aucun accès donné à Gemini Enterprise)"
}

output "ge_agents_page" {
  value = local.publish ? "https://console.cloud.google.com/gemini-enterprise/locations/${var.ge_location}/engines/${var.ge_app_id}/agents?project=${var.ge_project_id}" : "(ge_app_id vide : agents non publiés)"
}

output "oauth" {
  description = "Agents OAuth : autorisation(s) attendue(s) dans l'app et portées à demander (docs/12-1-8)."
  value = { for k, a in local.agents : k => {
    autorisations = var.oauth_agents[k]
    portees       = join(" ", concat(try(a.oauth.portees, []), ["https://www.googleapis.com/auth/cloud-platform"])) # cloud-platform : exigé sur Agent Runtime
  } if contains(keys(var.oauth_agents), k) }
}
