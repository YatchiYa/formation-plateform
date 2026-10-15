# Agents deployed on Agent Runtime are registered in Agent Registry
# automatically (nothing to write here).
#
# Agents running elsewhere (Cloud Run, GKE, another cloud...) are registered
# manually as a "Service". Here: the Cloud Run agent from project 01.
resource "google_agent_registry_service" "cloud_run_agent" {
  count = var.cloud_run_agent_url == "" ? 0 : 1

  location     = var.registry_location
  service_id   = "weather-agent-cloud-run"
  display_name = "weather-agent (Cloud Run)"
  description  = "Answers questions about the current weather in a city. ADK REST API (/run, /run_sse)."

  # NO_SPEC = plain REST agent. Use A2A_AGENT_CARD + content = <agent card JSON>
  # once the agent speaks A2A, so its skills become discoverable.
  agent_spec {
    type = "NO_SPEC"
  }

  interfaces {
    protocol_binding = "HTTP_JSON"
    url              = var.cloud_run_agent_url
  }

  depends_on = [google_project_service.apis]
}
