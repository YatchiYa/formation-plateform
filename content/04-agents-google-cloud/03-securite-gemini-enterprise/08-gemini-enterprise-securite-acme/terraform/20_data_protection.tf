# COUCHE 2 - PROTECTION DES DONNÉES : CMEK (clés du client) + secrets.

# 2.1 Clé principale, multi-région "europe" pour une app "eu".
#     Rotation MANUELLE : exigence Gemini Enterprise (pas de rotation_period).
resource "google_kms_key_ring" "ge" {
  count      = var.enable_cmek ? 1 : 0
  name       = var.kms_key_ring
  location   = local.kms_location
  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key" "ge" {
  count    = var.enable_cmek ? 1 : 0
  name     = "gemini-enterprise-data"
  key_ring = google_kms_key_ring.ge[0].id
  purpose  = "ENCRYPT_DECRYPT"
  labels   = { usage = "gemini-enterprise", owner = "security" }

  # Détruire cette clé = rendre TOUTES les données indexées illisibles (crypto-shredding).
  # Terraform refuse donc de la supprimer. Voir le guide, section "Désactiver la clé".
  lifecycle {
    prevent_destroy = true
  }
}

# 2.2 Clés régionales : exigées pour les connecteurs TIERS en mode ingestion.
resource "google_kms_key_ring" "regional" {
  for_each   = var.enable_cmek ? toset(local.regional_kms_locations) : toset([])
  name       = var.kms_key_ring
  location   = each.value
  depends_on = [google_project_service.apis]
}

resource "google_kms_crypto_key" "regional" {
  for_each = google_kms_key_ring.regional
  name     = "gemini-enterprise-connectors"
  key_ring = each.value.id
  purpose  = "ENCRYPT_DECRYPT"
  labels   = { usage = "gemini-enterprise-connectors", owner = "security" }
  lifecycle {
    prevent_destroy = true
  }
}

# 2.3 Seuls Gemini Enterprise et le stockage temporaire d'import peuvent utiliser les clés.
data "google_storage_project_service_account" "gcs" {}

locals {
  all_keys = var.enable_cmek ? merge(
    { main = google_kms_crypto_key.ge[0].id },
    { for loc, k in google_kms_crypto_key.regional : loc => k.id },
  ) : {}
  key_users = {
    gemini_enterprise = local.ge_sa
    storage           = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
  }
}

resource "google_kms_crypto_key_iam_member" "key_users" {
  for_each      = { for pair in setproduct(keys(local.all_keys), keys(local.key_users)) : "${pair[0]}|${pair[1]}" => { key = local.all_keys[pair[0]], member = local.key_users[pair[1]] } }
  crypto_key_id = each.value.key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value.member
  depends_on    = [terraform_data.service_agents]
}

# 2.4 Enregistrement de la clé dans Gemini Enterprise : AVANT toute app ou connecteur,
#     sinon ceux créés avant restent chiffrés par Google.
resource "google_discovery_engine_cmek_config" "ge" {
  count          = var.enable_cmek ? 1 : 0
  location       = var.ge_location
  cmek_config_id = "default-cmek"
  kms_key        = google_kms_crypto_key.ge[0].id
  set_default    = true

  dynamic "single_region_keys" {
    for_each = google_kms_crypto_key.regional
    content {
      kms_key = single_region_keys.value.id
    }
  }

  depends_on = [google_kms_crypto_key_iam_member.key_users]
}

# 2.5 Secrets des connecteurs : JAMAIS dans le code ni dans l'état Terraform.
#     L'équipe sécurité crée les secrets (valeurs) ; Terraform ne fait que les référencer
#     et autoriser Gemini Enterprise à les lire, secret par secret.
locals {
  secret_ids = toset(flatten([for c in var.connectors : values(c.secret_params)]))
}

data "google_secret_manager_secret" "connector" {
  for_each  = local.secret_ids
  secret_id = each.value
}

resource "google_secret_manager_secret_iam_member" "ge_reads" {
  for_each   = local.secret_ids
  secret_id  = data.google_secret_manager_secret.connector[each.value].id
  role       = "roles/secretmanager.secretAccessor"
  member     = local.ge_sa
  depends_on = [terraform_data.service_agents]
}
