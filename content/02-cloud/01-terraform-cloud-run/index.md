---
title: Déployer un agent ADK sur Cloud Run avec Terraform
description: "Infrastructure as code, image conteneur et CI/CD GitHub Actions pour un agent Google ADK."
tags: [terraform, cloud-run, adk, ci-cd, github-actions]
level: advanced
duration: 3h
date: 2026-09-20
authors: [Youcef]
references:
  - title: Agent Development Kit (ADK)
    url: https://google.github.io/adk-docs/
    note: Documentation officielle d'ADK
  - title: google/adk-python
    url: https://github.com/google/adk-python
  - title: "Provider Terraform Google : google_cloud_run_v2_service"
    url: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_service
  - title: google-github-actions/auth
    url: https://github.com/google-github-actions/auth
    note: Authentification sans clé via Workload Identity Federation
---

Ce cours montre comment passer d'un agent ADK qui tourne sur votre poste à un service Cloud Run reproductible, entièrement décrit en Terraform et déployé par une CI sans clé de compte de service.

## Au programme

1. **Prérequis** : outils, structure du dépôt et agent minimal.
2. **Infrastructure** : Artifact Registry, compte de service, Cloud Run, IAM.
3. **Déploiement continu** : GitHub Actions, Workload Identity Federation et stratégie de release.

Chaque leçon est autonome, mais elles suivent l'ordre dans lequel vous construirez le projet.
