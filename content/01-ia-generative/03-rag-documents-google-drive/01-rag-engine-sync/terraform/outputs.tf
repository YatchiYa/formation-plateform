output "url" {
  description = "URL du service (privé : passer par le proxy)."
  value       = google_cloud_run_v2_service.app.uri
}

output "ouvrir_interface" {
  description = "Commande pour ouvrir l'interface sur http://localhost:8080."
  value       = "gcloud run services proxy ${google_cloud_run_v2_service.app.name} --region=${var.region} --project=${var.project_id} --port=8080"
}

output "partager_drive_avec" {
  description = "Les 2 adresses à ajouter (Lecteur) au partage de chaque dossier Drive."
  value       = [google_service_account.kit.email, trimprefix(local.rag_agent, "serviceAccount:")]
}

output "corpus" {
  value = google_vertex_ai_rag_corpus.docs.id
}

output "bucket" {
  value = google_storage_bucket.docs.name
}

output "image" {
  value = local.image
}

output "hook_url" {
  description = "Adresse des notifications push Drive (vide si push = false)."
  value       = var.push ? "${google_cloud_run_v2_service.hook[0].uri}/hook/drive" : ""
}

output "oauth_redirect_uri" {
  description = "URI de redirection à déclarer dans le client OAuth (console)."
  value       = "http://localhost:8080/auth/google/callback"
}
