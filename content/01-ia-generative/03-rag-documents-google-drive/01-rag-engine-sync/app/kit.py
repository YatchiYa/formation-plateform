"""Tout ce que le service web et le job de synchro partagent : sources, synchro, recherche.

Variables d'environnement (posées par Terraform ou deployer_shell.sh) :
  PROJECT_ID, PROJECT_NUMBER, REGION, BUCKET, CORPUS (nom complet projects/…/ragCorpora/…),
  LAYOUT_PARSER (nom complet du processeur Document AI, vide = parsing simple),
  SYNC_JOB (nom du job Cloud Run, vide = synchro dans le processus, pour le poste local), SA_EMAIL.
"""

import json
import logging
import os
import re
import time
import warnings
from datetime import datetime, timezone

warnings.filterwarnings("ignore", module="vertexai")  # « vertexai.rag est déprécié » : imposé par ADK 2.10
for _noisy in ("googleapiclient.http", "google_auth_httplib2"):  # « httplib2 … per-request timeout » à chaque appel
    logging.getLogger(_noisy).setLevel(logging.ERROR)

import google.auth
import vertexai

import gdrive
from google.api_core.exceptions import FailedPrecondition, NotFound
from google.auth.transport.requests import AuthorizedSession
from google.cloud import storage
from googleapiclient.discovery import build
from vertexai import rag

PROJECT_ID = os.environ.get("PROJECT_ID", "")
PROJECT_NUMBER = os.environ.get("PROJECT_NUMBER", "")
REGION = os.environ.get("REGION", "europe-west4")
BUCKET = os.environ.get("BUCKET", "")
CORPUS = os.environ.get("CORPUS", "")
LAYOUT_PARSER = os.environ.get("LAYOUT_PARSER", "")
SYNC_JOB = os.environ.get("SYNC_JOB", "")
SA_EMAIL = os.environ.get("SA_EMAIL", "")
TRIGGER = os.environ.get("TRIGGER", "manuel")  # « auto » : passe planifiée ou notification push
RAG_AGENT_EMAIL = f"service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com"

UPLOADS = "uploads/"  # préfixe des fichiers déposés dans l'interface
CONFIG_OBJ = "config.json"  # {"drive_folders": [{"id": "...", "name": "..."}]}
LAST_SYNC_OBJ = "sync/last.json"
FOLDER_MIME = "application/vnd.google-apps.folder"

vertexai.init(project=PROJECT_ID, location=REGION)
_bucket = storage.Client(project=PROJECT_ID).bucket(BUCKET) if BUCKET else None


# --- Sources ------------------------------------------------------------------

def parse_folder_id(text: str) -> str:
    """URL de dossier Drive (…/folders/ID, …?id=ID) ou ID brut -> ID."""
    text = text.strip()
    m = re.search(r"/folders/([\w-]+)", text) or re.search(r"[?&]id=([\w-]+)", text)
    folder_id = m.group(1) if m else text
    if not re.fullmatch(r"[\w-]{10,}", folder_id):
        raise ValueError(f"Ce n'est ni une URL de dossier Drive ni un ID : {text!r}")
    return folder_id


def load_sources() -> dict:
    blob = _bucket.blob(CONFIG_OBJ)
    cfg = json.loads(blob.download_as_text()) if blob.exists() else {}
    return {"drive_folders": cfg.get("drive_folders", []), "google": cfg.get("google", [])}


def save_sources(cfg: dict) -> None:
    _bucket.blob(CONFIG_OBJ).upload_from_string(json.dumps(cfg, ensure_ascii=False, indent=2),
                                                content_type="application/json")


# --- Drive (vu par le compte de service du kit) -----------------------------------

