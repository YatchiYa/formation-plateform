output "app_console_url" {
  description = "Gemini Enterprise admin page: copy the web app link from 'Integration' there."
  value       = "https://console.cloud.google.com/gemini-enterprise/locations/${var.ge_location}/engines/${var.app_id}/overview?project=${var.project_id}"
}

output "app_resource_name" {
  value = google_discovery_engine_search_engine.app.name
}

output "prompt_template" {
  value = google_model_armor_template.shield["prompt-shield"].id
}

output "response_template" {
  value = google_model_armor_template.shield["response-shield"].id
}

output "agent_resource_name" {
  value = google_vertex_ai_reasoning_engine.expense_agent.name
}

output "docs_bucket" {
  value = google_storage_bucket.docs.name
}
