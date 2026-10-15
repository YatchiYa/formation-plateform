"""Test de bout en bout du serveur MCP Google Sheets, sans compte Google.

Le serveur tourne en HTTP (comme sur Cloud Run). Un client MCP l'appelle avec
"Authorization: Bearer <jeton>", exactement comme Gemini Enterprise.
Les API Google (tokeninfo, userinfo, Sheets, Drive) sont remplacées par un faux
Google en mémoire, injecté via les transports Mock de httpx / httpx2.

Lancer :  python tests/test_server.py
"""
import asyncio
import json
import os
import socket
import sys
import threading
import time
from pathlib import Path

os.environ["OAUTH_CLIENT_IDS"] = "client-gemini-enterprise.apps.googleusercontent.com"
os.environ["ALLOWED_DOMAINS"] = "acme.example"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server"))

import httpx  # noqa: E402
import httpx2  # noqa: E402
import uvicorn  # noqa: E402
from fastmcp import Client  # noqa: E402
from fastmcp.client.transports import StreamableHttpTransport  # noqa: E402

import main  # noqa: E402

CLIENT = "client-gemini-enterprise.apps.googleusercontent.com"
SCOPES = f"{main.SCOPE_SHEETS} {main.SCOPE_DRIVE_META} openid https://www.googleapis.com/auth/userinfo.email"
TOKENS = {
    "tok-alice": {"aud": CLIENT, "sub": "1", "email": "alice@acme.example", "email_verified": "true", "scope": SCOPES, "expires_in": "3599"},
    "tok-other-app": {"aud": "another-app.apps.googleusercontent.com", "sub": "2", "email": "bob@acme.example", "email_verified": "true", "scope": SCOPES, "expires_in": "3599"},
    "tok-outsider": {"aud": CLIENT, "sub": "3", "email": "eve@gmail.com", "email_verified": "true", "scope": SCOPES, "expires_in": "3599"},
    "tok-no-scope": {"aud": CLIENT, "sub": "4", "email": "carl@acme.example", "email_verified": "true", "scope": "openid", "expires_in": "3599"},
}

# Faux classeur : SID -> onglets
BOOK = {"title": "Ventes 2026", "sheets": {"Ventes": [["Produit", "Prix"], ["Vélo", "299"], ["Tente", "149"]], "Stock": [["SKU", "Qté"]]}}
CALLS: list[tuple[str, str]] = []


def _resp(data, status=200):
    return {"status_code": status, "content": json.dumps(data).encode(), "headers": {"content-type": "application/json"}}


def google_handler(method: str, url, headers, body: bytes):
    path, params = url.path, dict(url.params)
    auth = headers.get("authorization", "")
    tok = auth.removeprefix("Bearer ")
    if url.host == "oauth2.googleapis.com" and path == "/tokeninfo":
        return _resp(TOKENS[tok]) if tok in TOKENS else _resp({"error": "invalid_token"}, 400)
    if path == "/oauth2/v2/userinfo":
        return _resp({"name": "Alice"})
    assert tok == "tok-alice", f"l'API Google doit recevoir le jeton de l'utilisateur, reçu {auth!r}"
    CALLS.append((method, path))
    if url.host == "www.googleapis.com" and path == "/drive/v3/files":
        assert "application/vnd.google-apps.spreadsheet" in params["q"]
        return _resp({"files": [{"id": "SID", "name": BOOK["title"]}]})
    base = "/v4/spreadsheets"
    if method == "POST" and path == base:
        b = json.loads(body)
        return _resp({"spreadsheetId": "NEW", "spreadsheetUrl": "https://docs.google.com/x", "properties": b["properties"],
                      "sheets": b.get("sheets", [{"properties": {"title": "Feuille 1"}}])})
    if not path.startswith(base + "/SID"):
        return _resp({"error": {"message": "Requested entity was not found."}}, 404)
    rest = path[len(base) + 4:]
    if rest == "" and method == "GET":
        return _resp({"spreadsheetId": "SID", "spreadsheetUrl": "https://docs.google.com/SID", "properties": {"title": BOOK["title"], "locale": "fr_FR"},
                      "sheets": [{"properties": {"sheetId": i, "title": t, "index": i, "gridProperties": {"rowCount": 1000, "columnCount": 26}}}
                                 for i, t in enumerate(BOOK["sheets"])]})
    if rest == ":batchUpdate":
        reqs = json.loads(body)["requests"]
        replies = []
        for r in reqs:
            if "addSheet" in r:
                t = r["addSheet"]["properties"]["title"]; BOOK["sheets"][t] = []
                replies.append({"addSheet": {"properties": {"sheetId": len(BOOK["sheets"]) - 1, "title": t}}})
            elif "deleteSheet" in r:
                t = list(BOOK["sheets"])[r["deleteSheet"]["sheetId"]]; del BOOK["sheets"][t]; replies.append({})
            else:
                replies.append({})
        return _resp({"replies": replies, "_requests": reqs})
    if rest.startswith("/values:batchGet"):
        rngs = [v for k, v in url.params.multi_items() if k == "ranges"]
        return _resp({"valueRanges": [{"range": r, "values": BOOK["sheets"][r.split("!")[0]]} for r in rngs]})
    if rest.startswith("/values/"):
        rng = rest[len("/values/"):]
        sheet = rng.split("!")[0].split(":")[0]
        if rng.endswith(":append"):
            sheet = rng[:-7].split("!")[0]
            rows = json.loads(body)["values"]; BOOK["sheets"][sheet] += rows
            return _resp({"updates": {"updatedRange": f"{sheet}!A{len(BOOK['sheets'][sheet])}", "updatedRows": len(rows)}})
        if rng.endswith(":clear"):
            return _resp({"clearedRange": rng[:-6]})
        if method == "PUT":
            rows = json.loads(body)["values"]
            return _resp({"updatedRange": rng, "updatedRows": len(rows), "updatedColumns": len(rows[0]), "updatedCells": sum(map(len, rows))})
        if sheet not in BOOK["sheets"]:
            return _resp({"error": {"message": "Unable to parse range"}}, 400)
        return _resp({"range": rng, "values": BOOK["sheets"][sheet]})
    return _resp({"error": {"message": f"route non simulée {method} {path}"}}, 500)


