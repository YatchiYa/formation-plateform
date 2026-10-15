"""Le serveur local : http://localhost:8765 — interface, API, connexion Google, chat (Claude, en streaming)."""

import json
import os
import posixpath
import secrets
import threading

import uvicorn
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel

import llm
import sources as S
from embed import Embedder
from store import Store
from sync import POLL_SECONDS, Syncer

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.getenv("PORT", "8765"))
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", f"http://localhost:{PORT}/auth/google/callback")
MAX_UPLOAD = 100 * 1024 * 1024

store = Store(os.path.join(S.DATA, "index.sqlite"))
embedder = Embedder()
syncer = Syncer(store, embedder)
app = FastAPI(title="RAG local", docs_url=None, redoc_url=None)
_flows: dict = {}  # état OAuth en cours -> Flow (PKCE)


def sync_soon(only=None):
    """Lance une passe en arrière-plan (la page suit l'état via /api/status)."""
    threading.Thread(target=syncer.run, kwargs={"only": only}, daemon=True).start()


@app.on_event("startup")
def startup():
    sync_soon()
    syncer.start_background()


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


@app.get("/api/status")
def status():
    counts = {}
    for d in store.documents():
        counts[d["source"]] = counts.get(d["source"], 0) + 1
    return {"modele": llm.MODEL, "effort": llm.EFFORT, "embeddings": embedder.name, "poll_s": POLL_SECONDS,
            "cle_claude": bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")),
            "sources": [{**s, "documents": counts.get(s["id"], 0)} for s in S.load_sources()],
            "derniere_synchro": syncer.last, "synchro_en_cours": syncer.running}


@app.get("/api/documents")
def documents():
    return store.documents()


@app.post("/api/upload")
def upload(files: list[UploadFile] = File(...)):
    saved = []
    for f in files:
        name = posixpath.basename((f.filename or "").replace("\\", "/")).strip()
        if not name or name.startswith("."):
            raise HTTPException(400, f"Nom de fichier invalide : {f.filename!r}")
        if os.path.splitext(name)[1].lower() not in S.INDEXABLE:
            raise HTTPException(400, f"« {name} » : format non pris en charge ({', '.join(sorted(S.INDEXABLE))}).")
        data = f.file.read(MAX_UPLOAD + 1)
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, f"« {name} » dépasse 100 Mo.")
        open(os.path.join(S.UPLOADS, name), "wb").write(data)
        saved.append(name)
    sync_soon(["depot"])
    return {"deposes": saved}


@app.delete("/api/documents/{doc_id:path}")
def delete_document(doc_id: str):
    source, _, key = doc_id.partition(":")
    if source != "depot":
        raise HTTPException(400, "Seuls les fichiers déposés se suppriment ici (les autres : dans leur source).")
    path = os.path.realpath(os.path.join(S.UPLOADS, key))
    if not path.startswith(os.path.realpath(S.UPLOADS) + os.sep) or not os.path.exists(path):
        raise HTTPException(404, "Fichier introuvable.")
    os.remove(path)
    sync_soon(["depot"])
    return {"supprime": doc_id}


@app.get("/fichiers/{source_id}/{rel:path}", include_in_schema=False)
def serve_file(source_id: str, rel: str):
    src = next((s for s in S.load_sources() if s["id"] == source_id and s["type"] != "gdrive"), None)
    if not src:
        raise HTTPException(404)
    try:
        name, _ = S.LocalFolder(src).fetch(rel)  # vérifie que le chemin reste dans le dossier de la source
    except (PermissionError, FileNotFoundError):
        raise HTTPException(404)
    return FileResponse(os.path.join(S.LocalFolder(src).root, rel), filename=name)


# --- Sources ----------------------------------------------------------------------

class LocalSource(BaseModel):
    chemin: str
    auto: bool = True


@app.post("/api/sources/dossier")
def add_folder(body: LocalSource):
    path = os.path.realpath(os.path.expanduser(body.chemin.strip()))
    if not os.path.isdir(path):
        raise HTTPException(400, f"Dossier introuvable : {path}")
    srcs = S.load_sources()
    src = {"id": S.new_id("d"), "type": "dossier", "nom": f"Dossier {os.path.basename(path) or path}", "chemin": path,
           "auto": body.auto}
    S.save_sources(srcs + [src])
    sync_soon([src["id"]])
    return {"ajoute": src}


class GoogleSource(BaseModel):
    compte: str
    mode: str  # « tout » ou « dossiers »
    dossiers: list[dict] = []
    auto: bool = True


@app.post("/api/sources/google")
def add_google(body: GoogleSource):
    if body.compte not in S.google_accounts():
        raise HTTPException(403, f"Compte « {body.compte} » non connecté.")
    if body.mode not in ("tout", "dossiers") or (body.mode == "dossiers" and not body.dossiers):
        raise HTTPException(400, "Choisissez « tout mon Drive » ou au moins un dossier.")
    what = "tout le Drive" if body.mode == "tout" else ", ".join(d["name"] for d in body.dossiers)
    src = {"id": S.new_id("g"), "type": "gdrive", "nom": f"Google Drive {body.compte} ({what})", "compte": body.compte,
           "mode": body.mode, "dossiers": [{"id": d["id"], "name": d["name"]} for d in body.dossiers], "auto": body.auto}
    S.save_sources(S.load_sources() + [src])
    sync_soon([src["id"]])
    return {"ajoute": src}


