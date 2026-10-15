"""Tests sans clé d'API : contrôles, écritures, lecture PDF et pipeline complet avec un faux modèle.

    pytest -q
"""
import asyncio
import csv
from datetime import date

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

import generer_factures
from factures import Facture, controler, ecritures, extracteur, texte_pdf, traiter

AUJ = date(2026, 10, 15)
OK = {"numero": "F-1", "fournisseur": "Test", "date_facture": "2026-10-01", "date_echeance": "2026-10-31",
      "lignes": [{"designation": "a", "quantite": 2, "prix_unitaire_ht": 10, "montant_ht": 20},
                 {"designation": "b", "quantite": 1, "prix_unitaire_ht": 5.5, "montant_ht": 5.5}],
      "total_ht": 25.5, "taux_tva": 20, "montant_tva": 5.1, "total_ttc": 30.6}


def facture(**modifs):
    return Facture.model_validate({**OK, **modifs})


def test_facture_coherente():
    assert controler(facture(), AUJ) == ([], [])


def test_anomalies_detectees():
    assert "somme des lignes" in controler(facture(total_ht=27.5, total_ttc=32.6, montant_tva=5.5), AUJ)[0][0]
    assert any("TVA imprimée" in a for a in controler(facture(montant_tva=10.2, total_ttc=35.7), AUJ)[0])
    assert any("TTC" in a for a in controler(facture(total_ttc=31), AUJ)[0])
    assert any("taux" in a for a in controler(facture(taux_tva=19.6, montant_tva=5.0, total_ttc=30.5), AUJ)[0])
    assert controler(facture(date_echeance="2026-10-01", date_facture="2026-09-01"), AUJ)[1] == [
        "échéance dépassée depuis le 2026-10-01"]
    assert controler(facture(date_echeance=None), AUJ)[1] == ["date d'échéance absente"]


def test_ecritures_equilibrees():
    lignes = ecritures(facture())
    debit = sum(float(l["debit"] or 0) for l in lignes)
    credit = sum(float(l["credit"] or 0) for l in lignes)
    assert round(debit, 2) == round(credit, 2) == 30.6


class FauxModele(BaseLlm):
    """Renvoie un JSON tiré du texte reçu : simule l'extraction sans appeler Gemini."""
    async def generate_content_async(self, llm_request, stream=False):
        texte = llm_request.contents[-1].parts[0].text
        num = texte.split("FACTURE N° ")[1].split()[0]
        json = facture(numero=num).model_dump_json()
        yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=json)]))


def test_pipeline_complet(tmp_path, monkeypatch):
    monkeypatch.setattr(generer_factures, "DOSSIER", tmp_path / "factures")
    (tmp_path / "factures").mkdir()
    for f in generer_factures.FACTURES[:2]:
        generer_factures.dessiner(tmp_path / "factures" / f"{f[0]}.pdf", *f)
    assert "Total TTC : 165.60 EUR" in texte_pdf(tmp_path / "factures" / "F-2026-0412.pdf")

    agent = extracteur.model_copy(update={"model": FauxModele(model="faux")})
    bilan = asyncio.run(traiter(tmp_path / "factures", tmp_path / "sortie", AUJ,
                                InMemoryRunner(agent=agent, app_name="factures")))
    assert [b["numero"] for b in bilan] == ["F-2026-0412", "F-2026-0413"]
    with open(tmp_path / "sortie" / "ecritures.csv", encoding="utf-8") as fh:
        assert len(list(csv.DictReader(fh, delimiter=";"))) == 6  # 3 écritures par facture
