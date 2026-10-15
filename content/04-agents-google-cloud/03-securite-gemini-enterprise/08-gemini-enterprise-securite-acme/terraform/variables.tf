# =============================================================================
# 1. Projet et localisation
# =============================================================================
variable "project_id" {
  description = "Projet GCP (dans l'organisation Google Workspace du client)."
  type        = string
}

variable "region" {
  description = "Région par défaut des ressources régionales (Agent Gateway...)."
  type        = string
  default     = "europe-west1"
}

variable "ge_location" {
  description = "Multi-région de l'app Gemini Enterprise. 'eu' pour un client français : résidence UE, et CMEK impossible en 'global'. IMMUABLE."
  type        = string
  default     = "eu"
  validation {
    condition     = contains(["eu", "us"], var.ge_location)
    error_message = "Utilisez 'eu' ou 'us' : CMEK et Access Transparency ne sont pas supportés en 'global'."
  }
}

variable "app_id" {
  type    = string
  default = "assistant-ia"
}

variable "app_display_name" {
  type    = string
  default = "Assistant IA"
}

variable "company_name" {
  type    = string
  default = "Acme"
}

# =============================================================================
# 2. Identité et accès (groupes uniquement)
# =============================================================================
variable "identity_provider" {
  description = "GSUITE (Google Workspace / Cloud Identity) ou THIRD_PARTY (Entra ID via Workforce Identity Federation)."
  type        = string
  default     = "GSUITE"
  validation {
    condition     = contains(["GSUITE", "THIRD_PARTY"], var.identity_provider)
    error_message = "identity_provider doit valoir GSUITE ou THIRD_PARTY."
  }
}

variable "workforce_pool" {
  description = "Si THIRD_PARTY : 'locations/global/workforcePools/POOL_ID'."
  type        = string
  default     = ""
}

variable "user_groups" {
  description = "Groupes autorisés à utiliser l'app (rôle agentspaceUser)."
  type        = list(string)
}

variable "admin_groups" {
  description = "Administrateurs Gemini Enterprise (rôle agentspaceAdmin). Petit groupe."
  type        = list(string)
}

variable "security_groups" {
  description = "Équipe sécurité : SEULE à gérer Model Armor, les clés KMS et à lire les journaux privés."
  type        = list(string)
}

variable "viewer_groups" {
  description = "Lecture seule + analytics (pilotage, DPO). Optionnel."
  type        = list(string)
  default     = []
}

# =============================================================================
# 3. Protection des données
# =============================================================================
variable "enable_cmek" {
  description = "Chiffrement avec les clés du client (Cloud KMS). Doit être activé AVANT la création de l'app."
  type        = bool
  default     = true
}

variable "kms_key_ring" {
  type    = string
  default = "gemini-enterprise"
}

variable "session_ttl_days" {
  description = "Durée de conservation des conversations (défaut Google : 60 jours). Minimisation RGPD."
  type        = number
  default     = 30
}

# =============================================================================
# 4. Connecteurs (générique : une entrée = une source)
# =============================================================================
variable "connectors" {
  description = "Sources de données. Voir terraform.tfvars.example et le guide (section Connecteurs)."
  type = map(object({
    data_source      = string # google_drive, sharepoint, github, jira, bigquery...
    display_name     = string
    modes            = optional(list(string), ["FEDERATED"]) # FEDERATED = pas de copie, droits de la source
    params           = optional(map(string), {})             # paramètres non secrets
    secret_params    = optional(map(string), {})             # clé du paramètre => ID du secret Secret Manager
    entities         = optional(list(object({ name = string, params = optional(string) })), [])
    refresh_interval = optional(string, "86400s")
    static_ip        = optional(bool, false) # IP sortantes fixes à autoriser côté SaaS (IMMUABLE)
  }))
  default = {}
}

variable "extra_data_store_ids" {
  description = "Data stores créés hors Terraform (console) à rattacher à l'app."
  type        = list(string)
  default     = []
}

# =============================================================================
# 5. Filtrage IA (Model Armor)
# =============================================================================
variable "armor_confidence" {
  description = "Seuil des filtres injection/jailbreak et contenus : LOW_AND_ABOVE (strict), MEDIUM_AND_ABOVE (équilibré), HIGH."
  type        = string
  default     = "MEDIUM_AND_ABOVE"
  validation {
    condition     = contains(["LOW_AND_ABOVE", "MEDIUM_AND_ABOVE", "HIGH"], var.armor_confidence)
    error_message = "armor_confidence doit valoir LOW_AND_ABOVE, MEDIUM_AND_ABOVE ou HIGH."
  }
}

