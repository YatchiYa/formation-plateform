"""Déployer (ou supprimer) l'agent « Assistant Google Sheets » sur Agent Runtime, par l'API REST (pas d'image, pas de Docker).

Appelé par « ./scripts/deployer.sh agent-runtime » ; à la main :
  python scripts/deployer_agent_runtime.py --projet P --region R --compte-service SA --env MCP_URL=… --env AUTH_ID=…
  python scripts/deployer_agent_runtime.py --projet P --region R --trouver            # chemin de l'agent, ou rien
  python scripts/deployer_agent_runtime.py --projet P --supprimer projects/…/reasoningEngines/ID

Envoie le dossier agent/ (point d'entrée sheets_agent.agent, objet agent_runtime_app), attend la fin (5 à 10 min),
affiche « déployé : projects/NUM/locations/REGION/reasoningEngines/ID » : c'est le chemin à coller dans Gemini Enterprise.
Pas de doublon : un agent nommé déjà « sheets-agent » => le script le dit et ne crée rien (supprimer puis relancer).
Repris et simplifié du projet 09 (scripts/deployer_agent_runtime.py).
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
NOM = "sheets-agent"


def appel(methode: str, url: str, corps: dict | None = None) -> dict:
    jeton = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
    req = urllib.request.Request(url, json.dumps(corps).encode() if corps is not None else None, method=methode,
                                 headers={"Authorization": "Bearer " + jeton, "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"ERREUR {e.code} sur {url}\n{e.read().decode()[:1500]}")


def attendre(base: str, operation: str) -> dict:
    print(f"opération : {operation}")
    for i in range(120):  # 20 minutes
        op = appel("GET", f"{base}/v1/{operation}")
        if op.get("done"):
            if "error" in op:
                sys.exit(f"ÉCHEC : {json.dumps(op['error'], ensure_ascii=False)} (code 13 = erreur interne : relancer)")
            return op.get("response", {})
        print(f"  en cours… {i * 10} s", flush=True)
        time.sleep(10)
    sys.exit("Délai dépassé : regarder la console (Agent Runtime) avant de relancer.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projet", required=True)
    p.add_argument("--region", default="europe-west1")
    p.add_argument("--compte-service")
    p.add_argument("--env", action="append", default=[], help="NOM=valeur (répétable)")
    p.add_argument("--trouver", action="store_true", help="affiche le chemin de l'agent déployé (rien s'il n'existe pas)")
    p.add_argument("--supprimer", metavar="RESSOURCE")
    a = p.parse_args()
    base = f"https://{a.region}-aiplatform.googleapis.com"
    liste = f"{base}/v1/projects/{a.projet}/locations/{a.region}/reasoningEngines"

    if a.supprimer:
        op = appel("DELETE", f"{base}/v1/{a.supprimer}?force=true")   # force : supprime aussi les sessions
        attendre(base, op["name"]) if op.get("name") and not op.get("done") else None
        print(f"supprimé : {a.supprimer}")
        return
    deja = next((e["name"] for e in appel("GET", liste).get("reasoningEngines", []) if e.get("displayName") == NOM), None)
    if a.trouver:
        print(deja or "")
        return
    if deja:
        sys.exit(f"existe déjà : {deja}\n(nouvelle version : --supprimer {deja}, puis relancer)")
    if not a.compte_service:
        p.error("--compte-service est obligatoire pour déployer")

    sys.path.insert(0, str(ICI / "agent"))
    from carte import DESCRIPTION  # noqa: E402
    archive = subprocess.run([sys.executable, str(ICI / "scripts" / "pack.py")], input=json.dumps(
        {"src": str(ICI / "agent"), "only": "sheets_agent,requirements.txt"}), capture_output=True, text=True, check=True)
    corps = {
        "displayName": NOM, "description": DESCRIPTION,
        "spec": {
            "agentFramework": "google-adk", "serviceAccount": a.compte_service,
            "classMethods": json.loads((ICI / "agent" / "class_methods.json").read_text()),
            "sourceCodeSpec": {
                "inlineSource": {"sourceArchive": json.loads(archive.stdout)["archive"]},
                "pythonSpec": {"version": "3.12", "entrypointModule": "sheets_agent.agent",
                               "entrypointObject": "agent_runtime_app", "requirementsFile": "requirements.txt"}},
            "deploymentSpec": {"env": [{"name": k, "value": v} for k, v in (e.split("=", 1) for e in a.env)],
                               "minInstances": 0, "maxInstances": 2},
        },
    }
    op = appel("POST", liste, corps)
    reponse = attendre(base, op["name"])
    print(f"déployé : {reponse.get('name') or op['name'].split('/operations/')[0]}")


if __name__ == "__main__":
    main()
