# 01. Comprendre le RAG local

## 1. Le chemin d'une question

1. **Recherche hybride** (`store.py`) sur l'index local :
   - par **mots** : index plein texte SQLite FTS5 (BM25, accents ignorés) — retrouve un code exact comme `PEL-8826-NG` ;
   - par **sens** : cosinus entre le vecteur de la question et ceux des morceaux — retrouve « travailler depuis chez
     soi » dans un texte qui dit « télétravail » ;
   - les deux classements sont **fusionnés par rang** (RRF), 20 candidats gardés.
2. **Second tri** (Voyage `rerank-2.5`, si une clé Voyage est fournie) : 8 extraits gardés.
3. **Claude** (`llm.py`) reçoit les 8 extraits (titre, lien, texte) et la question, avec la consigne de ne répondre
   qu'avec eux et de citer chaque information `[titre](lien)`. Réponse affichée au fil de l'eau.

Un seul appel à Claude par question (pas d'agent qui boucle) : le plus simple, le plus rapide, le moins cher. La
conversation garde les 10 derniers échanges pour les questions de suivi.

## 2. Ce qui sort de votre ordinateur

| Donnée | Où elle va |
|---|---|
| Fichiers, index, vecteurs, jetons Google | **Restent** dans `data/` (jetons : fichier lisible par vous seul, droits 600) |
| La question + les 8 extraits utilisés | API Claude (Anthropic), pour rédiger la réponse |
| Le texte des morceaux, à l'indexation | Voyage AI **seulement** si `EMBEDDINGS=voyage` ; en `local`, rien ne sort |
| Contenu Google Drive | Lu depuis Google avec votre compte (lecture seule) |

Le serveur n'écoute que sur `127.0.0.1` : il n'est pas joignable depuis le réseau.

## 3. Local ou Voyage ?

| | `local` (défaut sans clé) | `voyage` |
|---|---|---|
| Coût | 0 € | ≈ 0,06 $ / M de jetons indexés (voyage-4), reranking ≈ 0,05 $ / M |
| Confidentialité | Rien ne sort à l'indexation | Le texte des documents part chez Voyage |
| Qualité | Bonne en français (modèle multilingue ; 5 questions reformulées sur 5 au test) | Meilleure, surtout sur de gros corpus, + second tri |
| Vitesse | CPU de votre machine (≈ quelques centaines de morceaux / s) | Réseau |

Prix Voyage relevés sur des sources tierces (octobre 2026) : vérifiez sur le site de Voyage.

## 4. Coût de Claude

Par question : ≈ 3 000 à 5 000 jetons en entrée (consigne + 8 extraits + question) et quelques centaines en
sortie. Avec `claude-opus-5-5` (4 $ / M en entrée, 20 $ / M en sortie) : **≈ 2 à 3 centimes par question** ;
`claude-sonnet-5-5` divise par deux, `claude-haiku-5-5` par plus de 30.

## 5. Limites

| Limite | Valeur | Au-delà |
|---|---|---|
| Taille de l'index | ~100 000 morceaux (recherche vectorielle en mémoire) | Index ANN (sqlite-vec, Qdrant) |
| PDF scannés (images) | Pas de reconnaissance de caractères | OCR (Document AI, Tesseract) avant dépôt |
| Droits par utilisateur | Non : application personnelle, une seule personne | Kit 1 / Gemini Enterprise |
