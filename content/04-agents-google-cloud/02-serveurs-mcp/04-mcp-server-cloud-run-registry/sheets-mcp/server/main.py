"""Serveur MCP Google Sheets : interaction native avec Google Sheets, AU NOM de l'utilisateur.

Flux (Gemini Enterprise -> Cloud Run privé) :
  X-Serverless-Authorization : jeton du service agent Gemini Enterprise (vérifié par Cloud Run IAM)
  Authorization: Bearer <jeton OAuth de l'utilisateur> (vérifié ici, puis utilisé pour appeler Sheets)

Chaque appel à Google Sheets / Drive est fait avec le jeton de l'utilisateur :
il ne voit et ne modifie que ce que ses droits Google Drive lui permettent.
"""
import hashlib
import json
import logging
import os
import re
import sys
import time
from typing import Annotated, Any, Literal
from urllib.parse import quote

import httpx
import uvicorn
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.auth.providers.google import GoogleTokenVerifier
from fastmcp.server.dependencies import get_access_token
from pydantic import Field

SHEETS = "https://sheets.googleapis.com/v4/spreadsheets"
DRIVE = "https://www.googleapis.com/drive/v3/files"
SCOPE_SHEETS = "https://www.googleapis.com/auth/spreadsheets"
SCOPE_DRIVE_META = "https://www.googleapis.com/auth/drive.metadata.readonly"

# --- configuration (variables d'environnement posées par Terraform) -----------------
# Clients OAuth dont on accepte les jetons (celui créé pour Gemini Enterprise).
ALLOWED_AUDIENCES = [a.strip() for a in os.environ.get("OAUTH_CLIENT_IDS", "").split(",") if a.strip()]
# Domaines autorisés (ex. "acme.example"). Vide = tout compte Google (déconseillé).
ALLOWED_DOMAINS = {d.strip().lower() for d in os.environ.get("ALLOWED_DOMAINS", "").split(",") if d.strip()}
MAX_CELLS = int(os.environ.get("MAX_CELLS_PER_READ", "20000"))  # garde-fou : taille des réponses au modèle

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("sheets-mcp")


def audit(tool: str, **fields: Any) -> None:
    """Journal structuré (Cloud Logging) : qui, quel outil, quel fichier. Jamais le contenu des cellules."""
    token = get_access_token()
    log.info(json.dumps({"severity": "INFO", "event": "tool_call", "tool": tool,
                         "user": token.claims.get("email") if token else None, **fields}))


# --- authentification -----------------------------------------------------------------
class CompanyGoogleTokenVerifier(GoogleTokenVerifier):
    """Vérifie le jeton Google (audience = notre client OAuth, scope Sheets), PUIS :
    - e-mail vérifié et appartenant à un domaine autorisé ;
    - cache court pour ne pas appeler Google à chaque requête MCP."""

    _cache: dict[str, tuple[float, Any]] = {}

    async def verify_token(self, token: str):
        key = hashlib.sha256(token.encode()).hexdigest()
        hit = self._cache.get(key)
        if hit and hit[0] > time.time():
            return hit[1]
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
        ttl = min(300, (result.expires_at - time.time()) if result.expires_at else 300)
        if len(self._cache) > 5000:
            self._cache.clear()
        self._cache[key] = (time.time() + max(ttl, 0), result)
        return result


if not ALLOWED_AUDIENCES:
    raise RuntimeError("OAUTH_CLIENT_IDS est vide : refuser de démarrer sans audience OAuth à vérifier.")

mcp = FastMCP(
    "google-sheets",
    instructions=(
        "Lire et modifier Google Sheets au nom de l'utilisateur connecté. "
        "Utilise search_spreadsheets pour trouver un fichier, get_spreadsheet_info pour connaître ses onglets, "
        "puis read_range / write_range / append_rows. Les plages sont en notation A1 (ex. 'Ventes!A1:D20'). "
        "Avant toute modification, confirme le fichier et la plage ciblés."
    ),
    auth=CompanyGoogleTokenVerifier(required_scopes=[SCOPE_SHEETS], audience=ALLOWED_AUDIENCES),
)

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
        hint = {401: "jeton expiré ou révoqué : reconnectez Google Sheets dans Gemini Enterprise",
                403: "accès refusé : vous n'avez pas les droits sur ce fichier (ou scope manquant)",
                404: "fichier, onglet ou plage introuvable",
                429: "quota Google Sheets atteint : réessayez dans une minute"}.get(r.status_code, "erreur Google")
        raise ToolError(f"{hint} ({r.status_code}) : {msg}")
    return r.json() if r.content else {}


