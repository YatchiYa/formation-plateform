---
title: Installation et premier corpus
description: Préparer le projet GCP, créer l'infrastructure avec Terraform et indexer les premiers documents.
duration: 1h
---

## 1. Préparer le projet

```bash
export PROJECT_ID="main-project-511608"
export REGION="europe-west1"

gcloud config set project "$PROJECT_ID"
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com

gcloud auth application-default login
```

> [!IMPORTANT]
> RAG Engine n'est pas disponible dans toutes les régions. Vérifiez la liste des régions supportées dans la documentation avant de choisir `REGION` : le corpus, le bucket et l'agent doivent idéalement être co-localisés.

## 2. L'infrastructure en Terraform

```hcl
resource "google_storage_bucket" "sources" {
  name                        = "${var.project_id}-rag-sources"
  location                    = var.region
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

resource "google_service_account" "agent" {
  account_id   = "rag-agent"
  display_name = "Agent RAG (Cloud Run)"
}

resource "google_project_iam_member" "agent_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent.email}"
}

resource "google_storage_bucket_iam_member" "agent_read" {
  bucket = google_storage_bucket.sources.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.agent.email}"
}
```

> [!WARNING]
> L'agent de service Vertex AI (`service-PROJECT_NUMBER@gcp-sa-vertex-rag.iam.gserviceaccount.com`) doit lui aussi pouvoir lire le bucket, sinon l'import échoue avec une erreur de permission peu explicite.

## 3. Créer le corpus et importer

```python
import vertexai
from vertexai import rag

vertexai.init(project="main-project-511608", location="europe-west1")

corpus = rag.create_corpus(
    display_name="docs-internes",
    backend_config=rag.RagVectorDbConfig(
        rag_embedding_model_config=rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model="publishers/google/models/text-embedding-005"
            )
        )
    ),
)

rag.import_files(
    corpus.name,
    ["gs://main-project-511608-rag-sources/docs/"],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
)
print(corpus.name)
```

> [!CAUTION]
> `rag.delete_corpus()` supprime définitivement l'index **et** les embeddings calculés. Il n'y a pas de corbeille : une réindexation complète d'un gros corpus peut coûter plusieurs heures et des quotas d'embedding.

## 4. Configuration de l'agent

```yaml
# agent.yaml
model: gemini-2.5-flash
corpus: projects/main-project-511608/locations/europe-west1/ragCorpora/1234567890
retrieval:
  top_k: 5
  vector_distance_threshold: 0.5
instructions: |
  Réponds uniquement à partir du contexte fourni.
  Cite les documents sources.
```

Exemple de réponse brute de `retrieval_query` :

```json
{
  "contexts": {
    "contexts": [
      {
        "sourceUri": "gs://main-project-511608-rag-sources/docs/vpc-sc.md",
        "text": "Le périmètre VPC Service Controls protège...",
        "score": 0.27
      }
    ]
  }
}
```

## Démonstration

![Démo](../files/demo.mp4)

Pour aller plus loin, une présentation vidéo :

https://www.youtube.com/watch?v=dQw4w9WgXcQ
