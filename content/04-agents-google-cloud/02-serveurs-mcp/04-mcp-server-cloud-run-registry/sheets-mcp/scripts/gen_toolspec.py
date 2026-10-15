"""Génère terraform/toolspec.json (liste des outils publiée dans Agent Registry) DEPUIS le serveur.
Ainsi le registre ne peut pas diverger du code.   Usage : python scripts/gen_toolspec.py
"""
import asyncio
import json
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
os.environ.setdefault("OAUTH_CLIENT_IDS", "generation-only")
sys.path.insert(0, str(root / "server"))
import main  # noqa: E402


async def build():
    tools = await main.mcp.list_tools()
    spec = {"tools": []}
    for t in sorted(tools, key=lambda t: t.name):
        a = t.annotations
        spec["tools"].append({
            "name": t.name,
            "description": (t.description or "").strip().splitlines()[0],
            "annotations": {k: v for k, v in {"title": a.title, "readOnlyHint": a.readOnlyHint, "destructiveHint": a.destructiveHint}.items() if v is not None},
        })
    out = root / "terraform" / "toolspec.json"
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n")
    print(f"{out} : {len(spec['tools'])} outils, {len(out.read_bytes())} octets (max 10 Ko)")


asyncio.run(build())
