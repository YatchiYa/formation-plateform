"""Tests sans clé d'API : sources issues du grounding, validation des signaux, rapport, flux complet simulé.

    pytest -q
"""
import asyncio
from datetime import date

from google.adk.agents import Agent
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from veille import creer_veilleur, lancer_veille, rediger_rapport

META = types.GroundingMetadata(
    grounding_chunks=[types.GroundingChunk(web=types.GroundingChunkWeb(uri="https://exemple.test/a", title="exemple.test")),
                      types.GroundingChunk(web=types.GroundingChunkWeb(uri="https://autre.test/b", title="autre.test"))],
    grounding_supports=[types.GroundingSupport(segment=types.Segment(text="ACME baisse ses prix de 10 %."),
                                               grounding_chunk_indices=[1])])


class FauxModele(BaseLlm):
    """Rejoue un script ; une réponse peut porter des métadonnées d'ancrage, comme google_search."""
    script: list = []
    vus: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        part, meta = self.script.pop(0)
        yield LlmResponse(content=types.Content(role="model", parts=[part]), grounding_metadata=meta)


def appel(nom, **args):
    return types.Part(function_call=types.FunctionCall(name=nom, args=args)), None


def test_rapport_markdown():
    signaux = [{"concurrent": "ACME", "categorie": "prix", "resume": "Baisse de 10 %", "date": "2026-10-12", "sources": [2]}]
    sources = [{"id": 1, "titre": "non cité", "url": "https://x.test"}, {"id": 2, "titre": "autre.test", "url": "https://autre.test/b"}]
    md = rediger_rapport("Les prix baissent.", signaux, sources, date(2026, 10, 15))
    assert md.startswith("# Veille concurrentielle - semaine 42 (2026)")
    assert "| 2026-10-12 | ACME | Baisse de 10 % | [2] |" in md
    assert "2. [autre.test](https://autre.test/b)" in md and "non cité" not in md


def test_flux_complet_simule():
    sous_modele = FauxModele(model="faux", script=[(types.Part(text="- ACME baisse ses prix"), META)])
    chercheur = Agent(name="chercheur_web", model=sous_modele, instruction="cherche")
    modele = FauxModele(model="faux", script=[
        appel("chercheur_web", request="ACME actualités"),
        appel("enregistrer_signal", concurrent="ACME", categorie="prix", resume="x", date_signal="2026-10-12", source_ids=[9]),
        appel("enregistrer_signal", concurrent="ACME", categorie="prix", resume="Baisse de 10 %",
              date_signal="2026-10-12", source_ids=[2]),
        (types.Part(text="ACME mène une guerre des prix."), None)])
    md, etat = asyncio.run(lancer_veille({"secteur": "test", "concurrents": ["ACME"]}, date(2026, 10, 15),
                                         creer_veilleur(modele, chercheur)))
    reponses = [p.function_response.response for c in modele.vus[-1].contents for p in c.parts if p.function_response]
    # 1. la recherche renvoie chaque fait relié à SA source (chunk 1 -> source 2)
    assert reponses[0]["faits_sources"] == [{"texte": "ACME baisse ses prix de 10 %.", "sources": [2]}]
    # 2. une source inventée (9) est refusée, le modèle doit corriger
    assert "erreur" in reponses[1]
    assert len(etat["signaux"]) == 1 and etat["signaux"][0]["sources"] == [2]
    assert "ACME mène une guerre des prix." in md and "(https://autre.test/b)" in md
