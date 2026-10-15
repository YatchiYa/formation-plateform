"""Routeur de modèles avec cache sémantique et mesures (TTFT, latence, tokens, coût).

Chemin d'une question :
  1. embedding -> cache sémantique : question déjà vue (même sens) ? réponse immédiate ;
  2. sinon petit modèle (flash-lite) en streaming, qui répond ET donne sa confiance ;
  3. confiance trop basse -> escalade vers le grand modèle (flash), si le budget le permet.
"""
import asyncio
import json
import os
import random
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SMALL_MODEL = os.environ.get("SMALL_MODEL", "gemini-3.5-flash-lite")
BIG_MODEL = os.environ.get("BIG_MODEL", "gemini-3.8-flash")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
THINKING = os.environ.get("THINKING_LEVEL", "low")  # vide = réglage par défaut (modèles 2.5)
CONF_MIN = float(os.environ.get("CONF_MIN", "0.8"))
CACHE_SIM = float(os.environ.get("CACHE_SIM", "0.90"))
MAX_COST_USD = float(os.environ.get("MAX_COST_USD", "0.01"))  # budget par requête

# USD par million de tokens : (entrée, entrée en cache, sortie). Grille publique de l'API Gemini
# relevée le 2026-10-15 (ai.google.dev/gemini-api/docs/pricing). Vérifiez-la avant de décider.
PRICES = {
    "gemini-3.5-flash-lite": (0.30, 0.03, 2.50),
    "gemini-3.8-flash": (0.75, 0.075, 3.75),
    "gemini-embedding-2": (0.20, 0.20, 0.0),
}

KB = (Path(__file__).parent / "faq.md").read_text(encoding="utf-8")
SYSTEM = (
    "Tu es l'assistant du support client de Lumen & Co. Réponds en français, en 1 à 3 phrases, "
    "UNIQUEMENT à partir de la base de connaissances ci-dessous. Fais les calculs demandés. "
    "Donne ta confiance entre 0 et 1 que ta réponse est exacte et complète ; si l'information "
    "manque ou si le calcul est incertain, mets une confiance basse.\n\n" + KB
)
SCHEMA = {
    "type": "object",
    "properties": {"answer": {"type": "string"}, "confidence": {"type": "number"}},
    "required": ["answer", "confidence"],
}


def cost_usd(model: str, prompt: int, cached: int, output: int) -> float:
    """Coût d'un appel. Les tokens de réflexion (thinking) sont facturés comme de la sortie."""
    p_in, p_cached, p_out = PRICES.get(model, (0.0, 0.0, 0.0))
    return ((prompt - cached) * p_in + cached * p_cached + output * p_out) / 1e6


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower().replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text.replace(".", ","))


def grade(answer: str, expect: list) -> bool:
    """Qualité = chaque fait attendu est présent ; "a|b" = l'une des formulations suffit."""
    a = normalize(answer).replace(" ", "")
    return all(any(normalize(alt).replace(" ", "") in a for alt in e.split("|")) for e in expect)


class SemanticCache:
    """Cache en mémoire : cosinus entre embeddings normalisés. Limite connue : recherche linéaire O(n),
    passez à un index vectoriel (Memorystore, Vector Search) au-delà de quelques milliers d'entrées."""

    def __init__(self, threshold: float = CACHE_SIM):
        self.threshold, self.vecs, self.values = threshold, [], []

    def get(self, vec):
        if not self.vecs:
            return None, 0.0
        sims = np.array(self.vecs) @ vec
        i = int(sims.argmax())
        return (self.values[i] if sims[i] >= self.threshold else None), float(sims[i])

    def put(self, vec, value):
        self.vecs.append(vec)
        self.values.append(value)


def unit(values) -> np.ndarray:
    v = np.asarray(values, dtype=np.float32)
    return v / np.linalg.norm(v)


async def with_retry(fn, tries: int = 5):
    """Réessaie sur 429 (quota) et 5xx avec attente exponentielle + gigue."""
    for i in range(tries):
        try:
            return await fn()
        except Exception as e:  # google.genai.errors.APIError porte .code
            code = getattr(e, "code", None)
            if code not in (429, 500, 503, 504) or i == tries - 1:
                raise
            await asyncio.sleep(2 ** i + random.random())


