#!/usr/bin/env bash
# Installe le service Terraform local de A à Z (idempotent : peut être relancé).
#   Gitea  : utilisateurs, organisation acme, dépôt privé infra-demo, protection de main, webhook
#   MinIO  : bucket d'état "tfstate" versionné
#   Atlantis : démarré avec le jeton de son compte de service Gitea
set -euo pipefail
cd "$(dirname "$0")/.."

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
rand() { head -c 24 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 24; }

# --- 1. Secrets locaux (.env, jamais committé) ------------------------------------------
if [ ! -f .env ]; then
  say "Génération des secrets dans .env"
  cat > .env <<ENV
GITEA_PORT=3000
ATLANTIS_PORT=4141
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=tfstate-admin
MINIO_ROOT_PASSWORD=$(rand)
ADMIN_PASSWORD=$(rand)
ALICE_PASSWORD=$(rand)
BOB_PASSWORD=$(rand)
BOT_PASSWORD=$(rand)
ATLANTIS_WEBHOOK_SECRET=$(rand)
ATLANTIS_GITEA_TOKEN=
ENV
fi
set -a; source .env; set +a
API="http://localhost:${GITEA_PORT}/api/v1"

# --- 2. Gitea et MinIO ------------------------------------------------------------------
say "Démarrage de Gitea et MinIO"
docker compose up -d gitea minio
for svc in gitea minio; do
  until [ "$(docker inspect -f '{{.State.Health.Status}}' "tfsvc-$svc-1")" = healthy ]; do sleep 2; done
  echo "  $svc : prêt"
done

G() { docker compose exec -T -u git gitea gitea "$@"; }
mkuser() {  # mkuser <nom> <mot de passe> [--admin]
  G admin user create --username "$1" --password "$2" --email "$1@acme.local" --must-change-password=false ${3:-} >/dev/null 2>&1 \
    && echo "  utilisateur $1 créé" || echo "  utilisateur $1 : existe déjà"
}
token() {   # token <nom> : jeton d'API (stocké dans .env)
  G admin user generate-access-token --username "$1" --token-name "tok-$(date +%s%N)" --scopes all --raw | tail -1
}
setenv() { sed -i "s|^$1=.*|$1=$2|" .env || true; grep -q "^$1=" .env || echo "$1=$2" >> .env; }

say "Utilisateurs Gitea"
mkuser platform-admin "$ADMIN_PASSWORD" --admin
mkuser atlantis-bot "$BOT_PASSWORD"   # compte de service d'Atlantis
mkuser alice "$ALICE_PASSWORD"        # développeuse
mkuser bob "$BOB_PASSWORD"            # équipe sécurité (relecteur + propriétaire des politiques)

say "Jetons d'API"
setenv ADMIN_TOKEN "$(token platform-admin)"
setenv ATLANTIS_GITEA_TOKEN "$(token atlantis-bot)"
setenv ALICE_TOKEN "$(token alice)"
setenv BOB_TOKEN "$(token bob)"
set -a; source .env; set +a

api() {  # api <jeton> <méthode> <chemin> [json]
  curl -sS -o /tmp/tfsvc-api.json -w '%{http_code}' -X "$2" -H "Authorization: token $1" -H 'Content-Type: application/json' \
       "$API$3" ${4:+-d "$4"}
}

say "Organisation acme et dépôt privé infra-demo"
code=$(api "$ADMIN_TOKEN" POST /orgs '{"username":"acme","visibility":"private"}'); echo "  org acme : HTTP $code"
code=$(api "$ADMIN_TOKEN" POST /orgs/acme/repos '{"name":"infra-demo","private":true,"default_branch":"main"}'); echo "  dépôt : HTTP $code"
for u in alice bob atlantis-bot; do
  code=$(api "$ADMIN_TOKEN" PUT "/repos/acme/infra-demo/collaborators/$u" '{"permission":"write"}'); echo "  $u : collaborateur (HTTP $code)"
done

say "Contenu initial du dépôt (infra-repo/)"
if [ "$(api "$ADMIN_TOKEN" GET /repos/acme/infra-demo/branches/main)" != 200 ]; then
  tmp=$(mktemp -d); cp -r infra-repo/. "$tmp"; cd "$tmp"
  git init -q -b main && git add -A
  git -c user.name=platform-admin -c user.email=platform-admin@acme.local commit -qm "Initialisation : socle infra-demo"
  git push -q "http://platform-admin:${ADMIN_PASSWORD}@localhost:${GITEA_PORT}/acme/infra-demo.git" main
  cd - >/dev/null; rm -rf "$tmp"; echo "  poussé sur main"
else
  echo "  main existe déjà"
fi

say "Protection de la branche main : 1 approbation, pas de push direct"
code=$(api "$ADMIN_TOKEN" POST /repos/acme/infra-demo/branch_protections \
  '{"rule_name":"main","enable_push":false,"required_approvals":1,"block_on_rejected_reviews":true,"dismiss_stale_approvals":true}')
echo "  HTTP $code (409/422 = déjà en place)"

say "Webhook Gitea → Atlantis"
if ! api "$ADMIN_TOKEN" GET /repos/acme/infra-demo/hooks >/dev/null || ! grep -q atlantis:4141 /tmp/tfsvc-api.json; then
  code=$(api "$ADMIN_TOKEN" POST /repos/acme/infra-demo/hooks "$(cat <<JSON
{"type":"gitea","active":true,"branch_filter":"*",
 "config":{"url":"http://atlantis:4141/events","content_type":"json","secret":"${ATLANTIS_WEBHOOK_SECRET}"},
 "events":["push","pull_request","pull_request_sync","issue_comment","pull_request_comment",
           "pull_request_review_approved","pull_request_review_rejected"]}
JSON
)"); echo "  HTTP $code"
else
  echo "  existe déjà"
fi

say "Bucket d'état MinIO (versionné)"
docker compose exec -T minio sh -c "mc alias set local http://localhost:9000 '$MINIO_ROOT_USER' '$MINIO_ROOT_PASSWORD' >/dev/null \
  && mc mb --ignore-existing local/tfstate && mc version enable local/tfstate"

say "Démarrage d'Atlantis"
docker compose up -d atlantis
until curl -fsS "http://localhost:${ATLANTIS_PORT}/healthz" >/dev/null 2>&1; do sleep 2; done
echo "  Atlantis : prêt"

cat <<MSG

Service prêt :
  Gitea     http://localhost:${GITEA_PORT}      (alice / bob / platform-admin : mots de passe dans .env)
  Atlantis  http://localhost:${ATLANTIS_PORT}   (verrous, historique)
  MinIO     http://localhost:${MINIO_CONSOLE_PORT}      (${MINIO_ROOT_USER} / voir .env)
Suite : python3 scripts/scenario.py
MSG
