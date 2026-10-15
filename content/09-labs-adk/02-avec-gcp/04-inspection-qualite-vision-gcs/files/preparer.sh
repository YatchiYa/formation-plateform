#!/usr/bin/env bash
# Crée le bucket temporaire, génère les photos fictives et les y dépose.
set -euo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
REGION="${REGION:-europe-west1}"
BUCKET="${BUCKET:-lab-inspection-qualite-${PROJECT_ID}}"   # nom unique au monde

gcloud storage buckets create "gs://${BUCKET}" --project "$PROJECT_ID" --location "$REGION" \
  --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update "gs://${BUCKET}" --update-labels formation-lab=inspection-qualite-vision-gcs
python generer_images.py images
gcloud storage cp images/*.png "gs://${BUCKET}/images/"
echo "export BUCKET=${BUCKET}"
