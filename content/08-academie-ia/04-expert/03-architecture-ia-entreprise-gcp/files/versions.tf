# Versions figées : Terraform >= 1.6 et le provider google 6.x.
terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # En équipe, l'état vit dans un bucket GCS versionné (jamais dans Git) :
  # backend "gcs" {
  #   bucket = "mon-bucket-tfstate"
  #   prefix = "plateforme-ia"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region

  # Ajoute le label à toutes les ressources qui en acceptent.
  default_labels = var.labels
}
