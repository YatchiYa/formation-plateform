"""Déploie assistant_it sur Vertex AI Agent Engine, avec un Memory Bank.

    python deployer.py        # 5 à 15 minutes ; écrit etat_deploiement.json
Crée : 1 bucket de staging + 1 instance Agent Engine (nommés lab-agent-engine-memory-bank*).
Supprimez TOUT ensuite avec :  python nettoyer.py
"""
import json
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
SLUG = "agent-engine-memory-bank"
PROJET = os.environ.get("GOOGLE_CLOUD_PROJECT", "votre-projet")
REGION = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
LABELS = {"formation-lab": SLUG}
ETAT = Path(__file__).with_name("etat_deploiement.json")
ICI = Path(__file__).parent


def configuration(bucket: str) -> dict:
    """Configuration Agent Engine sobre : 1 instance au plus, 1 vCPU, 1 Gio, 0 au repos."""
    return {
        "display_name": f"lab-{SLUG}",
        "description": "Lab formation : assistant IT avec Memory Bank (à supprimer).",
        "labels": LABELS,
        "staging_bucket": bucket,
        "requirements": ["google-cloud-aiplatform[agent_engines,adk]==1.165.1",
                         "google-adk==2.10.0"],
        "extra_packages": ["agent_memoire.py"],          # le module de l'agent, envoyé tel quel
        "env_vars": {"MODEL": os.environ.get("MODEL", "gemini-2.5-flash")},
        "min_instances": 0, "max_instances": 1,
        "resource_limits": {"cpu": "1", "memory": "1Gi"},
        "context_spec": {"memory_bank_config": {
            "ttl_config": {"default_ttl": f"{30 * 24 * 3600}s"},   # oubli automatique : 30 jours
        }},
    }


def creer_bucket() -> str:
    from google.cloud import storage
    nom = f"lab-{SLUG}-{secrets.token_hex(3)}"
    b = storage.Bucket(storage.Client(project=PROJET), nom)
    b.labels = LABELS
    b.iam_configuration.uniform_bucket_level_access_enabled = True
    b.create(location=REGION)
    return f"gs://{nom}"


def main():
    import vertexai
    from vertexai.agent_engines import AdkApp

    from agent_memoire import root_agent

    os.chdir(ICI)                                         # extra_packages : chemins relatifs
    vertexai.init(project=PROJET, location=REGION)
    bucket = creer_bucket()
    ETAT.write_text(json.dumps({"bucket": bucket}))       # noté AVANT : nettoyable même si échec
    print("Bucket de staging :", bucket)
    client = vertexai.Client(project=PROJET, location=REGION)
    distant = client.agent_engines.create(agent=AdkApp(agent=root_agent, app_name="assistant_it"),
                                          config=configuration(bucket))
    nom = distant.api_resource.name
    ETAT.write_text(json.dumps({"bucket": bucket, "agent_engine": nom}))
    print("Agent Engine déployé :", nom)


if __name__ == "__main__":
    main()
