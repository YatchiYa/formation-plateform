# 04. RAG local avec Claude : vos documents, sur votre ordinateur, sans Google Cloud

**Le but :** le même assistant que le kit 1 (réponses citées, synchro automatique, glisser-déposer), mais **qui tourne
sur votre ordinateur**, sans projet GCP ni service à déployer. Les réponses sont rédigées par **Claude** avec votre
clé API ; les documents restent chez vous (seuls la question et les extraits utiles partent vers Claude).

```
 Google Drive (OAuth) ─┐                       ┌──────────────── data/index.sqlite ────────────────┐
 Dossier du disque  ───┼─► synchro (60 s) ───► │ documents · morceaux · vecteurs · index plein texte │
 Glisser-déposer    ───┘   seul le changé      └───────────────────────┬────────────────────────────┘
                                                  recherche hybride ◄──┘ (mots + sens, fusion RRF, rerank Voyage)
 Vous ──► http://localhost:8765 ──► question ──► 8 meilleurs extraits ──► Claude ──► réponse citée [titre](lien)
```

> **Testé en vrai** le 14/10/2026 (Linux, Python 3.12) : 5 tests automatiques ; serveur avec embeddings **locaux**
> (multilingues) ; dossier local indexé (Markdown, texte, PDF avec tableau, Word avec tableau, sous-dossier) ;
> 5 questions reformulées sur 5 → bon document en tête ; dépôt et suppression ; fichier modifié et fichier supprimé
> sur le disque pris en compte **sans clic** ; connecteur Google Drive (listing complet, puis ajout et corbeille vus
> par l'API `changes`). **Pas testé faute de clés** : la réponse de Claude (`ANTHROPIC_API_KEY`) et Voyage
> (`VOYAGE_API_KEY`) — l'interface affiche un message clair tant que la clé manque — et l'écran de connexion
> Google (il faut votre client OAuth, [docs/03](docs/03-google-drive.md)).

## Démarrer (2 commandes)

```bash
cd gcp_rag/04-rag-local-claude
./rag              # 1re fois : installe tout (≈ 1 min) et crée .env ; puis http://localhost:8765
```

Mettez votre clé dans `.env` (`ANTHROPIC_API_KEY=sk-ant-…`) puis relancez `./rag`. Ajoutez une source dans
l'interface : un **dossier de l'ordinateur**, des fichiers **glissés-déposés**, ou **Google Drive** (après
[docs/03](docs/03-google-drive.md)).

## Ce qui est possible

| Source | Comment | Synchro |
|---|---|---|
| Fichiers déposés | Glisser-déposer dans l'interface (100 Mo max) | Immédiate |
| Dossier de l'ordinateur | Chemin du dossier, sous-dossiers compris | Toutes les 60 s : ajout, modification, suppression |
| **OneDrive / SharePoint, en attendant le connecteur** | Le dossier synchronisé par le client OneDrive (Windows/Mac) ou par rclone (Linux) | Idem |
| Google Drive | « Se connecter avec Google », puis tout le Drive ou des dossiers (sélecteur intégré) | Toutes les 60 s, API `changes` (seul le changé est relu) |
| OneDrive, SharePoint (connecteur direct) | Affichés « bientôt » | — |

## Réglages (`.env`)

| Variable | Défaut | Rôle |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Clé Claude (réponses) |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Ou `claude-sonnet-5-5` (moins cher), `claude-haiku-5-5` (le plus rapide) |
| `CLAUDE_EFFORT` | `low` | Profondeur de réflexion : `low` suffit pour des questions-réponses |
| `EMBEDDINGS` | `auto` | `voyage` si `VOYAGE_API_KEY` est remplie, sinon `local` (gratuit, sur la machine) |
| `VOYAGE_MODEL` / `RERANK_MODEL` | `voyage-4` / `rerank-2.5` | Modèles Voyage (embeddings, second tri) |
| `LOCAL_EMBED_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Modèle local (≈ 220 Mo, téléchargé au 1er lancement) |
| `POLL_SECONDS` | `60` | Fréquence de la synchro automatique |
| `PORT` | `8765` | Port de l'interface (écoute sur 127.0.0.1 seulement) |

Changer de modèle d'embeddings (`EMBEDDINGS`, `VOYAGE_MODEL`, `LOCAL_EMBED_MODEL`) **réindexe tout** au démarrage
suivant (vecteurs incompatibles) — c'est automatique.

## Les docs

| # | Document |
|---|---|
| 01 | [Comprendre](docs/01-comprendre.md) : architecture, recherche hybride, ce qui part vers Claude, coûts |
| 02 | [Sources et synchro](docs/02-sources-et-synchro.md) : dossier local, dépôt, OneDrive/SharePoint en attendant, règles de synchro |
| 03 | [Google Drive](docs/03-google-drive.md) : client OAuth (console, 5 min), connexion, tout le Drive ou dossiers |
| 04 | [Dépannage](docs/04-depannage.md) |

## Le code

| Fichier | Rôle |
|---|---|
| [app/server.py](app/server.py) | Serveur : interface, API, connexion Google, chat (flux SSE) |
| [app/sync.py](app/sync.py) | Synchro identique pour toutes les sources ; passe planifiée |
| [app/sources.py](app/sources.py) | Dépôts, dossier local, Google Drive (OAuth, API `changes`) |
| [app/store.py](app/store.py) | Index SQLite : documents, morceaux, vecteurs, FTS5 ; recherche hybride (RRF) |
| [app/embed.py](app/embed.py) | Embeddings et reranking : Voyage ou local (fastembed) |
| [app/parse.py](app/parse.py) | PDF, Word, PowerPoint, texte, HTML, CSV → texte → morceaux |
| [app/llm.py](app/llm.py) | Claude : une recherche, un appel en streaming, citations ; repli serveur si refus |
| [app/static/index.html](app/static/index.html) | L'interface |
| [tests/test_core.py](tests/test_core.py) | `./rag test` |
