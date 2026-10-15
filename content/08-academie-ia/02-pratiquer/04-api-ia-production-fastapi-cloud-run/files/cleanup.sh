#!/usr/bin/env bash
# Supprime TOUT ce que deploy.sh a créé, puis vérifie.  Usage : PROJECT_ID=mon-projet ./cleanup.sh
set -uo pipefail
PROJECT_ID="${PROJECT_ID:?définissez PROJECT_ID}"; REGION="${REGION:-europe-west1}"
SA="lab-api-ia@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud run services delete lab-api-ia --region "$REGION" --project "$PROJECT_ID" --quiet
gcloud artifacts repositories delete lab-api-ia --location "$REGION" --project "$PROJECT_ID" --quiet  # supprime aussi les images
gcloud storage rm --recursive "gs://lab-api-ia-build-${PROJECT_ID}"
gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:${SA}" --role roles/aiplatform.user --condition=None --quiet >/dev/null
gcloud iam service-accounts delete "$SA" --project "$PROJECT_ID" --quiet

echo "--- vérification (tout doit être vide)"
gcloud run services list --region "$REGION" --project "$PROJECT_ID" --filter "metadata.name=lab-api-ia" --format "value(metadata.name)"
gcloud artifacts repositories list --location "$REGION" --project "$PROJECT_ID" --filter "name~lab-api-ia" --format "value(name)"
gcloud storage buckets list --project "$PROJECT_ID" --filter "name~lab-api-ia" --format "value(name)"
gcloud iam service-accounts list --project "$PROJECT_ID" --filter "email~lab-api-ia" --format "value(email)"
echo "--- fin"
