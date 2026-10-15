terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }
  # backend "gcs" { bucket = "acme-tfstate-gemini-enterprise"  prefix = "trio-cloud-run-a2a" }
}

# Deux « providers » : le projet des agents, et celui de l'app (seulement pour publier : ge_project_id + ge_app_id).
provider "google" {
  alias                 = "agents" # projet de l'équipe qui PUBLIE les agents
  project               = var.agents_project_id
  region                = var.region
  billing_project       = var.agents_project_id
  user_project_override = true
}

provider "google" {
  alias                 = "ge"                                               # projet de l'app Gemini Enterprise (équipe qui CONSOMME)
  project               = coalesce(var.ge_project_id, var.agents_project_id) # utilisé seulement pour publier
  region                = var.region
  billing_project       = coalesce(var.ge_project_id, var.agents_project_id)
  user_project_override = true
}