variable "sdp_mode" {
  description = "advanced = détecteurs FR/UE (NIR, CNI, IBAN...) via un template DLP ; basic = détecteurs Google par défaut (orientés US)."
  type        = string
  default     = "advanced"
  validation {
    # Une faute de frappe désactiverait silencieusement la détection des données sensibles.
    condition     = contains(["advanced", "basic"], var.sdp_mode)
    error_message = "sdp_mode doit valoir advanced ou basic."
  }
}

variable "dlp_location" {
  description = "Localisation du template DLP (à valider en recette avec un template Model Armor 'eu')."
  type        = string
  default     = "europe"
}

variable "sensitive_info_types" {
  description = "Types de données bloqués dans les prompts et réponses (mode advanced)."
  type        = list(string)
  default = [
    "FRANCE_NIR", "FRANCE_CNI", "FRANCE_PASSPORT", "FRANCE_TAX_IDENTIFICATION_NUMBER",
    "IBAN_CODE", "CREDIT_CARD_NUMBER",
    "GCP_CREDENTIALS", "GCP_API_KEY", "AUTH_TOKEN", "AWS_CREDENTIALS", "ENCRYPTION_KEY",
  ]
}

variable "log_screened_content" {
  description = "Journaliser le CONTENU filtré par Model Armor. Google le déconseille pour Gemini Enterprise (prompts lisibles dans les logs)."
  type        = bool
  default     = false
}

variable "banned_phrases" {
  description = "Expressions que l'assistant ne doit jamais produire (noms de code de projets confidentiels...)."
  type        = list(string)
  default     = []
}

# =============================================================================
# 6. Exposition et fonctionnalités
# =============================================================================
variable "web_grounding" {
  description = "WEB_GROUNDING_TYPE_DISABLED (défaut) | WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH. Google Search grounding est incompatible avec résidence des données et CMEK."
  type        = string
  default     = "WEB_GROUNDING_TYPE_DISABLED"
  validation {
    condition     = contains(["WEB_GROUNDING_TYPE_DISABLED", "WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH", "WEB_GROUNDING_TYPE_GOOGLE_SEARCH"], var.web_grounding)
    error_message = "Valeur de web_grounding inconnue."
  }
}

variable "features" {
  description = "Fonctionnalités de l'app (clés de l'API Engine.features)."
  type        = map(string)
  default = {
    "disable-agent-sharing"                = "FEATURE_STATE_ON"  # pas de partage d'agents maison tant que la gouvernance n'est pas définie
    "skill-sharing-without-admin-approval" = "FEATURE_STATE_OFF" # partage de skills = validation admin
    "session-sharing"                      = "FEATURE_STATE_OFF" # une conversation (souvent confidentielle) ne se partage pas
    "feedback"                             = "FEATURE_STATE_ON"  # retours utilisateurs pour le pilotage
  }
}

variable "enable_observability" {
  description = "Traces OpenTelemetry de l'app (SANS le contenu des prompts)."
  type        = bool
  default     = true
}

# =============================================================================
# 7. Options avancées (désactivées par défaut)
# =============================================================================
variable "enable_agent_gateway" {
  description = "Agent Gateway en sortie (AGENT_TO_ANYWHERE). Utile dès qu'il y a des agents personnalisés / outils MCP."
  type        = bool
  default     = false
}

variable "agent_gateway_allowed_mcp_servers" {
  description = "IDs des serveurs MCP (Agent Registry, global) que Gemini Enterprise et les agents peuvent joindre via Agent Gateway. Tout le reste est refusé."
  type        = list(string)
  default     = []
}

variable "vpc_sc_access_policy" {
  description = "ID numérique de la politique Access Context Manager de l'organisation. Vide = pas de périmètre VPC-SC."
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Boîte de l'équipe sécurité pour les alertes."
  type        = string
  default     = ""
}

