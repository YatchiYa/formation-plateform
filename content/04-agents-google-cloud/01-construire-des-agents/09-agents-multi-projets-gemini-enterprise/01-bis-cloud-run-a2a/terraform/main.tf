# 01-bis : les 3 agents du trio sur Cloud Run, en A2A, prêts pour Gemini Enterprise.
#
#   1 image   -> 3 services Cloud Run privés (un par agent : URL, identité, droit d'appel propres)
#             -> 3 cartes A2A v0.3 (format exigé par Gemini Enterprise)
#             -> déclarées dans Agent Registry (catalogue du projet agents)
#             -> droit d'appel pour Gemini Enterprise (si ge_project_number est renseigné)
#             -> ajoutées à l'app Gemini Enterprise (si ge_app_id est renseigné)

locals {
  trio_dir = abspath("${path.module}/../../agents/trio")
  src_dir  = abspath("${path.module}/..")
  racine   = abspath("${path.module}/../..") # dossier du projet : ce que Cloud Build reçoit (filtré par .gcloudignore)
  # Les agents à déployer : ceux de var.agents (clés du catalogue), ou TOUT le catalogue si la liste est vide.
  # Chaque ressource « par agent » fait for_each sur cette carte : une clé = un agent = ses propres ressources.
  catalogue = jsondecode(file("${local.trio_dir}/catalogue.json"))
  agents    = { for k in(length(var.agents) == 0 ? keys(local.catalogue) : var.agents) : k => local.catalogue[k] }

  # Une image PAR AGENT, étiquetée par l'empreinte de ce qui entre dedans : le commun + le dossier de l'agent.
  # Code de l'agent modifié => nouveau tag => nouvelle révision de CE service. Autre agent ajouté ou modifié => rien.
  commun_files = concat([for f in ["Dockerfile", "main.py", "cloudbuild.yaml"] : "${local.src_dir}/${f}"],
  [for f in ["commun.py", "requirements.txt"] : "${local.trio_dir}/${f}"])
  image = { for k, a in local.agents : k => "${var.region}-docker.pkg.dev/${var.agents_project_id}/agents-a2a/${k}:${substr(sha1(join("", [
    for f in concat(local.commun_files, [for f in sort(tolist(fileset("${local.trio_dir}/${a.dossier}", "**/*.py"))) : "${local.trio_dir}/${a.dossier}/${f}"]) : filesha1(f)
  ])), 0, 12)}" }

  # URL d'un service Cloud Run, connue AVANT sa création : https://SERVICE-NUMERO_PROJET.REGION.run.app
  # (la carte A2A, qui contient l'URL, est passée au service lui-même). Vérifiée après création (postcondition).
  url = { for k, a in local.agents : k => "https://${k}-a2a-${data.google_project.agents.number}.${var.region}.run.app" }

  # Carte A2A v0.3 : exactement le format de la documentation Gemini Enterprise.
  card = { for k, a in local.agents : k => jsonencode({
    protocolVersion    = "0.3"
    name               = a.dossier
    description        = a.description
    url                = local.url[k]
    preferredTransport = "JSONRPC"
    version            = "1.0.0"
    capabilities       = { streaming = true }
    defaultInputModes  = ["text/plain"]
    defaultOutputModes = ["text/plain"]
    skills             = a.competences
  }) }

  create_armor      = var.prompt_template == ""
  prompt_template   = local.create_armor ? module.armor[0].prompt : var.prompt_template
  response_template = local.create_armor ? module.armor[0].response : var.response_template
  armor_project     = split("/", local.prompt_template)[1]

  # Le compte de Gemini Enterprise : c'est LUI qui appelle les agents. Il appartient au projet de l'app (numéro).
  grant_ge         = var.ge_project_number != ""
  publish          = var.ge_app_id != ""
  ge_service_agent = "serviceAccount:service-${var.ge_project_number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}

data "google_project" "agents" {
  provider = google.agents
}

