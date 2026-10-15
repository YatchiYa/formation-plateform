"""Serveur MCP Google, pour Cloud Run : PRODUIT=sheets (défaut) ou PRODUIT=slides choisit les outils.

Une seule image, deux services (sheets-mcp, slides-mcp) : même sécurité (noyau.py), outils différents
(outils_sheets.py, outils_slides.py). Lancer en local : PRODUIT=slides OAUTH_CLIENT_IDS=… python mcp_server/main.py
"""
import importlib
import os

import uvicorn

PRODUIT = os.getenv("PRODUIT", "sheets")
outils = importlib.import_module(f"outils_{PRODUIT}")
mcp = outils.mcp

# Stateless : Cloud Run peut lancer plusieurs instances sans session MCP en mémoire.
app = mcp.http_app(path="/mcp", stateless_http=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
