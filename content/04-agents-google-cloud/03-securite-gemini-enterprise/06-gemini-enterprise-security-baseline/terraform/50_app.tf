# L'APPLICATION Gemini Enterprise et son assistant.

resource "google_discovery_engine_search_engine" "app" {
  location          = var.ge_location
  collection_id     = "default_collection"
  engine_id         = var.app_id
  display_name      = var.app_display_name
  industry_vertical = "GENERIC"
  app_type          = "APP_TYPE_INTRANET" # = une app Gemini Enterprise
  data_store_ids    = concat(local.connector_data_store_ids, var.extra_data_store_ids)
  kms_key_name      = var.enable_cmek ? google_kms_crypto_key.ge[0].id : null
  features          = var.features

  common_config {
    company_name = var.company_name
  }

  search_engine_config {
    search_tier                = "SEARCH_TIER_ENTERPRISE"
    search_add_ons             = ["SEARCH_ADD_ON_LLM"]
    required_subscription_tier = "SUBSCRIPTION_TIER_ENTERPRISE"
  }

  depends_on = [google_discovery_engine_cmek_config.ge]
}

resource "google_discovery_engine_assistant" "default" {
  location           = var.ge_location
  collection_id      = "default_collection"
  engine_id          = google_discovery_engine_search_engine.app.engine_id
  assistant_id       = "default_assistant"
  display_name       = "${var.app_display_name} - assistant"
  web_grounding_type = var.web_grounding

  generation_config {
    default_language = "fr"
    system_instruction {
      additional_system_instruction = "Réponds à partir des données de l'entreprise et cite tes sources. Ne demande jamais de mot de passe, de numéro de sécurité sociale ou de coordonnées bancaires."
    }
  }

  customer_policy {
    model_armor_config {
      user_prompt_template = google_model_armor_template.shield["ge-prompt-shield"].id
      response_template    = google_model_armor_template.shield["ge-response-shield"].id
      failure_mode         = "FAIL_CLOSED" # Model Armor indisponible => refus, jamais de réponse non filtrée
    }
    dynamic "banned_phrases" {
      for_each = var.banned_phrases
      content {
        phrase            = banned_phrases.value
        match_type        = "WORD_BOUNDARY_STRING_MATCH"
        ignore_diacritics = true
      }
    }
  }

  depends_on = [google_project_iam_member.ge_uses_armor]
}

# Réglages de l'app que le provider Terraform n'expose pas encore : API REST v1alpha (version utilisée
# par la doc Google « Manage observability settings »), appelée
# à chaque changement de valeur. Conservation des conversations, observabilité sans
# contenu, et (option) Agent Gateway.
locals {
  engine_settings = merge(
    {
      sessionConfig       = { sessionTtl = { days = var.session_ttl_days } }
      observabilityConfig = { observabilityEnabled = var.enable_observability, sensitiveLoggingEnabled = var.enable_observability && var.log_prompts_responses }
    },
    var.enable_agent_gateway ? {
      agentGatewaySetting = { defaultEgressAgentGateway = { name = "projects/${local.project_number}/locations/${var.region}/agentGateways/${google_network_services_agent_gateway.egress[0].name}" } }
    } : {},
  )
}

resource "terraform_data" "engine_settings" {
  triggers_replace = [jsonencode(local.engine_settings), google_discovery_engine_search_engine.app.id]

  provisioner "local-exec" {
    command = <<-EOT
      curl -fsS -X PATCH \
        -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        -H "Content-Type: application/json" -H "X-Goog-User-Project: ${var.project_id}" \
        "https://${local.de_host}/v1alpha/${google_discovery_engine_search_engine.app.name}?updateMask=${join(",", keys(local.engine_settings))}" \
        -d '${jsonencode(local.engine_settings)}' >/dev/null && echo "engine settings applied"
    EOT
  }
}
