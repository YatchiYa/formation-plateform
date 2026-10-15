"""Source « Google Drive connecté » : le compte de l'utilisateur (OAuth), tout son Drive ou des dossiers, recopié dans
un miroir GCS (gs://BUCKET/mirror/<source>/…) que RAG Engine indexe. Changements lus par l'API `changes` (seulement ce
qui a bougé), réveil par notifications push (`changes.watch`), réconciliation complète une fois par jour.

Comptes et jetons : secret `<prefix>-google-tokens` = {"email": "refresh_token"}. Le compte de service du kit peut
lui-même servir de « compte connecté » (valeur SELF) : mêmes appels Drive, utile pour tester sans écran OAuth.
"""

import base64
import io
import json
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta, timezone

import google.auth
from google.auth.transport.requests import AuthorizedSession, Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

PROJECT_ID = os.environ.get("PROJECT_ID", "")
PREFIX = os.environ.get("PREFIX", "rag-kit")
SA_EMAIL = os.environ.get("SA_EMAIL", "")
HOOK_URL = os.environ.get("HOOK_URL", "")  # vide = pas de notifications push (passes planifiées seulement)
SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "openid", "https://www.googleapis.com/auth/userinfo.email"]
TOKENS_SECRET = f"{PREFIX}-google-tokens"
CLIENT_SECRET = f"{PREFIX}-oauth-client"
SELF = "__compte_du_kit__"
MIRROR = "mirror/"
FOLDER = "application/vnd.google-apps.folder"
MAX_BYTES = 50 * 1024 * 1024
CHANNEL_DAYS = 7  # durée max d'un canal changes.watch
# Google natifs -> format exporté (Drive limite l'export à 10 Mo)
EXPORT = {
    "application/vnd.google-apps.document": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    "application/vnd.google-apps.spreadsheet": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.drawing": ("application/pdf", ".pdf"),
}
INDEXABLE = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html", ".htm", ".json"}


# --- Secrets (API REST : pas de dépendance de plus) ----------------------------------

def _sm(method: str, path: str, body: dict | None = None):
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    r = AuthorizedSession(creds).request(method, f"https://secretmanager.googleapis.com/v1/projects/{PROJECT_ID}/{path}",
                                         json=body)
    if r.status_code == 404 or (r.status_code == 400 and "FAILED_PRECONDITION" in r.text):
        return None  # secret sans version (encore jamais rempli)
    r.raise_for_status()
    return r.json()


def _read_secret(name: str) -> dict:
    r = _sm("GET", f"secrets/{name}/versions/latest:access")
    return json.loads(base64.b64decode(r["payload"]["data"])) if r else {}


def _write_secret(name: str, data: dict) -> None:
    old = _sm("GET", f"secrets/{name}/versions?filter=state:ENABLED") or {}
    _sm("POST", f"secrets/{name}:addVersion",
        {"payload": {"data": base64.b64encode(json.dumps(data).encode()).decode()}})
    for v in old.get("versions", []):  # une seule version active : les anciens jetons sont détruits
        _sm("POST", f"{v['name'].split('/', 2)[2]}:destroy", {})


def oauth_client() -> dict | None:
    """Le client OAuth « Application Web » créé dans la console (fichier JSON téléchargé), ou None."""
    data = _read_secret(CLIENT_SECRET)
    return data.get("web") or data.get("installed") or None


def accounts() -> list[str]:
    return sorted(_read_secret(TOKENS_SECRET))


def save_account(email: str, refresh_token: str) -> None:
    tokens = _read_secret(TOKENS_SECRET)
    tokens[email] = refresh_token
    _write_secret(TOKENS_SECRET, tokens)


def remove_account(email: str) -> None:
    tokens = _read_secret(TOKENS_SECRET)
    tokens.pop(email, None)
    _write_secret(TOKENS_SECRET, tokens)


def credentials(account: str):
    """Identifiants Drive du compte : jeton OAuth de l'utilisateur, ou le compte de service du kit lui-même."""
    if account in (SELF, SA_EMAIL):
        creds, _ = google.auth.default(scopes=SCOPES[:1])
        return creds
    token = _read_secret(TOKENS_SECRET).get(account)
    client = oauth_client()
    if not token or not client:
        raise PermissionError(f"Compte « {account} » non connecté : reconnectez-le depuis l'interface.")
    return Credentials(None, refresh_token=token, client_id=client["client_id"],
                       client_secret=client["client_secret"], token_uri="https://oauth2.googleapis.com/token",
                       scopes=SCOPES)