def _drive():
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def drive_folder(folder_id: str) -> dict:
    """Nom du dossier. Lève une erreur 404 si le compte du kit n'y a pas accès (dossier non partagé)."""
    f = _drive().files().get(fileId=folder_id, fields="id,name,mimeType", supportsAllDrives=True).execute()
    if f["mimeType"] != FOLDER_MIME:
        raise ValueError(f"« {f['name']} » est un fichier, pas un dossier.")
    return f


def list_drive_files(folder_id: str) -> dict:
    """Tous les fichiers (hors dossiers, hors corbeille) sous le dossier, sous-dossiers compris.
    {id: {"name": …, "modified": datetime}}."""
    # ponytail: listing complet à chaque passe, OK jusqu'à quelques milliers de fichiers ; au-delà, API changes.
    drive, files, todo = _drive(), {}, [folder_id]
    while todo:
        parent, token = todo.pop(), None
        while True:
            r = drive.files().list(q=f"'{parent}' in parents and trashed = false", pageSize=1000, pageToken=token,
                                   fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                                   supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            for f in r.get("files", []):
                if f["mimeType"] == FOLDER_MIME:
                    todo.append(f["id"])
                else:
                    files[f["id"]] = {"name": f["name"],
                                      "modified": datetime.fromisoformat(f["modifiedTime"].replace("Z", "+00:00"))}
            token = r.get("nextPageToken")
            if not token:
                break
    return files


# --- Corpus -------------------------------------------------------------------

def corpus_key(rag_file) -> str:
    """Clé d'un fichier du corpus : ID Drive, ou URI gs://."""
    if rag_file.google_drive_source and rag_file.google_drive_source.resource_ids:
        return rag_file.google_drive_source.resource_ids[0].resource_id
    if rag_file.gcs_source and rag_file.gcs_source.uris:
        return rag_file.gcs_source.uris[0]
    return rag_file.name  # fichier envoyé autrement (upload direct) : jamais souhaité -> supprimé


def list_corpus() -> list:
    return list(rag.list_files(corpus_name=CORPUS, page_size=1000))


def to_delete(present: dict, desired: set) -> list:
    """present = {clé: nom de ressource RAG}. Renvoie les noms des fichiers à retirer du corpus."""
    return sorted(name for key, name in present.items() if key not in desired)


def drive_to_import(drive_files: dict, indexed_at: dict) -> list:
    """IDs Drive à (ré)importer : absents du corpus, ou modifiés dans Drive après leur dernière indexation.
    RAG Engine, lui, réimporte TOUT fichier Drive à chaque import, même inchangé (vérifié) : on filtre ici.
    ponytail: un fichier modifié PENDANT son import peut attendre sa prochaine modification ; un type non supporté
    (image…) est retenté à chaque passe (compté en échec) — filtrer par mimeType si ça devient gênant."""
    return sorted(i for i, f in drive_files.items() if i not in indexed_at or f["modified"] > indexed_at[i])


def _import(paths: list, sink: str):
    kwargs = {"layout_parser": rag.LayoutParserConfig(processor_name=LAYOUT_PARSER)} if LAYOUT_PARSER else {}
    # Même découpage et même parsing à chaque passe : sinon RAG Engine réindexerait tout.
    return rag.import_files(
        corpus_name=CORPUS, paths=paths, import_result_sink=sink, timeout=3600,
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)),
        **kwargs)


class Busy(Exception):
    """Un autre import tourne déjà sur le corpus (RAG Engine n'en accepte qu'un, vérifié)."""


def _import_or_busy(paths: list, sink: str):
    try:
        return _import(paths, sink)
    except FailedPrecondition as e:
        raise Busy(e.message) from e
    except RuntimeError as e:  # le SDK enveloppe l'erreur dans un RuntimeError
        if "other operations running" in str(e):
            raise Busy(str(e)) from e
        raise


