---
type: course
title: "Planificateur de voyage multi-agents"
description: "Construire avec Google ADK un pipeline qui lance trois agents de recherche en parallèle (transport, hébergement, activités), assemble un itinéraire structuré puis vérifie le budget en Python."
level: advanced
duration: "3h"
tags: [ia, adk, multi-agents, parallelagent, sequentialagent, gemini]
date: 2026-10-15
authors: [Youcef]
usecases: [assistant-interne, automatisation-processus]
platforms: [google-adk, gemini-api]
references:
  - title: "ADK : agents séquentiels (SequentialAgent)"
    url: https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/
  - title: "ADK : agents parallèles (ParallelAgent)"
    url: https://google.github.io/adk-docs/agents/workflow-agents/parallel-agents/
  - title: "ADK : agents personnalisés (BaseAgent)"
    url: https://google.github.io/adk-docs/agents/custom-agents/
  - title: "ADK : l'état de session (state)"
    url: https://google.github.io/adk-docs/sessions/state/
  - title: "ADK : Workflows, le successeur des agents de workflow"
    url: https://google.github.io/adk-docs/workflows/
  - title: "Gemini API : sortie structurée"
    url: https://ai.google.dev/gemini-api/docs/structured-output
  - title: "google/adk-python (code source)"
    url: https://github.com/google/adk-python
---

Organiser un déplacement, c'est trois recherches **indépendantes** (comment y aller, où dormir, quoi faire) suivies d'un travail d'**assemblage** et d'une **vérification** du budget. C'est exactement la forme d'un pipeline multi-agents : on parallélise ce qui est indépendant, on enchaîne ce qui dépend du reste, et on confie au code ce qui doit être exact.

Dans ce lab, vous construisez ce pipeline avec **Google ADK** (Agent Development Kit, le framework open source de Google pour écrire des agents en Python) et un modèle **Gemini** appelé avec une simple clé d'API. Les données (vols, hôtels, activités) sont **fictives** et servies par des outils Python : tout tourne sur votre poste.

## Ce que vous allez construire

```mermaid
flowchart LR
  U["Demande : Lyon vers Lisbonne, 2 voyageurs, 3 nuits, 900 EUR"] --> P
  subgraph P["ParallelAgent recherches"]
    T["transport + outil chercher_transports"]
    H["hebergement + outil chercher_hebergements"]
    A["activites + outil chercher_activites"]
  end
  P --> S["assembleur (sortie structurée Itineraire)"]
  S --> B["controle_budget (code Python, sans LLM)"]
  B --> R["Itinéraire + verdict budgétaire"]
```

- **Un `ParallelAgent`** lance les trois spécialistes en même temps ; chacun écrit son résultat dans l'**état de session** (un dictionnaire partagé).
- **Un assembleur** lit ces trois résultats et produit un itinéraire **validé par un schéma Pydantic**.
- **Un agent personnalisé** (`BaseAgent`) recalcule le coût à partir du catalogue, jamais à partir des chiffres écrits par le modèle.

## Pour qui ?

- Développeurs Python à l'aise avec `async`/`await`, les dictionnaires et `pip`.
- Vous avez déjà écrit un agent ADK simple avec un outil (sinon, commencez par un lab ADK de niveau intermédiaire).

## Prérequis

- Python 3.10 ou plus récent, `pip install -r files/requirements.txt` (google-adk 2.10.0).
- Une clé d'API Gemini créée dans Google AI Studio, placée dans un fichier `.env` (modèle : [.env.example](./files/.env.example)).
- Aucune connaissance de Google Cloud n'est nécessaire.

## Programme

| Module | Leçon | Ce que vous faites |
| --- | --- | --- |
| 1. Cas d'usage et architecture | Pourquoi un pipeline parallèle puis séquentiel | Découper le problème, choisir les agents de workflow |
| 2. Construire pas à pas | Outils et agents de recherche en parallèle | Écrire les outils, les 3 spécialistes, `output_key` |
| 2. Construire pas à pas | Assembleur structuré et contrôle du budget | `output_schema`, injection d'état, `BaseAgent` déterministe |
| 3. Tester, évaluer, exploiter | Tester sans clé, exécuter pour de vrai, exploiter | Faux modèle, test réel, `adk web`, pistes de production |

## En local ou sur GCP ?

| | En local (ce lab) | Sur Google Cloud (pour aller plus loin) |
| --- | --- | --- |
| Modèle | Gemini via clé d'API (`GOOGLE_GENAI_USE_VERTEXAI=FALSE`) | Gemini via Vertex AI (`GOOGLE_GENAI_USE_VERTEXAI=TRUE` + projet) |
| Exécution | `python agent.py` ou `adk web` | Cloud Run ou Vertex AI Agent Engine |
| Données | Catalogue fictif en Python | Vos API de réservation réelles derrière les mêmes outils |
| Coût | Quelques appels au modèle | Appels au modèle + hébergement |

Le code ne change pas entre les deux : seules les variables d'environnement changent.

## Le code

Tout est dans le dossier `files/` : [agent.py](./files/agent.py), [donnees.py](./files/donnees.py), [test_agent.py](./files/test_agent.py), [requirements.txt](./files/requirements.txt).
