---
type: course
title: "Assistant e-commerce : commandes, panier et escalade"
description: "Construire avec Google ADK un agent de service client qui consulte le catalogue et le stock, gère un panier en état de session, fait confirmer la commande, suit les livraisons et passe la main à un humain, protégé par des callbacks de garde-fou."
level: intermediate
duration: "2h30"
tags: [ia, adk, agents, gemini, support-client, garde-fous]
date: 2026-10-15
authors: [Youcef]
usecases: [support-client]
platforms: [google-adk, gemini-api]
references:
  - title: "ADK : outils fonction (Function tools)"
    url: https://adk.dev/tools-custom/function-tools/
  - title: "ADK : état de session (State)"
    url: https://adk.dev/sessions/state/
  - title: "ADK : types de callbacks"
    url: https://adk.dev/callbacks/types-of-callbacks/
  - title: "ADK : confirmation des actions"
    url: https://adk.dev/tools-custom/confirmation/
    note: "L'alternative intégrée à notre confirmation en deux temps"
  - title: "ADK : sécurité des agents"
    url: https://adk.dev/safety/
  - title: "Gemini API : function calling"
    url: https://ai.google.dev/gemini-api/docs/function-calling
  - title: "google/adk-python (code source)"
    url: https://github.com/google/adk-python
---

Un client écrit : « Vous avez des casques ? Mettez-m'en deux. » Derrière cette phrase, il faut chercher dans le catalogue, vérifier le stock, remplir un panier, faire valider un total, enregistrer la commande et, si le client se fâche, prévenir un humain. Dans ce lab, vous construisez cet agent avec **Google ADK** (Agent Development Kit, le framework open source de Google pour écrire des agents en Python) et **une simple clé d'API Gemini**.

La boutique, « Atelier Son », est fictive, tout comme ses produits et ses commandes.

## Pour qui ?

- Développeurs Python à l'aise avec les fonctions, les dictionnaires et `pip`.
- Vous savez ce qu'est un appel d'outil (function calling) ; sinon, la leçon 1 le rappelle en deux phrases.
- Aucun projet Google Cloud nécessaire.

## Ce que vous construisez

```mermaid
flowchart LR
  C["Client"] --> GE["Callback avant modèle : carte bancaire ? confirmation ?"]
  GE --> M["Gemini (gemini-3.5-flash)"]
  M -->|"appel d'outil"| GT["Callback avant outil : commande confirmée ?"]
  GT --> T["8 outils Python : catalogue, stock, panier, commande, livraison, escalade"]
  T --> S[("État de session : panier, commande en attente")]
  T --> M
  M --> R["Réponse au client"]
```

## Prérequis

- Python 3.10 ou plus récent.
- Une clé d'API Gemini créée dans Google AI Studio (gratuite pour démarrer).
- 15 minutes pour installer : `pip install -r files/requirements.txt`.

## Programme

| Module | Leçon | Ce que vous faites | Durée |
| --- | --- | --- | --- |
| 1. Cas d'usage | [Le cas d'usage et l'architecture](./01-cas-d-usage/01-cas-d-usage-et-architecture.md) | Délimiter ce que l'agent a le droit de faire, dessiner le flux | 30 min |
| 2. Construire | [Outils et état de session](./02-construire/01-outils-et-etat-de-session.md) | Écrire les outils, le panier dans `state` | 40 min |
| 2. Construire | [Confirmation, escalade, garde-fous](./02-construire/02-confirmation-escalade-et-garde-fous.md) | Commande en deux temps, callbacks | 40 min |
| 3. Tester et exploiter | [Tester sans clé, puis en réel](./03-tester-et-exploiter/01-tester-et-exploiter.md) | Faux modèle, scénario réel, `adk web`, pistes de production | 40 min |

## Le code

Tout est dans [files/](./files/) : [agent.py](./files/agent.py) (l'agent), [run.py](./files/run.py) (scénario réel), [test_agent.py](./files/test_agent.py) (7 tests sans clé), [requirements.txt](./files/requirements.txt) et `.env.example` (modèle de configuration à copier en `.env`).

## En local ou sur Google Cloud ?

| | En local (ce lab) | Sur Google Cloud (piste) |
| --- | --- | --- |
| Modèle | API Gemini avec une clé (`GOOGLE_API_KEY`) | Vertex AI (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`, projet et région) |
| Sessions | `InMemoryRunner` : tout disparaît à l'arrêt | service de sessions persistant (base de données ou Vertex AI) |
| Exposition | `python run.py` ou `adk web` | `adk deploy cloud_run` |
| Coût | quelques appels de modèle | Cloud Run + modèle |

Le code de l'agent est **identique** dans les deux cas : seules les variables d'environnement et le service de sessions changent. Ce lab a été testé de bout en bout en local le 2026-10-15 ; la partie Google Cloud est décrite mais n'a pas été déployée ici.
