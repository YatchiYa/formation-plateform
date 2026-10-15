# Ce que le pipeline exécute : EXACTEMENT le Terraform du projet 10 (../../terraform), avec l'état dans le bucket du
# socle 3S (09/03-bis-stack-3s/bootstrap). Les valeurs sont dans mcp.auto.tfvars, versionné (GitOps).
terraform {
  required_version = ">= 1.9"
  backend "gcs" {
    prefix = "10-mcp-sheets"
  }
}

module "mcp" {
  source                = "../../terraform"
  project_id            = var.project_id
  project_number        = var.project_number
  region                = var.region
  oauth_client_ids      = var.oauth_client_ids
  allowed_domains       = var.allowed_domains
  auth_id               = var.auth_id
  ge_project_number     = var.ge_project_number
  produits_mcp          = var.produits_mcp
  deploy_agent_cloudrun = var.deploy_agent_cloudrun
  deploy_agent_runtime  = var.deploy_agent_runtime
}

output "mcp" {
  value = module.mcp
}
