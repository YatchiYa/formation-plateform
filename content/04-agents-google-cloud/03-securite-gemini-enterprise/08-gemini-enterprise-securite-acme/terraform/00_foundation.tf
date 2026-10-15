# Fondations : APIs et "service agents" (comptes gérés par Google qui agissent
# pour Gemini Enterprise dans le projet).

data "google_project" "this" {}

locals {
  project_number = data.google_project.this.number
  de_host        = "${var.ge_location}-discoveryengine.googleapis.com"
  kms_location   = var.ge_location == "eu" ? "europe" : "us" # multi-région KMS correspondante
  # Clés régionales exigées par les connecteurs TIERS en mode ingestion + CMEK.
  regional_kms_locations = var.ge_location == "eu" ? ["europe-west1", "europe-west4", "europe-north1"] : ["us-east1", "us-central1", "us-west1"]

  # Identité de Gemini Enterprise : lit les sources, appelle Model Armor, chiffre avec KMS.
  ge_sa = "serviceAccount:service-${local.project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

resource "google_project_service" "apis" {
  for_each = toset(concat(
    [
      "discoveryengine.googleapis.com", # Gemini Enterprise
      "modelarmor.googleapis.com",      # filtrage IA
      "dlp.googleapis.com",             # détecteurs de données sensibles (FR)
      "cloudkms.googleapis.com",        # CMEK
      "secretmanager.googleapis.com",   # secrets des connecteurs
      "logging.googleapis.com",
      "monitoring.googleapis.com",
      # Projet 08
      "aiplatform.googleapis.com",    # agents personnalisés (Agent Runtime) + plancher Model Armor
      "agentregistry.googleapis.com", # catalogue unique des agents / outils (note §10)
      "cloudasset.googleapis.com",    # inventaire anti « Shadow AI » (note §2)
    ],
    var.enable_agent_gateway ? ["networkservices.googleapis.com", "networksecurity.googleapis.com", "certificatemanager.googleapis.com", "compute.googleapis.com", "iap.googleapis.com"] : [],
    var.vpc_sc_access_policy != "" ? ["accesscontextmanager.googleapis.com"] : [],
    var.enable_siem_export ? ["pubsub.googleapis.com"] : [],
    length(var.access_approval_emails) > 0 ? ["accessapproval.googleapis.com"] : [],
    var.swp != null ? ["networkservices.googleapis.com", "networksecurity.googleapis.com", "compute.googleapis.com"] : [],
  ))
  service            = each.value
  disable_on_destroy = false
}

# Les service agents sont créés "à la demande" par Google : on force leur création
# pour que les droits IAM ci-dessous puissent leur être attribués.
resource "terraform_data" "service_agents" {
  triggers_replace = var.project_id
  provisioner "local-exec" {
    command = <<-EOT
      gcloud beta services identity create --service=discoveryengine.googleapis.com --project=${var.project_id}
      gcloud beta services identity create --service=modelarmor.googleapis.com --project=${var.project_id}
    EOT
  }
  depends_on = [google_project_service.apis]
}
