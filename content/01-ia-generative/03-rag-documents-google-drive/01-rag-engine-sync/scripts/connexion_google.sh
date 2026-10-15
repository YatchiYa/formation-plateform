#!/usr/bin/env bash
# Ranger le client OAuth « Application Web » (fichier JSON téléchargé depuis la console) dans Secret Manager.
#   source scripts/config.sh config/test.env && bash scripts/connexion_google.sh ~/Téléchargements/client_secret_….json
# Étapes console : docs/04-bis-connexion-google.md. Relançable (nouvelle version du secret, l'ancienne est détruite).
set -euo pipefail
: "${PROJECT_ID:?Configuration non chargée : source scripts/config.sh config/<fichier>.env}"
F="${1:?Usage : bash scripts/connexion_google.sh <client_secret_….json>}"
python3 - "$F" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
c = d.get("web")
assert c, "Ce n'est pas un client « Application Web » (clé « web » absente) : recréez-le avec ce type."
uris = c.get("redirect_uris", [])
need = "http://localhost:8080/auth/google/callback"
assert need in uris, f"URI de redirection manquante dans le client : ajoutez {need} dans la console."
print(f"   client {c['client_id'][:24]}… : type Web, redirection {need} OK")
PY
OLD="$(gcloud secrets versions list "$PREFIX-oauth-client" --project="$PROJECT_ID" --filter=state:ENABLED --format='value(name)')"
gcloud secrets versions add "$PREFIX-oauth-client" --data-file="$F" --project="$PROJECT_ID" --quiet
for v in $OLD; do gcloud secrets versions destroy "$v" --secret="$PREFIX-oauth-client" --project="$PROJECT_ID" --quiet; done
echo "== Connexion Google configurée. Rechargez l'interface : le bouton « Se connecter avec Google » apparaît."
