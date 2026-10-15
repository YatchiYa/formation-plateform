# Valeurs : config/<nom>.env, exportées en TF_VAR_… par scripts/config.sh.

variable "project_id" {
  description = "Projet de l'app Gemini Enterprise (ou qui l'accueillera)."
  type        = string
}

variable "project_number" {
  description = "Numéro du projet (calculé par scripts/config.sh)."
  type        = string
}

variable "ge_location" {
  description = "Emplacement Gemini Enterprise : eu, us ou global (le même que l'app)."
  type        = string
  default     = "eu"
}

variable "region" {
  description = "Région du bucket des dépôts et de la planification (dans la zone de ge_location)."
  type        = string
  default     = "europe-west1"
}

variable "prefix" {
  description = "Préfixe des noms (bucket, data stores, comptes)."
  type        = string
  default     = "rag-ge"
}

# --- Briques ------------------------------------------------------------------------------
variable "depots" {
  description = "Data store « fichiers déposés » (bucket GCS) + resynchro planifiée."
  type        = bool
  default     = true
}

variable "depots_schedule" {
  description = "Fréquence de resynchro du bucket (cron, Europe/Paris) ; vide = import seulement au déploiement."
  type        = string
  default     = "*/15 * * * *"
}

variable "connectors" {
  description = "Connecteurs Gemini Enterprise gérés par Terraform (forme documentée : sharepoint_federated_search). Drive et OneDrive : scripts (console/API), voir docs/03 et 04."
  type = map(object({
    data_source      = string
    display_name     = string
    modes            = optional(list(string), ["FEDERATED"])
    params           = optional(map(string), {})
    secret_params    = optional(map(string), {}) # paramètre => ID du secret Secret Manager (jamais la valeur)
    entities         = optional(list(object({ name = string, params = optional(string) })), [])
    refresh_interval = optional(string, "7200s")
  }))
  default = {}
}

# --- App -----------------------------------------------------------------------------------
variable "app_id" {
  description = "ID de l'app Gemini Enterprise. Existante : les data stores y sont rattachés par scripts/rattacher.sh. Vide + create_app : créée."
  type        = string
  default     = ""
}

variable "create_app" {
  description = "true = créer l'app (intranet + assistant). Exige un abonnement Gemini Enterprise (licences)."
  type        = bool
  default     = false
}

variable "app_display_name" {
  type    = string
  default = "Documents de l'équipe"
}

variable "company_name" {
  type    = string
  default = "Mon entreprise"
}
