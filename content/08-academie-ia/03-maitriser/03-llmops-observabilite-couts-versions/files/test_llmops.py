"""Tests sans clé : registre, wrapper instrumenté, rapport, porte de non-régression.

Le dernier test appelle le VRAI modèle ; il ne tourne que si une clé est présente (CI avec secret).
"""
import json
import os

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import llm_wrapper
import regression
from prompt_registry import REGISTRY, fingerprint, load
from report import percentile, summarize, to_markdown

EXPORTER = InMemorySpanExporter()
llm_wrapper.setup_tracing(span_exporter=EXPORTER)

CASES = [{"demande": "PC en panne", "service": "it", "urgence": "haute"},
         {"demande": "Mes congés ?", "service": "rh", "urgence": "normale"}]


def fake(answers):
    """Faux modèle : renvoie les réponses données, dans l'ordre, avec des comptes de tokens fixes."""
    it = iter(answers)

    def generate(model, system, prompt, config):
        a = next(it)
        if isinstance(a, Exception):
            raise a
        return a, 100, 20
    return generate


@pytest.fixture(autouse=True)
def tmp_log(tmp_path, monkeypatch):
    monkeypatch.setattr(llm_wrapper, "LOG_PATH", str(tmp_path / "calls.jsonl"))
    EXPORTER.clear()
    return tmp_path / "calls.jsonl"


def test_registry_versions_are_untouched():
    for v in ("v1", "v2"):
        pv = load("router", v)
        assert pv.sha256 == fingerprint({"model": pv.model, "config": pv.config,
                                         "system": pv.system, "template": pv.template})
    assert load("router").version == "v1"   # alias « production »


def test_registry_refuses_edited_version(tmp_path):
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    data["router"]["versions"]["v1"]["system"] += " (modifié en douce)"
    p = tmp_path / "prompts.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="nouvelle version"):
        load("router", "v1", path=p)


def test_call_is_traced_logged_and_priced(tmp_log):
    r = llm_wrapper.call_llm("router", "v1", generate=fake(['{"service":"it","urgence":"haute"}']), demande="x")
    span = EXPORTER.get_finished_spans()[0]
    assert span.attributes["gen_ai.request.model"] == "gemini-3.5-flash-lite"
    assert span.attributes["gen_ai.usage.input_tokens"] == 100
    assert span.attributes["app.prompt.version"] == "v1"
    line = json.loads(tmp_log.read_text().splitlines()[0])
    assert line["trace_id"] == format(span.context.trace_id, "032x")
    assert line["ok"] and line["cost_usd"] == pytest.approx((100 * 0.30 + 20 * 2.50) / 1e6)
    assert "demande" not in line and r["text"].startswith("{")


def test_retry_then_error_is_recorded(tmp_log, monkeypatch):
    monkeypatch.setattr(llm_wrapper.time, "sleep", lambda s: None)

    class Busy(Exception):
        code = 503
    r = llm_wrapper.call_llm("router", "v1", generate=fake([Busy("surchargé"), "{}"]), demande="x")
    assert r["ok"] and r["attempts"] == 2
    r = llm_wrapper.call_llm("router", "v1", generate=fake([ValueError("bug")]), demande="x")
    assert not r["ok"] and r["attempts"] == 1 and r["severity"] == "ERROR"
    assert EXPORTER.get_finished_spans()[-1].status.status_code.name == "ERROR"


def test_report_percentiles_and_costs():
    assert percentile([10, 20, 30, 40, 1000], 50) == 30
    assert percentile([10, 20, 30, 40, 1000], 95) == 1000
    recs = [{"prompt_id": "router", "prompt_version": "v1", "model": "m", "latency_ms": l, "ok": ok,
             "tokens_in": 100, "tokens_out": 10, "cost_usd": 0.001} for l, ok in ((100, True), (300, True), (0, False))]
    s = summarize(recs)["router@v1 (m)"]
    assert s["appels"] == 3 and s["taux_erreur"] == pytest.approx(0.333, abs=1e-3)
    assert s["p50_ms"] == 100 and s["cout_1000_appels_usd"] == pytest.approx(1.0)
    assert "router@v1" in to_markdown(summarize(recs))


def test_gate_rejects_degraded_version():
    good = fake(['{"service":"it","urgence":"haute"}', '{"service":"rh","urgence":"normale"}'])
    bad = fake(['{"service":"Informatique","urgence":"élevée"}', "pas du JSON"])
    base = regression.evaluate("v1", good, CASES)
    cand = regression.evaluate("v2", bad, CASES)
    assert base["exactitude"] == 1.0 and regression.gate(base, base) == []
    assert cand["exactitude"] == 0.0 and cand["json_valide"] == 0.5
    assert len(regression.gate(cand, base)) == 2


@pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_GENAI_USE_VERTEXAI") != "TRUE",
                    reason="pas de clé : test réel ignoré")
def test_production_prompt_does_not_regress_live():
    version = os.environ.get("CANDIDATE_VERSION", "v1")
    result = regression.evaluate(version)
    baseline = json.loads(regression.BASELINE.read_text())
    assert regression.gate(result, baseline) == [], result["echecs"]
