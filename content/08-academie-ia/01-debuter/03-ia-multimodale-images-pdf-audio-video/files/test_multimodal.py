"""Tests SANS clé ni réseau : un faux client remplace Gemini.   pytest -q"""
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from google.genai import errors

import multimodal as mm

ICI = Path(__file__).parent

TICKET_OK = {"type": "ticket", "commercant": "BOULANGERIE DU CANAL", "date": "2026-10-14",
             "numero": "004521", "lignes": [{"libelle": "Croissant", "montant": 2.6},
                                            {"libelle": "Café", "montant": 6.9}],
             "total_ttc": 9.5, "tva": 0.86, "devise": "EUR", "lisible": True}


class FauxClient:
    """Imite client.models.generate_content et client.files.*"""

    def __init__(self, textes, erreurs=0):
        self.textes, self.erreurs, self.appels = list(textes), erreurs, []
        self.models = NS(generate_content=self._generer)
        self.supprimes = []
        self.files = NS(upload=lambda file, config: NS(name="files/x1", state=NS(name="ACTIVE")),
                        get=lambda name: NS(name=name, state=NS(name="ACTIVE")),
                        delete=lambda name: self.supprimes.append(name))

    def _generer(self, model, contents, config):
        self.appels.append(contents)
        if self.erreurs:
            self.erreurs -= 1
            raise errors.APIError(503, {"error": {"message": "surchargé"}})
        return NS(text=self.textes.pop(0),
                  usage_metadata=NS(prompt_token_count=1000, candidates_token_count=100))


def test_justificatif_coherent():
    res = mm.analyser_justificatif(FauxClient([json.dumps(TICKET_OK)]), ICI / "ticket.png")
    assert res["justificatif"]["total_ttc"] == 9.5
    assert res["alertes"] == []


def test_justificatif_incoherent_genere_des_alertes():
    faux = dict(TICKET_OK, total_ttc=12.0, date="14/10/2026", lisible=False)
    res = mm.analyser_justificatif(FauxClient([json.dumps(faux)]), ICI / "ticket.png")
    texte = " ".join(res["alertes"])
    assert "somme des lignes 9.5 != total 12.0" in texte
    assert "mauvais format" in texte and "vérification humaine" in texte


def test_json_invalide_leve_une_erreur():
    with pytest.raises(Exception):
        mm.analyser_justificatif(FauxClient(['{"type": "ticket"}']), ICI / "ticket.png")


def test_mime_et_choix_inline_ou_files():
    assert mm.mime_of("a.PDF") == "application/pdf"
    assert mm.mime_of("memo.wav") == "audio/wav"
    assert not mm.doit_uploader(ICI / "ticket.png")          # petite image -> inline
    assert mm.doit_uploader(ICI / "tuto.mp4")                # vidéo -> API Files
    assert mm.doit_uploader(ICI / "rapport.pdf", forcer_files=True)


def test_pdf_via_files_puis_nettoyage():
    resume = {"titre": "T", "resume": "R", "points_cles": ["a"], "chiffres_cles": ["412 000 EUR (page 1)"]}
    client = FauxClient([json.dumps(resume)])
    res = mm.resumer_pdf(client, ICI / "rapport.pdf", via_files=True)
    assert res["titre"] == "T" and res["tokens"] == {"entree": 1000, "sortie": 100}
    mm.nettoyer(client)
    assert client.supprimes == ["files/x1"] and mm.ENVOYES == []


def test_comparaison_etiquette_chaque_image():
    client = FauxClient(["Image 2 est la facture"])
    mm.comparer_images(client, [ICI / "ticket.png", ICI / "facture.png"])
    contenu = client.appels[0]
    assert contenu[0] == "Image 1 :" and contenu[2] == "Image 2 :"


def test_reessai_sur_503(monkeypatch):
    monkeypatch.setattr(mm.time, "sleep", lambda s: None)
    client = FauxClient(["ok"], erreurs=2)
    assert mm.transcrire(client, ICI / "memo.wav")["texte"] == "ok"
    assert len(client.appels) == 3
