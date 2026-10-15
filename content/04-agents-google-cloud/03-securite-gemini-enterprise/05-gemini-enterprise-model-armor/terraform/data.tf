# Company knowledge: files in a bucket, indexed in a data store the assistant
# searches and cites. (Drive / Gmail / Calendar / SharePoint... connectors: see README.)

resource "google_storage_bucket" "docs" {
  name                        = "${var.project_id}-ge-docs"
  location                    = upper(var.ge_location) == "GLOBAL" ? "EU" : upper(var.ge_location)
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  labels                      = { data-classification = "internal" }
  versioning {
    enabled = true # a bad or malicious overwrite of a policy document can be rolled back
  }
  force_destroy = true # learning project
  depends_on    = [google_project_service.apis]
}

resource "google_storage_bucket_object" "docs" {
  for_each = fileset("${path.module}/../docs", "*")
  bucket   = google_storage_bucket.docs.name
  name     = each.value
  source   = "${path.module}/../docs/${each.value}"
}

# Gemini Enterprise reads the bucket with its own service agent.
resource "google_storage_bucket_iam_member" "ge_reads_docs" {
  bucket     = google_storage_bucket.docs.name
  role       = "roles/storage.objectViewer"
  member     = "serviceAccount:${local.sa_discoveryengine}"
  depends_on = [terraform_data.service_agents]
}

resource "google_discovery_engine_data_store" "docs" {
  location          = var.ge_location
  data_store_id     = "${var.app_id}-docs"
  display_name      = "Company documents"
  industry_vertical = "GENERIC"
  content_config    = "CONTENT_REQUIRED" # unstructured files (PDF, DOCX, HTML, TXT...)
  solution_types    = ["SOLUTION_TYPE_SEARCH"]
  # L'API renvoie un document_processing_config par défaut ; non déclaré ici, Terraform voudrait le retirer, ce qui
  # RECRÉE le data store (index perdu, ID bloqué plusieurs heures) — constaté le 14/10/2026 (gcp_rag/02).
  lifecycle {
    ignore_changes = [document_processing_config]
  }
  depends_on = [google_discovery_engine_acl_config.identity]
}

# Terraform has no "import documents" resource: call the API whenever the files change.
resource "terraform_data" "import_docs" {
  triggers_replace = [for o in google_storage_bucket_object.docs : o.md5hash]

  provisioner "local-exec" {
    command = <<-EOT
      curl -fsS -X POST \
        -H "Authorization: Bearer $(gcloud auth print-access-token)" \
        -H "Content-Type: application/json" -H "X-Goog-User-Project: ${var.project_id}" \
        "https://${local.de_host}/v1/${google_discovery_engine_data_store.docs.name}/branches/0/documents:import" \
        -d '{"gcsSource": {"inputUris": ["gs://${google_storage_bucket.docs.name}/*"], "dataSchema": "content"}, "reconciliationMode": "FULL"}'
    EOT
  }

  depends_on = [google_storage_bucket_iam_member.ge_reads_docs]
}
