---
type: course
title: "Embeddings et recherche sémantique"
description: "Construire un moteur de recherche sémantique sur 60 fiches produit avec gemini-embedding-2, numpy et sqlite : recherche multilingue, produits similaires, dédoublonnage, clustering, et rappel@5 mesuré pour de vrai."
level: intermediate
duration: "4h"
tags: [ia, embeddings, recherche-semantique, gemini, numpy, bigquery]
date: 2026-10-15
authors: [Youcef]
usecases: [recherche-documentaire, analyse-donnees]
platforms: [gemini-api, vertex-ai]
references:
  - title: "Embeddings avec l'API Gemini"
    url: https://ai.google.dev/gemini-api/docs/embeddings
    note: "Préfixes de tâche, output_dimensionality, agrégation des entrées"
  - title: "Fiche du modèle gemini-embedding-2"
    url: https://ai.google.dev/gemini-api/docs/models/gemini-embedding-2
  - title: "Matryoshka Representation Learning (Kusupati et al., 2022)"
    url: https://arxiv.org/abs/2205.13147
    note: "Pourquoi on peut tronquer un embedding sans tout perdre"
  - title: "BigQuery : recherche vectorielle"
    url: https://cloud.google.com/bigquery/docs/vector-search
  - title: "BigQuery : fonction VECTOR_SEARCH"
    url: https://cloud.google.com/bigquery/docs/reference/standard-sql/search_functions
  - title: "Vertex AI Vector Search : présentation"
    url: https://cloud.google.com/vertex-ai/docs/vector-search/overview
  - title: "Embeddings de texte sur Vertex AI"
    url: https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings
---

Une recherche par mots-clés trouve « tente » quand on tape « tente ». Elle ne trouve rien quand un client tape « dormir dehors à trois » ou « tent for three people ». Une **recherche sémantique** compare le **sens** des textes : chaque texte devient un vecteur de nombres, un **embedding**, et deux textes proches par le sens ont des vecteurs proches.

Fil rouge : un catalogue de **60 fiches produit fictives** (chaussures, cuisine, bureau, audio, camping…), dont 3 quasi-doublons glissés volontairement. On y construit un moteur de recherche, une recommandation « produits similaires », un détecteur de doublons, un regroupement automatique, et on **mesure** la qualité avec un jeu de 31 requêtes en 4 langues.

## Pour qui ?

- Développeurs ou analystes Python à l'aise avec les listes, les dictionnaires et JSON.
- Aucune connaissance préalable des embeddings ni de l'algèbre linéaire : on explique le produit scalaire au moment où on s'en sert.
- Une clé Gemini suffit. BigQuery et Vertex AI sont présentés en option.

## Ce que vous construisez

```mermaid
flowchart LR
  P["produits.json (60 fiches)"] --> T["Texte formaté : title: ... | text: ..."]
  T --> E["gemini-embedding-2 (768 dims)"]
  E --> N[("vecteurs.npy")]
  P --> S[("produits.sqlite")]
  Q["Requête (fr, en, es, de)"] --> QE["task: search result | query: ..."]
  QE --> E2["gemini-embedding-2"]
  E2 --> C["Cosinus = produit scalaire (numpy)"]
  N --> C
  C --> R["Top 5 + fiches depuis sqlite"]
  R --> EV["evaluer.py : rappel@5"]
```

## Objectifs mesurables

1. **Expliquer** ce qu'est un embedding et calculer une similarité cosinus avec numpy.
2. **Utiliser** `gemini-embedding-2` correctement : préfixes de tâche, `output_dimensionality`, une `Content` par texte.
3. **Construire** un index local persistant (`.npy` + sqlite) qui ne recalcule que les fiches modifiées.
4. **Exploiter** les vecteurs : recherche multilingue, produits similaires, doublons, clustering.
5. **Mesurer** la qualité avec le rappel@k et comparer à une recherche par mots-clés (BM25).
6. **Décider** quand passer à BigQuery `VECTOR_SEARCH` ou à Vertex AI Vector Search.

## Prérequis techniques

- Python 3.10 ou plus récent, `pip install -r files/requirements.txt`.
- Une clé d'API Gemini (Google AI Studio) dans `GOOGLE_API_KEY`, ou un projet Google Cloud.

## Programme

| Module | Contenu | Durée indicative |
| --- | --- | --- |
| 1. Comprendre les embeddings | Vecteurs, cosinus avec numpy, `gemini-embedding-2`, préfixes de tâche, dimensions | 1h |
| 2. Construire le moteur | Index persistant `.npy` + sqlite, recherche multilingue, similaires et doublons, clustering | 1h30 |
| 3. Évaluer et passer à l'échelle | Rappel@k contre BM25, BigQuery `VECTOR_SEARCH`, Vertex AI Vector Search | 45 min |
| 4. Projet final | Le moteur produits de bout en bout, tests sans clé, résultats réels | 45 min |

## Le code du lab

Tout est dans le dossier `files/` : [generer_produits.py](./files/generer_produits.py) et [produits.json](./files/produits.json) (les 60 fiches), [moteur.py](./files/moteur.py) (index, recherche, similaires, doublons, clusters), [requetes_eval.json](./files/requetes_eval.json) et [evaluer.py](./files/evaluer.py) (rappel@5), [test_moteur.py](./files/test_moteur.py) (8 tests sans clé), [bigquery_vector_search.py](./files/bigquery_vector_search.py) (option Google Cloud).

## En local ou sur Google Cloud ?

| | En local (« sans GCP ») | Sur Google Cloud |
| --- | --- | --- |
| Embeddings | API Gemini, clé `GOOGLE_API_KEY` | Vertex AI, `GOOGLE_CLOUD_LOCATION=global` |
| Lots | jusqu'à 20 textes par requête dans le lab | 1 texte par requête (limite constatée sur Vertex AI) |
| Index | `vecteurs.npy` + `produits.sqlite` | table BigQuery + `VECTOR_SEARCH` |
| Testé le 2026-10-15 | indexation, recherche, rappel@5 = 0,99 | indexation Vertex AI (rappel@5 = 0,99), BigQuery `VECTOR_SEARCH` (mêmes 5 résultats qu'en local) |
| À supprimer après | rien | le dataset `lab_embeddings_recherche` (`--nettoyer`) |
