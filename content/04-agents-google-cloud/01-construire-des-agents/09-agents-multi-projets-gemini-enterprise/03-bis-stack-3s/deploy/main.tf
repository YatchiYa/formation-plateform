# Ce que le pipeline exécute : EXACTEMENT le Terraform du 01-bis (aucune copie), avec l'état dans le bucket du socle.
#   terraform init -backend-config=bucket=<GCP_TFSTATE_BUCKET>   puis   terraform apply
# Les valeurs sont dans agents.auto.tfvars, versionné : Git est la source de vérité (GitOps).
terraform {
  required_version = ">= 1.9"
  backend "gcs" {
    prefix = "09-agents-a2a"
  }
}

module "agents" {
  source            = "../../01-bis-cloud-run-a2a/terraform"
  agents_project_id = var.agents_project_id
  ge_project_number = var.ge_project_number
  ge_project_id     = var.ge_project_id
  ge_app_id         = var.ge_app_id
  ge_location       = var.ge_location
  region            = var.region
  agents            = var.agents
}

output "agents" {
  value = module.agents
}
