#!/usr/bin/env bash
# Poser une question à l'app Gemini Enterprise avec VOTRE identité (droits des sources appliqués : Drive fédéré,
# SharePoint… ne renvoient que ce que vous pouvez lire). Affiche la réponse et ses sources.
#
#   source scripts/config.sh config/<fichier>.env
#   bash scripts/question.sh "Quel est le numéro du contrat de mutuelle ?"
#
# Les sources Google Workspace refusent les comptes de service : connectez-vous avec votre compte
# (gcloud auth login vous@entreprise.com).
set -euo pipefail
: "${PROJECT_ID:?Configuration non chargée}"
: "${APP_ID:?APP_ID vide dans la configuration}"
Q="${1:?Usage : bash scripts/question.sh \"votre question\"}"
ENGINE="projects/$PROJECT_ID/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID"
BODY="$(python3 -c 'import json,sys; print(json.dumps({"query": {"text": sys.argv[1]},
  "answerGenerationSpec": {"includeCitations": True, "answerLanguageCode": "fr", "ignoreAdversarialQuery": True},
  "searchSpec": {"searchParams": {"maxReturnResults": 8}}}))' "$Q")"
curl -sS -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: $PROJECT_ID" -d "$BODY" \
  "https://$DE_HOST/v1/$ENGINE/servingConfigs/default_search:answer" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if "error" in d:
    sys.exit("Erreur : " + d["error"].get("message", "")[:400])
a = d.get("answer", {})
print("Réponse :", a.get("answerText") or "(aucune)")
if a.get("answerSkippedReasons"):
    print("Réponse non générée :", ", ".join(a["answerSkippedReasons"]))
refs = a.get("references", [])
print("Sources :")
for r in refs:
    doc = r.get("chunkInfo", {}).get("documentMetadata") or r.get("unstructuredDocumentInfo") or {}
    print("  -", doc.get("title") or doc.get("document", "?"), "|", doc.get("uri", ""))
'
