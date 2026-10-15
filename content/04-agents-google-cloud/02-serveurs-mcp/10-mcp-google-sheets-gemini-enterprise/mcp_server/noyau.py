"""Le noyau commun des serveurs MCP Google (Sheets, Slides) : vérification du jeton de l'utilisateur, appels Google
AVEC ce jeton, journal d'audit, annotations. Chaque produit (outils_sheets.py, outils_slides.py) crée son serveur avec
creer_mcp() et y ajoute ses outils.

Flux (Gemini Enterprise -> Cloud Run privé) :
  X-Serverless-Authorization : jeton du compte de l'app ou de l'agent (vérifié par Cloud Run IAM, run.invoker)
  Authorization: Bearer <jeton OAuth de l'utilisateur> (vérifié ici, puis utilisé pour appeler Google)
Chaque appel à Google se fait avec le jeton de l'utilisateur : il ne voit et ne modifie que ce que ses droits permettent.
"""
import json
import logging
import os
import sys
from typing import Annotated, Any

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth.providers.google import GoogleTokenVerifier
from fastmcp.server.dependencies import get_access_token
from pydantic import Field

DRIVE = "https://www.googleapis.com/drive/v3/files"
SCOPE_DRIVE_META = "https://www.googleapis.com/auth/drive.metadata.readonly"

# --- configuration (variables d'environnement posées par le script ou Terraform) ---------
# Clients OAuth dont on accepte les jetons (celui du connecteur et/ou de l'agent).
ALLOWED_AUDIENCES = [a.strip() for a in os.environ.get("OAUTH_CLIENT_IDS", "").split(",") if a.strip()]
# Domaines autorisés (ex. "acme.example"). Vide = tout compte Google (déconseillé).
ALLOWED_DOMAINS = {d.strip().lower() for d in os.environ.get("ALLOWED_DOMAINS", "").split(",") if d.strip()}

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("mcp-google")

RO = {"readOnlyHint": True, "openWorldHint": False}
WRITE = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False}


def audit(tool: str, **fields: Any) -> None:
    """Journal structuré (Cloud Logging) : qui, quel outil, quel fichier. Jamais le contenu."""
    token = get_access_token()
    log.info(json.dumps({"severity": "INFO", "event": "tool_call", "tool": tool,
                         "user": token.claims.get("email") if token else None, **fields}, ensure_ascii=False))


class CompanyGoogleTokenVerifier(GoogleTokenVerifier):
    """Vérifie le jeton Google (audience = nos clients OAuth, portée du produit ; cache intégré de 5 min), PUIS :
    e-mail vérifié et appartenant à un domaine autorisé."""

    async def verify_token(self, token: str):
        result = await super().verify_token(token)
        if result is None:
            return None
        email = (result.claims.get("email") or "").lower()
        if not result.claims.get("email_verified") or not email:
            log.warning(json.dumps({"severity": "WARNING", "event": "auth_rejected", "reason": "email_not_verified"}))
            return None
        if ALLOWED_DOMAINS and email.rsplit("@", 1)[-1] not in ALLOWED_DOMAINS:
            log.warning(json.dumps({"severity": "WARNING", "event": "auth_rejected", "reason": "domain", "user": email}))
            return None
        return result


def creer_mcp(nom: str, portee: str, instructions: str) -> FastMCP:
    """Le serveur MCP d'un produit : n'accepte que les jetons de nos clients OAuth, avec la portée du produit.
    Ajoute l'outil whoami, commun à tous."""
    if not ALLOWED_AUDIENCES:
        raise RuntimeError("OAUTH_CLIENT_IDS est vide : refuser de démarrer sans audience OAuth à vérifier.")
    mcp = FastMCP(nom, instructions=instructions, auth=CompanyGoogleTokenVerifier(
        required_scopes=[portee], audience=ALLOWED_AUDIENCES, cache_ttl_seconds=300))

    @mcp.tool(annotations={"title": "Qui suis-je ?", **RO})
    async def whoami() -> dict:
        """Retourne l'utilisateur Google connecté (pour vérifier la connexion OAuth)."""
        t = get_access_token()
        audit("whoami")
        return {"email": t.claims.get("email"), "name": t.claims.get("name"), "scopes": t.scopes}

    return mcp


# --- client Google (le jeton de l'utilisateur, à chaque appel) ---------------------------
_client = httpx.AsyncClient(timeout=30)


async def google(method: str, url: str, **kw) -> dict:
    token = get_access_token()
    if token is None:
        raise ToolError("Non authentifié.")
    r = await _client.request(method, url, headers={"Authorization": f"Bearer {token.token}"}, **kw)
    if r.status_code >= 400:
        try:
            msg = r.json().get("error", {}).get("message", r.text)
        except ValueError:
            msg = r.text
        hint = {401: "jeton expiré ou révoqué : reconnectez le connecteur dans Gemini Enterprise",
                403: "accès refusé : vous n'avez pas les droits sur ce fichier (ou portée manquante)",
                404: "fichier, élément ou plage introuvable",
                429: "quota Google atteint : réessayez dans une minute"}.get(r.status_code, "erreur Google")
        raise ToolError(f"{hint} ({r.status_code}) : {msg}")
    return r.json() if r.content else {}


async def chercher_fichiers(mime: str, query: str, max_results: int) -> list[dict]:
    """Fichiers Drive d'un type, accessibles à l'utilisateur, par nom (Mon Drive et Drive partagés)."""
    q = f"mimeType='{mime}' and trashed=false"
    if query.strip():
        q += " and name contains '" + query.replace("\\", "\\\\").replace("'", "\\'") + "'"
    data = await google("GET", DRIVE, params={
        "q": q, "pageSize": max_results, "orderBy": "modifiedTime desc",
        "fields": "files(id,name,modifiedTime,webViewLink,owners(displayName,emailAddress))",
        "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"})
    return data.get("files", [])


Requete = Annotated[str, Field(description="Mots du nom du fichier (vide = les plus récents).")]
NbMax = Annotated[int, Field(ge=1, le=50)]
