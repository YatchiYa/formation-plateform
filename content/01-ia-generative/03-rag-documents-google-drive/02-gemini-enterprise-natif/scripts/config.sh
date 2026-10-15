# Charger config/<fichier>.env dans le terminal (source, jamais bash). Ne modifie rien dans Google Cloud.
#   source scripts/config.sh config/test.env
if [ -z "${1:-}" ] || [ ! -f "$1" ]; then
  echo "Usage : source scripts/config.sh config/<fichier>.env"; return 1 2>/dev/null || exit 1
fi
set -a; . "$1"; set +a
export CLOUDSDK_CORE_PROJECT="$PROJECT_ID"
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)' 2>/dev/null)"
export DE_HOST="$([ "$GE_LOCATION" = global ] && echo discoveryengine.googleapis.com || echo "$GE_LOCATION-discoveryengine.googleapis.com")"
export GE_AGENT="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
export BUCKET="${PROJECT_ID}-${PREFIX}-depots"
export TF_VAR_project_id="$PROJECT_ID" TF_VAR_project_number="$PROJECT_NUMBER" TF_VAR_ge_location="$GE_LOCATION" \
  TF_VAR_region="$REGION" TF_VAR_prefix="$PREFIX" TF_VAR_app_id="${APP_ID:-}" TF_VAR_create_app="${CREATE_APP:-false}" \
  TF_VAR_depots="${DEPOTS:-true}" TF_VAR_depots_schedule="${DEPOTS_SCHEDULE:-}"
echo "== $1 : projet $PROJECT_ID (n° ${PROJECT_NUMBER:-INCONNU}), Gemini Enterprise $GE_LOCATION, app ${APP_ID:-(aucune)}"
echo "   dépôts : ${DEPOTS:-true} (gs://$BUCKET, resynchro « ${DEPOTS_SCHEDULE:-aucune} »)"
[ -n "$PROJECT_NUMBER" ] && echo "   OK" || echo "   À CORRIGER : projet introuvable ou pas de droit"
