---
type: course
title: "Évaluation avancée des agents : trajectoires, juges calibrés et garde-fous testés"
description: "Évaluer un agent ADK sur ce qu'il fait (outils, ordre, arguments) et sur ce qu'il dit, calibrer un LLM-juge contre des annotations humaines, prouver ses garde-fous par des tests et bloquer une mise en production en CI."
level: expert
duration: "4h30"
tags: [ia, adk, evaluation, llm-juge, securite, ci]
date: 2026-10-15
authors: [Youcef]
usecases: [support-client, assistant-interne]
platforms: [google-adk, gemini-api, vertex-ai]
references:
  - title: "ADK : évaluer un agent (evalset, adk eval, critères)"
    url: https://google.github.io/adk-docs/evaluate/
  - title: "ADK : callbacks (before_tool_callback…)"
    url: https://google.github.io/adk-docs/callbacks/
  - title: "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (Zheng et al., 2023)"
    url: https://arxiv.org/abs/2306.05685
    note: "Accord juge / humains et biais connus des LLM-juges"
  - title: "Service d'évaluation de l'IA générative (Google Cloud)"
    url: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-overview
  - title: "OWASP Top 10 for LLM Applications"
    url: https://genai.owasp.org/llm-top-10/
  - title: "PyRIT (Microsoft) : outillage de red teaming pour l'IA générative"
    url: https://github.com/Azure/PyRIT
  - title: "promptfoo : tests et red teaming de LLM en CI"
    url: https://github.com/promptfoo/promptfoo
---

« L'agent a bien répondu » ne suffit pas. Un agent de support peut donner le bon solde en ayant appelé le mauvais outil, réussir neuf demandes sur dix et exécuter un virement interdit à la dixième, ou être noté « excellent » par un LLM-juge qui ne mesure pas ce que vous croyez. Cette formation vous apprend à évaluer un agent **comme un système** : ce qu'il fait, ce qu'il dit, et ce qu'il ne doit jamais faire.

Fil rouge : l'assistant de support d'une banque **fictive**, la Banque Atelier, en deux versions. La v1 est naïve (l'identité du client vient du modèle, aucun contrôle des virements dans le code). La v2 est durcie (identité de session, garde-fou en code). Vous mesurez l'écart entre les deux, chiffres réels à l'appui.

## Pour qui ?

- Développeurs et responsables qualité qui ont déjà construit un agent ADK avec des outils.
- À l'aise avec Python et `pytest`. Aucune expérience préalable de l'évaluation de LLM n'est nécessaire.

## Ce que vous construisez

```mermaid
flowchart LR
  E[("evalset.json (format ADK)")] --> H["harness.py : trajectoires"]
  G[("guardrail_cases.json")] --> GF["guardrails.py : règles vérifiées en code"]
  L[("human_labels.json")] --> J["llm_judge.py : juge + calibration"]
  A["bank_agent.py v1 / v2"] --> H
  A --> GF
  H --> R["run_all.py → results.json"]
  GF --> R
  J --> R
  R --> C["report.py --ci : rapport.md + seuils"]
  C -->|"code de sortie 1"| X["mise en production bloquée"]
```

## Prérequis techniques

- Python 3.10 ou plus récent, `pip install -r requirements.txt` (ADK 2.10.0).
- Une clé Gemini (Google AI Studio) **ou** un projet Google Cloud avec Vertex AI.

## Programme

| Module | Leçons | Durée indicative |
| --- | --- | --- |
| 1. Évaluer la trajectoire | Réponse et trajectoire ; harnais de trajectoire ; `adk eval` | 1h45 |
| 2. Juger les réponses | LLM-juge et grille ; calibration contre des annotations humaines | 1h15 |
| 3. Garde-fous, red teaming et CI | Tester les garde-fous ; red teaming (principes) ; projet final en CI | 1h30 |

Code complet dans [files/](./files/) : [bank_agent.py](./files/bank_agent.py), [harness.py](./files/harness.py), [guardrails.py](./files/guardrails.py), [llm_judge.py](./files/llm_judge.py), [run_all.py](./files/run_all.py), [report.py](./files/report.py), [test_lab.py](./files/test_lab.py), et le rapport réellement produit : [rapport.md](./files/rapport.md).

## En local ou avec Vertex AI ?

| | Sans GCP (clé Gemini) | Avec GCP (Vertex AI) |
| --- | --- | --- |
| Variables | `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI=FALSE` | `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` |
| Code | identique | identique (le SDK `google-genai` choisit le service) |
| À grande échelle | votre harnais | aussi le service d'évaluation de Google Cloud |

> [!NOTE]
> Tout a été exécuté le 2026-10-15 avec `gemini-3.5-flash` : 8 tests sans clé verts, puis 38 appels réels au total (évaluation complète, recalibration du juge et `adk eval`). Les sorties sont reproduites dans les sections « Résultat obtenu ». Le red teaming est traité dans ses principes et son processus ; pour les risques eux-mêmes, voir aussi [IA responsable et sécurité des LLM](../../../01-ia-generative/09-ia-responsable-securite-llm/index.md).
