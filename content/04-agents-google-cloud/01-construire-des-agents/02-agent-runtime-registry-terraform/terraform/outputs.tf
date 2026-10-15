output "agent_resource_name" {
  description = "Full resource name: projects/.../locations/.../reasoningEngines/ID"
  value       = google_vertex_ai_reasoning_engine.agent.name
}

output "agent_id" {
  description = "Numeric ID (the last part of the resource name)."
  value       = element(split("/", google_vertex_ai_reasoning_engine.agent.name), 5)
}

output "query_url" {
  description = "REST endpoint for :query / :streamQuery calls."
  value       = "https://${var.region}-aiplatform.googleapis.com/v1/${google_vertex_ai_reasoning_engine.agent.name}"
}

output "console_url" {
  description = "Agent Runtime page in the console (playground, traces, logs, sessions)."
  value       = "https://console.cloud.google.com/vertex-ai/agents/agent-engines?project=${var.project_id}"
}

output "registered_cloud_run_agent" {
  description = "Agent Registry resource created for the Cloud Run agent (if any)."
  value       = one(google_agent_registry_service.cloud_run_agent[*].registry_resource)
}
