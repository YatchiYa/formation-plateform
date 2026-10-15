# 01. Préparer Terraform et reprendre ce qui a été fait en console

**Pour qui :** DevOps / plateforme. **Durée :** une demi-journée.

---

## 1. Se connecter

Terraform utilise les **identifiants applicatifs** (ADC), pas ceux de la commande `gcloud`. Il faut les deux :

```bash
gcloud auth login                          # pour gcloud
gcloud auth application-default login      # pour Terraform et les scripts Python
gcloud config set project acme-ge-recette
```

En CI, pas de connexion manuelle : la CI utilise une fédération d'identité (fiche [06](06-ci-cd.md)).

---

## 2. Un état distant, partagé et protégé

L'**état** (`terraform.tfstate`) est la mémoire de Terraform : la liste de ce qu'il a créé. En équipe, il doit être
**partagé** (un seul état, pas un par poste), **verrouillé** (deux `apply` en même temps = corruption) et **protégé**
(il contient des identifiants de ressources).

```bash
gcloud storage buckets create gs://acme-tfstate-gemini-enterprise \
  --location=EU --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://acme-tfstate-gemini-enterprise --versioning   # retour arrière possible
```

Puis décommenter dans `terraform/versions.tf` :

```hcl
backend "gcs" {
  bucket = "acme-tfstate-gemini-enterprise"
  prefix = "securite-acme/recette"      # un préfixe par environnement / domaine
}
```

Accès au bucket : **lecture/écriture pour le compte de la CI seulement**, lecture pour l'équipe plateforme. Le verrou
est natif avec le backend GCS.

> Si Acme a déjà un service Terraform managé (voir le guide Terraform et le projet 07), c'est **lui** qui porte
> l'état : ne pas créer ce bucket, utiliser le backend fourni.

---

## 3. Remplir `terraform.tfvars`

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars     # ne JAMAIS committer ce fichier (.gitignore)
```

| Section du fichier | À remplir avec | Qui fournit |
|---|---|---|
| `project_id` | ID du projet | Plateforme |
| `user_groups`, `admin_groups`, `security_groups`, `viewer_groups` | Groupes au format `group:nom@acme.example` | Admins Workspace / Entra |
| `alert_email` | Boîte de l'équipe sécurité | Sécurité |
| `connectors` | Une entrée par source (voir docs/00 §7) | Admins GE + propriétaires des sources |
| Palier A : `armor_agent_platform_mode`, `agent_developer_groups` | `"inspect"`, groupe développeurs | Sécurité, plateforme |
| Paliers B, C, D | Laisser commenté au début | — |

Les valeurs fausses sont arrêtées **avant** d'appeler Google : `variables.tf` contient des `validation`
(ex. `armor_agent_platform_mode` n'accepte que `off`, `inspect`, `block`).

---

## 4. Premier `init` et `validate`

```bash
terraform init          # télécharge le provider google 8.x et external, configure l'état
terraform validate      # vérifie la syntaxe et les types, sans appeler Google
```

---

## 5. Reprendre ce qui a été créé en console (`import`)

**Le problème.** En phase 1, des ressources ont été créées à la main (templates, plancher, buckets…). Si Terraform
essaie de les **créer**, Google répond « already exists » et l'`apply` échoue.

**La solution.** Dire à Terraform : « cette ressource existe déjà, elle correspond à tel bloc de mon code ».
Depuis Terraform 1.5, cela s'écrit dans un fichier :

```hcl
import {
  to = google_model_armor_template.shield["ge-prompt-shield"]          # l'adresse dans NOTRE code
  id = "projects/PROJECT_ID/locations/eu/templates/ge-prompt-shield"   # la ressource existante chez Google
}
```

**Procédure.**

```bash
cp imports.tf.example imports.tf
# 1. Supprimer les blocs des ressources NON créées en console (voir le journal de bord de la phase 1).
# 2. Remplacer PROJECT_ID partout.
sed -i "s/PROJECT_ID/$PROJECT_ID/g" imports.tf
terraform plan -out=tfplan
```

**Correspondance journal de bord → bloc `import`.**

| Créé en console (phase 1) | `to =` | `id =` |
|---|---|---|
| Template questions | `google_model_armor_template.shield["ge-prompt-shield"]` | `projects/P/locations/eu/templates/ge-prompt-shield` |
| Template réponses | `google_model_armor_template.shield["ge-response-shield"]` | `projects/P/locations/eu/templates/ge-response-shield` |
| Plancher | `google_model_armor_floorsetting.project` | `projects/P/locations/global/floorSetting` |
| Modèle DLP | `google_data_loss_prevention_inspect_template.fr[0]` | `projects/P/locations/europe/inspectTemplates/ge-donnees-sensibles-fr` |
| Journaux d'audit (un par service) | `google_project_iam_audit_config.audit["discoveryengine.googleapis.com"]` | `P discoveryengine.googleapis.com` (espace entre les deux) |
| Buckets de journaux | `google_logging_project_bucket_config.security` / `.usage` | `projects/P/locations/eu/buckets/ge-security` |
| Politique d'org | `google_org_policy_policy.guardrails["run.allowedIngress"]` | `projects/P/policies/run.allowedIngress` |
| Access Approval | `google_project_access_approval_settings.this[0]` | `projects/P/accessApprovalSettings` |
| Périmètre VPC-SC | `google_access_context_manager_service_perimeter.ge[0]` | `accessPolicies/POLICY/servicePerimeters/NOM` |

> **Les noms doivent être identiques.** Le code attend `ge-prompt-shield`, `ge-security`, etc. Si la console a utilisé
> un autre nom : soit on supprime la ressource console et Terraform la recrée, soit on renomme dans le code (PR).
> Pour le périmètre VPC-SC, le nom Terraform est `gemini_enterprise_<projet>` : le plus simple est de supprimer le
> périmètre dry-run de la console et de laisser Terraform le recréer (aucun effet sur le trafic).

**Réglages faits en console sans ressource Terraform dédiée** : le réglage Model Armor de l'assistant et les
fonctionnalités de l'app sont portés par `google_discovery_engine_assistant.default` et
`google_discovery_engine_search_engine.app`. Si l'app a été créée en console, importer aussi l'app et l'assistant :

```hcl
import {
  to = google_discovery_engine_search_engine.app
  id = "projects/PROJECT_ID/locations/eu/collections/default_collection/engines/APP_ID"
}
import {
  to = google_discovery_engine_assistant.default
  id = "projects/PROJECT_ID/locations/eu/collections/default_collection/engines/APP_ID/assistants/default_assistant"
}
```

---

## 6. Lire un plan (la compétence la plus importante)

```
  # google_model_armor_template.shield["ge-prompt-shield"] will be imported
  # google_model_armor_floorsetting.project will be updated in-place
  ~ resource "google_model_armor_floorsetting" "project" {
      ~ integrated_services = [] -> ["AI_PLATFORM"]
    }
  # google_pubsub_topic.siem[0] will be created
  + resource "google_pubsub_topic" "siem" { ... }

