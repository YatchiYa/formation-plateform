#!/usr/bin/env bash
# Déployer TOUT le kit avec gcloud (sans Terraform). Même résultat que terraform/ ; relançable sans risque :
# chaque étape vérifie ce qui existe déjà et ne fait que la différence.
#
#   source scripts/config.sh config/test.env && bash scripts/deployer_shell.sh
#
# Durée : ~5 min la 1re fois (dont ~2 min de construction d'image), ~3 min ensuite.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${PROJECT_ID:?Configuration non chargée : source scripts/config.sh config/<fichier>.env}"
P="$PROJECT_ID"; R="$REGION"
API="https://${R}-aiplatform.googleapis.com/v1/projects/${P}/locations/${R}"
etape() { printf '\n== %s\n' "$*"; }
tok() { gcloud auth print-access-token; }
rest() { curl -sS -H "Authorization: Bearer $(tok)" -H "Content-Type: application/json" -H "x-goog-user-project: $P" "$@"; }
jq_() { python3 -c "import json,sys; d=json.load(sys.stdin); $1"; }

etape "1/14 API"
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com aiplatform.googleapis.com \
  documentai.googleapis.com discoveryengine.googleapis.com drive.googleapis.com run.googleapis.com \
  cloudscheduler.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com storage.googleapis.com \
  iam.googleapis.com logging.googleapis.com monitoring.googleapis.com cloudtrace.googleapis.com \
  telemetry.googleapis.com secretmanager.googleapis.com picker.googleapis.com apikeys.googleapis.com --project="$P"

etape "2/14 Comptes de service"
for sa in "$PREFIX-sa:Kit RAG : interface, agent et synchro" "$PREFIX-scheduler-sa:Kit RAG : lance la synchro planifiée" \
          "$PREFIX-build-sa:Kit RAG : construit l'image (Cloud Build)"; do
  id="${sa%%:*}"
  gcloud iam service-accounts describe "$id@$P.iam.gserviceaccount.com" --project="$P" >/dev/null 2>&1 \
    || gcloud iam service-accounts create "$id" --display-name="${sa#*:}" --project="$P"
done

etape "3/14 Droits sur le projet"
for role in roles/aiplatform.user roles/discoveryengine.viewer roles/logging.logWriter roles/monitoring.metricWriter \
            roles/cloudtrace.agent roles/telemetry.writer; do
  gcloud projects add-iam-policy-binding "$P" --member="serviceAccount:$SA_EMAIL" --role="$role" --condition=None -q >/dev/null
done
for role in roles/storage.objectViewer roles/artifactregistry.writer roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "$P" --member="serviceAccount:$BUILD_SA" --role="$role" --condition=None -q >/dev/null
done
echo "   $SA_EMAIL et $BUILD_SA : rôles en place"

etape "4/14 Bucket gs://$BUCKET"
gcloud storage buckets describe "gs://$BUCKET" >/dev/null 2>&1 \
  || gcloud storage buckets create "gs://$BUCKET" --location="$R" --uniform-bucket-level-access --public-access-prevention --project="$P"
if ! gcloud storage objects describe "gs://$BUCKET/config.json" >/dev/null 2>&1; then
  python3 -c 'import json,sys; print(json.dumps({"drive_folders": [{"id": i, "name": i} for i in sys.argv[1].split()]}))' \
    "${DRIVE_FOLDERS:-}" | gcloud storage cp - "gs://$BUCKET/config.json" --content-type=application/json
fi
gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$SA_EMAIL" --role=roles/storage.objectAdmin -q >/dev/null

etape "5/14 Corpus RAG « $PREFIX »"
if [ -n "${RAG_TIER:-}" ]; then   # projet déprovisionné : RAG Engine ne se réactive pas seul (vérifié)
  OP="$(rest -X PATCH "$API/ragEngineConfig" -d "{\"ragManagedDbConfig\": {\"$RAG_TIER\": {}}}" | jq_ "print(d.get('name',''))")"
  until [ -z "$OP" ] || rest "https://${R}-aiplatform.googleapis.com/v1/$OP" | jq_ "sys.exit(0 if d.get('done') else 1)"; do sleep 5; done
  echo "   palier RagManagedDb : $RAG_TIER"
