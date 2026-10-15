---
title: "Build a RAG on GCP"
description: "From document ingestion to a production agent: Vertex AI RAG Engine, Gemini and Cloud Run."
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

This course walks you step by step through building a **Retrieval-Augmented Generation** (RAG) system fully hosted on Google Cloud.

## What you will build

An assistant that answers your teams' questions from internal documentation, citing its sources:

1. a **Vertex AI RAG Engine corpus** fed from Cloud Storage;
2. a **sync job** on Cloud Run that re-indexes changed documents;
3. an **ADK agent** served on Cloud Run that queries the corpus and calls Gemini.

## Outline

| Module | Content | Duration |
| --- | --- | --- |
| Fundamentals | RAG architecture, embeddings, similarity | 1h30 |
| Implementation | Setup, Terraform, deployment, recap | 2h30 |

## Prerequisites

- A Google Cloud project with billing enabled.
- Basic Python and command-line skills.
- Some Terraform knowledge helps.
