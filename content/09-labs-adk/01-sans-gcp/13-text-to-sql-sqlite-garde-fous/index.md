---
type: course
title: "Text-to-SQL sur SQLite avec garde-fous"
description: "Construire avec Google ADK un analyste qui transforme des questions en français en SQL lecture seule, contrôlé par SQLite lui-même, puis le mesurer sur 15 questions de référence."
level: advanced
duration: "3h"
tags: [ia, adk, text-to-sql, sqlite, garde-fous, evaluation]
date: 2026-10-15
authors: [Youcef]
usecases: [analyse-donnees]
platforms: [google-adk, gemini-api]
references:
  - title: "ADK : outils fonctions (Function tools)"
    url: https://google.github.io/adk-docs/tools/function-tools/
    note: "Comment ADK transforme une fonction Python en outil"
  - title: "ADK : sécurité et garde-fous"
    url: https://google.github.io/adk-docs/safety/
  - title: "SQLite : sqlite3_set_authorizer"
    url: https://www.sqlite.org/c3ref/set_authorizer.html
    note: "Le mécanisme qui refuse une table ou une action à la compilation"
  - title: "SQLite : URI et mode=ro"
    url: https://www.sqlite.org/uri.html
  - title: "Python : module sqlite3"
    url: https://docs.python.org/3/library/sqlite3.html
  - title: "Spider : un jeu de référence text-to-SQL (Yu et al., 2018)"
    url: https://arxiv.org/abs/1809.08887
    note: "D'où vient l'idée d'évaluer par exécution"
  - title: "OWASP Top 10 for LLM Applications"
    url: https://owasp.org/www-project-top-10-for-large-language-model-applications/
---

« Combien de commandes livrées en septembre ? » : la question est simple, la requête SQL aussi. Laisser un LLM écrire ce SQL et l'**exécuter** sur une vraie base, en revanche, demande des précautions : le modèle peut se tromper de table, inventer une colonne, ou se faire manipuler pour lire une table sensible ou supprimer des données.

Dans ce lab, vous construisez un **analyste text-to-SQL** (texte vers SQL : le modèle traduit une question en langage naturel en requête SQL) avec **Google ADK** (Agent Development Kit, le framework d'agents open source de Google) et **Gemini**. La sécurité ne repose pas sur la bonne volonté du modèle : elle est appliquée par le code et par SQLite.

## Ce que vous construisez

- une base **SQLite** de ventes 100 % fictive (60 clients, 12 produits, 400 commandes) qui contient aussi une table sensible, `comptes_internes`, que l'agent ne doit jamais lire ;
- un module `garde_fous.py` à quatre couches : contrôle du texte, **autorisateur SQLite** (liste blanche de tables et d'actions), connexion en **lecture seule**, **LIMIT forcé** et délai maximal ;
- un agent ADK à un seul outil, `executer_sql`, qui valide la requête avant exécution, se corrige après un refus et **explique** son résultat ;
- une **évaluation par exécution** sur 15 questions de référence, plus 2 questions pièges, lancée pour de vrai.

```mermaid
flowchart LR
  U["Question en français"] --> A["Agent ADK (Gemini)"]
  A -->|"requete SQL"| T["executer_sql"]
  subgraph G["garde_fous.py"]
    direction TB
    V1["1. Texte : SELECT ou WITH, une requête"] --> V2["2. Autorisateur : tables et actions permises"]
    V2 --> V3["3. Connexion mode=ro"]
    V3 --> V4["4. LIMIT 50 et délai 2 s"]
  end
  T --> G
  G --> DB[("ventes.db")]
  G -->|"lignes ou erreur"| A
  A --> R["Réponse + SQL + explication"]
```

## Pour qui ?

- Développeurs et analystes à l'aise avec Python et le SQL de base (`SELECT`, `JOIN`, `GROUP BY`).
- Vous avez déjà vu un agent ADK simple (par exemple dans [Construire un agent IA de A à Z](../../../01-ia-generative/07-construire-un-agent-ia/index.md)).

## Prérequis

- Python 3.10 ou plus récent, `pip install -r files/requirements.txt` (google-adk 2.10.0).
- Une **clé d'API Gemini** (créée dans Google AI Studio) dans `GOOGLE_API_KEY`, avec `GOOGLE_GENAI_USE_VERTEXAI=FALSE`. Les tests automatiques, eux, tournent **sans clé**.

## Programme

| Module | Leçon | Ce que vous faites |
| --- | --- | --- |
| 1. Cas d'usage et architecture | [Text-to-SQL : promesse et risques](./01-cas-d-usage-et-architecture/01-promesse-et-risques.md) | Cartographier les risques et choisir où placer chaque garde-fou |
| 2. Construire pas à pas | [La base et les garde-fous](./02-construire-pas-a-pas/01-base-et-garde-fous.md) | Base fictive, autorisateur SQLite, lecture seule, LIMIT forcé |
| | [L'agent ADK et son outil](./02-construire-pas-a-pas/02-agent-et-outil.md) | Instruction avec schéma, outil `executer_sql`, explication du résultat |
| 3. Tester, évaluer, exploiter | [Tests sans clé et évaluation sur 15 questions](./03-tester-evaluer-exploiter/01-tests-et-evaluation.md) | Faux modèle, pytest, exactitude par exécution |
| | [Exploiter en confiance](./03-tester-evaluer-exploiter/02-exploiter.md) | `adk web`, journal d'audit, passage à une vraie base |

## En local ou sur Google Cloud ?

Tout ce lab tourne **en local** : SQLite est un fichier, l'agent appelle Gemini avec une simple clé d'API. Pour la même idée sur un entrepôt de données dans le cloud, suivez le lab [Analyste BigQuery](../../02-avec-gcp/01-analyste-bigquery/index.md), où les garde-fous deviennent un dry-run et un plafond d'octets facturés.

## Le code

Tout est dans [`files/`](./files/) : [agent.py](./files/agent.py), [garde_fous.py](./files/garde_fous.py), [creer_base.py](./files/creer_base.py), [evaluer.py](./files/evaluer.py), [questions_reference.json](./files/questions_reference.json) et [test_text_to_sql.py](./files/test_text_to_sql.py).
