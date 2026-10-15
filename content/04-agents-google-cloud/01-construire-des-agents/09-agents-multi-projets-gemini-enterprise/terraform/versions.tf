terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
  }
  # backend "gcs" { bucket = "acme-tfstate-gemini-enterprise"  prefix = "agents-multi-projets" }
}

# Deux projets, deux "providers". Pour un essai, les deux variables peuvent valoir le même projet.
provider "google" {
  alias                 = "agents" # projet de l'équipe qui PUBLIE l'agent (ex. Supply)
  project               = var.agents_project_id
  region                = var.region
  billing_project       = var.agents_project_id
  user_project_override = true
}

provider "google" {
  alias                 = "ge" # projet de l'app Gemini Enterprise (équipe qui CONSOMME)
  project               = var.ge_project_id
  region                = var.region
  billing_project       = var.ge_project_id
  user_project_override = true
}
