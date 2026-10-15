terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.7" # 8.7 : google_vertex_ai_rag_corpus et google_vertex_ai_rag_engine_config
    }
  }

  # État local pour apprendre. En équipe : backend "gcs" { bucket = "…-tfstate", prefix = "rag-kit" }
}

provider "google" {
  project               = var.project_id
  region                = var.region
  user_project_override = true
  billing_project       = var.project_id
}
