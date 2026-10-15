# 08. Coûts

**Le but :** savoir ce que coûte le kit au repos et à l'usage, et comment arrêter toute facturation.

Prix relevés le **14/10/2026** dans le catalogue de facturation Google (API Cloud Billing Catalog, en euros, hors
taxes, région `europe-west4`). Ils changent : refaites le calcul avec le
[simulateur](https://cloud.google.com/products/calculator) avant un engagement.

---

## 1. Le coût fixe : la base RagManagedDb

RAG Engine range les vecteurs dans une instance **Spanner Enterprise dédiée au projet et à la région**, créée à la
première utilisation et **facturée en continu, même sans aucune question** :

| Palier | Capacité | Calcul | ≈ par mois |
|---|---|---|---|
| **Basic** (défaut) | 100 unités de traitement (0,1 nœud) + sauvegarde | 0,1 nœud × 3 réplicas × 0,415 €/h × 730 h | **≈ 91 €** + stockage (0,10 €/Go/réplica, négligeable) |
| Scaled | 1 à 10 nœuds, autoscaling | × 10 au minimum | ≈ 910 € et plus |
| Unprovisioned | aucune | — | 0 € (**et toutes les données RAG du projet+région sont effacées**) |

**Une seule base pour tous les corpus du projet dans la région** : 1 ou 10 kits dans le même projet ⇒ même coût
fixe.

> **Le mode Serverless** (sans coût fixe) existe, mais en **préversion et en `us-central1` uniquement** (octobre 2026),
> sans RagManagedDb. Il n'est donc pas utilisé par ce kit (UE).

## 2. Les coûts à l'usage

| Poste | Prix | Pour 1 000 pages / 100 questions |
|---|---|---|
| Layout parser (Document AI) | 8,80 € / 1 000 pages, **à chaque (ré)indexation** d'un fichier | 8,80 € pour 1 000 pages ; 0 si `LAYOUT_PARSER=false` (parsing simple gratuit) |
| Embeddings (`text-multilingual-embedding-002`) | facturé au nombre de caractères indexés | quelques centimes |
| Reranking (API Ranking) | 0,88 € / 1 000 recherches | ≈ 0,15 € (≈ 1,5 recherche par question) |
| **Gemini 2.5 Flash** (défaut) | 0,13 € / M en entrée, 0,53 € / M en sortie (unités du catalogue) | ≈ 0,15 € (≈ 10 000 jetons lus et 300 écrits par question) |
| Gemini 3.5 Flash (option) | 1,32 € / M en entrée, 7,92 € / M en sortie | ≈ 1,5 € |
| Cloud Run (service, job) | à la seconde, zéro au repos | < 1 € par mois pour un usage d'équipe |
| Cloud Scheduler | 3 tâches gratuites par compte de facturation (tarif public, non relevé dans le catalogue) | 0 € |
| Cloud Storage, Artifact Registry, Cloud Build | quelques centimes | < 1 € |
| Passes planifiées toutes les 5 min (≈ 8 600/mois, incrémentales, 2 à 15 s facturées chacune) | Cloud Run à la seconde | ≈ 2 à 3 € / mois |
| Secret Manager (2 secrets, 1 version active chacun) + service `rag-kit-hook` | à l'usage | < 0,50 € / mois |
| Miroir Google (`mirror/`) | stockage GCS | taille de vos documents exportés, centimes |

**Synchro sans changement** : aucun import (le kit n'envoie à RAG Engine que le nouveau et le modifié), 2 à 4 s de
Cloud Run (mesuré).
**Un fichier modifié** est re-parsé (layout parser) et ré-embeddé : un gros PDF modifié souvent coûte à chaque fois.

## 3. Exemple

Équipe de 20 personnes, 2 000 pages indexées une fois, 50 pages modifiées par semaine, 1 000 questions par mois :

| Poste | € / mois |
|---|---|
| RagManagedDb Basic | ≈ 91 |
| Layout parser : 2 000 pages la 1re fois (17,60 €), puis ≈ 200 pages/mois | ≈ 1,80 (+ 17,60 une fois) |
| Questions (Gemini 2.5 Flash + reranking) | ≈ 3 (≈ 16 avec Gemini 3.5 Flash) |
| Le reste | ≈ 2 |
| **Total** | **≈ 98 € / mois** (≈ 116 € le 1er mois) |

Le coût fixe domine : **mutualisez** (plusieurs kits ou corpus dans un même projet) ou **coupez la base** quand le kit
ne sert pas ([10](10-tout-supprimer.md#3-arrêter-le-coût-fixe-ragmanageddb)).

## 4. Surveiller la facture

- Console → **Facturation** → **Rapports**, filtre sur le projet, regroupé par SKU : la ligne
  « Read-Write Replica for Enterprise Edition in Netherlands » est la base RagManagedDb.
- Mettez un **budget** avec alertes (Facturation → Budgets et alertes), par exemple 150 € / mois.
