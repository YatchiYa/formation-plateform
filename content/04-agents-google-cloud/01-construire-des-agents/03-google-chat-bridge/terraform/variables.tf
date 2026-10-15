variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "Region for the bridge (Cloud Run + Artifact Registry)."
  type        = string
  default     = "europe-west1"
}

variable "agent_resource_name" {
  description = "Agent Runtime agent to expose in Chat (output agent_resource_name of project 02)."
  type        = string
}
