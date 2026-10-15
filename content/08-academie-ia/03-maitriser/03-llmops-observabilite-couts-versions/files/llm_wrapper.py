"""Un seul point d'entrée pour appeler le LLM : trace OpenTelemetry + journal JSON + coût.

    from llm_wrapper import call_llm
    r = call_llm("router", "v1", demande="Mon PC ne démarre plus")

Exporteur de traces (variable OTEL_EXPORTER) :
  console (défaut) -> une ligne JSON par span dans traces.jsonl
  gcp              -> Cloud Trace (pip install opentelemetry-exporter-gcp-trace)
  none             -> pas d'export
"""
import functools
import json
import os
import time
import uuid

from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode

from prompt_registry import load

load_dotenv()

# Prix en dollars par million de tokens, relevés le 2026-10-15 sur ai.google.dev/gemini-api/docs/pricing
# (palier payant, texte). Ils changent : revérifiez-les, ou surchargez-les via PRICES_JSON.
PRICES = {"gemini-3.5-flash-lite": {"input": 0.30, "output": 2.50},
          "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40}}
PRICES.update(json.loads(os.environ.get("PRICES_JSON", "{}")))

LOG_PATH = os.environ.get("LLM_LOG", "calls.jsonl")
RETRYABLE = (429, 500, 503)
_tracer = None


def setup_tracing(exporter: str | None = None, span_exporter=None):
    """Configure OpenTelemetry une fois pour tout le processus."""
    global _tracer
    exporter = exporter or os.environ.get("OTEL_EXPORTER", "console")
    provider = TracerProvider(resource=Resource.create({"service.name": "assistant-interne",
                                                         "service.version": os.environ.get("APP_VERSION", "dev")}))
    if span_exporter is not None:                       # tests : exporteur en mémoire
        provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    elif exporter == "gcp":
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
        provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
    elif exporter == "console":
        out = open("traces.jsonl", "a", encoding="utf-8")
        provider.add_span_processor(SimpleSpanProcessor(
            ConsoleSpanExporter(out=out, formatter=lambda s: s.to_json(indent=None) + "\n")))
    _tracer = provider.get_tracer("llmops-lab")
    return provider


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float | None:
    p = PRICES.get(model)
    return None if p is None else round((tokens_in * p["input"] + tokens_out * p["output"]) / 1e6, 8)


@functools.cache
def _client():
    from google import genai

    return genai.Client()   # un seul client par processus (il garde ses connexions ouvertes)


def gemini_generate(model, system, prompt, config):
    """Appel réel. Renvoie (texte, tokens entrée, tokens sortie y compris réflexion)."""
    from google.genai import types

    r = _client().models.generate_content(
        model=model, contents=prompt, config=types.GenerateContentConfig(system_instruction=system, **config))
    u = r.usage_metadata
    return r.text, u.prompt_token_count or 0, (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)


def log(record: dict):
    """Journal structuré : une ligne JSON = un appel. Cloud Logging lit 'severity' et 'message'."""
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def call_llm(prompt_id: str, version: str = "production", generate=gemini_generate, retries: int = 4,
             **variables) -> dict:
    if _tracer is None:
        setup_tracing()
    pv = load(prompt_id, version)
    prompt = pv.render(**variables)
    provider = "gcp.vertex_ai" if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE" else "gcp.gemini"
    with _tracer.start_as_current_span(f"chat {pv.model}", kind=SpanKind.CLIENT) as span:
        span.set_attributes({"gen_ai.operation.name": "chat", "gen_ai.provider.name": provider,
                             "gen_ai.request.model": pv.model,
                             "gen_ai.request.temperature": pv.config.get("temperature", -1),
                             "app.prompt.id": pv.prompt_id, "app.prompt.version": pv.version,
                             "app.prompt.sha256": pv.sha256})
        t0, text, tin, tout, error, attempts = time.perf_counter(), None, 0, 0, None, 0
        for attempts in range(1, retries + 1):
            try:
                text, tin, tout = generate(pv.model, pv.system, prompt, pv.config)
                error = None
                break
            except Exception as e:  # noqa: BLE001 — on journalise TOUTE erreur, puis on décide
                error = e
                code = getattr(e, "code", None)
                span.add_event("retry", {"attempt": attempts, "error.type": type(e).__name__})
                if code not in RETRYABLE or attempts == retries:
                    break
                time.sleep(2 ** attempts)
        latency_ms = round((time.perf_counter() - t0) * 1000)
        cost = cost_usd(pv.model, tin, tout)
        span.set_attributes({"gen_ai.usage.input_tokens": tin, "gen_ai.usage.output_tokens": tout,
                             "app.cost_usd": cost or 0.0, "app.attempts": attempts})
        if error:
            span.set_attribute("error.type", type(error).__name__)
            span.set_status(Status(StatusCode.ERROR, str(error)[:200]))
        ctx = span.get_span_context()
        record = {"severity": "ERROR" if error else "INFO", "message": "llm_call",
                  "call_id": uuid.uuid4().hex[:12], "trace_id": format(ctx.trace_id, "032x"),
                  "span_id": format(ctx.span_id, "016x"), "prompt_id": pv.prompt_id, "prompt_version": pv.version,
                  "prompt_sha256": pv.sha256, "model": pv.model, "latency_ms": latency_ms,
                  "tokens_in": tin, "tokens_out": tout, "cost_usd": cost, "attempts": attempts,
                  "ok": error is None, "error": f"{type(error).__name__}: {str(error)[:120]}" if error else None}
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if project:   # relie la ligne de journal à sa trace dans la console Google Cloud
            record["logging.googleapis.com/trace"] = f"projects/{project}/traces/{record['trace_id']}"
        log(record)
        return {**record, "text": text}
