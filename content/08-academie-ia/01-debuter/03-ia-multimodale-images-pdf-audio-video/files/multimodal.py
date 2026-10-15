"""Lab « IA multimodale » : analyseur de justificatifs + résumeur de PDF (+ audio, vidéo, comparaison).

    python multimodal.py justificatif ticket.png
    python multimodal.py pdf rapport.pdf [--files]
    python multimodal.py comparer ticket.png facture.png
    python multimodal.py audio memo.wav
    python multimodal.py video tuto.mp4

Clé : GOOGLE_API_KEY (ou GEMINI_API_KEY) dans l'environnement ou un fichier .env.
"""
import json
import mimetypes
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
# Les guides image/audio/vidéo donnent 20 Mo par requête en inline : on reste prudent.
INLINE_MAX = 20 * 1024 * 1024
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
        ".pdf": "application/pdf", ".wav": "audio/wav", ".mp3": "audio/mp3", ".m4a": "audio/m4a",
        ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}


ENVOYES = []  # fichiers envoyés à l'API Files pendant ce run, supprimés à la fin


# ---------- Schémas de sortie (ce que le modèle DOIT renvoyer) ----------
class Ligne(BaseModel):
    libelle: str
    montant: float = Field(description="montant TTC de la ligne, en nombre (2.60)")


class Justificatif(BaseModel):
    type: str = Field(description="ticket, facture ou autre")
    commercant: str
    date: str = Field(description="au format AAAA-MM-JJ")
    numero: str | None = None
    lignes: list[Ligne]
    total_ttc: float
    tva: float | None = None
    devise: str = "EUR"
    lisible: bool = Field(description="false si l'image est trop floue pour être sûr")


class ResumePdf(BaseModel):
    titre: str
    resume: str = Field(description="3 phrases maximum")
    points_cles: list[str]
    chiffres_cles: list[str] = Field(description="chiffres recopiés du document, avec leur page")


# ---------- Préparer un fichier pour le modèle ----------
def mime_of(path) -> str:
    p = Path(path)
    return MIME.get(p.suffix.lower()) or mimetypes.guess_type(p.name)[0] or "application/octet-stream"


def doit_uploader(path, forcer_files=False) -> bool:
    """Inline si petit ; API Files si gros, si vidéo, ou si on veut réutiliser le fichier."""
    return forcer_files or mime_of(path).startswith("video/") or Path(path).stat().st_size > INLINE_MAX


def uploader(client, path, attente_max=120):
    """Envoie le fichier à l'API Files (stocké 48 h) et attend qu'il soit ACTIVE."""
    f = client.files.upload(file=str(path), config={"mime_type": mime_of(path)})
    ENVOYES.append(f.name)
    debut = time.time()
    while f.state and f.state.name == "PROCESSING":
        if time.time() - debut > attente_max:
            raise TimeoutError(f"{path} toujours en traitement")
        time.sleep(2)
        f = client.files.get(name=f.name)
    if f.state and f.state.name == "FAILED":
        raise RuntimeError(f"Traitement échoué pour {path}")
    return f


def nettoyer(client):
    """Supprime les fichiers envoyés (sinon ils restent 48 h dans le projet)."""
    while ENVOYES:
        client.files.delete(name=ENVOYES.pop())


def part_from(client, path, forcer_files=False):
    if doit_uploader(path, forcer_files):
        return uploader(client, path)
    return types.Part.from_bytes(data=Path(path).read_bytes(), mime_type=mime_of(path))


# ---------- Appel au modèle, avec réessais sur 429/503 ----------
def generer(client, contents, schema=None, essais=4):
    config = types.GenerateContentConfig(temperature=0)
    if schema:
        config.response_mime_type = "application/json"
        config.response_schema = schema
    for i in range(essais):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=config)
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == essais - 1:
                raise
            time.sleep(5 * 2 ** i)  # 5 s, 10 s, 20 s


def tokens(reponse) -> dict:
    u = reponse.usage_metadata
    return {"entree": u.prompt_token_count, "sortie": u.candidates_token_count}


# ---------- Cas d'usage ----------
PROMPT_JUSTIFICATIF = (
    "Tu es un assistant comptable. Extrais les informations de ce justificatif. "
    "Recopie les montants tels qu'ils sont écrits (virgule -> point). "
    "N'invente rien : si un champ est illisible ou absent, mets null et lisible=false.")


def verifier(j: Justificatif) -> list[str]:
    """Contrôles déterministes : le modèle extrait, le code vérifie."""
    alertes = []
    somme = round(sum(l.montant for l in j.lignes), 2)
    if j.lignes and abs(somme - j.total_ttc) > 0.01:
        alertes.append(f"somme des lignes {somme} != total {j.total_ttc}")
    if j.tva is not None and not 0 <= j.tva < j.total_ttc:
        alertes.append(f"TVA incohérente : {j.tva}")
    if not (len(j.date) == 10 and j.date[4] == j.date[7] == "-"):
        alertes.append(f"date au mauvais format : {j.date}")
    if not j.lisible:
        alertes.append("image jugée peu lisible : vérification humaine")
    return alertes


def analyser_justificatif(client, image_path):
    r = generer(client, [part_from(client, image_path), PROMPT_JUSTIFICATIF], schema=Justificatif)
    j = Justificatif.model_validate_json(r.text)
    return {"justificatif": j.model_dump(), "alertes": verifier(j), "tokens": tokens(r)}


def resumer_pdf(client, pdf_path, via_files=False):
    prompt = ("Résume ce document pour un manager pressé. Ne cite que des chiffres "
              "présents dans le document, en indiquant la page.")
    r = generer(client, [part_from(client, pdf_path, via_files), prompt], schema=ResumePdf)
    return {**ResumePdf.model_validate_json(r.text).model_dump(), "tokens": tokens(r)}


def comparer_images(client, chemins):
    parts = []
    for i, c in enumerate(chemins, 1):  # on étiquette chaque image pour pouvoir y faire référence
        parts += [f"Image {i} :", part_from(client, c)]
    parts.append("Compare ces justificatifs : type, émetteur, date, total. "
                 "Lequel est une facture d'entreprise ? Réponds en 5 lignes maximum.")
    r = generer(client, parts)
    return {"texte": r.text, "tokens": tokens(r)}


def transcrire(client, audio_path):
    r = generer(client, [part_from(client, audio_path),
                         "Transcris cet audio mot à mot en français, puis liste les actions à faire "
                         "sous la forme « - action (échéance) »."])
    return {"texte": r.text, "tokens": tokens(r)}


def decrire_video(client, video_path):
    r = generer(client, [part_from(client, video_path),
                         "Liste les étapes montrées dans cette vidéo avec leur horodatage (MM:SS)."])
    return {"texte": r.text, "tokens": tokens(r)}


ACTIONS = {"justificatif": analyser_justificatif, "pdf": resumer_pdf, "audio": transcrire,
           "video": decrire_video}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    action, args = sys.argv[1], sys.argv[2:]
    client = genai.Client()  # lit GOOGLE_API_KEY / GEMINI_API_KEY
    try:
        if action == "comparer":
            res = comparer_images(client, args)
        elif action == "pdf":
            res = resumer_pdf(client, args[0], via_files="--files" in args)
        else:
            res = ACTIONS[action](client, args[0])
    finally:
        nettoyer(client)
    print(json.dumps(res, ensure_ascii=False, indent=2))
