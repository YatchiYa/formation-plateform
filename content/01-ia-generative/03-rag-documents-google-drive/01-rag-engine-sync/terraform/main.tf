locals {
  app_dir = abspath("${path.module}/../app")

  # Empreinte du code : un fichier change => nouvelle image => nouvelle révision. Rien ne change => rien n'est reconstruit.
  app_files = sort(tolist(fileset(local.app_dir, "**/{*.py,*.html,*.txt,*.yaml,Dockerfile,.gcloudignore}")))
  app_hash  = sha1(join("", [for f in local.app_files : filesha1("${local.app_dir}/${f}")]))
  image     = "${var.region}-docker.pkg.dev/${var.project_id}/${var.prefix}/app:${substr(local.app_hash, 0, 12)}"

  project_number = var.project_number
  rag_agent      = "serviceAccount:service-${local.project_number}@gcp-sa-vertex-rag.iam.gserviceaccount.com"
  bucket_name    = "${var.project_id}-${var.prefix}"
  sync_job_name  = "${var.prefix}-sync"
  layout_parser  = var.layout_parser ? google_document_ai_processor.layout[0].id : ""

  # Les mêmes variables pour le service et le job (ils partagent kit.py).
  env = {
    PROJECT_ID                = var.project_id
    PROJECT_NUMBER            = local.project_number
    REGION                    = var.region
    BUCKET                    = google_storage_bucket.docs.name
    CORPUS                    = google_vertex_ai_rag_corpus.docs.id
    CORPUS_GE                 = var.ge_serving_config == "" ? "" : google_vertex_ai_rag_corpus.ge[0].id # id = chemin complet ; name = numéro seul (vérifié)
    LAYOUT_PARSER             = local.layout_parser
    SYNC_JOB                  = local.sync_job_name
    SA_EMAIL                  = google_service_account.kit.email
    MODEL                     = var.model
    GOOGLE_GENAI_USE_VERTEXAI = "true"
    GOOGLE_CLOUD_PROJECT      = var.project_id
    GOOGLE_CLOUD_LOCATION     = var.model_location
    OTEL_TO_CLOUD             = "true"
    PREFIX                    = var.prefix
    HOOK_URL                  = var.push ? "${google_cloud_run_v2_service.hook[0].uri}/hook/drive" : ""
    PICKER_API_KEY            = google_apikeys_key.picker.key_string
  }
}

# 1. API -----------------------------------------------------------------------------------
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",      # Gemini + RAG Engine
    "documentai.googleapis.com",      # layout parser
    "discoveryengine.googleapis.com", # reranking (API Ranking)
    "drive.googleapis.com",           # lister les dossiers Drive (détection des suppressions)
    "run.googleapis.com",             # service + job
    "cloudscheduler.googleapis.com",  # synchro planifiée
    "cloudbuild.googleapis.com",      # construction de l'image
    "artifactregistry.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "cloudtrace.googleapis.com",
    "telemetry.googleapis.com",
    "secretmanager.googleapis.com", # client OAuth et jetons des comptes Google connectés
    "picker.googleapis.com",        # sélecteur de dossiers Google dans l'interface
    "apikeys.googleapis.com",       # clé du sélecteur
  ])
  service            = each.value
  disable_on_destroy = false # d'autres choses peuvent s'en servir
}

# 2. Le RAG : palier de la base, corpus, parseur ------------------------------------------------
# Le palier vaut pour TOUT le projet dans cette région. Laissé tel quel par défaut (Basic à la 1re utilisation).
resource "google_vertex_ai_rag_engine_config" "tier" {
  count  = var.rag_tier == "" ? 0 : 1
  region = var.region
  rag_managed_db_config {
    dynamic "basic" {
      for_each = var.rag_tier == "basic" ? [1] : []
      content {}
    }
    dynamic "scaled" {
      for_each = var.rag_tier == "scaled" ? [1] : []
      content {}
    }
  }
  # destroy ne « déprovisionne » PAS la base (ce qui effacerait tous les corpus du projet) : voir docs/10.
  deletion_policy = "ABANDON"
  depends_on      = [google_project_service.apis]
}

resource "google_vertex_ai_rag_corpus" "docs" {
  region       = var.region
  display_name = var.prefix
  description  = "Documents Drive + dépôts (kit ${var.prefix})"
  vector_db_config {
    rag_managed_db {
      knn {}
    }
    rag_embedding_model_config {
      vertex_prediction_endpoint {
        endpoint = "projects/${var.project_id}/locations/${var.region}/publishers/google/models/${var.embedding_model}"
      }
    }
  }
  depends_on = [google_project_service.apis, google_vertex_ai_rag_engine_config.tier]
}

# Hybride : un 2e corpus, adossé à l'app Gemini Enterprise (ses data stores et connecteurs). En lecture seule :
# Google le tient à jour, le kit ne fait qu'y chercher (vérifié : corpus europe-west4 sur une app « eu »).
resource "google_vertex_ai_rag_corpus" "ge" {
  count        = var.ge_serving_config == "" ? 0 : 1
  region       = var.region
  display_name = "${var.prefix}-gemini-enterprise"
  description  = "Adossé à ${var.ge_serving_config}"
  vertex_ai_search_config {
    serving_config = var.ge_serving_config
  }
  depends_on = [google_project_service.apis]
}

