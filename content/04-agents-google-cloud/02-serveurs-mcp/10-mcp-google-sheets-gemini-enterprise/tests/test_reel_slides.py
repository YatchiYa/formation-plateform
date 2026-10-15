"""Test RÉEL du serveur MCP Google Slides : vrais appels à Google, sur une vraie présentation, les 20 outils.

Appelle le serveur comme Gemini Enterprise (Authorization = jeton de l'utilisateur ; X-Serverless-Authorization si
ID_TOKEN, vers Cloud Run). Il ajoute des diapositives de test, puis les SUPPRIME : la présentation est rendue intacte.

Variables : MCP_URL (…/mcp du serveur PRODUIT=slides), USER_TOKEN (portées presentations + userinfo.email
+ drive.metadata.readonly), ID_TOKEN (Cloud Run), PRESENTATION_ID (une présentation que l'utilisateur peut modifier).
  python tests/test_reel_slides.py
"""
import asyncio
import os

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

URL, PID = os.environ["MCP_URL"], os.environ["PRESENTATION_ID"]
H = {"Authorization": f"Bearer {os.environ['USER_TOKEN']}"}
if os.getenv("ID_TOKEN"):
    H["X-Serverless-Authorization"] = f"Bearer {os.environ['ID_TOKEN']}"
IMAGE = "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"


async def main():
    async with Client(StreamableHttpTransport(URL, headers=H)) as c:
        async def t(nom, **args):
            r = await c.call_tool(nom, args)
            return r.data if r.data is not None else r.structured_content

        outils = await c.list_tools()
        print(f"tools/list : {len(outils)} outils")
        assert len(outils) == 20, sorted(o.name for o in outils)
        print(f"whoami                 : {(await t('whoami'))['email']}")
        trouves = await t("search_presentations", query="MCP Slides")
        assert any(f["id"] == PID for f in trouves), trouves
        print(f"search_presentations   : {len(trouves)} présentation(s), dont celle de test")
        info = await t("get_presentation_info", presentation_id=PID)
        avant = len(info["diapositives"])
        print(f"get_presentation_info  : « {info['titre']} », {avant} diapositive(s), format {info['format_pt']} pt")
        mises = await t("list_layouts", presentation_id=PID)
        print(f"list_layouts           : {len(mises)} mises en page, ex. {[m['nom'] for m in mises[:4]]}")

        crees = []
        try:
            a = await t("add_slide", presentation_id=PID, layout="TITLE_AND_BODY", title="Bilan magasin Lille",
                        body="Chiffre d'affaires : 120 k€\nVisiteurs : 18 400\nTop rayon : randonnée", notes="Insister sur la randonnée.")
            crees.append(a["objectId"])
            print(f"add_slide              : {a['objectId']} ({a['zones_remplies']} zones remplies : titre, corps, notes)")
            assert a["zones_remplies"] == 3, a
            d = await t("duplicate_slide", presentation_id=PID, slide=a["objectId"])
            crees.append(d["objectId"])
            print(f"duplicate_slide        : {d['objectId']}")
            m = await t("move_slide", presentation_id=PID, slide=d["objectId"], position=1)
            print(f"move_slide             : copie placée en position {m['position']}")
            assert (await t("get_presentation_info", presentation_id=PID))["diapositives"][0]["objectId"] == d["objectId"]
            b = await t("insert_text_box", presentation_id=PID, slide=a["objectId"], text="Objectif 2027 : +15 %",
                        x_pt=40, y_pt=330, width_pt=300, height_pt=40, font_size_pt=18)
            f = await t("format_text", presentation_id=PID, object_id=b["objectId"], bold=True, color_hex="#0082C3", alignment="CENTER")
            print(f"insert_text_box/format : {b['objectId']} ; mise en forme {f['applique']}")
            im = await t("insert_image", presentation_id=PID, slide=a["objectId"], image_url=IMAGE, x_pt=500, y_pt=20, width_pt=180, height_pt=60)
            print(f"insert_image           : {im['objectId']}")
            tb = await t("create_table", presentation_id=PID, slide=d["objectId"],
                         rows=[["Magasin", "CA"], ["Lille", "120 k€"], ["Paris", "310 k€"]], y_pt=200, height_pt=120)
            print(f"create_table           : {tb['lignes']} x {tb['colonnes']}")
            await t("set_background", presentation_id=PID, slide=d["objectId"], color_hex="#F5F6FB")
            print("set_background         : fond #F5F6FB")
            r = await t("replace_text", presentation_id=PID, find="Lille", replace="Villeneuve-d'Ascq", slides=[a["objectId"], d["objectId"]])
            print(f"replace_text           : {r['remplacements']} remplacement(s)")
            assert r["remplacements"] >= 3, r
            n = await t("set_speaker_notes", presentation_id=PID, slide=a["objectId"], notes="Notes mises à jour par le MCP.")
            print(f"set_speaker_notes      : notes remplacées = {n['notes_remplacees']}")
            bu = await t("batch_update", presentation_id=PID, requests=[{"createLine": {"lineCategory": "STRAIGHT", "elementProperties": {
                "pageObjectId": a["objectId"], "size": {"width": {"magnitude": 640, "unit": "PT"}, "height": {"magnitude": 0, "unit": "PT"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 40, "translateY": 320, "unit": "PT"}}}}])
            print(f"batch_update (ligne)   : {len(bu['replies'])} réponse")
            lu = await t("read_slide", presentation_id=PID, slide=a["objectId"])
            print(f"read_slide             : {[(e['type'], e.get('zone_du_modele'), (e.get('texte') or '')[:30]) for e in lu['elements']][:6]}")
            print(f"                         notes : {lu['notes'].strip()!r}")
            assert lu["notes"].strip() == "Notes mises à jour par le MCP.", lu["notes"]
            tout = await t("read_presentation_text", presentation_id=PID)
            print(f"read_presentation_text : {len(tout['diapositives'])} diapositives ; diapo 1 : {tout['diapositives'][0]['texte'][:80]!r}")
            th = await t("get_slide_thumbnail", presentation_id=PID, slide=a["objectId"], size="SMALL")
            print(f"get_slide_thumbnail    : {th['largeur']} x {th['hauteur']} px, {th['url'][:60]}…")
        finally:
            for oid in crees:
                await t("delete_slide", presentation_id=PID, slide=oid)
            print(f"delete_slide           : {len(crees)} diapositive(s) de test supprimée(s)")
        assert len((await t("get_presentation_info", presentation_id=PID))["diapositives"]) == avant
        print(f"présentation rendue intacte : {avant} diapositive(s)")
        try:
            print(f"create_presentation    : {(await t('create_presentation', title='test MCP'))['url']}")
        except Exception as e:   # compte de service : pas d'espace Drive ; un vrai utilisateur, si
            print(f"create_presentation    : refusé pour ce compte ({str(e)[:70]}…)")
    print("\nOK : test réel Slides terminé")


asyncio.run(main())
