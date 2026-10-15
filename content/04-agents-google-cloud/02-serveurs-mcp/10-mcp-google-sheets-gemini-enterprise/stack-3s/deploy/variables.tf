# Mêmes sens que dans ../../terraform/variables.tf (et config/10-mcp.env).
variable "project_id" { type = string }
variable "project_number" { type = string }
variable "region" {
  type    = string
  default = "europe-west1"
}
variable "oauth_client_ids" { type = list(string) }
variable "allowed_domains" { type = list(string) }
variable "auth_id" {
  type    = string
  default = "acces-sheets"
}
variable "ge_project_number" {
  type    = string
  default = ""
}
variable "produits_mcp" {
  type    = list(string)
  default = ["sheets", "slides"]
}
variable "deploy_agent_cloudrun" {
  type    = bool
  default = true
}
variable "deploy_agent_runtime" {
  type    = bool
  default = false
}
