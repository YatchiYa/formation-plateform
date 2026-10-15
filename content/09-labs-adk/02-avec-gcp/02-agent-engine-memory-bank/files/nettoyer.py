"""Supprime TOUT ce que deployer.py a créé, puis vérifie.

    python nettoyer.py
"""
import json
import time

from deployer import ETAT, LABELS, PROJET, REGION, SLUG


def main():
    import vertexai
    from google.api_core.exceptions import NotFound
    from google.cloud import storage

    etat = json.loads(ETAT.read_text()) if ETAT.exists() else {}
    client = vertexai.Client(project=PROJET, location=REGION)

    # 1. Agent Engine : force=True supprime aussi sessions et souvenirs (Memory Bank).
    noms = {etat["agent_engine"]} if etat.get("agent_engine") else set()
    noms |= {e.api_resource.name for e in client.agent_engines.list()
             if (e.api_resource.display_name or "").startswith(f"lab-{SLUG}")}
    for nom in noms:
        for essai in range(20):  # 10 minutes au plus
            try:
                client.agent_engines.delete(name=nom, force=True)
                print("Suppression demandée :", nom)
                break
            except Exception as e:  # ex. génération de souvenirs encore en cours
                if "other operations running" not in str(e) or essai == 19:
                    raise
                print("Opération en cours sur l'instance, nouvel essai dans 30 s")
                time.sleep(30)

    # 2. Buckets de staging du lab (repérés par leur label).
    gcs = storage.Client(project=PROJET)
    for b in gcs.list_buckets():
        if (b.labels or {}).get("formation-lab") == LABELS["formation-lab"]:
            try:
                b.delete(force=True)       # force : supprime d'abord les objets (< 256)
                print("Bucket supprimé :", b.name)
            except NotFound:
                pass

    # 3. Vérification (la suppression est une opération longue : on attend sa fin).
    for _ in range(20):
        restants = [e.api_resource.name for e in client.agent_engines.list()
                    if (e.api_resource.display_name or "").startswith(f"lab-{SLUG}")]
        if not restants:
            break
        time.sleep(15)
    buckets = [b.name for b in gcs.list_buckets()
               if (b.labels or {}).get("formation-lab") == LABELS["formation-lab"]]
    print("Restant :", {"agent_engines": restants, "buckets": buckets})
    if not restants and not buckets:
        ETAT.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
