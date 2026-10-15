variable "agents_project_id" {
  description = "Projet où l'équipe Supply publie l'agent spécialiste (stock-agent)."
  type        = string
}

variable "ge_project_id" {
  description = "Projet de l'app Gemini Enterprise, où vit aussi l'agent orchestrateur."
  type        = string
}

variable "ge_location" {
  description = "Localisation de l'app Gemini Enterprise (eu, us, global)."
  type        = string
  default     = "eu"
}

variable "ge_app_id" {
  description = "ID de l'app Gemini Enterprise existante (projets 06 / 08). Vide = déployer et tester les agents sans les publier."
  type        = string
  default     = ""
}

variable "region" {
  description = "Région Agent Runtime. App 'eu' => région europe-* obligatoire (règle Google)."
  type        = string
  default     = "europe-west1"
  validation {
    condition     = can(regex("^(europe|us)-", var.region))
    error_message = "Région Agent Runtime attendue en europe-* (app eu) ou us-* (app us)."
  }
}

variable "model" {
  type    = string
  default = "gemini-3.5-flash"
}

variable "prompt_template" {
  description = "Template Model Armor des questions (sortie model_armor_templates du projet 08). Vide = Terraform crée une paire de templates dans le projet agents."
  type        = string
  default     = ""
}

variable "response_template" {
  description = "Template Model Armor des réponses. Vide si prompt_template est vide."
  type        = string
  default     = ""
}

variable "discover_via_registry" {
  description = "true : l'orchestrateur trouve l'agent stock dans Agent Registry. false : nom de ressource passé en dur."
  type        = bool
  default     = true
}

variable "publish_specialist_in_ge" {
  description = "Publier aussi l'agent stock (projet agents) directement dans l'app Gemini Enterprise (cas « ajout cross-project »)."
  type        = bool
  default     = true
}

variable "external_adk_agents" {
  description = <<-EOT
    Agents ADK DÉJÀ déployés sur Agent Runtime par d'autres équipes (n'importe quel projet), à publier
    dans l'app. Une entrée = une PR. Terraform donne aussi le droit cross-project nécessaire.
    Ex. { pricing = { engine = "projects/acme-pricing/locations/europe-west1/reasoningEngines/123",
                      display_name = "Prix et promotions", description = "..." } }
  EOT
  type = map(object({
    engine       = string
    display_name = string
    description  = string
  }))
  default = {}
}
