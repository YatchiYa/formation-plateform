# Projet 10 : les serveurs MCP Google Sheets et Google Slides (Cloud Run privés), l'agent qui l'utilise (A2A sur Cloud Run, et/ou Agent
# Runtime), leur entrée dans Agent Registry, et les droits du compte de Gemini Enterprise. Même résultat que
# scripts/deployer.sh (preparer, mcp, agent, agent-runtime, registre, droits-app). Guide : docs/10-3.

locals {
  racine = abspath("${path.module}/..")
  num    = var.project_number
  depot  = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
  # Les serveurs MCP : UNE image, un service par produit (PRODUIT choisit les outils). Adresses connues d'avance.
  produits = { for p in var.produits_mcp : p => "https://${p}-mcp-${local.num}.${var.region}.run.app/mcp" }
  mcp_url  = lookup(local.produits, "sheets", "")
  # L'agent reçoit l'adresse de chaque serveur MCP déployé (au moins un) : MCP_URL (Sheets), MCP_SLIDES_URL (Slides).
  env_mcp = merge(contains(var.produits_mcp, "sheets") ? { MCP_URL = local.produits["sheets"] } : {},
  contains(var.produits_mcp, "slides") ? { MCP_SLIDES_URL = local.produits["slides"] } : {})
  agent_url = "https://sheets-agent-${local.num}.${var.region}.run.app"
  # Étiquette d'image = empreinte du code : code inchangé => même image => rien à redéployer.
  empreinte = { for d in ["mcp_server", "agent"] : d => substr(sha1(join("", [
    for f in sort(fileset("${local.racine}/${d}", "**")) : filesha1("${local.racine}/${d}/${f}")
    if !strcontains(f, "__pycache__") && !strcontains(f, ".adk/")
  ])), 0, 12) }
  image_mcp   = "${local.depot}/mcp-google:${local.empreinte["mcp_server"]}"
  image_agent = "${local.depot}/sheets-agent:${local.empreinte["agent"]}"
  ge_sa       = var.ge_project_number == "" ? "" : "serviceAccount:service-${var.ge_project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

# 1. API -------------------------------------------------------------------------------------------------------------
resource "google_project_service" "apis" {
  # cloudresourcemanager : Terraform lit et modifie les rôles IAM du projet par cette API (refus sur un projet neuf sinon).
  for_each = toset(concat(["cloudresourcemanager.googleapis.com", "run.googleapis.com", "cloudbuild.googleapis.com", "artifactregistry.googleapis.com",
    "iam.googleapis.com", "logging.googleapis.com", "sheets.googleapis.com", "slides.googleapis.com", "drive.googleapis.com", "aiplatform.googleapis.com"],
  var.register_in_agent_registry ? ["agentregistry.googleapis.com"] : []))
  service            = each.value
  disable_on_destroy = false
}

# 2. Comptes de service ----------------------------------------------------------------------------------------------
resource "google_service_account" "build" {
  account_id   = "sheets-build-sa"
  display_name = "Construction des images du projet 10 (Cloud Build)"
  depends_on   = [google_project_service.apis]
}
resource "google_project_iam_member" "build" {
  for_each   = toset(["roles/storage.objectViewer", "roles/artifactregistry.writer", "roles/logging.logWriter"])
  project    = var.project_id
  role       = each.value
  member     = google_service_account.build.member
  depends_on = [google_project_service.apis]
}
resource "google_service_account" "mcp" { # AUCUN rôle : il n'agit qu'avec le jeton de l'utilisateur
  account_id   = "sheets-mcp-sa"
  display_name = "Serveur MCP Google Sheets : AUCUN rôle (agit avec le jeton de l'utilisateur)"
  depends_on   = [google_project_service.apis]
}
resource "google_service_account" "agent" {
  account_id   = "sheets-agent-sa"
  display_name = "Agent Assistant Google Sheets (Cloud Run et Agent Runtime)"
  depends_on   = [google_project_service.apis]
}
resource "google_project_iam_member" "agent" {
  for_each   = toset(["roles/aiplatform.user", "roles/logging.logWriter"])
  project    = var.project_id
  role       = each.value
  member     = google_service_account.agent.member
  depends_on = [google_project_service.apis]
}

# 3. Images, construites par Cloud Build (pas de Docker sur le poste) ------------------------------------------------
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = "sheets-mcp"
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}
resource "terraform_data" "image" {
  for_each         = { mcp_server = local.image_mcp, agent = local.image_agent }
  triggers_replace = each.value
  provisioner "local-exec" {
    interpreter = ["bash", "-c"]
    command     = <<-EOT
      for essai in 1 2 3 4; do   # compte de construction tout neuf : refusé 1 à 2 minutes
        gcloud builds submit "${local.racine}/${each.key}" --config="${local.racine}/cloudbuild.yaml" \
          --substitutions="_IMAGE=${each.value}" --region=${var.region} --project=${var.project_id} \
          --service-account=${google_service_account.build.id} && exit 0
        sleep 40
      done
      exit 1
    EOT
  }
  depends_on = [google_project_iam_member.build, google_artifact_registry_repository.images]
}

