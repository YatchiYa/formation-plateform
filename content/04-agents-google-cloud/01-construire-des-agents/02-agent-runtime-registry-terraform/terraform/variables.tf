variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Agent Runtime region."
  type        = string
  default     = "europe-west1"
}

variable "display_name" {
  description = "Display name of the agent in Agent Runtime / Agent Registry."
  type        = string
  default     = "currency-agent"
}

variable "model" {
  description = "Gemini model ID used by the agent."
  type        = string
  default     = "gemini-3.5-flash"
}

variable "cloud_run_agent_url" {
  description = "URL of the Cloud Run agent from project 01. Empty = don't register it."
  type        = string
  default     = ""
}

variable "registry_location" {
  description = "Agent Registry location for manually registered services."
  type        = string
  default     = "global"
}
