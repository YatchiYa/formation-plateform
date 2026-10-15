# ---------------------------------------------------------------------------
# 6. Garde-fous : Model Armor, résidence UE, budget
# ---------------------------------------------------------------------------
# Modèle Model Armor appelé par l'assistant avant et après Gemini.
resource "google_model_armor_template" "assistant" {
  project     = var.project_id
  location    = var.region
  template_id = "${var.prefix}-assistant"

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE"
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    sdp_settings {
      basic_config {
        filter_enforcement = "ENABLED" # données sensibles (cartes, identifiants...)
      }
    }
    rai_settings {
      rai_filters {
        filter_type      = "HARASSMENT"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "HATE_SPEECH"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
      rai_filters {
        filter_type      = "SEXUALLY_EXPLICIT"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
    }
  }

  template_metadata {
    log_sanitize_operations = true
  }

  depends_on = [google_project_service.apis]
}

# Contrainte d'organisation : aucune ressource hors des régions UE dans ce projet.
resource "google_org_policy_policy" "eu_only" {
  count  = var.enforce_eu_location_policy ? 1 : 0
  name   = "projects/${var.project_id}/policies/gcp.resourceLocations"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      values {
        allowed_values = ["in:eu-locations"]
      }
    }
  }
}

# Budget mensuel avec alertes à 50, 90 et 100 % (alerte, pas plafond !).
resource "google_billing_budget" "ai" {
  count           = var.billing_account == null ? 0 : 1
  billing_account = var.billing_account
  display_name    = "${var.prefix}-budget"

  budget_filter {
    projects = ["projects/${local.number}"]
  }

  amount {
    specified_amount {
      currency_code = "EUR"
      units         = tostring(var.monthly_budget_eur)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.9, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }
}