def _httpx_handler(request: httpx.Request):
    r = google_handler(request.method, request.url, request.headers, request.content)
    return httpx.Response(**r)


def _httpx2_handler(request):
    r = google_handler(request.method, request.url, request.headers, request.content)
    return httpx2.Response(**r)


# Injection du faux Google dans les deux clients HTTP du serveur.
main._client = httpx.AsyncClient(transport=httpx.MockTransport(_httpx_handler))
main.mcp.auth._http_client = httpx2.AsyncClient(transport=httpx2.MockTransport(_httpx2_handler))


def free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


async def call(port: int, token: str, tool: str, args: dict | None = None):
    transport = StreamableHttpTransport(f"http://127.0.0.1:{port}/mcp", headers={"Authorization": f"Bearer {token}"})
    async with Client(transport) as c:
        return await c.call_tool(tool, args or {})


async def list_tools(port: int, token: str):
    transport = StreamableHttpTransport(f"http://127.0.0.1:{port}/mcp", headers={"Authorization": f"Bearer {token}"})
    async with Client(transport) as c:
        return await c.list_tools()


async def expect_rejected(port: int, token: str, label: str):
    try:
        await list_tools(port, token)
    except Exception:
        print(f"  ok  rejeté : {label}")
        return
    raise AssertionError(f"aurait dû être rejeté : {label}")


