---
type: course
title: "Recherche web et synthèse sourcée avec Google Search"
description: "Construire avec Google ADK un agent de veille qui interroge Google Search (ancrage), découpe une question d'actualité, cite ses sources réelles et livre un rapport Markdown structuré."
level: intermediate
duration: "2h30"
tags: [ia, adk, google-search, grounding, recherche, gemini]
date: 2026-10-15
authors: [Youcef]
usecases: [recherche-documentaire, analyse-donnees]
platforms: [google-adk, gemini-api]
references:
  - title: "ADK : outil Google Search de l'API Gemini"
    url: https://adk.dev/integrations/google-search/
  - title: "ADK : limites des outils (outils intégrés et autres outils)"
    url: https://adk.dev/tools/limitations/
  - title: "ADK : Google Search Grounding"
    url: https://adk.dev/grounding/google_search_grounding/
  - title: "Gemini API : ancrage avec Google Search"
    url: https://ai.google.dev/gemini-api/docs/google-search
  - title: "ADK : types de callbacks"
    url: https://adk.dev/callbacks/types-of-callbacks/
  - title: "google/adk-python (code source)"
    url: https://github.com/google/adk-python
---

Un modèle de langage ne connaît que ce qu'il a lu pendant son entraînement. Pour répondre à « quelles sont les dernières nouveautés de X ? », il doit **chercher**. Dans ce lab, vous donnez à un agent Google ADK l'outil intégré `google_search` : Gemini lance lui-même des recherches Google et renvoie, avec sa réponse, la liste des pages utilisées (les **métadonnées d'ancrage**, ou *grounding metadata*).

Vous allez surtout apprendre à respecter une contrainte réelle d'ADK et de l'API Gemini : **un outil intégré comme `google_search` ne se mélange pas librement avec vos propres fonctions dans le même agent**. On la contourne proprement avec un sous-agent exposé comme outil (`AgentTool`).

## Pour qui ?

- Développeurs Python qui ont déjà écrit un agent ADK simple (ou suivi le lab [Assistant e-commerce](../01-assistant-ecommerce-commandes/index.md)).
- Toute personne qui doit produire des notes de veille sourcées.

## Ce que vous construisez

```mermaid
flowchart LR
  U["Question d'actualité"] --> A["analyste_recherche (agent principal)"]
  A -->|"outil fonction"| D["date_du_jour()"]
  A -->|"AgentTool, 2 à 3 fois"| C["chercheur_web (sous-agent)"]
  C -->|"seul outil"| G["google_search (intégré à Gemini)"]
  C -->|"after_model_callback"| S[("state['sources'] numérotées")]
  A --> R["Rapport Markdown : Synthèse, Points clés [n], Incertitudes, Sources"]
  S --> R
```

## Prérequis

- Python 3.10+, une clé d'API Gemini (Google AI Studio).
- `pip install -r files/requirements.txt`.

## Programme

| Module | Leçon | Ce que vous faites | Durée |
| --- | --- | --- | --- |
| 1. Cas d'usage | [Le cas d'usage et l'architecture](./01-cas-d-usage/01-cas-d-usage-et-architecture.md) | Comprendre l'ancrage et la contrainte des outils intégrés | 30 min |
| 2. Construire | [Le sous-agent de recherche](./02-construire/01-sous-agent-google-search.md) | `google_search` isolé, `AgentTool`, l'erreur 400 réelle | 40 min |
| 2. Construire | [Sources citées et rapport](./02-construire/02-sources-et-rapport.md) | Callback qui numérote les sources, rapport structuré | 40 min |
| 3. Tester et exploiter | [Tester et exploiter](./03-tester-et-exploiter/01-tester-et-exploiter.md) | Faux modèles, run réel, coûts, règles d'affichage | 40 min |

## Le code

Dans `files/` : [agent.py](./files/agent.py), [run.py](./files/run.py) (recherche réelle, écrit `rapport.md`), [test_agent.py](./files/test_agent.py) (3 tests sans clé), [requirements.txt](./files/requirements.txt) et `.env.example`.

## En local ou sur Google Cloud ?

| | En local (ce lab) | Sur Google Cloud (piste) |
| --- | --- | --- |
| Modèle et recherche | API Gemini + `google_search`, avec une clé | Vertex AI + `google_search` (même code, variables `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, projet, région) |
| Sources internes | non | `VertexAiSearchTool` sur vos documents (autre outil intégré, mêmes contraintes) |
| Hébergement | `python run.py` | `adk deploy cloud_run` |

Testé de bout en bout en local le 2026-10-15 ; la variante Google Cloud n'a pas été déployée ici.
