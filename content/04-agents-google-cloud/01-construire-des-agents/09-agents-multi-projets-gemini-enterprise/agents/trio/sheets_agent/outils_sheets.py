"""Google Sheets niveau expert : comprendre, lire, chercher, écrire, structurer, analyser, visualiser. JAMAIS de perte.

Pourquoi l'agent ne peut RIEN supprimer ni effacer :
  - la portée « spreadsheets » permet tout DANS un classeur (Google n'a pas de portée « sans suppression ») mais pas
    de supprimer le fichier (il faudrait une portée Drive en écriture) ;
  - le reste est bloqué ICI, dans le code : aucun outil n'efface ; sheets_ecrire refuse de vider une cellule remplie et
    demande confirmation avant d'écraser ; sheets_modifier n'accepte que des requêtes sans perte (AUTORISEES), avec
    des garde-fous sur celles qui pourraient en causer (fusion de cellules remplies, réduction de la grille…).
Toute modification reste dans l'historique des versions du classeur (Fichier > Historique des versions).
"""
import random
import urllib.parse

from . import grille
from .api import Refus, appel, id_fichier, jeton, outil, q

SHEETS = "https://sheets.googleapis.com/v4/spreadsheets"
RENDUS = {"valeurs": "FORMATTED_VALUE", "brut": "UNFORMATTED_VALUE", "formules": "FORMULA"}
# Requêtes batchUpdate acceptées : elles ajoutent, mettent en forme, déplacent, sans perte de données.
# Exclues : delete*, clear*, cutPaste, copyPaste, pasteData, updateCells, findReplace, autoFill, trimWhitespace,
# randomizeRange, textToColumns, deleteDuplicates… (elles peuvent effacer ou écraser des données).
AUTORISEES = {
    "addSheet", "duplicateSheet", "updateSheetProperties", "updateSpreadsheetProperties",
    "repeatCell", "mergeCells", "unmergeCells", "updateBorders", "autoResizeDimensions", "updateDimensionProperties",
    "insertDimension", "appendDimension", "insertRange", "moveDimension", "sortRange",
    "setDataValidation", "addConditionalFormatRule", "updateConditionalFormatRule",
    "addNamedRange", "updateNamedRange", "addBanding", "updateBanding",
    "addChart", "updateChartSpec", "updateEmbeddedObjectPosition", "updateEmbeddedObjectBorder",
    "setBasicFilter", "addFilterView", "updateFilterView", "duplicateFilterView", "addSlicer", "updateSlicerSpec",
    "addProtectedRange", "updateProtectedRange", "addDimensionGroup", "updateDimensionGroup"}
TYPES_GRAPHIQUE = {"COLUMN", "BAR", "LINE", "AREA", "STEPPED_AREA", "SCATTER", "COMBO", "PIE"}
FONCTIONS = {"SUM", "COUNTA", "COUNT", "COUNTUNIQUE", "AVERAGE", "MAX", "MIN", "MEDIAN", "PRODUCT", "STDEV", "VAR"}


def _vide(v) -> bool:
    return v is None or str(v).strip() == ""


def _onglets(cid: str, j: str) -> list[dict]:
    """Propriétés de chaque onglet (titre, sheetId, taille) + bandes et filtre existants."""
    r = appel(f"{SHEETS}/{cid}?" + q({"fields": "sheets(properties,bandedRanges.bandedRangeId,basicFilter.range)"}), j)
    return r.get("sheets", [])


def _ids(onglets: list[dict]) -> dict[str, int]:
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in onglets}


def _lire(cid: str, j: str, plages: list[str], rendu: str = "FORMATTED_VALUE") -> list[list[list]]:
    r = appel(f"{SHEETS}/{cid}/values:batchGet?" + q({"ranges": plages, "valueRenderOption": rendu}), j)
    return [v.get("values", []) for v in r.get("valueRanges", [])]


def _maj(cid: str, j: str, requetes: list[dict]) -> dict:
    return appel(f"{SHEETS}/{cid}:batchUpdate", j, {"requests": requetes})


