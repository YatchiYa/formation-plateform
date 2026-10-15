---
title: Déploiement en production
description: Choisir son backend vectoriel, planifier la mise en production et consulter les supports.
duration: 1h
---

## Les supports du cours

Le support complet, à lire en ligne ou à télécharger :

![Support de cours](../files/support-cours.pdf)

Le guide d'installation pas à pas :

![Guide d'installation](../files/guide-installation.docx)

La présentation utilisée en session :

![Présentation](../files/presentation.pptx)

## Choisir son backend vectoriel

| Backend | Gestion | Volume conseillé | Filtrage métadonnées | Coût de départ |
| --- | --- | --- | --- | --- |
| RagManagedDb | Entièrement managé | < 1 M chunks | Basique | Faible |
| Vertex AI Vector Search | Managé, endpoint dédié | Milliards | Avancé (restricts) | Élevé (nœud permanent) |
| Vertex AI Feature Store | Managé, BigQuery | Millions | Via SQL | Moyen |
| AlloyDB + pgvector | Semi-managé | Dizaines de millions | SQL complet | Moyen |
| Cloud SQL + pgvector | Semi-managé | Millions | SQL complet | Faible |
| BigQuery Vector Search | Serverless | Milliards (batch) | SQL complet | Au volume scanné |
| Pinecone | SaaS tiers | Milliards | Avancé | Variable |
| Weaviate | SaaS ou auto-hébergé | Centaines de millions | Avancé | Variable |
| Firestore vector search | Serverless | Millions | Requêtes Firestore | Faible |

## Planning de mise en production

```mermaid
gantt
    title Mise en production du RAG
    dateFormat YYYY-MM-DD
    axisFormat %d/%m
    section Socle
    Projet et IAM            :done, s1, 2026-10-01, 2d
    Terraform réseau          :done, s2, after s1, 3d
    section Données
    Ingestion initiale        :active, d1, 2026-10-06, 4d
    Job de synchronisation    :d2, after d1, 3d
    section Agent
    Agent ADK                 :a1, 2026-10-08, 5d
    Évaluation                :a2, after a1, 4d
    section Go live
    Revue sécurité            :crit, g1, after a2, 2d
    Ouverture aux utilisateurs :milestone, g2, after g1, 0d
```

## Checklist de déploiement

- **Infrastructure**
  - Terraform appliqué depuis la CI uniquement
    - état distant dans un bucket versionné
    - verrouillage de l'état activé
  - Workload Identity Federation pour GitHub Actions
- **Agent**
  1. Image construite et poussée dans Artifact Registry
  2. Déploiement Cloud Run avec un compte de service dédié
     - `--no-allow-unauthenticated`
     - concurrence ajustée (80 par défaut)
  3. Trafic basculé progressivement (`--tag canary`)
- **Observabilité**
  - Cloud Logging et Cloud Trace
  - Tableau de bord des scores de retrieval

> « En production, la question n'est pas de savoir si le retrieval va se tromper, mais si vous le verrez. »
>
> — Retour d'expérience d'une équipe plateforme
