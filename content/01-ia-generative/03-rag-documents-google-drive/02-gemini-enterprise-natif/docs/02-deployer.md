# 02. Déployer

## 1. Prérequis

| Quoi | Pourquoi |
|---|---|
| Projet de l'app Gemini Enterprise, facturation active | Data stores et app vivent dans ce projet |
| Rôles : `roles/discoveryengine.admin` (ou Propriétaire), `roles/resourcemanager.projectIamAdmin` | Créer data stores, droits |
| `gcloud`, Terraform ≥ 1.9, provider `hashicorp/google` ≥ 8.7 | — |
| Pour Drive : Google Workspace ; pour SharePoint/OneDrive : un tenant Microsoft 365 et un administrateur Entra | Connecteurs |

## 2. Configurer

```bash
cd gcp_rag/02-gemini-enterprise-natif
cp config/exemple.env config/moi.env
```

| Variable | Exemple | Rôle |
|---|---|---|
| `PROJECT_ID` | `acme-gemini-prod` | Projet de l'app |
| `GE_LOCATION` | `eu` | **Le même** emplacement que l'app (eu, us, global) |
| `REGION` | `europe-west1` | Bucket des dépôts et planification |
| `APP_ID` | `mon-app_1234…` | App existante (console Gemini Enterprise → Apps, colonne ID) |
| `CREATE_APP` | `false` | `true` : le kit crée l'app (exige un abonnement) |
| `DEPOTS` / `DEPOTS_SCHEDULE` | `true` / `"*/15 * * * *"` | Data store des fichiers déposés et sa resynchro |

`source scripts/config.sh config/moi.env` doit finir par `OK`.

## 3. Terraform

```bash
cd terraform && terraform init && terraform plan && terraform apply
```

Obtenu sur le projet de test (brique dépôts seule) : `Plan: 13 to add` puis `Apply complete! Resources: 13 added`,
et une relance : `No changes`. Le 1er import peut renvoyer une erreur dans le journal si le bucket est vide : la
planification refait l'import toutes les 15 min.

**SharePoint par Terraform** : décommentez le bloc `connectors` de `config/exemple.env` → voir [04](04-sharepoint-onedrive.md).

## 4. Rattacher à l'app

```bash
cd .. && bash scripts/rattacher.sh                    # data stores de Terraform
bash scripts/rattacher.sh <id-drive> <id-onedrive>   # + ceux créés dans la console
```

Obtenu (app de test) :

```
== App rag-ge-test-app2 : déjà rattachés : rag-ge-test-amorce rag-ge-test-amorce2
   À rattacher : rag-ge2-depots
== Rattachés : rag-ge-test-amorce, rag-ge-test-amorce2, rag-ge2-depots
```

Relance : `Rien à ajouter.` Le script **n'enlève jamais** un data store existant.

> **Vérifié :** une app créée avec **un seul** data store refuse tout ajout (`Engines with a single data store
> cannot add or remove data stores`). Une app Gemini Enterprise à plusieurs sources l'accepte. Si votre app n'a
> qu'une source, ajoutez les autres depuis la console (Apps → votre app → Données connectées), ou recréez-la.

## 5. Ou créer l'app avec le kit

`CREATE_APP=true` et `APP_ID=mon-app` : Terraform crée une app **intranet** (`APP_TYPE_INTRANET`, niveau
Enterprise + IA générative) avec les data stores du kit. Il faut un abonnement Gemini Enterprise et des licences
(console → Gemini Enterprise → Licences). Ensuite : `terraform apply` ne touche plus à la liste des sources
(Drive et OneDrive s'ajoutent par `rattacher.sh`).
