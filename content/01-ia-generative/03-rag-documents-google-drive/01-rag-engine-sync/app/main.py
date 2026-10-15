"""Serveur web : API de l'agent (ADK) + API de gestion (/api/*) + la page (/)."""

import os
import posixpath
import secrets

import uvicorn
from fastapi import File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from google.adk.cli.fast_api import get_fast_api_app
from pydantic import BaseModel

import gdrive
import kit

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_UPLOAD = 30 * 1024 * 1024  # Cloud Run refuse les requêtes > 32 Mo

# ADK fournit /apps/{app}/users/{user}/sessions, /run, /run_sse…
app = get_fast_api_app(
    agents_dir=os.path.join(HERE, "agents"),
    # ponytail: sessions en mémoire, d'où 1 seule instance ; base Cloud SQL / Agent Runtime pour monter en charge.
    session_service_uri=os.getenv("SESSION_SERVICE_URI"),
    web=False,
    otel_to_cloud=os.getenv("OTEL_TO_CLOUD", "false") == "true",
    # Derrière « gcloud run services proxy », le navigateur est sur http://localhost:<port> mais l'hôte vu par le
    # service est …run.app : sans cette liste, ADK refuse la création de session (403, vérifié). Sûr : le service
    # reste privé (jeton IAM ajouté par le proxy). Ajoutez votre URL IAP ici si vous l'activez.
    allow_origins=os.getenv("ALLOW_ORIGINS", r"regex:http://(localhost|127\.0\.0\.1)(:\d+)?").split(),
)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


# Redirection OAuth : la page est ouverte par le proxy sur http://localhost:8080 (déclarée dans le client OAuth).
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/google/callback")


@app.get("/api/status")
def status():
    cfg = kit.load_sources()
    return {
        "projet": kit.PROJECT_ID, "region": kit.REGION, "corpus": kit.CORPUS, "bucket": kit.BUCKET,
        "partager_avec": [kit.SA_EMAIL, kit.RAG_AGENT_EMAIL],
        "sources": cfg["drive_folders"],
        "google": [{k: v for k, v in g.items()} for g in cfg["google"]],
        "derniere_synchro": kit.last_sync(),
        "synchro_en_cours": kit.sync_running(),
    }


class Folder(BaseModel):
    dossier: str  # URL ou ID


