terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }
  # État LOCAL ici : ce socle se crée une fois, avant le bucket d'état. Chez Acme, c'est la 3S qui le fournit.
}

provider "google" {
  project               = var.project_id
  billing_project       = var.project_id
  user_project_override = true
}
