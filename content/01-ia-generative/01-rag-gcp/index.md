---
usecases: [recherche-documentaire]
platforms: [vertex-ai]
title: "Construire un RAG sur GCP"
description: "De l'ingestion de documents à l'agent en production : Vertex AI RAG Engine, Gemini et Cloud Run."
cover: ./images/cover.svg
tags: [rag, gcp, vertex-ai, gemini, cloud-run]
level: intermediate
duration: 4h
date: 2026-09-01
updated: 2026-10-01
authors: [Youcef]
references:
  - title: awesome-llm-apps
    url: https://github.com/Shubhamsaboo/awesome-llm-apps
    note: "Collection d'applications LLM et de RAG open source"
  - title: GoogleCloudPlatform/generative-ai
    url: https://github.com/GoogleCloudPlatform/generative-ai
    note: Notebooks officiels Vertex AI et Gemini
  - title: "Vertex AI RAG Engine : vue d'ensemble"
    url: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview
  - title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)"
    url: https://arxiv.org/abs/2005.11401
    note: Article fondateur du RAG
---

Ce cours vous guide pas à pas dans la construction d'un système de **Retrieval-Augmented Generation** (RAG) entièrement hébergé sur Google Cloud.

## Ce que vous allez construire

Un assistant qui répond aux questions de vos équipes à partir de la documentation interne, en citant ses sources :

1. un **corpus Vertex AI RAG Engine** alimenté depuis Cloud Storage ;
2. un **job de synchronisation** sur Cloud Run qui réindexe les documents modifiés ;
3. un **agent ADK** exposé sur Cloud Run, qui interroge le corpus et appelle Gemini.

## Organisation

| Module | Contenu | Durée |
| --- | --- | --- |
| Fondamentaux | Architecture RAG, embeddings, similarité | 1h30 |
| Mise en œuvre | Installation, Terraform, déploiement, récapitulatif | 2h30 |

## Prérequis

- Un projet Google Cloud avec la facturation activée.
- Des bases en Python et en ligne de commande.
- Des notions de Terraform sont un plus.

Les ressources (support PDF, guide d'installation, présentation, notebook et jeu de données) sont téléchargeables en bas de page.
