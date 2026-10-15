output "app_service_account" {
  description = "Identité de l'assistant (à vérifier avec check_posture.py)."
  value       = google_service_account.app.email
}

output "cloud_run_service" {
  description = "Nom du service Cloud Run (non joignable en direct)."
  value       = google_cloud_run_v2_service.app.name
}

output "lb_ip" {
  description = "IP publique du load balancer : créez l'enregistrement DNS A de app_domain vers elle."
  value       = local.with_lb ? google_compute_global_address.lb[0].address : null
}

output "cmek_key" {
  description = "Clé CMEK à passer aux ressources Vertex AI (encryption_spec.kms_key_name)."
  value       = google_kms_crypto_key.ai.id
}

output "kb_bucket" {
  description = "Bucket des documents de l'assistant."
  value       = google_storage_bucket.kb.name
}

output "model_armor_template" {
  description = "Modèle Model Armor à appeler avant et après Gemini."
  value       = google_model_armor_template.assistant.id
}

output "psc_endpoint" {
  description = "IP privée qui représente les API Google dans le VPC."
  value       = var.psc_ip
}
