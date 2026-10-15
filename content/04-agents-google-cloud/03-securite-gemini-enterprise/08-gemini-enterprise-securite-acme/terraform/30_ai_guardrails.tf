# COUCHE 3 - FILTRAGE IA : Model Armor sur chaque question et chaque réponse.

# 3.1 Détecteurs de données sensibles adaptés à la France (mode advanced).
resource "google_data_loss_prevention_inspect_template" "fr" {
  count        = var.sdp_mode == "advanced" ? 1 : 0
  parent       = "projects/${var.project_id}/locations/${var.dlp_location}"
  template_id  = "ge-donnees-sensibles-fr"
  display_name = "Gemini Enterprise - données sensibles FR/UE"
  description  = "Identifiants français, données bancaires, secrets techniques."

  inspect_config {
    min_likelihood = "LIKELY" # évite les faux positifs sur des nombres quelconques
    dynamic "info_types" {
      for_each = var.sensitive_info_types
      content {
        name = info_types.value
      }
    }
  }
  depends_on = [google_project_service.apis]
}

# Le service agent Model Armor lit le template DLP.
resource "google_project_iam_member" "armor_reads_dlp" {
  for_each   = var.sdp_mode == "advanced" ? toset(["roles/dlp.user", "roles/dlp.reader"]) : toset([])
  project    = var.project_id
  role       = each.value
  member     = "serviceAccount:service-${local.project_number}@gcp-sa-modelarmor.iam.gserviceaccount.com"
  depends_on = [terraform_data.service_agents]
}

# 3.2 Deux templates : un pour les questions (entrée), un pour les réponses (sortie).
resource "google_model_armor_template" "shield" {
  for_each    = toset(["ge-prompt-shield", "ge-response-shield"])
  location    = var.ge_location # app 'eu' => templates 'eu'
  template_id = each.value
  labels      = { app = var.app_id, owner = "security" }

  filter_config {
    # Injection de prompt / jailbreak : "ignore tes instructions...".
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = var.armor_confidence
    }
    # Liens de phishing / malware connus (256 premières URL).
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    # IA responsable : haine, harcèlement, sexuel explicite, dangereux.
    rai_settings {
      dynamic "rai_filters" {
        for_each = ["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"]
        content {
          filter_type      = rai_filters.value
          confidence_level = var.armor_confidence
        }
      }
    }
    # Données sensibles : détecteurs FR (advanced) ou détecteurs Google par défaut (basic).
    sdp_settings {
      dynamic "advanced_config" {
        for_each = var.sdp_mode == "advanced" ? [1] : []
        content {
          inspect_template = google_data_loss_prevention_inspect_template.fr[0].id
        }
      }
      dynamic "basic_config" {
        for_each = var.sdp_mode == "basic" ? [1] : []
        content {
          filter_enforcement = "ENABLED"
        }
      }
    }
  }

  template_metadata {
    enforcement_type        = "INSPECT_AND_BLOCK"
    log_template_operations = true                     # QUI modifie les filtres : toujours tracé
    log_sanitize_operations = var.log_screened_content # le CONTENU filtré : non par défaut (RGPD)
    multi_language_detection {
      enable_multi_language_detection = true # français testé par Google
    }
  }

  depends_on = [google_project_service.apis, google_project_iam_member.armor_reads_dlp]
}

# 3.3 Gemini Enterprise est autorisé à appeler Model Armor.
resource "google_project_iam_member" "ge_uses_armor" {
  project    = var.project_id
  role       = "roles/modelarmor.user"
  member     = local.ge_sa
  depends_on = [terraform_data.service_agents]
}

# 3.4 Plancher (floor setting) : personne ne peut créer ou modifier un template
#     moins strict que ce minimum, même un administrateur pressé.
resource "google_model_armor_floorsetting" "project" {
  parent                           = "projects/${var.project_id}"
  location                         = "global"
  enable_floor_setting_enforcement = true

  # Projet 08 (note §1 et §3) : le plancher s'applique AUSSI à chaque appel Gemini
  # fait dans le projet (agents ADK sur Agent Runtime, scripts, notebooks).
  # C'est la seule protection Model Armor native pour les agents personnalisés :
  # celle de Gemini Enterprise ne les couvre pas. 'inspect' d'abord, puis 'block'.
  integrated_services = var.armor_agent_platform_mode == "off" ? [] : ["AI_PLATFORM"]

  dynamic "ai_platform_floor_setting" {
    for_each = var.armor_agent_platform_mode == "off" ? [] : [1]
    content {
      inspect_only         = var.armor_agent_platform_mode == "inspect"
      inspect_and_block    = var.armor_agent_platform_mode == "block"
      enable_cloud_logging = true # verdicts seulement visibles si journalisés : indispensable en phase 'inspect'
    }
  }

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "HIGH" # minimum absolu ; les templates sont plus stricts (MEDIUM)
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    rai_settings {
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = "HIGH"
      }
    }
  }

  floor_setting_metadata {
    multi_language_detection {
      enable_multi_language_detection = true
    }
  }

  depends_on = [google_project_service.apis]
}
