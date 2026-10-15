---
type: usecase
title: Interroger ses documents
icon: "📚"
level: beginner
tags: [rag, recherche-documentaire]
description: Poser une question en langage naturel et obtenir une réponse sourcée à partir de vos documents internes (Drive, SharePoint, PDF).
---

## Le besoin

L'information existe, mais elle est éparpillée dans des centaines de documents. Plutôt que de chercher par mots-clés, on veut demander : « quelle est la procédure de retour pour un client pro ? » et obtenir la réponse, avec le lien vers le document.

## La technique : le RAG

```mermaid
flowchart LR
  Q["Question"] --> S["Recherche des passages pertinents"]
  D[("Vos documents")] --> S
  S --> M["Modèle : rédige la réponse"]
  M --> R["Réponse + sources"]
```

## Par où commencer

- *Les fondamentaux de l'IA générative* (comprendre les embeddings et la recherche sémantique).
- *RAG sur vos documents Google Drive* : quatre kits prêts à déployer, testés en vrai.
- *Évaluer et fiabiliser une application LLM* : vérifier que les réponses citent les bonnes sources.
