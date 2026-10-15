"""Tests sans clé d'API : faux embeddings et faux modèle."""
import hashlib
import json

import numpy as np
import pytest

import eval as ev
import faq_rag


def fake_embed(texts, kind="doc"):
    v = np.zeros((len(texts), 512), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in t.lower().replace("?", " ").replace(",", " ").split():
            v[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


@pytest.fixture
def idx(tmp_path):
    return faq_rag.FAQIndex(index_path=tmp_path / "i.npz", embed_fn=fake_embed)


def test_cache_reutilise_si_faq_inchangee(tmp_path):
    calls = []
    counting = lambda texts, kind="doc": calls.append(len(texts)) or fake_embed(texts, kind)
    faq_rag.FAQIndex(index_path=tmp_path / "i.npz", embed_fn=counting)
    faq_rag.FAQIndex(index_path=tmp_path / "i.npz", embed_fn=counting)
    assert calls == [16]  # le second chargement lit le cache


def test_seuil_refuse_et_journalise(idx, tmp_path):
    log = tmp_path / "log.jsonl"
    r = faq_rag.rechercher(idx, "recette de la tarte tatin", seuil=0.5, log_path=log)
    assert r["status"] == "hors_perimetre"
    assert json.loads(log.read_text())["question"] == "recette de la tarte tatin"
    ok = faq_rag.rechercher(idx, "Combien coûte la livraison ?", seuil=0.3, log_path=log)
    assert ok["status"] == "ok" and ok["resultats"][0]["id"] == "FAQ-02"


def test_verifier_citations():
    assert faq_rag.verifier_citations("Gratuit dès 60 euros [FAQ-02].", ["FAQ-02", "FAQ-01"])
    assert not faq_rag.verifier_citations("Gratuit dès 60 euros.", ["FAQ-02"])          # pas de citation
    assert not faq_rag.verifier_citations("Gratuit [FAQ-09].", ["FAQ-02"])              # id inventé
    assert faq_rag.verifier_citations("Je ne sais pas.", [])


def test_repondre_garde_fous(idx, tmp_path):
    log = tmp_path / "log.jsonl"
    q = "Combien coûte la livraison ?"
    bon = faq_rag.repondre(idx, q, lambda p: "4,90 euros, gratuit dès 60 euros [FAQ-02].", 0.3, log)
    assert not bon["refus"] and "FAQ-02" in bon["ids"]
    invente = faq_rag.repondre(idx, q, lambda p: "Gratuit pour tous [FAQ-99].", 0.3, log)
    assert invente["refus"] and invente["raison"] == "citation invalide"
    hors = faq_rag.repondre(idx, "tarte tatin pommes caramel", lambda p: 1 / 0, 0.5, log)
    assert hors["raison"] == "seuil"  # le modèle n'a même pas été appelé
    assert len(log.read_text().splitlines()) == 2


def test_rapport_regroupe(tmp_path):
    log = tmp_path / "log.jsonl"
    for q in ["Vendez-vous des trottinettes ?", "vendez vous des trottinettes", "Location ?"]:
        faq_rag.log_non_couverte(q, 0.5, log)
    assert faq_rag.rapport(log)[0] == ("vendez vous des trottinettes", 2)


def test_calibrer_et_metriques():
    golden = [{"attendu": ["A"]}, {"attendu": ["B"]}, {"attendu": []}]
    hits = [[{"id": "A", "score": 0.8}], [{"id": "C", "score": 0.7}], [{"id": "A", "score": 0.6}]]
    seuil, acc, _ = ev.calibrer(golden, hits)
    assert seuil == 0.65 and acc == 1.0
    answers = [{"refus": False, "answer": "x", "ids": ["A"]}, {"refus": True}, {"refus": True}]
    res = ev.evaluate(golden, hits, answers, lambda a, ids: True)
    assert res == {"rappel@k": 0.5, "fidelite": 1.0, "refus_corrects": 1.0, "faux_refus": 0.5}


def test_outil_de_l_agent(idx, monkeypatch, tmp_path):
    import agent
    monkeypatch.setattr(agent, "_index", idx)
    monkeypatch.setattr(faq_rag, "SEUIL", 0.3)
    monkeypatch.setattr(faq_rag, "LOG_PATH", tmp_path / "l.jsonl")
    assert agent.rechercher_faq("Combien coûte la livraison ?")["status"] == "ok"
    assert agent.agent.tools == [agent.rechercher_faq]
