#!/usr/bin/env bash
# Supprime le bucket ET tout son contenu (images + rapport), puis vérifie.
set -uo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
BUCKET="${BUCKET:-lab-inspection-qualite-${PROJECT_ID}}"
gcloud storage rm -r "gs://${BUCKET}" --project "$PROJECT_ID"
gcloud storage buckets list --project "$PROJECT_ID" --filter "name=${BUCKET}" --format 'value(name)'  # doit être vide
