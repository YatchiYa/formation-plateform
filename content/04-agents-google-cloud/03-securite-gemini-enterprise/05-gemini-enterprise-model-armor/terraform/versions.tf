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

  # backend "gcs" {
  #   bucket = "YOUR-TF-STATE-BUCKET"
  #   prefix = "gemini-enterprise"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
