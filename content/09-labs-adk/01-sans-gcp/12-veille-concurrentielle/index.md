---
type: course
title: "Lab ADK : un agent de veille concurrentielle sourcée"
description: "Construire avec Google ADK un agent qui cherche sur le web l'actualité de vos concurrents, en extrait des signaux (prix, lancements, recrutements, partenariats) reliés à leurs sources, et produit chaque semaine une synthèse Markdown planifiée."
level: advanced
duration: "3h"
tags: [ia, adk, google-search, grounding, veille, multi-agents]
date: 2026-10-15
authors: [Youcef]
usecases: [analyse-donnees, recherche-documentaire]
platforms: [google-adk, gemini-api]
references:
  - title: "ADK : outil Google Search"
    url: https://google.github.io/adk-docs/tools/gemini-api/google-search/
  - title: "API Gemini : ancrage avec la recherche Google (grounding)"
    url: https://ai.google.dev/gemini-api/docs/google-search
    note: "groundingChunks, groundingSupports"
  - title: "ADK : systèmes multi-agents et AgentTool"
    url: https://google.github.io/adk-docs/agents/multi-agents/
  - title: "ADK : callbacks (after_tool_callback)"
    url: https://google.github.io/adk-docs/callbacks/
  - title: "Cloud Run : exécuter des jobs selon un planning"
    url: https://cloud.google.com/run/docs/execute/jobs-on-schedule
  - title: "Cloud Scheduler : documentation"
    url: https://cloud.google.com/scheduler/docs
  - title: "Tarifs de l'API Gemini (dont la recherche ancrée)"
    url: https://ai.google.dev/gemini-api/docs/pricing
---

Une équipe produit veut savoir chaque lundi matin ce que ses concurrents ont annoncé la semaine passée : baisses de prix, nouvelles offres, recrutements massifs, partenariats. Aujourd'hui, quelqu'un y passe une demi-journée. Dans ce lab, un agent ADK fait la recherche, structure les faits **avec leurs sources**, et un script met en forme une synthèse hebdomadaire prête à relire.

L'exemple porte sur trois hébergeurs cloud européens (OVHcloud, Scaleway, Hetzner), choisis parce que leur actualité est publique et abondante. Remplacez-les par vos propres concurrents dans [concurrents.json](./files/concurrents.json).

## Pour qui ?

- Vous avez déjà construit un agent ADK avec des outils fonctions.
- Vous voulez comprendre l'**ancrage** (grounding : la réponse du modèle est rattachée aux pages web qu'il a consultées) et la composition d'agents.
- Niveau avancé : callbacks, état temporaire, métadonnées d'ancrage.

## Ce que vous allez construire

```mermaid
flowchart LR
  C["concurrents.json"] --> V["Agent veilleur"]
  V -->|"AgentTool"| R["Sous-agent chercheur_web (google_search)"]
  R --> G["Métadonnées d'ancrage : URL + passages"]
  G --> CB["after_tool_callback : sources numérotées, faits reliés"]
  CB --> V
  V -->|"enregistrer_signal"| S["État : signaux + sources"]
  S --> M["rediger_rapport (Python)"]
  M --> F["rapports/veille-2026-S42.md"]
```

## Prérequis techniques

- Python 3.10 ou plus récent, une clé d'API Gemini.
- La recherche ancrée a sa propre ligne de tarif : d'après la page de tarifs consultée le 2026-10-15, elle n'est pas disponible dans le niveau gratuit pour la plupart des modèles et, en niveau payant, 5 000 requêtes de recherche par mois sont offertes (partagées entre les modèles Gemini 3 et suivants) avant facturation. Vérifiez la page avant de planifier la veille.
- [requirements.txt](./files/requirements.txt) : `google-adk==2.10.0`, `httpx`, `python-dotenv`, `pytest`.

## Programme

| Module | Leçon | Durée indicative |
| --- | --- | --- |
| 1. Le cas d'usage | La veille avec un agent : signaux, sources, architecture | 30 min |
| 2. Construire | La recherche et les sources ; les signaux et le rapport | 1h45 |
| 3. Tester et exploiter | Tests sans clé, test réel, planification (cron, Cloud Scheduler) | 45 min |

## En local ou sur Google Cloud ?

| | En local (ce lab) | Sur Google Cloud (pour aller plus loin) |
| --- | --- | --- |
| Exécution | `python veille.py` | job Cloud Run |
| Planification | `cron` sur un poste ou un serveur | Cloud Scheduler qui déclenche le job |
| Rapport | fichier `rapports/*.md` | bucket Cloud Storage, e-mail ou message d'équipe |
| Modèle | API Gemini (clé) | Vertex AI |

Code complet : [files/](./files/). Testé le 2026-10-15 avec `google-adk` 2.10.0 et `gemini-3.5-flash`.