@app.post("/api/sources")
def add_source(body: Folder):
    try:
        folder_id = kit.parse_folder_id(body.dossier)
        folder = kit.drive_folder(folder_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception:
        raise HTTPException(403, f"Le kit ne voit pas ce dossier. Partagez-le en lecture avec {kit.SA_EMAIL} "
                                 f"et {kit.RAG_AGENT_EMAIL}, puis réessayez.")
    cfg = kit.load_sources()
    if folder_id not in {f["id"] for f in cfg["drive_folders"]}:
        cfg["drive_folders"].append({"id": folder_id, "name": folder["name"]})
        kit.save_sources(cfg)
    return {"ajoute": folder["name"], "synchro": kit.start_sync()}


@app.delete("/api/sources/{folder_id}")
def remove_source(folder_id: str):
    cfg = kit.load_sources()
    cfg["drive_folders"] = [f for f in cfg["drive_folders"] if f["id"] != folder_id]
    kit.save_sources(cfg)
    return {"retire": folder_id, "synchro": kit.start_sync()}


# --- Connexion Google ---------------------------------------------------------------

@app.get("/api/google")
def google_info():
    """Ce dont la page a besoin pour le bouton de connexion et le sélecteur de dossiers."""
    client = gdrive.oauth_client()
    return {"configure": bool(client), "comptes": gdrive.accounts() if client else [],
            "client_id": client["client_id"] if client else None, "picker_key": os.getenv("PICKER_API_KEY", ""),
            "app_id": kit.PROJECT_NUMBER, "push": bool(gdrive.HOOK_URL), "redirect_uri": REDIRECT_URI}


@app.get("/auth/google/start", include_in_schema=False)
def google_start():
    if not gdrive.oauth_client():
        raise HTTPException(400, "Connexion Google pas encore configurée : voir docs/04-bis-connexion-google.md.")
    state = secrets.token_urlsafe(24)
    r = RedirectResponse(gdrive.auth_url(REDIRECT_URI, state))
    r.set_cookie("oauth_state", state, max_age=600, httponly=True, samesite="lax")
    return r


@app.get("/auth/google/callback", include_in_schema=False)
def google_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    if error:
        return RedirectResponse(f"/?erreur={error}")
    if not state or not secrets.compare_digest(state, request.cookies.get("oauth_state", "")):
        raise HTTPException(400, "Requête de connexion invalide (état différent) : recommencez depuis l'interface.")
    try:
        email = gdrive.finish_auth(code, REDIRECT_URI)
    except PermissionError as e:
        return RedirectResponse(f"/?erreur={e}")
    r = RedirectResponse(f"/?connecte={email}")
    r.delete_cookie("oauth_state")
    return r


@app.get("/api/google/jeton")
def google_token(compte: str):
    """Jeton d'accès court pour le sélecteur de dossiers Google (dans le navigateur)."""
    try:
        return {"jeton": gdrive.access_token(compte)}
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.delete("/api/google/comptes/{compte}")
def google_disconnect(compte: str):
    cfg = kit.load_sources()
    for src in [g for g in cfg["google"] if g["compte"] == compte]:
        gdrive.stop_source(kit._bucket, src)
    cfg["google"] = [g for g in cfg["google"] if g["compte"] != compte]
    kit.save_sources(cfg)
    gdrive.remove_account(compte)
    return {"deconnecte": compte, "synchro": kit.start_sync()}


class GoogleSource(BaseModel):
    compte: str
    mode: str  # "tout" ou "dossiers"
    dossiers: list[dict] = []  # [{"id": …, "name": …}] (sélecteur Google)
    auto: bool = True


@app.post("/api/sources/google")
def add_google_source(body: GoogleSource):
    if body.mode not in ("tout", "dossiers") or (body.mode == "dossiers" and not body.dossiers):
        raise HTTPException(400, "Choisissez « tout mon Drive » ou au moins un dossier.")
    if body.compte not in gdrive.accounts() and body.compte != kit.SA_EMAIL:
        raise HTTPException(403, f"Compte « {body.compte} » non connecté.")
    cfg = kit.load_sources()
    src = {"id": gdrive.new_source_id(), "compte": body.compte, "mode": body.mode,
           "dossiers": [{"id": d["id"], "name": d.get("name", d["id"])} for d in body.dossiers], "auto": body.auto}
    cfg["google"].append(src)
    kit.save_sources(cfg)
    return {"ajoute": src, "synchro": kit.start_sync()}


class AutoSync(BaseModel):
    auto: bool


@app.patch("/api/sources/google/{source_id}")
def toggle_google_source(source_id: str, body: AutoSync):
    cfg = kit.load_sources()
    for g in cfg["google"]:
        if g["id"] == source_id:
            g["auto"] = body.auto
    kit.save_sources(cfg)
    return {"source": source_id, "auto": body.auto, "synchro": kit.start_sync()}  # ouvre/ferme le canal push


@app.delete("/api/sources/google/{source_id}")
def remove_google_source(source_id: str):
    cfg = kit.load_sources()
    for src in [g for g in cfg["google"] if g["id"] == source_id]:
        gdrive.stop_source(kit._bucket, src)
    cfg["google"] = [g for g in cfg["google"] if g["id"] != source_id]
    kit.save_sources(cfg)
    return {"retire": source_id, "synchro": kit.start_sync()}


@app.get("/api/documents")
def documents():
    out = []
    for f in kit.list_corpus():
        key = kit.corpus_key(f)
        origin = ("depot" if key.startswith(f"gs://{kit.BUCKET}/{kit.UPLOADS}")
                  else "google" if key.startswith(f"gs://{kit.BUCKET}/{gdrive.MIRROR}")
                  else "drive" if "/" not in key else "autre")
        name = kit.mirror_meta(key).get("titre", f.display_name) if origin == "google" else f.display_name
        out.append({"nom": name, "origine": origin, "cle": key,
                    "lien": kit.public_link(key) if key.startswith("gs://") else f"https://drive.google.com/open?id={key}",
                    "maj": f.update_time.isoformat() if f.update_time else None})
    return sorted(out, key=lambda d: d["nom"].lower())


@app.post("/api/upload")
def upload(files: list[UploadFile] = File(...)):
    saved = []
    for f in files:
        name = posixpath.basename((f.filename or "").replace("\\", "/")).strip()
        if not name or name.startswith("."):
            raise HTTPException(400, f"Nom de fichier invalide : {f.filename!r}")
        data = f.file.read(MAX_UPLOAD + 1)
        if len(data) > MAX_UPLOAD:
            raise HTTPException(413, f"« {name} » dépasse 30 Mo : mettez-le dans le dossier Drive à la place.")
        kit._bucket.blob(kit.UPLOADS + name).upload_from_string(data, content_type=f.content_type)
        saved.append(name)
    return {"deposes": saved, "synchro": kit.start_sync()}


@app.delete("/api/documents")
def delete_upload(cle: str):
    prefix = f"gs://{kit.BUCKET}/{kit.UPLOADS}"
    if not cle.startswith(prefix):  # les fichiers Drive se suppriment dans Drive, pas ici
        raise HTTPException(400, "Seuls les fichiers déposés se suppriment ici ; pour Drive, supprimez-le dans Drive.")
    kit._bucket.blob(cle[len(f"gs://{kit.BUCKET}/"):]).delete()
    return {"supprime": cle, "synchro": kit.start_sync()}


@app.post("/api/sync")
def sync():
    return {"synchro": kit.start_sync()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