# ---------- Comprendre ----------
@outil
def sheets_infos(classeur: str, tool_context=None) -> dict:
    """La carte d'un classeur : titre, langue (locale, qui fixe le format des nombres et des dates), fuseau, onglets
    (nom, sheetId, lignes, colonnes, lignes/colonnes figées, masqué), plages nommées, graphiques, filtres, plages
    protégées, mises en forme conditionnelles. À appeler EN PREMIER sur tout classeur.

    Args:
        classeur: Le lien ou l'id du classeur.
    """
    champs = ("properties(title,locale,timeZone),spreadsheetUrl,namedRanges,sheets(properties,charts(chartId,spec.title),"
              "basicFilter.range,filterViews(filterViewId,title),protectedRanges(protectedRangeId,description),"
              "conditionalFormats.ranges,bandedRanges.bandedRangeId)")
    r = appel(f"{SHEETS}/{id_fichier(classeur)}?" + q({"fields": champs}), jeton(tool_context))
    titres = {s["properties"]["sheetId"]: s["properties"]["title"] for s in r.get("sheets", [])}
    onglets = []
    for s in r.get("sheets", []):
        p, gp = s["properties"], s["properties"].get("gridProperties", {})
        onglets.append({
            "nom": p["title"], "sheetId": p["sheetId"], "type": p.get("sheetType", "GRID"), "masque": p.get("hidden", False),
            "lignes": gp.get("rowCount"), "colonnes": gp.get("columnCount"),
            "lignes_figees": gp.get("frozenRowCount", 0), "colonnes_figees": gp.get("frozenColumnCount", 0),
            "graphiques": [{"chartId": c["chartId"], "titre": c.get("spec", {}).get("title", "")} for c in s.get("charts", [])],
            "filtre": "basicFilter" in s, "vues_filtrees": [v.get("title") for v in s.get("filterViews", [])],
            "plages_protegees": len(s.get("protectedRanges", [])), "mises_en_forme_conditionnelles": len(s.get("conditionalFormats", [])),
            "bandes": len(s.get("bandedRanges", []))})
    return {"titre": r["properties"]["title"], "lien": r["spreadsheetUrl"], "locale": r["properties"].get("locale"),
            "fuseau": r["properties"].get("timeZone"), "onglets": onglets,
            "plages_nommees": [{"nom": n["name"], "plage": grille.grille_vers_a1(n["range"], titres)}
                               for n in r.get("namedRanges", []) if n.get("range", {}).get("sheetId", 0) in titres]}


@outil
def sheets_lire(classeur: str, plages: list[str], rendu: str = "valeurs", max_lignes: int = 500, tool_context=None) -> dict:
    """Les valeurs d'une ou plusieurs plages, en UN appel.

    Args:
        classeur: Le lien ou l'id du classeur.
        plages: Notation A1, ex. ["Ventes!A1:F50", "Stock"] (un nom d'onglet seul = tout l'onglet).
        rendu: « valeurs » (affichées, formatées), « brut » (nombres et dates non formatés, pour calculer) ou
               « formules » (le texte des formules, pour les auditer ou les recopier).
        max_lignes: Lignes renvoyées au plus par plage (1 à 5000) ; au-delà, « tronque » le signale.
    """
    if rendu not in RENDUS:
        raise Refus(f"rendu doit valoir : {', '.join(RENDUS)}.")
    n = max(1, min(int(max_lignes), 5000))
    lues = _lire(id_fichier(classeur), jeton(tool_context), plages, RENDUS[rendu])
    return {"plages": [{"plage": p, "lignes": len(v), "valeurs": v[:n], "tronque": len(v) > n} for p, v in zip(plages, lues)]}


@outil
def sheets_profil(classeur: str, plage: str, entete: bool = True, tool_context=None) -> dict:
    """Le portrait d'un tableau sans le lire en entier : par colonne, type (nombre, date, texte), cellules remplies et
    vides, valeurs distinctes, min/max/somme/moyenne, valeurs fréquentes ; nombre de lignes en double. Idéal avant
    une analyse, un nettoyage ou un tableau croisé.

    Args:
        classeur: Le lien ou l'id du classeur.
        plage: Le tableau, ex. « Ventes » ou « Ventes!A1:H ».
        entete: True si la 1re ligne contient les noms de colonnes.
    """
    valeurs = _lire(id_fichier(classeur), jeton(tool_context), [plage], "UNFORMATTED_VALUE")[0]
    return {"plage": plage, **grille.profil(valeurs, entete)}


