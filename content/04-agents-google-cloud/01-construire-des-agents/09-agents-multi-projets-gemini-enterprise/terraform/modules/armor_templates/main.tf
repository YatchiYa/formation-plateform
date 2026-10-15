# Une paire de templates Model Armor (questions / réponses), pour les agents qui n'ont pas encore ceux du projet 08.
# Réglages identiques à ceux du projet 08, en version « basic » (sans inspection DLP sur mesure).

terraform {
  required_providers {
    google = { source = "hashicorp/google" }
  }
}

variable "prefix" { type = string }   # ex. "trio-a2a" : deux piles dans le même projet ne se marchent pas dessus
variable "location" { type = string } # même localisation que l'app : "eu" pour une app eu

resource "google_model_armor_template" "shield" {
  for_each    = toset(["prompt", "response"])
  location    = var.location
  template_id = "${var.prefix}-${each.value}-shield"

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE"
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    rai_settings {
      dynamic "rai_filters" {
        for_each = ["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"]
        content {
          filter_type      = rai_filters.value
          confidence_level = "MEDIUM_AND_ABOVE"
        }
      }
    }
    sdp_settings {
      basic_config {
        filter_enforcement = "ENABLED"
      }
    }
  }

  template_metadata {
    enforcement_type        = "INSPECT_AND_BLOCK"
    log_template_operations = true
    multi_language_detection {
      enable_multi_language_detection = true
    }
  }
}

output "prompt" { value = google_model_armor_template.shield["prompt"].id }
output "response" { value = google_model_armor_template.shield["response"].id }
