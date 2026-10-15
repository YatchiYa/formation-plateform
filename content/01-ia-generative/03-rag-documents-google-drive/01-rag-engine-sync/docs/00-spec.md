# 00. Spécification — Kit RAG Google Drive sur GCP (RAG Engine + synchro)

**Statut :** validée le 14/10/2026 · **Sous-projet :** 1 / 3 de [`gcp_rag`](../../README.md)
**Projet de test :** `main-project-511608` (compte Gmail, sans organisation)

---

## 1. Le besoin

> « J'arrive, je donne mon dossier Drive, et j'ai un RAG performant dessus, mis à jour automatiquement.
> Je peux aussi déposer des documents par glisser-déposer. Plus tard : OneDrive, SharePoint. »

| Exigence | Réponse du kit |
|---|---|
| Brancher un dossier Google Drive en 1 geste | Coller l'URL du dossier dans l'interface + le partager (lecture) avec **2 adresses** affichées par l'interface |
| RAG performant | Parsing Document AI *layout parser* (tableaux, titres), embeddings multilingues, reranking sémantique, réponses citées |
| Mise à jour automatique | Job de synchro toutes les 10 min (réglable) + bouton « Synchroniser maintenant » : ajouts, modifications **et suppressions** |
| Glisser-déposer | Zone de dépôt → bucket GCS → même synchro |
| Clé en main | 1 fichier `config/*.env`, 3 méthodes de déploiement (shell, Terraform, console), test de bout en bout automatique |
| Services managés, IAM propre | Tout est managé (RAG Engine, Cloud Run, Scheduler, Document AI, Gemini) ; 1 compte de service au moindre privilège |
| Plus tard OneDrive / SharePoint | RAG Engine importe déjà SharePoint (sous-projets [2 et 3](../../README.md)) |

**Hors périmètre (volontaire) :** droits par utilisateur (chacun ne voit que ses documents) → sous-projet 2
(Gemini Enterprise natif). Ici, **toute personne qui a accès à l'interface interroge tout le corpus**.

---

## 2. Architecture

```
  Dossier(s) Google Drive                     Navigateur (vous, collègues)
  partagé(s) en lecture avec :                      │  gcloud run services proxy
   • rag-kit-sa@…   (liste, détecte suppressions)   ▼
   • service-N@gcp-sa-vertex-rag… (importe)   ┌──────────────────────────────────────┐
        │                                     │ Cloud Run « rag-kit » (privé)          │
        │                                     │  FastAPI : API ADK + /api/* + page web │
        │                                     │  Agent ADK « assistant_documents »     │
        │                                     │  (Gemini 2.5 Flash, outil de recherche)│
        │                                     └───┬─────────────┬──────────────┬──────┘
        │                         dépôt de fichier │  lance le job │  recherche   │
        │                          ▼               │               ▼              ▼
        │                   GCS  gs://…-rag-kit    │      Cloud Run job    RAG Engine
        │                    uploads/ · config.json└────► « rag-kit-sync » ─► corpus « rag-kit »
        └─────────────────────────────────────────────────▲  (RagManagedDb, europe-west4)
                                      Cloud Scheduler ────┘  */10 * * * *
                                                              Document AI layout parser (eu)
```

**Une seule image** sert au service (interface + agent) et au job (synchro) ; seule la commande change.

---

## 3. Composants

| # | Composant | Rôle | Fichier |
|---|---|---|---|
| 1 | `kit.py` | Bibliothèque partagée : config des sources (JSON dans GCS), listing Drive/GCS, diff, appels RAG Engine, recherche | `app/kit.py` |
| 2 | Synchro | `python sync_job.py` : une passe de synchro idempotente | `app/sync_job.py` |
| 3 | Agent ADK | `assistant_documents` : répond **uniquement** depuis les documents, cite ses sources | `app/agents/assistant_documents/agent.py` |
| 4 | Serveur web | API ADK (`/run_sse`, sessions) + `/api/*` (sources, documents, dépôt, synchro) + page | `app/main.py` |
| 5 | Interface | 1 page HTML/CSS/JS, sans framework ni build | `app/static/index.html` |
| 6 | Infra | Terraform **ou** script shell **ou** console | `terraform/`, `scripts/`, `docs/03-*` |

### 3.1 Synchro (le cœur) — algorithme

