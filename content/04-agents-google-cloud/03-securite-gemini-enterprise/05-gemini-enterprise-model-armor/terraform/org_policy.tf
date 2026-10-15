# Data residency guard-rail: nobody can create resources outside the EU in this
# project, even by mistake. Optional because it needs an org-level role.
resource "google_org_policy_policy" "eu_only" {
  count  = var.enforce_eu_locations ? 1 : 0
  name   = "projects/${var.project_id}/policies/gcp.resourceLocations"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      values {
        allowed_values = ["in:eu-locations"]
      }
    }
  }

  depends_on = [google_project_service.apis]
}