resource "google_document_ai_processor" "layout" {
  count        = var.layout_parser ? 1 : 0
  location     = "eu" # vérifié : processeur « eu » utilisable par un corpus europe-west4
  type         = "LAYOUT_PARSER_PROCESSOR"
  display_name = "${var.prefix}-layout"
  depends_on   = [google_project_service.apis]
}

# 3. Le bucket : fichiers déposés (uploads/), config.json, rapports de synchro (sync/) ---------------
resource "google_storage_bucket" "docs" {
  name                        = local.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # kit d'apprentissage : destroy vide le bucket. À retirer en production.
  depends_on                  = [google_project_service.apis]

  lifecycle_rule { # rapports d'import détaillés : 30 jours suffisent
    condition {
      age            = 30
      matches_prefix = ["sync/runs/"]
    }
    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_object" "sources" {
  bucket       = google_storage_bucket.docs.name
  name         = "config.json"
  content_type = "application/json"
  content      = jsonencode({ drive_folders = [for id in var.drive_folders : { id = id, name = id }] })
  lifecycle {
    # Créé une fois ; ensuite c'est l'interface qui gère la liste. Sans « all », chaque apply réécrivait le fichier
    # (l'empreinte change dès que l'interface l'édite) et effaçait les dossiers ajoutés depuis l'interface (vérifié).
    ignore_changes = all
  }
}

# L'agent de service RAG (créé par Google avec le corpus) lit les dépôts et écrit ses rapports d'import.
resource "google_storage_bucket_iam_member" "rag_agent" {
  for_each   = toset(["roles/storage.objectViewer", "roles/storage.objectCreator"]) # sans objectCreator : 403 (vérifié)
  bucket     = google_storage_bucket.docs.name
  role       = each.value
  member     = local.rag_agent
  depends_on = [google_vertex_ai_rag_corpus.docs]
}

# 4. Identités ---------------------------------------------------------------------------------
resource "google_service_account" "kit" {
  account_id   = "${var.prefix}-sa"
  display_name = "Kit RAG : interface, agent et synchro"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "kit" {
  for_each = toset([
    "roles/aiplatform.user",        # Gemini + RAG Engine (recherche, import, suppression)
    "roles/discoveryengine.viewer", # reranking : discoveryengine.rankingConfigs.rank (sans lui : 403, vérifié)
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/cloudtrace.agent",
    "roles/telemetry.writer",
  ])
  project = var.project_id
  role    = each.value
  member  = google_service_account.kit.member
}

resource "google_storage_bucket_iam_member" "kit" {
  bucket = google_storage_bucket.docs.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.kit.member
}

resource "google_service_account" "scheduler" {
  account_id   = "${var.prefix}-scheduler-sa"
  display_name = "Kit RAG : lance la synchro planifiée"
  depends_on   = [google_project_service.apis]
}

resource "google_service_account" "build" {
  account_id   = "${var.prefix}-build-sa"
  display_name = "Kit RAG : construit l'image (Cloud Build)"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "build" {
  for_each = toset(["roles/storage.objectViewer", "roles/artifactregistry.writer", "roles/logging.logWriter"])
  project  = var.project_id
  role     = each.value
  member   = google_service_account.build.member
}

# 5. L'image (une seule pour le service et le job) ----------------------------------------------------
resource "google_artifact_registry_repository" "images" {
  location      = var.region
  repository_id = var.prefix
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

resource "terraform_data" "image" {
  triggers_replace = local.image

  provisioner "local-exec" {
    working_dir = local.app_dir
    interpreter = ["bash", "-c"]
    # Jusqu'à 4 essais : les droits d'un compte tout neuf mettent 1 à 2 minutes à s'appliquer.
    command = <<-EOT
      for essai in 1 2 3 4; do
        gcloud builds submit . --project=${var.project_id} --region=${var.region} --config=cloudbuild.yaml \
          --service-account=${google_service_account.build.id} --substitutions=_IMAGE=${local.image} --quiet && exit 0
        echo "construction : nouvel essai dans 40 s (droits en cours d'activation)"; sleep 40
      done
      exit 1
    EOT
  }

  depends_on = [google_artifact_registry_repository.images, google_project_iam_member.build]
}

# 6. Le job de synchro + sa planification ------------------------------------------------------------
resource "google_cloud_run_v2_job" "sync" {
  name                = local.sync_job_name
  location            = var.region
  deletion_protection = false

  template {
    task_count = 1
    template {
      service_account = google_service_account.kit.email
      timeout         = "3600s"
      max_retries     = 0 # la passe suivante rattrape ; pas de 2e import concurrent
      containers {
        image   = local.image
        command = ["python", "sync_job.py"]
        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }
        dynamic "env" {
          for_each = local.env
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  depends_on = [terraform_data.image, google_project_iam_member.kit, google_storage_bucket_iam_member.kit]
}

# Le service lance le job (bouton « Synchroniser », webhook) et lit son état. « WithOverrides » : pour passer
# TRIGGER=auto (run.invoker ne contient pas run.jobs.runWithOverrides, vérifié).
resource "google_cloud_run_v2_job_iam_member" "kit" {
  for_each = toset(["roles/run.jobsExecutorWithOverrides", "roles/run.viewer"])
  name     = google_cloud_run_v2_job.sync.name
  location = var.region
  role     = each.value
  member   = google_service_account.kit.member
}

resource "google_cloud_run_v2_job_iam_member" "scheduler" {
  name     = google_cloud_run_v2_job.sync.name
  location = var.region
  role     = "roles/run.jobsExecutorWithOverrides"
  member   = google_service_account.scheduler.member
}

resource "google_cloud_scheduler_job" "sync" {
  count     = var.sync_schedule == "" ? 0 : 1 # vide = pas de passe planifiée (push et bouton seulement)
  name      = "${var.prefix}-sync"
  region    = var.region
  schedule  = var.sync_schedule
  time_zone = "Europe/Paris"

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.sync.name}:run"
    headers     = { "Content-Type" = "application/json" }
    # TRIGGER=auto : les sources Google dont la synchro auto est coupée sont laissées de côté.
    body = base64encode(jsonencode({ overrides = { containerOverrides = [{ env = [{ name = "TRIGGER", value = "auto" }] }] } }))
    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [google_cloud_run_v2_job_iam_member.scheduler]
}

# 7. Le service web (interface + agent) ----------------------------------------------------------------
resource "google_cloud_run_v2_service" "app" {
  name                = var.prefix
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.kit.email
    timeout         = "300s"
    scaling {
      min_instance_count = 0
      # ponytail: 1 instance car les conversations sont en mémoire ; base de sessions avant d'augmenter.
      max_instance_count = 1
    }
    containers {
      image = local.image
      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }
      dynamic "env" {
        for_each = local.env
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }

  depends_on = [terraform_data.image, google_project_iam_member.kit, google_storage_bucket_iam_member.kit]
}

# Privé : seuls les principaux listés (et les propriétaires du projet) peuvent l'ouvrir.
resource "google_cloud_run_v2_service_iam_member" "users" {
  for_each = toset(var.users)
  name     = google_cloud_run_v2_service.app.name
  location = var.region
  role     = "roles/run.invoker"
  member   = each.value
}

# 8. Connexion Google (OAuth) ------------------------------------------------------------------------
# Le client OAuth « Application Web » se crée dans la console (pas d'API pour les portées Drive) puis se range ici
# avec scripts/connexion_google.sh. Les jetons des comptes connectés vont dans le second secret.
resource "google_secret_manager_secret" "oauth" {
  for_each  = toset(["oauth-client", "google-tokens"])
  secret_id = "${var.prefix}-${each.key}"
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }
  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_iam_member" "kit_read" {
  for_each  = google_secret_manager_secret.oauth
  secret_id = each.value.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.kit.member
}

resource "google_secret_manager_secret_iam_member" "kit_tokens" {
  secret_id = google_secret_manager_secret.oauth["google-tokens"].id
  role      = "roles/secretmanager.secretVersionManager" # ajouter un jeton, détruire l'ancienne version
  member    = google_service_account.kit.member
}

# Clé du sélecteur Google (Picker) : clé « navigateur », publique par nature, limitée à l'API Picker et aux pages
# ouvertes par le proxy.
resource "google_apikeys_key" "picker" {
  name         = "${var.prefix}-picker"
  display_name = "Kit RAG : sélecteur de dossiers Google"
  restrictions {
    api_targets {
      service = "picker.googleapis.com"
    }
    browser_key_restrictions {
      allowed_referrers = ["http://localhost:8080/*", "http://127.0.0.1:8080/*"]
    }
  }
  depends_on = [google_project_service.apis]
}

# 9. Notifications push de Drive -------------------------------------------------------------------------
# Service PUBLIC (Google doit pouvoir l'appeler) qui n'accepte que les canaux ouverts par le kit (jeton secret).
resource "google_cloud_run_v2_service" "hook" {
  count               = var.push ? 1 : 0
  name                = "${var.prefix}-hook"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account = google_service_account.kit.email
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image   = local.image
      command = ["uvicorn", "hook:app", "--host", "0.0.0.0", "--port", "8080"]
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "REGION"
        value = var.region
      }
      env {
        name  = "BUCKET"
        value = google_storage_bucket.docs.name
      }
      env {
        name  = "SYNC_JOB"
        value = local.sync_job_name
      }
      env {
        name  = "PREFIX"
        value = var.prefix
      }
    }
  }

  depends_on = [terraform_data.image, google_project_iam_member.kit, google_storage_bucket_iam_member.kit]
}

resource "google_cloud_run_v2_service_iam_member" "hook_public" {
  count    = var.push ? 1 : 0
  name     = google_cloud_run_v2_service.hook[0].name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# La planification est devenue optionnelle (count) : un état existant migre sans recréation.
moved {
  from = google_cloud_scheduler_job.sync
  to   = google_cloud_scheduler_job.sync[0]
}
