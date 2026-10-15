---
type: course
title: "Un agent ADK privé sur Cloud Run, au moindre privilège"
description: "Déployer un assistant interne ADK sur Cloud Run en service privé, avec un compte de service qui n'a que roles/aiplatform.user, l'appeler avec un jeton d'identité, lire ses journaux, puis tout supprimer."
level: advanced
duration: "2h30"
tags: [adk, cloud-run, iam, vertex-ai, deploiement, securite]
date: 2026-10-15
authors: [Youcef]
usecases: [assistant-interne]
platforms: [google-adk, vertex-ai]
references:
  - title: "ADK : déployer sur Cloud Run"
    url: https://google.github.io/adk-docs/deploy/cloud-run/
  - title: "Cloud Run : identité de service (compte de service dédié)"
    url: https://cloud.google.com/run/docs/securing/service-identity
  - title: "Cloud Run : authentifier les développeurs (jeton d'identité)"
    url: https://cloud.google.com/run/docs/authenticating/developers
  - title: "Cloud Run : journalisation et journaux structurés"
    url: https://cloud.google.com/run/docs/logging
  - title: "Vertex AI : contrôle d'accès IAM"
    url: https://cloud.google.com/vertex-ai/docs/general/access-control
  - title: "google/adk-python (code source d'ADK)"
    url: https://github.com/google/adk-python
---

# Un agent ADK privé sur Cloud Run, au moindre privilège

Un assistant interne répond aux employés sur les règles RH et IT (congés, télétravail, VPN…) et ouvre des tickets. Il ne doit **jamais** être joignable par Internet sans authentification, et s'il est compromis, il ne doit **rien pouvoir faire d'autre** qu'appeler Gemini. Ce lab vous fait construire exactement cela, de bout en bout, sur un vrai projet Google Cloud, puis tout supprimer.

## Pour qui ?

Vous savez déjà écrire un agent ADK simple (un `Agent`, un ou deux outils) et vous avez un projet Google Cloud avec la facturation activée. Vous voulez passer de « ça marche sur mon poste » à « c'est en ligne, privé et propre ».

## Ce que vous construisez

```mermaid
flowchart LR
  E["Employé (gcloud ou appli interne)"] -->|"HTTPS + jeton d'identité"| CR["Cloud Run : lab-agent-cloud-run-iam (privé)"]
  X["Internet sans jeton"] -.->|"403 Forbidden"| CR
  CR -->|"identité : compte de service dédié"| V["Vertex AI : gemini-2.5-flash"]
  CR -->|"stdout JSON"| L["Cloud Logging (journaux structurés)"]
  SA["Compte de service lab-agent-cloud-run-iam : roles/aiplatform.user seulement"] -.-> CR
```

## Prérequis

- Python 3.10+ et `gcloud` installé, connecté (`gcloud auth login` et `gcloud auth application-default login`).
- Un projet avec les API `run`, `aiplatform`, `cloudbuild`, `artifactregistry` activées et le rôle Propriétaire (ou Éditeur + Administrateur IAM) pour **créer** les ressources.
- Le code du lab : [files/](./files/agent.py) (agent, client, tests, scripts de déploiement et de nettoyage).

## Programme

| Module | Leçon | Ce que vous faites |
|---|---|---|
| 1. Cas d'usage et architecture | [Un assistant interne qui reste privé](./01-cas-d-usage/01-assistant-interne-prive.md) | menaces, choix d'architecture, rôle de chaque brique |
| 2. Construire pas à pas | [L'agent et ses journaux structurés](./02-construire/01-agent-et-journaux.md) | outils, journal JSON, tests sans clé |
| | [Compte de service au moindre privilège](./02-construire/02-compte-de-service.md) | un compte, un rôle, pourquoi pas le compte par défaut |
| 3. Déployer et exploiter | [Déployer et appeler avec un jeton](./03-deployer-exploiter/01-deployer-et-appeler.md) | `adk deploy cloud_run`, test 403 / 200, client Python |
| | [Journaux, coûts et nettoyage](./03-deployer-exploiter/02-journaux-et-nettoyage.md) | `gcloud logging read`, tout supprimer et le prouver |

## En local ou sur GCP ?

| | En local | Sur GCP (ce lab) |
|---|---|---|
| Modèle | Vertex AI via vos identifiants ADC | Vertex AI via le compte de service du service |
| Accès | votre machine seulement | URL HTTPS privée, IAM obligatoire |
| Journaux | votre terminal | Cloud Logging, filtrables |
| Coût | appels Gemini | appels Gemini + Cloud Build + quelques secondes de Cloud Run (ordre de grandeur : quelques centimes pour le lab) |

> [!WARNING]
> Ce lab crée de vraies ressources facturables. La dernière leçon les supprime toutes avec `nettoyer.sh` et montre comment le vérifier. Ne la sautez pas.
