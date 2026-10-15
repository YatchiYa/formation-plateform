variable "project_id" {
  description = "Projet GCP (le même que l'app Gemini Enterprise)."
  type        = string
}

variable "region" {
  description = "Région Cloud Run (UE)."
  type        = string
  default     = "europe-west1"
}

variable "service_name" {
  type    = string
  default = "sheets-mcp"
}

variable "oauth_client_ids" {
  description = "ID du (des) client(s) OAuth dont le serveur accepte les jetons : celui créé pour Gemini Enterprise (étape 1 du guide)."
  type        = list(string)
  validation {
    condition     = length(var.oauth_client_ids) > 0
    error_message = "Au moins un client OAuth est requis."
  }
}

variable "allowed_domains" {
  description = "Domaines Google Workspace autorisés, ex. [\"acme.example\"]. Les comptes d'autres domaines sont refusés."
  type        = list(string)
  validation {
    condition     = length(var.allowed_domains) > 0
    error_message = "Indiquez au moins un domaine : un serveur ouvert à tout compte Google est refusé."
  }
}

variable "min_instances" {
  description = "1 = pas de démarrage à froid (réponses plus rapides dans Gemini Enterprise), 0 = coût minimal."
  type        = number
  default     = 1
}

variable "max_instances" {
  type    = number
  default = 10
}

variable "register_in_agent_registry" {
  description = "Publier le serveur et ses outils dans Agent Registry (catalogue de l'entreprise)."
  type        = bool
  default     = true
}

variable "registry_location" {
  type    = string
  default = "global"
}

variable "extra_invokers" {
  description = "Autres identités autorisées à appeler le service (tests), ex. [\"user:moi@acme.example\"]."
  type        = list(string)
  default     = []
}