# 4. Les serveurs MCP (Sheets, Slides), PRIVÉS ------------------------------------------------------------------------
moved { # un déploiement fait avant l'ajout de Slides : le service Sheets est gardé tel quel (pas de destruction)
  from = google_cloud_run_v2_service.mcp
  to   = google_cloud_run_v2_service.mcp["sheets"]
}
resource "google_cloud_run_v2_service" "mcp" {
  for_each            = local.produits
  name                = "${each.key}-mcp"
  location            = var.region
  deletion_protection = false
  template {
    service_account = google_service_account.mcp.email
    timeout         = "120s"
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }
    containers {
      image = local.image_mcp
      resources { limits = { cpu = "1", memory = "512Mi" } }
      env {
        name  = "PRODUIT"
        value = each.key
      }
      env {
        name  = "OAUTH_CLIENT_IDS"
        value = join(",", var.oauth_client_ids)
      }
      env {
        name  = "ALLOWED_DOMAINS"
        value = join(",", var.allowed_domains)
      }
    }
  }
  lifecycle {
    precondition {
      condition     = length(var.oauth_client_ids) > 0
      error_message = "oauth_client_ids est vide : le serveur MCP refuserait de démarrer. Créez le client OAuth (docs/10-5, étape 1), remplissez OAUTH_CLIENT_IDS, rechargez la configuration."
    }
  }
  depends_on = [terraform_data.image]
}

# 5. L'agent A2A sur Cloud Run ----------------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "agent" {
  count               = var.deploy_agent_cloudrun ? 1 : 0
  name                = "sheets-agent"
  location            = var.region
  deletion_protection = false
  template {
    service_account = google_service_account.agent.email
    timeout         = "300s"
    scaling {
      min_instance_count = 0
      max_instance_count = 1 # sessions en mémoire
    }
    containers {
      image = local.image_agent
      resources { limits = { cpu = "1", memory = "1Gi" } }
      dynamic "env" {
        for_each = merge({ AGENT_URL = local.agent_url, AUTH_ID = var.auth_id, MODEL = var.model, GOOGLE_CLOUD_PROJECT = var.project_id }, local.env_mcp)
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
  depends_on = [terraform_data.image, google_project_iam_member.agent]
}

# 6. L'agent sur Agent Runtime (même code, dossier agent/) -------------------------------------------------------------
data "external" "agent_source" {
  count   = var.deploy_agent_runtime ? 1 : 0
  program = ["python3", "${local.racine}/scripts/pack.py"]
  query   = { src = "${local.racine}/agent", only = "sheets_agent,requirements.txt" }
}
resource "google_vertex_ai_reasoning_engine" "agent" {
  count           = var.deploy_agent_runtime ? 1 : 0
  display_name    = "sheets-agent"
  description     = "Lit et modifie les Google Sheets de l'utilisateur connecté (serveur MCP), avec ses propres droits."
  region          = var.region
  deletion_policy = "FORCE" # supprime aussi les sessions (sinon destroy échoue dès que l'agent a servi)
  spec {
    agent_framework = "google-adk"
    service_account = google_service_account.agent.email
    class_methods   = file("${local.racine}/agent/class_methods.json")
    source_code_spec {
      inline_source { source_archive = data.external.agent_source[0].result.archive }
      python_spec {
        version           = "3.12"
        entrypoint_module = "sheets_agent.agent"
        entrypoint_object = "agent_runtime_app"
        requirements_file = "requirements.txt"
      }
    }
    deployment_spec {
      min_instances = 0
      max_instances = 2
      dynamic "env" {
        for_each = merge({ AUTH_ID = "${var.auth_id}-runtime", MODEL = var.model }, local.env_mcp)
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
  timeouts {
    create = "30m"
    update = "30m"
  }
  depends_on = [google_project_iam_member.agent]
}

# 7. Qui peut appeler quoi ---------------------------------------------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "mcp" { # sur chaque serveur MCP : l'agent, et l'app (connecteur natif)
  # Clé : le membre seul pour Sheets (comme avant Slides : un déploiement existant ne perd pas ses droits), « slides <membre> » pour Slides.
  for_each = { for pm in setproduct(keys(local.produits), compact([google_service_account.agent.member, local.ge_sa])) : (pm[0] == "sheets" ? pm[1] : "${pm[0]} ${pm[1]}") => pm }
  name     = google_cloud_run_v2_service.mcp[each.value[0]].name
  location = var.region
  role     = "roles/run.invoker"
  member   = each.value[1]
}
resource "google_cloud_run_v2_service_iam_member" "agent" { # l'app appelle l'agent A2A
  count    = var.deploy_agent_cloudrun && local.ge_sa != "" ? 1 : 0
  name     = google_cloud_run_v2_service.agent[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = local.ge_sa
}
resource "google_project_iam_member" "ge_runtime" { # l'app appelle l'agent Agent Runtime
  count      = var.deploy_agent_runtime && local.ge_sa != "" ? 1 : 0
  project    = var.project_id
  role       = "roles/discoveryengine.serviceAgent"
  member     = local.ge_sa
  depends_on = [google_project_service.apis]
}

# 8. Agent Registry : le serveur MCP et ses outils (générés par scripts/gen_toolspec.py) ------------------------------
moved {
  from = google_agent_registry_service.mcp[0]
  to   = google_agent_registry_service.mcp["sheets"]
}
resource "google_agent_registry_service" "mcp" {
  for_each     = var.register_in_agent_registry ? local.produits : {}
  location     = var.registry_location
  service_id   = "${each.key}-mcp"
  display_name = each.key == "sheets" ? "Google Sheets (MCP)" : "Google Slides (MCP)"
  description  = "Lecture et modification de ${each.key == "sheets" ? "Google Sheets" : "Google Slides"} au nom de l'utilisateur (OAuth Google, domaine restreint)."
  mcp_server_spec {
    type    = "TOOL_SPEC"
    content = file("${path.module}/toolspec-${each.key}.json") # scripts/gen_toolspec.py
  }
  interfaces {
    protocol_binding = "JSONRPC"
    url              = each.value
  }
  depends_on = [google_project_service.apis]
}
