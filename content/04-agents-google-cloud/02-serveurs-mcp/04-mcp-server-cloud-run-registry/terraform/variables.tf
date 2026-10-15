variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run and Artifact Registry."
  type        = string
  default     = "europe-west1"
}

variable "service_name" {
  description = "Cloud Run service name. Also the MCP server's display name in Agent Registry."
  type        = string
  default     = "product-catalog"
}

variable "registry_location" {
  description = "Agent Registry location for the MCP server entry (manual registration: not 'us'/'eu')."
  type        = string
  default     = "global"
}

variable "invokers" {
  description = "Extra principals allowed to call the MCP server, e.g. [\"serviceAccount:my-agent@...\"]. Project owners can always call it."
  type        = list(string)
  default     = []
}
