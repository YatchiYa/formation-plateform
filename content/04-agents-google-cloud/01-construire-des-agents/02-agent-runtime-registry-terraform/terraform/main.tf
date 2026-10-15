# 1. APIs ---------------------------------------------------------------------
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",           # Agent Platform: Agent Runtime + Gemini
    "agentregistry.googleapis.com",        # Agent Registry
    "cloudresourcemanager.googleapis.com", # needed by Agent Runtime deploys
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "telemetry.googleapis.com",
  ])
  service            = each.value
  disable_on_destroy = false
}

# 2. Package the agent source -------------------------------------------------
# Runs scripts/pack.py on every plan. Same code => same archive => no redeploy.
data "external" "agent_source" {
  program = ["python3", "${path.module}/../scripts/pack.py"]
  query   = { src = abspath("${path.module}/../agent") }
}

# 3. The agent on Agent Runtime (a.k.a. Agent Engine / ReasoningEngine) -------
# Agent Runtime builds a container from the source, installs requirements.txt,
# imports currency_agent.agent and serves the `app` object.
# It is registered in Agent Registry automatically.
resource "google_vertex_ai_reasoning_engine" "agent" {
  display_name = var.display_name
  description  = "Converts amounts between currencies. Built with ADK, deployed with Terraform."
  region       = var.region

  spec {
    agent_framework = "google-adk"

    # Terraform can't introspect the Python object, so the API methods are
    # declared by hand. Without them, clients can't call the agent.
    class_methods = file("${path.module}/class_methods.json")

    # No service_account => runs as the "Reasoning Engine Service Agent",
    # which already has what it needs. See README for custom SA / Agent Identity.

    source_code_spec {
      inline_source {
        source_archive = data.external.agent_source.result.archive
      }
      python_spec {
        version           = "3.12"
        entrypoint_module = "currency_agent.agent"
        entrypoint_object = "app"
        requirements_file = "requirements.txt"
      }
    }

    deployment_spec {
      min_instances = 0 # scale to zero when idle
      max_instances = 2

      env {
        name  = "MODEL"
        value = var.model
      }
    }
  }

  timeouts {
    create = "30m"
    update = "30m"
  }

  depends_on = [google_project_service.apis]
}