def access_token(account: str) -> str:
    """Jeton d'accès court (1 h) pour le sélecteur Google dans le navigateur."""
    creds = credentials(account)
    creds.refresh(Request())
    return creds.token


# --- Connexion OAuth (code d'autorisation) -------------------------------------------

def auth_url(redirect_uri: str, state: str) -> str:
    c = oauth_client()
    q = {"client_id": c["client_id"], "redirect_uri": redirect_uri, "response_type": "code",
         "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent select_account",
         "include_granted_scopes": "true", "state": state}
    from urllib.parse import urlencode
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(q)


def finish_auth(code: str, redirect_uri: str) -> str:
    """Échange le code contre les jetons, range le jeton de rafraîchissement, renvoie l'e-mail du compte."""
    import httpx
    c = oauth_client()
    r = httpx.post("https://oauth2.googleapis.com/token", data={
        "code": code, "client_id": c["client_id"], "client_secret": c["client_secret"],
        "redirect_uri": redirect_uri, "grant_type": "authorization_code"}, timeout=30)
    r.raise_for_status()
    tok = r.json()
    if "refresh_token" not in tok:
        raise PermissionError("Google n'a pas renvoyé de jeton de rafraîchissement : réessayez la connexion.")
    granted = set(tok.get("scope", "").split())
    if SCOPES[0] not in granted:
        raise PermissionError("L'accès en lecture à Google Drive n'a pas été accordé (case décochée ?).")
    email = httpx.get("https://openidconnect.googleapis.com/v1/userinfo",
                      headers={"Authorization": f"Bearer {tok['access_token']}"}, timeout=30).json()["email"]
    save_account(email, tok["refresh_token"])
    return email


# --- État d'une source (dans le bucket) -------------------------------------------------

def _rm(bucket, name: str) -> None:
    blob = bucket.blob(name)
    if blob.exists():
        blob.delete()


def _state_blob(bucket, source_id: str):
    return bucket.blob(f"state/{source_id}.json")


def load_state(bucket, source_id: str) -> dict:
    b = _state_blob(bucket, source_id)
    return json.loads(b.download_as_text()) if b.exists() else {"files": {}}


def save_state(bucket, source_id: str, state: dict) -> None:
    _state_blob(bucket, source_id).upload_from_string(json.dumps(state, ensure_ascii=False), content_type="application/json")


# --- Synchro d'une source ----------------------------------------------------------------

def _plan(f: dict):
    """(mimeType d'export ou None, extension) si le fichier est indexable, sinon None."""
    mime = f["mimeType"]
    if mime in EXPORT:
        return EXPORT[mime]
    if mime.startswith("application/vnd.google-apps."):
        return None  # formulaires, raccourcis, sites… : rien à lire
    ext = os.path.splitext(f["name"])[1].lower()
    if ext not in INDEXABLE or int(f.get("size", 0)) > MAX_BYTES:
        return None
    return (None, ext)


def _object_name(source_id: str, f: dict, ext: str) -> str:
    base = re.sub(r"[^\w\-. ]+", "_", os.path.splitext(f["name"])[0]).strip()[:120] or "document"
    return f"{MIRROR}{source_id}/{f['id']}/{base}{ext}"


FIELDS = "id, name, mimeType, modifiedTime, trashed, parents, webViewLink, size"


def _list_folder_tree(drive, folder_ids: list[str]) -> dict:
    files, todo = {}, list(folder_ids)
    while todo:
        parent, token = todo.pop(), None
        while True:
            r = drive.files().list(q=f"'{parent}' in parents and trashed = false", pageSize=1000, pageToken=token,
                                   fields=f"nextPageToken, files({FIELDS})", supportsAllDrives=True,
                                   includeItemsFromAllDrives=True).execute()
            for f in r.get("files", []):
                if f["mimeType"] == FOLDER:
                    todo.append(f["id"])
                else:
                    files[f["id"]] = f
            token = r.get("nextPageToken")
            if not token:
                break
    return files


def _list_all(drive) -> dict:
    files, token = {}, None
    while True:  # « Tout mon Drive » : mes fichiers et ceux partagés avec moi
        r = drive.files().list(q=f"trashed = false and mimeType != '{FOLDER}'", pageSize=1000, pageToken=token,
                               fields=f"nextPageToken, files({FIELDS})").execute()
        files.update({f["id"]: f for f in r.get("files", [])})
        token = r.get("nextPageToken")
        if not token:
            return files


