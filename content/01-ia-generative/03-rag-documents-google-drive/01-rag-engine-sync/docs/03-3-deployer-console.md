# 03-3. Déployer avec la **console** Google Cloud (à la souris)

**Le but :** créer le kit écran par écran, pour comprendre chaque pièce ou quand on n'a pas de terminal. Même
résultat que [03-1 Shell](03-1-deployer-shell.md) et [03-2 Terraform](03-2-deployer-terraform.md).

> **Statut :** les parties marquées 🖥️ se font dans la console ; deux étapes n'existent **pas** dans la console
> (construction de l'image, création du corpus avec un modèle d'embeddings précis) et se font dans **Cloud Shell**
> (le terminal intégré à la console, bouton `>_` en haut à droite) : rien à installer sur votre poste.
> Les écrans décrits sont ceux d'octobre 2026 ; les commandes Cloud Shell sont celles du script shell, testées.

Remplacez partout `PROJET` par l'ID de votre projet, `NUMERO` par son numéro (page d'accueil de la console,
carte « Infos sur le projet »), et gardez la région `europe-west4`.

---

## 1. Activer les API 🖥️

**API et services** → **Bibliothèque**, puis pour chacune : rechercher, **Activer**.
Cloud Resource Manager, Vertex AI (« Agent Platform »), Document AI, Discovery Engine, Google Drive, Cloud Run,
Cloud Scheduler, Cloud Build, Artifact Registry, Cloud Storage, IAM.

Plus rapide, dans Cloud Shell : l'étape 1 de `scripts/deployer_shell.sh`.

## 2. Créer les comptes de service 🖥️

**IAM et administration** → **Comptes de service** → **Créer un compte de service**, trois fois :

| ID | Rôles à donner (étape « Accorder à ce compte l'accès au projet ») |
|---|---|
| `rag-kit-sa` | Utilisateur Vertex AI (`aiplatform.user`), Lecteur Discovery Engine (`discoveryengine.viewer`), Rédacteur de journaux, Rédacteur de métriques Monitoring, Agent Cloud Trace, Rédacteur de télémétrie |
| `rag-kit-scheduler-sa` | aucun (droit donné sur le job à l'étape 7) |
| `rag-kit-build-sa` | Lecteur des objets Storage, Rédacteur Artifact Registry, Rédacteur de journaux |

## 3. Créer le bucket 🖥️

**Cloud Storage** → **Buckets** → **Créer** : nom `PROJET-rag-kit`, région `europe-west4`, classe Standard,
**Appliquer la protection contre l'accès public**, contrôle d'accès **Uniforme**. Puis onglet **Autorisations** →
**Accorder l'accès** :

| Principal | Rôle |
|---|---|
| `rag-kit-sa@PROJET.iam.gserviceaccount.com` | Administrateur des objets Storage |
| `service-NUMERO@gcp-sa-vertex-rag.iam.gserviceaccount.com` | Lecteur des objets Storage **et** Créateur des objets Storage |

> L'agent de service RAG n'existe qu'après la première utilisation de RAG Engine : faites l'étape 4 d'abord si la
> console refuse l'adresse.

## 4. Créer le corpus (Cloud Shell)

La console (**Vertex AI → RAG Engine → Créer un corpus**) permet de le créer, mais choisissez bien
**Région `europe-west4`**, base **RagManagedDb**, modèle d'embeddings **`text-multilingual-embedding-002`**.
`gemini-embedding-001` est refusé (vérifié). Nom : `rag-kit`. Ou, dans Cloud Shell, l'étape 5 du script.

Notez le nom complet du corpus (`projects/…/locations/europe-west4/ragCorpora/<numéro>`) : il sert à l'étape 7.

## 5. Créer le layout parser 🖥️

**Document AI** → **Galerie des processeurs** → **Layout Parser** → **Créer** : nom `rag-kit-layout`, région **UE**.
Notez son nom complet (`projects/NUMERO/locations/eu/processors/<id>`).

## 6. Construire l'image (Cloud Shell)

```bash
# Dans Cloud Shell : menu ⋮ → Importer → le dossier 01-rag-engine-sync, puis :
cd 01-rag-engine-sync
gcloud artifacts repositories create rag-kit --repository-format=docker --location=europe-west4
gcloud builds submit app --region=europe-west4 --config=app/cloudbuild.yaml \
  --service-account=projects/PROJET/serviceAccounts/rag-kit-build-sa@PROJET.iam.gserviceaccount.com \
  --substitutions=_IMAGE=europe-west4-docker.pkg.dev/PROJET/rag-kit/app:v1
```

## 7. Créer le job de synchro 🖥️

**Cloud Run** → **Jobs** → **Déployer un conteneur** :

- Image : `europe-west4-docker.pkg.dev/PROJET/rag-kit/app:v1` ; nom `rag-kit-sync` ; région `europe-west4`.
- **Conteneur** → **Commande** : `python`, **Arguments** : `sync_job.py`. 1 Gio, 1 processeur.
- **Variables** : voir le tableau ci-dessous.
- **Sécurité** → compte de service `rag-kit-sa`. **Tâches** : 1, **nouvelles tentatives** : 0, **délai** : 3600 s.
- Une fois créé, onglet **Autorisations** : `rag-kit-sa` → *Demandeur Cloud Run* **et** *Lecteur Cloud Run* ;
  `rag-kit-scheduler-sa` → *Demandeur Cloud Run*.
- Onglet **Déclencheurs** → **Ajouter un déclencheur de programmeur** : fréquence `*/10 * * * *`, fuseau
  Europe/Paris, compte `rag-kit-scheduler-sa`.

| Variable | Valeur |
|---|---|
| `PROJECT_ID` / `GOOGLE_CLOUD_PROJECT` | `PROJET` |
| `PROJECT_NUMBER` | `NUMERO` |
| `REGION` | `europe-west4` |
| `BUCKET` | `PROJET-rag-kit` |
| `CORPUS` | nom complet de l'étape 4 |
| `LAYOUT_PARSER` | nom complet de l'étape 5 (vide = parsing simple) |
| `SYNC_JOB` | `rag-kit-sync` |
| `SA_EMAIL` | `rag-kit-sa@PROJET.iam.gserviceaccount.com` |
| `MODEL` | `gemini-2.5-flash` |
| `GOOGLE_GENAI_USE_VERTEXAI` | `true` |
| `GOOGLE_CLOUD_LOCATION` | `europe-west4` |
| `OTEL_TO_CLOUD` | `true` |

## 8. Créer le service (interface + agent) 🖥️

**Cloud Run** → **Services** → **Déployer un conteneur** : même image, nom `rag-kit`, région `europe-west4`,
**Authentification : Exiger l'authentification**, instances 0 à **1**, 1 Gio, compte `rag-kit-sa`, **mêmes
variables** qu'à l'étape 7. Puis onglet **Sécurité/Autorisations** → ajoutez vos collègues en *Demandeur Cloud Run*.

## 9. Utiliser

Dans Cloud Shell : `gcloud run services proxy rag-kit --region=europe-west4 --port=8080`, puis
**Aperçu sur le Web** (icône en haut de Cloud Shell) → port 8080. La suite : [04](04-connecter-drive.md) et
[05](05-utiliser-interface.md).

## 10. Supprimer 🖥️

Dans l'ordre : service, job (et son déclencheur), corpus (Vertex AI → RAG Engine), processeur Document AI, dépôt
Artifact Registry, bucket, comptes de service. Ou `scripts/supprimer_shell.sh` dans Cloud Shell.
