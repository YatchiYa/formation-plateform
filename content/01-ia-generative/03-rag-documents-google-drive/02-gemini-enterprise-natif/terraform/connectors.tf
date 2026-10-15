# Connecteurs Gemini Enterprise gérés par Terraform. Seule forme documentée par Google pour vos sources :
# SharePoint en recherche fédérée (data_source = "sharepoint_federated_search") — voir config/exemple.env.
# Google Drive (fédéré, Workspace) et OneDrive (ingestion) : console ou API (scripts/, docs/03 et 04).
data "google_secret_manager_secret" "connector" {
  for_each  = toset(flatten([for c in var.connectors : values(c.secret_params)]))
  secret_id = each.value
}

resource "google_secret_manager_secret_iam_member" "ge_reads" {
  for_each   = data.google_secret_manager_secret.connector
  secret_id  = each.value.id
  role       = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${local.ge_agent}"
  depends_on = [terraform_data.service_agent]
}

resource "google_discovery_engine_data_connector" "src" {
  for_each                = var.connectors
  location                = var.ge_location
  collection_id           = "${var.prefix}-${each.key}"
  collection_display_name = each.value.display_name
  data_source             = each.value.data_source
  connector_modes         = each.value.modes
  refresh_interval        = each.value.refresh_interval
  json_params = jsonencode(merge(each.value.params,
  { for k, s in each.value.secret_params : k => "${data.google_secret_manager_secret.connector[s].name}/versions/latest" }))
  dynamic "entities" {
    for_each = each.value.entities
    content {
      entity_name = entities.value.name
      params      = entities.value.params
    }
  }
  lifecycle {
    ignore_changes = [collection_display_name, entities, refresh_interval] # comme l'exemple officiel
  }
  depends_on = [google_secret_manager_secret_iam_member.ge_reads]
}

locals {
  connector_data_stores = flatten([for c in google_discovery_engine_data_connector.src :
  [for e in c.entities : basename(e.data_store) if try(e.data_store != null && e.data_store != "", false)]])
  data_store_ids = concat(var.depots ? [google_discovery_engine_data_store.depots[0].data_store_id] : [], local.connector_data_stores)
}