async def embed(client, texts: list) -> list:
    from google.genai import types

    async def call():
        return await client.aio.models.embed_content(
            # Une liste de str serait fusionnée en UN seul texte : un Content par texte.
            model=EMBED_MODEL, contents=[types.Content(parts=[types.Part(text=t)]) for t in texts],
            config=types.EmbedContentConfig(output_dimensionality=768))
    r = await with_retry(call)
    assert len(r.embeddings) == len(texts), "un embedding attendu par texte"
    return [unit(e.values) for e in r.embeddings]


@dataclass
class Call:
    model: str
    answer: str = ""
    confidence: float = 0.0
    ttft: float = 0.0     # time to first token, en secondes
    latency: float = 0.0  # réponse complète
    prompt_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0  # sortie + réflexion

    @property
    def cost(self) -> float:
        return cost_usd(self.model, self.prompt_tokens, self.cached_tokens, self.output_tokens)


async def ask(client, model: str, question: str, max_output_tokens: int = 1024) -> Call:
    """Un appel en streaming : on chronomètre le premier fragment (TTFT) et la fin."""
    from google.genai import types

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM,
        response_mime_type="application/json",
        response_schema=SCHEMA,
        max_output_tokens=max_output_tokens,
        thinking_config=types.ThinkingConfig(thinking_level=THINKING) if THINKING else None,
    )

    async def call():
        c, parts, t0 = Call(model), [], time.perf_counter()
        async for chunk in await client.aio.models.generate_content_stream(
                model=model, contents=question, config=config):
            if not c.ttft and chunk.text:
                c.ttft = time.perf_counter() - t0
            parts.append(chunk.text or "")
            if chunk.usage_metadata:
                u = chunk.usage_metadata
                c.prompt_tokens = u.prompt_token_count or 0
                c.cached_tokens = u.cached_content_token_count or 0
                c.output_tokens = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
        c.latency = time.perf_counter() - t0
        try:
            data = json.loads("".join(parts))
            c.answer, c.confidence = data["answer"], float(data["confidence"])
        except (ValueError, KeyError):
            c.answer, c.confidence = "".join(parts), 0.0  # sortie illisible = confiance nulle
        return c

    return await with_retry(call)


@dataclass
class Result:
    answer: str
    route: str  # cache | small | escalated | big
    calls: list = field(default_factory=list)
    latency: float = 0.0
    ttft: float = 0.0
    similarity: float = 0.0  # meilleure similarité trouvée dans le cache

    @property
    def cost(self) -> float:
        return sum(c.cost for c in self.calls)


class Router:
    def __init__(self, client, cache: SemanticCache | None = None, conf_min: float = CONF_MIN,
                 max_cost: float = MAX_COST_USD):
        self.client, self.cache, self.conf_min, self.max_cost = client, cache, conf_min, max_cost

    async def answer(self, question: str, vec=None) -> Result:
        t0, sim = time.perf_counter(), 0.0
        if self.cache is not None and vec is not None:
            hit, sim = self.cache.get(vec)
            if hit is not None:
                dt = time.perf_counter() - t0
                return Result(hit, "cache", latency=dt, ttft=dt, similarity=sim)

        small = await ask(self.client, SMALL_MODEL, question)
        res = Result(small.answer, "small", [small], ttft=small.ttft)
        # Escalade si la confiance est basse ET si le budget de la requête le permet.
        # Coût estimé du grand modèle : mêmes tokens, sortie doublée par prudence.
        big_estimate = cost_usd(BIG_MODEL, small.prompt_tokens, small.cached_tokens, 2 * small.output_tokens)
        if small.confidence < self.conf_min and small.cost + big_estimate <= self.max_cost:
            big = await ask(self.client, BIG_MODEL, question)
            res = Result(big.answer, "escalated", [small, big], ttft=small.latency + big.ttft)
        res.latency, res.similarity = time.perf_counter() - t0, sim
        if self.cache is not None and vec is not None:
            self.cache.put(vec, res.answer)
        return res
