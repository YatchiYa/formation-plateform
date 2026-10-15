---
type: course
title: "Contrats : découpage par structure et métadonnées"
description: "Construire un RAG sur des contrats qui découpe par articles et clauses, filtre par type, partie et date, répond aux questions comparatives par un tableau cité et produit un récapitulatif des contrats en sortie structurée."
level: advanced
duration: "3h30"
tags: [rag, chunking, metadonnees, contrats, sortie-structuree, evaluation]
date: 2026-10-15
authors: [Youcef]
usecases: [recherche-documentaire, analyse-donnees, assistant-interne]
platforms: [gemini-api]
references:
  - title: "Embeddings avec l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/embeddings
  - title: "Sortie structurée (JSON) avec l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/structured-output
    note: "response_schema avec un modèle pydantic : utilisé pour les filtres et le tableau"
  - title: "sqlite3 : module de la bibliothèque standard Python"
    url: https://docs.python.org/3/library/sqlite3.html
  - title: "Lost in the Middle: How Language Models Use Long Contexts (Liu et al., 2023)"
    url: https://arxiv.org/abs/2307.03172
    note: "Pourquoi envoyer des morceaux ciblés plutôt que des contrats entiers"
  - title: "Ragas: Automated Evaluation of Retrieval Augmented Generation"
    url: https://arxiv.org/abs/2309.15217
  - title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)"
    url: https://arxiv.org/abs/2005.11401
---

Un contrat n'est pas un texte comme les autres : il est **structuré** (articles, clauses numérotées), il a une **identité** (référence, type, parties, date de signature) et les questions qu'on lui pose sont souvent **comparatives** (« quels préavis dans nos contrats de prestation ? »). Un RAG qui découpe tous les 500 caractères et ignore cette identité se trompe de contrat ou coupe une clause en deux.

Ce lab travaille sur 5 contrats **fictifs** d'Atelier Nova (location d'entrepôt, maintenance logicielle, nettoyage, licence, accord de confidentialité).

## Ce que vous allez construire

```mermaid
flowchart LR
  T["contrats/*.txt"] --> P["parse_contract : en-tête + articles + clauses"]
  P --> M[("SQLite : contrats (type, parties, date)")]
  P --> CS["chunk_structure : 1 morceau par article"]
  CS --> E["embeddings + titre du contrat"]
  E --> CH[("SQLite : chunks")]
  Q["Question"] --> F["extraire_filtres (sortie structurée)"]
  F --> S["search : WHERE type/partie/date puis cosinus"]
  CH --> S
  M --> S
  S --> G["Gemini : réponse ou tableau cité [CT-... art. N]"]
  M --> R["tableau : récapitulatif de tous les contrats"]
```

## Pour qui ?

- Vous avez fait les labs [1](../01-rag-pdf-local-sqlite/index.md) et [2](../02-faq-support-citations-et-refus/index.md), ou vous avez déjà écrit un RAG simple.
- Vous travaillez sur des documents structurés (contrats, politiques, normes, cahiers des charges).

## Prérequis

- Python 3.10+, une clé d'API Gemini dans `.env` (voir [.env.example](./files/.env.example)).
- `pip install -r requirements.txt` ([requirements.txt](./files/requirements.txt)) : google-genai, numpy, pydantic.

## Programme

| Module | Leçon | Ce que vous faites | Fichiers |
| --- | --- | --- | --- |
| 1. Le cas d'usage | Contrats et architecture | structure d'un contrat, questions types, corpus fictif | `make_contracts.py` |
| 2. Construire | Découper par structure | parseur, articles et clauses, comparaison avec un découpage par taille | `contrats_rag.py` |
| 2. Construire | Filtres, comparaisons et tableau | self-query, filtres SQL, un résultat par contrat, métadonnées dans le contexte, récapitulatif | `contrats_rag.py` |
| 3. Évaluer | Évaluer et exploiter | tests sans clé, rappel taille vs structure, filtres corrects, fidélité, refus | `eval.py`, `golden.json`, `test_contrats.py` |

## En local ou sur GCP ?

| | Ce lab | Sur Google Cloud |
| --- | --- | --- |
| Contrats | fichiers texte | PDF dans Cloud Storage, extraits par Document AI |
| Métadonnées et filtres | colonnes SQLite + `WHERE` | métadonnées de Vertex AI Search ou filtres de Vector Search |
| Tableau récapitulatif | sortie structurée Gemini | idem, résultat écrit dans BigQuery |

Code complet : [contrats_rag.py](./files/contrats_rag.py), [eval.py](./files/eval.py), [test_contrats.py](./files/test_contrats.py), [make_contracts.py](./files/make_contracts.py).
