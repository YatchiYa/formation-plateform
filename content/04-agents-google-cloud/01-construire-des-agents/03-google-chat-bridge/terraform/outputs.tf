output "url" {
  description = "Paste this as the HTTP endpoint URL in Chat API > Configuration."
  value       = google_cloud_run_v2_service.bridge.uri
}

output "chat_config_console" {
  description = "Where to finish the Chat app setup (console-only step)."
  value       = "https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat?project=${var.project_id}"
}
