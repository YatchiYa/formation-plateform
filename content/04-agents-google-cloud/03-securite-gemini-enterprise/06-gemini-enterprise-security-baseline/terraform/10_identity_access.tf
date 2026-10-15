# COUCHE 1 - IDENTITÉ ET ACCÈS
# Qui peut entrer (SSO), qui peut faire quoi (rôles), et qui ne peut PAS
# désactiver la sécurité (séparation des rôles).

# 1.1 Fournisseur d'identité de l'app (un seul par localisation).
resource "google_discovery_engine_acl_config" "identity" {
  location = var.ge_location
  idp_config {
    idp_type = var.identity_provider
    dynamic "external_idp_config" {
      for_each = var.identity_provider == "THIRD_PARTY" ? [1] : []
      content {
        workforce_pool_name = var.workforce_pool
      }
    }
  }
  depends_on = [google_project_service.apis]
}

# 1.2 Rôles, attribués à des GROUPES (arrivées/départs gérés dans l'annuaire).
locals {
  role_bindings = merge(
    { for g in var.user_groups : "user|${g}" => { role = "roles/discoveryengine.agentspaceUser", member = g } },
    { for g in var.admin_groups : "admin|${g}" => { role = "roles/discoveryengine.agentspaceAdmin", member = g } },
    { for g in var.viewer_groups : "viewer|${g}" => { role = "roles/discoveryengine.agentspaceViewer", member = g } },
    # 1.3 Séparation des rôles : la sécurité possède les garde-fous, les clés et les journaux privés.
    { for g in var.security_groups : "armor|${g}" => { role = "roles/modelarmor.admin", member = g } },
    { for g in var.security_groups : "kms|${g}" => { role = "roles/cloudkms.admin", member = g } },
    { for g in var.security_groups : "logs|${g}" => { role = "roles/logging.privateLogViewer", member = g } },
  )
}

resource "google_project_iam_member" "access" {
  for_each = local.role_bindings
  project  = var.project_id
  role     = each.value.role
  member   = each.value.member
}
