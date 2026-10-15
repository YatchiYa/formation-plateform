# NOTE §1, §9, §10 - AGENTS PERSONNALISÉS ET CATALOGUE.
#
#  §10 Agent Registry = l'inventaire officiel : un agent/outil non enregistré
#      n'est pas joignable via Agent Gateway (deny par défaut) et déclenche
#      l'alerte Shadow AI (75_shadow_ai.tf).
#  §1  Agents sur Agent Runtime (géré, identité dédiée, journaux, Model Armor).
#  §9  Validation humaine des actions : dans le code de l'agent (require_confirmation).

# 10.1 Qui lit / qui publie dans le catalogue.
resource "google_project_iam_member" "registry_viewers" {
  for_each = toset(var.user_groups)
  project  = var.project_id
  role     = "roles/agentregistry.viewer"
  member   = each.value
}

resource "google_project_iam_member" "registry_editors" {
  for_each = toset(var.agent_developer_groups)
  project  = var.project_id
  role     = "roles/agentregistry.editor"
  member   = each.value
}

# 1.1 Identité dédiée de l'agent : jamais le compte de service partagé Agent Runtime
#     (un droit donné à celui-ci vaudrait pour TOUS les agents du projet).
resource "google_service_account" "secure_agent" {
  count        = var.deploy_secure_agent ? 1 : 0
  account_id   = "secure-agent-sa"
  display_name = "Identité d'exécution de l'agent service client"
}

resource "google_project_iam_member" "secure_agent" {
  for_each = var.deploy_secure_agent ? toset([
    "roles/aiplatform.user", # Gemini + ses propres sessions
    "roles/modelarmor.user", # filtrage (ModelArmorPlugin)
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
  ]) : toset([])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.secure_agent[0].email}"
}

data "external" "agent_source" {
  count   = var.deploy_secure_agent ? 1 : 0
  program = ["python3", "${path.module}/../scripts/pack.py"]
  query   = { src = abspath("${path.module}/../agent") }
}

resource "google_vertex_ai_reasoning_engine" "secure_agent" {
  count        = var.deploy_secure_agent ? 1 : 0
  display_name = "service-client-securise"
  description  = "Commandes et remboursements. Model Armor + validation humaine."
  region       = var.region

  spec {
    agent_framework = "google-adk"
    service_account = google_service_account.secure_agent[0].email
    class_methods   = file("${path.module}/class_methods.json")

    source_code_spec {
      inline_source {
        source_archive = data.external.agent_source[0].result.archive
      }
      python_spec {
        version           = "3.12"
        entrypoint_module = "secure_agent.agent"
        entrypoint_object = "agent_runtime_app"
        requirements_file = "requirements.txt"
      }
    }

    deployment_spec {
      min_instances = 0
      max_instances = 2
      env {
        name  = "MODEL"
        value = var.agent_model
      }
      env {
        name  = "PROMPT_TEMPLATE"
        value = google_model_armor_template.shield["ge-prompt-shield"].id
      }
      env {
        name  = "RESPONSE_TEMPLATE"
        value = google_model_armor_template.shield["ge-response-shield"].id
      }

      # §5 : les appels SORTANTS de l'agent passent par Agent Gateway
      #      (seuls les outils/agents enregistrés dans Agent Registry sont joignables).
      dynamic "agent_gateway_config" {
        for_each = var.enable_agent_gateway ? [1] : []
        content {
          agent_to_anywhere_config {
            agent_gateway = google_network_services_agent_gateway.egress[0].id
          }
        }
      }
    }
  }

  timeouts {
    create = "30m"
    update = "30m"
  }

  depends_on = [google_project_service.apis, google_project_iam_member.secure_agent]
}

# Publication dans l'app Gemini Enterprise (pas encore de ressource Terraform : REST).
resource "terraform_data" "register_agent" {
  count = var.deploy_secure_agent ? 1 : 0
  input = {
    project_id   = var.project_id
    host         = local.de_host
    parent       = "projects/${var.project_id}/locations/${var.ge_location}/collections/default_collection/engines/${google_discovery_engine_search_engine.app.engine_id}/assistants/default_assistant"
    agent        = google_vertex_ai_reasoning_engine.secure_agent[0].name
    display_name = "Service client (sécurisé)"
    description  = "Consulte les commandes ; prépare des remboursements validés par un humain."
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
