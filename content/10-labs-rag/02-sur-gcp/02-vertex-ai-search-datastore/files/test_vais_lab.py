"""Tests sans clé ni réseau : python -m pytest -q"""
import json
import os

import pytest

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "projet-factice")

from google.cloud import discoveryengine_v1 as de

import vais_lab as lab


def test_jsonl_une_ligne_par_document_avec_metadonnees_et_lien_gcs():
    lignes = [json.loads(x) for x in lab.jsonl_lines("mon-bucket", ["onboarding", "notes-de-frais"]).splitlines()]
    assert lignes[0]["id"] == "onboarding" and lignes[0]["structData"]["categorie"] == "rh"
    assert lignes[1]["content"] == {"mimeType": "text/plain", "uri": "gs://mon-bucket/docs/notes-de-frais.txt"}


def test_tous_les_documents_ont_un_fichier():
    assert all((lab.DOCS / f"{n}.txt").exists() for n in lab.METADATA)


def test_build_filter():
    assert lab.build_filter() == ""
    assert lab.build_filter("rh", 2026) == 'categorie: ANY("rh") AND annee >= 2026'
    with pytest.raises(ValueError):
        lab.build_filter('rh") OR categorie: ANY("finance')  # tentative d'injection refusée


def test_requetes_visent_l_application_et_portent_le_filtre():
    s = lab.search_request("télétravail", "annee >= 2026")
    a = lab.answer_request("télétravail", "annee >= 2026")
    assert s.serving_config.endswith("/engines/lab-vais-app/servingConfigs/default_search")
    assert s.filter == a.search_spec.search_params.filter == "annee >= 2026"
    assert a.answer_generation_spec.include_citations and a.answer_generation_spec.answer_language_code == "fr"


def test_parse_answer_ne_garde_que_les_sources_citees():
    ref = lambda t: de.Answer.Reference(chunk_info=de.Answer.Reference.ChunkInfo(
        content="…", document_metadata=de.Answer.Reference.ChunkInfo.DocumentMetadata(title=t)))
    ans = de.Answer(answer_text="3 jours par semaine. Le mardi est obligatoire.",
                    references=[ref("Télétravail v3"), ref("Guide d'accueil")],
                    citations=[de.Answer.Citation(start_index=0, end_index=19,
                                                  sources=[de.Answer.CitationSource(reference_id="0")])])
    out = lab.parse_answer(ans)
    assert out["sources"] == ["Télétravail v3"]          # le guide a été lu mais pas cité
    assert out["citations"][0]["passage"] == "3 jours par semaine"