def run_sync() -> dict:
    """Une passe de synchro, idempotente. Écrit et renvoie le rapport."""
    started = time.time()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = {"debut": stamp, "statut": "ok", "sources": [], "supprimes": 0, "erreurs": []}

    # 0. Comptes Google connectés : mise à jour du miroir (gs://BUCKET/mirror/), voir gdrive.py.
    cfg = load_sources()
    google_report = {"sources": [], "erreurs": report["erreurs"]}
    for src in cfg.get("google", []):
        if TRIGGER == "auto" and not src.get("auto"):
            continue  # synchro auto désactivée pour cette source : seulement à la demande
        try:
            gdrive.sync_source(_bucket, src, google_report)
        except Exception as e:  # source en panne : son miroir reste tel quel, donc rien n'est retiré de l'index
            report["erreurs"].append(f"Google Drive « {src['compte']} » : {type(e).__name__} : {str(e)[:200]}")

    # 1-2. Souhaité : fichiers des dossiers partagés + fichiers déposés + miroir.
    desired, drive, block_deletes = set(), {}, False
    folders = cfg["drive_folders"]
    for folder in folders:
        try:
            # D'abord le dossier lui-même : sans partage, files.get lève une 404, alors que files.list
            # renverrait une liste VIDE sans erreur (et la synchro supprimerait tout).
            name = drive_folder(folder["id"])["name"]
            if folder.get("name") != name:  # ajouté par Terraform (nom inconnu) ou renommé dans Drive
                folder["name"] = name
                save_sources({**cfg, "drive_folders": folders})
            drive[folder["id"]] = list_drive_files(folder["id"])
            desired |= set(drive[folder["id"]])
        except Exception as e:  # dossier plus partagé, supprimé…
            why = (f"introuvable : plus partagé avec {SA_EMAIL}, ou supprimé" if "404" in str(e) else str(e)[:200])
            report["erreurs"].append(f"Drive « {folder.get('name', folder['id'])} » illisible ({why}). "
                                     "Rien n'est retiré de l'index tant que ce n'est pas réglé.")
            block_deletes = True
    uploads = {f"gs://{BUCKET}/{b.name}" for b in _bucket.list_blobs(prefix=UPLOADS) if not b.name.endswith("/")}
    mirrored = {f"gs://{BUCKET}/{b.name}" for b in _bucket.list_blobs(prefix=gdrive.MIRROR)}
    desired |= uploads | mirrored

    try:
        # 3-4. Supprimer ce qui n'est plus souhaité. Si un dossier est illisible, on ne supprime rien ce tour-ci :
        # une panne de partage ne doit pas vider le corpus.
        corpus = list_corpus()
        present = {corpus_key(f): f.name for f in corpus}
        for name in ([] if block_deletes else to_delete(present, desired)):
            try:
                rag.delete_file(name=name, corpus_name=CORPUS)
            except (FailedPrecondition, RuntimeError) as e:
                if "other operations running" not in str(e):
                    raise
                raise Busy(str(e)) from e
            report["supprimes"] += 1

        # 5. Drive : seulement le nouveau et le modifié, par lots.
        indexed_at = {corpus_key(f): f.update_time for f in corpus if f.update_time}
        for folder in folders:
            if folder["id"] not in drive:
                continue
            files = drive[folder["id"]]
            todo = drive_to_import(files, indexed_at)
            src = {"source": f"Drive « {folder['name']} »", "importes": 0,
                   "inchanges": len(files) - len(todo), "echecs": 0}
            unreadable = []
            for n in range(0, len(todo), 25):  # ponytail: lots de 25 fichiers par import, limite prudente
                batch = todo[n:n + 25]
                try:
                    r = _import_or_busy([f"https://drive.google.com/file/d/{i}" for i in batch],
                                        f"gs://{BUCKET}/sync/runs/{stamp}-{folder['id']}-{n}.ndjson")
                    src["importes"] += r.imported_rag_files_count
                    src["echecs"] += r.failed_rag_files_count
                except NotFound:
                    # Un fichier du lot est invisible pour l'agent RAG (404, vérifié) : tout le lot échoue.
                    # On rejoue fichier par fichier pour isoler les fautifs.
                    for i in batch:
                        try:
                            r = _import_or_busy([f"https://drive.google.com/file/d/{i}"],
                                                f"gs://{BUCKET}/sync/runs/{stamp}-{i}.ndjson")
                            src["importes"] += r.imported_rag_files_count
                        except NotFound:
                            unreadable.append(files[i]["name"])
            if unreadable:
                src["echecs"] += len(unreadable)
                report["erreurs"].append(
                    f"{src['source']} : {len(unreadable)} fichier(s) illisible(s) pour l'agent RAG "
                    f"({', '.join(unreadable[:5])}{'…' if len(unreadable) > 5 else ''}). Partagez le dossier (lecteur) "
                    f"avec {RAG_AGENT_EMAIL}.")
            report["sources"].append(src)

        # 6. Dépôts et miroir Google : RAG Engine saute lui-même l'inchangé pour GCS (vérifié).
        prefixes = ([f"gs://{BUCKET}/{UPLOADS}"] if uploads else []) + ([f"gs://{BUCKET}/{gdrive.MIRROR}"] if mirrored else [])
        if prefixes:
            r = _import_or_busy(prefixes, f"gs://{BUCKET}/sync/runs/{stamp}-gcs.ndjson")
            report["sources"].append({"source": "Fichiers déposés" + (" et miroir Google" if mirrored else ""),
                                      "importes": r.imported_rag_files_count, "inchanges": r.skipped_rag_files_count,
                                      "echecs": r.failed_rag_files_count})

        # 7. Contrôle : fichiers Drive vus par le kit mais absents du corpus (souvent : agent RAG pas dans le partage).
        indexed = {corpus_key(f) for f in list_corpus()}
        for folder, src in zip([f for f in folders if f["id"] in drive], report["sources"]):
            missing = [f["name"] for i, f in drive[folder["id"]].items() if i not in indexed]
            src["non_indexes"] = missing[:20]
            already = any(e.startswith(src["source"]) for e in report["erreurs"])
            if missing and len(missing) == len(drive[folder["id"]]) and not already:
                report["erreurs"].append(f"{src['source']} : aucun fichier indexé. Le dossier est-il partagé "
                                         f"(lecteur) avec {RAG_AGENT_EMAIL} ?")
        report["sources"] += google_report["sources"]
    except Busy:
        # Une autre passe tourne : l'appelant (sync_job.py) attend et recommence TOUTE la passe, avec un listing
        # frais. Ce rapport n'écrase pas celui de l'autre passe.
        report["statut"] = "occupe"
        return report
    except Exception as e:  # imprévu : on l'écrit dans le rapport (visible dans l'interface), puis on échoue
        report["statut"] = "erreur"
        report["erreurs"].append(f"{type(e).__name__} : {str(e)[:300]}")
        _write_report(report, started)
        raise

    if report["erreurs"] and report["statut"] == "ok":
        report["statut"] = "avertissement"
    _write_report(report, started)
    return report


