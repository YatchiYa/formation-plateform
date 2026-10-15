#!/usr/bin/env bash
# main: changes only through a reviewed PR with green CI — except the repo owner (admin), who may push directly.
# Usage: scripts/protect-main.sh YatchiYa/formation-plateform   (needs `gh auth login` as the owner)
set -euo pipefail
REPO="${1:?usage: $0 owner/repo}"
gh api -X POST "repos/$REPO/rulesets" -H "Accept: application/vnd.github+json" --input - <<JSON
{
  "name": "protect-main",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["refs/heads/main"], "exclude": [] } },
  "bypass_actors": [ { "actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always" } ],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    { "type": "required_linear_history" },
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 1, "require_code_owner_review": true,
        "dismiss_stale_reviews_on_push": true, "require_last_push_approval": false,
        "required_review_thread_resolution": true } },
    { "type": "required_status_checks", "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [ { "context": "build-and-test" } ] } }
  ]
}
JSON
echo "✓ ruleset protect-main active on $REPO (repository admins can bypass)"