async def run(port: int):
    # 1. Authentification
    print("Authentification")
    await expect_rejected(port, "tok-unknown", "jeton invalide")
    await expect_rejected(port, "tok-other-app", "jeton émis pour une autre application (audience)")
    await expect_rejected(port, "tok-outsider", "compte hors domaine acme.example")
    await expect_rejected(port, "tok-no-scope", "scope Sheets absent")
    me = (await call(port, "tok-alice", "whoami")).data
    assert me["email"] == "alice@acme.example", me
    print("  ok  accepté : alice@acme.example")

    # 2. Catalogue d'outils et annotations (confirmation dans Gemini Enterprise)
    tools = {t.name: t for t in await list_tools(port, "tok-alice")}
    print(f"Outils ({len(tools)}) : {', '.join(sorted(tools))}")
    for n in ["whoami", "search_spreadsheets", "get_spreadsheet_info", "read_range", "read_ranges", "find_in_sheet"]:
        assert tools[n].annotations.readOnlyHint is True, n
    for n in ["write_range", "clear_range", "delete_sheet", "delete_dimension", "batch_update"]:
        assert tools[n].annotations.destructiveHint is True, n

    # 3. Lecture
    print("Lecture")
    assert (await call(port, "tok-alice", "search_spreadsheets", {"query": "Ventes"})).data[0]["id"] == "SID"
    info = (await call(port, "tok-alice", "get_spreadsheet_info", {"spreadsheet_id": "SID"})).data
    assert [s["title"] for s in info["sheets"]] == ["Ventes", "Stock"], info
    r = (await call(port, "tok-alice", "read_range", {"spreadsheet_id": "SID", "range_a1": "Ventes!A1:B3"})).data
    assert r["values"][1] == ["Vélo", "299"], r
    rr = (await call(port, "tok-alice", "read_ranges", {"spreadsheet_id": "SID", "ranges": ["Ventes!A:A", "Stock!A1"]})).data
    assert len(rr) == 2
    hits = (await call(port, "tok-alice", "find_in_sheet", {"spreadsheet_id": "SID", "text": "tente"})).data
    assert hits == [{"cell": "Ventes!A3", "value": "Tente"}], hits
    print("  ok  search, info, read_range, read_ranges, find_in_sheet")

    # 4. Écriture et structure
    print("Écriture et structure")
    w = (await call(port, "tok-alice", "write_range", {"spreadsheet_id": "SID", "range_a1": "Ventes!C1:C2", "values": [["Marge"], ["=B2*0.3"]]})).data
    assert w["updatedCells"] == 2
    a = (await call(port, "tok-alice", "append_rows", {"spreadsheet_id": "SID", "range_a1": "Ventes", "values": [["Sac", "39"]]})).data
    assert a["updatedRows"] == 1 and BOOK["sheets"]["Ventes"][-1] == ["Sac", "39"]
    assert (await call(port, "tok-alice", "clear_range", {"spreadsheet_id": "SID", "range_a1": "Stock!A2:B10"})).data["clearedRange"]
    assert (await call(port, "tok-alice", "create_spreadsheet", {"title": "Inventaire", "sheet_names": ["Lille"]})).data["id"] == "NEW"
    assert (await call(port, "tok-alice", "add_sheet", {"spreadsheet_id": "SID", "title": "Archive"})).data["title"] == "Archive"
    await call(port, "tok-alice", "rename_sheet", {"spreadsheet_id": "SID", "current_title": "Stock", "new_title": "Stock"})
    await call(port, "tok-alice", "insert_dimension", {"spreadsheet_id": "SID", "sheet": "Ventes", "dimension": "ROWS", "start_index": 1, "count": 2})
    await call(port, "tok-alice", "delete_dimension", {"spreadsheet_id": "SID", "sheet": "Ventes", "dimension": "COLUMNS", "start_index": 2})
    f = (await call(port, "tok-alice", "format_range", {"spreadsheet_id": "SID", "range_a1": "Ventes!A1:B1", "bold": True, "background_hex": "#FFF2CC"})).data
    assert "userEnteredFormat.textFormat.bold" in f["applied"]
    assert (await call(port, "tok-alice", "delete_sheet", {"spreadsheet_id": "SID", "title": "Archive"})).data["deleted"] == "Archive"
    bu = (await call(port, "tok-alice", "batch_update", {"spreadsheet_id": "SID", "requests": [{"sortRange": {"range": {"sheetId": 0}, "sortSpecs": [{"dimensionIndex": 1}]}}]})).data
    assert "replies" in bu
    print("  ok  write, append, clear, create, add/rename/delete sheet, insert/delete rows-cols, format, batch_update")

    # 5. Erreurs claires
    try:
        await call(port, "tok-alice", "read_range", {"spreadsheet_id": "INCONNU", "range_a1": "A1"})
        raise AssertionError("404 attendu")
    except Exception as e:
        assert "introuvable" in str(e), e
    print("  ok  erreur Google traduite en message clair (404)")


def unit_a1():
    assert main.parse_a1("Ventes!B2:D10") == ("Ventes", {"startColumnIndex": 1, "endColumnIndex": 4, "startRowIndex": 1, "endRowIndex": 10})
    assert main.parse_a1("'Mon onglet'!A:A") == ("Mon onglet", {"startColumnIndex": 0, "endColumnIndex": 1})
    assert main.parse_a1("C5") == (None, {"startColumnIndex": 2, "endColumnIndex": 3, "startRowIndex": 4, "endRowIndex": 5})
    assert main.parse_a1("Feuil1!2:4") == ("Feuil1", {"startRowIndex": 1, "endRowIndex": 4})
    assert main.parse_a1("AA1:AB2")[1]["startColumnIndex"] == 26
    print("  ok  notation A1")


if __name__ == "__main__":
    print("Notation A1")
    unit_a1()
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    asyncio.run(run(port))
    server.should_exit = True
    print(f"\nOK : tous les tests passent ({len(CALLS)} appels Google simulés, tous avec le jeton de l'utilisateur).")
