"""Les sources de documents. Chacune sait (1) lister ce qu'elle contient, avec une « version » qui change quand le
contenu change, et (2) donner les octets d'un fichier. La synchro (sync.py) fait le reste pour toutes.

Types : « depot » (fichiers glissés-déposés), « dossier » (n'importe quel dossier du disque : y compris celui de
Google Drive pour ordinateur ou du client OneDrive), « gdrive » (compte Google connecté par OAuth).
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

from parse import INDEXABLE

DATA = os.getenv("DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"))
UPLOADS = os.path.join(DATA, "depots")
STATE = os.path.join(DATA, "etat")
SOURCES_FILE = os.path.join(DATA, "sources.json")
for d in (DATA, UPLOADS, STATE):
    os.makedirs(d, exist_ok=True)


def load_sources() -> list[dict]:
    if not os.path.exists(SOURCES_FILE):
        return [{"id": "depot", "type": "depot", "nom": "Fichiers déposés", "auto": True}]
    return json.load(open(SOURCES_FILE, encoding="utf-8"))


def save_sources(sources: list[dict]) -> None:
    tmp = SOURCES_FILE + ".tmp"
    json.dump(sources, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, SOURCES_FILE)


# --- Fichiers sur le disque (dépôts, dossier local) -----------------------------------------

class LocalFolder:
    def __init__(self, src: dict):
        self.src = src
        self.root = UPLOADS if src["type"] == "depot" else os.path.expanduser(src["chemin"])

    def listing(self) -> dict:
        if not os.path.isdir(self.root):
            raise FileNotFoundError(f"Dossier introuvable : {self.root}")
        out = {}
        for base, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.startswith(".") or os.path.splitext(f)[1].lower() not in INDEXABLE:
                    continue
                p = os.path.join(base, f)
                st = os.stat(p)
                rel = os.path.relpath(p, self.root)
                out[rel] = {"title": f, "link": f"/fichiers/{self.src['id']}/{rel}",
                            "version": f"{st.st_mtime_ns}-{st.st_size}"}
        return out

    def fetch(self, key: str) -> tuple[str, bytes]:
        path = os.path.realpath(os.path.join(self.root, key))
        if not path.startswith(os.path.realpath(self.root) + os.sep):
            raise PermissionError("chemin hors du dossier de la source")
        return os.path.basename(path), open(path, "rb").read()


# --- Google Drive (OAuth du compte de l'utilisateur) -----------------------------------------

SCOPES = ["https://www.googleapis.com/auth/drive.readonly", "openid", "https://www.googleapis.com/auth/userinfo.email"]
CLIENT_FILE = os.getenv("GOOGLE_CLIENT_FILE", os.path.join(DATA, "google_client.json"))
TOKENS_FILE = os.path.join(DATA, "google_tokens.json")  # {email: refresh_token} — à protéger comme un mot de passe
FOLDER = "application/vnd.google-apps.folder"
EXPORT = {  # natifs Google -> format exporté (Drive limite l'export à 10 Mo)
    "application/vnd.google-apps.document": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    "application/vnd.google-apps.presentation": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", ".pptx"),
    "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),  # 1re feuille
}
FIELDS = "id, name, mimeType, modifiedTime, trashed, parents, webViewLink, size"


def google_client() -> dict | None:
    if not os.path.exists(CLIENT_FILE):
        return None
    d = json.load(open(CLIENT_FILE))
    return d.get("web") or d.get("installed")


def google_accounts() -> dict:
    return json.load(open(TOKENS_FILE)) if os.path.exists(TOKENS_FILE) else {}


def save_google_account(email: str, refresh_token: str | None) -> None:
    tokens = google_accounts()
    if refresh_token:
        tokens[email] = refresh_token
    else:
        tokens.pop(email, None)
    fd = os.open(TOKENS_FILE + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)  # lisible par vous seul
    with os.fdopen(fd, "w") as f:
        json.dump(tokens, f)
    os.replace(TOKENS_FILE + ".tmp", TOKENS_FILE)


def drive_service(account: str):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    token, client = google_accounts().get(account), google_client()
    if not token or not client:
        raise PermissionError(f"Compte « {account} » non connecté : reconnectez-le depuis l'interface.")
    creds = Credentials(None, refresh_token=token, client_id=client["client_id"], client_secret=client["client_secret"],
                        token_uri="https://oauth2.googleapis.com/token", scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def plan(f: dict):
    """(mimeType d'export ou None, extension) si le fichier est lisible, sinon None."""
    if f["mimeType"] in EXPORT:
        return EXPORT[f["mimeType"]]
    if f["mimeType"].startswith("application/vnd.google-apps."):
        return None
    ext = os.path.splitext(f["name"])[1].lower()
    return (None, ext) if ext in INDEXABLE and int(f.get("size", 0)) <= 50 * 1024 * 1024 else None


class GoogleDrive:
    """Tout le Drive ou des dossiers. L'état (jeton de page + fichiers suivis) est gardé dans data/etat/<id>.json :
    chaque passe ne lit que les changements (API `changes`) ; une réconciliation complète a lieu une fois par jour."""

    def __init__(self, src: dict):
        self.src = src
        self.path = os.path.join(STATE, f"{src['id']}.json")
        self._drive = None

    @property
    def drive(self):
        if self._drive is None:
            self._drive = drive_service(self.src["compte"])
        return self._drive

    def _state(self) -> dict:
        return json.load(open(self.path)) if os.path.exists(self.path) else {"files": {}}

    def _save(self, st: dict) -> None:
        json.dump(st, open(self.path, "w"))

    def _in_scope(self, f: dict, cache: dict) -> bool:
        if self.src["mode"] == "tout":
            return True
        roots = {d["id"] for d in self.src["dossiers"]}

        def under(fid, depth=0):
            if fid in roots:
                return True
            if depth > 50:
                return False
            if fid not in cache:
                try:
                    cache[fid] = self.drive.files().get(fileId=fid, fields="parents", supportsAllDrives=True).execute().get("parents", [])
                except Exception:
                    cache[fid] = []
            return any(under(p, depth + 1) for p in cache[fid])
        return any(under(p) for p in f.get("parents", []))

    def _full(self) -> dict:
        files, todo = {}, ([None] if self.src["mode"] == "tout" else [d["id"] for d in self.src["dossiers"]])
        while todo:
            parent, token = todo.pop(), None
            q = (f"trashed = false and mimeType != '{FOLDER}'" if parent is None
                 else f"'{parent}' in parents and trashed = false")
            while True:
                r = self.drive.files().list(q=q, pageSize=1000, pageToken=token, fields=f"nextPageToken, files({FIELDS})",
                                            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
                for f in r.get("files", []):
                    if f["mimeType"] == FOLDER:
                        todo.append(f["id"])
                    elif plan(f):
                        files[f["id"]] = {"name": f["name"], "mime": f["mimeType"], "modified": f["modifiedTime"],
                                          "link": f.get("webViewLink", "")}
                token = r.get("nextPageToken")
                if not token:
                    break
        return files

    def listing(self) -> dict:
        st = self._state()
        stale = not st.get("last_full") or datetime.fromisoformat(st["last_full"]) < datetime.now(timezone.utc) - timedelta(days=1)
        scope_changed = st.get("scope") != [self.src["mode"], sorted(d["id"] for d in self.src.get("dossiers", []))]
        full = not st.get("page_token") or stale or scope_changed
        if not full:
            token, cache = st["page_token"], {}
            while token:
                r = self.drive.changes().list(pageToken=token, includeRemoved=True, pageSize=1000, supportsAllDrives=True,
                                              includeItemsFromAllDrives=True,
                                              fields=f"nextPageToken, newStartPageToken, changes(fileId, removed, file({FIELDS}))").execute()
                for c in r.get("changes", []):
                    f = c.get("file") or {}
                    if f.get("mimeType") == FOLDER:
                        full = full or self.src["mode"] == "dossiers"  # dossier déplacé : on réconcilie
                    elif c.get("removed") or f.get("trashed") or not plan(f) or not self._in_scope(f, cache):
                        st["files"].pop(c["fileId"], None)
                    else:
                        st["files"][f["id"]] = {"name": f["name"], "mime": f["mimeType"], "modified": f["modifiedTime"],
                                                "link": f.get("webViewLink", "")}
                token = r.get("nextPageToken")
                if r.get("newStartPageToken"):
                    st["page_token"] = r["newStartPageToken"]
        if full:
            start = self.drive.changes().getStartPageToken(supportsAllDrives=True).execute()["startPageToken"]
            st.update(files=self._full(), page_token=start, last_full=datetime.now(timezone.utc).isoformat(),
                      scope=[self.src["mode"], sorted(d["id"] for d in self.src.get("dossiers", []))])
        self._save(st)
        return {fid: {"title": f["name"], "link": f["link"], "version": f["modified"], "mime": f["mime"]}
                for fid, f in st["files"].items()}

    def fetch(self, key: str) -> tuple[str, bytes]:
        import io
        from googleapiclient.http import MediaIoBaseDownload
        f = self.drive.files().get(fileId=key, fields="name, mimeType, size", supportsAllDrives=True).execute()
        export_mime, ext = plan(f)
        req = (self.drive.files().export_media(fileId=key, mimeType=export_mime) if export_mime
               else self.drive.files().get_media(fileId=key, supportsAllDrives=True))
        buf, done = io.BytesIO(), False
        dl = MediaIoBaseDownload(buf, req, chunksize=8 * 1024 * 1024)
        while not done:
            _, done = dl.next_chunk()
        name = f["name"] if f["name"].lower().endswith(ext) else f["name"] + ext
        return name, buf.getvalue()


def open_source(src: dict):
    return GoogleDrive(src) if src["type"] == "gdrive" else LocalFolder(src)


def new_id(prefix: str) -> str:
    return f"{prefix}{int(time.time() * 1000) % 10**10}"
