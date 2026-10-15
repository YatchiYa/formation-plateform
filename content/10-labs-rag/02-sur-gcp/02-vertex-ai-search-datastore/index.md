---
type: course
title: "Vertex AI Search : data store, recherche filtrée et réponses citées"
description: "Créer par l'API un data store Vertex AI Search alimenté depuis Cloud Storage, une application de recherche, obtenir des réponses résumées avec citations et des filtres sur les métadonnées, comprendre le lien avec Gemini Enterprise, puis tout supprimer."
level: advanced
duration: "2h30"
tags: [rag, vertex-ai-search, discovery-engine, gemini-enterprise, cloud-storage, gcp]
date: 2026-10-15
authors: [Youcef]
usecases: [recherche-documentaire]
platforms: [vertex-ai, gemini-enterprise]
references:
  - title: "Vertex AI Search : documentation"
    url: https://docs.cloud.google.com/generative-ai-app-builder/docs
  - title: "Préparer les données (documents non structurés et métadonnées)"
    url: https://docs.cloud.google.com/generative-ai-app-builder/docs/prepare-data
  - title: "Filtrer la recherche sur les métadonnées"
    url: https://docs.cloud.google.com/generative-ai-app-builder/docs/filter-search-metadata
  - title: "Obtenir des réponses et des relances (API answer)"
    url: https://docs.cloud.google.com/generative-ai-app-builder/docs/answer
  - title: "Emplacements de Vertex AI Search"
    url: https://docs.cloud.google.com/generative-ai-app-builder/docs/locations
  - title: "Gemini Enterprise : connecteurs et data stores"
    url: https://docs.cloud.google.com/gemini/enterprise/docs/connectors/introduction-to-connectors-and-data-stores
  - title: "Tarifs"
    url: https://cloud.google.com/generative-ai-app-builder/pricing
---

**Vertex AI Search** est le moteur de recherche d'entreprise de Google Cloud (son API s'appelle **Discovery Engine**). Là où RAG Engine vous donne des briques (corpus, passages, outil pour Gemini), Vertex AI Search vous donne un **moteur complet** : index, classement, extraits, filtres, et une réponse générée avec ses citations. C'est aussi le moteur sur lequel s'appuie **Gemini Enterprise**.

Dans ce lab, vous créez **tout par l'API Python** (pas de console) pour la société fictive Nimbus Conseil : un data store de 5 documents avec métadonnées, une application de recherche, des requêtes avec réponse citée et filtres, puis la suppression vérifiée de chaque ressource.

## Pour qui ?

- Développeurs Python à l'aise avec Google Cloud (`gcloud`, IAM de base).
- Vous savez ce qu'est le RAG ; idéalement vous avez fait le lab [Vertex AI RAG Engine](../01-vertex-ai-rag-engine/index.md).

## Ce que vous construisez

```mermaid
flowchart LR
  D["docs/*.txt + metadata.jsonl"] -->|"upload"| G["Bucket lab-vais-…"]
  G -->|"import_documents"| DS["Data store lab-vais-docs (eu)"]
  DS --> APP["Application lab-vais-app (Enterprise + LLM)"]
  Q["Question + filtre"] --> S["search : documents classés"]
  Q --> A["answer_query : réponse + citations"]
  S --> APP
  A --> APP
  APP -.->|"même moteur"| GE["Gemini Enterprise"]
```

## Prérequis

- Python 3.10+, `pip install -r files/requirements.txt` (dont `google-cloud-discoveryengine`).
- `gcloud auth application-default login` et l'API `discoveryengine.googleapis.com` activée.
- Un projet avec facturation. Vertex AI Search n'existe qu'en **multi-région** (`global`, `eu`, `us`) : on prend `eu`.

## Programme

| Module | Leçon | Durée |
|---|---|---|
| 1. Cas d'usage et architecture | [Vertex AI Search, RAG Engine et Gemini Enterprise](./01-cas-usage-et-architecture/01-cas-usage-et-architecture.md) | 30 min |
| 2. Construire pas à pas | [Data store, schéma et import depuis GCS](./02-construire-pas-a-pas/01-data-store-et-import.md) | 40 min |
| | [Application, réponses citées et filtres](./02-construire-pas-a-pas/02-application-reponses-filtres.md) | 40 min |
| 3. Tester et exploiter | [Tests, Gemini Enterprise, coûts et nettoyage](./03-tester-et-exploiter/01-tests-gemini-enterprise-nettoyage.md) | 40 min |

## En local ou sur GCP ?

| | En local | Sur GCP (ce lab) |
|---|---|---|
| `pytest` (JSONL, filtres, analyse des réponses) | Oui, sans réseau | — |
| Data store, application, requêtes | — | Oui, ADC + projet de quota |
| Durée | secondes | ≈ 6 min de création, puis l'index répond tout de suite |

Code complet : [vais_lab.py](./files/vais_lab.py), [test_vais_lab.py](./files/test_vais_lab.py), documents fictifs dans `files/docs/`.
