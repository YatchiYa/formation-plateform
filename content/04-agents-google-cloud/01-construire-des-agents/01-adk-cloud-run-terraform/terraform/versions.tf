terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }

  # Local state is fine to learn. For a team, store state in a GCS bucket:
  # backend "gcs" {
  #   bucket = "YOUR-TF-STATE-BUCKET"
  #   prefix = "adk-cloud-run"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