@outil
def sheets_chercher(classeur: str, texte: str, nombre: int = 50, tool_context=None) -> dict:
    """Cherche un texte dans TOUS les onglets d'un classeur (sans tenir compte des majuscules) : cellule, valeur.

    Args:
        classeur: Le lien ou l'id du classeur.
        texte: Le texte à trouver.
        nombre: Résultats au plus (1 à 200).
    """
    cid, j = id_fichier(classeur), jeton(tool_context)
    titres = list(_ids(_onglets(cid, j)))
    cible, trouves = texte.casefold(), []
    for titre, valeurs in zip(titres, _lire(cid, j, ["'" + t.replace("'", "''") + "'" for t in titres])):
        for i, ligne in enumerate(valeurs):
            for c, v in enumerate(ligne):
                if cible in str(v).casefold() and len(trouves) < max(1, min(int(nombre), 200)):
                    trouves.append({"onglet": titre, "cellule": f"{grille.lettre(c)}{i + 1}", "valeur": v})
    return {"texte": texte, "nombre": len(trouves), "resultats": trouves}


# ---------- Écrire (sans jamais effacer) ----------
@outil
def sheets_creer(titre: str, onglets: list[str] | None = None, entetes: list[str] | None = None, tool_context=None) -> dict:
    """Crée un classeur dans le Drive de l'utilisateur. Avec des en-têtes : 1re ligne de chaque onglet en gras, figée.

    Args:
        titre: Le titre du classeur.
        onglets: Les noms des onglets (vide = un seul onglet par défaut).
        entetes: Les noms de colonnes à mettre en 1re ligne de chaque onglet (facultatif).
    """
    j = jeton(tool_context)
    r = appel(SHEETS, j, {"properties": {"title": titre}, "sheets": [{"properties": {"title": o}} for o in onglets or []]})
    if entetes:
        feuilles = [s["properties"] for s in r.get("sheets", [])]
        appel(f"{SHEETS}/{r['spreadsheetId']}/values:batchUpdate", j, {"valueInputOption": "USER_ENTERED", "data": [
            {"range": "'" + p["title"].replace("'", "''") + "'!A1", "values": [entetes]} for p in feuilles]})
        _maj(r["spreadsheetId"], j, [x for p in feuilles for x in _style_entete(p["sheetId"], len(entetes))])
    return {"id": r["spreadsheetId"], "lien": r["spreadsheetUrl"]}


