"""Tests sans clé d'API :  pytest -q
Règles de modération testées directement ; agents et callbacks testés avec un faux modèle."""
import asyncio
from pathlib import Path

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from agent import BLOQUE, CANAUX, creer_agent, decliner, rapport
from moderation import masquer_donnees_personnelles, promesses_interdites

ICI = Path(__file__).parent


@pytest.mark.parametrize("texte,type_", [
    ("écrire à lea.dupont@exemple.fr", "email"),
    ("appeler le 06 12 34 56 78", "telephone"),
    ("ou le +33 6 12 34 56 78", "telephone"),
    ("IBAN FR76 3000 6000 0112 3456 7890 189", "iban"),
    ("carte 4970 1012 3456 7890", "carte"),
])
def test_donnees_personnelles_masquees(texte, type_):
    masque, trouves = masquer_donnees_personnelles(texte)
    assert type_ in trouves and f"[{type_.upper()}]" in masque


def test_pas_de_faux_positif():
    texte = "Froid 24 h, chaud 12 h, 500 ml, 29,90 € jusqu'au 30/11/2026."
    assert masquer_donnees_personnelles(texte) == (texte, [])
    assert promesses_interdites(texte) == []
    assert promesses_interdites("Une finition soigneusement contrôlée.") == []


@pytest.mark.parametrize("texte", [
    "Garantie à vie !", "100 % efficace", "Zéro risque pour vous",
    "La meilleure gourde du marché", "Un effet miracle", "Elle guérit la fatigue",
])
def test_promesses_detectees(texte):
    assert promesses_interdites(texte)


class FauxModele(BaseLlm):
    """Répond selon le nom de l'agent appelant ; garde chaque requête reçue."""
    reponses: dict = {}
    vus: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.vus.append(llm_request)
        consignes = str(llm_request.config.system_instruction)
        canal = next(c for c, (_, txt) in CANAUX.items() if txt in consignes)
        yield LlmResponse(content=types.Content(role="model", parts=[
            types.Part(text=self.reponses[canal])]))


def lancer(brief, reponses):
    modele = FauxModele(model="faux", reponses=reponses, vus=[])
    etat = asyncio.run(decliner(brief, creer_agent(model=modele)))
    return modele, etat


def test_brief_propre_et_masquage():
    reponses = {c: f"Texte {c} : gourde Clairo à 29,90 €." for c in CANAUX}
    modele, etat = lancer((ICI / "brief_produit.md").read_text(encoding="utf-8"), reponses)
    assert len(modele.vus) == 4                         # un appel par canal
    for req in modele.vus:                              # le modèle n'a jamais vu le contact
        vu = str([c.model_dump() for c in req.contents])
        assert "lea.dupont@exemple.fr" not in vu and "06 12 34 56 78" not in vu
        assert "[EMAIL]" in vu and "[TELEPHONE]" in vu
    for c in CANAUX:
        assert etat[f"texte_{c}"] == reponses[c]
        assert etat[f"moderation_{c}"][0]["etape"] == "entrée : masquage"


def test_brief_piege_bloque_avant_le_modele():
    modele, etat = lancer((ICI / "brief_piege.md").read_text(encoding="utf-8"), {})
    assert modele.vus == []                             # aucun appel : 0 token
    for c in CANAUX:
        assert etat[f"texte_{c}"].startswith(BLOQUE)
    assert "BLOQUÉ" in rapport(etat)


def test_sortie_bloquee_sur_un_seul_canal():
    reponses = {c: "Texte sobre." for c in CANAUX}
    reponses["instagram"] = "La gourde garantie à vie ! Écrivez à jean@exemple.fr"
    _, etat = lancer("Brief : gourde Clairo 500, 29,90 €.", reponses)
    assert etat["texte_instagram"].startswith(BLOQUE)
    assert etat["moderation_instagram"][-1]["motif"] == ["garantie absolue", "email"]
    assert all(etat[f"texte_{c}"] == "Texte sobre." for c in CANAUX if c != "instagram")
