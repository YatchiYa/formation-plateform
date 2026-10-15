# Charger un fichier config/*.env dans le terminal. À lancer avec « source », jamais « bash ».
#
#   source scripts/config.sh config/test.env
#
# Exporte les valeurs du fichier, calcule celles qui en dépendent (numéro de projet, noms des ressources,
# adresses à mettre dans le partage Drive), prépare Terraform (TF_VAR_…) et gcloud (projet par défaut de CE
# terminal). Ne crée et ne modifie rien dans Google Cloud. Sans danger à relancer.

if [ -z "${1:-}" ] || [ ! -f "$1" ]; then
  echo "Usage : source scripts/config.sh config/<fichier>.env   (fichiers : $(ls config/*.env 2>/dev/null | tr '\n' ' '))"
  return 1 2>/dev/null || exit 1
fi

set -a
. "$1"
set +a
export CONFIG_FICHIER="$1"

_manque=""
for _v in PROJECT_ID REGION PREFIX MODEL MODEL_LOCATION; do
  eval "[ -n \"\${$_v:-}\" ]" || _manque="$_manque $_v"
done
if [ -n "$_manque" ]; then
  echo "MANQUANT dans $1 :$_manque"
  return 1 2>/dev/null || exit 1
fi

# Valeurs calculées
export CLOUDSDK_CORE_PROJECT="$PROJECT_ID"   # projet gcloud par défaut, dans CE terminal seulement
export PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)' 2>/dev/null)"
export BUCKET="${PROJECT_ID}-${PREFIX}"
export SERVICE="$PREFIX" SYNC_JOB="${PREFIX}-sync"
export SA_EMAIL="${PREFIX}-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export SCHEDULER_SA="${PREFIX}-scheduler-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export BUILD_SA="${PREFIX}-build-sa@${PROJECT_ID}.iam.gserviceaccount.com"
export RAG_AGENT="service-${PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com"
export REPO="${REGION}-docker.pkg.dev/${PROJECT_ID}/${PREFIX}"

# Listes « a b c » -> JSON pour Terraform
_json() { python3 -c 'import json,sys; print(json.dumps(sys.argv[1].split()))' "$1"; }
export TF_VAR_project_id="$PROJECT_ID" TF_VAR_project_number="$PROJECT_NUMBER" TF_VAR_region="$REGION" TF_VAR_prefix="$PREFIX"
export TF_VAR_model="$MODEL" TF_VAR_model_location="$MODEL_LOCATION" TF_VAR_sync_schedule="$SYNC_SCHEDULE"
export TF_VAR_layout_parser="${LAYOUT_PARSER:-true}" TF_VAR_rag_tier="${RAG_TIER:-}" TF_VAR_push="${PUSH:-true}"
export TF_VAR_ge_serving_config="${GE_SERVING_CONFIG:-}"
export TF_VAR_drive_folders="$(_json "${DRIVE_FOLDERS:-}")" TF_VAR_users="$(_json "${USERS:-}")"

echo "== Configuration chargée : $1"
echo "   Projet     : $PROJECT_ID (numéro ${PROJECT_NUMBER:-INCONNU}), région $REGION, préfixe $PREFIX"
echo "   Modèle     : $MODEL sur $MODEL_LOCATION ; synchro « $SYNC_SCHEDULE » ; layout parser ${LAYOUT_PARSER:-true}"
echo "   Dossiers   : ${DRIVE_FOLDERS:-(aucun au départ)}"
echo "   Interface  : ${USERS:-(propriétaires du projet seulement)}"
echo "   Partager chaque dossier Drive (Lecteur) avec :"
echo "     $SA_EMAIL"
echo "     $RAG_AGENT"
if [ -z "$PROJECT_NUMBER" ]; then
  echo "   À CORRIGER : projet « $PROJECT_ID » introuvable ou pas de droit (gcloud auth login ?)"
else
  echo "   OK"
fi
