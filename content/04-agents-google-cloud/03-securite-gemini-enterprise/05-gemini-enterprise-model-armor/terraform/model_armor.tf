# Model Armor = a firewall for LLM text. A *template* is a set of filters:
#   - prompt injection & jailbreak      - malicious URLs
#   - responsible AI (hate, harassment, sexual, dangerous)
#   - sensitive data (credit cards, IDs, keys... via Sensitive Data Protection)
# We make two: one for what users send, one for what the model answers.

locals {
  templates = {
    prompt-shield = {
      purpose = "user prompts"
      message = "Your request was blocked by the company AI security policy (Model Armor)."
    }
    response-shield = {
      purpose = "model responses"
      message = "The answer was withheld by the company AI security policy (Model Armor)."
    }
  }
  rai_filters = ["HATE_SPEECH", "HARASSMENT", "SEXUALLY_EXPLICIT", "DANGEROUS"]
}

resource "google_model_armor_template" "shield" {
  for_each    = local.templates
  location    = var.armor_location
  template_id = each.key
  labels      = { purpose = replace(each.value.purpose, " ", "-") }

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
        for_each = local.rai_filters
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
    log_sanitize_operations = true # each screening decision goes to Cloud Logging
    log_template_operations = true
    multi_language_detection {
      enable_multi_language_detection = true # French prompts too
    }
    custom_prompt_safety_error_message       = each.value.message
    custom_llm_response_safety_error_message = each.value.message
  }

  depends_on = [google_project_service.apis]
}

# Who may call Model Armor with these templates.
resource "google_project_iam_member" "armor_users" {
  for_each = {
    gemini_enterprise = local.sa_discoveryengine # the GE assistant
    gemini_api        = local.sa_aiplatform      # the floor setting on Gemini calls
  }
  project    = var.project_id
  role       = "roles/modelarmor.user"
  member     = "serviceAccount:${each.value}"
  depends_on = [terraform_data.service_agents]
}

# Floor setting = the project-wide MINIMUM. Also screens every Gemini call made
# through Agent Platform in this project (all your agents), with no code change.
# Start with INSPECT_ONLY (log only), switch to INSPECT_AND_BLOCK once tuned.
resource "google_model_armor_floorsetting" "project" {
  parent   = "projects/${var.project_id}"
  location = "global"

  enable_floor_setting_enforcement = true # templates weaker than this are rejected
  integrated_services              = var.floor_setting_mode == "OFF" ? [] : ["AI_PLATFORM"]

  filter_config {
    pi_and_jailbreak_filter_settings {
      filter_enforcement = "ENABLED"
      confidence_level   = "MEDIUM_AND_ABOVE"
    }
    malicious_uri_filter_settings {
      filter_enforcement = "ENABLED"
    }
    rai_settings {
      rai_filters {
        filter_type      = "DANGEROUS"
        confidence_level = "MEDIUM_AND_ABOVE"
      }
    }
  }

  ai_platform_floor_setting {
    inspect_only         = var.floor_setting_mode == "INSPECT_ONLY"
    inspect_and_block    = var.floor_setting_mode == "INSPECT_AND_BLOCK"
    enable_cloud_logging = true
  }

  depends_on = [google_project_service.apis]
}

# Separation of duties: the security team owns the guardrails; Gemini
# Enterprise admins can't weaken them (agentspaceAdmin has no modelarmor.* rights).
resource "google_project_iam_member" "security_admins" {
  for_each = toset(var.security_admins)
  project  = var.project_id
  role     = "roles/modelarmor.admin"
  member   = each.value
}
