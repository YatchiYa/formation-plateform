"""Tests sans clé ni réseau : faux modèle, pannes simulées, reprise.  Lancer : pytest -q"""
import asyncio
import json

import batch_api
import classer
import rapport
from generer_avis import generer


class ErreurApi(Exception):
    def __init__(self, code):
        self.code = code


def faux_lot(pannes=None, appels=None):
    """Remplace l'appel au modèle : renvoie la réponse attendue, échoue sur demande."""
    pannes = pannes if pannes is not None else {}

    async def traiter_lot(client, lot):
        if appels is not None:
            appels.append([a["id"] for a in lot])
        cle = lot[0]["id"]
        if pannes.get(cle):
            pannes[cle] -= 1
            raise ErreurApi(pannes.get("code", 429))
        brut = json.dumps([{"id": a["id"], "sentiment": a["sentiment_attendu"],
                            "categorie": a["categorie_attendue"], "a_recontacter": False} for a in lot])
        return {"resultats": classer.valider(lot, brut), "tokens_in": 100, "tokens_out": 50}
    return traiter_lot


def lancer(avis, sortie, **kw):
    return asyncio.run(classer.traiter(None, avis, str(sortie), taille_lot=10, rpm=6000, **kw))


def test_generation_reproductible():
    assert generer(50, 1) == generer(50, 1) and len({a["id"] for a in generer(200, 42)}) == 200


def test_valider_filtre_les_reponses_invalides():
    lot = [{"id": "A1"}, {"id": "A2"}]
    brut = json.dumps([
        {"id": "A1", "sentiment": "positif", "categorie": "prix", "a_recontacter": False},
        {"id": "A1", "sentiment": "positif", "categorie": "prix", "a_recontacter": False},   # doublon
        {"id": "A2", "sentiment": "furieux", "categorie": "prix", "a_recontacter": True},    # hors liste
        {"id": "X9", "sentiment": "neutre", "categorie": "prix", "a_recontacter": True},     # jamais demandé
    ])
    assert [r["id"] for r in classer.valider(lot, brut)] == ["A1"]


def test_reessais_puis_succes(tmp_path, monkeypatch):
    async def sans_pause(_): pass
    monkeypatch.setattr(classer.asyncio, "sleep", sans_pause)
    avis = generer(30, 1)
    stats = lancer(avis, tmp_path / "r.jsonl", traiter_lot=faux_lot({"A0011": 2}))
    assert stats == {"lots_ok": 3, "lots_echec": 0, "avis_ok": 30}


def test_erreur_non_reessayable_abandonne_le_lot_seulement(tmp_path):
    avis = generer(30, 1)
    stats = lancer(avis, tmp_path / "r.jsonl", traiter_lot=faux_lot({"A0011": 1, "code": 400}))
    assert stats["lots_echec"] == 1 and stats["avis_ok"] == 20


def test_reprise_apres_coupure(tmp_path):
    sortie = tmp_path / "r.jsonl"
    avis = generer(50, 1)
    lancer(avis[:20], sortie, traiter_lot=faux_lot())           # 1re exécution, coupée après 20 avis
    with open(sortie, "a") as f:
        f.write('{"lot": ["A0021"], "resulta')                     # ligne tronquée par la coupure
    appels = []
    lancer(avis, sortie, traiter_lot=faux_lot(appels=appels))     # relance
    assert sum(len(x) for x in appels) == 30                       # seuls les 30 restants sont refaits
    assert classer.deja_faits(str(sortie)) == {a["id"] for a in avis}


def test_concurrence_bornee(tmp_path):
    en_vol, pic = 0, 0

    async def lent(client, lot):
        nonlocal en_vol, pic
        en_vol += 1
        pic = max(pic, en_vol)
        await asyncio.sleep(0.1)
        en_vol -= 1
        return {"resultats": [], "tokens_in": 0, "tokens_out": 0}
    lancer(generer(100, 1), tmp_path / "r.jsonl", concurrence=3, traiter_lot=lent)
    assert pic == 3


def test_rapport_et_incoherences():
    assert rapport.incoherent(1, "positif") and not rapport.incoherent(3, "positif")
    avis = {a["id"]: a for a in generer(10, 1)}
    classes = {i: {"id": i, "sentiment": a["sentiment_attendu"], "categorie": "autre",
                   "a_recontacter": True} for i, a in list(avis.items())[:8]}
    s = rapport.statistiques(avis, classes)
    assert s["avis_classes"] == 8 and len(s["manquants"]) == 2
    assert s["accord_sentiment"] == 1.0 and s["a_recontacter"] == 8


def test_format_jsonl_batch(tmp_path):
    lots = [generer(3, 1)]
    chemin = tmp_path / "in.jsonl"
    batch_api.construire_jsonl(lots, str(chemin), avec_cle=True)
    ligne = json.loads(chemin.read_text().splitlines()[0])
    assert ligne["key"] == "lot-0"
    assert ligne["request"]["generationConfig"]["responseJsonSchema"] == classer.SCHEMA
    reponse = {"candidates": [{"content": {"parts": [{"text": json.dumps([
        {"id": "A0001", "sentiment": "neutre", "categorie": "prix", "a_recontacter": False}])}]}}],
        "usageMetadata": {"promptTokenCount": 40, "candidatesTokenCount": 9}}
    lu = batch_api.lire_reponse(lots[0], reponse)
    assert lu["tokens_in"] == 40 and [r["id"] for r in lu["resultats"]] == ["A0001"]


def test_avis_oublie_refait(tmp_path):
    sortie = tmp_path / "r.jsonl"
    avis = generer(10, 1)

    async def oublie_le_dernier(client, lot):
        brut = json.dumps([{"id": a["id"], "sentiment": "neutre", "categorie": "autre",
                            "a_recontacter": False} for a in lot[:-1]])
        return {"resultats": classer.valider(lot, brut), "tokens_in": 1, "tokens_out": 1}

    lancer(avis, sortie, traiter_lot=oublie_le_dernier)
    assert len(classer.deja_faits(str(sortie))) == 9
    appels = []
    lancer(avis, sortie, traiter_lot=faux_lot(appels=appels))
    assert appels == [["A0010"]]
