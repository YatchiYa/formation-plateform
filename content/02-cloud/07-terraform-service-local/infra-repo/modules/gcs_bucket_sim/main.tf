# Module « bucket Cloud Storage » SIMULÉ : terraform_data enregistre la configuration
# comme le ferait google_storage_bucket, sans appeler Google Cloud.
# Pour passer en réel : remplacer terraform_data par google_storage_bucket (mêmes variables).
variable "name" { type = string }
variable "location" { type = string }
variable "labels" { type = map(string) }
variable "public" {
  type    = bool
  default = false
}

resource "terraform_data" "bucket" {
  input = {
    kind     = "google_storage_bucket"
    name     = var.name
    location = var.location
    labels   = var.labels
    public   = var.public
    url      = "gs://${var.name}"
  }
}

output "url" { value = terraform_data.bucket.output.url }
