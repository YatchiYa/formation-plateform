"""Écrit un petit incident FICTIF dans le journal « lab-supervision » (11 entrées), daté des 10 dernières minutes.

Scénario : la base « commandes-db » expire (cause), puis la passerelle renvoie des 503 (conséquence).
Supprimez ensuite le journal : gcloud logging logs delete lab-supervision --project "$PROJECT_ID" --quiet
"""
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from google.cloud import logging as cloud_logging
from google.cloud.logging import Resource

load_dotenv()

JOURNAL = "lab-supervision"


def scenario(maintenant: datetime) -> list[tuple[timedelta, str, str, str]]:
    """(décalage dans le passé, sévérité, service, message)."""
    t = []
    for i in range(4):
        t.append((timedelta(minutes=10 - i), "ERROR", "api-commandes",
                  f"Timeout: connexion à commandes-db expirée après 30 s (requête {1040 + i})"))
    for i in range(3):
        t.append((timedelta(minutes=8 - i), "ERROR", "passerelle",
                  f"HTTP 503 : upstream api-commandes indisponible (tentative {i + 1})"))
    t.append((timedelta(minutes=5), "CRITICAL", "api-commandes", "Pool de connexions épuisé : 50/50 utilisées"))
    for i in range(2):
        t.append((timedelta(minutes=4 - i), "WARNING", "passerelle", f"Latence p95 élevée : {2300 + 100 * i} ms"))
    t.append((timedelta(minutes=2), "INFO", "api-commandes", "Redémarrage du worker 3"))
    return t


def main() -> None:
    client = cloud_logging.Client(project=os.environ["GOOGLE_CLOUD_PROJECT"])
    logger = client.logger(JOURNAL, labels={"formation-lab": "supervision-cloud-logging"})
    maintenant = datetime.now(timezone.utc)
    for decalage, severite, service, message in scenario(maintenant):
        logger.log_struct({"message": message, "service": service}, severity=severite,
                          timestamp=maintenant - decalage, labels={"service": service,
                                                                   "formation-lab": "supervision-cloud-logging"},
                          resource=Resource(type="global", labels={}))
    print(f"{len(scenario(maintenant))} entrées écrites dans le journal {JOURNAL}")


if __name__ == "__main__":
    main()