def _download(drive, f: dict, export_mime: str | None) -> bytes:
    req = (drive.files().export_media(fileId=f["id"], mimeType=export_mime) if export_mime
           else drive.files().get_media(fileId=f["id"], supportsAllDrives=True))
    buf = io.BytesIO()
    dl = MediaIoBaseDownload(buf, req, chunksize=8 * 1024 * 1024)
    done = False
    while not done:
        _, done = dl.next_chunk()
    return buf.getvalue()


class _Scope:
    """Le fichier est-il sous un des dossiers choisis ? (remonte les parents, avec cache)"""

    def __init__(self, drive, folder_ids):
        self.drive, self.roots, self.cache = drive, set(folder_ids), {}

    def __call__(self, f: dict) -> bool:
        return any(self._under(p, 0) for p in f.get("parents", []))

    def _under(self, fid: str, depth: int) -> bool:
        if fid in self.roots:
            return True
        if depth > 50:
            return False
        if fid not in self.cache:
            try:
                self.cache[fid] = self.drive.files().get(fileId=fid, fields="parents",
                                                         supportsAllDrives=True).execute().get("parents", [])
            except HttpError:
                self.cache[fid] = []  # dossier invisible : hors périmètre
        return any(self._under(p, depth + 1) for p in self.cache[fid])


class _Lock:
    """Une seule passe à la fois par source (sinon deux canaux push, vérifié) : objet GCS créé « seulement s'il
    n'existe pas ». On attend l'autre passe ; un verrou de plus de 20 min (passe tuée) est repris."""

    def __init__(self, bucket, source_id):
        self.blob = bucket.blob(f"locks/{source_id}")

    def __enter__(self):
        from google.api_core.exceptions import PreconditionFailed
        for _ in range(120):  # 10 min au plus
            try:
                self.blob.upload_from_string("", if_generation_match=0)
                return self
            except PreconditionFailed:
                self.blob.reload()
                if self.blob.updated and self.blob.updated < datetime.now(timezone.utc) - timedelta(minutes=20):
                    self.blob.delete()
                time.sleep(5)
        raise TimeoutError("une autre passe garde cette source depuis 10 min")

    def __exit__(self, *exc):
        try:
            self.blob.delete()
        except Exception:
            pass


def sync_source(bucket, src: dict, report: dict) -> None:
    """Met le miroir de la source à jour. `src` = {id, compte, mode: tout|dossiers, dossiers: [{id,name}], auto}."""
    with _Lock(bucket, src["id"]):
        _sync_source(bucket, src, report)


