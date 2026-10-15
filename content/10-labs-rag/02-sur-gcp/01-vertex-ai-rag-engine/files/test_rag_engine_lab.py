"""Tests sans clé ni réseau : python -m pytest -q"""
import asyncio
import os
from types import SimpleNamespace as NS

import pytest

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projet-factice")
os.environ.setdefault("RAG_CORPUS", "projects/p/locations/europe-west4/ragCorpora/123")

import rag_engine_lab as lab


def test_chunking_valide_et_refuse_un_chevauchement_trop_grand():
    cfg = lab.chunking(300, 50)
    assert cfg.chunking_config.chunk_size == 300 and cfg.chunking_config.chunk_overlap == 50
    with pytest.raises(ValueError):
        lab.chunking(100, 100)


def test_format_contexts_garde_le_nom_du_fichier():
    resp = NS(contexts=NS(contexts=[NS(source_uri="gs://b/docs/notes-de-frais.md", score=0.27149, text="Plafonds")]))
    assert lab.format_contexts(resp) == [{"source": "notes-de-frais.md", "score": 0.271, "texte": "Plafonds"}]


def _chunk(name):
    return NS(retrieved_context=NS(uri=f"gs://b/docs/{name}"))


def test_cited_sources_ne_garde_que_les_morceaux_cites():
    gm = NS(grounding_chunks=[_chunk("a.md"), _chunk("b.md"), _chunk("a.md")],
            grounding_supports=[NS(grounding_chunk_indices=[2, 0])])
    assert lab.cited_sources(gm) == ["a.md"]          # b.md récupéré mais pas cité
    assert lab.cited_sources(NS(grounding_chunks=[_chunk("a.md")], grounding_supports=None)) == []
    assert lab.cited_sources(None) == []


def test_l_agent_ajoute_l_outil_retrieval_natif_a_la_requete():
    from google.adk.models.llm_request import LlmRequest
    import agent
    req = LlmRequest(model="gemini-2.5-flash")
    asyncio.run(agent.recherche_documents.process_llm_request(tool_context=None, llm_request=req))
    store = req.config.tools[-1].retrieval.vertex_rag_store
    assert store.rag_corpora == [os.environ["RAG_CORPUS"]] and store.similarity_top_k == 4
