terraform {
  required_version = ">= 1.9"
  required_providers {
    google   = { source = "hashicorp/google", version = "~> 8.4" }
    external = { source = "hashicorp/external", version = "~> 2.3" }
  }
  # backend "gcs" { bucket = "<bucket-tfstate>"  prefix = "10-mcp-sheets" }   # en équipe : l'état dans un bucket
}

provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true
}