def _rng(a1: str) -> str:
    return quote(a1, safe="")


# --- notation A1 -> GridRange (pour les opérations de structure / mise en forme) ---------
_A1 = re.compile(r"^(?:(?P<sheet>'(?:[^']|'')+'|[^!]+)!)?(?P<c1>[A-Za-z]*)(?P<r1>\d*)(?::(?P<c2>[A-Za-z]*)(?P<r2>\d*))?$")


def _col(letters: str) -> int:
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def parse_a1(a1: str) -> tuple[str | None, dict]:
    """'Ventes!B2:D10' -> ('Ventes', {startRowIndex:1, endRowIndex:10, startColumnIndex:1, endColumnIndex:4})."""
    m = _A1.match(a1.strip())
    if not m:
        raise ToolError(f"Plage A1 invalide : {a1!r}")
    sheet = m["sheet"]
    if sheet and sheet.startswith("'"):
        sheet = sheet[1:-1].replace("''", "'")
    g: dict = {}
    c1, r1, c2, r2 = m["c1"], m["r1"], m["c2"], m["r2"]
    if m.group(0).find(":") == -1:  # cellule ou ligne/colonne unique
        c2, r2 = c1, r1
    if c1:
        g["startColumnIndex"] = _col(c1)
    if c2:
        g["endColumnIndex"] = _col(c2) + 1
    if r1:
        g["startRowIndex"] = int(r1) - 1
    if r2:
        g["endRowIndex"] = int(r2)
    return sheet, g


async def _sheet_id(spreadsheet_id: str, title: str | None) -> int:
    meta = await google("GET", f"{SHEETS}/{spreadsheet_id}", params={"fields": "sheets.properties(sheetId,title)"})
    sheets = [s["properties"] for s in meta.get("sheets", [])]
    if not sheets:
        raise ToolError("Classeur sans onglet.")
    if title is None:
        return sheets[0]["sheetId"]
    for p in sheets:
        if p["title"] == title:
            return p["sheetId"]
    raise ToolError(f"Onglet {title!r} introuvable. Onglets : {', '.join(p['title'] for p in sheets)}")


async def _grid(spreadsheet_id: str, a1: str) -> dict:
    sheet, g = parse_a1(a1)
    return {"sheetId": await _sheet_id(spreadsheet_id, sheet), **g}


def _cap(values: list) -> tuple[list, bool]:
    out, cells = [], 0
    for row in values:
        cells += len(row)
        if cells > MAX_CELLS:
            return out, True
        out.append(row)
    return out, False


async def _batch(spreadsheet_id: str, requests: list[dict]) -> dict:
    return await google("POST", f"{SHEETS}/{spreadsheet_id}:batchUpdate", json={"requests": requests})


