"""Agent d'inspection qualité : lit des photos dans Cloud Storage, classe les défauts, publie un rapport.

Variables : BUCKET (obligatoire), MODEL, VISION_MODEL, GOOGLE_GENAI_USE_VERTEXAI=TRUE,
GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION (identifiants ADC, aucune clé).
"""
import os
from collections import Counter
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
VISION_MODEL = os.environ.get("VISION_MODEL", MODEL)
PREFIXE_IMAGES = "images/"
CHEMIN_RAPPORT = "rapports/rapport-inspection.md"
DEFAUTS = ("aucun", "rayure", "fissure", "tache", "manque")

CONSIGNE_VISION = (
    "Tu es contrôleur qualité. La photo montre une rondelle métallique grise sur un convoyeur clair. "
    "Défauts possibles : rayure (trait clair fin), fissure (trait sombre irrégulier), "
    "tache (zone brune de rouille), manque (morceau absent du bord), ou aucun. "
    "Gravité : fissure et manque = majeure ; rayure et tache = mineure ; aucun = aucune."
)


class Inspection(BaseModel):
    """Sortie structurée imposée au modèle de vision."""
    conforme: bool
    defaut: Literal["aucun", "rayure", "fissure", "tache", "manque"]
    gravite: Literal["aucune", "mineure", "majeure"]
    confiance: float = Field(ge=0, le=1)
    description: str = Field(description="une phrase factuelle sur ce qui est visible")


@lru_cache
def _bucket():
    from google.cloud import storage
    return storage.Client(project=os.environ.get("GOOGLE_CLOUD_PROJECT")).bucket(os.environ["BUCKET"])


@lru_cache
def _genai():
    # Réessaie automatiquement sur 429 / 503 (quota partagé, surcharge passagère)
    return genai.Client(http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2, http_status_codes=[429, 503])))


def classer_image(image: bytes, mime: str = "image/png") -> Inspection:
    """Un appel de vision Gemini, réponse forcée au format JSON du schéma Inspection."""
    r = _genai().models.generate_content(
        model=VISION_MODEL,
        contents=[types.Part.from_bytes(data=image, mime_type=mime), CONSIGNE_VISION],
        config=types.GenerateContentConfig(
            temperature=0, response_mime_type="application/json", response_schema=Inspection),
    )
    return r.parsed if isinstance(r.parsed, Inspection) else Inspection.model_validate_json(r.text)


_resultats: dict[str, dict] = {}


def lister_images() -> dict:
    """Liste les photos de pièces à inspecter dans le bucket."""
    noms = [b.name for b in _bucket().list_blobs(prefix=PREFIXE_IMAGES) if b.name.endswith((".png", ".jpg"))]
    return {"nombre": len(noms), "images": noms}


def inspecter_image(nom: str) -> dict:
    """Inspecte une photo du bucket et renvoie le défaut détecté.

    Args:
        nom: chemin de l'objet dans le bucket, par exemple « images/piece-01.png ».
    """
    if not nom.startswith(PREFIXE_IMAGES) or ".." in nom:
        return {"erreur": f"seuls les objets sous {PREFIXE_IMAGES} sont inspectables"}
    blob = _bucket().blob(nom)
    mime = "image/jpeg" if nom.endswith(".jpg") else "image/png"
    resultat = classer_image(blob.download_as_bytes(), mime).model_dump()
    _resultats[nom] = resultat
    return {"image": nom, **resultat}


def construire_rapport(resultats: dict[str, dict]) -> str:
    """Rapport Markdown déterministe (pas de LLM) à partir des inspections."""
    compte = Counter(r["defaut"] for r in resultats.values())
    rejets = sum(not r["conforme"] for r in resultats.values())
    lignes = [
        "# Rapport d'inspection qualité", "",
        f"- Pièces inspectées : {len(resultats)}",
        f"- Pièces à rejeter : {rejets}",
        "- Répartition : " + ", ".join(f"{d} = {compte.get(d, 0)}" for d in DEFAUTS), "",
        "| Image | Verdict | Défaut | Gravité | Confiance | Observation |",
        "|---|---|---|---|---|---|",
    ]
    for nom, r in sorted(resultats.items()):
        verdict = "conforme" if r["conforme"] else "REJET"
        lignes.append(f"| {nom} | {verdict} | {r['defaut']} | {r['gravite']} | {r['confiance']:.2f} | {r['description']} |")
    return "\n".join(lignes) + "\n"


def publier_rapport() -> dict:
    """Écrit le rapport des inspections déjà faites dans le bucket et renvoie la synthèse."""
    if not _resultats:
        return {"erreur": "aucune image inspectée"}
    texte = construire_rapport(_resultats)
    _bucket().blob(CHEMIN_RAPPORT).upload_from_string(texte, content_type="text/markdown; charset=utf-8")
    rejets = [n for n, r in _resultats.items() if not r["conforme"]]
    return {"rapport": f"gs://{os.environ['BUCKET']}/{CHEMIN_RAPPORT}", "inspectees": len(_resultats), "rejets": rejets}


root_agent = Agent(
    name="inspecteur_qualite",
    # Réessais avec attente sur 429/503 : le quota Vertex AI est partagé par le projet
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2)),
    description="Inspecte les photos de pièces d'un bucket et publie un rapport qualité.",
    instruction=(
        "Tu es l'agent de contrôle qualité d'une ligne de production fictive. Réponds en français. "
        "Procédure : 1) lister_images ; 2) inspecter_image pour CHAQUE image listée ; "
        "3) publier_rapport ; 4) termine par une synthèse de 5 lignes maximum : nombre de pièces, "
        "pièces à rejeter avec leur défaut, et une action recommandée à l'atelier. "
        "Ne déduis jamais un défaut du nom du fichier : seul inspecter_image fait foi."
    ),
    tools=[lister_images, inspecter_image, publier_rapport],
)
