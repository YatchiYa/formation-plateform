terraform {
  required_version = ">= 1.9"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.4"
    }
  }
  # backend "gcs" { bucket = "VOTRE-BUCKET-TFSTATE", prefix = "sheets-mcp" }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
