# 04-bis : un agent Dialogflow CX (conversationnel, sans code Python), pour le mode
# « Agent personnalisé via Dialogflow » de Gemini Enterprise. Les valeurs viennent de scripts/config.sh.

terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }
}

variable "agents_project_id" { type = string }
variable "region" {
  type    = string
  default = "europe-west1"
}
# Variables passées par scripts/config.sh mais inutiles ici (déclarées pour éviter un avertissement).
variable "ge_project_number" { default = "" }
variable "ge_project_id" { default = "" }
variable "ge_location" { default = "" }
variable "ge_app_id" { default = "" }
variable "agent_gateway" { default = false }

provider "google" {
  project               = var.agents_project_id
  region                = var.region
  billing_project       = var.agents_project_id
  user_project_override = true
}

resource "google_project_service" "dialogflow" {
  service            = "dialogflow.googleapis.com"
  disable_on_destroy = false
}

resource "google_dialogflow_cx_agent" "accueil" {
  display_name          = "Accueil magasin"
  description           = "Agent conversationnel d'accueil : salutations et orientation en magasin."
  location              = var.region
  default_language_code = "fr"
  time_zone             = "Europe/Paris"
  depends_on            = [google_project_service.dialogflow]
}

output "dialogflow_agent" {
  description = "Source de l'agent Dialogflow, à coller dans Gemini Enterprise (Agent personnalisé via Dialogflow)."
  value       = google_dialogflow_cx_agent.accueil.id
}
