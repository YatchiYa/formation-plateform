output "url" {
  description = "Base URL of the agent API."
  value       = google_cloud_run_v2_service.agent.uri
}

output "image" {
  description = "Image currently deployed."
  value       = local.image
}

output "service_account" {
  description = "Identity the agent runs as."
  value       = google_service_account.agent.email
}