Une passe, idempotente, sûre à relancer :

1. Lire `config.json` (liste des dossiers Drive) dans le bucket.
2. **Souhaité** = fichiers Drive (récursif, hors corbeille, types supportés) de chaque dossier + objets `gs://BUCKET/uploads/**`.
3. **Présent** = `list_files(corpus)` ; clé de chaque fichier : ID Drive (`google_drive_source.resource_ids[0].resource_id`)
   ou URI GCS (`gcs_source.uris[0]`).
4. **Supprimer** du corpus tout fichier présent et non souhaité (supprimé, déplacé hors du dossier, dossier retiré).
5. **Importer** : pour Drive, **seulement** les fichiers nouveaux ou dont la date de modification Drive est
   postérieure à leur dernière indexation, par lots de 25 (`https://drive.google.com/file/d/<ID>`) ; pour les dépôts,
   le préfixe `gs://BUCKET/uploads/`. **Vérifié :** RAG Engine saute l'inchangé pour GCS, mais **réimporte tout
   fichier Drive à chaque import** (5 imports sur 5) — d'où ce filtre, sinon chaque passe re-parserait tout Drive.
6. Écrire un rapport `sync/last.json` (compteurs, erreurs, durée) lu par l'interface ; le détail par fichier va dans
   `sync/runs/<horodatage>.ndjson` (*import_result_sink*).

**Concurrence :** un seul import à la fois par corpus (sinon `FailedPrecondition: There are other operations running`,
vérifié). → chaque action lance une **nouvelle** exécution du job ; une passe qui trouve le corpus occupé attend
15 s et **recommence entièrement** (listing frais), jusqu'à 15 min. La dernière passe lancée voit donc le dernier état.

**Plafond connu :** le listing Drive complet à chaque passe convient jusqu'à quelques milliers de fichiers. Au-delà :
API `changes` de Drive (jeton de page stocké dans le bucket).

### 3.2 Qualité du RAG (réglages par défaut)

| Étape | Choix | Pourquoi / vérifié |
|---|---|---|
| Parsing | Document AI **Layout Parser** (processeur `eu`) | Tableaux PDF rendus en markdown (vérifié : « Albatros = 990 € » retrouvé) |
| Découpage | 512 jetons, recouvrement 100 | Défaut recommandé |
| Embeddings | `text-multilingual-embedding-002` | Documents FR ; `gemini-embedding-001` **refusé** par RAG Engine (« Publisher model is not allowed for use in Vertex RAG yet », vérifié 14/10/2026) |
| Base vectorielle | RagManagedDb, palier **Basic** | Managé, sans index à gérer ; palier `Scaled` pour la production |
| Recherche | top 8 → reranking `semantic-ranker-default@latest` | Vérifié |
| Génération | `gemini-2.5-flash` en `europe-west4` | Tout reste en UE ; 6/6 appels en ≈ 1 s. `gemini-3.5-flash` : `global` seulement, 429 fréquents sur le projet de test (vérifié) → option |
| Citations | titre + lien Drive ou `gs://` renvoyés par l'outil, consignes de citation dans l'agent | Liens cliquables dans l'interface |
| Réflexion du modèle | `thinking_level = low` (Gemini 3) ; 3 recherches au plus par question | Sans ça : ~200 s de réflexion quand l'info n'existe pas (vérifié) |
| Robustesse | 6 essais espacés (2 à 30 s) sur erreur du modèle ; une panne de recherche est rendue à l'agent (pas de 500) | `429 RESOURCE_EXHAUSTED` vu en vrai sur projet neuf |

### 3.3 Interface (1 page)

- **Sources** : ajouter un dossier Drive (URL ou ID) ; l'interface vérifie qu'elle voit le dossier et affiche les
  2 adresses à ajouter au partage ; retirer un dossier.
- **Dépôt** : glisser-déposer (ou parcourir), 30 Mo max par fichier (limite de requête Cloud Run 32 Mo).
- **Documents** : liste du corpus (nom, origine Drive/dépôt, date), suppression des fichiers déposés.
- **Synchro** : état de la dernière passe, bouton « Synchroniser maintenant ».
- **Chat** : réponses en streaming (`/run_sse`), citations cliquables, nouvelle conversation.

---

## 4. Identités et droits

