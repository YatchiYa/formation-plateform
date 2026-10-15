# 00. Les bases de Terraform (pour lire et écrire ce projet)

Ce cours explique **toutes** les notions Terraform utilisées dans les fichiers du dossier `terraform/`. Lisez-le une
fois, puis gardez-le ouvert à côté des fiches de chaque fichier (`01-…` à `12-…`).

---

## 1. Terraform en une phrase

Vous **décrivez** dans des fichiers `.tf` l'infrastructure que vous voulez (« je veux une clé de chiffrement, un
filtre Model Armor, une app Gemini Enterprise… »). Terraform **compare** cette description avec ce qui existe
vraiment, puis **crée, modifie ou supprime** ce qu'il faut pour que la réalité corresponde.

On ne dit pas *comment* faire (« clique ici, puis là ») : on dit *ce qu'on veut*. C'est le principe **déclaratif**.

---

## 2. Le cycle de travail

```bash
terraform init       # 1. télécharge les "providers" (plugins) déclarés dans versions.tf
terraform fmt        # 2. met en forme les fichiers (indentation, alignement)
terraform validate   # 3. vérifie la syntaxe et les types, SANS contacter Google
terraform plan       # 4. SIMULATION : affiche ce qui serait créé (+), modifié (~), détruit (-)
terraform apply      # 5. applique (demande "yes")
terraform output     # 6. affiche les valeurs de sortie (outputs.tf)
terraform destroy    # supprime tout ce que ce dossier a créé
```

Comment lire un `plan` :

| Symbole | Signification | Vigilance |
|---|---|---|
| `+` | sera créé | — |
| `~` | sera modifié sur place | lire ce qui change |
| `-/+` | sera **détruit puis recréé** | ⚠️ perte possible (données, ID) |
| `-` | sera détruit | ⚠️ |

---

## 3. L'état (« state »)

Terraform garde la mémoire de ce qu'il a créé dans un fichier **`terraform.tfstate`**. C'est grâce à lui qu'il sait
que `google_kms_crypto_key.ge` correspond à telle clé réelle chez Google.

- **Ne jamais le modifier à la main, ne jamais le committer** (il peut contenir des informations sensibles).
- En équipe, on le stocke dans un bucket GCS (bloc `backend "gcs"` de `versions.tf`).

---

## 4. Un dossier = un « module »

Terraform lit **tous** les fichiers `.tf` d'un dossier et les fusionne. Les noms de fichiers (`00_foundation.tf`,
`10_identity_access.tf`…) servent **uniquement aux humains** à ranger le code. Les numéros n'imposent **aucun ordre**
d'exécution : Terraform calcule l'ordre lui-même (section 9).

---

## 5. La syntaxe : des blocs

Tout est écrit en **HCL** (HashiCorp Configuration Language). La brique de base est le **bloc** :

```hcl
TYPE "ÉTIQUETTE_1" "ÉTIQUETTE_2" {
  argument = valeur
  sous_bloc {
    argument = valeur
  }
}
```

Les 6 types de blocs utilisés dans ce projet :

| Bloc | Rôle | Exemple du projet |
|---|---|---|
| `terraform { }` | Réglages de Terraform lui-même (versions, backend) | `versions.tf` |
| `provider "google" { }` | Configure le plugin qui parle à Google Cloud | `versions.tf` |
| `variable "nom" { }` | Une **entrée** (paramètre) | `variables.tf` |
| `locals { }` | Des **valeurs calculées** réutilisables | `00_foundation.tf` |
| `resource "type" "nom" { }` | Quelque chose que Terraform **crée et gère** | partout |
| `data "type" "nom" { }` | Quelque chose que Terraform **lit** seulement | `data "google_project" "this"` |
| `output "nom" { }` | Une **sortie** affichée après `apply` | `outputs.tf` |

### Les valeurs

```hcl
nom        = "texte"                 # chaîne (string)
nombre     = 30                      # nombre
actif      = true                    # booléen
liste      = ["a", "b", "c"]         # liste
dico       = { cle = "valeur" }      # map / objet
commentaire = 1  # ceci est un commentaire (aussi //  et /* … */)
```