ID = Annotated[str, Field(description="ID du classeur (dans l'URL : docs.google.com/spreadsheets/d/<ID>/edit).")]
A1 = Annotated[str, Field(description="Plage en notation A1, ex. 'Feuille1!A1:D20', 'Ventes!A:A', 'B2'.")]
RO = {"readOnlyHint": True, "openWorldHint": False}
WRITE = {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
DESTRUCTIVE = {"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False}

# ======================================================================== LECTURE
@mcp.tool(annotations={"title": "Qui suis-je ?", **RO})
async def whoami() -> dict:
    """Retourne l'utilisateur Google connecté (pour vérifier la connexion OAuth)."""
    t = get_access_token()
    audit("whoami")
    return {"email": t.claims.get("email"), "name": t.claims.get("name"), "scopes": t.scopes}


@mcp.tool(annotations={"title": "Rechercher des classeurs", **RO})
async def search_spreadsheets(
    query: Annotated[str, Field(description="Mots du nom du fichier (vide = les plus récents).")] = "",
    max_results: Annotated[int, Field(ge=1, le=50)] = 10,
) -> list[dict]:
    """Recherche des Google Sheets accessibles à l'utilisateur, par nom (Mon Drive et Drive partagés)."""
    audit("search_spreadsheets")
    q = "mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    if query.strip():
        q += " and name contains '" + query.replace("\\", "\\\\").replace("'", "\\'") + "'"
    data = await google("GET", DRIVE, params={
        "q": q, "pageSize": max_results, "orderBy": "modifiedTime desc",
        "fields": "files(id,name,modifiedTime,webViewLink,owners(displayName,emailAddress))",
        "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"})
    return data.get("files", [])


@mcp.tool(annotations={"title": "Infos d'un classeur", **RO})
async def get_spreadsheet_info(spreadsheet_id: ID) -> dict:
    """Titre, lien, et liste des onglets (nom, id, nombre de lignes et colonnes) d'un classeur."""
    audit("get_spreadsheet_info", spreadsheet_id=spreadsheet_id)
    d = await google("GET", f"{SHEETS}/{spreadsheet_id}", params={
        "fields": "spreadsheetId,spreadsheetUrl,properties(title,locale,timeZone),"
                  "sheets.properties(sheetId,title,index,gridProperties(rowCount,columnCount,frozenRowCount))"})
    return {"id": d["spreadsheetId"], "title": d["properties"]["title"], "url": d.get("spreadsheetUrl"),
            "locale": d["properties"].get("locale"), "sheets": [s["properties"] for s in d.get("sheets", [])]}


@mcp.tool(annotations={"title": "Lire une plage", **RO})
async def read_range(
    spreadsheet_id: ID, range_a1: A1,
    render: Annotated[Literal["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"],
                      Field(description="FORMATTED_VALUE = tel qu'affiché ; UNFORMATTED_VALUE = valeurs brutes ; FORMULA = formules.")] = "FORMATTED_VALUE",
) -> dict:
    """Lit les valeurs d'une plage (liste de lignes)."""
    audit("read_range", spreadsheet_id=spreadsheet_id, range=range_a1)
    d = await google("GET", f"{SHEETS}/{spreadsheet_id}/values/{_rng(range_a1)}", params={"valueRenderOption": render})
    values, truncated = _cap(d.get("values", []))
    return {"range": d.get("range"), "values": values, "truncated": truncated}


@mcp.tool(annotations={"title": "Lire plusieurs plages", **RO})
async def read_ranges(spreadsheet_id: ID, ranges: Annotated[list[str], Field(min_length=1, max_length=20)]) -> list[dict]:
    """Lit plusieurs plages en un seul appel."""
    audit("read_ranges", spreadsheet_id=spreadsheet_id, ranges=ranges)
    d = await google("GET", f"{SHEETS}/{spreadsheet_id}/values:batchGet", params=[("ranges", r) for r in ranges])
    out = []
    for vr in d.get("valueRanges", []):
        values, truncated = _cap(vr.get("values", []))
        out.append({"range": vr.get("range"), "values": values, "truncated": truncated})
    return out


@mcp.tool(annotations={"title": "Chercher une valeur", **RO})
async def find_in_sheet(
    spreadsheet_id: ID,
    text: Annotated[str, Field(description="Texte à chercher (insensible à la casse).")],
    sheet: Annotated[str | None, Field(description="Onglet (vide = premier onglet).")] = None,
    max_matches: Annotated[int, Field(ge=1, le=200)] = 50,
) -> list[dict]:
    """Retourne les cellules (adresse A1 + valeur) qui contiennent le texte."""
    audit("find_in_sheet", spreadsheet_id=spreadsheet_id, sheet=sheet)
    if sheet is None:
        info = await google("GET", f"{SHEETS}/{spreadsheet_id}", params={"fields": "sheets.properties.title"})
        sheet = info["sheets"][0]["properties"]["title"]
    d = await google("GET", f"{SHEETS}/{spreadsheet_id}/values/{_rng(sheet)}")
    needle, hits = text.lower(), []
    for i, row in enumerate(d.get("values", [])):
        for j, v in enumerate(row):
            if needle in str(v).lower():
                col, n = "", j + 1
                while n:
                    n, rem = divmod(n - 1, 26)
                    col = chr(65 + rem) + col
                hits.append({"cell": f"{sheet}!{col}{i + 1}", "value": v})
                if len(hits) >= max_matches:
                    return hits
    return hits


# ======================================================================== ÉCRITURE
Values = Annotated[list[list[Any]], Field(description="Lignes de valeurs, ex. [[\"Nom\", \"Prix\"], [\"Vélo\", 299]]. Les formules commencent par '='.")]
InputOption = Annotated[Literal["USER_ENTERED", "RAW"],
                        Field(description="USER_ENTERED = interprété comme une saisie (formules, dates) ; RAW = texte brut.")]


@mcp.tool(annotations={"title": "Écrire dans une plage (remplace)", **DESTRUCTIVE})
async def write_range(spreadsheet_id: ID, range_a1: A1, values: Values, input_option: InputOption = "USER_ENTERED") -> dict:
    """Écrit des valeurs à partir de la plage indiquée, en REMPLAÇANT le contenu existant."""
    audit("write_range", spreadsheet_id=spreadsheet_id, range=range_a1, rows=len(values))
    d = await google("PUT", f"{SHEETS}/{spreadsheet_id}/values/{_rng(range_a1)}",
                     params={"valueInputOption": input_option}, json={"values": values})
    return {k: d.get(k) for k in ("updatedRange", "updatedRows", "updatedColumns", "updatedCells")}


@mcp.tool(annotations={"title": "Ajouter des lignes", **WRITE})
async def append_rows(spreadsheet_id: ID, range_a1: Annotated[str, Field(description="Onglet ou tableau cible, ex. 'Ventes' ou 'Ventes!A:D'.")],
                      values: Values, input_option: InputOption = "USER_ENTERED") -> dict:
    """Ajoute des lignes à la fin du tableau (sans écraser l'existant)."""
    audit("append_rows", spreadsheet_id=spreadsheet_id, range=range_a1, rows=len(values))
    d = await google("POST", f"{SHEETS}/{spreadsheet_id}/values/{_rng(range_a1)}:append",
                     params={"valueInputOption": input_option, "insertDataOption": "INSERT_ROWS"}, json={"values": values})
    u = d.get("updates", {})
    return {"updatedRange": u.get("updatedRange"), "updatedRows": u.get("updatedRows")}


@mcp.tool(annotations={"title": "Effacer une plage", **DESTRUCTIVE})
async def clear_range(spreadsheet_id: ID, range_a1: A1) -> dict:
    """Efface les VALEURS d'une plage (la mise en forme est conservée)."""
    audit("clear_range", spreadsheet_id=spreadsheet_id, range=range_a1)
    d = await google("POST", f"{SHEETS}/{spreadsheet_id}/values/{_rng(range_a1)}:clear", json={})
    return {"clearedRange": d.get("clearedRange")}


@mcp.tool(annotations={"title": "Créer un classeur", **WRITE})
async def create_spreadsheet(title: str, sheet_names: Annotated[list[str] | None, Field(description="Onglets à créer.")] = None) -> dict:
    """Crée un nouveau Google Sheets dans le Drive de l'utilisateur."""
    audit("create_spreadsheet")
    body: dict = {"properties": {"title": title}}
    if sheet_names:
        body["sheets"] = [{"properties": {"title": n}} for n in sheet_names]
    d = await google("POST", SHEETS, json=body)
    return {"id": d["spreadsheetId"], "url": d.get("spreadsheetUrl"), "sheets": [s["properties"]["title"] for s in d.get("sheets", [])]}


@mcp.tool(annotations={"title": "Ajouter un onglet", **WRITE})
async def add_sheet(spreadsheet_id: ID, title: str) -> dict:
    """Ajoute un onglet au classeur."""
    audit("add_sheet", spreadsheet_id=spreadsheet_id)
    d = await _batch(spreadsheet_id, [{"addSheet": {"properties": {"title": title}}}])
    return d["replies"][0]["addSheet"]["properties"]


@mcp.tool(annotations={"title": "Renommer un onglet", **WRITE})
async def rename_sheet(spreadsheet_id: ID, current_title: str, new_title: str) -> dict:
    """Renomme un onglet."""
    audit("rename_sheet", spreadsheet_id=spreadsheet_id)
    sid = await _sheet_id(spreadsheet_id, current_title)
    await _batch(spreadsheet_id, [{"updateSheetProperties": {"properties": {"sheetId": sid, "title": new_title}, "fields": "title"}}])
    return {"sheetId": sid, "title": new_title}


@mcp.tool(annotations={"title": "Supprimer un onglet", **DESTRUCTIVE})
async def delete_sheet(spreadsheet_id: ID, title: str) -> dict:
    """Supprime un onglet ET tout son contenu."""
    audit("delete_sheet", spreadsheet_id=spreadsheet_id)
    sid = await _sheet_id(spreadsheet_id, title)
    await _batch(spreadsheet_id, [{"deleteSheet": {"sheetId": sid}}])
    return {"deleted": title}


Dim = Annotated[Literal["ROWS", "COLUMNS"], Field(description="ROWS ou COLUMNS.")]


@mcp.tool(annotations={"title": "Insérer des lignes ou colonnes", **WRITE})
async def insert_dimension(spreadsheet_id: ID, sheet: str, dimension: Dim,
                           start_index: Annotated[int, Field(ge=0, description="Position (0 = avant la 1re ligne/colonne).")],
                           count: Annotated[int, Field(ge=1, le=1000)] = 1) -> dict:
    """Insère des lignes ou colonnes vides."""
    audit("insert_dimension", spreadsheet_id=spreadsheet_id, dimension=dimension, count=count)
    sid = await _sheet_id(spreadsheet_id, sheet)
    await _batch(spreadsheet_id, [{"insertDimension": {"range": {"sheetId": sid, "dimension": dimension, "startIndex": start_index,
                                                                  "endIndex": start_index + count}, "inheritFromBefore": start_index > 0}}])
    return {"inserted": count, "dimension": dimension, "at": start_index}


@mcp.tool(annotations={"title": "Supprimer des lignes ou colonnes", **DESTRUCTIVE})
async def delete_dimension(spreadsheet_id: ID, sheet: str, dimension: Dim,
                           start_index: Annotated[int, Field(ge=0, description="Première ligne/colonne à supprimer (0 = la 1re).")],
                           count: Annotated[int, Field(ge=1, le=1000)] = 1) -> dict:
    """Supprime des lignes ou colonnes et leur contenu."""
    audit("delete_dimension", spreadsheet_id=spreadsheet_id, dimension=dimension, count=count)
    sid = await _sheet_id(spreadsheet_id, sheet)
    await _batch(spreadsheet_id, [{"deleteDimension": {"range": {"sheetId": sid, "dimension": dimension, "startIndex": start_index,
                                                                  "endIndex": start_index + count}}}])
    return {"deleted": count, "dimension": dimension, "from": start_index}


@mcp.tool(annotations={"title": "Mettre en forme une plage", **WRITE})
async def format_range(
    spreadsheet_id: ID, range_a1: A1,
    bold: bool | None = None, italic: bool | None = None,
    background_hex: Annotated[str | None, Field(description="Couleur de fond, ex. '#FFF2CC'.")] = None,
    text_hex: Annotated[str | None, Field(description="Couleur du texte, ex. '#1C2333'.")] = None,
    number_format: Annotated[str | None, Field(description="Motif, ex. '#,##0.00 €', '0%', 'dd/mm/yyyy'.")] = None,
    horizontal_align: Literal["LEFT", "CENTER", "RIGHT"] | None = None,
) -> dict:
    """Applique gras, italique, couleurs, format de nombre ou alignement à une plage."""
    audit("format_range", spreadsheet_id=spreadsheet_id, range=range_a1)

    def rgb(h: str) -> dict:
        h = h.lstrip("#")
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
            raise ToolError(f"Couleur invalide : {h!r} (attendu #RRGGBB)")
        return {"red": int(h[0:2], 16) / 255, "green": int(h[2:4], 16) / 255, "blue": int(h[4:6], 16) / 255}

    fmt: dict = {}
    fields: list[str] = []
    text: dict = {}
    if bold is not None:
        text["bold"] = bold; fields.append("userEnteredFormat.textFormat.bold")
    if italic is not None:
        text["italic"] = italic; fields.append("userEnteredFormat.textFormat.italic")
    if text_hex:
        text["foregroundColor"] = rgb(text_hex); fields.append("userEnteredFormat.textFormat.foregroundColor")
    if text:
        fmt["textFormat"] = text
    if background_hex:
        fmt["backgroundColor"] = rgb(background_hex); fields.append("userEnteredFormat.backgroundColor")
    if number_format:
        fmt["numberFormat"] = {"type": "NUMBER", "pattern": number_format}; fields.append("userEnteredFormat.numberFormat")
    if horizontal_align:
        fmt["horizontalAlignment"] = horizontal_align; fields.append("userEnteredFormat.horizontalAlignment")
    if not fields:
        raise ToolError("Aucune mise en forme demandée.")
    grid = await _grid(spreadsheet_id, range_a1)
    await _batch(spreadsheet_id, [{"repeatCell": {"range": grid, "cell": {"userEnteredFormat": fmt}, "fields": ",".join(fields)}}])
    return {"formatted": range_a1, "applied": fields}


@mcp.tool(annotations={"title": "Opérations avancées (batchUpdate)", **DESTRUCTIVE})
async def batch_update(
    spreadsheet_id: ID,
    requests: Annotated[list[dict], Field(min_length=1, max_length=50,
                                          description="Requêtes de l'API Sheets spreadsheets.batchUpdate (tri, filtres, fusion, mise en forme "
                                                      "conditionnelle, graphiques, validation, protection…). Voir developers.google.com/sheets/api/reference/rest/v4/spreadsheets/request.")],
) -> dict:
    """Accès complet à l'API Sheets : exécute des requêtes batchUpdate natives (atomique : tout ou rien)."""
    audit("batch_update", spreadsheet_id=spreadsheet_id, kinds=sorted({k for r in requests for k in r}))
    d = await _batch(spreadsheet_id, requests)
    return {"replies": d.get("replies", [])}


# Stateless : Cloud Run peut lancer plusieurs instances sans session MCP en mémoire.
app = mcp.http_app(path="/mcp", stateless_http=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
