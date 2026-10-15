#!/usr/bin/env bash
# Arrête et SUPPRIME tout (conteneurs, volumes, secrets locaux).
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose down -v
rm -f .env
echo "Tout est supprimé."