class Auto(BaseModel):
    auto: bool


@app.patch("/api/sources/{source_id}")
def toggle(source_id: str, body: Auto):
    srcs = S.load_sources()
    for s in srcs:
        if s["id"] == source_id:
            s["auto"] = body.auto
    S.save_sources(srcs)
    return {"source": source_id, "auto": body.auto}


@app.delete("/api/sources/{source_id}")
def remove_source(source_id: str):
    if source_id == "depot":
        raise HTTPException(400, "La source « Fichiers déposés » est permanente.")
    S.save_sources([s for s in S.load_sources() if s["id"] != source_id])
    n = store.delete_source(source_id)
    state = os.path.join(S.STATE, f"{source_id}.json")
    if os.path.exists(state):
        os.remove(state)
    return {"retire": source_id, "documents_retires": n}


@app.post("/api/sync")
def sync_now():
    if syncer.running:
        return {"synchro": "en_cours"}
    sync_soon()
    return {"synchro": "lancee"}


# --- Connexion Google ---------------------------------------------------------------

@app.get("/api/google")
def google_info():
    return {"configure": bool(S.google_client()), "comptes": sorted(S.google_accounts()), "redirect_uri": REDIRECT_URI}


@app.get("/auth/google/start", include_in_schema=False)
def google_start():
    from google_auth_oauthlib.flow import Flow
    client = S.google_client()
    if not client:
        raise HTTPException(400, "Connexion Google pas configurée : placez le client OAuth dans data/google_client.json (docs/03).")
    flow = Flow.from_client_config({"web": client}, scopes=S.SCOPES, redirect_uri=REDIRECT_URI)
    url, state = flow.authorization_url(access_type="offline", prompt="consent select_account",
                                        include_granted_scopes="true")
    _flows[state] = flow
    return RedirectResponse(url)


@app.get("/auth/google/callback", include_in_schema=False)
def google_callback(state: str = "", code: str = "", error: str = ""):
    flow = _flows.pop(state, None)
    if error or not flow:
        return RedirectResponse(f"/?erreur={error or 'connexion expirée, recommencez'}")
    os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")  # Google renvoie les portées dans un autre ordre
    flow.fetch_token(code=code)
    creds = flow.credentials
    if S.SCOPES[0] not in (creds.granted_scopes or creds.scopes or []):
        return RedirectResponse("/?erreur=accès Drive non accordé (case décochée)")
    from google.auth.transport.requests import AuthorizedSession
    email = AuthorizedSession(creds).get("https://openidconnect.googleapis.com/v1/userinfo").json()["email"]
    S.save_google_account(email, creds.refresh_token)
    return RedirectResponse(f"/?connecte={email}")


@app.get("/api/google/dossiers")
def google_folders(compte: str, parent: str = "root"):
    """Pour le sélecteur de dossiers de l'interface : les sous-dossiers de `parent` (« partages » = partagés avec moi)."""
    try:
        drive = S.drive_service(compte)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    q = (f"sharedWithMe = true and mimeType = '{S.FOLDER}' and trashed = false" if parent == "partages"
         else f"'{parent}' in parents and mimeType = '{S.FOLDER}' and trashed = false")
    r = drive.files().list(q=q, pageSize=200, orderBy="name", fields="files(id, name)", supportsAllDrives=True,
                           includeItemsFromAllDrives=True).execute()
    return r.get("files", [])


@app.delete("/api/google/comptes/{compte}")
def google_disconnect(compte: str):
    for s in [s for s in S.load_sources() if s.get("compte") == compte]:
        remove_source(s["id"])
    S.save_google_account(compte, None)
    return {"deconnecte": compte}


@app.get("/api/recherche")
def search(q: str, k: int = 8):
    """Les extraits que Claude recevrait pour cette question (diagnostic, sans appeler Claude)."""
    return embedder.rerank(q, store.search(q, embedder.query(q), k=20), k=k)


# --- Chat ------------------------------------------------------------------------------

class Ask(BaseModel):
    question: str
    historique: list[dict] = []


@app.post("/api/chat")
def chat(body: Ask):
    """Flux SSE : d'abord les extraits trouvés, puis le texte de la réponse au fil de l'eau."""
    hits = embedder.rerank(body.question, store.search(body.question, embedder.query(body.question), k=20), k=8)

    def events():
        yield f"data: {json.dumps({'type': 'sources', 'extraits': hits}, ensure_ascii=False)}\n\n"
        try:
            for delta in llm.answer_stream(body.question, body.historique[-10:], hits):
                yield f"data: {json.dumps({'type': 'texte', 'delta': delta}, ensure_ascii=False)}\n\n"
        except llm.anthropic.AuthenticationError:
            yield f"data: {json.dumps({'type': 'erreur', 'message': 'Clé Claude absente ou invalide : renseignez ANTHROPIC_API_KEY dans .env, puis relancez.'})}\n\n"
        except TypeError as e:
            msg = ("Clé Claude absente : renseignez ANTHROPIC_API_KEY dans .env, puis relancez."
                   if "authentication" in str(e).lower() else str(e))
            yield f"data: {json.dumps({'type': 'erreur', 'message': msg}, ensure_ascii=False)}\n\n"
        except llm.anthropic.APIError as e:
            yield f"data: {json.dumps({'type': 'erreur', 'message': f'Claude : {e}'}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'fin'})}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT)  # local uniquement : rien d'exposé sur le réseau
