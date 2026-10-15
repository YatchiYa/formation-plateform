"""Tests sans clé d'API : garde-fous des serveurs, filtrage des outils, appel MCP réel via un faux modèle.

    pytest -q
"""
import asyncio
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

# Base de test hors du dossier du lab, partagée avec le serveur MCP lancé en sous-processus.
DB = Path(tempfile.mkdtemp()) / "commandes.db"
os.environ["COMMANDES_DB"] = str(DB)

import commandes_server  # noqa: E402
import fichiers_server  # noqa: E402
from agent import commandes, fichiers  # noqa: E402


@pytest.fixture(autouse=True)
def base_neuve():
    commandes_server.creer_base(DB)


def test_select_autorise():
    r = commandes_server.executer_select("SELECT COUNT(*) AS n FROM commandes")
    assert r == {"colonnes": ["n"], "lignes": [(8,)], "tronque": False}


@pytest.mark.parametrize("sql", ["DELETE FROM commandes", "SELECT 1; DROP TABLE clients",
                                 "UPDATE commandes SET statut='x'"])
def test_ecritures_refusees(sql):
    assert "erreur" in commandes_server.executer_select(sql)


def test_connexion_en_lecture_seule():
    with pytest.raises(sqlite3.OperationalError):
        commandes_server._lecture_seule().execute("DELETE FROM commandes")


@pytest.mark.parametrize("nom", ["../agent.py", "/etc/passwd", "../../.env"])
def test_fichiers_hors_dossier_refuses(nom):
    with pytest.raises(ValueError):
        fichiers_server.lire_document(nom)


def test_lecture_document():
    assert "30 jours" in fichiers_server.lire_document("politique-retours.md")


def test_filtrage_des_outils_mcp():
    """Démarre les vrais serveurs MCP (sous-processus) et vérifie ce que voit le modèle."""
    async def noms():
        try:
            return ([t.name for t in await commandes.get_tools_with_prefix()], [t.name for t in await fichiers.get_tools_with_prefix()])
        finally:
            await commandes.close()
            await fichiers.close()
    cmd, docs = asyncio.run(noms())
    assert sorted(cmd) == ["executer_select", "lister_tables"]  # annuler_commande filtré
    assert sorted(docs) == ["docs_lire_document", "docs_lister_documents"]


class FauxModele(BaseLlm):
    script: list = []
    vus: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        yield LlmResponse(content=types.Content(role="model", parts=[self.script.pop(0)]))


def test_appel_outil_mcp_de_bout_en_bout():
    sql = "SELECT nom FROM clients WHERE segment='pro' ORDER BY id"
    modele = FauxModele(model="faux", script=[
        types.Part(function_call=types.FunctionCall(name="executer_select", args={"sql": sql})),
        types.Part(text="fini")])

    async def run():
        runner = InMemoryRunner(agent=Agent(name="a", model=modele, tools=[commandes]), app_name="t")
        try:
            s = await runner.session_service.create_session(app_name="t", user_id="u")
            async for _ in runner.run_async(user_id="u", session_id=s.id,
                                            new_message=types.Content(role="user", parts=[types.Part(text="?")])):
                pass
        finally:
            await runner.close()
    asyncio.run(run())
    # 2e requête au modèle : elle contient la réponse de l'outil MCP (exécuté dans le sous-processus).
    reponse = [p.function_response.response for c in modele.vus[1].contents for p in c.parts if p.function_response]
    assert "Cyclo Rapide SARL" in str(reponse) and "Atelier du Rhône" in str(reponse)
