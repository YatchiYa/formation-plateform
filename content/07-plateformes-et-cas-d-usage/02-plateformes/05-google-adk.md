---
type: platform
title: Google ADK (Agent Development Kit)
icon: "🛠️"
url: https://google.github.io/adk-docs/
tags: [adk, agents, google, open-source]
description: "Le framework open source de Google pour construire des agents : outils, sous-agents, mémoire, évaluation, puis déploiement sur Cloud Run ou Agent Engine."
---

## En bref

ADK structure un agent en briques : un **modèle**, des **instructions**, des **outils** (fonctions Python, recherche Google, exécution de code, serveurs MCP), des **sous-agents** et des agents de flux (séquentiel, parallèle, boucle). Le même code tourne avec une simple **clé d'API Gemini** sur votre poste, ou sur **Vertex AI** dans un projet Google Cloud.

```bash
pip install google-adk
adk web        # interface de test locale
```

Les Labs Google ADK de ce site sont 20 agents complets, chacun avec son code testé.