---

## 6. Les blocs en détail

### 6.1 `resource` : ce que Terraform crée

```hcl
resource "google_kms_key_ring" "ge" {
  name     = "gemini-enterprise"
  location = "europe"
}
```

- `google_kms_key_ring` = le **type** (défini par le provider Google ; la doc de chaque type est sur
  registry.terraform.io → hashicorp/google → Resources).
- `ge` = le **nom local**, choisi par vous, pour y faire référence ailleurs.
- **Adresse** de la ressource : `google_kms_key_ring.ge`.

### 6.2 `data` : ce que Terraform lit

```hcl
data "google_project" "this" {}          # lit les infos du projet courant
# utilisation : data.google_project.this.number
```

Une source de données ne crée **rien**. Elle va chercher une information qui existe déjà.

### 6.3 `variable` : les entrées

```hcl
variable "session_ttl_days" {
  description = "Durée de conservation des conversations."
  type        = number
  default     = 30                 # sans default, la variable est OBLIGATOIRE
  validation {                     # (optionnel) refuse les valeurs invalides
    condition     = var.session_ttl_days > 0
    error_message = "Doit être positif."
  }
}
# utilisation : var.session_ttl_days
```

Les valeurs se donnent dans **`terraform.tfvars`** (`session_ttl_days = 15`) ou en ligne de commande
(`terraform plan -var session_ttl_days=15`).

**Types complexes** (utilisés pour les connecteurs) :

```hcl
type = map(object({
  data_source = string                          # champ obligatoire
  modes       = optional(list(string), ["FEDERATED"])   # champ optionnel AVEC valeur par défaut
}))
```

### 6.4 `locals` : les valeurs calculées

```hcl
locals {
  kms_location = var.ge_location == "eu" ? "europe" : "us"
}
# utilisation : local.kms_location   (attention : "local." au singulier)
```

On s'en sert pour **ne pas répéter** un calcul et pour **donner un nom parlant** à une expression.

### 6.5 `output` : les sorties

```hcl
output "cmek_key" {
  value = google_kms_crypto_key.ge[0].id
}
# lecture : terraform output cmek_key
```

---

## 7. Les références : relier les blocs entre eux

| Écriture | Signifie |
|---|---|
| `var.project_id` | la variable `project_id` |
| `local.ge_sa` | la valeur locale `ge_sa` |
| `google_kms_crypto_key.ge.id` | l'attribut `id` de la ressource |
| `google_kms_crypto_key.ge[0].id` | idem, quand la ressource utilise `count` (élément n° 0) |
| `google_model_armor_template.shield["ge-prompt-shield"].id` | idem, quand la ressource utilise `for_each` (élément de clé `"ge-prompt-shield"`) |
| `data.google_project.this.number` | l'attribut `number` d'une source de données |
| `"projects/${var.project_id}"` | **interpolation** : insérer une valeur dans un texte |

Les attributs disponibles (`id`, `name`, `number`…) sont listés dans la doc du type, section *Attributes Reference*.

---

## 8. Créer plusieurs exemplaires : `count` et `for_each`

### 8.1 `count` : 0 ou N exemplaires (souvent pour optionnel)

```hcl
resource "google_kms_key_ring" "ge" {
  count = var.enable_cmek ? 1 : 0     # 1 si CMEK activé, 0 sinon (= n'existe pas)
  ...
}
# référence : google_kms_key_ring.ge[0]
```

### 8.2 `for_each` : un exemplaire par élément d'une map ou d'un set

```hcl
resource "google_model_armor_template" "shield" {
  for_each    = toset(["ge-prompt-shield", "ge-response-shield"])
  template_id = each.value          # each.key / each.value = l'élément en cours
}
# référence : google_model_armor_template.shield["ge-prompt-shield"]
```

Avec une **map**, `each.key` est la clé et `each.value` la valeur :

```hcl
for_each = var.connectors                  # { gdrive = {...}, sharepoint = {...} }
collection_id = each.key                   # "gdrive", puis "sharepoint"
data_source   = each.value.data_source     # "google_drive", puis "sharepoint"
```