| Identité | Où | Droits | Pourquoi |
|---|---|---|---|
| **`rag-kit-sa`** (service ET job) | Projet | `aiplatform.user`, `discoveryengine.viewer` (reranking), `logging.logWriter`, `monitoring.metricWriter`, `cloudtrace.agent` | Gemini, RAG Engine, observabilité |
| | Bucket | `storage.objectAdmin` | Dépôts, `config.json`, rapports |
| | Job `rag-kit-sync` | `run.invoker` + `run.viewer` (sur le job) | Bouton « Synchroniser » + état |
| | Dossier Drive | **Lecteur** (partage Drive) | Lister les fichiers (détecter les suppressions) |
| **Agent de service RAG** `service-NUM@gcp-sa-vertex-rag.iam.gserviceaccount.com` | Bucket | `storage.objectViewer` + `storage.objectCreator` | Lire les dépôts, écrire le rapport d'import (sans `objectCreator` : 403, vérifié) |
| | Dossier Drive | **Lecteur** (partage Drive) | Importer. Sans ce partage : import par dossier = 0 fichier **sans erreur** ; par fichier = 404 → le kit importe par fichier et signale chaque fichier illisible (vérifié) |
| | Document AI | rien à ajouter (vérifié) | Layout parser |
| **`rag-kit-scheduler-sa`** | Job | `run.invoker` | Cloud Scheduler lance le job |
| **Utilisateurs** | Service `rag-kit` | `run.invoker` | Accès à l'interface (liste `USERS` du `.env`) |

**Accès à l'interface :** service **privé** ; on y accède par `gcloud run services proxy rag-kit` (marche avec un
compte Gmail, sans organisation, vérifié). **Option** documentée : IAP sur Cloud Run (`iap_enabled`) quand le projet a
une organisation.

**Choix assumé :** un seul compte de service pour le service et le job (ils touchent les mêmes ressources ; les rôles
RAG Engine ne distinguent pas lecture et écriture). Séparation possible, décrite en [07](07-droits-iam.md).

---

## 5. Configuration (`config/<nom>.env`)

| Variable | Exemple | Rôle |
|---|---|---|
| `PROJECT_ID` | `main-project-511608` | Projet GCP |
| `REGION` | `europe-west4` | Cloud Run, bucket, corpus, scheduler |
| `MODEL` / `MODEL_LOCATION` | `gemini-2.5-flash` / `europe-west4` | Modèle de réponse (option : `gemini-3.5-flash` / `global`) |
| `PREFIX` | `rag-kit` | Préfixe de tous les noms |
| `SYNC_SCHEDULE` | `*/10 * * * *` | Fréquence de synchro |
| `DRIVE_FOLDERS` | `1gYDE…` | Dossiers Drive initiaux (séparés par des espaces) |
| `USERS` | `user:moi@exemple.com` | Qui peut ouvrir l'interface |
| `LAYOUT_PARSER` | `true` | Parsing avancé (Document AI) |
| `RAG_TIER` | `basic` | Palier RagManagedDb (`basic` / `scaled`) |

---

## 6. Livrables

```
01-rag-engine-sync/
├── README.md                  démarrage en 5 commandes
├── config/                    exemple.env, test.env (Terraform), test-shell.env (shell)
├── app/                       code (1 image : service + job), Dockerfile, requirements.txt
├── terraform/                 toute l'infra (corpus et palier RAG compris)
├── scripts/                   deployer_shell.sh, supprimer_shell.sh, ouvrir_interface.sh,
│                              test_e2e.py, config.sh  (le contrôle des partages Drive est fait
│                              par l'interface et par chaque passe de synchro)
├── tests/                     test_sync.py (logique de diff, sans réseau)
└── docs/
    00-spec.md                 (ce document)
    01-comprendre-et-choisir.md  marché + 3 approches
    02-prerequis.md            poste, comptes, API
    03-1-deployer-shell.md · 03-2-deployer-terraform.md · 03-3-deployer-console.md
    04-connecter-drive.md      partage, vérification, pièges
    05-utiliser-interface.md
    06-synchro-exploitation.md fréquence, logs, rapports, réindexation complète
    07-droits-iam.md           matrice détaillée, variantes
    08-couts.md
    09-depannage.md
    10-tout-supprimer.md
```

## 7. Validation (critères d'acceptation)

