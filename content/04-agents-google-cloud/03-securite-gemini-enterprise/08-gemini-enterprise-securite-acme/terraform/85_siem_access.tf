# NOTE §4 - JOURNAUX VERS LE SOC, ET CONTRÔLE DES ACCÈS DE GOOGLE.

# 4.1 Export SIEM : les mêmes journaux de sécurité que le bucket ge-security
#     partent en temps réel vers Pub/Sub ; le SIEM (Splunk, Chronicle, Sentinel...)
#     consomme l'abonnement. Pas de contenu utilisateur sauf si Model Armor le journalise.
resource "google_pubsub_topic" "siem" {
  count                      = var.enable_siem_export ? 1 : 0
  name                       = "ge-security-siem"
  message_retention_duration = "604800s" # 7 jours de rattrapage si le SIEM est indisponible
  # ponytail: chiffrement Google par défaut (messages éphémères, 7 j). CMEK possible :
  # kms_key_name + roles/cloudkms.cryptoKeyEncrypterDecrypter pour le service agent Pub/Sub.
  depends_on = [google_project_service.apis]
}

resource "google_pubsub_subscription" "siem" {
  count                      = var.enable_siem_export ? 1 : 0
  name                       = "ge-security-siem-pull"
  topic                      = google_pubsub_topic.siem[0].id
  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
  expiration_policy {
    ttl = "" # ne jamais expirer, même sans lecteur
  }
}

resource "google_logging_project_sink" "siem" {
  count                  = var.enable_siem_export ? 1 : 0
  name                   = "ge-security-to-siem"
  destination            = "pubsub.googleapis.com/${google_pubsub_topic.siem[0].id}"
  filter                 = local.security_log_filter
  unique_writer_identity = true
}

# Le "writer" du sink (compte géré par Google) publie dans le topic.
resource "google_pubsub_topic_iam_member" "siem_writer" {
  count  = var.enable_siem_export ? 1 : 0
  topic  = google_pubsub_topic.siem[0].id
  role   = "roles/pubsub.publisher"
  member = google_logging_project_sink.siem[0].writer_identity
}

resource "google_pubsub_subscription_iam_member" "siem_reader" {
  count        = var.enable_siem_export && var.siem_subscriber != "" ? 1 : 0
  subscription = google_pubsub_subscription.siem[0].id
  role         = "roles/pubsub.subscriber"
  member       = var.siem_subscriber
}

# 4.2 Access Approval : tout accès d'un ingénieur Google à vos données (support)
#     attend VOTRE approbation. Prérequis : Access Transparency activé sur
#     l'organisation (console, IAM & Admin > Access Transparency), qui exige un
#     support Enhanced/Premium. 'all' enrôle tous les services éligibles, dont
#     Gemini Enterprise, Agent Runtime, Model Armor et Cloud KMS (GA).
resource "google_project_access_approval_settings" "this" {
  count               = length(var.access_approval_emails) > 0 ? 1 : 0
  project_id          = var.project_id
  notification_emails = var.access_approval_emails

  enrolled_services {
    cloud_product = "all"
  }
  depends_on = [google_project_service.apis]
}
