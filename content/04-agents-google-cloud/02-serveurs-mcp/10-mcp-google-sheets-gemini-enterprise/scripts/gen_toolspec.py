"""Génère terraform/toolspec-sheets.json et terraform/toolspec-slides.json : la liste des outils publiée dans Agent
Registry, DEPUIS le code des serveurs (elle ne peut donc pas diverger).   Usage : python scripts/gen_toolspec.py
Aucun appel réseau. Agent Registry exige le schéma des paramètres (inputSchema) et limite le fichier à 10 Ko.
"""
import asyncio
import importlib
import json
import os
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
os.environ.setdefault("OAUTH_CLIENT_IDS", "generation-seulement")
sys.path.insert(0, str(ICI / "mcp_server"))


def compact(schema):
    """Le schéma des paramètres, sans descriptions ni titres : types, valeurs permises, champs obligatoires."""
    if isinstance(schema, dict):
        return {k: compact(v) for k, v in schema.items()
                if k not in ("description", "title", "default", "examples", "additionalProperties")}
    if isinstance(schema, list):
        return [compact(x) for x in schema]
    return schema


async def main():
    for produit in ("sheets", "slides"):
        serveur = importlib.import_module(f"outils_{produit}").mcp
        outils = []
        for t in sorted(await serveur.list_tools(), key=lambda t: t.name):
            a = t.annotations
            outils.append({"name": t.name, "description": (t.description or "").strip().splitlines()[0],
                           "inputSchema": compact(t.parameters),   # obligatoire pour Agent Registry (refus sinon, vu en vrai)
                           "annotations": {k: v for k, v in {"title": a.title, "readOnlyHint": a.read_only_hint,
                                                             "destructiveHint": a.destructive_hint}.items() if v is not None}})
        out = ICI / "terraform" / f"toolspec-{produit}.json"
        out.write_text(json.dumps({"tools": outils}, ensure_ascii=False, separators=(",", ":")) + "\n")
        taille = len(out.read_bytes())
        print(f"{out.relative_to(ICI)} : {len(outils)} outils, {taille} octets (maximum Agent Registry : 10 Ko)")
        assert taille <= 10240, f"{out.name} dépasse 10 Ko : raccourcir les descriptions"


asyncio.run(main())