1. `pytest` : logique de diff (ajout, suppression, dossier retiré, fichier hors sources) — vert.
2. `scripts/test_e2e.py <url du proxy>` sur le projet déployé, **chaque étape vérifiée par une assertion** :
   dépôt d'un fichier contenant un fait unique → synchro → l'agent répond avec ce fait et cite le fichier →
   modification → nouvelle réponse → suppression → synchro → fichier absent du corpus.
3. Même scénario sur Drive (dossier de test partagé) : ajout dans un sous-dossier, suppression (corbeille).
4. Déploiement **Terraform** et **shell** : chacun déployé, testé (e2e), supprimé.
5. Chaque doc porte un bloc « Testé en vrai » daté avec les vraies sorties.

## 8. Faits vérifiés avant conception (14/10/2026, `main-project-511608`)

| Fait | Résultat |
|---|---|
| RAG Engine `europe-west4`, palier par défaut | `Basic` |
| `gemini-embedding-001` dans un corpus | **Refusé** (400) |
| `text-multilingual-embedding-002` | OK |
| Import dossier Drive (avec sous-dossier) partagé avec l'agent de service RAG | OK, récursif, ID Drive conservé |
| Import GCS + rapport d'import | OK après `objectViewer` + `objectCreator` pour l'agent RAG |
| Fichier GCS modifié puis réimporté | Réindexé (`imported 1`) ; inchangé : ignoré |
| Dossier Drive réimporté sans changement | **Réimporté à chaque fois** (`imported 2, skipped 0`, 5 essais) → filtre par date dans le kit |
| Import d'un fichier Drive par `…/file/d/<ID>` déjà indexé | Mis à jour sur place (même RagFile, pas de doublon) |
| 2 imports simultanés | `FailedPrecondition` (« other operations running ») |
| `delete_file` | OK |
| Layout parser `eu` + corpus `europe-west4` | OK, tableau en markdown |
| Reranking `semantic-ranker-default@latest` | OK |
| `gemini-3.5-flash` | `global` seulement ; `gemini-2.5-flash` OK en `europe-west4` |
| Terraform `hashicorp/google` 8.7 | `google_vertex_ai_rag_corpus`, `google_vertex_ai_rag_engine_config` existent |
| ADK 2.10 | impose `google-cloud-aiplatform` < 2 (module `vertexai.rag`, déprécié mais fonctionnel) |
| Reranking appelé avec `rag-kit-sa` | `403 discoveryengine.rankingConfigs.rank` ; **`discoveryengine.user` ne contient pas** la permission, `discoveryengine.viewer` oui |
| Gemini 3.5 Flash, question sans réponse dans les documents | ~200 s de réflexion entre 2 recherches → `thinking_level=low` + 3 recherches max |
| Projet neuf | `429 RESOURCE_EXHAUSTED` sur Gemini → 6 essais espacés |
| Import Drive par fichier sans partage avec l'agent RAG | `404 Unable to find some Google Drive resource(s)` (tout le lot échoue) → rejoué fichier par fichier |
| Drive `files.list` sur un dossier non partagé | liste **vide, sans erreur** → le kit lit d'abord le dossier (`files.get` = 404) et ne supprime rien |
| Compte de service supprimé puis recréé (même adresse) | partage Drive **perdu** (permission orpheline) : repartager |
| Terraform `config.json` avec `ignore_changes = [content]` | réécrit à chaque `apply` (empreinte) → `ignore_changes = all` |
| Cycle complet Terraform | `destroy` 42, `apply` 42 en 3 min 37 s, relance `No changes` (v1 ; v2 : 53 ressources) |
| v2 — `changes.list` avec le compte du kit | voit les changements des fichiers **partagés avec lui** |
| v2 — `changes.watch` vers une URL `run.app` | **accepté sans vérification de domaine** ; notification reçue 11 à 19 s après une création |
| v2 — délais push → indexé | création 40-43 s ; renommage et corbeille 2 min à 2 min 30 (notification retardée par Google ou passe planifiée) |
| v2 — export d'un Google Doc | `.docx` OK ; citation renvoyée vers le lien Drive d'origine |
| v2 — `run.invoker` pour lancer un job avec `overrides` | **insuffisant** → `run.jobsExecutorWithOverrides` |
| v2 — deux passes sur la même source | 2 canaux push (le 2e orphelin, notifications en 403) → verrou par source |

