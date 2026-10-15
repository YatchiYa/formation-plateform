variable "agents_project_id" {
  description = "Projet où tournent les 3 agents (Cloud Run)."
  type        = string
}

variable "ge_project_number" {
  description = "NUMÉRO du projet de l'app Gemini Enterprise (donné par l'admin GE). Terraform autorise le compte de Gemini Enterprise de ce projet à appeler les agents. Vide = agents déployés sans accès pour Gemini Enterprise (essai)."
  type        = string
  default     = ""
}

variable "ge_project_id" {
  description = "ID du projet de l'app Gemini Enterprise. Seulement pour PUBLIER les agents dans l'app (avec ge_app_id) : il faut alors être admin Gemini Enterprise de ce projet."
  type        = string
  default     = ""
}

variable "ge_app_id" {
  description = "ID de l'app Gemini Enterprise. Vide = ne pas publier (l'admin GE ajoute les agents lui-même : docs/09)."
  type        = string
  default     = ""
}

variable "ge_location" {
  description = "Localisation de l'app Gemini Enterprise (eu, us, global)."
  type        = string
  default     = "eu"
}

variable "region" {
  description = "Région Cloud Run et Agent Registry. App 'eu' => europe-west1."
  type        = string
  default     = "europe-west1"
}

variable "model" {
  type    = string
  default = "gemini-3.5-flash"
}

variable "prompt_template" {
  description = "Template Model Armor des questions (ex. sortie du projet 08). Vide = Terraform crée une paire de templates dans le projet agents."
  type        = string
  default     = ""
}

variable "response_template" {
  description = "Template Model Armor des réponses. Vide si prompt_template est vide."
  type        = string
  default     = ""
}

variable "register_in_agent_registry" {
  description = "Déclarer les 3 agents (carte A2A) dans l'Agent Registry du projet agents."
  type        = bool
  default     = true
}

variable "model_api_key_secret" {
  description = "Optionnel. Nom d'un secret Secret Manager (dans le projet des agents) qui contient une clé d'API pour le modèle. Vide = Vertex AI avec l'identité de l'agent (recommandé)."
  type        = string
  default     = ""
}

variable "model_api_key_type" {
  description = "Type de la clé du secret : gemini (clé Google AI Studio, API Gemini) ou vertex (clé d'API Vertex AI, mode express)."
  type        = string
  default     = "gemini"
  validation {
    condition     = contains(["gemini", "vertex"], var.model_api_key_type)
    error_message = "model_api_key_type : gemini ou vertex."
  }
}

variable "agent_gateway" {
  description = "Scénario 12-2 seulement (agents dans le projet de l'app) : créer l'Agent Gateway de l'app et autoriser Gemini Enterprise (iap.egressor) sur chaque entrée de registre, pour le mode « Agents depuis Agent Registry »."
  type        = bool
  default     = false
}

variable "oauth_agents" {
  description = "Agents qui agissent avec le compte de l'utilisateur : { clé_agent = \"ID de l'autorisation OAuth\" } (docs/12-3, partie C). Vide = aucun."
  type        = map(string)
  default     = {}
}

variable "ge_engine" {
  description = "Chemin de l'app Gemini Enterprise (projects/NUM/locations/LOC/collections/default_collection/engines/APP_ID), pour les agents qui cherchent dans ses sources (commun.recherche_gemini_enterprise)."
  type        = string
  default     = ""
}

variable "agents" {
  description = "Clés des agents à déployer (ex. [\"meteo\", \"taille\"]). Vide = tous les agents de agents/trio/catalogue.json. Retirer une clé de la liste SUPPRIME cet agent."
  type        = list(string)
  default     = []
  validation {
    condition     = length(var.agents) == length(distinct(var.agents))
    error_message = "Une clé apparaît deux fois dans agents."
  }
}
