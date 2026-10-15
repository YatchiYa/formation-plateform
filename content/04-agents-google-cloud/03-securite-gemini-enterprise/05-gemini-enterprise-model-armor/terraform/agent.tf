# A custom ADK agent on Agent Runtime, added to the Gemini Enterprise app.
# Gemini Enterprise does NOT run Model Armor on custom agents, so the agent
# screens itself (ModelArmorPlugin) with the same two templates.

# Dedicated identity for THIS agent (least privilege). Not the shared Agent
# Runtime service agent: granting Model Armor/Gemini to that one would grant it
# to every agent in the project.
resource "google_service_account" "expense_agent" {
  account_id   = "expense-agent-sa"
  display_name = "Runtime identity of the expense agent"
}

resource "google_project_iam_member" "expense_agent" {
  for_each = toset([
    "roles/aiplatform.user",         # call Gemini + its own Agent Runtime sessions
    "roles/modelarmor.user",         # screen prompts/answers (ModelArmorPlugin)
    "roles/logging.logWriter",       # logs
    "roles/monitoring.metricWriter", # metrics
    "roles/cloudtrace.agent",        # traces
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.expense_agent.email}"
}

data "external" "agent_source" {
  program = ["python3", "${path.module}/../scripts/pack.py"]
  query   = { src = abspath("${path.module}/../agent") }
}

resource "google_vertex_ai_reasoning_engine" "expense_agent" {
  display_name = "expense-agent"
  description  = "Checks expenses against the company policy. Screened by Model Armor."
  region       = var.region

  spec {
    agent_framework = "google-adk"
    service_account = google_service_account.expense_agent.email
    class_methods   = file("${path.module}/class_methods.json")

    source_code_spec {
      inline_source {
        source_archive = data.external.agent_source.result.archive
      }
      python_spec {
        version           = "3.12"
        entrypoint_module = "expense_agent.agent"
        entrypoint_object = "agent_runtime_app"
        requirements_file = "requirements.txt"
      }
    }

    deployment_spec {
      min_instances = 0
      max_instances = 2
      env {
        name  = "MODEL"
        value = var.model
      }
      env {
        name  = "PROMPT_TEMPLATE"
        value = google_model_armor_template.shield["prompt-shield"].id
      }
      env {
        name  = "RESPONSE_TEMPLATE"
        value = google_model_armor_template.shield["response-shield"].id
      }
    }
  }

  timeouts {
    create = "30m"
    update = "30m"
  }

  # Roles must exist before the agent starts, or its first calls are blocked (fail closed).
  depends_on = [google_project_service.apis, google_project_iam_member.expense_agent]
}

# Register the agent in the app (no Terraform resource yet => REST via a script).
# Re-registers if the agent changes; unregisters on destroy.
resource "terraform_data" "register_agent" {
  input = {
    project_id   = var.project_id
    host         = local.de_host
    parent       = "projects/${var.project_id}/locations/${var.ge_location}/collections/default_collection/engines/${google_discovery_engine_search_engine.app.engine_id}/assistants/default_assistant"
    agent        = google_vertex_ai_reasoning_engine.expense_agent.name
    display_name = "Expense policy checker"
    description  = "Tells you whether an expense fits the company policy and the limit per category."
    script       = abspath("${path.module}/../scripts/register_agent.sh")
  }

  provisioner "local-exec" {
    command     = "${self.input.script} create"
    environment = { for k, v in self.input : upper(k) => v if k != "script" }
  }

  provisioner "local-exec" {
    when        = destroy
    command     = "${self.input.script} delete"
    environment = { for k, v in self.input : upper(k) => v if k != "script" }
  }

  depends_on = [google_discovery_engine_assistant.default]
}
