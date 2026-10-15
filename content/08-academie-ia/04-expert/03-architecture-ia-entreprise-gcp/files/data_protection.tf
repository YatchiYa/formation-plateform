# ---------------------------------------------------------------------------
# 3. Données : clé CMEK dans l'UE, bucket chiffré, journaux d'audit
# ---------------------------------------------------------------------------
resource "google_kms_key_ring" "ai" {
  project    = var.project_id
  name       = "${var.prefix}-keyring"
  location   = var.region # la clé vit dans la même région que les données
  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key" "ai" {
  name            = "${var.prefix}-cmek"
  key_ring        = google_kms_key_ring.ai.id
  rotation_period = var.kms_rotation_period
  purpose         = "ENCRYPT_DECRYPT"

  lifecycle {
    # Détruire la clé rend illisibles toutes les données chiffrées avec elle.
    prevent_destroy = false # passez à true en production
  }
}

# Les agents de service (et eux seuls) peuvent chiffrer/déchiffrer.
resource "google_kms_crypto_key_iam_member" "agents" {
  for_each      = toset([local.vertex_agent, local.storage_agent])
  crypto_key_id = google_kms_crypto_key.ai.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value
}

# Bucket des documents de l'assistant : UE, privé, chiffré CMEK, versionné.
resource "google_storage_bucket" "kb" {
  project                     = var.project_id
  name                        = "${var.prefix}-kb-${local.number}"
  location                    = upper(var.region)
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # lab uniquement

  versioning {
    enabled = true
  }

  encryption {
    default_kms_key_name = google_kms_crypto_key.ai.id
  }

  depends_on = [google_kms_crypto_key_iam_member.agents]
}

# Journaux d'accès aux données (désactivés par défaut) pour Vertex AI et Model Armor.
resource "google_project_iam_audit_config" "ai" {
  for_each = toset(["aiplatform.googleapis.com", "modelarmor.googleapis.com"])
  project  = var.project_id
  service  = each.value

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# Bucket de logs régional à rétention longue, alimenté par un récepteur dédié.
resource "google_logging_project_bucket_config" "audit" {
  project        = var.project_id
  location       = var.region
  bucket_id      = "${var.prefix}-audit"
  retention_days = var.log_retention_days
}

resource "google_logging_project_sink" "audit" {
  project                = var.project_id
  name                   = "${var.prefix}-audit-sink"
  destination            = "logging.googleapis.com/${google_logging_project_bucket_config.audit.id}"
  filter                 = "logName:\"cloudaudit.googleapis.com\" AND (protoPayload.serviceName=\"aiplatform.googleapis.com\" OR protoPayload.serviceName=\"modelarmor.googleapis.com\")"
  unique_writer_identity = true
}
