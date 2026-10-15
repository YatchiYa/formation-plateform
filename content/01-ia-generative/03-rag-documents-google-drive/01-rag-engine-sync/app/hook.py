"""Service public « <prefix>-hook » : reçoit les notifications push de Google Drive et lance la synchro.

Google appelle POST /hook/drive à chaque changement (en-têtes X-Goog-*). On n'accepte que les canaux ouverts par le kit
(identifiant + jeton secret rangés dans l'état de la source), et on regroupe les rafales : si une exécution a été
créée il y a moins de 10 s et n'a pas encore fini, elle verra ce changement (elle n'a pas encore listé).
"""

import time
from datetime import datetime

from fastapi import FastAPI, Header, HTTPException, Response

import gdrive
import kit

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.post("/hook/drive")
def drive_notification(x_goog_channel_id: str = Header(""), x_goog_channel_token: str = Header(""),
                       x_goog_resource_state: str = Header("")):
    if not gdrive.find_channel(kit._bucket, x_goog_channel_id, x_goog_channel_token):
        raise HTTPException(403, "canal inconnu")
    if x_goog_resource_state == "sync":  # message d'ouverture du canal, pas un changement
        return Response(status_code=204)
    last = kit._run_api("GET").get("latestCreatedExecution", {})
    created = last.get("createTime")
    recent = created and time.time() - datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp() < 10
    if not (recent and not last.get("completionTime")):
        kit.start_sync(trigger="auto")
    return Response(status_code=204)
