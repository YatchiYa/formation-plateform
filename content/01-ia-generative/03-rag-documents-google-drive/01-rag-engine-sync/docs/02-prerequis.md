# 02. Prérequis : poste, compte, projet

**Le but :** avoir tout ce qu'il faut avant de déployer, et le vérifier en 5 minutes.

---

## 1. Sur votre poste

| Outil | Version testée | Vérifier | Installer |
|---|---|---|---|
| Google Cloud CLI (`gcloud`) | 587.0.0 | `gcloud --version` | <https://cloud.google.com/sdk/docs/install> |
| Terraform (méthode Terraform seulement) | 1.16.0 | `terraform version` | <https://developer.hashicorp.com/terraform/install> |
| Python 3 (pour les scripts ; bibliothèque standard seulement) | 3.10+ | `python3 --version` | déjà présent sur Mac/Linux |
| `curl`, `bash` | — | — | déjà présents |

**Pas besoin de Docker** : l'image est construite dans Google Cloud (Cloud Build).

Pour lancer l'application **sur votre poste** (facultatif, [05](05-utiliser-interface.md#5-lancer-en-local)) :
Python 3.12 et `pip install -r app/requirements.txt`.

## 2. Votre compte Google

```bash
gcloud auth login                         # votre compte (ouvre le navigateur)
gcloud auth application-default login     # identifiants pour Terraform et les bibliothèques Python
```

Droits nécessaires sur le projet : **Propriétaire** (`roles/owner`), le plus simple pour un premier déploiement. Pour
un compte non propriétaire, la liste minimale est en [07, partie 4](07-droits-iam.md#4-qui-déploie--droits-minimaux).

## 3. Le projet Google Cloud

- **Facturation active** : `gcloud billing projects describe <PROJET> --format='value(billingEnabled)'` → `True`.
- **Une seule API à activer à la main**, car Terraform en a besoin pour activer les autres (vérifié : sans elle,
  `Cloud Resource Manager API has not been used in project … before or it is disabled`) :

```bash
gcloud services enable cloudresourcemanager.googleapis.com --project=<PROJET>
```

Le script shell l'active lui-même ; Terraform active toutes les autres (14 API).

- **Pas besoin d'organisation ni de Google Workspace** : le kit a été testé sur un projet personnel (compte Gmail).

## 4. Choisir la région

| Région | RAG Engine | `gemini-2.5-flash` | `gemini-3.5-flash` | Remarque |
|---|---|---|---|---|
| `europe-west4` (Pays-Bas) | GA | régional | via `global` seulement | **Défaut du kit**, testé |
| `europe-west3` (Francfort) | GA | non vérifié | non vérifié | Non testé ici |
| `us-central1` | GA (+ mode Serverless en préversion) | non vérifié | non vérifié | Hors UE, non testé |

**Le modèle par défaut est `gemini-2.5-flash` en `europe-west4`** : tout (corpus, bucket, service, parseur
Document AI `eu`, modèle) reste dans l'UE, et c'est le plus fiable mesuré sur le projet de test (6 appels sur 6 en
≈ 1 s). `gemini-3.5-flash`, plus récent, n'existe qu'en `global` (vérifié : 404 en `europe-west4`), et sur le projet
de test sa capacité partagée était instable (`429 RESOURCE_EXHAUSTED` 1 fois sur 2, un appel bloqué 87 s). Pour
l'essayer : `MODEL=gemini-3.5-flash` et `MODEL_LOCATION=global` (le kit règle alors sa réflexion sur « basse »).

## 5. Le palier RAG Engine

`RAG_TIER=basic` (valeur fournie) : le déploiement active la base RagManagedDb du projet si elle ne l'est pas (projet
neuf, ou déprovisionné par [10, partie 3](10-tout-supprimer.md#3-arrêter-le-coût-fixe-ragmanageddb)). Coût fixe
≈ 91 €/mois tant qu'elle est active ([08](08-couts.md)). Elle est partagée par tous les corpus du projet dans la région.

## 6. Remplir la configuration

```bash
cd gcp_rag/01-rag-engine-sync
cp config/test.env config/moi.env      # puis éditez config/moi.env
source scripts/config.sh config/moi.env
```

Le résumé doit finir par `OK` et afficher les 2 adresses de partage Drive. Le détail de chaque variable est dans
le fichier lui-même et dans la [spec, partie 5](00-spec.md#5-configuration-confignomenv).

> **Le numéro de l'agent de service RAG** (`service-<numéro>@gcp-sa-vertex-rag…`) est calculé à partir du numéro
> du projet. Le compte lui-même est créé par Google à la première utilisation de RAG Engine (le déploiement s'en
> charge en créant le corpus).
