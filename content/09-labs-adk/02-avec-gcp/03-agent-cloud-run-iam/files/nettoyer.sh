#!/usr/bin/env bash
# Supprime TOUT ce que deployer.sh a créé, puis vérifie.
set -uo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
REGION="${REGION:-europe-west1}"
SERVICE="lab-agent-cloud-run-iam"
SA="${SERVICE}@${PROJECT_ID}.iam.gserviceaccount.com"
REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy"

gcloud run services delete "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --quiet
gcloud projects remove-iam-policy-binding "$PROJECT_ID" \
  --member "serviceAccount:${SA}" --role roles/aiplatform.user --condition None >/dev/null
gcloud iam service-accounts delete "$SA" --project "$PROJECT_ID" --quiet
# L'image construite par Cloud Build (le dépôt peut servir à d'autres services : on ne supprime que la nôtre)
gcloud artifacts docker images delete "${REPO}/${SERVICE}" --delete-tags --quiet 2>/dev/null
# Les sources zippées envoyées par le déploiement « --source »
gcloud storage rm -r "gs://run-sources-${PROJECT_ID}-${REGION}/services/${SERVICE}/" 2>/dev/null

echo "--- Vérification (doit être vide) ---"
gcloud run services list --project "$PROJECT_ID" --region "$REGION" --format 'value(metadata.name)' | grep -x "${SERVICE}"
gcloud iam service-accounts list --project "$PROJECT_ID" --filter "email=${SA}" --format 'value(email)'
gcloud artifacts docker images list "$REPO" --filter "package~${SERVICE}" --format 'value(package)' 2>/dev/null

# Si ce lab était votre seul déploiement « --source » dans la région, le dépôt et le bucket de sources
# créés automatiquement sont désormais inutiles (ils gardent des couches d'image orphelines) :
#   gcloud artifacts repositories delete cloud-run-source-deploy --location "$REGION" --project "$PROJECT_ID"
#   gcloud storage rm -r "gs://run-sources-${PROJECT_ID}-${REGION}"
