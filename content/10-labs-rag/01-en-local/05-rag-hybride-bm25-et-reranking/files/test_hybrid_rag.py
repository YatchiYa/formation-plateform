"""Tests sans clé d'API : tokenisation, BM25, RRF, fusion du reranking, métriques. Lancer : pytest -q"""
import numpy as np

from evaluate import evaluate, recall_at_k, reciprocal_rank
from hybrid_rag import HybridIndex, bm25_search, load_corpus, merge_ranking, rrf, tokenize, vector_search
from make_corpus import QUESTIONS, build_corpus


def test_tokenize_garde_les_identifiants():
    assert tokenize("Erreur HEL-6030 sur sync.batch_size, été") == ["erreur", "hel-6030", "sync.batch_size", "ete"]


def test_corpus_80_docs_et_25_questions():
    docs = build_corpus()
    assert len(docs) == 80 and len(QUESTIONS) == 25
    assert [d["id"] for d in load_corpus()] == [d["id"] for d in docs]  # corpus.jsonl à jour


def test_bm25_trouve_le_code_exact():
    docs = load_corpus()
    idx = HybridIndex(docs, np.eye(len(docs), dtype=np.float32))
    top = bm25_search(idx.bm25, "Que signifie HEL-6030 ?", 3)
    assert docs[top[0]]["id"] == "err-HEL-6030"


def test_vector_search_cosinus():
    vecs = np.array([[1, 0], [0, 1], [0.7, 0.7]], dtype=np.float32)
    assert vector_search(vecs, np.array([0, 1], dtype=np.float32), 2) == [1, 2]


def test_rrf_recompense_l_accord_des_deux_listes():
    # 7 est 2e partout : il bat 1 (1er d'une seule liste) et 9 (1er de l'autre seulement)
    assert rrf([[1, 7, 3], [9, 7, 4]])[0] == 7
    assert rrf([[1, 2]], k=60) == [1, 2]


def test_merge_ranking_ignore_les_ids_inventes():
    docs = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert merge_ranking(["c", "zzz", "c", "a"], docs, [0, 1, 2]) == [2, 0, 1]


def test_metriques():
    assert recall_at_k(["x", "a", "y"], ["a", "b"], 5) == 0.5
    assert reciprocal_rank(["x", "y", "a"], ["a"]) == 1 / 3
    assert reciprocal_rank(["x"], ["a"]) == 0.0


def test_evaluate_bm25_sans_reseau():
    docs = load_corpus()
    idx = HybridIndex(docs, np.eye(len(docs), dtype=np.float32))
    qs = [{"question": "Comment résoudre HEL-7050 ?", "relevant": ["err-HEL-7050"], "type": "identifiant"}]
    rows = evaluate(idx, qs, [None], modes=["bm25"])
    assert rows["bm25"][0]["rr"] == 1.0
