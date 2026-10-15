#!/usr/bin/env bash
# Déploie l'API sur Cloud Run : service privé, compte de service dédié, Gemini via Vertex AI (aucune clé).
# Usage : PROJECT_ID=mon-projet ./deploy.sh
set -euo pipefail
PROJECT_ID="${PROJECT_ID:?définissez PROJECT_ID}"
REGION="${REGION:-europe-west1}"
SERVICE="lab-api-ia"
LABEL="formation-lab=api-ia"
SA="lab-api-ia@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE}/api:v1"
STAGING="gs://${SERVICE}-build-${PROJECT_ID}"

# 1. APIs nécessaires (sans effet si elles sont déjà actives)
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com aiplatform.googleapis.com --project "$PROJECT_ID"

# 2. Dépôt d'images + bucket de dépôt des sources pour Cloud Build
gcloud artifacts repositories create "$SERVICE" --repository-format=docker \
  --location "$REGION" --labels "$LABEL" --project "$PROJECT_ID"
gcloud storage buckets create "$STAGING" --location "$REGION" \
  --uniform-bucket-level-access --project "$PROJECT_ID"

# 3. Compte de service dédié : il ne peut QUE appeler Vertex AI
gcloud iam service-accounts create lab-api-ia --display-name "API tickets (lab)" --project "$PROJECT_ID"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:${SA}" --role roles/aiplatform.user --condition=None --quiet >/dev/null

# 4. Construire l'image dans Cloud Build (pas besoin de Docker en local)
gcloud builds submit --tag "$IMAGE" --gcs-source-staging-dir "${STAGING}/source" \
  --region "$REGION" --project "$PROJECT_ID" .

# 5. Déployer : privé, borné, observable
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" --project "$PROJECT_ID" \
  --service-account "$SA" \
  --no-allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},MODEL=gemini-2.5-flash,LLM_TIMEOUT_S=20" \
  --cpu 1 --memory 512Mi \
  --concurrency 20 --min-instances 0 --max-instances 2 \
  --timeout 60 \
  --labels "$LABEL"
