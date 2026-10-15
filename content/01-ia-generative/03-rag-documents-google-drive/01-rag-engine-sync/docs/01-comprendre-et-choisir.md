# 01. Comprendre et choisir : RAG sur Google Drive, ce qui existe et ce que fait ce kit

**Le but :** savoir en 10 minutes ce qu'est un RAG, quelles solutions existent pour « brancher un Drive » sur
Google Cloud ou ailleurs, et pourquoi ce kit (sous-projet 1) est construit comme il l'est.

---

## Sommaire

1. [Le RAG en 2 minutes](#1-le-rag-en-2-minutes)
2. [Le marché : ce qui existe déjà](#2-le-marché--ce-qui-existe-déjà)
3. [Les 3 approches du dossier `gcp_rag`](#3-les-3-approches-du-dossier-gcp_rag)
4. [Ce que fait le kit 1, étape par étape](#4-ce-que-fait-le-kit-1-étape-par-étape)
5. [Ce qu'il ne fait pas (volontairement)](#5-ce-quil-ne-fait-pas-volontairement)
6. [Vocabulaire](#6-vocabulaire)

---

## 1. Le RAG en 2 minutes

Un modèle comme Gemini ne connaît pas **vos** documents. Le RAG (*Retrieval-Augmented Generation*) le lui fait
lire au bon moment :

```
  Indexation (une fois, puis à chaque changement)          Question (à chaque fois)
  ─────────────────────────────────────────────           ──────────────────────────────────────────
  document ─► découpage en morceaux (« chunks »)          question ─► recherche des morceaux proches
           ─► chaque morceau devient un vecteur                     ─► reclassement (reranking)
              (« embedding ») rangé dans une base                    ─► Gemini répond AVEC ces morceaux,
                                                                        en citant les documents
```

La qualité dépend de 4 choses, toutes réglées dans ce kit : **lire** correctement les documents (tableaux des PDF),
**découper** intelligemment, **retrouver** les bons morceaux (embeddings + reranking), et **obliger** le modèle à
répondre uniquement avec eux et à citer ses sources.

Le plus difficile en pratique n'est pas le RAG, c'est **la synchro** : un document ajouté, modifié, déplacé ou
supprimé dans Drive doit l'être aussi dans l'index, sans intervention.

---

## 2. Le marché : ce qui existe déjà

(État d'octobre 2026, vérifié sur la documentation officielle ; liens en fin de partie.)

### 2.1 Chez Google

| Solution | Drive | SharePoint / OneDrive | Synchro | Droits par utilisateur | À savoir |
|---|---|---|---|---|---|
| **Gemini Enterprise** (ex-Agentspace), connecteurs | Oui, **fédéré** (interroge Drive en direct, rien n'est copié) | Oui, **indexé** (copie dans Google Cloud) | Drive : toujours à jour. SharePoint/OneDrive : incrémentale toutes les 3 h au mieux, complète de 3 h à 7 j | **Oui** (chacun ne voit que ses documents) | Licences par utilisateur. Drive exige un **domaine Google Workspace**. Les recherches Workspace refusent les comptes de service : l'appli doit agir avec l'identité de l'utilisateur (OAuth). Connecteur Drive absent de Terraform (console ou API) → **sous-projet 2** |
| **Vertex AI RAG Engine** | Oui, **import** d'un dossier (récursif) | SharePoint oui (import) | **Aucune synchro continue** : on relance l'import ; GCS : inchangé ignoré ; **Drive : tout est réimporté à chaque fois** (vérifié) ; **supprimé = jamais retiré** | Non (tout le corpus pour tous) | Marche avec n'importe quel compte, Gmail compris, si le dossier est partagé avec l'agent de service RAG. **Si le partage manque : 0 fichier importé, aucune erreur** → **sous-projet 1** (ce kit ajoute la synchro et les contrôles) |
| **Vertex AI Search** (data store non structuré + GCS) | Non (via GCS) | Non | Import GCS périodique | Via ACL fournies à la main | Utile pour un site web ou un bucket ; pas pour Drive |

### 2.2 Hors Google (SaaS)

| Solution | Ce qu'elle apporte | Limite pour un projet GCP |
|---|---|---|
| **Ragie** | API RAG managée, connecteurs Drive, SharePoint, OneDrive, Notion… synchro automatique | Données hors de GCP ; facturé par connecteur |
| **Microsoft 365 Copilot / API Retrieval** | Recherche dans SharePoint et OneDrive avec les droits Microsoft | Monde Microsoft ; pas Drive |
| **Amazon Bedrock Knowledge Bases** | Connecteur SharePoint planifié | Monde AWS |
| Open source (Onyx/Danswer…) | Nombreux connecteurs, auto-hébergé | À exploiter soi-même (base, index, mises à jour) |

**Conclusion.** Pour rester **dans GCP**, sans Workspace ni licences, avec Drive **et** dépôt de fichiers, la brique la
plus solide est RAG Engine… à qui il manque la synchro (suppressions), le contrôle des partages, une interface et le
déploiement. C'est exactement ce qu'ajoute ce kit. Quand le client a Workspace et veut que chacun ne voie que ses
documents, Gemini Enterprise natif (sous-projet 2) est la bonne réponse.

---

## 3. Les 3 approches du dossier `gcp_rag`

| | 1. RAG Engine + synchro (**ce kit**) | 2. Gemini Enterprise natif | 3. Hybride |
|---|---|---|---|
| Comptes | N'importe quel projet GCP (Gmail OK) | Workspace + licences GE | Les deux |
| Drive | Import + synchro toutes les 10 min (réglable) + bouton | Fédéré, temps réel | Selon le client |
| Dépôt de fichiers | Oui (bucket) | Oui (data store GCS) | Oui |
| Droits par utilisateur | Non | **Oui** | Selon le moteur |
| Tout en Terraform | Oui | Presque (connecteur Drive : API) | Oui |
| Coût fixe | Base RagManagedDb (voir [08](08-couts.md)) | Licences | Selon |

---

## 4. Ce que fait le kit 1, étape par étape

```
  Dossier(s) Drive partagé(s)           Vous, dans le navigateur
  en lecture avec 2 adresses                   │ (gcloud run services proxy)
           │                                   ▼
           │                      ┌──────────────────────────────────┐
           │                      │ Cloud Run « rag-kit » (privé)    │
           │                      │  page web + API + agent ADK      │
           │                      └──┬───────────┬────────────┬─────┘
           │          dépôt de fichier│  « Synchroniser »   │ recherche
           │                ▼         │           ▼            ▼
           │         bucket (uploads/)│   job « rag-kit-sync » ─► corpus RAG Engine
           └──────────────────────────┴─────────▲               (europe-west4)
                                  Cloud Scheduler (toutes les 10 min)
```

1. **Brancher** : vous collez l'URL d'un dossier Drive dans l'interface. Elle vérifie qu'elle le voit, sinon elle
   vous donne les 2 adresses à mettre dans le partage ([04](04-connecter-drive.md)).
2. **Déposer** : glisser-déposer → fichier rangé dans le bucket.
3. **Synchroniser** : le job compare ce qui **devrait** être indexé (fichiers des dossiers + dépôts) à ce qui
   **l'est**, retire ce qui a disparu, puis importe seulement le nouveau et le modifié. Il tourne toutes les 10 min et à chaque action dans l'interface ([06](06-synchro-exploitation.md)).
4. **Demander** : l'agent ADK cherche (8 meilleurs morceaux, reclassés), répond uniquement avec eux, et cite
   chaque document avec un lien ([05](05-utiliser-interface.md)).

---

## 5. Ce qu'il ne fait pas (volontairement)

- **Droits par utilisateur** : toute personne qui ouvre l'interface interroge tout le corpus. Mettez dans un même
  kit des documents qui peuvent être lus par les mêmes personnes, ou passez au sous-projet 2.
- **Temps réel** : jusqu'à 10 min de décalage pour un changement fait dans Drive (0 pour un dépôt ou un clic
  sur « Synchroniser »).
- **Très gros volumes** : au-delà de quelques milliers de fichiers par dossier, le listing complet à chaque passe
  devient lent ; il faudra passer à l'API *changes* de Drive ([06](06-synchro-exploitation.md#limites)).
- **Mémoire longue des conversations** : elles vivent dans le service (1 instance) et disparaissent à son
  redémarrage.

---

## 6. Vocabulaire

| Mot | En clair |
|---|---|
| **Corpus** | L'index RAG Engine : la liste des fichiers et de leurs morceaux vectorisés |
| **RagManagedDb** | La base vectorielle gérée par Google derrière le corpus (Spanner) |
| **Agent de service RAG** | `service-<numéro>@gcp-sa-vertex-rag.iam.gserviceaccount.com` : le compte Google qui **importe** les fichiers. Il doit pouvoir lire le dossier Drive et le bucket |
| **Compte du kit** | `rag-kit-sa@<projet>.iam.gserviceaccount.com` : le compte de l'interface, de l'agent et du job. Il **liste** les dossiers Drive (pour voir les suppressions) |
| **Layout parser** | Lecteur Document AI qui comprend la mise en page (tableaux, titres) des PDF |
| **Reranking** | Second tri des morceaux trouvés par un modèle spécialisé, plus précis que la seule distance vectorielle |
| **ADK** | *Agent Development Kit* : la bibliothèque Python de Google pour écrire l'agent |

**Sources :** [RAG Engine, ingestion](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/use-data-connectors) ·
[Gemini Enterprise, connecteurs](https://docs.cloud.google.com/gemini/enterprise/docs/introduction-to-connectors-and-data-stores) ·
[Gemini Enterprise, Google Drive](https://docs.cloud.google.com/gemini/enterprise/docs/connect-google-drive) ·
[Gemini Enterprise, OneDrive](https://docs.cloud.google.com/gemini/enterprise/docs/ms-onedrive/set-up-data-store) ·
[Gemini Enterprise, Terraform](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/connect-terraform) ·
[RAG Engine, facturation](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-engine-billing) ·
[RAG Engine, mode Serverless](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/serverless-mode) ·
[Ragie, Google Drive](https://www.ragie.ai/blog/powering-your-rag-integrating-google-drive-for-seamless-knowledge-ingestion) ·
[Microsoft, API Retrieval](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/api-reference/retrieval-api-overview)
