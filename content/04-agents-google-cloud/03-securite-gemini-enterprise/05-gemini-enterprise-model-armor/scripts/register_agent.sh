#!/usr/bin/env bash
# Register / unregister an Agent Runtime agent in a Gemini Enterprise app.
# Called by Terraform (terraform_data.register_agent) with these env vars:
#   PROJECT_ID HOST PARENT AGENT DISPLAY_NAME DESCRIPTION
# Usage: register_agent.sh create|delete
set -euo pipefail

H=(-H "Authorization: Bearer $(gcloud auth print-access-token)"
   -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJECT_ID")
BASE="https://$HOST/v1alpha"

# Find an existing registration with the same display name (makes the script idempotent).
EXISTING=$(curl -fsS "${H[@]}" "$BASE/$PARENT/agents" | python3 -c '
import json, os, sys
agents = json.load(sys.stdin).get("agents", [])
print(next((a["name"] for a in agents if a.get("displayName") == os.environ["DISPLAY_NAME"]), ""))')

case "${1:-}" in
  create)
    [ -n "$EXISTING" ] && curl -fsS -X DELETE "${H[@]}" "$BASE/$EXISTING" >/dev/null   # replace, never duplicate
    curl -fsS -X POST "${H[@]}" "$BASE/$PARENT/agents" -d @- <<JSON
{"displayName": "$DISPLAY_NAME", "description": "$DESCRIPTION",
 "adkAgentDefinition": {"provisionedReasoningEngine": {"reasoningEngine": "$AGENT"}}}
JSON
    echo; echo "registered $DISPLAY_NAME";;
  delete)
    [ -n "$EXISTING" ] && curl -fsS -X DELETE "${H[@]}" "$BASE/$EXISTING" >/dev/null
    echo "unregistered $DISPLAY_NAME";;
  *) echo "usage: $0 create|delete" >&2; exit 2;;
esac
