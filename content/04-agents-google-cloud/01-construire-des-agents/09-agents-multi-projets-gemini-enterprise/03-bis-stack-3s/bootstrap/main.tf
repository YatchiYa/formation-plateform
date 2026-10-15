# 03-bis : le SOCLE « à la 3S », créé une fois par projet. Il remplace « gcloud auth login » sur un poste :
#   GitHub Actions --(jeton OIDC du dépôt, sans clé)--> Workload Identity Federation --> compte agents-deployer-sa
#   --> terraform (état dans un bucket GCS) --> les ressources du 01-bis (ou du projet 10).
# Chez Acme, la 3S fournit l'équivalent (projet, bucket d'état, identité de déploiement) : ce dossier sert
# à comprendre ce qu'elle fait, et à le reproduire sur un projet de test.

data "google_project" "p" {}

resource "google_project_service" "apis" {
  for_each = toset(["iam.googleapis.com", "iamcredentials.googleapis.com", "sts.googleapis.com",
  "cloudresourcemanager.googleapis.com", "storage.googleapis.com", "serviceusage.googleapis.com"])
  service            = each.value
  disable_on_destroy = false
}

# 1. L'état Terraform partagé : versionné (on peut revenir en arrière), jamais public.
resource "google_storage_bucket" "tfstate" {
  name                        = "${var.project_id}-tfstate"
  location                    = var.state_location
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true # ponytail: pratique en test ; en production, false
  versioning {
    enabled = true
  }
  depends_on = [google_project_service.apis]
}

# 2. L'identité du pipeline, et ce qu'elle peut faire.
resource "google_service_account" "deployer" {
  account_id   = "agents-deployer-sa"
  display_name = "Déploiement des agents par GitHub Actions (socle 3S)"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "deployer" {
  for_each = toset(var.roles)
  project  = var.project_id
  role     = each.value
  member   = google_service_account.deployer.member
}

resource "google_storage_bucket_iam_member" "deployer" {
  bucket = google_storage_bucket.tfstate.name
  role   = "roles/storage.objectAdmin"
  member = google_service_account.deployer.member
}

# 3. La confiance GitHub -> Google : seul CE dépôt obtient un jeton, et seule SA branche peut agir en écriture
#    (les pull requests passent par le même fournisseur mais n'ont pas le droit d'emprunter le compte : voir 4).
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  depends_on                = [google_project_service.apis]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }
  attribute_condition = "assertion.repository == '${var.github_repo}'"
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 4. Emprunter le compte : seulement depuis la branche protégée (le sujet OIDC d'un push sur main est
#    « repo:ORG/DEPOT:ref:refs/heads/main »). Une PR (sujet « repo:ORG/DEPOT:pull_request ») est refusée :
#    elle ne fait que « terraform validate » (voir github/deploy-agents.yml).
resource "google_service_account_iam_member" "github" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principal://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/subject/repo:${var.github_repo}:ref:refs/heads/${var.github_branch}"
}
