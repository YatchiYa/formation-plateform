# 03-2. Déployer avec **Terraform**

**Le but :** créer tout le kit (42 ressources en v1, 53 avec la connexion Google et le push) avec **une** commande, le tester, le modifier, le supprimer.

**Les autres méthodes, même résultat :** [03-1 Shell](03-1-deployer-shell.md) · [03-3 Console](03-3-deployer-console.md).

> **Testé en vrai** le 14/10/2026 sur `main-project-511608` (compte Gmail, sans organisation) : `destroy` (42),
> `apply` complet depuis zéro (42 en 3 min 37 s), relance (`No changes`), `scripts/test_e2e.py` (dépôt,
> modification, suppression, question Drive) : TOUT EST OK.
> Les sorties ci-dessous sont les vraies.

---

## Sommaire

0. [Terraform en 2 minutes](#0-terraform-en-2-minutes)
1. [Ce que Terraform crée](#1-ce-que-terraform-crée)
2. [Pas à pas](#2-pas-à-pas)
3. [Tester](#3-tester)
4. [Modifier](#4-modifier)
5. [Supprimer](#5-supprimer)
6. [Ce qui peut arriver](#6-ce-qui-peut-arriver)

---

## 0. Terraform en 2 minutes

Terraform lit les fichiers `terraform/*.tf` qui **décrivent** ce qui doit exister, compare avec ce qui existe, et
fait **seulement la différence**.

| Commande | Effet |
|---|---|
| `terraform init` | Prépare le dossier (télécharge le provider Google `~> 8.7`). Une fois par poste |
| `terraform plan` | **Montre** ce qui va changer. Ne fait rien |
| `terraform apply` | Fait le plan, après votre `yes` |
| `terraform destroy` | Supprime tout ce que le dossier a créé |
| `terraform output` | Réaffiche les résultats (URL, adresses de partage…) |

Les valeurs viennent du fichier `config/*.env` : `scripts/config.sh` les exporte en `TF_VAR_…`, donc **pas de
`terraform.tfvars` à écrire**. L'état (`terraform/terraform.tfstate`) est local : ne le supprimez pas. En équipe,
rangez-le dans un bucket (bloc `backend "gcs"` commenté dans `versions.tf`).

## 1. Ce que Terraform crée

| Fichier `main.tf`, partie | Ressources |
|---|---|
| 1. API | 14 API (`aiplatform`, `documentai`, `discoveryengine`, `drive`, `run`, `cloudscheduler`, `cloudbuild`…) |
| 2. RAG | Corpus `rag-kit` (RagManagedDb KNN, embeddings `text-multilingual-embedding-002`) ; processeur Document AI `rag-kit-layout` (`eu`) ; palier RagManagedDb **seulement si** `RAG_TIER` est rempli |
| 3. Bucket | `<projet>-rag-kit` (privé, accès uniforme, rapports détaillés effacés après 30 j), `config.json`, droits de l'agent RAG |
| 4. Identités | `rag-kit-sa`, `rag-kit-scheduler-sa`, `rag-kit-build-sa` et leurs rôles ([07](07-droits-iam.md)) |
| 5. Image | Dépôt Artifact Registry `rag-kit` ; image construite par Cloud Build, étiquetée par le hachage du code |
| 6. Synchro | Job Cloud Run `rag-kit-sync`, ses droits, planification Cloud Scheduler |
| 7. Interface | Service Cloud Run `rag-kit` (privé, 1 instance max), droits des `USERS` |
| 8. Connexion Google | Secrets `rag-kit-oauth-client` et `rag-kit-google-tokens` et leurs droits ; clé du sélecteur `rag-kit-picker` ([04-bis](04-bis-connexion-google.md)) |
| 9. Push | Service **public** `rag-kit-hook` (notifications Drive), si `PUSH=true` |

## 2. Pas à pas

**2.1 Préparer** (une fois) : [02-prerequis](02-prerequis.md), dont :

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=<PROJET>
```

**2.2 Charger la configuration** (dans chaque nouveau terminal) :

```bash
cd gcp_rag/01-rag-engine-sync
source scripts/config.sh config/test.env
```

Résultat obtenu :

```
== Configuration chargée : config/test.env
   Projet     : main-project-511608 (numéro 246738341891), région europe-west4, préfixe rag-kit
   Modèle     : gemini-2.5-flash sur europe-west4 ; synchro « */10 * * * * » ; layout parser true
   Dossiers   : 1gYDE23jVl5GLPAe5Z8QbRVaMa0dtaKYM
   Interface  : user:noreply.syctra@gmail.com
   Partager chaque dossier Drive (Lecteur) avec :
     rag-kit-sa@main-project-511608.iam.gserviceaccount.com
     service-100000000005@gcp-sa-vertex-rag.iam.gserviceaccount.com
   OK
```

**2.3 Déployer :**

```bash
cd terraform
terraform init
terraform plan          # Plan: 42 to add, 0 to change, 0 to destroy.
terraform apply         # yes   (3 min 37 s mesurées, dont ≈ 2 min de construction d'image)
```

Fin obtenue :

```
Apply complete! Resources: 42 added, 0 changed, 0 destroyed.

Outputs:
bucket = "main-project-511608-rag-kit"
corpus = "projects/main-project-511608/locations/europe-west4/ragCorpora/8070450532247928832"
image = "europe-west4-docker.pkg.dev/main-project-511608/rag-kit/app:25d1c553bf6e"
ouvrir_interface = "gcloud run services proxy rag-kit --region=europe-west4 --project=main-project-511608 --port=8080"
partager_drive_avec = [
  "rag-kit-sa@main-project-511608.iam.gserviceaccount.com",
  "service-100000000005@gcp-sa-vertex-rag.iam.gserviceaccount.com",
]
url = "https://rag-kit-7wbgvvbhua-ez.a.run.app"
```

**2.4 Partager le dossier Drive** avec les 2 adresses `partager_drive_avec` ([04](04-connecter-drive.md)).

**2.5 Ouvrir l'interface :**

```bash
cd .. && bash scripts/ouvrir_interface.sh      # puis http://localhost:8080
```

Cliquez **Synchroniser maintenant** : en ≈ 20 s, l'état passe à `À jour` et les documents du dossier apparaissent.

## 3. Tester

Avec l'interface ouverte (proxy sur le port 8080), dans un **autre** terminal :

```bash
python3 scripts/test_e2e.py http://localhost:8080 "Quel est le numéro de contrat de la mutuelle ?" "PEL-8826-NG"
```

(Les 2 derniers arguments sont facultatifs : une question sur un de **vos** documents Drive et un mot attendu dans la
réponse.) Le test dépose un fichier avec un code unique, le modifie, le supprime, et vérifie à chaque fois l'index
**et** la réponse de l'agent (≈ 2 min). Résultat obtenu :

```
[1] l'API répond
    OK  corpus projects/main-project-511608/locations/europe-west4/ragCorpora/8070450532247928832
[2] dépôt de e2e-szjj-9040.txt (code SZJJ-9040) puis synchro
    OK  déposé : ['e2e-szjj-9040.txt'] (synchro lancee)
    OK  synchro ok en 8.5 s
    OK  e2e-szjj-9040.txt indexé (origine dépôt)
    OK  l'agent répond SZJJ-9040  (réponse : "Le code d'accès du local à vélos du bâtiment Héron est SZJJ-9040 [e2e-szjj-9040.txt](https://storage.cloud.google.com/m…")
    OK  et cite le fichier
[3] modification : nouveau code FYWX-4924
    ..  dernière passe : {'source': 'Fichiers déposés', 'importes': 1, 'inchanges': 0, 'echecs': 0}
    OK  l'agent répond FYWX-4924 (plus SZJJ-9040)  (réponse : "Le code d'accès du local à vélos du bâtiment Héron est FYWX-4924.\n\nSources :\n[e2e-szjj-9040.txt](ht…")
[4] suppression
    ..  dernière passe : 1 retiré(s)
    OK  e2e-szjj-9040.txt absent de l'index
    OK  l'agent ne connaît plus le code
[5] Drive : « Quel est le numéro de contrat de la mutuelle ? »
    OK  réponse contient « PEL-8826-NG »  ('Le numéro de contrat de groupe de la mutuelle est PEL-8826-NG. [mutuelle-2026](https://docs.google.com/document/d/1tZU5r6…")
    OK  avec un lien Drive

TOUT EST OK
```

## 4. Modifier

| Je veux… | Je fais… | `apply` fait |
|---|---|---|
| Changer la fréquence de synchro | `SYNC_SCHEDULE` dans le `.env` | 1 modification (planification) |
| Ajouter des utilisateurs | `USERS="user:a@x.com group:b@x.com"` | +1 droit par personne |
| Changer de modèle | `MODEL`, `MODEL_LOCATION` | Service et job mis à jour |
| Modifier le code (`app/…`) | Éditer les fichiers | Nouvelle image, nouvelle révision du service et du job |

Après chaque modification du `.env` : `source scripts/config.sh …` **puis** `terraform apply`.

**Relance sans changement** : `terraform plan` → `No changes. Your infrastructure matches the configuration.`

## 5. Supprimer

```bash
terraform destroy       # yes   → Destroy complete! Resources: 42 destroyed.
```

> **Après un `destroy` puis un nouvel `apply`, repartagez vos dossiers Drive avec `rag-kit-sa@…`** (vérifié) : le
> compte recréé a la même adresse mais c'est une nouvelle identité pour Google ; l'ancien partage devient une
> permission orpheline (sans adresse) dans Drive. Le kit le signale : « Drive « … » illisible (introuvable : plus
> partagé avec rag-kit-sa@…) ». L'agent de service RAG, lui, n'est jamais recréé : son partage reste valable.

Puis, si plus rien n'utilise RAG Engine dans le projet : [10, partie 3](10-tout-supprimer.md#3-arrêter-le-coût-fixe-ragmanageddb)
pour arrêter le coût fixe.

## 6. Ce qui peut arriver

Voir [09-depannage, partie 1](09-depannage.md#1-déploiement). Les deux plus fréquents : l'API Cloud Resource Manager
non activée (2.1), et le 1er essai de construction d'image en `403` (réessayé automatiquement).
