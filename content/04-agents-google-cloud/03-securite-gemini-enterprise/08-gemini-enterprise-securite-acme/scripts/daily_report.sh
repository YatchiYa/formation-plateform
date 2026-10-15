#!/usr/bin/env bash
# Journal quotidien de sécurité Gemini Enterprise (à lancer chaque matin ou via Cloud Scheduler).
# Lit les buckets ge-security / ge-usage créés par Terraform. Sortie : Markdown.
#   ./daily_report.sh > rapport-$(date +%F).md
# Rôles requis : roles/logging.viewAccessor sur les vues des buckets (groupe sécurité).
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT=${PROJECT_ID:-$(terraform -chdir=terraform output -raw project_id 2>/dev/null || gcloud config get project)}
LOC=${GE_LOCATION:-eu}
SINCE=${SINCE:-24h}
SEC=ge-security   # buckets créés par terraform/80_logging.tf
USE=ge-usage

count() {  # count <bucket> <filtre>
  gcloud logging read "$2" --project="$PROJECT" --bucket="$1" --view=_AllLogs \
    --location="$LOC" --freshness="$SINCE" --limit=10000 --format="value(insertId)" 2>/dev/null | wc -l
}

top() {  # top <bucket> <filtre> <champ>  -> 5 valeurs les plus fréquentes
  gcloud logging read "$2" --project="$PROJECT" --bucket="$1" --view=_AllLogs \
    --location="$LOC" --freshness="$SINCE" --limit=10000 --format="value($3)" 2>/dev/null |
    sort | uniq -c | sort -rn | head -5 | sed 's/^/    /'
}

cat <<MD
# Journal sécurité Gemini Enterprise — $(date +%F) (dernières $SINCE, projet $PROJECT)

| Indicateur | Valeur | Seuil d'action |
|---|---|---|
| Modifications de garde-fous (audit admin) | $(count "$SEC" 'logName:"cloudaudit.googleapis.com%2Factivity" protoPayload.methodName=~"(Template|FloorSetting|CryptoKey|SetIamPolicy|Assistant|AclConfig)"') | > 0 sans PR = incident |
| Blocages Model Armor (contenu journalisé) | $(count "$SEC" 'jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"') | pic x3 vs moyenne |
| Réponses bloquées par la politique (usage) | $(count "$USE" '"CUSTOMER_POLICY_VIOLATION"') | pic x3 vs moyenne |
| Signaux Shadow AI (agent créé, service public) | $(count "$SEC" 'logName:"cloudaudit.googleapis.com%2Factivity" (protoPayload.serviceName="aiplatform.googleapis.com" AND protoPayload.methodName=~"CreateReasoningEngine") OR (protoPayload.serviceName="agentregistry.googleapis.com" AND protoPayload.methodName=~"Create")') | > 0 sans PR = enquête |
| Accès refusés (PERMISSION_DENIED) | $(count "$SEC" 'protoPayload.status.code=7') | pic = tentative d'accès |
| Violations VPC-SC (dry-run ou réel) | $(count "$SEC" 'protoPayload.metadata.@type="type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata"') | avant enforcement : à analyser |
| Requêtes utilisateurs (usage) | $(count "$USE" 'logName:"gemini_enterprise_user_activity"') | tendance d'adoption |

## Qui a modifié la configuration
$(top "$SEC" 'logName:"cloudaudit.googleapis.com%2Factivity" protoPayload.serviceName=("modelarmor.googleapis.com" OR "discoveryengine.googleapis.com" OR "cloudkms.googleapis.com")' 'protoPayload.authenticationInfo.principalEmail')

## Filtres Model Armor les plus déclenchés
$(top "$SEC" 'jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"' 'jsonPayload.sanitizationResult.filterResults.list()')

## Méthodes refusées (PERMISSION_DENIED)
$(top "$SEC" 'protoPayload.status.code=7' 'protoPayload.methodName')
MD
