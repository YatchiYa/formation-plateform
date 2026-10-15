"""Tests sans clé ni réseau : on remplace le modèle par un faux.  Lancer : pytest -q"""
import asyncio

from fastapi.testclient import TestClient
from google.genai import errors

import main

TICKET = {"subject": "Facture en double", "body": "J'ai été prélevé deux fois ce mois-ci, merci de corriger."}


class FakeLLM:
    def __init__(self, delay: float = 0, fail: int | None = None):
        self.delay, self.fail = delay, fail

    async def analyze(self, t):
        await asyncio.sleep(self.delay)
        if self.fail:
            raise errors.APIError(self.fail, {"error": {"message": "boom"}})
        return main.Analysis(summary="Double prélèvement.", category="facturation",
                             priority="haute", sentiment="negatif"), {"tokens_in": 10, "tokens_out": 5}

    async def stream_summary(self, t):
        for piece in ["- Double ", "prélèvement\n", "- Rembourser"]:
            yield piece


def client(llm) -> TestClient:
    main.app.dependency_overrides[main.get_llm] = lambda: llm
    return TestClient(main.app)


def test_health():
    assert client(FakeLLM()).get("/health").json()["status"] == "ok"


def test_analyze_ok():
    r = client(FakeLLM()).post("/v1/tickets/analyze", json=TICKET)
    assert r.status_code == 200
    assert r.json()["category"] == "facturation"


def test_validation_rejects_bad_input():
    c = client(FakeLLM())
    assert c.post("/v1/tickets/analyze", json={"subject": "x", "body": "court"}).status_code == 422
    assert c.post("/v1/tickets/analyze", json={**TICKET, "body": "a" * 9000}).status_code == 422
    assert c.post("/v1/tickets/analyze", json={**TICKET, "language": "de"}).status_code == 422


def test_timeout_returns_504(monkeypatch):
    monkeypatch.setattr(main, "LLM_TIMEOUT_S", 0.05)
    assert client(FakeLLM(delay=1)).post("/v1/tickets/analyze", json=TICKET).status_code == 504


def test_quota_error_returns_503_with_retry_after():
    r = client(FakeLLM(fail=429)).post("/v1/tickets/analyze", json=TICKET)
    assert r.status_code == 503 and r.headers["retry-after"] == "5"


def test_stream_sse():
    with client(FakeLLM()).stream("POST", "/v1/tickets/summarize-stream", json=TICKET) as r:
        assert r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    assert "event: delta" in body and 'data: {"text": "- Double "}' in body
    assert body.rstrip().endswith('data: {"done": true}')


def test_json_logs(capsys):
    main.handler.setStream(__import__("sys").stdout)  # pointe vers la sortie capturée par pytest
    client(FakeLLM()).get("/health")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    entry = __import__("json").loads(line)
    assert entry["severity"] == "INFO" and entry["path"] == "/health" and "latency_ms" in entry
