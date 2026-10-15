"""Tests sans clé ni GCP : regroupement, corrélation, outils sur faux clients. Lancer : pytest -q"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import agent
import generer_logs_test

T0 = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def _entrees():
    return [{"horodatage": T0 - d, "severite": s, "source": src, "message": m}
            for d, s, src, m in generer_logs_test.scenario(T0) if s in ("ERROR", "CRITICAL")]


def test_signature_ignore_les_nombres():
    assert agent.signature("Requête 1040 expirée après 30 s") == agent.signature("Requête 1041 expirée après 30 s")


def test_regrouper_et_correler_le_scenario():
    groupes = agent.regrouper(_entrees())
    assert [(g["source"], g["nombre"]) for g in groupes[:2]] == [("api-commandes", 4), ("passerelle", 3)]
    liens = agent.correler(groupes)
    assert liens and liens[0]["cause_probable"].startswith("api-commandes : Timeout")
    assert liens[0]["consequence"].startswith("passerelle : HTTP 503")
    assert liens[0]["ecart_secondes"] == 120


def test_pas_de_correlation_au_dela_de_5_minutes():
    g = [{"source": "a", "premier": T0, "exemple": "x"}, {"source": "b", "premier": T0 + timedelta(minutes=6), "exemple": "y"}]
    assert agent.correler(g) == []


def test_lire_erreurs_construit_le_filtre_et_borne(monkeypatch):
    vus = {}

    def list_entries(filter_, order_by, max_results, page_size):
        vus.update(filtre=filter_, max=max_results)
        return [NS(timestamp=T0, severity="ERROR", payload={"message": "Timeout 1"}, labels={"service": "api"},
                   resource=NS(type="global", labels={}))]

    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "projet-test")
    monkeypatch.setattr(agent, "_logging", lambda: NS(list_entries=list_entries))
    r = agent.lire_erreurs(heures=500, journal="lab-supervision", max_entrees=10**6)
    assert 'severity>=ERROR' in vus["filtre"] and 'logName="projects/projet-test/logs/lab-supervision"' in vus["filtre"]
    assert vus["max"] == 1000
    assert r["groupes"][0]["source"] == "api" and r["entrees_lues"] == 1


def test_compter_par_severite(monkeypatch):
    serie = lambda sev, vals: NS(metric=NS(labels={"severity": sev}),
                                 points=[NS(value=NS(int64_value=v)) for v in vals])
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "projet-test")
    monkeypatch.setattr(agent, "_monitoring", lambda: NS(list_time_series=lambda request: [
        serie("ERROR", [4, 3]), serie("WARNING", [2])]))
    assert agent.compter_par_severite(1, "lab-supervision")["par_severite"] == {"ERROR": 7, "WARNING": 2}


def test_agent_sans_outil_d_ecriture():
    assert {t.__name__ for t in agent.root_agent.tools} == {"lire_erreurs", "compter_par_severite"}