def _write_report(report: dict, started: float) -> None:
    report["duree_s"] = round(time.time() - started, 1)
    report["documents"] = len(list_corpus())
    _bucket.blob(LAST_SYNC_OBJ).upload_from_string(json.dumps(report, ensure_ascii=False, indent=2),
                                                   content_type="application/json")


def last_sync() -> dict | None:
    blob = _bucket.blob(LAST_SYNC_OBJ)
    return json.loads(blob.download_as_text()) if blob.exists() else None


# --- Job Cloud Run (bouton « Synchroniser ») -------------------------------------

def _run_api(method: str, suffix: str = "", body: dict | None = None):
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/{REGION}/jobs/{SYNC_JOB}{suffix}"
    r = AuthorizedSession(creds).request(method, url, json=body)
    r.raise_for_status()
    return r.json()


def sync_running() -> bool:
    if not SYNC_JOB:
        return False
    last = _run_api("GET").get("latestCreatedExecution", {})
    return bool(last.get("createTime")) and not last.get("completionTime")


def start_sync(trigger: str = "manuel") -> str:
    """Lance une passe : 'lancee' (job Cloud Run), ou 'terminee' en local (pas de SYNC_JOB).
    Toujours une NOUVELLE exécution, même si une autre tourne : celle-ci attendra son tour (voir sync_job.py) et,
    partie après l'action, verra forcément le dernier état. (Une file « à refaire » posée pendant une passe se
    perdait si la passe finissait au même instant : vérifié.)"""
    if not SYNC_JOB:
        run_sync()
        return "terminee"
    # TRIGGER=auto (webhook) : les sources dont la synchro auto est coupée sont laissées de côté.
    _run_api("POST", ":run", {"overrides": {"containerOverrides": [{"env": [{"name": "TRIGGER", "value": trigger}]}]}})
    return "lancee"


