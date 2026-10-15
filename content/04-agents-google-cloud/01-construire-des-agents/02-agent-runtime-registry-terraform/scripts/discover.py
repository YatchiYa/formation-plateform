"""Discover agents through Agent Registry, like an orchestrator agent would.

Usage: python scripts/discover.py [LOCATION]      (default: the Terraform region)
"""
import json
import os
import subprocess
import sys

from google.adk.integrations.agent_registry import AgentRegistry

project = os.getenv("GOOGLE_CLOUD_PROJECT") or subprocess.check_output(
    ["gcloud", "config", "get", "project"], text=True
).strip()
location = sys.argv[1] if len(sys.argv) > 1 else "europe-west1"

registry = AgentRegistry(project_id=project, location=location)
agents = registry.list_agents().get("agents", [])
print(f"{len(agents)} agent(s) in {project}/{location}")
for a in agents:
    print(json.dumps({k: a.get(k) for k in ("name", "displayName", "description", "framework", "protocols")}, indent=2))
