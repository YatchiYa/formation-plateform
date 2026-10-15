# --- Where ---------------------------------------------------------------------
variable "project_id" {
  description = "GCP project ID (must be linked to your Google Workspace organization)."
  type        = string
}

variable "ge_location" {
  description = "Gemini Enterprise multi-region: global, eu or us. Cannot be changed after creation."
  type        = string
  default     = "eu"
}

variable "armor_location" {
  description = "Model Armor template location. Must be 'eu' for an eu app, 'us' for a us app, 'eu' or 'us' for global."
  type        = string
  default     = "eu"
}

variable "region" {
  description = "Region of the custom agent (Agent Runtime). Use an EU region for an eu app."
  type        = string
  default     = "europe-west1"
}

# --- App -----------------------------------------------------------------------
variable "app_id" {
  description = "Gemini Enterprise app (engine) ID."
  type        = string
  default     = "company-assistant"
}

variable "app_display_name" {
  type    = string
  default = "Company Assistant"
}

variable "company_name" {
  description = "Helps Gemini answer with company context."
  type        = string
  default     = "Novagen"
}

variable "assistant_language" {
  description = "Default answer language (ISO 639-1)."
  type        = string
  default     = "fr"
}

variable "assistant_instruction" {
  description = "Extra system instruction for the Gemini Enterprise assistant."
  type        = string
  default     = "You are the internal assistant of the company. Prefer company documents over the web, cite your sources, and never ask users for passwords or personal data."
}

variable "banned_phrases" {
  description = "Phrases the assistant must never output (exact policy, on top of Model Armor)."
  type        = list(string)
  default     = ["project nightingale"]
}

variable "web_grounding" {
  description = "WEB_GROUNDING_TYPE_DISABLED, WEB_GROUNDING_TYPE_GOOGLE_SEARCH or WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH."
  type        = string
  default     = "WEB_GROUNDING_TYPE_DISABLED" # no query leaves for the public web unless you decide so
}

variable "logo_url" {
  description = "Public HTTPS URL of your logo for the web app (empty = default)."
  type        = string
  default     = ""
}

# --- People --------------------------------------------------------------------
variable "users" {
  description = "Who may use the app, e.g. [\"group:all@novagen.tech\"] or [\"user:yarab@novagen.tech\"]."
  type        = list(string)
  default     = []
}

variable "admins" {
  description = "Gemini Enterprise admins (manage agents, connectors, settings)."
  type        = list(string)
  default     = []
}

# --- Licences (BILLED!) --------------------------------------------------------
variable "license_count" {
  description = "Licences to buy through Terraform. 0 = manage licences in the console (recommended to start)."
  type        = number
  default     = 0
}

variable "license_free_trial" {
  description = "Request a free trial instead of a paid subscription (if your org is eligible)."
  type        = bool
  default     = true
}

variable "license_start_date" {
  description = "Licence start date, YYYY-MM-DD."
  type        = string
  default     = "2026-10-05"
}

# --- Security ------------------------------------------------------------------
variable "floor_setting_mode" {
  description = "Project-wide Model Armor floor for Agent Platform Gemini calls: OFF, INSPECT_ONLY or INSPECT_AND_BLOCK."
  type        = string
  default     = "INSPECT_ONLY"
  validation {
    condition     = contains(["OFF", "INSPECT_ONLY", "INSPECT_AND_BLOCK"], var.floor_setting_mode)
    error_message = "floor_setting_mode must be OFF, INSPECT_ONLY or INSPECT_AND_BLOCK."
  }
}

variable "security_admins" {
  description = "Who may change Model Armor templates/floor (security team). Separate from Gemini Enterprise admins."
  type        = list(string)
  default     = []
}

variable "alert_email" {
  description = "Email notified when Model Armor blocks spike (possible attack). Empty = no email channel."
  type        = string
  default     = ""
}

variable "alert_threshold" {
  description = "Model Armor matches in 10 minutes that trigger the alert."
  type        = number
  default     = 20
}

variable "enforce_eu_locations" {
  description = "Org policy: only allow EU locations in this project (needs roles/orgpolicy.policyAdmin)."
  type        = bool
  default     = false
}

# --- Custom agent --------------------------------------------------------------
variable "model" {
  description = "Gemini model used by the custom agent."
  type        = string
  default     = "gemini-3.5-flash"
}