@outil
def sheets_ecrire(classeur: str, ecritures: list[dict], confirme: bool = False, tool_context=None) -> dict:
    """Écrit des valeurs ou des formules dans une ou plusieurs plages, en UN appel. Formules en anglais avec des
    virgules, ex. « =SUMIFS(C:C,A:A,"Lille") », quelle que soit la langue du classeur.
    Garde-fous : ne vide JAMAIS une cellule remplie ; si des cellules remplies changeraient, rien n'est écrit et
    l'outil renvoie status « confirmation_requise » avec l'avant/après : le montrer à l'utilisateur, puis rappeler
    avec confirme=True seulement s'il accepte. Renvoie les anciennes valeurs (pour annuler si besoin).

    Args:
        classeur: Le lien ou l'id du classeur.
        ecritures: Liste de {"plage": coin haut gauche ou plage A1, "valeurs": lignes}, ex.
                   [{"plage": "Ventes!A1", "valeurs": [["Ville", "Total"], ["Lille", "120"]]},
                    {"plage": "Ventes!D2", "valeurs": [["=B2*C2"]]}].
        confirme: True seulement après accord explicite de l'utilisateur pour écraser les cellules signalées.
    """
    cid, j = id_fichier(classeur), jeton(tool_context)
    if not ecritures or any(not isinstance(e, dict) or "plage" not in e or "valeurs" not in e for e in ecritures):
        raise Refus('ecritures : liste de {"plage": "...", "valeurs": [[...]]}.')
    avant = _lire(cid, j, [e["plage"] for e in ecritures], "FORMULA")   # FORMULA : une formule compte comme remplie
    ecrasees = []
    for e, anc in zip(ecritures, avant):
        for i, ligne in enumerate(e["valeurs"]):
            for c, v in enumerate(ligne):
                old = anc[i][c] if i < len(anc) and c < len(anc[i]) else ""
                if _vide(old):
                    continue
                if _vide(v):
                    raise Refus(f"Refusé : {e['plage']}, ligne {i + 1}, colonne {c + 1} contient « {old} » ; cet agent ne "
                                "peut pas effacer de données. Mettre une valeur, ou laisser l'utilisateur le faire.")
                if str(old) != str(v):
                    ecrasees.append({"plage": e["plage"], "ligne": i + 1, "colonne": c + 1, "avant": old, "apres": v})
    if ecrasees and not confirme:
        return {"status": "confirmation_requise", "cellules_a_ecraser": len(ecrasees), "apercu": ecrasees[:30],
                "consigne": "Montrer cet avant/après à l'utilisateur ; rappeler avec confirme=True s'il accepte."}
    r = appel(f"{SHEETS}/{cid}/values:batchUpdate", j, {"valueInputOption": "USER_ENTERED", "data": [
        {"range": e["plage"], "values": e["valeurs"]} for e in ecritures]})
    return {"cellules_modifiees": r.get("totalUpdatedCells", 0),
            "plages": [x.get("updatedRange") for x in r.get("responses", [])],
            "anciennes_valeurs": [{"plage": e["plage"], "valeurs": a} for e, a in zip(ecritures, avant) if a]}


@outil
def sheets_ajouter_lignes(classeur: str, onglet: str, lignes: list[list[str]], tool_context=None) -> dict:
    """Ajoute des lignes après les dernières données d'un onglet (insère de nouvelles lignes : n'écrase rien).

    Args:
        classeur: Le lien ou l'id du classeur.
        onglet: Le nom de l'onglet.
        lignes: Les lignes à ajouter, ex. [["2026-10-12", "Lille", "120"]].
    """
    r = appel(f"{SHEETS}/{id_fichier(classeur)}/values/{urllib.parse.quote(onglet)}:append?"
              + q({"valueInputOption": "USER_ENTERED", "insertDataOption": "INSERT_ROWS"}),
              jeton(tool_context), {"values": lignes})
    return {"plage": r.get("updates", {}).get("updatedRange"), "lignes_ajoutees": r.get("updates", {}).get("updatedRows", 0)}


def verifier_requetes(requetes: list[dict]) -> None:
    """Refuse toute requête batchUpdate qui pourrait supprimer ou effacer (vérification sans réseau)."""
    for r in requetes:
        if not isinstance(r, dict) or len(r) != 1 or next(iter(r)) not in AUTORISEES:
            nom = ", ".join(r) if isinstance(r, dict) else str(r)[:80]
            raise Refus(f"Refusé : requête « {nom} » non autorisée (cet agent ne supprime ni n'efface rien). "
                        f"Autorisées : {', '.join(sorted(AUTORISEES))}.")
        nom, corps = next(iter(r.items()))
        champs = [f.strip() for f in str(corps.get("fields", "")).split(",") if f.strip()]
        if nom == "repeatCell" and not (champs and all(f.startswith("userEnteredFormat") for f in champs)):
            raise Refus("Refusé : repeatCell sert à la mise en forme ; fields doit commencer par « userEnteredFormat ». "
                        "Pour écrire des valeurs : sheets_ecrire.")
        if nom == "setDataValidation" and not corps.get("rule"):
            raise Refus("Refusé : setDataValidation sans « rule » supprimerait une validation.")
        if nom == "updateSheetProperties" and any(f in ("*", "gridProperties") or f.endswith(("rowCount", "columnCount"))
                                                  for f in champs):
            raise Refus("Refusé : changer le nombre de lignes ou de colonnes (ou fields « * ») peut tronquer l'onglet. "
                        "Pour agrandir : appendDimension. Pour figer : fields « gridProperties.frozenRowCount ».")