Plan: 1 to import, 1 to add, 1 to change, 0 to destroy.
```

| Symbole | Sens | Réaction |
|---|---|---|
| `+` | création | Normal pour un nouveau palier |
| `~` | modification sur place | Lire **chaque** attribut modifié |
| `-/+` | **suppression puis recréation** | **Stop.** Comprendre pourquoi (attribut immuable changé). Une app GE ou une clé recréée = perte de données |
| `-` | suppression | **Stop** sauf si c'est voulu et écrit dans la PR |
| `will be imported` | adoption sans recréation | Normal après la phase 1 |

**Un `~` sur une ressource importée = un écart entre la console et le code.** Deux cas :
- le code a raison → on applique, la console est corrigée ;
- la console avait un meilleur réglage → on corrige le **code** (PR), puis on relance le plan.

**Ne jamais appliquer un plan qu'on ne comprend pas.**

---

## 7. Appliquer et nettoyer

```bash
terraform apply tfplan
rm imports.tf                 # les imports sont faits : le fichier ne sert plus (il est dans .gitignore)
terraform plan                # doit afficher : No changes. Your infrastructure matches the configuration.
```

## 8. Erreurs fréquentes

| Message | Cause → solution |
|---|---|
| `Error 409: already exists` | Ressource créée en console non importée → ajouter le bloc `import` |
| `Cannot import non-existent remote object` | Mauvais `id` (nom, localisation) → vérifier dans la console |
| `less strict than floor setting` | Un template du code est moins strict que le plancher → c'est le plancher qui a raison |
| `PERMISSION_DENIED` sur `org_policy` / `access_context_manager` | Rôle organisation manquant → palier C avec l'équipe Cloud centrale |
| `CMEK is not supported in global` | `ge_location = "eu"` |
| `Error acquiring the state lock` | Un autre `apply` en cours → attendre ; si orphelin : `terraform force-unlock ID` (avec l'équipe) |
