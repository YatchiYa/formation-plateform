"""Agent SRE en LECTURE SEULE : lit Cloud Logging et Cloud Monitoring, regroupe, corrèle, propose.

Il n'a aucun outil d'écriture. Son compte de service n'a que roles/logging.viewer et roles/monitoring.viewer.
Variables : GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI=TRUE, MODEL.
"""
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

load_dotenv()

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
FENETRE_CORRELATION = timedelta(minutes=5)


def _projet() -> str:
    return os.environ["GOOGLE_CLOUD_PROJECT"]


@lru_cache
def _logging():
    from google.cloud import logging as cloud_logging
    return cloud_logging.Client(project=_projet())


@lru_cache
def _monitoring():
    from google.cloud import monitoring_v3
    return monitoring_v3.MetricServiceClient()


# ---------- fonctions pures (testées sans GCP) ----------

def signature(message: str) -> str:
    """Remplace ce qui varie (nombres, identifiants) pour regrouper les messages « identiques »."""
    s = re.sub(r"[0-9a-f]{8,}", "<id>", message.lower())
    s = re.sub(r"\d+(\.\d+)?", "<n>", s)
    return s.strip()[:120]


def regrouper(entrees: list[dict]) -> list[dict]:
    """entrees : [{horodatage: datetime, severite, source, message}] -> groupes triés par volume."""
    groupes: dict[tuple, dict] = {}
    for e in entrees:
        cle = (e["source"], signature(e["message"]))
        g = groupes.setdefault(cle, {"source": e["source"], "signature": cle[1], "exemple": e["message"],
                                     "severite": e["severite"], "nombre": 0,
                                     "premier": e["horodatage"], "dernier": e["horodatage"]})
        g["nombre"] += 1
        g["premier"], g["dernier"] = min(g["premier"], e["horodatage"]), max(g["dernier"], e["horodatage"])
    return sorted(groupes.values(), key=lambda g: (-g["nombre"], g["premier"]))


def correler(groupes: list[dict]) -> list[dict]:
    """Deux groupes de sources différentes qui démarrent à moins de 5 min d'écart sont probablement liés ;
    celui qui commence en premier est la cause probable. (Corrélation n'est pas causalité : c'est un indice.)"""
    liens = []
    # Limite connue : double boucle O(n²) sur les groupes, suffisant pour quelques dizaines de groupes
    for a in groupes:
        for b in groupes:
            if a["source"] != b["source"] and a["premier"] <= b["premier"] \
                    and b["premier"] - a["premier"] <= FENETRE_CORRELATION and a is not b:
                liens.append({"cause_probable": f"{a['source']} : {a['exemple'][:80]}",
                              "consequence": f"{b['source']} : {b['exemple'][:80]}",
                              "ecart_secondes": int((b["premier"] - a["premier"]).total_seconds())})
    return liens


def _texte(payload) -> str:
    if isinstance(payload, dict):
        return str(payload.get("message") or payload.get("textPayload") or payload)
    return str(payload)


def _source(entree) -> str:
    labels = entree.resource.labels or {}
    return (labels.get("service_name") or (entree.labels or {}).get("service")
            or labels.get("function_name") or entree.resource.type)


# ---------- outils de l'agent (lecture seule) ----------

def lire_erreurs(heures: int = 1, journal: str = "", max_entrees: int = 200) -> dict:
    """Lit les entrées de sévérité ERROR ou plus des dernières heures, les regroupe et les corrèle.

    Args:
        heures: profondeur de recherche, de 1 à 72.
        journal: nom de journal à cibler (ex. « lab-supervision ») ; vide = tout le projet.
        max_entrees: nombre maximal d'entrées lues (200 par défaut, 1000 au plus).
    """
    heures, max_entrees = max(1, min(int(heures), 72)), max(1, min(int(max_entrees), 1000))
    depuis = (datetime.now(timezone.utc) - timedelta(hours=heures)).isoformat()
    filtre = f'severity>=ERROR AND timestamp>="{depuis}"'
    if journal:
        filtre += f' AND logName="projects/{_projet()}/logs/{journal}"'
    from google.cloud import logging as cloud_logging
    entrees = [{"horodatage": e.timestamp, "severite": e.severity, "source": _source(e), "message": _texte(e.payload)}
               for e in _logging().list_entries(filter_=filtre, order_by=cloud_logging.DESCENDING,
                                                max_results=max_entrees, page_size=max_entrees)]
    groupes = regrouper(entrees)
    liens = correler(groupes)
    for g in groupes:
        g["premier"], g["dernier"] = g["premier"].isoformat(), g["dernier"].isoformat()
    return {"filtre": filtre, "entrees_lues": len(entrees), "groupes": groupes[:10], "correlations": liens[:10]}


def compter_par_severite(heures: int = 1, journal: str = "") -> dict:
    """Compte les entrées de journal par sévérité via la métrique Cloud Monitoring logging.googleapis.com/log_entry_count.

    Args:
        heures: profondeur, de 1 à 72.
        journal: nom de journal à cibler ; vide = tout le projet.
    """
    from google.cloud import monitoring_v3
    heures = max(1, min(int(heures), 72))
    fin = datetime.now(timezone.utc)
    filtre = 'metric.type="logging.googleapis.com/log_entry_count"'
    if journal:
        filtre += f' AND metric.labels.log="{journal}"'
    series = _monitoring().list_time_series(request={
        "name": f"projects/{_projet()}",
        "filter": filtre,
        "interval": monitoring_v3.TimeInterval(start_time=fin - timedelta(hours=heures), end_time=fin),
        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
    })
    totaux: dict[str, int] = defaultdict(int)
    for s in series:
        totaux[s.metric.labels.get("severity", "?")] += sum(int(p.value.int64_value) for p in s.points)
    return {"metrique": "logging.googleapis.com/log_entry_count", "heures": heures, "par_severite": dict(totaux),
            "note": "les points de métrique arrivent avec quelques minutes de retard"}


root_agent = Agent(
    name="sre_lecture_seule",
    # Réessais avec attente sur 429/503 : le quota Vertex AI est partagé par le projet
    model=Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2)),
    description="Analyse les erreurs récentes du projet et propose des remédiations, sans rien modifier.",
    instruction=(
        "Tu es un ingénieur SRE (fiabilité des sites) en LECTURE SEULE sur un projet Google Cloud. Réponds en français. "
        "1) Appelle lire_erreurs puis compter_par_severite avec les mêmes paramètres. "
        "2) Rends un rapport court : « Résumé » (2 phrases), « Incidents » (un point par groupe : source, nombre, "
        "période), « Corrélations » (en t'appuyant uniquement sur le champ correlations, en disant que c'est un indice), "
        "« Remédiations proposées » (3 actions concrètes au plus, avec la commande gcloud à faire valider par un humain). "
        "Tu n'exécutes jamais rien et tu n'inventes aucune donnée absente des outils."
    ),
    tools=[lire_erreurs, compter_par_severite],
)
