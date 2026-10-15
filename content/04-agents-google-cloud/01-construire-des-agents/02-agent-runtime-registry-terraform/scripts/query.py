"""Call the agent deployed on Agent Runtime, the same way any Python client would.

Usage: python scripts/query.py "How much is 250 USD in MAD?"
Reads the resource name from `terraform output` unless AGENT_NAME is set.
"""
import asyncio
import os
import subprocess
import sys

import agentplatform

name = os.getenv("AGENT_NAME") or subprocess.check_output(
    ["terraform", "-chdir=terraform", "output", "-raw", "agent_resource_name"], text=True
).strip()
_, project, _, location, *_ = name.split("/")
question = " ".join(sys.argv[1:]) or "How much is 100 USD in EUR?"


async def main():
    remote = agentplatform.Client(project=project, location=location).runtimes.get(name=name)
    session = await remote.async_create_session(user_id="demo-user")
    print(f"session: {session['id']}")
    async for event in remote.async_stream_query(user_id="demo-user", session_id=session["id"], message=question):
        for part in (event.get("content") or {}).get("parts", []):
            if "function_call" in part:
                print(f"  -> tool call: {part['function_call']['name']}({part['function_call'].get('args')})")
            if part.get("text"):
                print(f"agent: {part['text']}")


asyncio.run(main())
