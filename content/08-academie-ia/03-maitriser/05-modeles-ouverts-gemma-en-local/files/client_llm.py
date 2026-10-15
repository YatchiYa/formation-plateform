"""Client « compatible OpenAI » minimal : le même code parle à Ollama, llama.cpp, LM Studio,
à l'API Gemini (Gemma et Gemini) et à Vertex AI.

Choix du fournisseur par la variable LLM_FOURNISSEUR : gemini (défaut), vertex, ollama, llamacpp, lmstudio,
ou LLM_BASE_URL / LLM_API_KEY pour tout autre serveur compatible.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()

BASES = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "ollama": "http://localhost:11434/v1",
    "llamacpp": "http://localhost:8080/v1",   # llama-server lancé avec --port 8080
    "lmstudio": "http://localhost:1234/v1",
}
PENSEE = re.compile(r"<(thought|think)>.*?</\1>", re.DOTALL)  # raisonnement renvoyé dans le texte


def nettoyer(texte: str) -> str:
    """Retire les blocs de raisonnement <thought>…</thought> ou <think>…</think>."""
    return PENSEE.sub("", texte or "").strip()


def _jeton_vertex() -> str:
    import google.auth
    import google.auth.transport.requests

    cred, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cred.refresh(google.auth.transport.requests.Request())
    return cred.token


def configuration(fournisseur: str | None = None) -> tuple[str, str]:
    """Renvoie (base_url, cle) selon le fournisseur choisi."""
    fournisseur = fournisseur or os.environ.get("LLM_FOURNISSEUR", "gemini")
    if os.environ.get("LLM_BASE_URL"):
        return os.environ["LLM_BASE_URL"].rstrip("/"), os.environ.get("LLM_API_KEY", "local")
    if fournisseur == "gemini":
        return BASES["gemini"], os.environ.get("GEMINI_API_KEY") or os.environ["GOOGLE_API_KEY"]
    if fournisseur == "vertex":
        projet, region = os.environ["GOOGLE_CLOUD_PROJECT"], os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
        base = f"https://{region}-aiplatform.googleapis.com/v1/projects/{projet}/locations/{region}/endpoints/openapi"
        return base, _jeton_vertex()
    if fournisseur in BASES:
        return BASES[fournisseur], "local"   # les serveurs locaux ignorent la clé
    raise ValueError(f"Fournisseur inconnu : {fournisseur}")


@dataclass
class Reponse:
    texte: str
    latence_s: float
    jetons_sortie: int | None


class ClientLLM:
    def __init__(self, base_url: str, cle: str, transport: httpx.BaseTransport | None = None, essais: int = 6):
        self.http = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {cle}"},
                                 timeout=120, transport=transport)
        self.essais = essais

    @classmethod
    def depuis_env(cls, fournisseur: str | None = None) -> "ClientLLM":
        return cls(*configuration(fournisseur))

    def discuter(self, modele: str, question: str, systeme: str | None = None, max_tokens: int = 2048) -> Reponse:
        messages = ([{"role": "system", "content": systeme}] if systeme else []) + [{"role": "user", "content": question}]
        corps = {"model": modele, "messages": messages, "max_tokens": max_tokens, "temperature": 0}
        for essai in range(self.essais):
            debut = time.perf_counter()
            r = self.http.post("/chat/completions", json=corps)
            latence = time.perf_counter() - debut
            if r.status_code in (429, 500, 503) and essai < self.essais - 1:
                time.sleep(3 * 2 ** essai)   # 3, 6, 12, 24, 48 s ; la latence mesurée exclut l'attente
                continue
            r.raise_for_status()
            data = r.json()
            texte = data["choices"][0]["message"].get("content") or ""
            return Reponse(nettoyer(texte), latence, (data.get("usage") or {}).get("completion_tokens"))
        raise RuntimeError("inaccessible")  # pragma: no cover

    def modeles(self) -> list[str]:
        return [m["id"] for m in self.http.get("/models").json()["data"]]


if __name__ == "__main__":
    client = ClientLLM.depuis_env()
    print([m for m in client.modeles() if "gemma" in m])
