terraform {
  required_version = ">= 1.10"
  # État distant sur MinIO (≈ backend "gcs" en production), verrouillage natif par fichier .tflock
  backend "s3" {
    bucket                      = "tfstate"
    key                         = "dev/terraform.tfstate"
    region                      = "eu-west-1"
    endpoints                   = { s3 = "http://minio:9000" }
    use_path_style              = true
    use_lockfile                = true
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_region_validation      = true
  }
}

module "raw" {
  source   = "../../modules/gcs_bucket_sim"
  name     = "acme-dev-raw"
  location = "EU"
  labels   = { owner = "data-team", env = "dev", cost_center = "cc-1234" }
}

output "buckets" { value = [module.raw.url] }
