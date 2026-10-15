"""Briques vocales avec l'API Gemini : synthèse (TTS), transcription (STT) + diarisation, compte rendu.

Les noms de modèles viennent de variables d'environnement (voir .env.example).
"""
import io
import json
import os
import time
import wave

from dotenv import load_dotenv
from typing import Literal

from pydantic import BaseModel

load_dotenv()

MODEL = os.getenv("MODEL", "gemini-3.5-flash")                  # résumé, raisonnement
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-3.8-flash-tts")      # texte -> voix
STT_MODEL = os.getenv("STT_MODEL", "gemini-3.5-transcribe")     # voix -> texte
RATE = 24000  # les modèles TTS Gemini produisent du PCM 16 bits mono à 24 kHz


def client():
    from google import genai  # import tardif : les tests n'en ont pas besoin
    return genai.Client()  # lit GOOGLE_API_KEY (ou GEMINI_API_KEY) dans l'environnement


def with_retry(fn, tries=5):
    """Réessaie sur 429 (quota) et 503 (surcharge), avec attente croissante."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # google.genai.errors.APIError porte un .code
            if getattr(e, "code", None) not in (429, 500, 503) or i == tries - 1:
                raise
            time.sleep(2 ** i * 3)


# ---------- WAV ----------
def save_wav(data: bytes, path: str, rate: int = RATE) -> float:
    """Écrit l'audio renvoyé par le TTS. Selon le modèle, c'est déjà un WAV (en-tête RIFF)
    ou du PCM brut qu'il faut envelopper. Renvoie la durée en secondes."""
    if not data.startswith(b"RIFF"):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(data)
        data = buf.getvalue()
    with open(path, "wb") as f:
        f.write(data)
    return wav_seconds(data)


def wav_seconds(data: bytes) -> float:
    with wave.open(io.BytesIO(data)) as w:
        return w.getnframes() / w.getframerate()


# ---------- TTS ----------
def _voice(name):
    from google.genai import types
    return types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=name))


def tts(c, text: str, path: str, voice: str = "Kore", style: str | None = None) -> float:
    """Une seule voix. Le style (« chaleureux, posé ») passe par speech_metadata."""
    from google.genai import types
    part = types.Part(text=text, speech_metadata=types.SpeechMetadata(style=style) if style else None)
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"], speech_config=types.SpeechConfig(voice_config=_voice(voice)))
    r = with_retry(lambda: c.models.generate_content(model=TTS_MODEL, contents=[part], config=cfg))
    return save_wav(r.candidates[0].content.parts[0].inline_data.data, path)


def tts_dialogue(c, lines: list[dict], voices: dict[str, str], path: str) -> float:
    """Plusieurs voix (2 maximum) : une Part par réplique, chacune étiquetée avec son locuteur."""
    from google.genai import types
    parts = [types.Part(text=l["text"], speech_metadata=types.SpeechMetadata(
        speaker=l["speaker"], style=l.get("style"))) for l in lines]
    cfg = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=[types.SpeakerVoiceConfig(speaker=s, voice_config=_voice(v))
                                   for s, v in voices.items()])))
    r = with_retry(lambda: c.models.generate_content(
        model=TTS_MODEL, contents=[types.Content(role="user", parts=parts)], config=cfg))
    return save_wav(r.candidates[0].content.parts[0].inline_data.data, path)


# ---------- STT ----------
def transcribe(c, path: str, language: str = "fr-FR") -> list[dict]:
    """Transcription + diarisation (qui parle quand). Renvoie [{"speaker": "spk:0", "text": ...}]."""
    from google.genai import types
    audio = types.Part.from_bytes(data=open(path, "rb").read(), mime_type="audio/wav")
    cfg = types.GenerateContentConfig(audio_transcription_config=types.AudioTranscriptionConfig(
        diarization=True, language_codes=[language]))
    r = with_retry(lambda: c.models.generate_content(model=STT_MODEL, contents=[audio], config=cfg))
    return segments_from_parts(r.candidates[0].content.parts)


def segments_from_parts(parts) -> list[dict]:
    """Fusionne les segments consécutifs d'un même locuteur."""
    out = []
    for p in parts:
        t = p.audio_transcription
        if not t or not t.text:
            continue
        spk = t.speaker_label or "spk:?"
        if out and out[-1]["speaker"] == spk:
            out[-1]["text"] += " " + t.text.strip()
        else:
            out.append({"speaker": spk, "text": t.text.strip()})
    return out


def as_text(segments: list[dict]) -> str:
    return "\n".join(f'{s["speaker"]}: {s["text"]}' for s in segments)


# ---------- Compte rendu ----------
class CompteRendu(BaseModel):
    role_agent: str                 # étiquette de diarisation de l'agent, ex. "spk:0"
    motif: str
    numero_commande: str | None
    sentiment_client: Literal["satisfait", "neutre", "mécontent"]  # une enum dans le schéma JSON
    actions: list[str]              # engagements pris par l'agent
    resume: str                     # 2 à 3 phrases
    reponse_vocale: str             # message de rappel lu au client (TTS), < 60 mots


PROMPT = """Tu analyses la transcription d'un appel au service client.
Les locuteurs sont étiquetés par la diarisation (spk:0, spk:1...). Déduis lequel est l'agent.
N'invente rien : si une information n'est pas dans l'appel, mets null.
reponse_vocale : message court et chaleureux, au vouvoiement, que l'on enverra au client
pour confirmer ce qui a été convenu (pas de liste, phrases simples faciles à écouter).

Transcription :
{transcript}"""


def summarize(c, segments: list[dict]) -> CompteRendu:
    cfg = {"response_mime_type": "application/json", "response_schema": CompteRendu}
    r = with_retry(lambda: c.models.generate_content(
        model=MODEL, contents=PROMPT.format(transcript=as_text(segments)), config=cfg))
    return CompteRendu.model_validate_json(r.text)


# ---------- Évaluation ----------
def wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate : (substitutions + suppressions + insertions) / nb de mots de référence."""
    norm = lambda s: "".join(ch.lower() if ch.isalnum() or ch in " '" else " " for ch in s).split()
    r, h = norm(reference), norm(hypothesis)
    d = list(range(len(h) + 1))  # distance d'édition sur les mots, une ligne à la fois
    for i, rw in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hw in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rw != hw))
    return d[len(h)] / max(len(r), 1)


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
