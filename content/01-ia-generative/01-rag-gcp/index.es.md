---
title: "Construir un RAG en GCP"
description: "De la ingesta de documentos al agente en producción: Vertex AI RAG Engine, Gemini y Cloud Run."
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

Este curso te guía paso a paso en la construcción de un sistema de **generación aumentada por recuperación** (RAG) alojado íntegramente en Google Cloud.

## Qué vas a construir

Un asistente que responde a las preguntas de tus equipos a partir de la documentación interna, citando sus fuentes:

1. un **corpus de Vertex AI RAG Engine** alimentado desde Cloud Storage;
2. un **job de sincronización** en Cloud Run que reindexa los documentos modificados;
3. un **agente ADK** desplegado en Cloud Run que consulta el corpus y llama a Gemini.

## Requisitos

- Un proyecto de Google Cloud con facturación activada.
- Conocimientos básicos de Python y de línea de comandos.
