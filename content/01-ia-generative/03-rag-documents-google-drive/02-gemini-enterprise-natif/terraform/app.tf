# App Gemini Enterprise créée par ce kit (create_app = true) : intranet + IA générative. Sinon, rattachement des
# data stores à une app existante : scripts/rattacher.sh (une app créée ailleurs n'est pas gérée ici).
resource "google_discovery_engine_search_engine" "app" {
  count             = var.create_app ? 1 : 0
  location          = var.ge_location
  collection_id     = "default_collection"
  engine_id         = var.app_id != "" ? var.app_id : "${var.prefix}-app"
  display_name      = var.app_display_name
  industry_vertical = "GENERIC"
  app_type          = "APP_TYPE_INTRANET"
  data_store_ids    = local.data_store_ids
  common_config {
    company_name = var.company_name
  }
  search_engine_config {
    search_tier                = "SEARCH_TIER_ENTERPRISE"
    search_add_ons             = ["SEARCH_ADD_ON_LLM"]
    required_subscription_tier = "SUBSCRIPTION_TIER_ENTERPRISE"
  }
  lifecycle {
    ignore_changes = [data_store_ids] # Drive / OneDrive ajoutés hors Terraform : scripts/rattacher.sh
  }
}