# --- Recherche (outil de l'agent) ---------------------------------------------------

CORPUS_GE = os.environ.get("CORPUS_GE", "")  # hybride : corpus adossé à l'app Gemini Enterprise (lecture seule)


def _retrieve(corpus: str, question: str, top_k: int, ranked: bool = True):
    cfg = rag.RagRetrievalConfig(top_k=top_k, ranking=rag.Ranking(
        rank_service=rag.RankService(model_name="semantic-ranker-default@latest")) if ranked else None)
    return rag.retrieval_query(text=question, rag_resources=[rag.RagResource(rag_corpus=corpus)],
                               rag_retrieval_config=cfg).contexts.contexts


def search(question: str, top_k: int = 8) -> list[dict]:
    """Extraits du corpus du kit, et (hybride) de l'app Gemini Enterprise, entrelacés par rang."""
    lists = [[("kit", c) for c in _retrieve(CORPUS, question, top_k)]]
    if CORPUS_GE:
        try:
            lists.append([("gemini-enterprise", c) for c in _retrieve(CORPUS_GE, question, top_k)])
        except Exception as e:  # l'app GE en panne ne doit pas priver des documents du kit
            logging.warning("recherche Gemini Enterprise en échec : %s", e)
    merged = [x for pair in zip(*lists) for x in pair] + [x for lst in lists for x in lst[min(map(len, lists)):]]
    out, seen = [], set()
    for origin, c in merged:
        key = (c.source_uri, c.text[:80])
        if key in seen:
            continue
        seen.add(key)
        out.append({"titre": _title(c), "lien": public_link(c.source_uri), "origine": origin,
                    "extrait": re.sub(r"</?b>", "", c.text)})  # surlignage renvoyé par Vertex AI Search
    return out[:top_k]


_meta_cache: dict = {}


def mirror_meta(uri: str) -> dict:
    """Métadonnées (titre, lien Drive) d'un fichier du miroir, gardées en cache."""
    if uri not in _meta_cache:
        blob = _bucket.get_blob(uri[len(f"gs://{BUCKET}/"):])
        _meta_cache[uri] = (blob.metadata or {}) if blob else {}
    return _meta_cache[uri]


def _title(ctx) -> str:
    if ctx.source_uri.startswith(f"gs://{BUCKET}/{gdrive.MIRROR}"):
        return mirror_meta(ctx.source_uri).get("titre") or ctx.source_display_name
    return ctx.source_display_name


def public_link(uri: str) -> str:
    """Miroir Google -> lien Drive d'origine ; gs://b/o -> téléchargement authentifié ; liens Drive tels quels."""
    if BUCKET and uri.startswith(f"gs://{BUCKET}/{gdrive.MIRROR}"):
        link = mirror_meta(uri).get("lien")
        if link:
            return link
    return uri.replace("gs://", "https://storage.cloud.google.com/", 1) if uri.startswith("gs://") else uri
