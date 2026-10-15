#!/usr/bin/env bash
# Rattacher des data stores à une app Gemini Enterprise EXISTANTE (créée hors de ce kit, ex. l'app Acme).
# Ajoute aux data stores déjà rattachés (n'en retire jamais). Relançable sans risque.
#
#   source scripts/config.sh config/<fichier>.env
#   bash scripts/rattacher.sh                      # les data stores créés par Terraform (sortie « data_stores »)
#   bash scripts/rattacher.sh mon-drive-ds autre   # + des data stores créés dans la console (Drive, OneDrive…)
set -euo pipefail
cd "$(dirname "$0")/.."
: "${PROJECT_ID:?Configuration non chargée : source scripts/config.sh config/<fichier>.env}"
: "${APP_ID:?APP_ID vide dans la configuration : l'ID de l'app (console Gemini Enterprise → Apps)}"
ENGINE="projects/$PROJECT_ID/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID"
api() { curl -sS -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
             -H "X-Goog-User-Project: $PROJECT_ID" "$@"; }

TF="$(terraform -chdir=terraform output -json data_stores 2>/dev/null || echo '[]')"
python3 - "$ENGINE" "$TF" "$@" <<'PY' > /tmp/rattacher.$$.json
import json, subprocess, sys
engine, tf, extra = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3:]
host = subprocess.run(["bash", "-c", 'echo "$DE_HOST"'], capture_output=True, text=True).stdout.strip()
token = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True).stdout.strip()
import urllib.request, os
req = urllib.request.Request(f"https://{host}/v1/{engine}", headers={"Authorization": f"Bearer {token}",
                             "X-Goog-User-Project": os.environ["PROJECT_ID"]})
try:
    current = json.load(urllib.request.urlopen(req)).get("dataStoreIds", [])
except urllib.error.HTTPError as e:
    sys.exit(f"App introuvable ou pas de droit : {engine} ({e.code}). Vérifiez APP_ID et GE_LOCATION.")
wanted = current + [d for d in tf + extra if d not in current]
print(json.dumps({"current": current, "wanted": wanted}))
PY
CUR="$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["current"]))' /tmp/rattacher.$$.json)"
NEW="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(" ".join(x for x in d["wanted"] if x not in d["current"]))' /tmp/rattacher.$$.json)"
echo "== App $APP_ID : déjà rattachés : ${CUR:-(aucun)}"
if [ -z "$NEW" ]; then echo "   Rien à ajouter."; rm -f /tmp/rattacher.$$.json; exit 0; fi
echo "   À rattacher : $NEW"
BODY="$(python3 -c 'import json,sys; print(json.dumps({"dataStoreIds": json.load(open(sys.argv[1]))["wanted"]}))' /tmp/rattacher.$$.json)"
rm -f /tmp/rattacher.$$.json
R="$(api -X PATCH "https://$DE_HOST/v1/$ENGINE?updateMask=dataStoreIds" -d "$BODY")"
if echo "$R" | grep -q '"error"'; then echo "$R" | head -c 600; echo; exit 1; fi
echo "$R" | python3 -c 'import json,sys; print("== Rattachés :", ", ".join(json.load(sys.stdin)["dataStoreIds"]))'