def _sync_source(bucket, src: dict, report: dict) -> None:
    state = load_state(bucket, src["id"])
    drive = build("drive", "v3", credentials=credentials(src["compte"]), cache_discovery=False)
    folders = [d["id"] for d in src.get("dossiers", [])]
    in_scope = (lambda f: True) if src["mode"] == "tout" else _Scope(drive, folders)
    stats = {"source": f"Google Drive « {src['compte']} » ({'tout le Drive' if src['mode'] == 'tout' else ', '.join(d['name'] for d in src['dossiers'])})",
             "importes": 0, "inchanges": 0, "echecs": 0, "ignores": 0, "retires": 0}

    def drop(fid):
        old = state["files"].pop(fid, None)
        if old:
            _rm(bucket, old["object"])
            stats["retires"] += 1

    def mirror(f):
        plan = _plan(f)
        if not plan:
            drop(f["id"])
            stats["ignores"] += 1
            return
        old = state["files"].get(f["id"])
        if old and old["modified"] == f["modifiedTime"]:
            stats["inchanges"] += 1
            return
        obj = _object_name(src["id"], f, plan[1])
        try:
            data = _download(drive, f, plan[0])
        except HttpError as e:  # export > 10 Mo, fichier protégé…
            stats["echecs"] += 1
            report["erreurs"].append(f"« {f['name']} » non récupéré : {str(e)[:150]}")
            return
        blob = bucket.blob(obj)
        blob.metadata = {"drive_id": f["id"], "lien": f.get("webViewLink", ""), "titre": f["name"]}
        blob.upload_from_string(data)
        if old and old["object"] != obj:  # renommé : l'ancien objet part
            _rm(bucket, old["object"])
        state["files"][f["id"]] = {"name": f["name"], "modified": f["modifiedTime"], "object": obj}
        stats["importes"] += 1

    last_full = state.get("last_full")
    full = (not state.get("page_token") or not last_full
            or datetime.fromisoformat(last_full) < datetime.now(timezone.utc) - timedelta(days=1)
            or state.get("mode") != src["mode"] or state.get("dossiers") != folders)
    if not full:  # incrémental : seulement ce qui a bougé depuis la dernière passe
        token, changes, new_token = state["page_token"], [], None
        while token:
            r = drive.changes().list(pageToken=token, includeRemoved=True, pageSize=1000, supportsAllDrives=True,
                                     includeItemsFromAllDrives=True,
                                     fields=f"nextPageToken, newStartPageToken, changes(fileId, removed, file({FIELDS}))").execute()
            changes += r.get("changes", [])
            token = r.get("nextPageToken")
            new_token = r.get("newStartPageToken") or new_token
        for c in changes:
            f = c.get("file") or {}
            if f.get("mimeType") == FOLDER:
                full = full or src["mode"] == "dossiers"  # un dossier déplacé : on réconcilie tout
                continue
            if c.get("removed") or f.get("trashed") or not in_scope(f):
                drop(c["fileId"])
            else:
                mirror(f)
        if new_token:
            state["page_token"] = new_token
    if full:  # réconciliation complète (1re passe, changement de périmètre, une fois par jour)
        start = drive.changes().getStartPageToken(supportsAllDrives=True).execute()["startPageToken"]
        wanted = _list_all(drive) if src["mode"] == "tout" else _list_folder_tree(drive, folders)
        for fid in list(state["files"]):
            if fid not in wanted:
                drop(fid)
        for i, f in enumerate(wanted.values()):
            mirror(f)
            if i % 50 == 49:
                save_state(bucket, src["id"], state)  # reprise possible si la passe est interrompue
        state.update(page_token=start, last_full=datetime.now(timezone.utc).isoformat(), mode=src["mode"],
                     dossiers=folders)
    _channel(drive, src, state)
    save_state(bucket, src["id"], state)
    stats["suivis"] = len(state["files"])
    report["sources"].append(stats)


# --- Notifications push --------------------------------------------------------------------

def _channel(drive, src: dict, state: dict) -> None:
    """Garde un canal changes.watch ouvert si la source est en auto (renouvelé à moins de 24 h de l'expiration)."""
    ch = state.get("channel")
    want = bool(src.get("auto") and HOOK_URL)
    if ch and (not want or ch["expiration"] / 1000 - time.time() < 86400):
        try:
            drive.channels().stop(body={"id": ch["id"], "resourceId": ch["resourceId"]}).execute()
        except HttpError:
            pass  # déjà expiré
        state.pop("channel")
        ch = None
    if want and not ch:
        token = secrets.token_urlsafe(24)
        w = drive.changes().watch(pageToken=state["page_token"], supportsAllDrives=True, includeItemsFromAllDrives=True,
                                  body={"id": str(uuid.uuid4()), "type": "web_hook", "address": HOOK_URL,
                                        "token": token,
                                        "expiration": int((time.time() + CHANNEL_DAYS * 86400) * 1000)}).execute()
        state["channel"] = {"id": w["id"], "resourceId": w["resourceId"], "expiration": int(w["expiration"]),
                            "token": token}


def stop_source(bucket, src: dict) -> None:
    """Source retirée : ferme son canal, efface son état et son miroir."""
    state = load_state(bucket, src["id"])
    if state.get("channel"):
        try:
            drive = build("drive", "v3", credentials=credentials(src["compte"]), cache_discovery=False)
            drive.channels().stop(body={"id": state["channel"]["id"],
                                        "resourceId": state["channel"]["resourceId"]}).execute()
        except Exception:
            pass
    for b in bucket.list_blobs(prefix=f"{MIRROR}{src['id']}/"):
        b.delete()
    _rm(bucket, f"state/{src['id']}.json")


def find_channel(bucket, channel_id: str, token: str) -> str | None:
    """Pour le webhook : l'ID de la source dont le canal correspond (jeton vérifié), sinon None."""
    for b in bucket.list_blobs(prefix="state/"):
        ch = json.loads(b.download_as_text()).get("channel") or {}
        if ch.get("id") == channel_id and secrets.compare_digest(ch.get("token", ""), token or ""):
            return b.name[len("state/"):-len(".json")]
    return None


def new_source_id() -> str:
    return "g" + uuid.uuid4().hex[:10]