@outil
def sheets_modifier(classeur: str, requetes: list[dict], tool_context=None) -> dict:
    """Modifie la structure ou la mise en forme d'un classeur (API batchUpdate), SANS suppression, en UN appel
    atomique (tout ou rien). Requêtes acceptées : voir AUTORISEES dans le message d'erreur ; les plus utiles :
    repeatCell (mise en forme, fields « userEnteredFormat… »), updateSheetProperties (renommer, figer, couleur),
    addConditionalFormatRule, setDataValidation (listes déroulantes), addBanding, addNamedRange, addChart,
    addProtectedRange, setBasicFilter, addFilterView, insertDimension, appendDimension, sortRange, mergeCells
    (refusé si plus d'une cellule remplie), autoResizeDimensions, updateBorders. Les plages sont des GridRange
    avec le sheetId (sheets_infos) ; index de début inclus, de fin exclu, à partir de 0.
    Pour les recettes prêtes à l'emploi, charger la compétence « sheets-formatting ».

    Args:
        classeur: Le lien ou l'id du classeur.
        requetes: Les requêtes, au format de l'API, ex. [{"repeatCell": {"range": {"sheetId": 0, "startRowIndex": 0,
                  "endRowIndex": 1}, "cell": {"userEnteredFormat": {"textFormat": {"bold": true}}},
                  "fields": "userEnteredFormat.textFormat.bold"}}].
    """
    if not requetes:
        raise Refus("Aucune requête.")
    verifier_requetes(requetes)
    cid, j = id_fichier(classeur), jeton(tool_context)
    fusions = [r["mergeCells"]["range"] for r in requetes if "mergeCells" in r]
    if fusions:   # fusionner ne garde que la cellule en haut à gauche : refusé s'il y a plus d'une cellule remplie
        titres = {v: k for k, v in _ids(_onglets(cid, j)).items()}
        for g, valeurs in zip(fusions, _lire(cid, j, [grille.grille_vers_a1(g, titres) for g in fusions], "FORMULA")):
            if sum(not _vide(v) for ligne in valeurs for v in ligne) > 1:
                raise Refus(f"Refusé : fusionner {grille.grille_vers_a1(g, titres)} effacerait des valeurs (une seule "
                            "cellule est gardée). Regrouper d'abord les valeurs, ou centrer sur plusieurs colonnes.")
    r = _maj(cid, j, requetes)
    return {"requetes_appliquees": len(r.get("replies", [])), "reponses": [x for x in r.get("replies", []) if x][:20]}


# ---------- Analyser et présenter (toujours dans un NOUVEL onglet ou par-dessus : aucune donnée touchée) ----------
def _style_entete(sheet_id: int, largeur: int) -> list[dict]:
    return [
        {"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0,
                                  "endColumnIndex": largeur},
                        "cell": {"userEnteredFormat": {
                            "backgroundColor": {"red": 0.0, "green": 0.31, "blue": 0.65},   # bleu Acme
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                            "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP"}},
                        "fields": "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy)"}},
        {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 1}},
                                   "fields": "gridProperties.frozenRowCount"}}]


def _nouvel_onglet(titre: str, existants: dict[str, int]) -> tuple[int, dict]:
    if titre in existants:
        raise Refus(f"L'onglet « {titre} » existe déjà : choisir un autre nom.")
    nid = random.randint(10**6, 2**31 - 1)   # sheetId choisi ici : addSheet et son contenu partent dans le même appel
    return nid, {"addSheet": {"properties": {"sheetId": nid, "title": titre}}}


