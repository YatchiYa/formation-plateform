variable "project_id" {
  description = "GCP project ID to deploy into."
  type        = string
}

variable "region" {
  description = "Region for Cloud Run and Artifact Registry."
  type        = string
  default     = "europe-west1"
}

variable "service_name" {
  description = "Cloud Run service name (also used for the image and service account)."
  type        = string
  default     = "weather-agent"
}

variable "model" {
  description = "Gemini model ID used by the agent."
  type        = string
  default     = "gemini-3.5-flash"
}

variable "public" {
  description = "true = anyone on the internet can call the agent. Keep false unless you add your own auth."
  type        = bool
  default     = false
}

variable "serve_web_ui" {
  description = "Serve the ADK dev web UI at / (handy for learning, turn off in prod)."
  type        = bool
  default     = true
}
