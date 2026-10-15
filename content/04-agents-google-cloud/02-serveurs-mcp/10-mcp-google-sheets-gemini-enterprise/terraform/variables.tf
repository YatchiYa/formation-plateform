# Toutes ces valeurs viennent de « source scripts/config.sh config/10-mcp.env » (variables TF_VAR_*).
variable "project_number" { type = string }         # NUM_PROJET : donné, pas lu (l API de lecture peut être inactive sur un projet neuf)
variable "project_id" { type = string }             # projet du serveur MCP et de l'agent
variable "region" { type = string }                 # ex. europe-west1 (app « eu » => europe-*)
variable "oauth_client_ids" { type = list(string) } # clients OAuth dont le serveur MCP accepte les jetons
variable "allowed_domains" { type = list(string) }  # ex. ["acme.example"]
variable "auth_id" { type = string }                # autorisation OAuth de l'agent A2A dans l'app (Agent Runtime : <auth_id>-runtime)
variable "model" {
  type    = string
  default = "gemini-3.5-flash"
}
variable "registry_location" {
  type    = string
  default = "europe-west1"
}
variable "ge_project_number" { # numéro du projet de l'app : vide = aucun droit donné à Gemini Enterprise
  type    = string
  default = ""
}
variable "deploy_agent_cloudrun" {
  type    = bool
  default = true
}
variable "deploy_agent_runtime" {
  type    = bool
  default = false
}
variable "register_in_agent_registry" {
  type    = bool
  default = true
}
variable "produits_mcp" { # les serveurs MCP qui doivent EXISTER (une image, un service chacun) : ["sheets"], ["slides"] ou les deux
  type    = list(string)
  default = ["sheets", "slides"]
  validation {
    condition     = length(var.produits_mcp) > 0 && alltrue([for p in var.produits_mcp : contains(["sheets", "slides"], p)])
    error_message = "produits_mcp : au moins un serveur, parmi « sheets » et « slides »."
  }
}
