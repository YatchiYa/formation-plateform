---
type: platform
title: Gemini API (Google AI Studio)
icon: "🔑"
url: https://ai.google.dev/gemini-api/docs
tags: [gemini, api, google-ai-studio]
description: "L'accès le plus simple aux modèles Gemini : une clé d'API créée dans Google AI Studio, sans projet Google Cloud."
---

## En bref

Créez une clé sur [Google AI Studio](https://aistudio.google.com/), mettez-la dans une variable d'environnement, et appelez les modèles Gemini (texte, image, audio, vidéo, embeddings) depuis Python, JavaScript ou `curl`. C'est le point de départ de la plupart des formations et des labs de ce site.

```bash
export GEMINI_API_KEY="votre-clé"   # jamais dans le code ni dans git
pip install google-genai
```

Pour passer à l'échelle (quotas, résidence des données, IAM, VPC-SC), le même code bascule sur **Vertex AI** avec `GOOGLE_GENAI_USE_VERTEXAI=TRUE`.
