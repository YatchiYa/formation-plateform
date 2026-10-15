output "url" {
  description = "Base URL of the Cloud Run service (the MCP endpoint is <url>/mcp)."
  value       = google_cloud_run_v2_service.mcp.uri
}

output "mcp_endpoint" {
  description = "What MCP clients connect to."
  value       = "${google_cloud_run_v2_service.mcp.uri}/mcp"
}

output "registry_mcp_server" {
  description = "Read-only MCP server resource in Agent Registry (what agents look up)."
  value       = google_agent_registry_service.mcp.registry_resource
}
