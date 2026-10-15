# The Gemini Enterprise app: an "engine" of type INTRANET with the LLM add-on.
resource "google_discovery_engine_search_engine" "app" {
  location          = var.ge_location
  collection_id     = "default_collection"
  engine_id         = var.app_id
  display_name      = var.app_display_name
  industry_vertical = "GENERIC"
  app_type          = "APP_TYPE_INTRANET"
  data_store_ids    = [google_discovery_engine_data_store.docs.data_store_id]

  common_config {
    company_name = var.company_name
  }

  search_engine_config {
    search_tier                = "SEARCH_TIER_ENTERPRISE"
    search_add_ons             = ["SEARCH_ADD_ON_LLM"]
    required_subscription_tier = "SUBSCRIPTION_TIER_ENTERPRISE"
  }

  features = {
    "agent-sharing-without-admin-approval" = "FEATURE_STATE_OFF" # admins approve shared agents
    "disable-agent-sharing"                = "FEATURE_STATE_OFF"
    "enable-end-user-sharing-with-groups"  = "FEATURE_STATE_ON"
  }

  knowledge_graph_config {}
}

# The assistant = the chat brain of the app: instructions, grounding, and safety.
resource "google_discovery_engine_assistant" "default" {
  location           = var.ge_location
  collection_id      = "default_collection"
  engine_id          = google_discovery_engine_search_engine.app.engine_id
  assistant_id       = "default_assistant" # every app has exactly this one
  display_name       = "${var.app_display_name} assistant"
  description        = "Managed by Terraform (project 05)."
  web_grounding_type = var.web_grounding

  generation_config {
    default_language = var.assistant_language
    system_instruction {
      additional_system_instruction = var.assistant_instruction
    }
  }

  customer_policy {
    # Model Armor on every user prompt and every assistant answer.
    model_armor_config {
      user_prompt_template = google_model_armor_template.shield["prompt-shield"].id
      response_template    = google_model_armor_template.shield["response-shield"].id
      failure_mode         = "FAIL_CLOSED" # Model Armor down => block, never answer unscreened
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

  depends_on = [google_project_iam_member.armor_users]
}

# The web app users open: branding, shortcuts, UI features.
resource "google_discovery_engine_widget_config" "web" {
  location         = var.ge_location
  collection_id    = "default_collection"
  engine_id        = google_discovery_engine_search_engine.app.engine_id
  widget_config_id = "default_search_widget_config"

  access_settings {
    enable_web_app = true
    language_code  = var.assistant_language
  }

  ui_settings {
    interaction_type           = "SEARCH_WITH_FOLLOW_UPS"
    enable_autocomplete        = true
    enable_quality_feedback    = true # thumbs up/down
    enable_create_agent_button = true # users can build no-code agents
    generative_answer_config {
      ignore_adversarial_query = true
    }
  }

  dynamic "ui_branding" {
    for_each = var.logo_url == "" ? [] : [var.logo_url]
    content {
      logo {
        url = ui_branding.value
      }
    }
  }

  homepage_setting {
    shortcuts {
      title           = "Expense policy"
      destination_uri = "https://storage.cloud.google.com/${google_storage_bucket.docs.name}/expense-policy.txt"
    }
  }
}
