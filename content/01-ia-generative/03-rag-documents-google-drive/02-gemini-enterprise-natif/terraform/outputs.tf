output "data_stores" {
  description = "Data stores créés (à rattacher à l'app : scripts/rattacher.sh)."
  value       = local.data_store_ids
}

output "bucket_depots" {
  value = var.depots ? google_storage_bucket.depots[0].name : ""
}

output "app" {
  value = var.create_app ? google_discovery_engine_search_engine.app[0].engine_id : var.app_id
}

output "console_app" {
  value = "https://console.cloud.google.com/gemini-enterprise/apps?project=${var.project_id}"
}
