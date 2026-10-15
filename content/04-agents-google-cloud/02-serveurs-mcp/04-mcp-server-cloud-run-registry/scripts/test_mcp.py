"""Smoke test for the deployed MCP server.

- connects to <url>/mcp with your Google identity token
- checks the tools served == the tools declared in terraform/toolspec.json (registry stays in sync)
- calls each tool once

Usage: python scripts/test_mcp.py            (URL from terraform output)
       URL=http://localhost:8080 python scripts/test_mcp.py
"""
import asyncio
import json
import os
import subprocess
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

root = Path(__file__).resolve().parent.parent
url = os.getenv("URL") or subprocess.check_output(
    ["terraform", f"-chdir={root / 'terraform'}", "output", "-raw", "url"], text=True
).strip()
token = subprocess.check_output(["gcloud", "auth", "print-identity-token"], text=True).strip()
declared = {t["name"] for t in json.loads((root / "terraform" / "toolspec.json").read_text())["tools"]}


async def main():
    transport = StreamableHttpTransport(f"{url}/mcp", headers={"Authorization": f"Bearer {token}"})
    async with Client(transport) as client:
        served = {t.name for t in await client.list_tools()}
        print("tools served:", sorted(served))
        assert served == declared, f"toolspec.json out of sync: served={served} declared={declared}"

        found = (await client.call_tool("search_products", {"query": "laptop"})).structured_content
        print("search_products('laptop') ->", found)
        stock = (await client.call_tool("get_stock", {"sku": "SKU-001"})).data
        print("get_stock('SKU-001') ->", stock)
        assert stock["status"] == "success"
    print("OK")


asyncio.run(main())
