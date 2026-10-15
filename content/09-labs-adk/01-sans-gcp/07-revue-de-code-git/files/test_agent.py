"""Tests sans clé d'API : dépôt temporaire + faux modèle scripté.  pytest -q"""
import asyncio

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import agent as a
import creer_depot


class FauxModele(BaseLlm):
    model: str = "faux"
    script: list = []
    reponses_outils: list = []   # ce que les outils ont renvoyé au modèle

    async def generate_content_async(self, llm_request, stream=False):
        self.reponses_outils = [p.function_response.response for c in llm_request.contents
                                for p in c.parts or [] if p.function_response]
        nom, args = self.script.pop(0)
        yield LlmResponse(content=types.Content(role="model", parts=[
            types.Part(function_call=types.FunctionCall(name=nom, args=args))]))


@pytest.fixture(scope="module")
def depot(tmp_path_factory):
    return str(creer_depot.creer(tmp_path_factory.mktemp("d") / "depot"))


def test_lecture_seule(depot):
    assert a.fichiers_modifies(depot, "HEAD~1", "HEAD") == ["app/panier.py", "app/utilisateurs.py"]
    with pytest.raises(PermissionError):
        a.git(depot, "commit", "-m", "x")
    with pytest.raises(PermissionError):
        a.git(depot, "push")
    with pytest.raises(ValueError):
        asyncio.run(a.relire(depot, base="--output=/tmp/x"))


def test_verifier_revue_durcit_la_decision():
    revue = {"decision": "approuver", "synthese": "ok", "fichiers": [
        {"fichier": "app/panier.py", "commentaires": [
            {"ligne": 7, "categorie": "securite", "gravite": "bloquant", "message": "m", "correctif": "c"}]},
        {"fichier": "/etc/passwd", "commentaires": []}]}
    v = a.verifier_revue(revue, ["app/panier.py"])
    assert v["decision"] == "demander_modifications" and v["decision_modifiee"]
    assert v["fichiers_ecartes"] == ["/etc/passwd"] and v["validation_humaine_requise"]


def test_agent_complet_avec_faux_modele(depot):
    revue = {"synthese": "Injection SQL.", "decision": "approuver", "fichiers": [
        {"fichier": "app/utilisateurs.py", "commentaires": [
            {"ligne": 7, "categorie": "securite", "gravite": "bloquant", "message": "Injection SQL",
             "correctif": 'conn.execute("... = ?", (email,))'}]}]}
    faux = FauxModele(script=[
        ("lister_fichiers_modifies", {}),
        ("lire_diff", {"fichier": "../../etc/passwd"}),          # tentative hors du diff
        ("lire_fichier", {"fichier": "app/utilisateurs.py"}),
        ("set_model_response", revue),                           # réponse finale structurée
    ])
    v = asyncio.run(a.relire(depot, agent=a.construire(faux)))
    assert "M\tapp/panier.py" in faux.reponses_outils[0]["fichiers"]
    assert faux.reponses_outils[1]["erreur"].startswith("refusé")
    assert "   7     cur = conn.execute(f\"SELECT" in faux.reponses_outils[2]["contenu"]
    assert v["decision"] == "demander_modifications" and v["decision_modifiee"]