fi
CORPUS="$(rest "$API/ragCorpora?pageSize=100" | jq_ "print(next((c['name'] for c in d.get('ragCorpora',[]) if c['displayName']=='$PREFIX'), ''))")"
if [ -z "$CORPUS" ]; then
  OP="$(rest -X POST "$API/ragCorpora" -d "{\"displayName\":\"$PREFIX\",\"description\":\"Documents Drive + dépôts (kit $PREFIX)\",
    \"vectorDbConfig\":{\"ragManagedDb\":{\"knn\":{}},\"ragEmbeddingModelConfig\":{\"vertexPredictionEndpoint\":
    {\"endpoint\":\"projects/$P/locations/$R/publishers/google/models/text-multilingual-embedding-002\"}}}}" | jq_ "print(d['name'])")"
  until rest "https://${R}-aiplatform.googleapis.com/v1/$OP" | jq_ "sys.exit(0 if d.get('done') else 1)"; do sleep 5; done
  CORPUS="$(rest "$API/ragCorpora?pageSize=100" | jq_ "print(next(c['name'] for c in d['ragCorpora'] if c['displayName']=='$PREFIX'))")"
fi
echo "   $CORPUS"

etape "6/14 Agent de service RAG sur le bucket"
for role in roles/storage.objectViewer roles/storage.objectCreator; do   # sans objectCreator : 403 (vérifié)
  gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" --member="serviceAccount:$RAG_AGENT" --role="$role" -q >/dev/null
done
echo "   $RAG_AGENT : lecture + écriture des rapports"

etape "7/14 Layout parser (Document AI, eu)"
LAYOUT=""
if [ "${LAYOUT_PARSER:-true}" = "true" ]; then
  DAI="https://eu-documentai.googleapis.com/v1/projects/$P/locations/eu/processors"
  LAYOUT="$(rest "$DAI" | jq_ "print(next((p['name'] for p in d.get('processors',[]) if p['displayName']=='$PREFIX-layout'), ''))")"
  [ -n "$LAYOUT" ] || LAYOUT="$(rest -X POST "$DAI" -d "{\"type\":\"LAYOUT_PARSER_PROCESSOR\",\"displayName\":\"$PREFIX-layout\"}" | jq_ "print(d['name'])")"
fi
echo "   ${LAYOUT:-(désactivé)}"

etape "8/14 Image (Cloud Build)"
gcloud artifacts repositories describe "$PREFIX" --location="$R" --project="$P" >/dev/null 2>&1 \
  || gcloud artifacts repositories create "$PREFIX" --repository-format=docker --location="$R" --project="$P"
TAG="$(cd app && find . -type f \( -name '*.py' -o -name '*.html' -o -name '*.txt' -o -name '*.yaml' -o -name Dockerfile -o -name .gcloudignore \) \
        -not -path '*/__pycache__/*' | LC_ALL=C sort | xargs sha1sum | sha1sum | cut -c1-12)"
IMAGE="$REPO/app:$TAG"
if gcloud artifacts docker images describe "$IMAGE" >/dev/null 2>&1; then
  echo "   $IMAGE existe déjà (code inchangé)"
else
  for essai in 1 2 3 4; do   # droits d'un compte neuf : 1 à 2 min avant d'être actifs
    gcloud builds submit app --project="$P" --region="$R" --config=app/cloudbuild.yaml \
      --service-account="projects/$P/serviceAccounts/$BUILD_SA" --substitutions="_IMAGE=$IMAGE" --quiet && break
    [ "$essai" = 4 ] && exit 1; echo "   nouvel essai dans 40 s"; sleep 40
  done
fi

etape "9/14 Connexion Google : secrets et clé du sélecteur"
for s in oauth-client google-tokens; do
  gcloud secrets describe "$PREFIX-$s" --project="$P" >/dev/null 2>&1 \
    || gcloud secrets create "$PREFIX-$s" --replication-policy=user-managed --locations="$R" --project="$P" --quiet >/dev/null
  gcloud secrets add-iam-policy-binding "$PREFIX-$s" --member="serviceAccount:$SA_EMAIL" \
    --role=roles/secretmanager.secretAccessor --project="$P" -q >/dev/null
done
gcloud secrets add-iam-policy-binding "$PREFIX-google-tokens" --member="serviceAccount:$SA_EMAIL" \
  --role=roles/secretmanager.secretVersionManager --project="$P" -q >/dev/null
KEY="$(gcloud services api-keys list --project="$P" --filter="displayName='$PREFIX-picker'" --format='value(name)' | head -1)"
[ -n "$KEY" ] || KEY="$(gcloud services api-keys create --project="$P" --display-name="$PREFIX-picker" \
  --api-target=service=picker.googleapis.com \
  --allowed-referrers='http://localhost:8080/*,http://127.0.0.1:8080/*' --format='value(response.name)' 2>/dev/null \
  || gcloud services api-keys list --project="$P" --filter="displayName='$PREFIX-picker'" --format='value(name)' | head -1)"
PICKER_KEY="$(gcloud services api-keys get-key-string "$KEY" --project="$P" --format='value(keyString)')"
echo "   secrets $PREFIX-oauth-client, $PREFIX-google-tokens ; clé du sélecteur prête"

etape "10/14 Notifications push : service public « $PREFIX-hook »"
HOOK_URL=""
if [ "${PUSH:-true}" = "true" ]; then
  gcloud run deploy "$PREFIX-hook" --image="$IMAGE" --region="$R" --project="$P" --service-account="$SA_EMAIL" \
    --command=uvicorn --args=hook:app,--host,0.0.0.0,--port,8080 --allow-unauthenticated --max-instances=2 \
    --memory=512Mi --set-env-vars="PROJECT_ID=$P,REGION=$R,BUCKET=$BUCKET,SYNC_JOB=$SYNC_JOB,PREFIX=$PREFIX" --quiet
  HOOK_URL="$(gcloud run services describe "$PREFIX-hook" --region="$R" --project="$P" --format='value(status.url)')/hook/drive"
fi
echo "   ${HOOK_URL:-(désactivé : PUSH=false)}"

ENVF="$(mktemp)"; trap 'rm -f "$ENVF"' EXIT
cat > "$ENVF" <<EOF
PROJECT_ID: "$P"
PROJECT_NUMBER: "$PROJECT_NUMBER"
REGION: "$R"
BUCKET: "$BUCKET"
CORPUS: "$CORPUS"
LAYOUT_PARSER: "$LAYOUT"
SYNC_JOB: "$SYNC_JOB"
SA_EMAIL: "$SA_EMAIL"
MODEL: "$MODEL"
GOOGLE_GENAI_USE_VERTEXAI: "true"
GOOGLE_CLOUD_PROJECT: "$P"
GOOGLE_CLOUD_LOCATION: "$MODEL_LOCATION"
OTEL_TO_CLOUD: "true"
PREFIX: "$PREFIX"
HOOK_URL: "$HOOK_URL"
PICKER_API_KEY: "$PICKER_KEY"
EOF

etape "11/14 Job de synchro « $SYNC_JOB »"
gcloud run jobs deploy "$SYNC_JOB" --image="$IMAGE" --region="$R" --project="$P" --service-account="$SA_EMAIL" \
  --command=python --args=sync_job.py --env-vars-file="$ENVF" --tasks=1 --max-retries=0 --task-timeout=3600s \
  --cpu=1 --memory=1Gi --quiet
# « WithOverrides » : pour passer TRIGGER=auto (run.invoker ne suffit pas, vérifié).
for m in "serviceAccount:$SA_EMAIL:roles/run.jobsExecutorWithOverrides" "serviceAccount:$SA_EMAIL:roles/run.viewer" \
         "serviceAccount:$SCHEDULER_SA:roles/run.jobsExecutorWithOverrides"; do
  gcloud run jobs add-iam-policy-binding "$SYNC_JOB" --region="$R" --project="$P" --member="${m%:*}" --role="${m##*:}" -q >/dev/null
done

etape "12/14 Planification « $SYNC_SCHEDULE »"
URI="https://run.googleapis.com/v2/projects/$P/locations/$R/jobs/$SYNC_JOB:run"
ARGS=(--location="$R" --project="$P" --schedule="$SYNC_SCHEDULE" --time-zone=Europe/Paris --uri="$URI" --http-method=POST
      --oauth-service-account-email="$SCHEDULER_SA" --oauth-token-scope=https://www.googleapis.com/auth/cloud-platform
      --headers=Content-Type=application/json
      --message-body='{"overrides":{"containerOverrides":[{"env":[{"name":"TRIGGER","value":"auto"}]}]}}')
if [ -z "${SYNC_SCHEDULE:-}" ]; then   # planification désactivée (./ragkit desactiver planif)
  gcloud scheduler jobs delete "$SYNC_JOB" --location="$R" --project="$P" --quiet >/dev/null 2>&1 || true
  ARGS=()
elif gcloud scheduler jobs describe "$SYNC_JOB" --location="$R" --project="$P" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "$SYNC_JOB" "${ARGS[@]}" --quiet >/dev/null
else
  gcloud scheduler jobs create http "$SYNC_JOB" "${ARGS[@]}" --quiet >/dev/null
fi
echo "   OK"

etape "13/14 Service « $SERVICE » (privé)"
gcloud run deploy "$SERVICE" --image="$IMAGE" --region="$R" --project="$P" --service-account="$SA_EMAIL" \
  --env-vars-file="$ENVF" --no-allow-unauthenticated --min-instances=0 --max-instances=1 --cpu=1 --memory=1Gi \
  --timeout=300 --quiet

etape "14/14 Accès à l'interface"
for u in ${USERS:-}; do
  gcloud run services add-iam-policy-binding "$SERVICE" --region="$R" --project="$P" --member="$u" --role=roles/run.invoker -q >/dev/null
  echo "   $u"
done

cat <<EOF

== Terminé.
   Partagez chaque dossier Drive (Lecteur) avec :
     $SA_EMAIL
     $RAG_AGENT
   Ouvrir l'interface :
     gcloud run services proxy $SERVICE --region=$R --project=$P --port=8080   puis http://localhost:8080
EOF