@outil
def sheets_embellir(classeur: str, onglet: str, tool_context=None) -> dict:
    """Met un tableau au propre en un geste (« mettre sous forme de tableau ») : en-tête coloré en gras, 1re ligne
    figée, lignes en bandes alternées, filtre, colonnes ajustées au contenu. Ne touche à aucune valeur.

    Args:
        classeur: Le lien ou l'id du classeur.
        onglet: Le nom de l'onglet (le tableau commence en A1).
    """
    cid, j = id_fichier(classeur), jeton(tool_context)
    s = next((s for s in _onglets(cid, j) if s["properties"]["title"] == onglet), None)
    if not s:
        raise Refus(f"Onglet « {onglet} » introuvable.")
    valeurs = _lire(cid, j, ["'" + onglet.replace("'", "''") + "'"])[0]
    if not valeurs:
        raise Refus(f"L'onglet « {onglet} » est vide.")
    sid, hauteur, largeur = s["properties"]["sheetId"], len(valeurs), max(map(len, valeurs))
    tableau = {"sheetId": sid, "startRowIndex": 0, "endRowIndex": hauteur, "startColumnIndex": 0, "endColumnIndex": largeur}
    req = _style_entete(sid, largeur)
    if not s.get("bandedRanges"):
        req.append({"addBanding": {"bandedRange": {"range": tableau, "rowProperties": {
            "headerColor": {"red": 0.0, "green": 0.31, "blue": 0.65}, "firstBandColor": {"red": 1, "green": 1, "blue": 1},
            "secondBandColor": {"red": 0.93, "green": 0.95, "blue": 0.98}}}}})
    if not s.get("basicFilter"):
        req.append({"setBasicFilter": {"filter": {"range": tableau}}})
    req.append({"autoResizeDimensions": {"dimensions": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0,
                                                        "endIndex": largeur}}})
    _maj(cid, j, req)
    return {"onglet": onglet, "tableau": f"A1:{grille.lettre(largeur - 1)}{hauteur}", "requetes_appliquees": len(req)}


@outil
def sheets_tableau_croise(classeur: str, source: str, lignes: list[str], valeurs: list[dict],
                          colonnes: list[str] | None = None, nouvel_onglet: str = "Tableau croisé",
                          tool_context=None) -> dict:
    """Crée un VRAI tableau croisé dynamique Google Sheets (il se met à jour avec les données) dans un nouvel onglet.

    Args:
        classeur: Le lien ou l'id du classeur.
        source: Le tableau source AVEC sa ligne d'en-tête, ex. « Ventes!A1:F » (colonnes ouvertes en bas = les
                futures lignes seront prises en compte).
        lignes: Noms des colonnes (en-têtes) à mettre en lignes, ex. ["Magasin"].
        valeurs: Ce qu'il faut calculer, ex. [{"colonne": "CA", "fonction": "SUM"}, {"colonne": "Commande",
                 "fonction": "COUNTA"}]. Fonctions : SUM, COUNTA, COUNT, COUNTUNIQUE, AVERAGE, MAX, MIN, MEDIAN…
        colonnes: Noms des colonnes à mettre en colonnes, ex. ["Mois"] (facultatif).
        nouvel_onglet: Le nom du nouvel onglet.
    """
    cid, j = id_fichier(classeur), jeton(tool_context)
    ids = _ids(_onglets(cid, j))
    g = grille.a1_vers_grille(source, ids)
    debut = g.get("startRowIndex", 0)
    entete = grille.grille_vers_a1({**g, "endRowIndex": debut + 1}, {v: k for k, v in ids.items()})
    noms = [str(x).strip() for x in (_lire(cid, j, [entete])[0] or [[]])[0]]

    def pos(nom):
        if nom.strip() not in noms:
            raise Refus(f"Colonne « {nom} » absente de l'en-tête de {source}. En-tête : {', '.join(noms)}.")
        return noms.index(nom.strip())   # sourceColumnOffset : relatif au début de la source

    vals = []
    for v in valeurs:
        fn = str(v.get("fonction", "SUM")).upper()
        if fn not in FONCTIONS:
            raise Refus(f"Fonction « {fn} » inconnue. Possibles : {', '.join(sorted(FONCTIONS))}.")
        vals.append({"summarizeFunction": fn, "sourceColumnOffset": pos(v["colonne"]), "name": f"{fn} de {v['colonne']}"})
    groupe = lambda n: {"sourceColumnOffset": pos(n), "showTotals": True, "sortOrder": "ASCENDING"}  # noqa: E731
    nid, ajout = _nouvel_onglet(nouvel_onglet, ids)
    pivot = {"source": g, "rows": [groupe(n) for n in lignes], "columns": [groupe(n) for n in colonnes or []],
             "values": vals, "valueLayout": "HORIZONTAL"}
    _maj(cid, j, [ajout, {"updateCells": {"start": {"sheetId": nid, "rowIndex": 0, "columnIndex": 0},
                                          "rows": [{"values": [{"pivotTable": pivot}]}], "fields": "pivotTable"}}])
    return {"onglet": nouvel_onglet, "sheetId": nid, "source": source}


