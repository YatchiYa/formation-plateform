# CONNECTEURS - un modèle générique : chaque entrée de var.connectors devient une source.
# Par défaut en FEDERATED : la question est envoyée en direct à la source avec le
# jeton de l'utilisateur => aucune copie chez Google, les droits de la source s'appliquent.

resource "google_discovery_engine_data_connector" "src" {
  for_each = var.connectors

  location                = var.ge_location
  collection_id           = each.key
  collection_display_name = each.value.display_name
  data_source             = each.value.data_source
  connector_modes         = each.value.modes
  refresh_interval        = each.value.refresh_interval
  static_ip_enabled       = each.value.static_ip

  # Paramètres : les valeurs secrètes sont des RÉFÉRENCES Secret Manager, jamais des valeurs.
  json_params = jsonencode(merge(
    each.value.params,
    { for k, s in each.value.secret_params : k => "${data.google_secret_manager_secret.connector[s].name}/versions/latest" },
  ))

  # CMEK : seules les données COPIÉES (ingestion) sont chiffrées avec la clé du client.
  kms_key_name = var.enable_cmek && contains(each.value.modes, "DATA_INGESTION") ? google_kms_crypto_key.ge[0].id : null

  dynamic "entities" {
    for_each = each.value.entities
    content {
      entity_name = entities.value.name
      params      = entities.value.params
    }
  }

  depends_on = [
    google_discovery_engine_acl_config.identity,
    google_discovery_engine_cmek_config.ge, # la clé doit être enregistrée AVANT
    google_secret_manager_secret_iam_member.ge_reads,
  ]
}

locals {
  # Chaque entité d'un connecteur produit un data store "<collection>_<entité>".
  connector_data_store_ids = flatten([
    for c in google_discovery_engine_data_connector.src : [
      for e in c.entities : basename(e.data_store) if try(e.data_store != null && e.data_store != "", false)
    ]
  ])
}