# =============================================================================
# 8. Journalisation (usage et sécurité)
# =============================================================================
variable "log_prompts_responses" {
  description = "Journaliser le TEXTE complet des questions et réponses (gen_ai.user.message / gen_ai.choice). Données personnelles : décision DPO/CSE."
  type        = bool
  default     = false
}

variable "security_log_retention_days" {
  description = "Conservation des journaux de sécurité (audit, Model Armor) dans le bucket dédié."
  type        = number
  default     = 365
}

variable "usage_log_retention_days" {
  description = "Conservation des journaux d'usage (activité des utilisateurs, peut contenir des questions). Minimisation RGPD."
  type        = number
  default     = 90
}

variable "lock_security_logs" {
  description = "Verrouiller le bucket de sécurité (personne ne peut réduire la rétention ni le supprimer). IRRÉVERSIBLE."
  type        = bool
  default     = false
}

variable "link_logs_to_bigquery" {
  description = "Exposer les buckets de logs dans BigQuery (dataset lié, lecture seule, sans copie) pour des tableaux de bord."
  type        = bool
  default     = false
}

# =============================================================================
# 9. Mesures de la note de sécurité Acme (projet 08)
# =============================================================================
variable "armor_agent_platform_mode" {
  description = "Model Armor sur TOUS les appels Gemini du projet (agents personnalisés, Agent Runtime) via le plancher : off | inspect (observer) | block."
  type        = string
  default     = "inspect"
  validation {
    condition     = contains(["off", "inspect", "block"], var.armor_agent_platform_mode)
    error_message = "armor_agent_platform_mode : off, inspect ou block."
  }
}

variable "vpc_sc_enforce" {
  description = "false = périmètre VPC-SC en observation seule (dry-run). true = appliqué (bloque). Passer à true après 2 semaines sans violation légitime."
  type        = bool
  default     = false
}

variable "corporate_ip_ranges" {
  description = "Plages IP publiques de sortie Acme (CIDR). Utilisées par le niveau d'accès VPC-SC. Vide = pas de niveau d'accès."
  type        = list(string)
  default     = []
}

variable "enable_siem_export" {
  description = "Exporter les journaux de sécurité vers un topic Pub/Sub lu par le SIEM (SOC)."
  type        = bool
  default     = false
}

variable "siem_subscriber" {
  description = "Identité du connecteur SIEM qui lit l'abonnement (ex. serviceAccount:siem@soc-proj.iam.gserviceaccount.com). Vide = à câbler plus tard."
  type        = string
  default     = ""
}

variable "access_approval_emails" {
  description = "Destinataires des demandes Access Approval (accès de Google à vos données). Vide = désactivé. Prérequis : Access Transparency activé sur l'organisation."
  type        = list(string)
  default     = []
}

variable "deploy_secure_agent" {
  description = "Déployer l'agent exemple sur Agent Runtime (identité dédiée, Model Armor, validation humaine)."
  type        = bool
  default     = false
}

variable "agent_model" {
  description = "Modèle de l'agent exemple."
  type        = string
  default     = "gemini-3.5-flash"
}

variable "agent_developer_groups" {
  description = "Groupes autorisés à enregistrer des agents/outils dans Agent Registry (rôle editor), format \"group:x@acme.example\". Les utilisateurs GE ont le rôle viewer."
  type        = list(string)
  default     = []
}

variable "swp" {
  description = "Secure Web Proxy (optionnel) pour les charges dans VOTRE VPC (Agent Runtime via PSC-I, Cloud Run en sortie VPC). null = désactivé."
  type = object({
    network         = string       # projects/P/global/networks/N
    subnetwork      = string       # sous-réseau des charges
    proxy_only_cidr = string       # ex. 10.129.0.0/23, réservé au proxy
    address         = string       # IP du proxy dans le sous-réseau
    allowed_hosts   = list(string) # domaines autorisés, ex. ["*.googleapis.com", "api.github.com"]
  })
  default = null
}

variable "enforce_org_policies" {
  description = "Poser au niveau du PROJET les politiques d'organisation anti-Shadow AI (Cloud Run non public, partage IAM limité au domaine, ressources en UE). Exige roles/orgpolicy.policyAdmin."
  type        = bool
  default     = false
}

variable "workspace_customer_id" {
  description = "ID client Google Workspace (Admin console > Compte > Paramètres du compte, ex. C0abc123). Utilisé par la restriction de partage au domaine."
  type        = string
  default     = ""
}
