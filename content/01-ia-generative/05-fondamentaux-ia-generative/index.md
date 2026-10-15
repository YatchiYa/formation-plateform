---
type: course
title: "Les fondamentaux de l'IA générative"
description: "Comprendre en mots simples comment fonctionne un assistant comme Claude ou Gemini, ce qu'il sait faire, ses limites, et choisir un premier cas d'usage utile pour votre équipe."
level: beginner
duration: "6h"
tags: [ia, ia-generative, llm, debutant, culture-ia, bonnes-pratiques]
date: 2026-10-15
authors: [Youcef]
usecases: [assistant-interne, generation-contenu]
platforms: [claude, gemini-enterprise]
references:
  - title: "Attention Is All You Need (Vaswani et al., 2017)"
    url: https://arxiv.org/abs/1706.03762
    note: "L'article qui a introduit l'architecture Transformer, à la base des LLM actuels"
  - title: "Training language models to follow instructions with human feedback (Ouyang et al., 2022)"
    url: https://arxiv.org/abs/2203.02155
    note: "L'article de référence sur le RLHF"
  - title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)"
    url: https://arxiv.org/abs/2005.11401
    note: "L'article fondateur du RAG"
  - title: "Anthropic : guide du prompt engineering"
    url: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
  - title: "Google : stratégies de prompt pour Gemini"
    url: https://ai.google.dev/gemini-api/docs/prompting-strategies
  - title: "CNIL : intelligence artificielle"
    url: https://www.cnil.fr/fr/intelligence-artificielle
    note: "Recommandations françaises sur l'IA et les données personnelles"
  - title: "Règlement européen sur l'IA (AI Act) sur EUR-Lex"
    url: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
---

Vous entendez parler d'IA générative tous les jours, vos collègues utilisent déjà ChatGPT, Claude ou Gemini, et vous aimeriez **comprendre ce qui se passe vraiment** derrière l'écran, sans équations ni jargon. Cette formation est faite pour vous.

## Pour qui ?

- **Managers** qui doivent décider où (et où ne pas) utiliser l'IA dans leur équipe.
- **Métiers** (RH, juridique, marketing, finance, support, achats…) qui veulent gagner du temps sans prendre de risque.
- **Curieux** qui veulent enfin une explication claire.

Aucune compétence technique n'est requise. Chaque mot technique est expliqué la première fois qu'il apparaît, avec une analogie de la vie courante.

## Objectifs mesurables

À la fin de la formation, vous serez capable de :

1. **Expliquer en 2 minutes** à un collègue ce qu'est un LLM, un token et une fenêtre de contexte.
2. **Repérer** au moins 3 situations où une réponse d'IA doit être vérifiée (hallucination, information récente, calcul).
3. **Distinguer** prompt, RAG, outils et agents, et dire lequel répond à un besoin donné.
4. **Classer** une information de votre équipe en « je peux la donner à un assistant » ou « je ne dois pas ».
5. **Rédiger** la fiche d'un premier cas d'usage réaliste, prête à être présentée à votre hiérarchie.

## Prérequis

- Savoir utiliser un navigateur web.
- Idéalement, avoir accès à un assistant (Claude, Gemini, ou celui fourni par votre entreprise) pour faire les exercices. Ce n'est pas obligatoire : chaque exercice a une solution détaillée.

## Programme

| Module | Leçons | Durée indicative |
| --- | --- | --- |
| 1. Comprendre ce qu'est un LLM | Tokens et prédiction du mot suivant · Comment un modèle apprend · Fenêtre de contexte et température | 1h30 |
| 2. Ce que l'IA sait et ne sait pas faire | Hallucinations et connaissances figées · Raisonnement et multimodalité · Coûts et latence | 1h30 |
| 3. Les briques d'une application IA | Le prompt · Embeddings et RAG · Outils et agents | 1h30 |
| 4. Choisir et utiliser un assistant | Les familles de modèles · Confidentialité et bonnes pratiques | 45 min |
| 5. Projet final | Rédiger la fiche d'un premier cas d'usage | 45 min |

```mermaid
flowchart LR
  M1["1. Comprendre un LLM"] --> M2["2. Forces et limites"]
  M2 --> M3["3. Briques d'une application"]
  M3 --> M4["4. Assistant au quotidien"]
  M4 --> P["Projet : fiche cas d'usage"]
```

## Comment ça se passe

Chaque leçon contient :

- un objectif clair en début de page ;
- des schémas pour visualiser ;
- des **quiz** pour vérifier que vous avez compris (vous pouvez vous tromper, l'explication s'affiche) ;
- un **exercice pratique** avec sa solution cachée ;
- une checklist « Je sais faire » à cocher : votre progression est sauvegardée.

## Ce que vous saurez faire

À la fin, vous ne serez pas ingénieur en IA, et ce n'est pas le but. Vous saurez **poser les bonnes questions** : « cette tâche est-elle adaptée à l'IA ? », « quelles données ai-je le droit d'utiliser ? », « comment vérifier le résultat ? ». Et vous repartirez avec une **fiche de cas d'usage** concrète pour votre équipe, autour d'un assistant interne ou de la génération de contenu.
