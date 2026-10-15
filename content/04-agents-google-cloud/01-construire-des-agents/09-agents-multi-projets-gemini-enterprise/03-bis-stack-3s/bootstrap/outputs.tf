# À recopier dans GitHub : Settings > Secrets and variables > Actions > Variables (rien de secret ici).
output "github_variables" {
  value = {
    GCP_WIF_PROVIDER   = google_iam_workload_identity_pool_provider.github.name
    GCP_DEPLOYER_SA    = google_service_account.deployer.email
    GCP_TFSTATE_BUCKET = google_storage_bucket.tfstate.name
  }
}
