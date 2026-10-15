#!/usr/bin/env bash
# Supprimer tout ce que deployer_shell.sh a créé (pour un déploiement Terraform : terraform destroy).
#
#   source scripts/config.sh config/test.env && bash scripts/supprimer_shell.sh
#
# Supprime : service, job, planification, corpus (et tout son index), processeur Document AI, images,
# bucket (fichiers déposés compris), comptes de service et leurs droits. Les dossiers Drive ne sont PAS touchés.
# Ne désactive pas les API et ne change pas le palier RagManagedDb (voir docs/10-tout-supprimer.md).
set -uo pipefail
cd "$(dirname "$0")/.."
: "${PROJECT_ID:?Configuration non chargée : source scripts/config.sh config/<fichier>.env}"
P="$PROJECT_ID"; R="$REGION"
rest() { curl -sS -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "x-goog-user-project: $P" "$@"; }
jq_() { python3 -c "import json,sys; d=json.load(sys.stdin); $1"; }

read -r -p "Supprimer le kit « $PREFIX » du projet $P (index et fichiers déposés compris) ? Tapez oui : " ok
[ "$ok" = "oui" ] || { echo "Annulé."; exit 1; }

gcloud run services delete "$SERVICE" --region="$R" --project="$P" -q
gcloud run services delete "$PREFIX-hook" --region="$R" --project="$P" -q 2>/dev/null
for s in oauth-client google-tokens; do gcloud secrets delete "$PREFIX-$s" --project="$P" -q 2>/dev/null; done
KEY="$(gcloud services api-keys list --project="$P" --filter="displayName='$PREFIX-picker'" --format='value(name)' | head -1)"
[ -n "$KEY" ] && gcloud services api-keys delete "$KEY" --project="$P" -q
gcloud scheduler jobs delete "$SYNC_JOB" --location="$R" --project="$P" -q
gcloud run jobs delete "$SYNC_JOB" --region="$R" --project="$P" -q

API="https://${R}-aiplatform.googleapis.com/v1/projects/${P}/locations/${R}"
CORPUS="$(rest "$API/ragCorpora?pageSize=100" | jq_ "print(next((c['name'] for c in d.get('ragCorpora',[]) if c['displayName']=='$PREFIX'), ''))")"
[ -n "$CORPUS" ] && rest -X DELETE "https://${R}-aiplatform.googleapis.com/v1/$CORPUS?force=true" >/dev/null && echo "corpus supprimé : $CORPUS"

DAI="https://eu-documentai.googleapis.com/v1/projects/$P/locations/eu/processors"
LAYOUT="$(rest "$DAI" | jq_ "print(next((p['name'] for p in d.get('processors',[]) if p['displayName']=='$PREFIX-layout'), ''))")"
[ -n "$LAYOUT" ] && rest -X DELETE "https://eu-documentai.googleapis.com/v1/$LAYOUT" >/dev/null && echo "processeur supprimé : $LAYOUT"

gcloud artifacts repositories delete "$PREFIX" --location="$R" --project="$P" -q
gcloud storage rm -r "gs://$BUCKET" -q

for role in roles/aiplatform.user roles/discoveryengine.viewer roles/logging.logWriter roles/monitoring.metricWriter \
            roles/cloudtrace.agent roles/telemetry.writer; do
  gcloud projects remove-iam-policy-binding "$P" --member="serviceAccount:$SA_EMAIL" --role="$role" --condition=None -q >/dev/null 2>&1
done
for role in roles/storage.objectViewer roles/artifactregistry.writer roles/logging.logWriter; do
  gcloud projects remove-iam-policy-binding "$P" --member="serviceAccount:$BUILD_SA" --role="$role" --condition=None -q >/dev/null 2>&1
done
for sa in "$SA_EMAIL" "$SCHEDULER_SA" "$BUILD_SA"; do
  gcloud iam service-accounts delete "$sa" --project="$P" -q
done

echo
echo "== Terminé. Pensez à retirer $SA_EMAIL et $RAG_AGENT du partage de vos dossiers Drive."
