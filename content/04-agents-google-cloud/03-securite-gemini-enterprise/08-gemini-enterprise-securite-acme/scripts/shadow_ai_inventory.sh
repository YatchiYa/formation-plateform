#!/usr/bin/env bash
# Note §2 - Inventaire « Shadow AI » avec Cloud Asset Inventory (natif, sans agent).
#   ./shadow_ai_inventory.sh organizations/123456789   (rôle : roles/cloudasset.viewer sur l'org)
#   ./shadow_ai_inventory.sh projects/mon-projet
# Liste : 1) les ressources IA (agents, endpoints, apps GE, serveurs Cloud Run)
#         2) celles ouvertes à Internet (allUsers / allAuthenticatedUsers)
#         3) celles sans label owner (personne n'en répond)
# À comparer avec Agent Registry : tout ce qui n'y est pas = à régulariser ou supprimer.
set -euo pipefail
SCOPE=${1:?usage: $0 organizations/ID|projects/ID}
OUT=${OUT:-shadow-ai-$(date +%F)}
mkdir -p "$OUT"

TYPES="aiplatform.googleapis.com/ReasoningEngine,aiplatform.googleapis.com/Endpoint,discoveryengine.googleapis.com/Engine,run.googleapis.com/Service"

echo "1/3 Ressources IA et services Cloud Run…"
gcloud asset search-all-resources --scope="$SCOPE" --asset-types="$TYPES" \
  --format="csv(assetType.basename(),name,project,location,labels.owner,createTime)" > "$OUT/ressources.csv"

echo "2/3 Ressources ouvertes à Internet…"
gcloud asset search-all-iam-policies --scope="$SCOPE" \
  --query="policy:(allUsers OR allAuthenticatedUsers)" \
  --format="csv(resource,assetType,project,policy.bindings.role.list())" > "$OUT/publiques.csv"

echo "3/3 Ressources IA sans propriétaire…"
gcloud asset search-all-resources --scope="$SCOPE" --asset-types="$TYPES" \
  --query="NOT labels.owner:*" --format="csv(name,project,createTime)" > "$OUT/sans-owner.csv"

for f in ressources publiques sans-owner; do
  printf "%-12s %s lignes\n" "$f" "$(($(wc -l < "$OUT/$f.csv") - 1))"
done
echo "Rapports dans $OUT/ (à joindre à la revue mensuelle)."
