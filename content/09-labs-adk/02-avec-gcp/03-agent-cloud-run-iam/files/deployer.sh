#!/usr/bin/env bash
# Déploie l'assistant interne en service Cloud Run PRIVÉ avec un compte de service dédié.
# Usage : PROJECT_ID=mon-projet ./deployer.sh   (à lancer depuis ce dossier files/)
set -euo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
REGION="${REGION:-europe-west1}"
SLUG="agent-cloud-run-iam"
SERVICE="lab-${SLUG}"
SA="${SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com"

# 1. Compte de service dédié, sans aucun rôle au départ
gcloud iam service-accounts describe "$SA" --project "$PROJECT_ID" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SERVICE" --project "$PROJECT_ID" \
    --display-name "Lab ${SLUG} : identité de l'agent"

# 2. Un seul rôle : appeler Gemini sur Vertex AI
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:${SA}" --role roles/aiplatform.user --condition None >/dev/null

# 3. Construction + déploiement (Cloud Build -> Artifact Registry -> Cloud Run)
adk deploy cloud_run \
  --project "$PROJECT_ID" --region "$REGION" \
  --service_name "$SERVICE" --app_name assistant_interne \
  --env GOOGLE_GENAI_USE_VERTEXAI=TRUE --env MODEL="${MODEL:-gemini-2.5-flash}" \
  . \
  -- --no-allow-unauthenticated --service-account "$SA" \
     --max-instances 1 --memory 1Gi --labels "formation-lab=${SLUG}"

gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" \
  --format 'value(status.url)'
