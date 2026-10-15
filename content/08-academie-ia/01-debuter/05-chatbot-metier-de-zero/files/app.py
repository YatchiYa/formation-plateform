"""API web d'Alti : sert la page HTML et répond en streaming.

Lancer en local :  uvicorn app:app --reload --port 8000
"""
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

import chatbot

app = FastAPI(title="Alti, assistant de la Salle Altitude")


class Question(BaseModel):
    session: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=2000)


class Avis(BaseModel):
    echange_id: str = Field(min_length=1, max_length=64)
    note: Literal[1, -1]
    commentaire: str = Field("", max_length=500)


@app.get("/")
def page():
    return FileResponse(Path(__file__).parent / "index.html")


@app.post("/chat")
def chat(q: Question):
    echange_id = uuid.uuid4().hex[:12]
    return StreamingResponse(
        chatbot.repondre(q.session, q.message, echange_id),
        media_type="text/plain; charset=utf-8",
        headers={"X-Echange-Id": echange_id})


@app.post("/avis")
def avis(a: Avis):
    chatbot.enregistrer_avis(a.echange_id, a.note, a.commentaire)
    return {"ok": True}


@app.get("/stats")
def stats():
    return chatbot.statistiques()


@app.get("/sante")
def sante():
    return {"ok": True, "modele": chatbot.MODEL}
