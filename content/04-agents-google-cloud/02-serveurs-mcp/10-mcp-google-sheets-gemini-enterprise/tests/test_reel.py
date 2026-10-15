"""Test RÉEL du serveur MCP Google Sheets : vrais appels à Google, sur un vrai classeur.

Il appelle le serveur EXACTEMENT comme Gemini Enterprise (connecteur « Custom MCP Server ») :
  Authorization: Bearer <jeton OAuth de l'utilisateur>        (toujours)
  X-Serverless-Authorization: Bearer <jeton d'identité>        (seulement vers Cloud Run, si ID_TOKEN est donné)

Il travaille dans un onglet temporaire « test-mcp-<heure> », qu'il supprime à la fin : le classeur est rendu intact.

Variables :
  MCP_URL          http://localhost:8080/mcp (local) ou https://sheets-mcp-<NUM>.<REGION>.run.app/mcp
  USER_TOKEN       jeton OAuth de l'utilisateur, avec les portées spreadsheets + userinfo.email (+ drive.metadata.readonly)
  ID_TOKEN         (Cloud Run) jeton d'identité d'un compte qui a roles/run.invoker sur le service
  SPREADSHEET_ID   un classeur que l'utilisateur peut modifier

  python tests/test_reel.py
"""
import asyncio
import os
import time

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

URL, SID = os.environ["MCP_URL"], os.environ["SPREADSHEET_ID"]
H = {"Authorization": f"Bearer {os.environ['USER_TOKEN']}"}
if os.getenv("ID_TOKEN"):
    H["X-Serverless-Authorization"] = f"Bearer {os.environ['ID_TOKEN']}"
ONGLET = time.strftime("test-mcp-%H%M%S")


async def main():
    async with Client(StreamableHttpTransport(URL, headers=H)) as c:
        async def t(nom, **args):
            r = await c.call_tool(nom, args)
            return r.data if r.data is not None else r.structured_content

        outils = await c.list_tools()
        print(f"tools/list : {len(outils)} outils")
        assert len(outils) == 17, [o.name for o in outils]

        me = await t("whoami")
        print(f"whoami                : {me['email']}")
        trouves = await t("search_spreadsheets", query="MCP Sheets")
        assert any(f["id"] == SID for f in trouves), trouves
        print(f"search_spreadsheets   : {len(trouves)} classeur(s), dont le classeur de test")
        info = await t("get_spreadsheet_info", spreadsheet_id=SID)
        premier = info["sheets"][0]["title"]
        print(f"get_spreadsheet_info  : « {info['title']} », locale {info['locale']}, onglets {[s['title'] for s in info['sheets']]}")
        lu = await t("read_range", spreadsheet_id=SID, range_a1=f"'{premier}'!A1:C4")
        print(f"read_range            : {lu['values']}")
        assert lu["values"][0][:2] == ["Produit", "Prix"], lu
        assert len(await t("read_ranges", spreadsheet_id=SID, ranges=[f"'{premier}'!A:A", f"'{premier}'!B1"])) == 2
        print("read_ranges           : 2 plages")
        hits = await t("find_in_sheet", spreadsheet_id=SID, text="tente", sheet=premier)
        print(f"find_in_sheet         : {hits}")
        assert hits and hits[0]["value"] == "Tente", hits

        # Écriture : dans un onglet temporaire, supprimé à la fin.
        await t("add_sheet", spreadsheet_id=SID, title=ONGLET)
        print(f"add_sheet             : {ONGLET}")
        try:
            w = await t("write_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!A1",
                        values=[["Produit", "Prix", "TTC"], ["Vélo", 299, "=B2*12/10"], ["Tente", 149, "=B3*12/10"]])
            print(f"write_range           : {w['updatedCells']} cellules (formules =B2*12/10 : valables dans toutes les locales)")
            a = await t("append_rows", spreadsheet_id=SID, range_a1=ONGLET, values=[["Sac", 39, "=B4*12/10"]])
            print(f"append_rows           : {a['updatedRange']}")
            await t("format_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!A1:C1", bold=True, background_hex="#FFF2CC")
            await t("format_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!B2:C4", number_format="#,##0.00 €")
            print("format_range          : en-tête en gras + fond, format monétaire")
            await t("batch_update", spreadsheet_id=SID, requests=[{"sortRange": {
                "range": {"sheetId": (await _sid(t, ONGLET)), "startRowIndex": 1, "endRowIndex": 4},
                "sortSpecs": [{"dimensionIndex": 1, "sortOrder": "DESCENDING"}]}}])
            trie = await t("read_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!A2:C4", render="UNFORMATTED_VALUE")
            print(f"batch_update (tri)    : {trie['values']}")
            assert [r[0] for r in trie["values"]] == ["Vélo", "Tente", "Sac"], trie
            assert abs(trie["values"][0][2] - 358.8) < 1e-6, trie
            f = await t("read_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!C2", render="FORMULA")
            print(f"read_range (FORMULA)  : {f['values']}")
            await t("insert_dimension", spreadsheet_id=SID, sheet=ONGLET, dimension="ROWS", start_index=1, count=2)
            await t("delete_dimension", spreadsheet_id=SID, sheet=ONGLET, dimension="ROWS", start_index=1, count=2)
            print("insert/delete_dimension : 2 lignes insérées puis supprimées")
            await t("clear_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!C2:C4")
            assert all(len(r) < 3 for r in (await t("read_range", spreadsheet_id=SID, range_a1=f"{ONGLET}!A2:C4"))["values"])
            print("clear_range           : colonne C effacée")
            await t("rename_sheet", spreadsheet_id=SID, current_title=ONGLET, new_title=ONGLET + "-r")
            print(f"rename_sheet          : {ONGLET}-r")
        finally:
            onglets = [s["title"] for s in (await t("get_spreadsheet_info", spreadsheet_id=SID))["sheets"]]
            for o in (ONGLET, ONGLET + "-r"):
                if o in onglets:
                    await t("delete_sheet", spreadsheet_id=SID, title=o)
                    print(f"delete_sheet          : {o} (classeur rendu intact)")
        try:
            r = await t("create_spreadsheet", title="test MCP")
            print(f"create_spreadsheet    : {r['url']}")
        except Exception as e:   # un compte de service n'a pas d'espace Drive ; un vrai utilisateur, si
            print(f"create_spreadsheet    : refusé pour ce compte ({str(e)[:70]}…)")
    print("\nOK : test réel terminé")


async def _sid(t, titre):
    return next(s["sheetId"] for s in (await t("get_spreadsheet_info", spreadsheet_id=SID))["sheets"] if s["title"] == titre)


asyncio.run(main())
