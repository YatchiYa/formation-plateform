---
type: course
title: "Construire un agent IA de A à Z"
description: "Coder en Python un agent qui appelle des outils, lui donner une mémoire, le brancher via MCP puis le passer en production avec Google ADK et Cloud Run."
level: intermediate
duration: "7h"
tags: [ia, agents, python, function-calling, mcp, adk]
date: 2026-10-15
authors: [Youcef]
usecases: [support-client, automatisation-processus, assistant-interne]
platforms: [watpilot, gemini-enterprise, vertex-ai]
references:
  - title: "Building effective agents (Anthropic)"
    url: https://www.anthropic.com/engineering/building-effective-agents
    note: "Workflows contre agents, et quand rester simple"
  - title: "Function calling avec l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/function-calling
  - title: "Compatibilité OpenAI de l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/openai
    note: "Le format utilisé par notre fonction call_llm"
  - title: "Model Context Protocol : documentation officielle"
    url: https://modelcontextprotocol.io
  - title: "Agent Development Kit (ADK) : documentation"
    url: https://google.github.io/adk-docs/
  - title: "Protocole Agent2Agent (A2A)"
    url: https://github.com/a2aproject/A2A
  - title: "ReAct: Synergizing Reasoning and Acting in Language Models (Yao et al., 2022)"
    url: https://arxiv.org/abs/2210.03629
    note: "L'article qui a popularisé la boucle raisonner / agir"
  - title: "OWASP Top 10 for LLM Applications"
    url: https://owasp.org/www-project-top-10-for-large-language-model-applications/
---

Un agent IA, ce n'est pas de la magie : c'est **une boucle** de quelques dizaines de lignes autour d'un LLM qui a le droit d'appeler des fonctions. Cette formation vous fait écrire cette boucle vous-même, en Python pur, avant de passer aux outils du marché (MCP, Google ADK) et à la production (multi-agents, garde-fous, Cloud Run).

Fil rouge : un **assistant de commandes** pour une boutique, qui consulte le catalogue, vérifie le stock, crée la commande et passe la main à un humain quand il le faut. C'est exactement le métier d'un agent comme Watpilot, qui prend des commandes et des rendez-vous sur WhatsApp avec Gemini et escalade vers un conseiller.

## Pour qui ?

- Développeurs Python à l'aise avec les fonctions, les dictionnaires, JSON et `pip`.
- Vous avez déjà appelé un LLM par API (ou suivi [Fondamentaux de l'IA générative](../05-fondamentaux-ia-generative/index.md)).
- Pas besoin d'expérience préalable avec les agents ni avec Google Cloud.

## Objectifs mesurables

À la fin de la formation, vous serez capable de :

1. **expliquer** en 3 phrases la différence entre chatbot, workflow et agent, et refuser un agent quand un workflow suffit ;
2. **écrire** de mémoire un agent de moins de 100 lignes, sans framework, qui appelle des outils décrits en JSON Schema ;
3. **rendre la boucle robuste** : erreurs d'outils renvoyées au modèle, limite d'itérations, sortie de secours vers un humain ;
4. **ajouter une mémoire** (historique tronqué, résumé, faits long terme) et **brancher un serveur MCP** ;
5. **réécrire** le même agent avec Google ADK, le découper en orchestrateur + spécialistes et le **déployer** sur Cloud Run ;
6. **livrer** un assistant de commandes à 3 outils + escalade humaine, évalué avec une grille.

## Prérequis techniques

- Python 3.10 ou plus récent.
- Une clé d'API pour un LLM qui sait appeler des outils (par exemple une clé Gemini créée dans Google AI Studio), exportée dans `LLM_API_KEY`.
- Pour le module 4 : un projet Google Cloud avec facturation (facultatif, la lecture suffit pour le reste).

## Programme

| Module | Contenu | Durée indicative |
| --- | --- | --- |
| 1. Comprendre les agents | Boucle perception → raisonnement → action, function calling, chatbot vs workflow vs agent, quand dire non | 1h |
| 2. Coder la boucle soi-même | `call_llm`, schémas d'outils, boucle complète, erreurs, limite d'itérations | 2h |
| 3. Mémoire, état et MCP | Historique, résumé, mémoire long terme, Model Context Protocol, le même agent avec Google ADK | 1h30 |
| 4. Multi-agents et production | Orchestrateur et spécialistes, A2A, garde-fous, observabilité, coûts, Cloud Run | 1h30 |
| 5. Projet final | Assistant de commandes : catalogue, stock, création de commande, passage à un humain | 1h |

Chaque leçon contient des schémas, des quiz corrigés, un exercice avec solution et une checklist « Je sais faire » que vous pouvez cocher.

## Ce que vous saurez faire

- Lire le code de n'importe quel framework d'agents et y reconnaître la même boucle.
- Décrire un outil pour qu'un LLM l'utilise correctement (nom, description, paramètres).
- Diagnostiquer un agent qui tourne en rond, invente un prix ou coûte trop cher.
- Mettre un agent derrière une URL, avec des traces et un budget.
