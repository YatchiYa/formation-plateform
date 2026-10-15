terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
    external = { # empaquetage du code de l'agent (scripts/pack.py)
      source  = "hashicorp/external"
      version = "~> 2.3"
    }
  }

  # Production : état distant chiffré, versionné, accès restreint à l'équipe plateforme.
  # backend "gcs" {
  #   bucket = "acme-tfstate-gemini-enterprise"
  #   prefix = "securite-acme"
  # }
}

provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true # requis par les API Discovery Engine (connecteurs)
}
