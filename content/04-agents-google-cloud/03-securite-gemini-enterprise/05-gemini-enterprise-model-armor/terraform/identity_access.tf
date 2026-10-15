# 1. Identity: Gemini Enterprise users sign in with their Google Workspace
#    account (GSUITE). Use THIRD_PARTY + a workforce pool for Entra ID / Okta.
resource "google_discovery_engine_acl_config" "identity" {
  location = var.ge_location
  idp_config {
    idp_type = "GSUITE"
  }
  depends_on = [google_project_service.apis]
}

# 2. Licences (optional, BILLED): a subscription for N users...
resource "google_discovery_engine_license_config" "licenses" {
  count             = var.license_count > 0 ? 1 : 0
  location          = var.ge_location
  license_config_id = "${var.app_id}-licenses"
  license_count     = var.license_count
  subscription_tier = "SUBSCRIPTION_TIER_ENTERPRISE"
  subscription_term = "SUBSCRIPTION_TERM_ONE_MONTH"
  free_trial        = var.license_free_trial
  auto_renew        = false

  start_date {
    year  = tonumber(split("-", var.license_start_date)[0])
    month = tonumber(split("-", var.license_start_date)[1])
    day   = tonumber(split("-", var.license_start_date)[2])
  }

  depends_on = [google_discovery_engine_acl_config.identity]
}

# ...automatically assigned to each user on their first visit.
resource "google_discovery_engine_user_store" "default" {
  count                        = var.license_count > 0 ? 1 : 0
  location                     = var.ge_location
  user_store_id                = "default_user_store"
  default_license_config       = google_discovery_engine_license_config.licenses[0].id
  enable_license_auto_register = true
}

# 3. Access: who can open the app / who administers it.
resource "google_project_iam_member" "users" {
  for_each = toset(var.users)
  project  = var.project_id
  role     = "roles/discoveryengine.user"
  member   = each.value
}

resource "google_project_iam_member" "admins" {
  for_each = toset(var.admins)
  project  = var.project_id
  role     = "roles/discoveryengine.agentspaceAdmin" # "Gemini Enterprise Admin"
  member   = each.value
}
