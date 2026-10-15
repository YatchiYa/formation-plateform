#!/usr/bin/env bash
# Supprime les 2 services, les 2 comptes de service, leurs rôles et le dépôt d'images, puis vérifie.
set -uo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
REGION="${REGION:-europe-west1}"
for S in lab-a2a-stock lab-a2a-commandes; do
  gcloud run services delete "$S" --region "$REGION" --project "$PROJECT_ID" --quiet
  gcloud projects remove-iam-policy-binding "$PROJECT_ID" --condition None >/dev/null \
    --member "serviceAccount:${S}@${PROJECT_ID}.iam.gserviceaccount.com" --role roles/aiplatform.user
  gcloud iam service-accounts delete "${S}@${PROJECT_ID}.iam.gserviceaccount.com" --project "$PROJECT_ID" --quiet
done
gcloud artifacts repositories delete lab-agents-a2a --location "$REGION" --project "$PROJECT_ID" --quiet

echo "--- Vérification (doit être vide) ---"
gcloud run services list --project "$PROJECT_ID" --format 'value(metadata.name)' | grep '^lab-a2a-'
gcloud iam service-accounts list --project "$PROJECT_ID" --format 'value(email)' | grep '^lab-a2a-'
gcloud artifacts repositories list --project "$PROJECT_ID" --format 'value(name)' 2>/dev/null | grep 'lab-agents-a2a'

# `gcloud builds submit` a déposé l'archive des sources dans gs://<projet>_cloudbuild/source/.
# Si ce bucket ne sert qu'à ce lab : gcloud storage rm -r "gs://${PROJECT_ID}_cloudbuild"
