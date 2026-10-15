"""Tests sans clé d'API : faux embeddings, faux modèle, faux JSON structuré."""
import hashlib

import numpy as np
import pytest

import contrats_rag as cr
import eval as ev
import make_contracts


def fake_embed(texts, kind="doc", titles=None):
    v = np.zeros((len(texts), 512), dtype=np.float32)
    for i, t in enumerate(texts):
        for w in t.lower().replace("?", " ").replace(",", " ").replace(".", " ").split():
            v[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-9)


@pytest.fixture
def db(tmp_path):
    make_contracts.build(tmp_path / "c")
    d = cr.connect(str(tmp_path / "t.db"))
    cr.index_folder(d, tmp_path / "c", fake_embed)
    return d


def test_parse_contract_metadonnees_et_articles():
    c = cr.parse_contract(make_contracts.render(make_contracts.CONTRATS[1]))
    assert (c["ref"], c["type"], c["date"]) == ("CT-2025-014", "prestation", "2025-03-12")
    assert c["parties"] == ["Atelier Nova", "DataPlume SAS"]
    assert [a["titre"] for a in c["articles"]][:2] == ["Objet", "Durée"]
    assert c["articles"][3]["clauses"][0][0] == "4.1"


def test_chunk_structure_coupe_entre_les_clauses():
    c = cr.parse_contract(make_contracts.render(make_contracts.CONTRATS[1]))
    chunks = [ch for ch in cr.chunk_structure(c) if ch["article"] == 4]
    assert len(chunks) >= 2 and chunks[1]["text"].startswith("Article 4 – Niveaux de service (suite)")
    for ch in chunks:  # chaque ligne après le titre est une clause entière
        assert all(l[:3] in {"4.1", "4.2", "4.3", "4.4", "4.5"} for l in ch["text"].splitlines()[1:])
    assert all(len(ch["text"]) <= 500 for ch in chunks)


def test_index_incremental_et_deux_strategies(db, tmp_path):
    n = dict(db.execute("SELECT strategie, COUNT(*) FROM chunks GROUP BY strategie"))
    assert n["structure"] > 20 and n["taille"] > 5
    assert cr.index_folder(db, tmp_path / "c", fake_embed)["inchanges"] == 5


def test_filtres_sql(db):
    hits = cr.search(db, "préavis résiliation", 10, filtres={"type": "prestation"}, embed_fn=fake_embed)
    assert {h["ref"] for h in hits} == {"CT-2025-014", "CT-2025-022"}
    assert cr.search(db, "x", 4, filtres={"partie": "Orbitel"}, embed_fn=fake_embed) == []
    hits = cr.search(db, "x", 4, filtres={"apres": "2025-05-01"}, embed_fn=fake_embed)
    assert {h["ref"] for h in hits} <= {"CT-2025-022", "CT-2025-040"}


def test_contexte_contient_les_metadonnees(db):
    h = cr.search(db, "redevance annuelle", 1, filtres={"partie": "Kerlogic"}, embed_fn=fake_embed)
    assert "[CT-2025-040 art." in cr.contexte(h) and "Atelier Nova / Kerlogic" in cr.contexte(h)


def test_par_contrat_garantit_chaque_contrat(db):
    hits = cr.search(db, "responsabilité plafond", filtres=None, par_contrat=1, embed_fn=fake_embed)
    assert len(hits) == 5 and len({h["ref"] for h in hits}) == 5


def test_extraire_filtres_rejette_un_type_invente(db):
    f = cr.extraire_filtres(db, "q", lambda p, s: {"type": "bail", "partie": "Kerlogic", "comparatif": False})
    assert f["type"] is None and f["partie"] == "Kerlogic"


def test_answer_refuse_sans_contrat_correspondant(db):
    r = cr.answer(db, "montant Orbitel", fake_embed, lambda p: 1 / 0,
                  lambda p, s: {"type": None, "partie": "Orbitel", "comparatif": False})
    assert r["refus"] and r["hits"] == []


def test_tableau(db):
    fake = lambda p, s: {"duree": "12 mois", "preavis_resiliation": "1 mois", "montant": "1 €", "juridiction": "Lyon"}
    t = cr.tableau(db, fake).splitlines()
    assert len(t) == 2 + 5 and t[2].startswith("| CT-2024-031 | location | SCI Les Tilleuls | 2024-06-03")


def test_metriques():
    hits = [{"ref": "A", "text": "préavis de trois (3) mois"}]
    assert ev.recall([*hits], [{"ref": "A", "preuve": "trois (3) mois"}, {"ref": "B", "preuve": "x"}]) == 0.5
    assert ev.recall(hits, [{"ref": "B", "preuve": "trois (3) mois"}]) == 0  # bon texte, mauvais contrat
    assert ev.filtres_ok({"type": None, "partie": "DataPlume"}, {"type": None, "partie": "DataPlume SAS"})
    assert not ev.filtres_ok({"type": "licence", "partie": None}, {"type": None, "partie": None})