---

## 9. v2 — Connexion Google, « tout mon Drive » ou dossiers, synchro push

**Demande (14/10/2026) :** l'utilisateur **connecte son Google Drive** depuis l'interface, choisit **tout son Drive** ou
**des dossiers** (sélecteur Google), active ou non la **synchro automatique** par source ; ajout, modification et
suppression se propagent seuls, le plus vite possible. SharePoint et OneDrive affichés « bientôt ».

### 9.1 Pourquoi un miroir

« Tout mon Drive » ne peut pas être partagé avec l'agent de service RAG. Le kit lit donc Drive **avec le compte de
l'utilisateur** (OAuth), recopie chaque fichier dans `gs://BUCKET/mirror/<source>/<fileId>/<nom>` (Docs → .docx,
Slides → .pptx, Sheets et Dessins → .pdf, le reste tel quel si son type est indexable) avec en métadonnées le lien
Drive et le titre, puis indexe ce préfixe. Avantages : RAG Engine **saute l'inchangé** côté GCS (vérifié), un seul
mécanisme pour toutes les sources (OneDrive/SharePoint suivront par Microsoft Graph vers le même miroir), et les
citations pointent vers le **lien Drive** d'origine.

La source « dossier partagé avec le kit » (v1, sans connexion) reste disponible.

### 9.2 Détection des changements (du plus rapide au filet de sécurité)

| Mécanisme | Délai | Rôle |
|---|---|---|
| **Notifications push Drive** (`changes.watch`) → service public `<prefix>-hook` → lance le job | secondes | Réactivité. Jeton secret par canal vérifié ; regroupement des rafales (20 s) |
| **API `changes`** avec jeton de page par source | — | Chaque passe ne lit **que** les changements, même sur un Drive entier |
| Passe planifiée (`SYNC_SCHEDULE`) | ≤ 10 min | Filet : notification perdue, canal expiré |
| Réconciliation complète (listing) | 1×/jour, et si un dossier bouge | Rattrape tout le reste (dossier déplacé…) |
| Renouvellement des canaux (expirent après 7 j au plus) | à chaque passe | Si < 24 h restantes |

`auto = false` sur une source : ni canal ni passe planifiée pour elle ; seulement « Synchroniser maintenant ».

### 9.3 Identités et secrets

| Élément | Où | Accès |
|---|---|---|
| Client OAuth « Application Web » (ID + secret) | créé dans la console (pas d'API publique pour les portées Drive, vérifié), rangé dans le secret `<prefix>-oauth-client` | `rag-kit-sa` : lecture |
| Jetons de rafraîchissement des comptes connectés | secret `<prefix>-google-tokens` (JSON `{email: jeton}`) | `rag-kit-sa` : lecture + nouvelles versions |
| Clé d'API du sélecteur (Picker) | Terraform (`google_apikeys_key`), limitée à l'API Picker et aux pages `localhost` | navigateur |
| Portées | `drive.readonly`, `openid`, `email` | `drive.readonly` est « restreinte » : en mode test (≤ 100 testeurs), jetons valables 7 jours ; voir doc 04-bis |
| Service `<prefix>-hook` | public (Google doit pouvoir le joindre) ; n'accepte que les jetons de canal connus | lance le job |

La connexion est **au niveau du kit** : un compte connecté sert à toutes les personnes qui ouvrent l'interface (comme
le corpus). Redirection OAuth : `http://localhost:8080/auth/google/callback` (le proxy, port 8080).

### 9.4 Interface

Panneau **Sources** : carte *Google Drive* (bouton « Se connecter avec Google », puis « Tout mon Drive » ou
« Choisir des dossiers » via le sélecteur Google, interrupteur « Synchro auto » par source, retrait) ; carte
*Dossier partagé avec le kit* (v1) ; cartes *OneDrive* et *SharePoint* « bientôt ».

### 9.5 Validation

Tests automatiques avec un **compte de service comme compte connecté** (mêmes appels Drive : miroir, `changes`,
`changes.watch`) : ajout, modification, suppression, déplacement hors dossier, notification push → indexé en moins
d'une minute, désactivation de l'auto. La connexion OAuth réelle (écran Google) est validée par l'utilisateur.
