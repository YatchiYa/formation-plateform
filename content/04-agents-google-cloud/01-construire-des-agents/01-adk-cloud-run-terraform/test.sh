#!/usr/bin/env bash
# Smoke test: list apps -> create a session -> ask a question -> check the tool was used.
# Usage: ./test.sh                     (uses the Cloud Run URL from terraform output)
#        URL=http://localhost:8080 ./test.sh   (local server)
set -euo pipefail
cd "$(dirname "$0")"

URL=${URL:-$(terraform -chdir=terraform output -raw url)}
TOKEN=$(gcloud auth print-identity-token)
H=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")
SID="smoke-$(date +%s)"

echo "== apps:"; curl -fsS "${H[@]}" "$URL/list-apps"; echo

curl -fsS "${H[@]}" -X POST "$URL/apps/weather_agent/users/u1/sessions/$SID" -d '{}' >/dev/null
echo "== session $SID created"

curl -fsS "${H[@]}" -X POST "$URL/run" -d @- <<JSON | python3 -c '
import json, sys
events = json.load(sys.stdin)
texts = [p["text"] for e in events for p in (e.get("content") or {}).get("parts", []) if p.get("text")]
calls = [p["functionCall"]["name"] for e in events for p in (e.get("content") or {}).get("parts", []) if p.get("functionCall")]
print("== tool calls:", calls)
print("== answer:", texts[-1])
assert "get_weather" in calls, "agent did not call get_weather"
print("OK")'
{"app_name": "weather_agent", "user_id": "u1", "session_id": "$SID",
 "new_message": {"role": "user", "parts": [{"text": "What is the weather in Paris?"}]}}
JSON
