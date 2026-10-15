#!/usr/bin/env bash
# Build the image here, ship it to the server over SSH, switch, health-check, roll back on failure.
# Used by CI (.github/workflows/ci.yml) and by hand:  DEPLOY_HOST=100.110.83.13 scripts/deploy.sh
set -euo pipefail
HOST="${DEPLOY_HOST:?set DEPLOY_HOST}"
USER_="${DEPLOY_USER:-gpnops}"
DIR="${DEPLOY_DIR:-apps/formation}"
PORT="${DEPLOY_PORT:-3090}"
TAG="${IMAGE_TAG:-$(git rev-parse --short=12 HEAD)}"
SSH="ssh ${DEPLOY_SSH_OPTS:-} -o BatchMode=yes -o StrictHostKeyChecking=accept-new $USER_@$HOST"

echo "▶ build atelier-formation:$TAG"
[ "${SKIP_BUILD:-}" = 1 ] || docker build -t "atelier-formation:$TAG" .

echo "▶ ship image ($(docker image inspect atelier-formation:$TAG --format '{{.Size}}' | numfmt --to=iec))"
docker save "atelier-formation:$TAG" | gzip -1 | $SSH 'gunzip | docker load' >/dev/null

echo "▶ switch"
scp ${DEPLOY_SSH_OPTS:-} -o BatchMode=yes -q deploy/docker-compose.prod.yml "$USER_@$HOST:$DIR/docker-compose.yml"
$SSH bash -s <<REMOTE
set -euo pipefail
cd "$DIR"
prev=\$(cat .current-tag 2>/dev/null || true)
IMAGE_TAG=$TAG PORT=$PORT docker compose up -d --remove-orphans
for i in \$(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$PORT/api/health" >/dev/null; then ok=1; break; fi
  sleep 2
done
if [ "\${ok:-}" != 1 ]; then
  echo "✗ health check failed"
  if [ -n "\$prev" ]; then echo "↩ rolling back to \$prev"; IMAGE_TAG=\$prev PORT=$PORT docker compose up -d; fi
  exit 1
fi
echo "$TAG" > .current-tag
# Keep the current and the previous image only.
docker images atelier-formation --format '{{.Tag}}' | grep -vxE "$TAG|\${prev:-none}|latest" | xargs -r -I{} docker rmi -f atelier-formation:{} >/dev/null 2>&1 || true
echo "✓ live: $TAG"
REMOTE
