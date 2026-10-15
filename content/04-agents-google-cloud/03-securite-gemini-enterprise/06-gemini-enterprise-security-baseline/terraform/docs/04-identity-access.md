# 04. `10_identity_access.tf` : identité et rôles (couche 1)

> Ce fichier choisit l'annuaire qui authentifie les collaborateurs et donne les rôles IAM à des **groupes**, en
> séparant administrateurs et équipe sécurité. Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Il répond à trois questions : **qui peut entrer** (connexion avec le compte d'entreprise, sans mot de passe dédié),
**qui peut faire quoi** (utiliser, administrer, consulter), et **qui ne peut pas désactiver la sécurité**. Les droits
sont donnés à des groupes de l'annuaire : une arrivée ou un départ se gère dans l'annuaire, sans Terraform. Les
administrateurs de l'app n'ont **aucun** droit sur Model Armor, les clés KMS ou les journaux privés : seule l'équipe
sécurité les a (principe des « quatre yeux »). Voir [README §5](../../README.md#5-couche-1--identité-et-accès).

Rappel : **IAM** (*Identity and Access Management*) est le système de droits de Google Cloud. Un **rôle** (ex.
`roles/cloudkms.admin`) est un paquet de permissions. On **attribue** un rôle à un **membre** (utilisateur, groupe,
compte de service) sur une ressource (ici, le projet).

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_discovery_engine_acl_config.identity` | resource | Déclare le fournisseur d'identité de Gemini Enterprise pour la localisation `eu`. |
| `local.role_bindings` | locals | Construit la liste « clé → (rôle, groupe) » de toutes les attributions de rôles. |
| `google_project_iam_member.access` | resource | Crée une attribution de rôle IAM par élément de `local.role_bindings`. |

---

## 3. Le code expliqué, bloc par bloc

### 3.1 En-tête

```hcl
# COUCHE 1 - IDENTITÉ ET ACCÈS
# Qui peut entrer (SSO), qui peut faire quoi (rôles), et qui ne peut PAS
# désactiver la sécurité (séparation des rôles).
```

Commentaires uniquement. SSO (*Single Sign-On*) : on se connecte une fois avec le compte d'entreprise.

### 3.2 `google_discovery_engine_acl_config.identity` : le fournisseur d'identité

```hcl
# 1.1 Fournisseur d'identité de l'app (un seul par localisation).
resource "google_discovery_engine_acl_config" "identity" {
  location = var.ge_location
  idp_config {
    idp_type = var.identity_provider
```

- `google_discovery_engine_acl_config` : réglage d'identité de Gemini Enterprise (Discovery Engine = nom technique de
  son API). IdP = *Identity Provider*, l'annuaire qui authentifie les personnes. ACL = *Access Control List*.
- Le commentaire « un seul par localisation » : il n'existe qu'**un** réglage d'identité pour toutes les apps d'une
  même localisation du projet.
- `location = var.ge_location` : `"eu"` par défaut, la même localisation que l'app.
- Pas d'argument `project` : la ressource hérite du projet du provider (voir [01-versions.md](01-versions.md)).
- `idp_config { … }` : sous-bloc qui décrit l'annuaire.
- `idp_type = var.identity_provider` : `"GSUITE"` par défaut (Google Workspace / Cloud Identity), ou `"THIRD_PARTY"`
  (annuaire externe comme Microsoft Entra ID).
  - Pourquoi l'annuaire d'entreprise : double authentification, durée de session et **suspension au départ** sont
    gérées à un seul endroit. Un compte suspendu perd l'accès immédiatement.

```hcl
    dynamic "external_idp_config" {
      for_each = var.identity_provider == "THIRD_PARTY" ? [1] : []
      content {
        workforce_pool_name = var.workforce_pool
      }
    }
  }
```

- `dynamic "external_idp_config"` : génère le sous-bloc `external_idp_config` **zéro ou plusieurs fois** (voir
  [00-bases §10](00-bases-terraform.md#10-les-blocs-imbriqués-optionnels-ou-répétés--dynamic)). Ici, on s'en sert
  pour un bloc **conditionnel**.
- `for_each = var.identity_provider == "THIRD_PARTY" ? [1] : []` :
  - avec `identity_provider = "GSUITE"` (exemple) : la condition est fausse → `[]` → **aucun** bloc généré ;
  - avec `"THIRD_PARTY"` : `[1]` → **un** bloc. La valeur `1` n'a aucun sens en soi : seule compte la **longueur**
    de la liste.
- `content { … }` : le contenu de chaque bloc généré.
- `workforce_pool_name = var.workforce_pool` : le pool *Workforce Identity Federation* (mécanisme Google qui fait
  confiance à un annuaire externe), au format `locations/global/workforcePools/POOL_ID`.
- Avec `THIRD_PARTY`, le résultat équivaut à écrire à la main :
  ```hcl
  idp_config {
    idp_type = "THIRD_PARTY"
    external_idp_config {
      workforce_pool_name = "locations/global/workforcePools/POOL_ID"
    }
  }
  ```
- Pourquoi un bloc conditionnel : en `GSUITE`, ce sous-bloc n'a pas lieu d'être. Le même code gère les deux cas.

```hcl
  depends_on = [google_project_service.apis]
}
```

- `depends_on` : attendre que les API (dont `discoveryengine.googleapis.com`) soient activées par
  [`00_foundation.tf`](../00_foundation.tf). Rien dans le bloc ne référence ces API, donc Terraform ne le devinerait
  pas seul. Voir [00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on).

> ⚠️ **Choix structurant** (README §5.1) : l'identité Google est obligatoire pour les connecteurs Google Workspace ;
> l'ingestion SharePoint/OneDrive/Outlook exige Entra ID ; **changer d'identité plus tard efface l'historique des
> conversations** et oblige à recréer les data stores.

### 3.3 `local.role_bindings` : la table de toutes les attributions

```hcl
# 1.2 Rôles, attribués à des GROUPES (arrivées/départs gérés dans l'annuaire).
locals {
  role_bindings = merge(
    { for g in var.user_groups : "user|${g}" => { role = "roles/discoveryengine.agentspaceUser", member = g } },
    { for g in var.admin_groups : "admin|${g}" => { role = "roles/discoveryengine.agentspaceAdmin", member = g } },
    { for g in var.viewer_groups : "viewer|${g}" => { role = "roles/discoveryengine.agentspaceViewer", member = g } },
```

Un deuxième bloc `locals` dans le projet (le premier est dans `00_foundation.tf`) : Terraform les fusionne, on peut
en écrire autant qu'on veut. Voir [00-bases §6.4](00-bases-terraform.md#64-locals--les-valeurs-calculées).

**L'expression `for` qui produit une map** (voir
[00-bases §12.2](00-bases-terraform.md#122-boucles-for-transformer-une-liste-ou-une-map)) :

```
{ for g in LISTE : CLÉ => VALEUR }
```

- `for g in var.user_groups` : parcourt la liste ; `g` vaut chaque groupe à tour de rôle.
- `"user|${g}"` : la **clé** de la map, un texte fait du préfixe `user|` et du groupe.
- `=> { role = "...", member = g }` : la **valeur**, un objet avec le rôle et le membre.

Avec `user_groups = ["group:gemini-utilisateurs@acme.example"]`, la première ligne produit :

```hcl
{
  "user|group:gemini-utilisateurs@acme.example" = {
    role   = "roles/discoveryengine.agentspaceUser"
    member = "group:gemini-utilisateurs@acme.example"
  }
}
```

Les trois rôles Gemini Enterprise (l'ancien nom du produit, « Agentspace », est resté dans les noms de rôles) :

| Variable | Rôle | Peut |
|---|---|---|
| `user_groups` | `roles/discoveryengine.agentspaceUser` | utiliser l'app |
| `admin_groups` | `roles/discoveryengine.agentspaceAdmin` | gérer l'app, les connecteurs, les agents |
| `viewer_groups` | `roles/discoveryengine.agentspaceViewer` | consulter configuration et statistiques |

Si `viewer_groups = []` (défaut), la troisième ligne produit `{}` : aucune attribution.

```hcl
    # 1.3 Séparation des rôles : la sécurité possède les garde-fous, les clés et les journaux privés.
    { for g in var.security_groups : "armor|${g}" => { role = "roles/modelarmor.admin", member = g } },
    { for g in var.security_groups : "kms|${g}" => { role = "roles/cloudkms.admin", member = g } },
    { for g in var.security_groups : "logs|${g}" => { role = "roles/logging.privateLogViewer", member = g } },
  )
}
```

- Le même groupe sécurité reçoit **trois** rôles :
  - `roles/modelarmor.admin` : gérer les filtres Model Armor ;
  - `roles/cloudkms.admin` : gérer les clés de chiffrement ;
  - `roles/logging.privateLogViewer` : lire les journaux privés (ex. journaux d'accès aux données).
- Pourquoi : ceux qui exploitent l'outil (`admin_groups`) ne doivent pas pouvoir **désactiver leur propre sécurité**.
  Aucun rôle `modelarmor.*` ni `cloudkms.*` n'est donné aux admins. Risque R6 du README (affaiblissement de la
  sécurité).

**`merge(…)`** : fusionne plusieurs maps en une seule (voir
[00-bases §12.4](00-bases-terraform.md#124-les-fonctions-utilisées)). En cas de clé identique, la dernière map
gagne. **C'est pour cela que chaque clé a un préfixe différent** (`user|`, `admin|`, `armor|`, `kms|`, `logs|`) : le
même groupe peut apparaître dans plusieurs lignes sans qu'une attribution en écrase une autre.

**Résultat complet avec `terraform.tfvars.example`** :

```hcl
{
  "user|group:gemini-utilisateurs@acme.example" = { role = "roles/discoveryengine.agentspaceUser",   member = "group:gemini-utilisateurs@acme.example" }
  "admin|group:gemini-admins@acme.example"      = { role = "roles/discoveryengine.agentspaceAdmin",  member = "group:gemini-admins@acme.example" }
  "viewer|group:gemini-pilotage@acme.example"   = { role = "roles/discoveryengine.agentspaceViewer", member = "group:gemini-pilotage@acme.example" }
  "armor|group:securite-ia@acme.example"        = { role = "roles/modelarmor.admin",                 member = "group:securite-ia@acme.example" }
  "kms|group:securite-ia@acme.example"          = { role = "roles/cloudkms.admin",                   member = "group:securite-ia@acme.example" }
  "logs|group:securite-ia@acme.example"         = { role = "roles/logging.privateLogViewer",         member = "group:securite-ia@acme.example" }
}
```

Astuce : tapez `local.role_bindings` dans `terraform console` pour voir ce résultat.

### 3.4 `google_project_iam_member.access` : une attribution par élément

```hcl
resource "google_project_iam_member" "access" {
  for_each = local.role_bindings
  project  = var.project_id
  role     = each.value.role
  member   = each.value.member
}
```

- `google_project_iam_member` : ajoute **un** membre à **un** rôle sur un projet. Elle est **non exclusive** : elle
  ne retire pas les autres membres qui ont déjà ce rôle (contrairement à `google_project_iam_binding` ou
  `google_project_iam_policy`, qui remplacent tout).
- `for_each = local.role_bindings` : une ressource par entrée de la map (6 avec l'exemple). Voir
  [00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set).
  - `each.key` = la clé, ex. `"kms|group:securite-ia@acme.example"` ;
  - `each.value` = l'objet, donc `each.value.role` = `"roles/cloudkms.admin"` et `each.value.member` =
    `"group:securite-ia@acme.example"`.
- Adresse d'un exemplaire : `google_project_iam_member.access["kms|group:securite-ia@acme.example"]`.
- `project = var.project_id` : les rôles sont donnés **au niveau du projet**.
- Pourquoi une map avec des clés lisibles plutôt qu'une liste avec `count` : retirer un groupe ne décale pas les
  autres ; Terraform supprime **seulement** l'attribution concernée.

---

## 4. Ce que Terraform crée concrètement

Avec `terraform.tfvars.example` :

| Dans Google Cloud | Nombre |
|---|---|
| Réglage d'identité Gemini Enterprise en `eu`, type `GSUITE` (console : *Gemini Enterprise → Paramètres → identité*, **à vérifier** selon la console) | 1 |
| Attributions de rôles dans *IAM et administration → IAM* : 1 utilisateur, 1 admin, 1 lecteur, 3 pour la sécurité | 6 |

Total : **7 ressources**. Formule générale : `1 + nb(user) + nb(admin) + nb(viewer) + 3 × nb(security)`.

Rien n'est créé dans l'annuaire : les **groupes doivent exister** avant (Google Workspace / Cloud Identity).

---

## 5. Dépendances avec les autres fichiers

**Ce que ce fichier utilise :**

| Valeur | Vient de |
|---|---|
| `var.ge_location`, `var.identity_provider`, `var.workforce_pool`, `var.user_groups`, `var.admin_groups`, `var.viewer_groups`, `var.security_groups`, `var.project_id` | [`variables.tf`](../variables.tf), section 2, voir [02-variables.md](02-variables.md) |
| `google_project_service.apis` | [`00_foundation.tf`](../00_foundation.tf), voir [03-foundation.md](03-foundation.md) |
| Projet par défaut de `acl_config` | provider de [`versions.tf`](../versions.tf), voir [01-versions.md](01-versions.md) |

**Qui utilise ce fichier :**

| Valeur de ce fichier | Utilisée dans |
|---|---|
| `google_discovery_engine_acl_config.identity` (via `depends_on`) | [`40_connectors.tf`](../40_connectors.tf) : les connecteurs ne sont créés qu'après le choix de l'identité. Voir [07-connectors.md](07-connectors.md). |
| `local.role_bindings`, `google_project_iam_member.access` | uniquement dans ce fichier. |

Les droits des **comptes techniques** (service agents) ne sont pas ici : ils sont dans
[`20_data_protection.tf`](../20_data_protection.tf) et [`30_ai_guardrails.tf`](../30_ai_guardrails.tf), au plus près
de la ressource concernée.

---

## 6. Pour reproduire / adapter

Modèle générique « rôles par groupe, avec séparation des rôles » :

```hcl
variable "app_users"     { type = list(string) }  # ex. ["group:app-users@exemple.com"]
variable "app_admins"    { type = list(string) }
variable "security_team" { type = list(string) }

locals {
  # Une entrée = une attribution. Clé = "préfixe|membre" : unique et stable.
  role_bindings = merge(
    { for g in var.app_users  : "user|${g}"  => { role = "roles/ROLE_UTILISATEUR", member = g } },
    { for g in var.app_admins : "admin|${g}" => { role = "roles/ROLE_ADMIN",       member = g } },
    # Séparation des rôles : la sécurité, et elle seule, gère les garde-fous.
    { for g in var.security_team : "kms|${g}" => { role = "roles/cloudkms.admin", member = g } },
  )
}

resource "google_project_iam_member" "access" {
  for_each = local.role_bindings
  project  = var.project_id
  role     = each.value.role
  member   = each.value.member # "group:…", "user:…" ou "serviceAccount:…"
}

# Sous-bloc conditionnel : présent seulement si la condition est vraie.
#   dynamic "sous_bloc" {
#     for_each = var.option == "VALEUR" ? [1] : []
#     content { argument = var.autre }
#   }
```

Étapes :

1. Listez les **profils** (utilisateur, admin, lecteur, sécurité) et le **rôle minimal** de chacun. Rôles prédéfinis :
   `https://cloud.google.com/iam/docs/roles-permissions` (ou `gcloud iam roles list --filter="name:discoveryengine"`).
2. Vérifiez qu'**aucun** profil d'exploitation n'a un rôle qui permet de désactiver la sécurité (`*.admin` sur KMS,
   Model Armor, journaux).
3. Créez les **groupes** dans l'annuaire et déclarez-les en variables, avec le préfixe `group:`.
4. Construisez `role_bindings` avec un préfixe **différent par ligne** de `merge`.
5. `terraform plan` : comptez les `+ google_project_iam_member.access["…"]` et relisez chaque paire rôle/groupe.

Documentation :
- `https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_acl_config`
- `google_project_iam_member` est documentée sur la page commune des ressources IAM projet :
  `https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam`

---

## 7. Pièges et bonnes pratiques

- **Préfixe obligatoire** dans `member` : `group:`, `user:` ou `serviceAccount:`. Une adresse seule est refusée.
- **N'utilisez pas `google_project_iam_policy` ni `google_project_iam_binding`** pour ce besoin : elles **remplacent**
  les membres existants et peuvent retirer des droits posés par d'autres (y compris les vôtres).
- **Doublon dans une liste** (le même groupe deux fois dans `user_groups`) : l'expression `for` produit deux fois la
  même clé, et Terraform s'arrête sur une erreur de clé dupliquée. Dédupliquez la liste.
- **Préfixes de clé uniques par ligne de `merge`** : sans eux, le même groupe dans `admin_groups` et `security_groups`
  verrait une attribution **écrasée en silence**.
- **Pas de droits nominatifs** (`user:prenom.nom@…`) : ils ne sont jamais nettoyés. Toujours des groupes.
- **Petit groupe admin et groupe sécurité distinct** : ne mettez pas le même groupe dans `admin_groups` et
  `security_groups`, sinon la séparation des rôles disparaît.
- **`identity_provider` est validé** (`GSUITE` ou `THIRD_PARTY`, voir [02-variables.md](02-variables.md)). Si vous choisissez
  `THIRD_PARTY`, renseignez `workforce_pool`, sinon le bloc est envoyé avec un nom vide (erreur côté Google
  probable, **à vérifier**).
- **Changer d'annuaire après le lancement** efface l'historique des conversations : décidez-le avant la production.
- **Le rôle seul ne suffit pas** pour utiliser l'app : il faut aussi une **licence** Gemini Enterprise attribuée
  (README §12.3).
- **Pour aller plus loin** (README §5.2) : accès **par app** avec `google_discovery_engine_search_engine_iam_member`
  si plusieurs apps cohabitent dans le projet.
