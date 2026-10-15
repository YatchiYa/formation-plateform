"""Déployer UN agent du dossier agents/trio sur Agent Runtime, sans Terraform (méthode « shell »).

À quoi sert ce script
  Fait exactement ce que fait Terraform (module adk_agent) : empaquette le code, appelle l'API Agent Runtime,
  attend la fin. Google installe alors le code et fait tourner l'agent (pas d'image, pas de Docker).
  Avec --supprimer, il supprime au contraire un agent Agent Runtime (et ses sessions).

Quand l'utiliser
  - docs/12-1-1, partie 8.1 (un agent) et 8.3 (plusieurs agents) ; partie 13 (suppression) ;
  - docs/12-3, partie 3.7 (un nouvel agent) et partie C4 (agent avec OAuth :
    --env AUTH_ID=… --env GE_ENGINE=…).

Prérequis
  - Dans le dossier du projet, venv activé (source .venv/bin/activate) ; configuration chargée :
      source scripts/config.sh config/12-1-agents-dans-projet-exp.env
    Le script ne lit PAS l'environnement : les exemples passent $PROJET_AGENTS, $REGION, $PROMPT_TEMPLATE…
  - gcloud connecté (gcloud auth login) : le jeton vient de `gcloud auth print-access-token`.
  - API aiplatform.googleapis.com activée (docs/12-1-1, partie 5).
  - Droits : roles/owner, ou aiplatform.admin + iam.serviceAccountUser (pour donner le compte de service
    à l'agent).
  - Le compte de service existe déjà, avec aiplatform.user, logging.logWriter, modelarmor.user (12-1-1, 8.1).
  - Les filtres Model Armor existent (12-1-1, partie 6) : sans PROMPT_TEMPLATE, l'agent refuse de démarrer.

Utilisation
  Déployer :
    python scripts/deployer_agent_runtime.py --projet MON_PROJET --agent meteo_agent \\
        --nom meteo-agent --compte-service meteo-agent-sa@MON_PROJET.iam.gserviceaccount.com \\
        --env PROMPT_TEMPLATE=projects/…/templates/… --env RESPONSE_TEMPLATE=projects/…/templates/…

  Comme dans docs/12-1-1, 8.1 (configuration chargée) :
    K=meteo; SA=$K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
    python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent \\
        --nom $K-shell --description "$DESC" --compte-service $SA \\
        --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE

  Supprimer :
    python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --supprimer \\
        projects/NUM/locations/europe-west1/reasoningEngines/ID

  Options :
    --projet            ID du projet des agents (obligatoire), ex. --projet $PROJET_AGENTS
    --region            région d'Agent Runtime, défaut europe-west1, ex. --region $REGION
    --agent             dossier de l'agent dans agents/trio (point d'entrée <dossier>/agent.py,
                        objet agent_runtime_app), ex. --agent meteo_agent
    --nom               nom affiché dans Agent Runtime et Agent Registry, ex. --nom meteo-shell
    --description       texte montré dans la console, ex. --description "Météo réelle d'une ville…"
    --compte-service    identité d'exécution,
                        ex. --compte-service meteo-shell-sa@MON_PROJET.iam.gserviceaccount.com
    --env NOM=valeur    variable d'environnement de l'agent, répétable,
                        ex. --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env AUTH_ID=acces-drive
    --source            dossier envoyé, défaut agents/trio (tout le dossier, sauf __pycache__, .adk, .env,
                        .venv),
                        ex. --source agents/trio
    --supprimer RESSOURCE  supprime cet agent au lieu de déployer (seul --projet est alors demandé)
  --agent, --nom et --compte-service sont obligatoires pour déployer.

Ce qu'il lit / ce qu'il crée, modifie ou supprime
  Lit : le code de --source, terraform/class_methods.json (les méthodes exposées : sessions, requêtes…).
  Crée : un agent Agent Runtime (reasoningEngine) dans le projet. Sans doublon : si un agent porte déjà ce --nom,
  le script le dit (« existe déjà : … ») et ne crée rien. Nouvelle version : supprimer l'ancien (--supprimer)
  puis redéployer, ou Terraform (mise à jour sur place).
  --supprimer : DESTRUCTIF, supprime l'agent ET ses sessions (conversations), sans confirmation.
  Aucun fichier local n'est écrit.

Résultat attendu
  opération : projects/NUM/locations/europe-west1/reasoningEngines/ID/operations/OP
    en cours… 0 s
    …
  déployé : projects/NUM/locations/europe-west1/reasoningEngines/ID
  (Notez ce nom de ressource : Gemini Enterprise et scripts/query.py le demandent.
  Tester 3 à 5 minutes après.)
  Avec --supprimer : supprimé : projects/…/reasoningEngines/ID

Erreurs fréquentes et que faire
  - « --agent, --nom et --compte-service sont obligatoires pour déployer » : ajouter l'option manquante.
  - ERREUR 403 sur https://… : un droit ou l'API manque -> docs/12-1-1, parties 4 et 5.
  - ERREUR 404 sur … avec --supprimer : nom de ressource faux, ou agent déjà supprimé.
  - ÉCHEC : {… "code": 13 …} : erreur interne de Google -> relancer la commande.
  - ÉCHEC : autre message : souvent le code de l'agent ou requirements.txt -> tester d'abord en local
    (docs/12-3, partie 1.4), corriger, relancer.
  - Délai dépassé (20 minutes) : regarder la console (Agent Runtime) avant de relancer, sinon doublon.
  - Réponses « filtrée par Model Armor » juste après : rôles du compte pas encore actifs,
    attendre 2 à 5 minutes.
"""
import argparse
import base64
import gzip
import io
import json
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent


