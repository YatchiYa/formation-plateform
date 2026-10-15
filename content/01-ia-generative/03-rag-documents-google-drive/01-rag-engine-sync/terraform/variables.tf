# Toutes ces valeurs viennent du fichier config/<nom>.env (scripts/config.sh les exporte en TF_VAR_…).

variable "project_id" {
  description = "Projet GCP."
  type        = string
}

variable "project_number" {
  description = "Numéro du projet (chiffres) ; calculé par scripts/config.sh."
  type        = string
}

variable "region" {
  description = "Région de Cloud Run, du bucket, du corpus RAG et du Scheduler (RAG Engine GA en Europe : europe-west3, europe-west4)."
  type        = string
  default     = "europe-west4"
}

variable "prefix" {
  description = "Préfixe de tous les noms (service, job, comptes, bucket, corpus)."
  type        = string
  default     = "rag-kit"
}

variable "model" {
  description = "Modèle Gemini de l'agent."
  type        = string
  default     = "gemini-2.5-flash"
}

variable "model_location" {
  description = "Où appeler le modèle : une région (europe-west4 : gemini-2.5-flash, résidence UE) ou « global » (gemini-3.5-flash)."
  type        = string
  default     = "europe-west4"
}

variable "embedding_model" {
  description = "Modèle d'embeddings du corpus. Ne peut plus changer après création (recréer le corpus)."
  type        = string
  default     = "text-multilingual-embedding-002"
}

variable "sync_schedule" {
  description = "Fréquence de la passe planifiée (cron, fuseau Europe/Paris) ; vide = aucune passe planifiée."
  type        = string
  default     = "*/5 * * * *"
}

variable "drive_folders" {
  description = "ID des dossiers Drive à synchroniser au départ (on en ajoute ensuite depuis l'interface)."
  type        = list(string)
  default     = []
}

variable "users" {
  description = "Qui peut ouvrir l'interface : [\"user:moi@exemple.com\", \"group:equipe@exemple.com\"]."
  type        = list(string)
  default     = []
}

variable "layout_parser" {
  description = "true = parsing Document AI (tableaux, titres des PDF) ; payant à la page."
  type        = bool
  default     = true
}

variable "rag_tier" {
  description = "Palier de la base RagManagedDb du projet+région : « » (ne pas y toucher), « basic » ou « scaled ». Voir docs/08-couts.md."
  type        = string
  default     = ""
  validation {
    condition     = contains(["", "basic", "scaled"], var.rag_tier)
    error_message = "rag_tier : « », « basic » ou « scaled »."
  }
}

variable "ge_serving_config" {
  description = "Hybride (sous-projet 3) : chemin d'une app Gemini Enterprise / Vertex AI Search (…/engines/<app>/servingConfigs/default_search). Vide = kit 1 seul."
  type        = string
  default     = ""
}

variable "push" {
  description = "true = notifications push de Google Drive (service public <prefix>-hook) : synchro en quelques secondes."
  type        = bool
  default     = true
}
