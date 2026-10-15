"""Tests sans clé d'API :  pytest -q
Les garde-fous sont testés directement ; l'agent est testé avec un faux modèle scripté."""
import asyncio
import json
from pathlib import Path

import pytest
from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import garde_fous as g
from agent import BASE, INSTRUCTION, demander, executer_sql
from evaluer import QUESTIONS, meme_resultat

CON = g.connecter(BASE)


@pytest.mark.parametrize("sql", [
    "DELETE FROM clients",
    "UPDATE produits SET prix = 0",
    "DROP TABLE clients",
    "INSERT INTO clients VALUES (999, 'x', 'y', 'z', '2026-01-01')",
    "PRAGMA table_info(clients)",
    "ATTACH 'autre.db' AS autre",
    "SELECT 1; DROP TABLE clients",
    "SELECT * FROM comptes_internes",
    "SELECT name FROM sqlite_master",
    "WITH x AS (SELECT * FROM comptes_internes) SELECT * FROM x",
    "SELECT * FROM clients WHERE id IN (SELECT id FROM comptes_internes)",
    "SELECT load_extension('evil')",
    "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r) SELECT COUNT(*) FROM r",
    "SELEC * FROM clients",
    "",
])
def test_requetes_refusees(sql):
    with pytest.raises(g.RequeteRefusee):
        g.executer(CON, sql)


def test_limit_force_et_commentaires():
    r = g.executer(CON, "-- tous les clients\nSELECT * FROM clients;")
    assert r["nb_lignes"] == g.LIMITE_LIGNES and r["tronque"] is True
    r = g.executer(CON, "SELECT * FROM clients LIMIT 5")
    assert r["nb_lignes"] == 5 and r["tronque"] is False


def test_delai_maximal():
    with pytest.raises(g.RequeteRefusee, match="trop longue"):
        g.executer(CON, "SELECT COUNT(*) FROM lignes_commande a, lignes_commande b, "
                        "lignes_commande c")


def test_base_inchangee():
    assert CON.execute("SELECT COUNT(*) FROM commandes").fetchone() == (400,)


def test_schema_sans_table_sensible():
    s = g.schema(BASE)
    assert "comptes_internes" not in s and "comptes_internes" not in INSTRUCTION
    assert "lignes_commande(" in s


def test_references_valides():
    assert len(QUESTIONS) == 15
    for q in QUESTIONS:
        assert g.executer(CON, q["sql"])["nb_lignes"] >= 1, q


def test_comparaison_par_execution():
    assert meme_resultat([["Lyon", 3.0], ["Lille", 2.004]], [[7, "Lille", 2.0], [8, "Lyon", 3.0]])
    assert not meme_resultat([["Lyon", 3.0]], [["Lyon", 3.0], ["Lille", 2.0]])
    assert not meme_resultat([[42]], [[41]])


class FauxModele(BaseLlm):
    """Rejoue une liste de réponses : un appel d'outil, puis du texte."""
    script: list = []
    vus: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        yield LlmResponse(content=self.script.pop(0))


def appel(nom, **args):
    return types.Content(role="model", parts=[types.Part(
        function_call=types.FunctionCall(name=nom, args=args))])


def texte(t):
    return types.Content(role="model", parts=[types.Part(text=t)])


def test_agent_corrige_apres_refus():
    modele = FauxModele(model="faux", script=[
        appel("executer_sql", requete="SELECT * FROM comptes_internes"),
        appel("executer_sql", requete="SELECT COUNT(*) FROM clients"),
        texte("**Réponse** : 60 clients."),
    ])
    agent = Agent(name="analyste_sql", model=modele, instruction=INSTRUCTION,
                  tools=[executer_sql])
    reponse, etat = asyncio.run(demander("Combien de clients ?", agent))
    assert reponse == "**Réponse** : 60 clients."
    assert etat["refus"] == 1 and etat["dernier_resultat"]["lignes"] == [[60]]
    # Le refus a bien été renvoyé au modèle, qui a pu se corriger.
    renvoye = json.dumps([c.model_dump(mode="json") for c in modele.vus[1].contents])
    assert "Acc\\u00e8s refus\\u00e9" in renvoye or "Accès refusé" in renvoye
