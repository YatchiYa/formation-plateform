#!/usr/bin/env bash
# Appelle le service privé avec un jeton d'identité.  Usage : PROJECT_ID=mon-projet ./call.sh
set -euo pipefail
PROJECT_ID="${PROJECT_ID:?définissez PROJECT_ID}"; REGION="${REGION:-europe-west1}"
URL=$(gcloud run services describe lab-api-ia --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')
TOKEN=$(gcloud auth print-identity-token)
TICKET='{"subject":"Prélevé deux fois","body":"Bonjour, ma carte a été débitée deux fois pour la commande de mars. Pouvez-vous rembourser le doublon ?"}'

echo "--- sans jeton (doit être refusé)"
curl -s -o /dev/null -w "%{http_code}\n" "$URL/health"
echo "--- avec jeton"
curl -s -H "Authorization: Bearer $TOKEN" "$URL/health"; echo
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST "$URL/v1/tickets/analyze" -d "$TICKET"; echo
echo "--- flux SSE"
curl -sN -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -X POST "$URL/v1/tickets/summarize-stream" -d "$TICKET"
