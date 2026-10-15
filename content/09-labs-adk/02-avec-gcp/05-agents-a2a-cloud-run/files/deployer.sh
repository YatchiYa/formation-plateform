#!/usr/bin/env bash
# Déploie les deux agents en services Cloud Run PRIVÉS ; seul agent_commandes peut appeler agent_stock.
# Usage : PROJECT_ID=mon-projet ./deployer.sh   (depuis ce dossier files/)
set -euo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
REGION="${REGION:-europe-west1}"
LABEL="formation-lab=agents-a2a-cloud-run"
NUM=$(gcloud projects describe "$PROJECT_ID" --format 'value(projectNumber)')
STOCK=lab-a2a-stock; CMD=lab-a2a-commandes
# URL déterministe de Cloud Run : connue AVANT le déploiement, donc utilisable dans la carte A2A
STOCK_URL="https://${STOCK}-${NUM}.${REGION}.run.app"
CMD_URL="https://${CMD}-${NUM}.${REGION}.run.app"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/lab-agents-a2a/agents:v1"
VERTEX="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},MODEL=${MODEL:-gemini-2.5-flash}"

# 1. Dépôt d'images + construction (une seule image pour les deux services)
gcloud artifacts repositories create lab-agents-a2a --repository-format docker \
  --location "$REGION" --project "$PROJECT_ID" --labels "$LABEL"
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID" --region "$REGION" .

# 2. Une identité par agent, avec le seul droit d'appeler Gemini
for SA in $STOCK $CMD; do
  gcloud iam service-accounts create "$SA" --project "$PROJECT_ID" --display-name "Lab A2A : $SA"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" --condition None >/dev/null \
    --member "serviceAccount:${SA}@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/aiplatform.user
done

# 3. Agent stock (privé)
gcloud run deploy "$STOCK" --image "$IMAGE" --region "$REGION" --project "$PROJECT_ID" \
  --no-allow-unauthenticated --service-account "${STOCK}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars "MODULE=stock_agent,PUBLIC_URL=${STOCK_URL},${VERTEX}" \
  --max-instances 1 --memory 1Gi --labels "$LABEL"

# 4. Seul le compte de service de agent_commandes peut invoquer agent_stock
gcloud run services add-iam-policy-binding "$STOCK" --region "$REGION" --project "$PROJECT_ID" \
  --member "serviceAccount:${CMD}@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/run.invoker

# 5. Agent commandes (privé lui aussi)
gcloud run deploy "$CMD" --image "$IMAGE" --region "$REGION" --project "$PROJECT_ID" \
  --no-allow-unauthenticated --service-account "${CMD}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --set-env-vars "MODULE=commandes_agent,PUBLIC_URL=${CMD_URL},STOCK_URL=${STOCK_URL},${VERTEX}" \
  --max-instances 1 --memory 1Gi --labels "$LABEL"

echo "STOCK_URL=${STOCK_URL}"
echo "CMD_URL=${CMD_URL}"
