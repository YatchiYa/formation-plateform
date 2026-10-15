"""Tests sans clé d'API : un faux modèle rejoue un script de réponses.  pytest -q"""
import asyncio
import json

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import agent as a


class FauxModele(BaseLlm):
    """Renvoie, dans l'ordre, des appels d'outil (tuple) ou du texte (str)."""
    model: str = "faux"
    script: list = []
    vus: list = []  # instructions système reçues, pour vérifier l'injection de l'état

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request.config.system_instruction)
        item = self.script.pop(0)
        part = (types.Part(function_call=types.FunctionCall(name=item[0], args=item[1]))
                if isinstance(item, tuple) else types.Part(text=item))
        yield LlmResponse(content=types.Content(role="model", parts=[part]))


def itineraire(transport="T2", hebergement="H2", activites=("A1", "A2")):
    return json.dumps({"titre": "Lisbonne", "transport_id": transport, "hebergement_id": hebergement,
                       "jours": [{"jour": 1, "programme": "Alfama", "activite_ids": list(activites)}],
                       "conseils": "Chaussures confortables."})


def faux(itin):
    modeles = {
        "transport": FauxModele(script=[("chercher_transports", {"origine": "Lyon", "destination": "Lisbonne"}), "T2 à 96 EUR"]),
        "hebergement": FauxModele(script=[("chercher_hebergements", {"ville": "Lisbonne", "prix_nuit_max": 120}), "H2 à 98 EUR"]),
        "activites": FauxModele(script=[("chercher_activites", {"ville": "Lisbonne", "centres_interet": ["culture"]}), "A1, A2"]),
        "assembleur": FauxModele(script=[itin]),
    }
    return modeles, (lambda nom: modeles[nom])


def test_outils_filtrent_le_catalogue():
    assert [o["id"] for o in a.chercher_transports("lyon", "LISBONNE")["options"]] == ["T1", "T2", "T3"]
    assert [o["id"] for o in a.chercher_hebergements("Lisbonne", 100)["options"]] == ["H2", "H3"]
    assert "erreur" in a.chercher_hebergements("Lisbonne", 10)
    assert {o["categorie"] for o in a.chercher_activites("Lisbonne", ["sport"])["options"]} == {"sport"}


def test_budget_recalcule_depuis_le_catalogue():
    v = a.calculer_budget(json.loads(itineraire()), voyageurs=2, nuits=3, budget_max=900)
    assert v["postes"] == {"transport": 192, "hebergement": 294, "activites": 140}
    assert v["total"] == 626 and v["respecte"]
    v = a.calculer_budget(json.loads(itineraire("T1", "H1", ("A3", "A2"))), 2, 3, 900)
    assert v["total"] == 378 + 435 + 248 and not v["respecte"]


def test_identifiant_invente_refuse():
    v = a.calculer_budget(json.loads(itineraire(activites=("A1", "A99"))), 2, 3, 900)
    assert not v["respecte"] and "identifiant inconnu : A99" in v["erreurs"]


def test_pipeline_complet_avec_faux_modele():
    modeles, fabrique = faux(itineraire())
    etat = asyncio.run(a.planifier(a.DEMANDE_EXEMPLE, agent=a.construire(fabrique)))
    # les 3 recherches parallèles ont écrit leur clé d'état
    assert etat["transport"] == "T2 à 96 EUR" and etat["hebergement"] == "H2 à 98 EUR"
    # l'assembleur a reçu les sorties des 3 agents dans son instruction
    assert "T2 à 96 EUR" in modeles["assembleur"].vus[-1] and "A1, A2" in modeles["assembleur"].vus[-1]
    assert etat["itineraire"]["hebergement_id"] == "H2"
    assert etat["controle_budget"]["total"] == 626 and etat["controle_budget"]["respecte"]
