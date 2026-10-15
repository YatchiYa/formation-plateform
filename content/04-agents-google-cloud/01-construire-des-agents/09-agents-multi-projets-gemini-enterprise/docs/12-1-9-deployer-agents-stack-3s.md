# 12-1-9. Déployer les agents « à la 3S » : GitHub Actions + Terraform, sans `gcloud auth login`

**Le but :** déployer **les mêmes agents** qu'en [12-1-1 (shell)](12-1-1-deployer-agents-shell.md) et
[12-1-2 (Terraform)](12-1-2-deployer-agents-terraform.md), mais comme une équipe Acme le fait sur la **3S** :
personne ne lance `terraform apply` depuis son poste. On pousse du code sur GitHub, une **pull request** est relue,
et le **merge sur `main`** déploie, avec une identité de pipeline, un état Terraform partagé et **aucune clé**.

**Le dossier :** [`03-bis-stack-3s/`](../03-bis-stack-3s/README.md). Il **réutilise** le Terraform du
[01-bis](../01-bis-cloud-run-a2a/README.md) tel quel (aucune copie) : seul le **chemin** jusqu'à `apply` change.

> **Ce qu'est la 3S, et ce que ce guide n'invente pas.** La 3S (*Self Service Stack*) est la plateforme cloud
> **interne** de Acme, sur GCP. Ce qui en est public (offres d'emploi, présentations) : GCP (Cloud Run, GKE),
> Terraform, GitHub Actions, FluxCD (GitOps sur GKE), Aiven (PostgreSQL, Kafka), Datadog / OpenTelemetry. Ses modules,
> ses noms de projets et son portail sont **internes** : ce guide ne les reproduit pas. Il construit **le même
> modèle** (Git → pipeline → Terraform → GCP) sur un projet à vous, pour comprendre ce que la 3S fait à votre place
> et savoir quoi demander à l'équipe 3S. Là où la 3S fournit déjà la brique, c'est indiqué **« 3S : »**.

> **Vérifié** (15 octobre 2026, projet de test `second-project-511608`) : `terraform validate` et `fmt` du socle, du
> déploiement et du workflow ; **`terraform plan` réels** du socle (24 ressources) et du déploiement (1 agent : 23,
> 2 agents : 31, tous : 87). Ce test a trouvé un **défaut du 01-bis et du 02-bis**, corrigé : avec `agents = ["meteo"]`,
> le plan échouait (« Inconsistent conditional result types »), car les agents du catalogue n'ont pas tous les mêmes
> champs. **Pas encore exécuté :** `terraform apply` du socle et le premier passage du workflow dans GitHub (parties 3 à 6).

---

## Sommaire

0. [Les mots à connaître](#0-les-mots-à-connaître)
1. [Ce qui change par rapport à 12-1-1 et 12-1-2](#1-ce-qui-change-par-rapport-à-12-1-1-et-12-1-2)
2. [Pourquoi Cloud Run, et pas GKE + FluxCD](#2-pourquoi-cloud-run-et-pas-gke--fluxcd)
3. [Le socle : bucket d'état, compte de déploiement, confiance GitHub (une fois)](#3-le-socle-une-fois)
4. [Brancher le dépôt GitHub](#4-brancher-le-dépôt-github)
5. [Déployer : une pull request, puis un merge](#5-déployer--une-pull-request-puis-un-merge)
6. [Tester le pipeline sans GitHub (option)](#6-tester-le-pipeline-sans-github-option)
7. [Ajouter un agent, en retirer un, connecter l'app](#7-ajouter-un-agent-en-retirer-un-connecter-lapp)
8. [Tout nettoyer](#8-tout-nettoyer)
9. [Ce qui peut arriver](#9-ce-qui-peut-arriver)
10. [Ce qu'il faut demander à l'équipe 3S](#10-ce-quil-faut-demander-à-léquipe-3s)

---

## 0. Les mots à connaître

| Mot | En clair |
|---|---|
| **3S** | *Self Service Stack* : la plateforme interne de Acme qui donne aux équipes un projet GCP, des modules Terraform et un pipeline, déjà conformes (sécurité, réseau, observabilité). |
| **GitOps** | Git est la **source de vérité** : ce qui est sur `main` est ce qui tourne. On change l'infrastructure par une pull request, jamais à la main. |
| **GitHub Actions** | Les pipelines de GitHub : un fichier YAML dans `.github/workflows/` lancé à chaque push ou pull request. |
| **Workload Identity Federation (WIF)** | Google fait confiance au **jeton OIDC** que GitHub donne à chaque exécution. Le pipeline obtient un jeton Google **sans clé** de compte de service. |
| **Compte de déploiement** | `agents-deployer-sa` : l'identité du pipeline. C'est **lui** qui crée les agents, plus votre compte personnel. |
| **État Terraform distant** | Le fichier d'état est dans un **bucket GCS** partagé (versionné), et non sur un poste : tout le monde, et le pipeline, voient le même. |
| **Socle** (*bootstrap*) | Ce qu'on crée **une fois**, avant le pipeline : le bucket, le compte de déploiement, la confiance GitHub. **3S :** fourni par la plateforme. |

---

## 1. Ce qui change par rapport à 12-1-1 et 12-1-2

```
 12-1-2 (Terraform local)                         12-1-9 (« à la 3S »)
 ┌────────────┐                                   ┌────────────┐  PR   ┌──────────────────────┐ merge ┌──────────────────────────┐
 │ votre poste │ gcloud auth login               │ votre poste │ ────▶ │ GitHub : relecture   │ ────▶ │ GitHub Actions           │
 │ terraform   │ terraform apply ──▶ GCP          │ git push    │       │ + terraform validate │       │ jeton OIDC ─▶ WIF ─▶     │
 │ état local  │ (votre compte, vos droits)       └────────────┘       └──────────────────────┘       │ agents-deployer-sa       │
 └────────────┘                                                                                      │ terraform plan + apply   │
                                                                                                     │ état : bucket GCS        │
                                                                                                     └────────────┬─────────────┘
                                                                                                                  ▼
                                                              Projet des agents : exactement les ressources du 01-bis
                                                              (images Cloud Build, Cloud Run privés, identités, Agent Registry)
```

| | 12-1-2 Terraform local | 12-1-9 « à la 3S » |
|---|---|---|
| Qui lance `apply` | Vous, sur votre poste | Le pipeline, au merge sur `main` |
| Avec quels droits | Les vôtres (souvent Owner) | Ceux de `agents-deployer-sa`, listés et limités |
| Où est l'état | `terraform.tfstate.d/` sur le poste | `gs://<projet>-tfstate/09-agents-a2a/` |
| Où sont les valeurs | `config/…env` ou `terraform.tfvars` (non versionné) | `03-bis-stack-3s/deploy/agents.auto.tfvars` (**versionné**) |
| Clé de compte de service | — | **Aucune** (WIF) |
| Code Terraform des agents | `01-bis-cloud-run-a2a/terraform` | **Le même**, appelé comme module |

**Les fichiers :**

| Fichier | Rôle |
|---|---|
| `03-bis-stack-3s/bootstrap/` | Le socle, appliqué **une fois** par un administrateur du projet. **3S :** déjà fait pour vous |
| `03-bis-stack-3s/deploy/main.tf` | Le backend GCS + l'appel du module `../../01-bis-cloud-run-a2a/terraform` |
| `03-bis-stack-3s/deploy/agents.auto.tfvars` | **La** configuration déployée : projet, agents, numéro du projet de l'app |
| `03-bis-stack-3s/github/deploy-agents.yml` | Le workflow GitHub Actions, à copier dans `.github/workflows/` |

---

## 2. Pourquoi Cloud Run, et pas GKE + FluxCD

La 3S propose aussi GKE avec FluxCD (des manifestes Kubernetes dans Git, synchronisés par Flux). Pour **ces** agents,
on reste sur **Cloud Run** :

1. **Gemini Enterprise appelle un agent A2A avec son propre compte** (`service-NUM_APP@gcp-sa-discoveryengine…`) et
   un jeton d'identité Google. Cloud Run vérifie ce jeton tout seul (`run.invoker`). Sur GKE, il faudrait exposer
   l'agent (Ingress, certificat, IAP ou vérification du jeton dans le code) : plus de pièces, même résultat.
2. **L'URL `.run.app` est exigée** pour l'authentification automatique (voir [01-bis, partie 1](../01-bis-cloud-run-a2a/README.md#1-comprendre-ce-qui-va-être-créé)).
3. **Coût** : Cloud Run descend à 0 instance ; un agent peu utilisé ne coûte presque rien.

GKE + FluxCD reste le bon choix pour une API métier qui tourne déjà sur le cluster de l'équipe. L'agent, lui, peut
**appeler** cette API depuis Cloud Run.

---

## 3. Le socle (une fois)

> **3S :** sautez cette partie. Demandez à l'équipe 3S les trois valeurs de la partie 4 (fournisseur WIF, compte de
> déploiement, bucket d'état) et vérifiez que le compte a les rôles de la liste ci-dessous.

**Qui :** un administrateur du projet des agents (rôle Owner, ou `resourcemanager.projectIamAdmin` +
`iam.workloadIdentityPoolAdmin` + `iam.serviceAccountAdmin` + `storage.admin`), **depuis son poste**, une seule fois.

```bash
cd 09-agents-multi-projets-gemini-enterprise/03-bis-stack-3s/bootstrap
gcloud auth application-default login
cp terraform.tfvars.example terraform.tfvars   # projet des agents + dépôt GitHub « organisation/depot »
terraform init
terraform plan     # 24 ressources à créer
terraform apply
terraform output github_variables
```

**Ce que le socle crée :**

| Ressource | Pourquoi |
|---|---|
| Bucket `<projet>-tfstate` (versionné, jamais public) | L'état Terraform partagé ; le versionnement permet de revenir en arrière |
| Compte `agents-deployer-sa` + 12 rôles | L'identité du pipeline : exactement ce que le 01-bis (et le projet 10) créent |
| Pool WIF `github` + fournisseur `github-oidc` | Google accepte les jetons de GitHub, **seulement** ceux de votre dépôt (`attribute_condition`) |
| `workloadIdentityUser` sur le compte | **Seule la branche `main`** peut emprunter le compte (`…:ref:refs/heads/main`) |

**Les 12 rôles du compte de déploiement**, et pourquoi (`bootstrap/variables.tf`) :

| Rôle | Pour |
|---|---|
| `serviceusage.serviceUsageAdmin` | Activer les API (Cloud Run, Vertex AI, Agent Registry…) |
| `iam.serviceAccountAdmin` | Créer l'identité de chaque agent |
| `iam.serviceAccountUser` | Attacher ces identités aux services ; lancer Cloud Build avec `agents-a2a-build-sa` |
| `resourcemanager.projectIamAdmin` | Donner à chaque identité ses rôles (`aiplatform.user`, `logging.logWriter`…) |
| `artifactregistry.admin` | Le dépôt d'images `agents-a2a` |
| `cloudbuild.builds.editor`, `storage.admin`, `logging.viewer` | `gcloud builds submit` : envoyer le code, construire, suivre le journal |
| `run.admin` | Les services Cloud Run et leur droit d'appel (`run.invoker` de Gemini Enterprise) |
| `modelarmor.admin` | Les templates Model Armor (si non fournis par le projet 08) |
| `agentregistry.admin` | Les entrées Agent Registry |
| `aiplatform.admin` | L'agent Agent Runtime du projet 10 (option) |

> **Attention, `projectIamAdmin` est puissant :** le compte peut se donner d'autres rôles. C'est pour cela que seul
> `main` (branche **protégée**, relecture obligatoire) peut l'utiliser. En production, on peut le restreindre avec une
> condition IAM qui liste les rôles qu'il a le droit de donner. **3S :** c'est le genre de règle que la plateforme pose.

---

## 4. Brancher le dépôt GitHub

1. **Copier le workflow** à la racine du dépôt (GitHub ne lit que `.github/workflows/`) :

   ```bash
   mkdir -p .github/workflows
   cp 09-agents-multi-projets-gemini-enterprise/03-bis-stack-3s/github/deploy-agents.yml .github/workflows/
   ```

   Si le dossier `09-…` n'est pas à la racine de votre dépôt, corrigez `paths` et `WORKDIR` dans le fichier.

2. **Les 3 variables** (pas des secrets, rien de sensible) : GitHub → **Settings** → **Secrets and variables** →
   **Actions** → onglet **Variables** → **New repository variable**, avec la sortie `github_variables` :

   | Variable | Exemple |
   |---|---|
   | `GCP_WIF_PROVIDER` | `projects/100000000002/locations/global/workloadIdentityPools/github/providers/github-oidc` |
   | `GCP_DEPLOYER_SA` | `agents-deployer-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com` |
   | `GCP_TFSTATE_BUCKET` | `aiml-gemini-ent-exp-0zga-tfstate` |

3. **Protéger `main`** : **Settings** → **Branches** → règle sur `main` : pull request obligatoire, 1 relecture,
   le contrôle `verifier` doit passer.

4. **Option, approbation manuelle avant chaque déploiement :** **Settings** → **Environments** → `production` →
   **Required reviewers**. Le job `deployer` attend alors un clic « Approve ».

---

## 5. Déployer : une pull request, puis un merge

**Choisir les agents** dans `03-bis-stack-3s/deploy/agents.auto.tfvars` :

```hcl
agents_project_id = "aiml-gemini-ent-exp-0zga"
ge_project_number = ""          # rempli à la partie 7
agents            = ["meteo"]   # [] = tous les agents de agents/trio/catalogue.json
```

```bash
git switch -c agents/meteo
git add 09-agents-multi-projets-gemini-enterprise/03-bis-stack-3s/deploy/agents.auto.tfvars
git commit -m "agents : déployer meteo"
git push -u origin agents/meteo      # puis ouvrir la pull request sur GitHub
```

**Sur la pull request**, le job `verifier` lance `terraform fmt -check` et `terraform validate`, **sans accès** à
Google Cloud (le jeton d'une PR ne peut pas emprunter le compte, partie 3). Un relecteur approuve, on merge.

**Sur `main`**, le job `deployer` :

| Étape | Ce qui se passe | Durée |
|---|---|---|
| `google-github-actions/auth` | Jeton OIDC GitHub → jeton Google de `agents-deployer-sa` | 5 s |
| `terraform init` | État lu dans `gs://…-tfstate/09-agents-a2a/` | 10 s |
| `terraform plan` | 23 ressources pour `meteo` au premier passage (vérifié) | 30 s |
| `terraform apply` | Comme au 01-bis : API, identités, **image construite par Cloud Build**, service Cloud Run privé, Agent Registry | 4 à 6 min |

**Vérifier** : les journaux du job (onglet **Actions** du dépôt), puis la console (Cloud Run → `meteo-a2a`, Agent
Registry → région `europe-west1`) ou le test A2A du 01-bis :

```bash
cd 09-agents-multi-projets-gemini-enterprise/01-bis-cloud-run-a2a && ./test.sh
```

---

## 6. Tester le pipeline sans GitHub (option)

Pour vérifier que le compte de déploiement **suffit** (aucun rôle oublié), on peut jouer le pipeline depuis son poste
en **empruntant** ce compte. Il faut, une fois, le droit de l'emprunter :

```bash
PROJET=aiml-gemini-ent-exp-0zga
SA=agents-deployer-sa@$PROJET.iam.gserviceaccount.com
gcloud iam service-accounts add-iam-policy-binding $SA --project=$PROJET \
  --member="user:$(gcloud config get-value account)" --role=roles/iam.serviceAccountTokenCreator

cd 09-agents-multi-projets-gemini-enterprise/03-bis-stack-3s/deploy
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT=$SA                 # Terraform agit en tant que le compte
export CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT=$SA           # gcloud builds submit aussi
terraform init -backend-config=bucket=$PROJET-tfstate
terraform plan
terraform apply
unset GOOGLE_IMPERSONATE_SERVICE_ACCOUNT CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT
```

Un `403 Permission denied` désigne le rôle manquant : ajoutez-le à `roles` dans `bootstrap/variables.tf`, puis
`terraform apply` dans `bootstrap/`. Retirez ensuite votre droit d'emprunt (`remove-iam-policy-binding`, mêmes options).

---

## 7. Ajouter un agent, en retirer un, connecter l'app

Toujours **une pull request** sur `agents.auto.tfvars` :

| Je veux | Je change | Effet au merge |
|---|---|---|
| Ajouter `taille` | `agents = ["meteo", "taille"]` | Image, identité, service, entrée de registre de `taille` (8 ressources) ; `meteo` intact |
| Retirer `meteo` | `agents = ["taille"]` | **Supprime** les ressources de `meteo` (le `plan` du job le montre : à relire) |
| Donner l'accès à l'app | `ge_project_number = "<NUMÉRO du projet de l'app>"` | `run.invoker` pour le compte de Gemini Enterprise sur chaque agent |
| Modifier le code d'un agent | `agents/trio/<agent>/…` | Nouvelle empreinte → nouvelle image → nouvelle révision de **cet** agent |

L'ajout dans l'app Gemini Enterprise reste l'étape de l'**admin de l'app** : [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md)
et [12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md). Publier depuis le pipeline (`ge_app_id`) est possible,
mais il faut alors donner au compte de déploiement un rôle d'admin Gemini Enterprise **dans le projet de l'app** :
à décider avec l'admin de l'app, pas par défaut.

---

## 8. Tout nettoyer

```bash
# 1. Les agents (avec le compte du pipeline, partie 6, ou un compte Owner)
cd 09-agents-multi-projets-gemini-enterprise/03-bis-stack-3s/deploy
terraform init -backend-config=bucket=<PROJET>-tfstate
terraform destroy

# 2. Le socle (supprime aussi le bucket d'état : à faire en dernier)
cd ../bootstrap && terraform destroy
```

Puis retirer `.github/workflows/deploy-agents.yml` et les 3 variables du dépôt. Le pool WIF supprimé reste
**30 jours** en état « supprimé » : recréer un pool `github` avant ce délai demande `gcloud iam workload-identity-pools undelete github --location=global`.

---

## 9. Ce qui peut arriver

| Symptôme | Cause | Solution |
|---|---|---|
| `Unable to exchange token` / `unauthorized_client` dans `auth` | Le dépôt ne correspond pas à `github_repo` (casse comprise) ou le job ne tourne pas sur `main` | Vérifier `github_repo` et la branche ; une PR n'a pas le droit (voulu) |
| `id-token` absent | `permissions: id-token: write` manquant | Le garder dans le workflow |
| `Error acquiring the state lock` | Un autre `apply` en cours, ou un job interrompu | Attendre ; sinon `terraform force-unlock <ID>` (l'ID est dans le message) |
| `403` sur `cloudbuild` ou `storage` pendant l'image | Rôle manquant au compte de déploiement | Partie 6, puis ajouter le rôle au socle |
| `Inconsistent conditional result types` | Ancien 01-bis (avant le 15 octobre 2026) | Mettre à jour le dépôt (corrigé) |
| Le plan veut **recréer** des agents déjà déployés en local | État local (12-1-2) et état GCS distincts | Migrer l'état (même méthode que [10-15, partie 5](../../10-mcp-google-sheets-gemini-enterprise/docs/10-15-deployer-stack-3s.md#5-déjà-déployé-avec-10-3-sur-le-poste-), vérifiée), avec `module.agents.` comme préfixe ; ou détruire en local avant |

---

## 10. Ce qu'il faut demander à l'équipe 3S

1. Le **projet** des agents, et s'il est déjà relié à un dépôt GitHub par la 3S (fournisseur WIF, compte de déploiement).
2. Le **bucket d'état** (et son préfixe) à utiliser.
3. Les **rôles** du compte de déploiement : comparer à la liste de la partie 3 ; ceux qui manquent sont souvent
   `agentregistry.admin` et `modelarmor.admin` (services récents).
4. Si la 3S impose **ses modules Terraform** (Cloud Run, comptes de service) : le 01-bis s'y adapte en remplaçant ses
   ressources `google_cloud_run_v2_service` et `google_service_account` par ces modules ; la carte A2A, Agent
   Registry et le droit de Gemini Enterprise restent identiques.
5. Les règles d'**organisation** (VPC-SC, domaines autorisés, régions) : [docs/05](05-droits-et-regions.md).
