"""Briques partagées du lab : étiquettes, prompt système, format Vertex AI, appel au modèle."""
import os
import time

from dotenv import load_dotenv

load_dotenv()

LABELS = ["facturation", "acces_compte", "bug_technique", "demande_fonctionnalite", "resiliation"]

SYSTEM = (
    "Tu classes les tickets du support client d'un logiciel de gestion en ligne. "
    "Réponds UNIQUEMENT par une étiquette parmi : " + ", ".join(LABELS) + "."
)


def to_example(ticket: str, label: str) -> dict:
    """Une ligne du JSONL de réglage supervisé Gemini sur Vertex AI."""
    return {
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [
            {"role": "user", "parts": [{"text": ticket}]},
            {"role": "model", "parts": [{"text": label}]},
        ],
    }


def from_example(ex: dict) -> tuple[str, str]:
    """(ticket, étiquette) depuis une ligne JSONL."""
    return ex["contents"][0]["parts"][0]["text"], ex["contents"][-1]["parts"][0]["text"]


def parse_label(text: str | None) -> str | None:
    """Ramène la réponse du modèle à une étiquette connue (ou None)."""
    t = (text or "").strip().strip("`\"'. ").lower().replace(" ", "_").replace("-", "_")
    if t in LABELS:
        return t
    hits = [l for l in LABELS if l in t]
    return hits[0] if len(hits) == 1 else None


def make_client():
    """Clé d'API (GOOGLE_API_KEY) ou Vertex AI (GOOGLE_GENAI_USE_VERTEXAI=TRUE + projet/région)."""
    from google import genai

    return genai.Client()


def generate(client, model, contents, config=None, retries=6):
    """generate_content avec attente exponentielle sur 429/500/503."""
    from google.genai import errors

    for i in range(retries):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except errors.APIError as e:
            if e.code in (429, 500, 503) and i < retries - 1:
                time.sleep(2 ** i * 2)
                continue
            raise


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)
