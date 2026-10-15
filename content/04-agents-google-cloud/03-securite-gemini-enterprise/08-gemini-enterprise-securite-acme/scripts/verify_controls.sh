#!/usr/bin/env bash
# Contrôle de conformité : chaque mesure de la note est-elle RÉELLEMENT en place ?
# Lecture seule. À lancer après chaque apply, et chaque mois (preuve pour l'audit).
#   PROJECT_ID=mon-projet APP_ID=acme-ge ./verify_controls.sh
# Sortie : une ligne OK / KO / INFO par contrôle ; code retour 1 si au moins un KO.
set -uo pipefail
P=${PROJECT_ID:?PROJECT_ID}; APP=${APP_ID:?APP_ID}; LOC=${GE_LOCATION:-eu}
TOKEN=$(gcloud auth print-access-token)
DE="https://$LOC-discoveryengine.googleapis.com/v1/projects/$P/locations/$LOC"
KO=0

rest() { curl -fsS -H "Authorization: Bearer $TOKEN" -H "X-Goog-User-Project: $P" "$1" 2>/dev/null || echo '{}'; }
# check <mesure> <libellé> <json> <expression python sur d (dict)>
check() {
  if python3 -c "import json,sys; d=json.loads(sys.argv[1] or '{}'); sys.exit(0 if ($4) else 1)" "$3" 2>/dev/null; then
    printf "OK   %-5s %s\n" "$1" "$2"
  else
    printf "KO   %-5s %s\n" "$1" "$2"; KO=1
  fi
}

ASSIST=$(rest "$DE/collections/default_collection/engines/$APP/assistants/default_assistant")
ENGINE=$(rest "$DE/collections/default_collection/engines/$APP")
FLOOR=$(rest "https://modelarmor.googleapis.com/v1/projects/$P/locations/global/floorSetting")
IAM=$(gcloud projects get-iam-policy "$P" --format=json 2>/dev/null)
SINKS=$(gcloud logging sinks list --project="$P" --format=json 2>/dev/null)
APIS=$(gcloud services list --enabled --project="$P" --format="json(config.name)" 2>/dev/null)

check "§3" "Model Armor actif sur l'assistant, FAIL_CLOSED" "$ASSIST" \
  "d.get('customerPolicy',{}).get('modelArmorConfig',{}).get('failureMode')=='FAIL_CLOSED'"
check "§3" "Plancher Model Armor appliqué" "$FLOOR" "d.get('enableFloorSettingEnforcement') is True"
check "§1" "Plancher étendu aux appels Gemini du projet (agents)" "$FLOOR" "'AI_PLATFORM' in d.get('integratedServices',[])"
check "§4" "Journaux d'accès aux données : discoveryengine, aiplatform, modelarmor" "$IAM" \
  "{'discoveryengine.googleapis.com','aiplatform.googleapis.com','modelarmor.googleapis.com'} <= {c['service'] for c in d.get('auditConfigs',[])}"
check "§4" "Routage vers le bucket ge-security" "$SINKS" "any(s['name']=='ge-security-logs' for s in d)"
check "§4" "Export SIEM (Pub/Sub)" "$SINKS" "any(s['name']=='ge-security-to-siem' for s in d)"
check "§10" "Agent Registry activé" "$APIS" "any(a['config']['name']=='agentregistry.googleapis.com' for a in d)"
check "§2" "Cloud Asset Inventory activé" "$APIS" "any(a['config']['name']=='cloudasset.googleapis.com' for a in d)"
check "data" "Conservation des conversations bornée" "$ENGINE" "int(d.get('sessionConfig',{}).get('sessionTtl',{}).get('days',0))>0"
check "§8" "Aucun utilisateur individuel avec un rôle Gemini Enterprise (groupes seulement)" "$IAM" \
  "not any(m.startswith('user:') for b in d.get('bindings',[]) if 'discoveryengine' in b['role'] for m in b['members'])"

PUBLIC=$(gcloud asset search-all-iam-policies --scope="projects/$P" --query="policy:(allUsers OR allAuthenticatedUsers)" --format="value(resource)" 2>/dev/null | wc -l)
check "§2" "Aucune ressource ouverte à Internet ($PUBLIC trouvée(s))" "{\"n\": $PUBLIC}" "d['n']==0"

for c in run.allowedIngress iam.allowedPolicyMemberDomains gcp.resourceLocations; do
  POL=$(gcloud org-policies describe "$c" --project="$P" --effective --format=json 2>/dev/null || echo '{}')
  check "§2" "Politique d'organisation $c effective" "$POL" "bool(d.get('spec',{}).get('rules'))"
done

AA=$(gcloud access-approval settings get --project="$P" --format=json 2>/dev/null || echo '{}')
check "§4" "Access Approval (accès Google soumis à approbation)" "$AA" "bool(d.get('enrolledServices'))"

exit $KO
