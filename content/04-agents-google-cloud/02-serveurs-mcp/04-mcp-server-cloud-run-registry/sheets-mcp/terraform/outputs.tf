output "mcp_server_url" {
  description = "À coller dans Gemini Enterprise : Data stores > Custom MCP Server > MCP server URL."
  value       = "${google_cloud_run_v2_service.mcp.uri}/mcp"
}

output "egress_fqdns_to_allow" {
  description = "Domaines à autoriser dans la politique d'organisation des connecteurs (egress)."
  value       = [trimprefix(google_cloud_run_v2_service.mcp.uri, "https://"), "accounts.google.com", "oauth2.googleapis.com"]
}

output "gemini_enterprise_oauth_settings" {
  description = "Valeurs du formulaire OAuth dans Gemini Enterprise (client ID/secret : ceux créés à l'étape 1)."
  value = {
    authorization_url        = "https://accounts.google.com/o/oauth2/v2/auth"
    authorization_url_params = "access_type=offline&prompt=consent&hd=${var.allowed_domains[0]}"
    token_url                = "https://oauth2.googleapis.com/token"
    scopes                   = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly"
    pkce                     = "activé"
    redirect_uri_to_register = "https://vertexaisearch.cloud.google.com/oauth-redirect"
  }
}