# 1. API -----------------------------------------------------------------------
resource "google_project_service" "agents" {
  provider = google.agents
  for_each = toset(concat(["run.googleapis.com", "artifactregistry.googleapis.com", "aiplatform.googleapis.com",
    "modelarmor.googleapis.com", "agentregistry.googleapis.com", "logging.googleapis.com", "iam.googleapis.com", "cloudbuild.googleapis.com"],
    var.model_api_key_secret == "" ? [] : ["secretmanager.googleapis.com"],
    # Agents OAuth (oauth_agents) : les API Google qu'ils appellent avec le jeton de l'utilisateur (catalogue, « oauth.apis »).
    # Le client OAuth est dans CE projet (docs/12-1-8) : c'est ici que Gmail, Drive… doivent être actives.
  flatten([for k, a in local.agents : try(a.oauth.apis, []) if contains(keys(var.oauth_agents), k)])))
  service            = each.value
  disable_on_destroy = false
}

resource "google_project_service" "ge" {
  count              = local.publish ? 1 : 0
  provider           = google.ge
  service            = "discoveryengine.googleapis.com"
  disable_on_destroy = false
}

# 2. Model Armor : templates fournis (projet 08) ou créés ici --------------------
module "armor" {
  count      = local.create_armor ? 1 : 0
  source     = "../../terraform/modules/armor_templates"
  providers  = { google = google.agents }
  prefix     = "trio-a2a"
  location   = var.ge_location
  depends_on = [google_project_service.agents]
}

# 3. Les images (une par agent), construites DANS Google Cloud (Cloud Build) : pas besoin de Docker sur le poste --
resource "google_artifact_registry_repository" "agents" {
  provider      = google.agents
  location      = var.region
  repository_id = "agents-a2a"
  format        = "DOCKER"
  depends_on    = [google_project_service.agents]
}

# Le compte qui construit les images. Dédié, car le compte par défaut de Cloud Build n'a souvent aucun droit
# (vérifié : « does not have storage.objects.get access »), surtout en entreprise.
resource "google_service_account" "build" {
  provider     = google.agents
  account_id   = "agents-a2a-build-sa"
  display_name = "Construction des images des agents A2A (Cloud Build, Terraform)"
  depends_on   = [google_project_service.agents]
}

resource "google_project_iam_member" "build" {
  provider = google.agents
  for_each = toset(["roles/storage.objectViewer", "roles/artifactregistry.writer", "roles/logging.logWriter"]) # lire le code envoyé, ranger l'image, écrire ses journaux
  project  = var.agents_project_id
  role     = each.value
  member   = google_service_account.build.member
}

resource "terraform_data" "image" {
  for_each         = local.agents
  triggers_replace = local.image[each.key]

  provisioner "local-exec" {
    working_dir = local.racine
    interpreter = ["bash", "-c"]
    # Jusqu'à 4 essais : les droits d'un compte tout neuf mettent 1 à 2 minutes à s'appliquer (403 au 1er essai).
    command = <<-EOT
      for essai in 1 2 3 4; do
        gcloud builds submit --project=${var.agents_project_id} --region=${var.region} \
          --service-account=${google_service_account.build.id} --config=01-bis-cloud-run-a2a/cloudbuild.yaml \
          --substitutions=_AGENT_DIR=${each.value.dossier},_IMAGE=${local.image[each.key]} --quiet . && exit 0
        echo "construction de ${each.key} : nouvel essai dans 40 s (droits en cours d'activation)"; sleep 40
      done
      exit 1
    EOT
  }

  depends_on = [google_artifact_registry_repository.agents, google_project_iam_member.build]
}

# 4. Une identité par agent (moindre privilège) ----------------------------------
resource "google_service_account" "agent" {
  provider     = google.agents
  for_each     = local.agents
  account_id   = "${each.key}-a2a-sa"
  display_name = "Identité d'exécution de ${each.value.nom_affiche} (Cloud Run, A2A)"
  depends_on   = [google_project_service.agents] # API IAM activée d'abord
}

