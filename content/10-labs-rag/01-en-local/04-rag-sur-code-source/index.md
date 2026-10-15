---
type: course
title: "RAG sur du code source"
description: "Construire un assistant qui répond aux questions sur une base de code Python avec des liens fichier:ligne vérifiés : découpage par fonction et classe avec le module ast, recherche hybride embeddings + BM25, et « où est géré X ? » sans appel de génération."
level: advanced
duration: "3h30"
tags: [rag, code, ast, bm25, recherche-hybride, evaluation]
date: 2026-10-15
authors: [Youcef]
usecases: [recherche-documentaire, assistant-interne]
platforms: [gemini-api]
references:
  - title: "Embeddings avec l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/embeddings
    note: "Préfixe « task: code retrieval » de gemini-embedding-2"
  - title: "ast : arbres syntaxiques abstraits (documentation Python)"
    url: https://docs.python.org/3/library/ast.html
  - title: "rank_bm25 : implémentation Python de BM25"
    url: https://github.com/dorianbrown/rank_bm25
  - title: "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods (Cormack et al., 2009)"
    url: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
    note: "La fusion de rangs utilisée pour la recherche hybride"
  - title: "Ragas: Automated Evaluation of Retrieval Augmented Generation"
    url: https://arxiv.org/abs/2309.15217
  - title: "Modèles de l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/models
---

« Où est gérée la relance des impayés ? », « que se passe-t-il si l'envoi d'e-mail échoue ? » : sur un projet que l'on découvre, ces questions coûtent des heures de lecture. Ce lab construit un RAG qui répond **avec des liens `fichier:ligne`** que l'on peut ouvrir, et qui refuse quand le code ne contient pas la réponse.

Le terrain de jeu : **facturo**, un petit projet Python **fictif** de facturation (16 fichiers, généré par un script), avec de vraies fonctions qui s'exécutent.

## Ce que vous allez construire

```mermaid
flowchart LR
  P["projet_demo/**/*.py"] --> A["ast.parse"]
  A --> C["morceaux : fonction, méthode, classe, constante + lignes début/fin"]
  C --> E["embeddings (titre = fichier + rôle du module)"]
  C --> B["BM25 sur les mots des identifiants"]
  E --> DB[("code.db")]
  Q["Question"] --> V["recherche vectorielle"]
  Q --> K["recherche BM25"]
  DB --> V
  B --> K
  V --> F["fusion RRF"]
  K --> F
  F --> OU["ou : liste fichier:ligne"]
  F --> G["Gemini : réponse"]
  G --> CHK{"chaque fichier:ligne dans un extrait ?"}
  CHK -- "oui" --> L["liens projet_demo/x.py#L12"]
  CHK -- "non" --> R["refus"]
```

## Pour qui ?

- Vous avez fait au moins le [lab 1](../01-rag-pdf-local-sqlite/index.md) ; le [lab 3](../03-contrats-chunking-et-metadonnees/index.md) (découpage par structure) est un bon échauffement.
- Vous lisez du Python couramment.

## Prérequis

- Python 3.10+, une clé d'API Gemini dans `.env` (voir [.env.example](./files/.env.example)).
- `pip install -r requirements.txt` ([requirements.txt](./files/requirements.txt)) : google-genai, numpy, rank-bm25.

## Programme

| Module | Leçon | Ce que vous faites | Fichiers |
| --- | --- | --- | --- |
| 1. Le cas d'usage | Questions sur du code | pourquoi le code est particulier, le projet fictif | `make_project.py` |
| 2. Construire | Découper avec ast | fonctions, méthodes, classes, constantes, lignes exactes | `code_rag.py` |
| 2. Construire | Recherche hybride et liens vérifiés | BM25, RRF, « où est géré X », citations vérifiées, liens | `code_rag.py` |
| 3. Évaluer | Évaluer et améliorer | 3 modes de recherche, 3 corrections mesurées, fidélité, refus | `eval.py`, `golden.json`, `test_code_rag.py` |

## En local ou sur GCP ?

| | Ce lab | Sur Google Cloud |
| --- | --- | --- |
| Code | dossier local | dépôt Git, synchronisé par Cloud Build |
| Index | `code.db` SQLite, réindexé par fichier | Vertex AI Vector Search + recherche plein texte |
| Accès | votre poste | Cloud Run derrière IAP, réservé à l'équipe |

Code complet : [code_rag.py](./files/code_rag.py), [eval.py](./files/eval.py), [test_code_rag.py](./files/test_code_rag.py), [make_project.py](./files/make_project.py).
