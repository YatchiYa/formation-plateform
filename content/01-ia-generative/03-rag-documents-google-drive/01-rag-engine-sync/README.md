# 01. Kit RAG Google Drive — RAG Engine + synchro automatique

**Le but :** vous donnez un dossier Google Drive (ou glissez des fichiers), vous obtenez un assistant qui répond à
partir de ces documents, **avec les sources**, et qui reste **à jour tout seul** (ajouts, modifications,
suppressions). Tout est managé sur Google Cloud, déployable en une commande.

```
 Dossier Drive ─┐                       ┌───────────────────────────────┐
 Glisser-déposer┼─► synchro (10 min) ─► │ Vertex AI RAG Engine (corpus) │ ◄─ agent ADK (Gemini) ◄─ vous
                │   + bouton            └───────────────────────────────┘     interface web privée
```

> **Testé en vrai** le 14/10/2026 sur `main-project-511608` (compte Gmail, sans organisation, sans Workspace) :
> déploiement Terraform et shell, synchro Drive (sous-dossiers), dépôt, modification, suppression, chat cité,
> relance sans changement, suppression. Test automatique : `scripts/test_e2e.py`.

## Démarrage en 5 commandes

> Raccourci : `./ragkit status`, `./ragkit deploy`, `./ragkit ouvrir` ([docs/11](docs/11-cli-ragkit.md)).

```bash
cd gcp_rag/01-rag-engine-sync
cp config/test.env config/moi.env && nano config/moi.env           # PROJECT_ID, USERS, DRIVE_FOLDERS
gcloud services enable cloudresourcemanager.googleapis.com --project=<PROJET>
source scripts/config.sh config/moi.env                            # affiche les 2 adresses de partage Drive
(cd terraform && terraform init && terraform apply)                # ≈ 4 min
bash scripts/ouvrir_interface.sh                                   # http://localhost:8080
```

Puis, au choix : **Se connecter avec Google** (après l'étape console de [04-bis](docs/04-bis-connexion-google.md)) et
choisir « Tout mon Drive » ou des dossiers ; ou partager un dossier avec les 2 adresses affichées
([04](docs/04-connecter-drive.md)). Posez vos questions.

## Les tutos

| # | Document | Pour |
|---|---|---|
| 00 | [Spécification](docs/00-spec.md) | Exigences, architecture, choix, faits vérifiés |
| 01 | [Comprendre et choisir](docs/01-comprendre-et-choisir.md) | Le RAG, le marché (Gemini Enterprise, RAG Engine, SaaS), les 3 approches |
| 02 | [Prérequis](docs/02-prerequis.md) | Poste, compte, projet, région |
| 03-1 | [Déployer : shell](docs/03-1-deployer-shell.md) | gcloud seul, sans Terraform |
| 03-2 | [Déployer : Terraform](docs/03-2-deployer-terraform.md) | **Recommandé** |
| 03-3 | [Déployer : console](docs/03-3-deployer-console.md) | À la souris + Cloud Shell |
| 04 | [Connecter Drive : dossier partagé](docs/04-connecter-drive.md) | Sans connexion : partage avec 2 adresses |
| 04-bis | [Connexion Google](docs/04-bis-connexion-google.md) | **« Se connecter avec Google »**, tout mon Drive ou des dossiers, synchro auto (push) |
| 05 | [Utiliser l'interface](docs/05-utiliser-interface.md) | Écran, questions, messages, mode local |
| 06 | [Synchro et exploitation](docs/06-synchro-exploitation.md) | Algorithme, fréquence, surveillance, limites |
| 07 | [Droits (IAM)](docs/07-droits-iam.md) | Matrice complète, variantes, IAP |
| 08 | [Coûts](docs/08-couts.md) | Coût fixe RagManagedDb, coûts à l'usage, exemple |
| 09 | [Dépannage](docs/09-depannage.md) | Toutes les erreurs rencontrées, avec leur solution |
| 10 | [Tout supprimer](docs/10-tout-supprimer.md) | Destroy, arrêt du coût fixe, partages |
| 11 | [CLI `ragkit`](docs/11-cli-ragkit.md) | Activer/désactiver les briques, déployer, synchro, journaux, tests |

## Le code

| Fichier | Rôle |
|---|---|
| [app/kit.py](app/kit.py) | Sources (config dans le bucket), listing Drive, **synchro**, recherche avec reranking |
| [app/gdrive.py](app/gdrive.py) | Comptes Google connectés (OAuth), miroir GCS, API `changes`, canaux push |
| [app/hook.py](app/hook.py) | Service public des notifications push Drive |
| [app/sync_job.py](app/sync_job.py) | Le job Cloud Run : une passe de synchro |
| [app/agents/assistant_documents/agent.py](app/agents/assistant_documents/agent.py) | L'agent ADK : répond uniquement avec les documents, cite ses sources |
| [app/main.py](app/main.py) | Serveur : API ADK (`/run_sse`…) + `/api/*` (sources, dépôt, documents, synchro) + page |
| [app/static/index.html](app/static/index.html) | L'interface (une page, sans framework ni build) |
| [terraform/](terraform/) | Toute l'infrastructure |
| [scripts/](scripts/) | `config.sh`, `deployer_shell.sh`, `supprimer_shell.sh`, `ouvrir_interface.sh`, `connexion_google.sh`, `test_e2e.py` |
| [tests/test_sync.py](tests/test_sync.py) | Tests de la logique de synchro (sans réseau) : `pytest -q tests/` |

**Versions testées :** `google-adk 2.10.0`, `google-cloud-aiplatform 1.165.1` (imposé par ADK), Terraform `1.16`,
provider `hashicorp/google 8.7`, `gcloud 587`, modèle `gemini-2.5-flash` (`europe-west4`, option `gemini-3.5-flash` sur `global`), embeddings `text-multilingual-embedding-002`.

**Voir aussi :** [02 Gemini Enterprise natif](../02-gemini-enterprise-natif/README.md) (droits par utilisateur),
[03 hybride](../03-hybride/README.md) (ce kit + une app Gemini Enterprise), [04 local](../04-rag-local-claude/README.md) (sans GCP, avec Claude).
