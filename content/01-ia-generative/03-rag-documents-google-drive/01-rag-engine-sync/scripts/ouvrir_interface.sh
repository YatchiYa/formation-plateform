#!/usr/bin/env bash
# Ouvrir l'interface (service privé) sur http://localhost:${PORT:-8080}, avec VOTRE identité Google.
#   source scripts/config.sh config/test.env && bash scripts/ouvrir_interface.sh
# Il faut le rôle run.invoker sur le service (variable USERS) ou être propriétaire du projet. Ctrl+C pour fermer.
set -euo pipefail
: "${PROJECT_ID:?Configuration non chargée : source scripts/config.sh config/<fichier>.env}"
echo "Interface : http://localhost:${PORT:-8080}   (Ctrl+C pour fermer)"
exec gcloud run services proxy "$SERVICE" --region="$REGION" --project="$PROJECT_ID" --port="${PORT:-8080}"
