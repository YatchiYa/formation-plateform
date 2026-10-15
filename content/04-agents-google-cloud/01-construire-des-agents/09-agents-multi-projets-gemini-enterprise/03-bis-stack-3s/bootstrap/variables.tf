variable "project_id" {
  description = "Projet où le pipeline déploie (projet des agents, et du serveur MCP du projet 10)."
  type        = string
}

variable "github_repo" {
  description = "Dépôt GitHub autorisé à déployer, sous la forme organisation/depot (ex. acme/agents-gemini-enterprise)."
  type        = string
}

variable "github_branch" {
  description = "Seule branche qui peut déployer (apply). Les pull requests n'ont que la lecture (plan)."
  type        = string
  default     = "main"
}

variable "state_location" {
  description = "Emplacement du bucket d'état Terraform."
  type        = string
  default     = "EU"
}

variable "roles" {
  description = "Rôles du compte de déploiement sur le projet : tout ce que les Terraform 01-bis et 10 créent."
  type        = list(string)
  default = [
    "roles/serviceusage.serviceUsageAdmin",  # activer les API
    "roles/iam.serviceAccountAdmin",         # créer les identités des agents
    "roles/iam.serviceAccountUser",          # les attacher aux services, lancer Cloud Build avec agents-a2a-build-sa
    "roles/resourcemanager.projectIamAdmin", # donner leurs rôles aux identités (aiplatform.user, logWriter…)
    "roles/artifactregistry.admin",          # dépôt d'images
    "roles/cloudbuild.builds.editor",        # gcloud builds submit
    "roles/storage.admin",                   # bucket <projet>_cloudbuild (code envoyé à Cloud Build)
    "roles/logging.viewer",                  # suivre le journal de la construction
    "roles/run.admin",                       # services Cloud Run et leurs droits d'appel
    "roles/modelarmor.admin",                # templates Model Armor
    "roles/agentregistry.admin",             # entrées Agent Registry
    "roles/aiplatform.admin",                # agent sur Agent Runtime (projet 10, option)
  ]
}
