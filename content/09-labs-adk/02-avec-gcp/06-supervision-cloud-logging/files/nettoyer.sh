#!/usr/bin/env bash
# Supprime le journal de test (toutes ses entrées) et vérifie.
set -uo pipefail
: "${PROJECT_ID:?définissez PROJECT_ID}"
gcloud logging logs delete lab-supervision --project "$PROJECT_ID" --quiet
# Doit afficher 0 (la suppression peut prendre quelques instants à se propager)
gcloud logging read 'logName:"logs/lab-supervision"' --project "$PROJECT_ID" --freshness 1d --format 'value(insertId)' | wc -l
