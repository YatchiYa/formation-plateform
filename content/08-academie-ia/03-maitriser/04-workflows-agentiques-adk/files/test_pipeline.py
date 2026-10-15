"""Tests sans clé d'API : fonctions pures + pipeline complet avec un faux modèle.

pytest -q
"""
import asyncio
import re
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

from google.adk.models import BaseLlm, LlmResponse  # noqa: E402
from google.genai import types  # noqa: E402

import agent  # noqa: E402
from run_pipeline import due_diligence  # noqa: E402


RAPPORT_COMPLET = ("## Synthèse\nScore 45, niveau moyen. Contact : achats@exemple.fr\n## Risques\n- finances\n"
                   "## Recommandation\nRETENIR SOUS CONDITIONS\n## Plan d'action\n1. audit")


def _reponse(part: types.Part) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[part]))


class FauxModele(BaseLlm):
    """Imite Gemini : appelle l'outil disponible, refuse la 1re version du rapport, approuve la 2e."""

    model: str = "faux-modele"
    relectures: int = 0
    appels: int = 0

    async def generate_content_async(self, llm_request, stream=False):
        self.appels += 1
        demande = llm_request.contents[0].parts[0].text
        fournisseur = re.search(r"fournisseur : (.+)$", demande).group(1)
        outils = list(llm_request.tools_dict)
        dernier = llm_request.contents[-1]
        if any(p.function_response for p in dernier.parts or []):
            yield _reponse(types.Part(text="- résumé factuel de l'outil"))
        elif outils and outils[0].startswith("consulter_"):
            yield _reponse(types.Part(function_call=types.FunctionCall(
                name=outils[0], args={"fournisseur": fournisseur})))
        elif "approuver_rapport" in outils:
            self.relectures += 1
            if self.relectures == 1:
                yield _reponse(types.Part(text="1. Ajouter la section ## Plan d'action."))
            else:
                yield _reponse(types.Part(function_call=types.FunctionCall(name="approuver_rapport", args={})))
        elif "Rédige" in str(llm_request.config.system_instruction):
            yield _reponse(types.Part(text=RAPPORT_COMPLET))
        else:
            yield _reponse(types.Part(text="Risque financier élevé."))


def test_score_par_fournisseur():
    niveaux = {}
    for nom in ("Cartonnerie Belval", "Composants Arvenne", "Transports Kervalec"):
        s = agent.calculer_score(agent.consulter_registre(nom), agent.consulter_finances(nom),
                                 agent.consulter_reputation(nom))
        niveaux[nom] = (s["score"], s["niveau"])
    assert niveaux == {"Cartonnerie Belval": (0, "faible"), "Composants Arvenne": (45, "moyen"),
                       "Transports Kervalec": (100, "élevé")}


def test_score_indetermine_si_donnee_manquante():
    s = agent.calculer_score(agent.consulter_registre("Inconnu SA"), None, {})
    assert s["niveau"] == "indéterminé" and s["score"] is None


def test_masquage_email_et_iban():
    texte = agent.masquer("Écrire à jean.martin@exemple.fr, IBAN FR76 3000 6000 0112 3456 7890 189.")
    assert "@" not in texte and "FR76" not in texte and "[IBAN masqué]" in texte


def test_controle_outil_refuse_nom_vide():
    assert agent.controler_outil(None, {"fournisseur": "  "}, None) == {"erreur": "Nom de fournisseur invalide."}
    assert agent.controler_outil(None, {"fournisseur": "Cartonnerie Belval"}, None) is None


def test_garde_fou_budget(monkeypatch):
    monkeypatch.setattr(agent, "MAX_APPELS_LLM", 2)
    ctx = SimpleNamespace(invocation_id="inv-test", agent_name="analyste")
    assert agent.garde_fou_budget(ctx, None) is None
    assert agent.garde_fou_budget(ctx, None) is None
    bloque = agent.garde_fou_budget(ctx, None)
    assert "[garde-fou]" in bloque.content.parts[0].text


def test_pipeline_complet_avec_faux_modele():
    faux = FauxModele()
    r = asyncio.run(due_diligence("Composants Arvenne", faux))
    assert r["score"]["score"] == 45
    assert r["statut"] == "approuvé" and r["passages"] == 2   # la boucle a tourné 2 fois
    assert "[e-mail masqué]" in r["rapport"]                    # after_model_callback appliqué
    assert faux.appels == 3 * 2 + 1 + 2 * 2                     # 3 chercheurs, analyste, 2 tours de boucle


def test_pipeline_fournisseur_inconnu():
    r = asyncio.run(due_diligence("Société Imaginaire", FauxModele()))
    assert r["score"]["niveau"] == "indéterminé"


def test_verifier_rapport():
    assert agent.verifier_rapport(RAPPORT_COMPLET, {"score": 45}) == []
    manques = agent.verifier_rapport("## Synthèse\nTout va bien.", {"score": 45})
    assert "section manquante : ## Plan d'action" in manques and "le score 45 n'est pas cité" in manques


def test_approbation_refusee_si_rapport_incomplet():
    ctx = SimpleNamespace(state={"rapport": "## Synthèse\nOK", "score_risque": {"score": 45}},
                          actions=SimpleNamespace(escalate=False, skip_summarization=False))
    r = agent.approuver_rapport(ctx)
    assert r["statut"] == "refusé" and ctx.actions.escalate is False   # la boucle continue
