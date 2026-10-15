terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }

  # Production : état distant chiffré, versionné, accès restreint à l'équipe plateforme.
  # backend "gcs" {
  #   bucket = "acme-tfstate-gemini-enterprise"
  #   prefix = "security-baseline"
  # }
}

provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true # requis par les API Discovery Engine (connecteurs)
}
