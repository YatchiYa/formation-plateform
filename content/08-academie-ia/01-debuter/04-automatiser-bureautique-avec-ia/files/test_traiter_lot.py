"""Tests SANS clé ni réseau : un faux client remplace Gemini.   pytest -q"""
import json
from pathlib import Path
from types import SimpleNamespace as NS

from google.genai import errors

import traiter_lot as tl

ICI = Path(__file__).parent


class FauxClient:
    def __init__(self, reponses):
        self.reponses, self.appels = list(reponses), 0
        self.models = NS(generate_content=self._gen)

    def _gen(self, model, contents, config):
        self.appels += 1
        r = self.reponses.pop(0)
        if isinstance(r, Exception):
            raise r
        return NS(text=json.dumps(r))


def analyse(cat="information", prio="normale"):
    return {"resume": "r", "categorie": cat, "priorite": prio, "brouillon_reponse": "Bonjour"}


def test_statut_humain_dans_la_boucle():
    assert tl.statut_pour(tl.Analyse(**analyse("reclamation"))) == "à relire en priorité"
    assert tl.statut_pour(tl.Analyse(**analyse("commande", "haute"))) == "à relire en priorité"
    assert tl.statut_pour(tl.Analyse(**analyse())) == "à valider"


def test_lot_csv_avec_limite_et_reprise(tmp_path):
    df = tl.lire(ICI / "emails.csv")
    assert len(df) == 20 and set(tl.COLONNES_IA) <= set(df.columns)
    assert tl.traiter(df, FauxClient([analyse()] * 3), limite=3) == 3
    assert list(df["statut"][:4]) == ["à valider"] * 3 + [""]
    # reprise : les 3 lignes déjà traitées ne sont pas rappelées
    client = FauxClient([analyse()] * 17)
    assert tl.traiter(df, client) == 17 and client.appels == 17
    sortie = tmp_path / "x_traite.csv"
    tl.ecrire(df, sortie)
    assert (tl.lire(sortie)["statut"] == "à valider").all()


def test_une_erreur_ne_bloque_pas_le_lot(monkeypatch):
    monkeypatch.setattr(tl.time, "sleep", lambda s: None)
    df = tl.lire(ICI / "emails.csv").head(2)
    erreur = errors.APIError(400, {"error": {"message": "mauvaise requête"}})
    tl.traiter(df, FauxClient([erreur, analyse("spam", "basse")]))
    assert df.at[0, "statut"].startswith("erreur") and df.at[1, "categorie"] == "spam"


def test_reessai_sur_429(monkeypatch):
    monkeypatch.setattr(tl.time, "sleep", lambda s: None)
    client = FauxClient([errors.APIError(429, {"error": {"message": "quota"}}), analyse()])
    assert tl.analyser(client, "o", "t").categorie == "information" and client.appels == 2


def test_excel_aller_retour(tmp_path):
    df = tl.lire(ICI / "emails.csv").head(3)
    tl.ecrire(df, tmp_path / "e.xlsx")
    assert len(tl.lire(tmp_path / "e.xlsx")) == 3
