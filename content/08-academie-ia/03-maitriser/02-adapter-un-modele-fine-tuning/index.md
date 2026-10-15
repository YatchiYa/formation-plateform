---
type: course
title: "Adapter un modèle : prompt, few-shot, RAG ou fine-tuning ?"
description: "Choisir la bonne façon d'adapter Gemini à une tâche, fabriquer par distillation un jeu de 100 tickets au format Vertex AI, mesurer une ligne de base few-shot et préparer un réglage supervisé prêt à lancer."
level: advanced
duration: "5h"
tags: [fine-tuning, distillation, vertex-ai, evaluation, jsonl, gemini]
date: 2026-10-15
authors: [Youcef]
usecases: [support-client, automatisation-processus]
platforms: [vertex-ai, gemini-api]
references:
  - title: "À propos du réglage supervisé des modèles Gemini (Vertex AI)"
    url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning
    note: "Modèles pris en charge, limites des jeux de données, cas d'usage"
  - title: "Préparer les données de réglage supervisé"
    url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare
    note: "Le format JSONL systemInstruction / contents / parts"
  - title: "Utiliser le réglage supervisé"
    url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-use-supervised-tuning
    note: "client.tunings.tune, suivi du job, appel du modèle réglé"
  - title: "Introduction au réglage des modèles (Vertex AI)"
    url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/tune-models
  - title: "Stratégies de prompting (API Gemini)"
    url: https://ai.google.dev/gemini-api/docs/prompting-strategies
    note: "Zero-shot, few-shot, consignes : à épuiser avant de régler"
  - title: "Tarifs de l'IA générative sur Vertex AI"
    url: https://cloud.google.com/vertex-ai/generative-ai/pricing
  - title: "Distilling the Knowledge in a Neural Network (Hinton et al., 2015)"
    url: https://arxiv.org/abs/1503.02531
    note: "L'article fondateur de la distillation professeur / élève"
  - title: "Retrieval-Augmented Generation (Lewis et al., 2020)"
    url: https://arxiv.org/abs/2005.11401
---

Votre équipe support reçoit des centaines de tickets par jour et veut les **classer automatiquement** (facturation, accès au compte, bug, demande de fonctionnalité, résiliation). Quelqu'un propose : « Il faut fine-tuner un modèle ! ». Peut-être. Peut-être pas. Cette formation vous apprend à **trancher avec des mesures**, puis à préparer un réglage proprement si les mesures le justifient.

Le fil rouge est un vrai lab, exécuté le 2026-10-15 : un grand modèle (`gemini-3.8-flash`) fabrique et étiquette 100 tickets fictifs, un petit modèle (`gemini-2.5-flash-lite` sur Vertex AI) est évalué en zero-shot et en few-shot, et un script de réglage supervisé est prêt, validé en dry-run.

> [!IMPORTANT]
> Le lab ne lance **aucun** job de réglage : c'est payant et ce n'est pas nécessaire pour apprendre. Le script `launch_tuning.py` est complet, ses paramètres sont vérifiés contre le SDK, et la leçon 3.1 détaille la procédure et le nettoyage.

## Pour qui ?

- Développeurs et ingénieurs data qui ont déjà appelé l'API Gemini en Python.
- Vous savez lire du JSON et lancer `pytest`.
- Pas besoin d'avoir déjà entraîné un modèle : chaque terme est expliqué.

## Ce que vous allez construire

```mermaid
flowchart LR
  P["Professeur : gemini-3.8-flash"] -->|"génère et étiquette"| D["100 tickets fictifs"]
  D --> V["validate_jsonl.py : format Vertex AI"]
  V --> S["Découpage 70 / 15 / 15"]
  S --> B["evaluate.py : ligne de base zero-shot et few-shot"]
  S --> T["launch_tuning.py : réglage supervisé (dry-run)"]
  T -.->|"si lancé"| M["Modèle réglé"]
  M -.-> B
```

## Prérequis techniques

- Python 3.10 ou plus récent, `pip install -r files/requirements.txt`.
- **En local (sans GCP)** : une clé d'API Gemini (Google AI Studio) dans `GOOGLE_API_KEY` suffit pour la distillation et pour l'évaluation (avec `MODEL=gemini-3.5-flash-lite`).
- **Sur GCP** : un projet avec l'API Vertex AI activée et `gcloud auth application-default login` pour évaluer le modèle qui sera réglé (`gemini-2.5-flash-lite`) et, si vous le décidez, lancer le réglage.

## Programme

| Module | Contenu | Durée indicative |
| --- | --- | --- |
| 1. Choisir la bonne approche | Arbre de décision prompt / few-shot / RAG / fine-tuning, mesurer une ligne de base | 1h15 |
| 2. Préparer les données | Format JSONL de Vertex AI, distillation, découpage train / validation / test | 1h45 |
| 3. Régler et évaluer | Procédure complète de réglage supervisé, évaluation avant / après | 1h15 |
| 4. Projet final | Le pipeline complet sur votre propre tâche de classification | 45 min |

## En local ou sur GCP

| Étape | En local (clé d'API) | Sur GCP (Vertex AI) |
| --- | --- | --- |
| Distillation (`distill.py`) | oui, `gemini-3.8-flash` | possible aussi |
| Validation du format | oui, sans réseau | identique |
| Ligne de base (`evaluate.py`) | oui, `gemini-3.5-flash-lite` | oui, **sur le modèle à régler** |
| Réglage (`launch_tuning.py --run`) | non | oui, payant |

Le code complet est dans le dossier `files/` (section Ressources) : `common.py`, `distill.py`, `validate_jsonl.py`, `evaluate.py`, `launch_tuning.py`, `test_lab.py` et les jeux de données réellement générés.
