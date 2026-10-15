#!/usr/bin/env bash
# Tester l'agent Dialogflow SEUL (sans Gemini Enterprise) : un message, la réponse de l'agent.
#   ./test.sh                     (agent lu dans terraform output)
#   AGENT=projects/P/locations/R/agents/ID ./test.sh "Bonjour"
set -euo pipefail
cd "$(dirname "$0")"
AGENT=${AGENT:-$(terraform -chdir=terraform output -raw dialogflow_agent)}
REGION=$(cut -d/ -f4 <<<"$AGENT"); PROJET=$(cut -d/ -f2 <<<"$AGENT"); TEXTE=${1:-Bonjour}
# Un agent tout juste créé répond 404 pendant quelques secondes (vérifié : 404 à +0 s, 200 à +5 s) : on réessaie.
for essai in 1 2 3 4 5 6; do
  REPONSE=$(curl -fsS -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
    -H "x-goog-user-project: $PROJET" "https://$REGION-dialogflow.googleapis.com/v3/$AGENT/sessions/test-$RANDOM:detectIntent" \
    -d "{\"queryInput\":{\"text\":{\"text\":\"$TEXTE\"},\"languageCode\":\"fr\"}}" 2>/dev/null) && break
  [ $essai = 6 ] && { echo "ÉCHEC : l'agent $AGENT ne répond pas (n'existe pas, ou pas de droit)."; exit 1; }
  echo "  agent pas encore prêt, nouvel essai dans 5 s…"; sleep 5
done
echo "$REPONSE" | python3 -c '
import json, sys
q = json.load(sys.stdin)["queryResult"]
print("intention :", q.get("intent", {}).get("displayName", "(aucune)"))
print("réponse   :", " ".join(t for m in q.get("responseMessages", []) for t in m.get("text", {}).get("text", [])))'
