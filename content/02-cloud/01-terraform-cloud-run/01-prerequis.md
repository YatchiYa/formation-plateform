---
title: Prérequis
description: Outils, structure du dépôt et agent ADK minimal.
duration: 30min
---

## Outils

| Outil | Version minimale | Vérification |
| --- | --- | --- |
| gcloud CLI | récente | `gcloud version` |
| Terraform | 1.8 | `terraform version` |
| Python | 3.11 | `python3 --version` |
| Docker | 24 | `docker version` |

## Structure du dépôt

```text
agent-adk/
├── app/
│   ├── __init__.py
│   └── agent.py
├── Dockerfile
├── requirements.txt
├── infra/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── .github/workflows/deploy.yml
```

## L'agent minimal

```python title="app/agent.py"
from google.adk.agents import Agent


def heure_serveur() -> dict:
    """Renvoie l'heure courante du serveur (UTC)."""
    from datetime import datetime, timezone
    return {"utc": datetime.now(timezone.utc).isoformat()}


root_agent = Agent(
    name="assistant_cloud",
    model="gemini-2.5-flash",
    description="Assistant qui répond aux questions sur l'infrastructure.",
    instruction="Tu es un assistant concis. Utilise les outils quand c'est utile.",
    tools=[heure_serveur],
)
```

Testez localement avec l'interface web d'ADK :

```bash
pip install google-adk
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=second-project-511608
export GOOGLE_CLOUD_LOCATION=europe-west1
adk web
```

> [!TIP]
> `adk web` découvre les agents à partir du dossier courant : lancez-le depuis la racine `agent-adk/`, le dossier `app/` doit exposer `root_agent` via `from . import agent` dans `__init__.py`.
