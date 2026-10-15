variable "project_id" {
  description = "Projet qui héberge la plateforme IA (un projet par environnement : dev, prod)."
  type        = string
}

variable "region" {
  description = "Région unique de la plateforme. Une région UE garde données et traitements dans l'Union."
  type        = string
  default     = "europe-west1"

  validation {
    condition     = startswith(var.region, "europe-")
    error_message = "Résidence des données UE : la région doit commencer par europe-."
  }
}

variable "prefix" {
  description = "Préfixe de nommage de toutes les ressources."
  type        = string
  default     = "lab-archi-ia"
}

variable "labels" {
  description = "Labels appliqués partout (coûts, inventaire, nettoyage)."
  type        = map(string)
  default     = { formation-lab = "architecture-ia" }
}

variable "subnet_cidr" {
  description = "Plage IP du sous-réseau privé."
  type        = string
  default     = "10.10.0.0/24"
}

variable "psc_ip" {
  description = "Adresse interne du point d'accès Private Service Connect vers les API Google (hors de tout sous-réseau)."
  type        = string
  default     = "10.255.0.2"
}

variable "app_image" {
  description = "Image du service Cloud Run (l'assistant interne)."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "app_domain" {
  description = "Nom de domaine de l'assistant (certificat géré par Google). Vide = pas de load balancer ni d'IAP."
  type        = string
  default     = ""
}

variable "iap_members" {
  description = "Qui peut ouvrir l'assistant derrière IAP (groupes de préférence)."
  type        = list(string)
  default     = []
}

variable "app_invokers" {
  description = "Groupes autorisés à appeler Vertex AI en direct (développeurs). Rôle roles/aiplatform.user."
  type        = list(string)
  default     = []
}

variable "kms_rotation_period" {
  description = "Rotation automatique de la clé CMEK."
  type        = string
  default     = "7776000s" # 90 jours
}

variable "log_retention_days" {
  description = "Rétention des journaux d'audit IA dans le bucket de logs dédié."
  type        = number
  default     = 365
}

variable "access_policy_id" {
  description = "Numéro de la politique Access Context Manager de l'organisation. null = pas de périmètre VPC-SC."
  type        = string
  default     = null
}

variable "vpcsc_dry_run" {
  description = "true = le périmètre journalise les violations sans bloquer (à faire d'abord)."
  type        = bool
  default     = true
}

variable "enforce_eu_location_policy" {
  description = "Applique la contrainte d'organisation gcp.resourceLocations (in:eu-locations) au projet."
  type        = bool
  default     = false
}

variable "billing_account" {
  description = "Compte de facturation (XXXXXX-XXXXXX-XXXXXX). null = pas de budget."
  type        = string
  default     = null
}

variable "monthly_budget_eur" {
  description = "Budget mensuel du projet, en euros."
  type        = number
  default     = 200
}
