output "app_console_url" {
  description = "Page d'administration ; lien de l'app web dans l'onglet Intégration."
  value       = "https://console.cloud.google.com/gemini-enterprise/locations/${var.ge_location}/engines/${var.app_id}/overview?project=${var.project_id}"
}

output "data_store_ids" {
  value = google_discovery_engine_search_engine.app.data_store_ids
}

output "connector_static_ips" {
  description = "IP sortantes à autoriser côté SaaS (connecteurs avec static_ip = true)."
  value       = { for k, c in google_discovery_engine_data_connector.src : k => c.static_ip_addresses if var.connectors[k].static_ip }
}

output "connector_states" {
  description = "État et blocages éventuels (ex. ALLOWLIST_STATIC_IP)."
  value       = { for k, c in google_discovery_engine_data_connector.src : k => { state = c.state, blocking = c.blocking_reasons } }
}

output "cmek_key" {
  value = var.enable_cmek ? google_kms_crypto_key.ge[0].id : "CMEK désactivé"
}

output "model_armor_templates" {
  value = { for k, t in google_model_armor_template.shield : k => t.id }
}

output "agent_gateway" {
  value = var.enable_agent_gateway ? google_network_services_agent_gateway.egress[0].id : "désactivé"
}

output "log_buckets" {
  description = "Buckets de journaux dédiés (Logs Explorer > Affiner la portée > Stockage)."
  value       = { for k, b in local.log_buckets : k => "projects/${var.project_id}/locations/${var.ge_location}/buckets/${b}" }
}
