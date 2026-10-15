"""Tests sans clé d'API : anonymisation, garde, score, permutation.  pytest -q"""
import asyncio
import json

import pytest
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

import agent as a
import evaluation as ev


class FauxModele(BaseLlm):
    model: str = "faux"
    reponse: str = ""
    appels: int = 0

    async def generate_content_async(self, llm_request, stream=False):
        self.appels += 1
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=self.reponse)]))


def reponse(note=2, preuve="FastAPI"):
    return json.dumps({"notes": [{"critere": c["id"], "note": note, "justification": "j", "preuve": preuve}
                                 for c in a.FICHE["criteres"]], "points_a_verifier": []})


@pytest.mark.parametrize("cv", a.CVS, ids=lambda c: c["id"])
def test_aucun_attribut_sensible_apres_anonymisation(cv):
    texte = a.anonymiser(cv).lower()
    assert not [t for t in a.termes_sensibles(cv) if t.lower() in texte]
    assert "loisirs" not in texte and "développeuse" not in texte and "diplômée" not in texte


@pytest.mark.parametrize("cid", list(ev.PERMUTATIONS))
def test_permutation_nom_genre_donne_la_meme_entree(cid):
    cv = next(c for c in a.CVS if c["id"] == cid)
    var = ev.permuter(cv, ev.PERMUTATIONS[cid])
    assert ev.texte_brut(var) != ev.texte_brut(cv)          # les CV bruts diffèrent bien...
    assert a.anonymiser(var) == a.anonymiser(cv)            # ...mais le modèle voit exactement la même chose


def test_garde_bloque_l_appel_si_fuite():
    faux = FauxModele(reponse=reponse())
    cv = a.CVS[0]
    with pytest.raises(PermissionError, match="Camille"):
        asyncio.run(a.evaluer_texte(ev.texte_brut(cv), a.termes_sensibles(cv), agent=a.construire(faux)))
    assert faux.appels == 0                                 # le modèle n'a jamais été appelé


def test_score_pondere_et_preuves_verifiees():
    texte = a.anonymiser(a.CVS[0])
    r = a.scorer(json.loads(reponse(3, "FastAPI")), texte)
    assert r["score"] == 100 and r["tranche"] == "fort" and r["statut"] == "en_attente_revue_humaine"
    r = a.scorer(json.loads(reponse(1, "COBOL depuis 20 ans")), texte)
    assert r["score"] == 33 and r["tranche"] == "faible" and len(r["preuves_introuvables"]) == 5


def test_pipeline_complet_avec_faux_modele(tmp_path):
    faux = FauxModele(reponse=reponse(2, "pytest"))
    r = asyncio.run(a.evaluer_cv(a.CVS[0], agent=a.construire(faux)))
    assert r["score"] == 67 and r["preuves_introuvables"] == [] and faux.appels == 1
    a.ecrire_revue_humaine([r], tmp_path / "revue.csv")
    assert "en_attente_revue_humaine" in (tmp_path / "revue.csv").read_text(encoding="utf-8")
