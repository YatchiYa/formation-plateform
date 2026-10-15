# Register the MCP server in Agent Registry, with the list of tools it offers.
# Agents (ADK AgentRegistry.get_mcp_toolset), Agent Studio, admins and the
# Agent Registry search can then find it by name / tool / description.
resource "google_agent_registry_service" "mcp" {
  location     = var.registry_location
  service_id   = var.service_name
  display_name = var.service_name
  description  = "Company product catalog: search products, read prices and stock levels (read-only)."

  mcp_server_spec {
    type    = "TOOL_SPEC"
    content = file("${path.module}/toolspec.json") # keep in sync with server/main.py (scripts/test_mcp.py checks it)
  }

  interfaces {
    protocol_binding = "JSONRPC" # MCP messages are JSON-RPC 2.0
    url              = "${google_cloud_run_v2_service.mcp.uri}/mcp"
  }

  depends_on = [google_project_service.apis]
}
