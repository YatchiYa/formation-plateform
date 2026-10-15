"""Tests sans clé ni réseau : python -m pytest -q"""
import os
from types import SimpleNamespace as NS

import pytest

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projet-factice")

import agent
import bq_rag


def test_split_sections_recopie_l_en_tete_dans_chaque_morceau():
    md = "# Titre\nVersion 3\n\n## A\ntexte a\n\n## B\ntexte b"
    morceaux = bq_rag.split_sections(md)
    assert len(morceaux) == 2 and all(m.startswith("# Titre\nVersion 3") for m in morceaux)
    assert bq_rag.split_sections("# Sans section") == ["# Sans section"]


def test_tous_les_documents_sont_decoupes():
    rows = bq_rag.rows_from_docs()
    assert {r["doc"] for r in rows} == set(bq_rag.METADATA) and len({r["id"] for r in rows}) == len(rows)


def test_build_query_sans_filtre():
    sql, params = bq_rag.build_query(top_k=3)
    assert "VECTOR_SEARCH" in sql and "WHERE" not in sql and "top_k => 3" in sql and params == {}


def test_build_query_filtres_passes_en_parametres():
    sql, params = bq_rag.build_query("rh", 2026)
    assert "WHERE categorie = @categorie AND annee >= @annee_min" in sql
    assert params == {"categorie": "rh", "annee_min": 2026}
    with pytest.raises(ValueError):
        bq_rag.build_query("rh' OR 1=1 --")  # injection : refusée avant d'atteindre BigQuery


def _ctx():
    return NS(state={})


def test_outil_transmet_les_filtres_et_limite_le_nombre_de_recherches(monkeypatch):
    appels = []
    monkeypatch.setattr(bq_rag, "search", lambda q, c, a: appels.append((q, c, a)) or [
        {"titre": "T", "annee": 2026, "distance": 0.2, "texte": "x", "doc": "d"}])
    ctx = _ctx()
    out = agent.rechercher_documents("télétravail jours", ctx, categorie="rh", annee_min=2026)
    assert appels == [("télétravail jours", "rh", 2026)] and out["resultats"][0]["titre"] == "T"
    agent.rechercher_documents("autre", ctx)                     # 2e recherche : autorisée, sans filtre
    assert appels[-1] == ("autre", None, None)
    assert "erreur" in agent.rechercher_documents("encore", ctx)  # 3e : refusée
    assert len(appels) == 2


def test_outil_renvoie_l_erreur_de_categorie_au_modele(monkeypatch):
    monkeypatch.setattr(bq_rag, "search", lambda q, c, a: bq_rag.build_query(c, a))
    assert "catégorie inconnue" in agent.rechercher_documents("x", _ctx(), categorie="juridique")["erreur"]


def test_le_parametre_tool_context_est_cache_au_modele():
    from google.adk.tools import FunctionTool
    decl = FunctionTool(agent.rechercher_documents)._get_declaration()
    schema = decl.parameters_json_schema  # ADK 2.10 : schéma JSON (decl.parameters vaut None)
    assert set(schema["properties"]) == {"requete", "categorie", "annee_min"} and schema["required"] == ["requete"]


def test_budget_remis_a_zero_a_chaque_question_dans_le_vrai_runner(monkeypatch):
    """Boucle ADK réelle avec un faux modèle qui veut chercher 3 fois par question."""
    import asyncio
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    class FauxModele(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            debut = max(i for i, c in enumerate(llm_request.contents)
                        if c.role == "user" and any(p.text for p in c.parts))
            n = sum(1 for c in llm_request.contents[debut:] for p in c.parts if p.function_response)
            part = (types.Part(function_call=types.FunctionCall(name="rechercher_documents", args={"requete": f"q{n}"}))
                    if n < 3 else types.Part(text="fin"))
            yield LlmResponse(content=types.Content(role="model", parts=[part]))

    monkeypatch.setattr(bq_rag, "search", lambda q, c, a: [{"titre": "T", "annee": 2026, "distance": 0.1, "texte": q}])
    monkeypatch.setattr(agent.root_agent, "model", FauxModele(model="faux"))

    async def run():
        runner = InMemoryRunner(agent=agent.root_agent, app_name="t")
        s = await runner.session_service.create_session(app_name="t", user_id="u")
        vu = []
        for question in ("première", "seconde"):
            async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=types.Content(
                    role="user", parts=[types.Part(text=question)])):
                vu += [list(p.function_response.response) for p in (ev.content.parts if ev.content else [])
                       if p.function_response]
        return vu

    # 2 recherches acceptées puis 1 refusée, pour CHAQUE question (« temp: » repart de zéro)
    assert asyncio.run(run()) == [["resultats"], ["resultats"], ["erreur"]] * 2
