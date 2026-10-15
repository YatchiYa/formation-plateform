"""Tests sans clé : un faux client imite l'API (streaming, usage, embeddings)."""
import asyncio
import json
from types import SimpleNamespace as NS

import numpy as np

import bench
import router as R


class FakeModels:
    def __init__(self, conf):
        self.conf, self.calls = conf, []

    async def generate_content_stream(self, model, contents, config):
        self.calls.append(model)
        text = json.dumps({"answer": f"{model}: 4,90 € et offerte dès 60 €", "confidence": self.conf[model]})

        async def gen():
            yield NS(text=text[:10], usage_metadata=None)
            yield NS(text=text[10:], usage_metadata=NS(prompt_token_count=1000, cached_content_token_count=400,
                                                       candidates_token_count=50, thoughts_token_count=10))
        return gen()

    async def embed_content(self, model, contents, config):
        return NS(embeddings=[NS(values=[1.0, float(i)]) for i, _ in enumerate(contents)])


async def same_vector(model, contents, config):
    return NS(embeddings=[NS(values=[1.0, 0.0]) for _ in contents])


def client(conf):
    return NS(aio=NS(models=FakeModels(conf)))


def run(c):
    return asyncio.run(c)


def test_cout_tient_compte_du_cache():
    # 600 non cachés à 0,30 + 400 cachés à 0,03 + 60 sortie à 2,50 (USD / M)
    assert abs(R.cost_usd("gemini-3.5-flash-lite", 1000, 400, 60) - (180 + 12 + 150) / 1e6) < 1e-12


def test_grade_normalise_et_alternatives():
    assert R.grade("Livraison : 4.90 €, offerte dès 60 €", ["4,90", "60"])
    assert R.grade("Les codes ne se cumulent pas.", ["un seul|ne se cumulent pas"])
    assert not R.grade("Livraison payante", ["4,90"])


def test_cache_semantique_seuil():
    c = R.SemanticCache(threshold=0.9)
    c.put(R.unit([1, 0]), "A")
    assert c.get(R.unit([1, 0.1]))[0] == "A"      # cosinus ~0,995
    assert c.get(R.unit([0, 1]))[0] is None       # orthogonal


def test_routeur_garde_le_petit_modele_si_confiant():
    cl = client({R.SMALL_MODEL: 0.95, R.BIG_MODEL: 0.9})
    res = run(R.Router(cl).answer("q"))
    assert res.route == "small" and cl.aio.models.calls == [R.SMALL_MODEL]
    assert res.ttft > 0 and res.calls[0].output_tokens == 60


def test_routeur_escalade_puis_cache():
    cl = client({R.SMALL_MODEL: 0.3, R.BIG_MODEL: 0.9})
    rt = R.Router(cl, R.SemanticCache())
    v = R.unit([1, 0])
    assert run(rt.answer("q", v)).route == "escalated"
    again = run(rt.answer("q bis", R.unit([1, 0.05])))
    assert again.route == "cache" and again.cost == 0
    assert cl.aio.models.calls == [R.SMALL_MODEL, R.BIG_MODEL]


def test_budget_bloque_l_escalade():
    cl = client({R.SMALL_MODEL: 0.3, R.BIG_MODEL: 0.9})
    res = run(R.Router(cl, max_cost=1e-6).answer("q"))
    assert res.route == "small"


def test_bench_router_complet():
    cl = client({R.SMALL_MODEL: 0.95, R.BIG_MODEL: 0.9})
    cl.aio.models.embed_content = same_vector
    q01, r01 = bench.QUESTIONS[0], bench.QUESTIONS[12]  # r01 reformule q01
    rows, _ = run(bench.run_router(cl, [q01, r01], 2))
    s = bench.summarize("router", rows, 1.0)
    assert s["n"] == 2 and s["qualite"] == 1.0 and s["cache"] == 1 and s["appels_llm"] == 1


def test_percentiles():
    vals = list(range(1, 101))
    assert bench.pct(vals, 50) == 50.5 and round(bench.pct(vals, 95), 2) == 95.05
