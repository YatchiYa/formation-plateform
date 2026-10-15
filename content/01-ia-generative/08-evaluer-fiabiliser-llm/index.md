---
type: course
title: "Évaluer et fiabiliser une application LLM"
description: "Construire un jeu de données doré, mesurer un assistant RAG avec des métriques et un LLM-juge, le protéger en production et bloquer les régressions en CI."
level: advanced
duration: "7h"
tags: [ia, evaluation, llm, rag, observabilite, mlops]
date: 2026-10-15
authors: [Youcef]
usecases: [recherche-documentaire, support-client, assistant-interne]
platforms: [vertex-ai, claude]
references:
  - title: "Anthropic : Define success criteria and build evaluations"
    url: https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests
    note: "Méthode Anthropic pour écrire des cas de test et des évaluations notées par code, humain ou modèle"
  - title: "Vertex AI : Gen AI evaluation service overview"
    url: https://cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-overview
    note: "Service d'évaluation de Vertex AI (métriques calculées et métriques basées sur un modèle)"
  - title: "RAGAS : Automated Evaluation of Retrieval Augmented Generation (Es et al., 2023)"
    url: https://arxiv.org/abs/2309.15217
  - title: "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., 2023)"
    url: https://arxiv.org/abs/2306.05685
  - title: "G-Eval : NLG Evaluation using GPT-4 with Better Human Alignment (Liu et al., 2023)"
    url: https://arxiv.org/abs/2303.16634
  - title: "OWASP Top 10 for Large Language Model Applications"
    url: https://owasp.org/www-project-top-10-for-large-language-model-applications/
  - title: "Anthropic : Building effective agents"
    url: https://www.anthropic.com/research/building-effective-agents
---

Une démo qui « marche bien » sur cinq questions n'est pas une application fiable. Dès qu'on change un prompt, un modèle ou un découpage de documents, la qualité peut baisser **sans que personne ne s'en aperçoive**. Cette formation vous apprend à transformer l'impression « ça a l'air bien » en **chiffres reproductibles**, puis à protéger l'application en production et à bloquer automatiquement les régressions.

> [!NOTE]
> Fil rouge : **un assistant RAG interne** qui répond aux questions des salariés sur les procédures RH et IT, déployé sur Vertex AI (Gemini) ou sur l'API Claude. Tous les exemples sont fictifs.

## Pour qui ?

- Développeurs et ingénieurs ML qui ont déjà mis un RAG ou un chatbot en ligne et veulent le rendre **mesurable**.
- Tech leads qui doivent décider « peut-on passer au nouveau modèle ? » avec autre chose qu'une intuition.
- Product owners d'assistants de support client ou de recherche documentaire qui veulent un **contrat de qualité** avec l'équipe technique.

## Prérequis

- Python à l'aise (fonctions, JSON, `pytest` ou équivalent).
- Avoir appelé un LLM par API (Gemini sur Vertex AI ou Claude).
- Connaître le principe d'un RAG (découpage, embeddings, recherche, génération).
- Notions de CI (GitHub Actions, GitLab CI ou Cloud Build).

## Objectifs mesurables

À la fin de la formation, vous serez capable de :

1. Rédiger avec le métier une **définition de « bonne réponse »** et un jeu de données doré d'au moins 30 cas.
2. Choisir, pour chaque critère, la méthode adaptée : **métrique exacte, heuristique, LLM-juge ou humain**.
3. Écrire une **grille de LLM-juge** et en mesurer l'accord avec un humain.
4. Mesurer séparément **la recherche** (rappel, pertinence du contexte) et **la génération** (fidélité) d'un RAG.
5. Ajouter à une application des **garde-fous**, une **sortie structurée validée**, des **retries**, un **repli** et un **plafond de coût**.
6. Mettre en place une **CI d'évaluation** qui bloque une fusion si le score passe sous un seuil.

## Programme

| Module | Contenu | Durée indicative |
|---|---|---|
| 1. Pourquoi évaluer | Non-déterminisme, régressions silencieuses, typologie d'erreurs, définir « bon », jeu de données doré | 1h15 |
| 2. Méthodes d'évaluation | Métriques exactes et heuristiques, LLM-juge et ses biais, évaluation humaine, RAG, agents, mini-harnais Python | 2h15 |
| 3. Fiabiliser en production | Garde-fous, sorties structurées, retries, repli, cache, coûts, observabilité, retours utilisateurs | 1h30 |
| 4. Boucle d'amélioration continue | CI d'évaluation, A/B, détection de dérive, revue des erreurs | 1h |
| 5. Projet final | Suite de 30 cas pour un assistant RAG avec seuil bloquant en CI | 1h |

```mermaid
flowchart LR
  A["Définir « bon » avec le métier"] --> B["Jeu de données doré"]
  B --> C["Harnais d'évaluation"]
  C --> D["CI : seuil bloquant"]
  D --> E["Production : garde-fous + traces"]
  E --> F["Revue des erreurs"]
  F --> B
```

## Ce que vous saurez faire

- Répondre à « le nouveau prompt est-il meilleur ? » avec un tableau de scores, pas une opinion.
- Expliquer à un sponsor pourquoi un taux de réussite de 92 % sur 30 cas a une marge d'incertitude importante.
- Repérer en quelques minutes, dans les traces, **où** un RAG s'est trompé : recherche ou génération.
- Livrer un dépôt où toute modification de prompt déclenche l'évaluation automatiquement.