**Pourquoi préférer `for_each` à `count` pour des listes :** avec `count`, retirer le 1er élément décale tous les
autres (Terraform croit qu'ils ont changé). Avec `for_each`, chaque élément a une **clé stable**.

---

## 9. L'ordre de création : automatique, ou forcé avec `depends_on`

Terraform construit un **graphe de dépendances** :
- si la ressource B **utilise** un attribut de A (`kms_key = google_kms_crypto_key.ge[0].id`), Terraform crée A avant B ;
- si la dépendance n'apparaît pas dans le code mais existe dans la réalité (ex. « la clé doit être **enregistrée**
  avant de créer l'app »), on la déclare :

```hcl
depends_on = [google_discovery_engine_cmek_config.ge]
```

---

## 10. Les blocs imbriqués optionnels ou répétés : `dynamic`

Certains sous-blocs doivent être répétés (un par élément d'une liste) ou n'exister que sous condition :

```hcl
rai_settings {
  dynamic "rai_filters" {                       # génère un bloc rai_filters…
    for_each = ["HATE_SPEECH", "HARASSMENT"]    # …par élément
    content {
      filter_type = rai_filters.value           # l'élément en cours s'appelle comme le bloc
    }
  }
}
```

Équivaut à écrire à la main :

```hcl
rai_settings {
  rai_filters { filter_type = "HATE_SPEECH" }
  rai_filters { filter_type = "HARASSMENT" }
}
```

**Bloc conditionnel :** `for_each = var.sdp_mode == "advanced" ? [1] : []` signifie « une fois si la condition est
vraie, zéro fois sinon ».

---

## 11. `lifecycle` : changer le comportement de Terraform

```hcl
lifecycle {
  prevent_destroy = true     # Terraform REFUSE toute action qui détruirait cette ressource
}
```

Utilisé sur les clés KMS : les détruire rendrait les données illisibles pour toujours.

---

## 12. Les expressions utilisées dans le projet

### 12.1 Condition (ternaire)

```hcl
condition ? valeur_si_vrai : valeur_si_faux
var.enable_cmek ? google_kms_crypto_key.ge[0].id : null     # null = "ne pas renseigner l'argument"
```

### 12.2 Boucles `for` (transformer une liste ou une map)

```hcl
[for g in var.user_groups : "user|${g}"]                    # liste → liste
{ for g in var.user_groups : "user|${g}" => { role = "...", member = g } }   # liste → map
[for e in c.entities : basename(e.data_store) if e.data_store != ""]        # avec filtre "if"
```

### 12.3 Texte sur plusieurs lignes (heredoc)

```hcl
command = <<-EOT
  ligne 1
  ligne 2
EOT
```

### 12.4 Les fonctions utilisées

| Fonction | Ce qu'elle fait | Exemple |
|---|---|---|
| `toset(liste)` | liste → ensemble (sans doublons, utilisable par `for_each`) | `toset(["a","b"])` |
| `concat(l1, l2)` | colle des listes | `concat(["a"], ["b"])` → `["a","b"]` |
| `merge(m1, m2)` | fusionne des maps | `merge({a=1}, {b=2})` → `{a=1, b=2}` |
| `flatten(liste_de_listes)` | aplatit | `[["a"],["b"]]` → `["a","b"]` |
| `keys(map)` / `values(map)` | clés / valeurs d'une map | |
| `contains(liste, x)` | `x` est-il dans la liste ? | `contains(["A","B"], "A")` → `true` |
| `jsonencode(valeur)` | transforme en texte JSON | `jsonencode({a=1})` → `"{\"a\":1}"` |
| `join(sep, liste)` | colle avec un séparateur | `join(",", ["a","b"])` → `"a,b"` |
| `replace(texte, a, b)` | remplace | `replace("a-b", "-", "_")` → `"a_b"` |
| `basename(chemin)` | dernière partie d'un chemin | `basename("x/y/z")` → `"z"` |
| `setproduct(l1, l2)` | toutes les combinaisons | `setproduct(["k1","k2"],["u1"])` → `[["k1","u1"],["k2","u1"]]` |
| `try(expr, défaut)` | `expr`, ou `défaut` si erreur | `try(e.data_store != null, false)` |

Pour tester une expression sans rien déployer : `terraform console`, puis tapez l'expression.

---

## 13. Les « providers » et la doc

Un **provider** est un plugin qui sait parler à une API. Ici : `hashicorp/google` (Google Cloud).

**Pour savoir quels arguments une ressource accepte**, ouvrez sa page de doc :
`https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/<type sans "google_">`
Exemple : `google_kms_crypto_key` → `.../docs/resources/kms_crypto_key`. Chaque page a :
- *Example Usage* : des exemples à copier ;
- *Argument Reference* : ce que vous pouvez écrire (Required / Optional) ;
- *Attributes Reference* : ce que vous pouvez lire après création (`id`, `name`…) ;
- *Import* : comment reprendre une ressource créée à la main.

---

## 14. Quand Terraform ne sait pas faire : `terraform_data` + `local-exec`

Certains réglages Google n'existent pas encore dans le provider (ex. durée de conservation des conversations).
On exécute alors une **commande** depuis Terraform :

```hcl
resource "terraform_data" "engine_settings" {
  triggers_replace = [jsonencode(local.engine_settings)]   # relancer quand ces valeurs changent
  provisioner "local-exec" {
    command = "curl -X PATCH ..."                          # exécuté sur VOTRE machine
  }
}
```

- `terraform_data` est une ressource « vide » qui sert de support.
- `triggers_replace` : quand cette valeur change, la ressource est recréée, donc la commande est relancée.
- `local-exec` exécute la commande sur la machine qui lance `terraform apply` (il faut donc `gcloud` et `curl`).
- **À utiliser en dernier recours** : Terraform ne sait pas « lire » l'effet de la commande. Si quelqu'un modifie le
  réglage à la main, Terraform ne le verra pas.

---

## 15. Méthode pour écrire votre propre fichier

1. **Identifier la ressource** dans la doc du provider (rechercher le service : « kms », « model armor »…).
2. **Copier l'*Example Usage***, puis ne garder que les arguments utiles.
3. **Remplacer les valeurs en dur** par des variables (`var.…`) ou des références (`google_….id`).
4. **Ajouter les droits** (`google_*_iam_member`) dont le service a besoin.
5. **Déclarer les dépendances invisibles** (`depends_on`).
6. `terraform fmt` → `terraform validate` → `terraform plan` → lire → `apply`.

---

## 16. Fiches de ce dossier

| Fiche | Fichier expliqué |
|---|---|
| [01-versions.md](01-versions.md) | `versions.tf` : versions et configuration du provider |
| [02-variables.md](02-variables.md) | `variables.tf` : toutes les entrées |
| [03-foundation.md](03-foundation.md) | `00_foundation.tf` : APIs, service agents, valeurs communes |
| [04-identity-access.md](04-identity-access.md) | `10_identity_access.tf` : identité et rôles |
| [05-data-protection.md](05-data-protection.md) | `20_data_protection.tf` : CMEK et secrets |
| [06-ai-guardrails.md](06-ai-guardrails.md) | `30_ai_guardrails.tf` : Model Armor et DLP |
| [07-connectors.md](07-connectors.md) | `40_connectors.tf` : connecteurs génériques |
| [08-app.md](08-app.md) | `50_app.tf` : app, assistant, réglages API |
| [09-advanced.md](09-advanced.md) | `60_advanced.tf` : Agent Gateway, VPC-SC |
| [10-detection.md](10-detection.md) | `70_detection.tf` : audit et alertes |
| [11-outputs.md](11-outputs.md) | `outputs.tf` : les sorties |
| [12-tfvars.md](12-tfvars.md) | `terraform.tfvars.example` : la configuration |
| [13-logging.md](13-logging.md) | `80_logging.tf` : journaux d'usage et de sécurité, buckets, alerte |