@outil
def sheets_graphique(classeur: str, source: str, type_graphique: str = "COLUMN", titre: str = "",
                     ancre: str = "", tool_context=None) -> dict:
    """Crée un graphique à partir d'un tableau : 1re colonne = catégories (axe X), colonnes suivantes = séries,
    1re ligne = en-têtes (noms des séries). Ne touche à aucune donnée.

    Args:
        classeur: Le lien ou l'id du classeur.
        source: Plage AVEC en-tête et colonnes bornées, ex. « Synthèse!A1:C13 » (A = mois, B et C = séries).
        type_graphique: COLUMN, BAR, LINE, AREA, STEPPED_AREA, SCATTER, COMBO ou PIE (PIE : 1 seule série).
        titre: Le titre du graphique.
        ancre: Cellule où poser le graphique, ex. « Synthèse!E2 » ; vide = dans un nouvel onglet dédié.
    """
    t = type_graphique.upper()
    if t not in TYPES_GRAPHIQUE:
        raise Refus(f"Type « {type_graphique} » inconnu. Possibles : {', '.join(sorted(TYPES_GRAPHIQUE))}.")
    cid, j = id_fichier(classeur), jeton(tool_context)
    ids = _ids(_onglets(cid, j))
    g = grille.a1_vers_grille(source, ids)
    c0, c1 = g.get("startColumnIndex", 0), g.get("endColumnIndex")
    if c1 is None or c1 - c0 < 2:
        raise Refus("source : il faut des colonnes bornées, au moins 2 (catégories + 1 série), ex. « Onglet!A1:C13 ».")
    col = lambda c: {"sourceRange": {"sources": [{**g, "startColumnIndex": c, "endColumnIndex": c + 1}]}}  # noqa: E731
    if t == "PIE":
        spec = {"title": titre, "pieChart": {"legendPosition": "RIGHT_LEGEND", "domain": col(c0), "series": col(c0 + 1)}}
    else:
        spec = {"title": titre, "basicChart": {
            "chartType": t, "legendPosition": "BOTTOM_LEGEND", "headerCount": 1,
            "domains": [{"domain": col(c0)}],
            "series": [{"series": col(c), "targetAxis": "LEFT_AXIS", **({"type": "LINE"} if t == "COMBO" and c > c0 + 1 else {})}
                       for c in range(c0 + 1, c1)]}}
    if ancre:
        a = grille.a1_vers_grille(ancre, ids)
        position = {"overlayPosition": {"anchorCell": {"sheetId": a["sheetId"], "rowIndex": a.get("startRowIndex", 0),
                                                       "columnIndex": a.get("startColumnIndex", 0)}}}
    else:
        position = {"newSheet": True}
    r = _maj(cid, j, [{"addChart": {"chart": {"spec": spec, "position": position}}}])
    return {"chartId": r["replies"][0]["addChart"]["chart"]["chartId"], "type": t,
            "emplacement": ancre or "nouvel onglet"}


OUTILS = [sheets_infos, sheets_lire, sheets_profil, sheets_chercher, sheets_creer, sheets_ecrire, sheets_ajouter_lignes,
          sheets_modifier, sheets_embellir, sheets_tableau_croise, sheets_graphique]
