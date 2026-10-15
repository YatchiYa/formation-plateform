"""Calculs purs (sans réseau) : notation A1 <-> GridRange de l'API, et profil d'un tableau de valeurs."""
import re
from collections import Counter

from .api import Refus


def lettre(i: int) -> str:
    """0 -> A, 25 -> Z, 26 -> AA."""
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def colonne(lettres: str) -> int:
    """A -> 0, AA -> 26."""
    n = 0
    for c in lettres.upper():
        n = n * 26 + ord(c) - 64
    return n - 1


def separer(a1: str) -> tuple[str, str]:
    """« 'Mon onglet'!A1:B2 » -> (« Mon onglet », « A1:B2 ») ; « Ventes » -> (« Ventes », « »)."""
    m = re.fullmatch(r"\s*(?:'((?:[^']|'')+)'|([^!']+?))\s*(?:!(.*))?", a1)
    if not m:
        raise Refus(f"Plage illisible : « {a1} ».")
    titre = (m.group(1) or "").replace("''", "'") or m.group(2)
    return titre, (m.group(3) or "").strip()


def a1_vers_grille(a1: str, onglets: dict[str, int]) -> dict:
    """« Ventes!B2:D » -> {"sheetId": 7, "startRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 4}.
    onglets : {titre: sheetId}. Bornes absentes = ouvertes (toute la colonne, tout l'onglet)."""
    titre, cellules = separer(a1)
    if titre not in onglets:
        raise Refus(f"Onglet « {titre} » introuvable. Onglets : {', '.join(onglets)}.")
    g = {"sheetId": onglets[titre]}
    if not cellules:
        return g
    coins = []
    for coin in (cellules.upper().split(":") + [cellules.upper()])[:2]:   # « B2 » seul = la cellule B2
        m = re.fullmatch(r"\$?([A-Z]*)\$?(\d*)", coin)
        if not m or not (m.group(1) or m.group(2)):
            raise Refus(f"Plage illisible : « {a1} ».")
        coins.append(m.groups())
    (c0, r0), (c1, r1) = coins
    if c0:
        g["startColumnIndex"] = colonne(c0)
    if r0:
        g["startRowIndex"] = int(r0) - 1
    if c1:
        g["endColumnIndex"] = colonne(c1) + 1
    if r1:
        g["endRowIndex"] = int(r1)
    return g


def grille_vers_a1(g: dict, titres: dict[int, str]) -> str:
    """Inverse de a1_vers_grille (pour lire une plage décrite en GridRange). titres : {sheetId: titre}."""
    t = "'" + titres[g.get("sheetId", 0)].replace("'", "''") + "'"
    c0, c1 = g.get("startColumnIndex", 0), g.get("endColumnIndex")
    r0, r1 = g.get("startRowIndex", 0), g.get("endRowIndex")
    debut = f"{lettre(c0)}{r0 + 1}"
    fin = (lettre(c1 - 1) if c1 else "ZZZ") + (str(r1) if r1 else "")
    return f"{t}!{debut}:{fin}"


def _nombre(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    try:   # « 1 234,5 », « 12.5 », « 30 % »
        s = str(v).replace(" ", "").replace("\xa0", "").replace(" ", "").replace("%", "").replace(",", ".")
        return float(s) if s and s.count(".") <= 1 else None
    except ValueError:
        return None


def profil(valeurs: list[list], entete: bool = True) -> dict:
    """Portrait d'un tableau : par colonne, type dominant, remplissage, valeurs distinctes, stats numériques ;
    lignes en double. De quoi comprendre un classeur inconnu sans tout lire."""
    if not valeurs:
        return {"lignes": 0, "colonnes": []}
    noms = [str(x) for x in valeurs[0]] if entete else []
    data = valeurs[1:] if entete else valeurs
    largeur = max(len(r) for r in valeurs)
    colonnes = []
    for j in range(largeur):
        cel = [r[j] if j < len(r) else "" for r in data]
        pleines = [v for v in cel if str(v).strip() != ""]
        nums = [n for n in map(_nombre, pleines) if n is not None]
        c = {"colonne": lettre(j), "nom": noms[j] if j < len(noms) else "", "remplies": len(pleines),
             "vides": len(cel) - len(pleines), "distinctes": len(set(map(str, pleines)))}
        if pleines and len(nums) >= 0.8 * len(pleines):
            c.update(type="nombre", min=min(nums), max=max(nums), somme=round(sum(nums), 4),
                     moyenne=round(sum(nums) / len(nums), 4), non_numeriques=len(pleines) - len(nums))
        elif pleines:
            c.update(type="date" if all(re.fullmatch(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}.*", str(v)) for v in pleines[:50])
                     else "texte", frequentes=Counter(map(str, pleines)).most_common(5))
        else:
            c["type"] = "vide"
        colonnes.append(c)
    vues = Counter(tuple(map(str, r)) for r in data if any(str(v).strip() for v in r))
    return {"lignes": len(data), "colonnes": colonnes, "lignes_en_double": sum(n - 1 for n in vues.values() if n > 1)}
