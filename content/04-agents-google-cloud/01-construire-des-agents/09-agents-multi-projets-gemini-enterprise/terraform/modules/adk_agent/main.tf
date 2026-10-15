# Un agent ADK sur Agent Runtime, avec SA PROPRE identité (moindre privilège).
# Utilisé deux fois : l'agent stock (projet agents) et l'orchestrateur (projet GE).

terraform {
  required_providers {
    google   = { source = "hashicorp/google" }
    external = { source = "hashicorp/external" }
  }
}

variable "project" { type = string } # projet de l'agent (passé explicitement : connu dès le plan)
variable "name" { type = string }    # ex. "stock-agent" : aussi le nom affiché dans Agent Registry
variable "description" { type = string }
variable "source_dir" { type = string } # dossier contenant le package Python + requirements.txt
variable "entrypoint_module" { type = string }
variable "region" { type = string }
variable "armor_project" { type = string }
variable "env" { type = map(string) }    # variables d'environnement de l'agent
variable "roles" { type = list(string) } # rôles de l'agent sur SON projet
variable "source_include" {              # éléments de source_dir à envoyer (vide = tout) : seulement le code de CET agent
  type    = list(string)
  default = []
}
variable "secret_env" { # variables d'environnement lues dans Secret Manager : { NOM_VARIABLE = "nom-du-secret" } (projet de l'agent)
  type    = map(string)
  default = {}
}

resource "google_service_account" "agent" {
  account_id   = "${var.name}-sa"
  display_name = "Identité d'exécution de ${var.name}"
}

resource "google_project_iam_member" "agent" {
  for_each = toset(var.roles)
  project  = var.project
  role     = each.value
  member   = "serviceAccount:${google_service_account.agent.email}"
}

# Model Armor : les templates peuvent vivre dans un autre projet (le projet sécurité / GE).
resource "google_project_iam_member" "armor" {
  project = var.armor_project
  role    = "roles/modelarmor.user"
  member  = "serviceAccount:${google_service_account.agent.email}"
}

# L'agent peut lire SES secrets (clé d'API du modèle, par exemple), et seulement eux.
resource "google_secret_manager_secret_iam_member" "agent" {
  for_each  = var.secret_env
  project   = var.project
  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent.email}"
}

data "external" "source" {
  program = ["python3", "${path.module}/../../../scripts/pack.py"]
  query   = { src = var.source_dir, only = join(",", var.source_include) }
}

resource "google_vertex_ai_reasoning_engine" "agent" {
  display_name = var.name
  description  = var.description
  region       = var.region
  # FORCE : supprime aussi les sessions de l'agent. Sans cela, `terraform destroy` échoue dès que l'agent a servi
  # (« contains child resources: sessions », vérifié au premier déploiement).
  deletion_policy = "FORCE"

  spec {
    agent_framework = "google-adk"
    service_account = google_service_account.agent.email
    class_methods   = file("${path.module}/../../class_methods.json")

    source_code_spec {
      inline_source {
        source_archive = data.external.source.result.archive
      }
      python_spec {
        version           = "3.12"
        entrypoint_module = var.entrypoint_module
        entrypoint_object = "agent_runtime_app"
        requirements_file = "requirements.txt"
      }
    }

    deployment_spec {
      min_instances = 0
      max_instances = 2
      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }
      dynamic "secret_env" {
        for_each = var.secret_env
        content {
          name = secret_env.key
          secret_ref {
            secret  = secret_env.value
            version = "latest"
          }
        }
      }
    }
  }

  timeouts {
    create = "30m"
    update = "30m"
  }

  # Les droits doivent exister avant le démarrage (sinon : blocage, mode fermé).
  depends_on = [google_project_iam_member.agent, google_project_iam_member.armor, google_secret_manager_secret_iam_member.agent]
}

# name = chemin complet projects/P/locations/R/reasoningEngines/ID : ce qu'attendent Gemini Enterprise et le SDK.
# (l'attribut "name" de la ressource ne contient que l'ID : vérifié au premier déploiement)
output "name" { value = google_vertex_ai_reasoning_engine.agent.id }
output "engine_id" { value = google_vertex_ai_reasoning_engine.agent.name } # ID seul, pour les ressources IAM
output "service_account" { value = "serviceAccount:${google_service_account.agent.email}" }