def jeton() -> str:
    """Jeton d'accès OAuth du compte connecté à gcloud (valable environ 1 heure)."""
    return subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()


def appel(methode: str, url: str, corps: dict | None = None) -> dict:
    """Appelle l'API REST Agent Runtime et renvoie la réponse JSON ; arrête le script sur une erreur HTTP."""
    # Nouveau jeton à chaque appel : le déploiement peut durer plus longtemps que la vie d'un jeton.
    req = urllib.request.Request(url, json.dumps(corps).encode() if corps is not None else None, method=methode,
                                 headers={"Authorization": "Bearer " + jeton(), "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"ERREUR {e.code} sur {url}\n{e.read().decode()[:1500]}")


def archive(dossier: Path) -> str:
    """tar.gz + base64 du code (même méthode que scripts/pack.py)."""
    brut = io.BytesIO()
    with tarfile.open(fileobj=brut, mode="w") as tar:
        for chemin in sorted(dossier.rglob("*")):
            rel = chemin.relative_to(dossier)
            # Ni caches, ni état local d'adk, ni secrets locaux (.env), ni environnement Python.
            if chemin.is_file() and not {"__pycache__", ".adk", ".env", ".venv"} & set(rel.parts):
                info = tar.gettarinfo(str(chemin), arcname=str(rel))
                # Dates et propriétaires neutralisés : même code => même archive (voir pack.py).
                info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
                with chemin.open("rb") as f:
                    tar.addfile(info, f)
    return base64.b64encode(gzip.compress(brut.getvalue(), mtime=0)).decode()


def attendre(base: str, operation: str) -> dict:
    """Interroge l'opération longue toutes les 10 s jusqu'à sa fin ; renvoie sa réponse, ou arrête."""
    print(f"opération : {operation}")
    for i in range(120):  # jusqu'à 20 minutes
        op = appel("GET", f"{base}/v1/{operation}")
        if op.get("done"):
            if "error" in op:
                sys.exit(f"ÉCHEC : {json.dumps(op['error'], ensure_ascii=False)}\n"
                         "(Error code 13 : erreur interne de Google ; relancer la commande.)")
            return op.get("response", {})
        print(f"  en cours… {i * 10} s", flush=True)
        time.sleep(10)
    sys.exit("Délai dépassé : regarder la console (Agent Runtime) avant de relancer.")


def main():
    """Lit les options, puis supprime (--supprimer) ou déploie l'agent et affiche son nom de ressource."""
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--projet", required=True)
    p.add_argument("--region", default="europe-west1")
    p.add_argument("--agent", help="dossier de l'agent dans agents/trio, ex. meteo_agent")
    p.add_argument("--nom", help="nom affiché dans Agent Runtime et Agent Registry, ex. meteo-agent")
    p.add_argument("--description", default="")
    p.add_argument("--compte-service", help="identité d'exécution de l'agent")
    p.add_argument("--env", action="append", default=[], help="variable d'environnement NOM=valeur (répétable)")
    p.add_argument("--source", default=str(ICI / "agents" / "trio"))
    p.add_argument("--supprimer", metavar="RESSOURCE", help="projects/…/reasoningEngines/ID à supprimer")
    a = p.parse_args()
    # Point d'accès régional de l'API (Agent Runtime fait partie de Vertex AI / aiplatform).
    base = f"https://{a.region}-aiplatform.googleapis.com"

    if a.supprimer:
        # force=true : supprime aussi les sessions ; sans lui, l'API refuse dès que l'agent a servi.
        op = appel("DELETE", f"{base}/v1/{a.supprimer}?force=true")
        attendre(base, op["name"]) if op.get("name") and not op.get("done") else None
        print(f"supprimé : {a.supprimer}")
        return
    if not (a.agent and a.nom and a.compte_service):
        p.error("--agent, --nom et --compte-service sont obligatoires pour déployer")

    # Pas de doublon : un agent de même nom affiché dans le projet -> on s'arrête (il faudrait le supprimer d'abord).
    existants = appel("GET", f"{base}/v1/projects/{a.projet}/locations/{a.region}/reasoningEngines").get("reasoningEngines", [])
    deja = next((e["name"] for e in existants if e.get("displayName") == a.nom), None)
    if deja:
        sys.exit(f"existe déjà : {deja}\n(nouvelle version : --supprimer {deja} puis relancer, ou Terraform)")

    # « NOM=valeur » -> {"name": NOM, "value": valeur} ; coupé au 1er « = » (une valeur peut en contenir).
    env = [{"name": k, "value": v} for k, v in (e.split("=", 1) for e in a.env)]
    # Même corps que la ressource Terraform google_vertex_ai_reasoning_engine (module adk_agent).
    corps = {
        "displayName": a.nom,
        "description": a.description,
        "spec": {
            "agentFramework": "google-adk",
            "serviceAccount": a.compte_service,
            "classMethods": json.loads((ICI / "terraform" / "class_methods.json").read_text()),
            "sourceCodeSpec": {
                "inlineSource": {"sourceArchive": archive(Path(a.source))},
                "pythonSpec": {"version": "3.12", "entrypointModule": f"{a.agent}.agent",
                               "entrypointObject": "agent_runtime_app", "requirementsFile": "requirements.txt"},
            },
            "deploymentSpec": {"env": env, "minInstances": 0, "maxInstances": 2},
        },
    }
    op = appel("POST", f"{base}/v1/projects/{a.projet}/locations/{a.region}/reasoningEngines", corps)
    reponse = attendre(base, op["name"])
    # Nom de ressource : dans la réponse ; à défaut, déduit du nom de l'opération (…/operations/ID).
    print(f"déployé : {reponse.get('name') or op['name'].split('/operations/')[0]}")


if __name__ == "__main__":
    main()
