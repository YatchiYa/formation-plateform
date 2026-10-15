#!/usr/bin/env bash
# REST smoke test against Agent Runtime: create a session, stream a query, check the tool ran.
set -euo pipefail
cd "$(dirname "$0")/.."

NAME=${AGENT_NAME:-$(terraform -chdir=terraform output -raw agent_resource_name)}
LOCATION=$(cut -d/ -f4 <<<"$NAME")
BASE="https://${LOCATION}-aiplatform.googleapis.com/v1/${NAME}"
H=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json")

SID=$(curl -fsS "${H[@]}" "$BASE:query" \
  -d '{"class_method": "async_create_session", "input": {"user_id": "smoke"}}' |
  python3 -c 'import json,sys; print(json.load(sys.stdin)["output"]["id"])')
echo "== session $SID"

OUT=$(curl -fsS -N "${H[@]}" "$BASE:streamQuery?alt=sse" -d @- <<JSON
{"class_method": "async_stream_query",
 "input": {"user_id": "smoke", "session_id": "$SID", "message": "Convert 100 USD to EUR"}}
JSON
)
echo "$OUT" | tail -c 600; echo
grep -q convert_currency <<<"$OUT" && echo "OK: tool was called" || { echo "FAIL: tool not called"; exit 1; }
