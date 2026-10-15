---
type: course
title: "FAQ de SAV : citations obligatoires et refus"
description: "Construire un assistant de service client qui répond avec la FAQ en citant ses sources, dit « je ne sais pas » hors périmètre grâce à un seuil calibré, et journalise les questions non couvertes ; version chaîne simple et version agent ADK."
level: intermediate
duration: "3h"
tags: [rag, adk, support, citations, evaluation, garde-fous]
date: 2026-10-15
authors: [Youcef]
usecases: [support-client, recherche-documentaire]
platforms: [gemini-api, google-adk]
references:
  - title: "Embeddings avec l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/embeddings
    note: "Préfixes de tâche de gemini-embedding-2 et envoi par lots"
  - title: "Agent Development Kit (ADK) : documentation"
    url: https://google.github.io/adk-docs/
  - title: "ADK : outils sous forme de fonctions"
    url: https://google.github.io/adk-docs/tools/function-tools/
    note: "Comment la docstring devient la description de l'outil"
  - title: "ADK : évaluer un agent"
    url: https://google.github.io/adk-docs/evaluate/
  - title: "Ragas: Automated Evaluation of Retrieval Augmented Generation"
    url: https://arxiv.org/abs/2309.15217
  - title: "Limites de débit de l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/rate-limits
---

Un assistant de service après-vente (SAV) qui invente un délai de remboursement coûte plus cher qu'un assistant qui n'existe pas. Ce lab construit un assistant pour **Roue Libre**, une boutique **fictive** de vélos électriques, avec trois garde-fous mesurés :

1. un **seuil de pertinence** : si aucune entrée de FAQ n'est assez proche de la question, on refuse **sans appeler le modèle** ;
2. des **citations obligatoires** `[FAQ-xx]`, vérifiées par du code : une réponse sans citation, ou qui cite une entrée non récupérée, est remplacée par un refus ;
3. un **journal des questions non couvertes**, pour savoir quelles entrées ajouter à la FAQ.

## Ce que vous allez construire

```mermaid
flowchart LR
  Q["Question client"] --> A["Agent ADK sav_roue_libre"]
  A --> T["Outil rechercher_faq"]
  T --> S{"meilleur score >= seuil ?"}
  S -- "non" --> L["questions_non_couvertes.jsonl"]
  S -- "non" --> HP["hors_perimetre"]
  S -- "oui" --> R["entrées FAQ + scores"]
  HP --> A
  R --> A
  A --> V{"citations valides ?"}
  V -- "oui" --> OK["réponse citée"]
  V -- "non" --> NS["Je ne sais pas + formulaire de contact"]
```

## Pour qui ?

- Vous avez fait le [lab 1](../01-rag-pdf-local-sqlite/index.md) ou vous savez ce que sont un embedding et une similarité cosinus.
- Vous voulez comprendre comment rendre un RAG **prudent** et le prouver par des chiffres.
- Première rencontre avec ADK (*Agent Development Kit*, le framework d'agents de Google) : tout est expliqué.

## Prérequis

- Python 3.10+, une clé d'API Gemini dans `.env` (voir [.env.example](./files/.env.example)).
- `pip install -r requirements.txt` ([requirements.txt](./files/requirements.txt)) : google-genai, google-adk, numpy.

## Programme

| Module | Leçon | Ce que vous faites | Fichiers |
| --- | --- | --- | --- |
| 1. Le cas d'usage | Le SAV et ses garde-fous | les 3 façons de refuser, la FAQ fictive | `faq.json` |
| 2. Construire | Index, seuil et journal | index en cache, recherche, calibration du seuil | `faq_rag.py`, `eval.py --calibrer` |
| 2. Construire | L'agent ADK et la vérification des citations | outil, instruction, runner, garde-fou | `agent.py` |
| 3. Évaluer | Évaluer et enrichir la FAQ | tests sans clé, 4 métriques, itération sur l'instruction, rapport | `test_faq.py`, `eval.py`, `golden.json` |

## En local ou sur GCP ?

| | Ce lab | Sur Google Cloud |
| --- | --- | --- |
| FAQ | `faq.json` | document dans Cloud Storage ou base de connaissances |
| Index | `faq_index.npz` (16 vecteurs) | Vertex AI RAG Engine |
| Agent | `InMemoryRunner` en local | Agent Engine ou Cloud Run |
| Journal | fichier JSONL | BigQuery ou Cloud Logging |

Le code complet : [faq_rag.py](./files/faq_rag.py), [agent.py](./files/agent.py), [eval.py](./files/eval.py), [test_faq.py](./files/test_faq.py).