resource "google_project_iam_member" "agent" {
  provider = google.agents
  for_each = { for p in setproduct(keys(local.agents), ["roles/aiplatform.user", "roles/logging.logWriter"]) : "${p[0]} ${p[1]}" => p }
  project  = var.agents_project_id
  role     = each.value[1]
  member   = google_service_account.agent[each.value[0]].member
}

resource "google_project_iam_member" "armor" {
  provider = google.agents
  for_each = local.agents
  project  = local.armor_project
  role     = "roles/modelarmor.user"
  member   = google_service_account.agent[each.key].member
}

resource "google_secret_manager_secret_iam_member" "agent" {
  provider  = google.agents
  for_each  = { for k, a in local.agents : k => a if var.model_api_key_secret != "" }
  project   = var.agents_project_id
  secret_id = var.model_api_key_secret
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.agent[each.key].member
}

# 5. Les 3 services Cloud Run, privés --------------------------------------------
resource "google_cloud_run_v2_service" "agent" {
  provider            = google.agents
  for_each            = local.agents
  name                = "${each.key}-a2a"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL" # joignable par Gemini Enterprise ; l'IAM fait le tri (pas d'accès public)
  deletion_protection = false

  template {
    service_account = google_service_account.agent[each.key].email
    scaling {
      min_instance_count = 0
      max_instance_count = 1 # ponytail: sessions A2A en mémoire ; base de sessions avant d'augmenter
    }
    containers {
      image = local.image[each.key]
      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }
      dynamic "env" {
        for_each = merge({
          AGENT                = each.value.dossier
          AGENT_CARD           = local.card[each.key]
          GOOGLE_CLOUD_PROJECT = var.agents_project_id
          MODEL                = var.model
          PROMPT_TEMPLATE      = local.prompt_template
          RESPONSE_TEMPLATE    = local.response_template
        }, contains(keys(var.oauth_agents), each.key) ? { AUTH_ID = var.oauth_agents[each.key], GE_ENGINE = var.ge_engine } : {})
        content {
          name  = env.key
          value = env.value
        }
      }
      # Clé d'API du modèle (optionnelle), lue dans Secret Manager.
      dynamic "env" {
        for_each = var.model_api_key_secret == "" ? {} : { (var.model_api_key_type == "gemini" ? "GEMINI_API_KEY" : "VERTEX_API_KEY") = var.model_api_key_secret }
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  lifecycle {
    postcondition {
      condition     = contains(self.urls, local.url[each.key])
      error_message = "L'URL réelle du service (${join(", ", self.urls)}) diffère de celle de la carte A2A (${local.url[each.key]})."
    }
  }

  # Les droits existent avant le démarrage : sinon l'agent bloque (Model Armor en mode fermé).
  depends_on = [terraform_data.image, google_project_iam_member.agent, google_project_iam_member.armor, google_secret_manager_secret_iam_member.agent]
}

# 6. Gemini Enterprise a le droit d'appeler CES services, et seulement eux --------
#    (même projet ou autre projet : même droit, posé sur le service)
resource "google_cloud_run_v2_service_iam_member" "ge_invokes" {
  provider = google.agents
  for_each = { for k, a in local.agents : k => a if local.grant_ge }
  name     = google_cloud_run_v2_service.agent[each.key].name
  location = var.region
  role     = "roles/run.invoker"
  member   = local.ge_service_agent
}

# 7. Agent Registry : le catalogue du projet agents -------------------------------
#    (un agent Agent Runtime s'y inscrit seul ; un agent Cloud Run, on le déclare avec sa carte)
resource "google_agent_registry_service" "agent" {
  provider     = google.agents
  for_each     = { for k, a in local.agents : k => a if var.register_in_agent_registry }
  location     = var.region
  service_id   = "${each.key}-a2a"
  display_name = each.value.nom_affiche
  description  = each.value.description

  agent_spec {
    type    = "A2A_AGENT_CARD"
    content = local.card[each.key] # l'URL est DANS la carte : pas de bloc interfaces (refusé par l'API avec une carte)
  }

  depends_on = [google_project_service.agents]
}

# 8. Publication dans l'app Gemini Enterprise (carte A2A collée, comme dans la console) --
resource "terraform_data" "publish" {
  for_each = { for k, a in local.agents : k => a if local.publish }
  input = {
    project_id   = var.ge_project_id
    host         = var.ge_location == "global" ? "discoveryengine.googleapis.com" : "${var.ge_location}-discoveryengine.googleapis.com"
    parent       = "projects/${var.ge_project_id}/locations/${var.ge_location}/collections/default_collection/engines/${var.ge_app_id}/assistants/default_assistant"
    card         = local.card[each.key]
    display_name = "${each.value.nom_affiche} (A2A)"
    description  = each.value.description
    # Autorisation OAuth de l'agent (oauth_agents), créée avant dans l'app : docs/12-3, partie C.
    # Plusieurs fournisseurs : "acces-google,acces-atlassian" (Agent Runtime seulement, docs/12-1-8).
    authorization = contains(keys(var.oauth_agents), each.key) ? join(",", [for id in split(",", var.oauth_agents[each.key]) : "projects/${var.ge_project_number}/locations/${var.ge_location}/authorizations/${id}"]) : ""
  }

  provisioner "local-exec" {
    command     = "${path.module}/../../scripts/register_agent.sh create"
    environment = { for k, v in self.input : upper(k) => v }
  }

  provisioner "local-exec" {
    when        = destroy
    command     = "${path.module}/../../scripts/register_agent.sh delete"
    environment = { for k, v in self.input : upper(k) => v }
  }

  lifecycle {
    precondition {
      condition     = length(distinct([for a in values(local.agents) : a.nom_affiche])) == length(local.agents)
      error_message = "Deux agents du catalogue ont le même nom_affiche : ils s'écraseraient dans Gemini Enterprise."
    }
    precondition {
      condition     = var.ge_project_id != "" && var.ge_project_number != ""
      error_message = "Pour publier (ge_app_id), renseigner aussi ge_project_id et ge_project_number."
    }
  }

  depends_on = [google_cloud_run_v2_service_iam_member.ge_invokes, google_project_service.ge]
}

# 9. (Option, scénario 12-2) Mode « Agents depuis Agent Registry » : passerelle + droit de passage --------
#    L'app n'importe que depuis le registre de SON projet : les agents doivent être dans le projet de l'app.
#    Relier la passerelle à l'app se fait ensuite dans la console (tout le trafic de l'app passera par elle).
resource "google_project_service" "gateway" {
  provider           = google.agents
  for_each           = var.agent_gateway ? toset(["networkservices.googleapis.com", "iap.googleapis.com"]) : toset([])
  service            = each.value
  disable_on_destroy = false
}

resource "google_network_services_agent_gateway" "ge" {
  provider = google.agents
  count    = var.agent_gateway ? 1 : 0
  name     = "ge-egress"
  location = var.region
  google_managed {
    governed_access_path = "AGENT_TO_ANYWHERE"
  }
  registries = ["//agentregistry.googleapis.com/projects/${var.agents_project_id}/locations/${var.region}"]

  lifecycle {
    precondition {
      condition     = var.ge_project_number == data.google_project.agents.number && var.register_in_agent_registry
      error_message = "agent_gateway : les agents doivent être dans le projet de l'app (scénario 12-2) et inscrits dans Agent Registry."
    }
  }
  depends_on = [google_project_service.gateway]
}

resource "google_iap_agent_registry_agent_iam_member" "ge_passe" {
  provider   = google.agents
  for_each   = { for k, a in local.agents : k => a if var.agent_gateway }
  location   = var.region
  agent_id   = element(split("/", google_agent_registry_service.agent[each.key].registry_resource), 5)
  role       = "roles/iap.egressor"
  member     = local.ge_service_agent
  depends_on = [google_project_service.gateway]
}
