"""Gmail, Agenda, Drive : LECTURE SEULE (portées readonly : Google refuse toute écriture, quoi que demande le modèle)."""
import base64
import datetime
import re
from concurrent.futures import ThreadPoolExecutor

from .api import Refus, appel, id_fichier, jeton, outil, q

GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me"
DRIVE = "https://www.googleapis.com/drive/v3/files"
CLASSEUR = "application/vnd.google-apps.spreadsheet"


@outil
def qui_suis_je(tool_context) -> dict:
    """Le compte Google de l'utilisateur connecté (nom, e-mail) et son quota Drive."""
    r = appel("https://www.googleapis.com/drive/v3/about?fields=user,storageQuota", jeton(tool_context))
    return {"nom": r["user"].get("displayName"), "compte": r["user"].get("emailAddress"),
            "drive_utilise_go": round(int(r.get("storageQuota", {}).get("usage", 0)) / 1e9, 2)}


@outil
def gmail_chercher(filtre: str = "newer_than:7d in:inbox", nombre: int = 20, tool_context=None) -> dict:
    """Cherche des e-mails de l'utilisateur : expéditeur, sujet, date, extrait, non lu, important, pièces jointes, id.

    Args:
        filtre: Recherche Gmail, comme dans Gmail. Ex. « is:unread », « from:x@acme.example newer_than:30d »,
                « has:attachment filename:xlsx ».
        nombre: Combien au plus (1 à 50).
    """
    j = jeton(tool_context)
    ids = appel(f"{GMAIL}/messages?" + q({"q": filtre, "maxResults": max(1, min(int(nombre), 50))}), j).get("messages", [])

    def meta(m):
        d = appel(f"{GMAIL}/messages/{m['id']}?" + q({"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]}), j)
        h = {x["name"]: x["value"] for x in d.get("payload", {}).get("headers", [])}
        return {"id": m["id"], "de": h.get("From", ""), "sujet": h.get("Subject", ""), "date": h.get("Date", ""),
                "extrait": d.get("snippet", "")[:300], "non_lu": "UNREAD" in d.get("labelIds", []),
                "important": "IMPORTANT" in d.get("labelIds", [])}

    with ThreadPoolExecutor(8) as ex:   # 8 en parallèle : 50 e-mails en ~1 s au lieu de ~10 s
        emails = list(ex.map(meta, ids))
    return {"filtre": filtre, "nombre": len(emails), "emails": emails}


@outil
def gmail_lire(email_id: str, tool_context=None) -> dict:
    """Le texte complet d'un e-mail (id donné par gmail_chercher) et la liste de ses pièces jointes.

    Args:
        email_id: L'id de l'e-mail.
    """
    d = appel(f"{GMAIL}/messages/{email_id}?format=full", jeton(tool_context))
    h = {x["name"]: x["value"] for x in d.get("payload", {}).get("headers", [])}
    texte, pj, pile = "", [], [d.get("payload", {})]
    while pile:   # 1re partie text/plain (sinon text/html), en parcourant les pièces imbriquées
        p = pile.pop(0)
        if p.get("filename"):
            pj.append({"nom": p["filename"], "type": p.get("mimeType"), "taille": p.get("body", {}).get("size")})
        elif not texte and p.get("mimeType") in ("text/plain", "text/html") and p.get("body", {}).get("data"):
            texte = base64.urlsafe_b64decode(p["body"]["data"] + "==").decode(errors="replace")
        pile += p.get("parts", [])
    return {"de": h.get("From", ""), "a": h.get("To", ""), "sujet": h.get("Subject", ""), "date": h.get("Date", ""),
            "texte": re.sub(r"<[^>]+>", " ", texte)[:8000], "pieces_jointes": pj}


@outil
def agenda_evenements(a_partir_du: str = "", jours: int = 7, tool_context=None) -> dict:
    """Les événements de l'agenda principal de l'utilisateur sur une période.

    Args:
        a_partir_du: Date de début AAAA-MM-JJ (vide = aujourd'hui).
        jours: Nombre de jours (1 à 60).
    """
    try:
        debut = datetime.date.fromisoformat(a_partir_du) if a_partir_du else datetime.date.today()
    except ValueError:
        raise Refus(f"Date « {a_partir_du} » invalide : format AAAA-MM-JJ.")
    fin = debut + datetime.timedelta(days=max(1, min(int(jours), 60)))
    r = appel("https://www.googleapis.com/calendar/v3/calendars/primary/events?" + q({
        "timeMin": f"{debut}T00:00:00Z", "timeMax": f"{fin}T00:00:00Z", "singleEvents": "true",
        "orderBy": "startTime", "maxResults": 250}), jeton(tool_context))
    return {"fuseau": r.get("timeZone"), "evenements": [{
        "titre": e.get("summary", "(sans titre)"), "debut": e["start"].get("dateTime") or e["start"].get("date"),
        "fin": e["end"].get("dateTime") or e["end"].get("date"), "lieu": e.get("location", ""),
        "participants": [a.get("email") for a in e.get("attendees", [])][:15], "lien": e.get("htmlLink")}
        for e in r.get("items", [])]}


@outil
def drive_chercher(texte: str = "", classeurs_seulement: bool = False, nombre: int = 20, tool_context=None) -> dict:
    """Cherche des fichiers dans le Drive de l'utilisateur (et les Drive partagés qu'il voit).

    Args:
        texte: Mots à chercher dans le nom ou le contenu (vide = les fichiers récents).
        classeurs_seulement: True pour ne chercher que des Google Sheets.
        nombre: Combien au plus (1 à 50).
    """
    filtre = ["trashed = false"]
    if texte:
        filtre.append("fullText contains '" + texte.replace("\\", "").replace("'", "\\'") + "'")
    if classeurs_seulement:
        filtre.append(f"mimeType = '{CLASSEUR}'")
    params = {"q": " and ".join(filtre), "pageSize": max(1, min(int(nombre), 50)), "includeItemsFromAllDrives": "true",
              "supportsAllDrives": "true", "corpora": "allDrives",
              "fields": "files(id,name,mimeType,modifiedTime,webViewLink,owners(displayName))"}
    if not texte:   # Drive refuse orderBy avec une recherche plein texte
        params["orderBy"] = "modifiedTime desc"
    r = appel(f"{DRIVE}?" + q(params), jeton(tool_context))
    return {"fichiers": [{"id": f["id"], "nom": f["name"], "type": f["mimeType"].split(".")[-1], "modifie": f.get("modifiedTime"),
                          "proprietaire": (f.get("owners") or [{}])[0].get("displayName"), "lien": f.get("webViewLink")}
                         for f in r.get("files", [])]}


@outil
def drive_lire(fichier_id: str, tool_context=None) -> dict:
    """Le texte d'un fichier Drive : Google Docs, Slides, fichiers texte et CSV. (Classeurs Google : sheets_lire.)

    Args:
        fichier_id: L'id (donné par drive_chercher) ou le lien du fichier.
    """
    j, fid = jeton(tool_context), id_fichier(fichier_id)
    f = appel(f"{DRIVE}/{fid}?fields=name,mimeType&supportsAllDrives=true", j)
    if f["mimeType"] == CLASSEUR:
        raise Refus(f"« {f['name']} » est un Google Sheets : utiliser sheets_infos puis sheets_lire.")
    if f["mimeType"].startswith("application/vnd.google-apps."):
        texte = appel(f"{DRIVE}/{fid}/export?mimeType=text/plain", j, brut=True)
    elif f["mimeType"].startswith("text/") or f["mimeType"] == "application/json":
        texte = appel(f"{DRIVE}/{fid}?alt=media&supportsAllDrives=true", j, brut=True)
    else:
        raise Refus(f"« {f['name']} » ({f['mimeType']}) : format non lisible en texte par cet outil.")
    return {"nom": f["name"], "texte": texte[:15000], "tronque": len(texte) > 15000}


OUTILS = [qui_suis_je, gmail_chercher, gmail_lire, agenda_evenements, drive_chercher, drive_lire]
