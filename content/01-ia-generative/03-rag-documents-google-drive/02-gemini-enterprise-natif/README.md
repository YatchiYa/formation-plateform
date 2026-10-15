# 02. Gemini Enterprise natif : Drive, SharePoint, OneDrive et dépôts, avec les droits de chacun

**Le but :** brancher vos documents sur l'**app Gemini Enterprise** de l'entreprise, avec les connecteurs de Google :
chaque personne ne voit **que ce qu'elle a le droit de lire** dans la source (Drive, SharePoint, OneDrive), la
synchro est gérée par Google, et l'interface est celle de Gemini Enterprise (web, mobile, agents).

```
 Google Drive  ── fédéré (en direct, droits Drive) ──────────────┐
 SharePoint    ── fédéré (en direct, droits Microsoft) ──────────┤
 OneDrive      ── ingestion (copie, synchro planifiée / temps réel)┼──► app Gemini Enterprise ──► vous (vos droits)
 Fichiers déposés ── bucket GCS ── import FULL toutes les 15 min ─┘      (recherche + réponses citées)
```

**Quand le choisir plutôt que le kit 1 :** l'entreprise a **Google Workspace** (et/ou Microsoft 365) et des
**licences Gemini Enterprise**, et chacun doit ne voir que ses documents. Sinon : [kit 1](../01-rag-engine-sync/README.md)
(n'importe quel projet, un corpus commun) ou [kit 4](../04-rag-local-claude/README.md) (local).

> **Testé en vrai** le 14/10/2026 sur `main-project-511608` (sans Workspace ni licence, donc **sans** Drive,
> SharePoint ni OneDrive) : Terraform de la brique « dépôts » (13 ressources, relance `No changes`), import GCS
> avec parseur de mise en page (tableau PDF lu), **suppression propagée** par la resynchro planifiée (import
> `FULL`), recherche, `rattacher.sh` sur une app existante (relance sans effet), `question.sh` (réponse juste et
> citée). **À dérouler chez vous** (Workspace, licences, Entra) : Drive, SharePoint, OneDrive, création de l'app —
> les étapes suivent la documentation officielle, liens dans chaque tuto.

## Démarrage

```bash
cd gcp_rag/02-gemini-enterprise-natif
cp config/exemple.env config/moi.env && nano config/moi.env    # PROJECT_ID et APP_ID de VOTRE app
source scripts/config.sh config/moi.env
(cd terraform && terraform init && terraform apply)           # dépôts (+ SharePoint si configuré)
bash scripts/rattacher.sh                                     # rattache à votre app
bash scripts/question.sh "Quelle est la politique de télétravail ?"
```

Puis Drive et OneDrive dans la console ([03](docs/03-google-drive.md), [04](docs/04-sharepoint-onedrive.md)) et
`bash scripts/rattacher.sh <id des data stores>`.

## Les tutos

| # | Document | Pour |
|---|---|---|
| 01 | [Comprendre](docs/01-comprendre.md) | Fédéré ou ingestion, droits, ce que fait Google et ce que fait le kit |
| 02 | [Déployer](docs/02-deployer.md) | Terraform (dépôts, SharePoint), app existante ou créée, rattachement |
| 03 | [Google Drive](docs/03-google-drive.md) | Data store Drive fédéré (Workspace), prérequis admin |
| 04 | [SharePoint et OneDrive](docs/04-sharepoint-onedrive.md) | Application Entra, SharePoint fédéré (Terraform), OneDrive (console) |
| 05 | [Tester et exploiter](docs/05-tester-exploiter.md) | `question.sh`, synchro, journaux, pièges vérifiés |
| 06 | [Supprimer](docs/06-supprimer.md) | Destroy, détacher de l'app |

## Les fichiers

| Fichier | Rôle |
|---|---|
| [terraform/main.tf](terraform/main.tf) | Agent de service, bucket et data store des dépôts, resynchro planifiée (Cloud Scheduler → API, sans code) |
| [terraform/connectors.tf](terraform/connectors.tf) | Connecteurs gérés par Terraform (SharePoint fédéré) ; secrets par référence |
| [terraform/app.tf](terraform/app.tf) | App Gemini Enterprise, seulement si `CREATE_APP=true` |
| [scripts/config.sh](scripts/config.sh) | Charge `config/*.env` |
| [scripts/rattacher.sh](scripts/rattacher.sh) | Ajoute des data stores à une app existante (n'en retire jamais) |
| [scripts/question.sh](scripts/question.sh) | Pose une question à l'app avec votre identité, affiche réponse et sources |
