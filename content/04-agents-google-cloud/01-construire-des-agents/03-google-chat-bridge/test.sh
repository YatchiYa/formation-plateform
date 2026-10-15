#!/usr/bin/env bash
# Sends a fake Google Chat "message" event to the bridge, exactly like Chat would.
# You can call it because, as project owner, you also have run.invoker.
set -euo pipefail
cd "$(dirname "$0")"
URL=${URL:-$(terraform -chdir=terraform output -raw url)}

curl -fsS -X POST "$URL/" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" -d @- <<'JSON' | python3 -m json.tool
{"chat": {"messagePayload": {"message": {
  "text": "How much is 100 USD in EUR?",
  "sender": {"name": "users/test-user", "displayName": "Test"}}}}}
JSON
