# 05. `20_data_protection.tf` : CMEK et secrets des connecteurs

> Ce fichier crée les clés de chiffrement du client (CMEK), les enregistre dans Gemini Enterprise, et autorise
> Gemini Enterprise à lire les secrets des connecteurs sans jamais en connaître la valeur dans Terraform.
> Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Tout ce que Gemini Enterprise **stocke** (index des connecteurs en ingestion, conversations, données de l'app) est
chiffré avec une clé qui **appartient au projet du client**, et non avec une clé gérée par Google. Le client peut
désactiver cette clé à tout moment : les données deviennent illisibles (« crypto-shredding »). Le fichier gère aussi
les **secrets** des connecteurs (identifiants OAuth SharePoint, GitHub…) : Terraform ne connaît que leur **nom**, jamais
leur valeur. Le « pourquoi » complet est dans le guide : [guide du socle (docs/00) §6.1](../../docs/00-socle-securite.md#61-cmek--chiffrement-avec-les-clés-de-acme)
et [guide du socle (docs/00) §6.2](../../docs/00-socle-securite.md#62-secrets-des-connecteurs--jamais-dans-le-code).

**Vocabulaire Google Cloud :**

| Terme | En clair |
|---|---|
| **KMS** (Cloud Key Management Service) | Le service Google qui garde les clés de chiffrement. La clé ne sort jamais de KMS : les services lui demandent de chiffrer/déchiffrer. |
| **CMEK** (Customer-Managed Encryption Key) | « Clé gérée par le client » : un service Google chiffre vos données avec **votre** clé KMS. |
| **Key ring** (trousseau) | Un dossier qui regroupe des clés, à un emplacement donné (`europe`, `europe-west1`…). |
| **Crypto key** | La clé elle-même (en réalité, une suite de **versions** ; la version « primaire » sert à chiffrer). |
| **IAM** | Le système de droits de Google Cloud : « tel compte a tel rôle sur telle ressource ». |
| **Service agent** | Un compte technique créé et géré par Google, qui agit **pour** un service dans votre projet (ex. le compte de Gemini Enterprise). |
| **Secret Manager** | Le coffre-fort à secrets de Google Cloud. Un secret a un nom et des **versions** (les valeurs). |

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_kms_key_ring.ge` | `resource` (avec `count`) | Trousseau multi-région (`europe`) de la clé principale. |
| `google_kms_crypto_key.ge` | `resource` (avec `count`) | Clé principale qui chiffre les données de Gemini Enterprise ; protégée contre la destruction. |
| `google_kms_key_ring.regional` | `resource` (avec `for_each`) | Un trousseau par région (`europe-west1`, `europe-west4`, `europe-north1`). |
| `google_kms_crypto_key.regional` | `resource` (avec `for_each`) | Une clé régionale par trousseau, exigée pour les connecteurs **tiers** en ingestion. |
| `data.google_storage_project_service_account.gcs` | `data` | Lit l'adresse du service agent Cloud Storage du projet. |
| `locals` (`all_keys`, `key_users`) | `locals` | Liste de toutes les clés et des deux comptes qui ont le droit de les utiliser. |
| `google_kms_crypto_key_iam_member.key_users` | `resource` (avec `for_each`) | Donne le droit « chiffrer/déchiffrer » à chaque couple (clé, compte). |
| `google_discovery_engine_cmek_config.ge` | `resource` (avec `count`) | Enregistre les clés dans Gemini Enterprise, comme clés **par défaut**. |
| `locals` (`secret_ids`) | `locals` | Liste (sans doublon) de tous les noms de secrets cités par les connecteurs. |
| `data.google_secret_manager_secret.connector` | `data` (avec `for_each`) | Vérifie que chaque secret existe et lit son identifiant (pas sa valeur). |
| `google_secret_manager_secret_iam_member.ge_reads` | `resource` (avec `for_each`) | Autorise Gemini Enterprise à lire chaque secret, un par un. |

---

## 3. Le code expliqué, bloc par bloc

Valeurs d'exemple utilisées tout au long de la fiche (celles de `terraform.tfvars.example` + défauts de
`variables.tf`) :

```hcl
project_id   = "acme-gemini-enterprise-prd"
ge_location  = "eu"                 # défaut
enable_cmek  = true                 # défaut
kms_key_ring = "gemini-enterprise"  # défaut
```

Et les valeurs calculées dans [`00_foundation.tf`](../00_foundation.tf) (voir [03-foundation.md](03-foundation.md)) :

```hcl
local.kms_location           = "europe"                                        # car ge_location = "eu"
local.regional_kms_locations = ["europe-west1", "europe-west4", "europe-north1"]
local.ge_sa                  = "serviceAccount:service-123456789012@gcp-sa-discoveryengine.iam.gserviceaccount.com"
# 123456789012 = numéro de projet fictif, utilisé dans toute la fiche
```

### 3.1 Le trousseau principal

```hcl
# COUCHE 2 - PROTECTION DES DONNÉES : CMEK (clés du client) + secrets.

# 2.1 Clé principale, multi-région "europe" pour une app "eu".
#     Rotation MANUELLE : exigence Gemini Enterprise (pas de rotation_period).
resource "google_kms_key_ring" "ge" {
  count      = var.enable_cmek ? 1 : 0
  name       = var.kms_key_ring
  location   = local.kms_location
  depends_on = [google_project_service.apis]
}
```

- `count = var.enable_cmek ? 1 : 0` : **première notion**. `count` dit combien d'exemplaires créer. L'expression
  `condition ? A : B` est un **ternaire** (« si… alors… sinon… ») : 1 exemplaire si CMEK est activé, 0 sinon (la
  ressource n'existe alors pas). Avec l'exemple, `enable_cmek = true` → 1 trousseau. On y fera référence avec `[0]` :
  `google_kms_key_ring.ge[0]`. Voir [00-bases §8](00-bases-terraform.md#8-créer-plusieurs-exemplaires--count-et-for_each)
  et [§12.1](00-bases-terraform.md#121-condition-ternaire).
- `name = var.kms_key_ring` : le nom du trousseau, `"gemini-enterprise"` par défaut.
- `location = local.kms_location` : `"europe"`. C'est une **multi-région KMS** (plusieurs régions européennes). Règle
  Google : une app Gemini Enterprise `eu` exige une clé dans la multi-région `europe`.
- `depends_on = [google_project_service.apis]` : force Terraform à activer d'abord les APIs (dont
  `cloudkms.googleapis.com`, dans [`00_foundation.tf`](../00_foundation.tf)). Sans cela, Terraform pourrait tenter de
  créer le trousseau avant que l'API KMS soit active. Voir [00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on).
- Pas de `rotation_period` (ici ni sur la clé) : Gemini Enterprise exige une rotation **manuelle** (le commentaire le
  rappelle).

Identifiant obtenu (`google_kms_key_ring.ge[0].id`) :
`projects/acme-gemini-enterprise-prd/locations/europe/keyRings/gemini-enterprise`.

### 3.2 La clé principale

```hcl
resource "google_kms_crypto_key" "ge" {
  count    = var.enable_cmek ? 1 : 0
  name     = "gemini-enterprise-data"
  key_ring = google_kms_key_ring.ge[0].id
  purpose  = "ENCRYPT_DECRYPT"
  labels   = { usage = "gemini-enterprise", owner = "security" }

  # Détruire cette clé = rendre TOUTES les données indexées illisibles (crypto-shredding).
  # Terraform refuse donc de la supprimer. Voir le guide, section "Désactiver la clé".
  lifecycle {
    prevent_destroy = true
  }
}
```

- `count` : même logique que le trousseau (les deux existent ensemble ou pas du tout).
- `name = "gemini-enterprise-data"` : nom fixe de la clé.
- `key_ring = google_kms_key_ring.ge[0].id` : **référence** à l'identifiant du trousseau créé juste avant. Grâce à
  cette référence, Terraform sait qu'il doit créer le trousseau **avant** la clé (pas besoin de `depends_on`). Voir
  [00-bases §7](00-bases-terraform.md#7-les-références--relier-les-blocs-entre-eux).
- `purpose = "ENCRYPT_DECRYPT"` : clé symétrique de chiffrement, le type attendu par CMEK.
- `labels` : étiquettes libres (map) pour retrouver la clé (inventaire, facturation, audit).
- `lifecycle { prevent_destroy = true }` : Terraform **refuse** tout `plan`/`apply` qui détruirait cette clé (y compris
  un `terraform destroy`). Détruire la clé rendrait les données illisibles **pour toujours**. Pour révoquer les
  données, on **désactive** la version de clé, à la main, selon une procédure ([guide du socle (docs/00) §14.3](../../docs/00-socle-securite.md#143-révoquer-les-données-incident-majeur-fin-de-contrat)).
  Voir [00-bases §11](00-bases-terraform.md#11-lifecycle--changer-le-comportement-de-terraform).

Identifiant obtenu (`google_kms_crypto_key.ge[0].id`) :
`projects/acme-gemini-enterprise-prd/locations/europe/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-data`.

### 3.3 Les trousseaux régionaux

```hcl
# 2.2 Clés régionales : exigées pour les connecteurs TIERS en mode ingestion.
resource "google_kms_key_ring" "regional" {
  for_each   = var.enable_cmek ? toset(local.regional_kms_locations) : toset([])
  name       = var.kms_key_ring
  location   = each.value
  depends_on = [google_project_service.apis]
}
```

- `for_each` : **crée un exemplaire par élément** d'un ensemble (set) ou d'une map. Ici :
  - `toset(...)` transforme la liste en **ensemble** (pas de doublon, pas d'ordre), le type accepté par `for_each`.
  - Le ternaire donne les 3 régions si CMEK est activé, un ensemble vide `toset([])` sinon (donc 0 trousseau). Les
    deux branches ont le même type (un set), ce que Terraform exige.
  - Avec l'exemple : `toset(["europe-west1", "europe-west4", "europe-north1"])` → **3 trousseaux**.
- `each.value` : l'élément en cours de la boucle. Pour un set de textes, `each.key` et `each.value` sont identiques
  (`"europe-west1"`, puis `"europe-west4"`, puis `"europe-north1"`).
- `name = var.kms_key_ring` : même nom `"gemini-enterprise"` que le trousseau principal. C'est possible car un nom de
  trousseau n'est unique **que dans sa région**.
- Adresses obtenues : `google_kms_key_ring.regional["europe-west1"]`, `["europe-west4"]`, `["europe-north1"]`.

Voir [00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set) et
[§12.4](00-bases-terraform.md#124-les-fonctions-utilisées) pour `toset`.

### 3.4 Les clés régionales

```hcl
resource "google_kms_crypto_key" "regional" {
  for_each = google_kms_key_ring.regional
  name     = "gemini-enterprise-connectors"
  key_ring = each.value.id
  purpose  = "ENCRYPT_DECRYPT"
  labels   = { usage = "gemini-enterprise-connectors", owner = "security" }
  lifecycle {
    prevent_destroy = true
  }
}
```

- `for_each = google_kms_key_ring.regional` : astuce utile. Une ressource créée avec `for_each` est une **map**
  `{ clé => ressource }`. On peut donc boucler **directement sur une autre ressource** : « une clé par trousseau
  régional ». Ici `each.key` = la région (`"europe-west1"`…) et `each.value` = l'objet trousseau complet.
- `key_ring = each.value.id` : l'identifiant du trousseau en cours, par exemple
  `projects/acme-gemini-enterprise-prd/locations/europe-west1/keyRings/gemini-enterprise`.
- `name = "gemini-enterprise-connectors"` : nom distinct de la clé principale, pour lire facilement à quoi elle sert.
- `prevent_destroy = true` : même protection que la clé principale.
- Résultat : 3 clés, adresses `google_kms_crypto_key.regional["europe-west1"]`, etc.

### 3.5 Le service agent Cloud Storage

```hcl
# 2.3 Seuls Gemini Enterprise et le stockage temporaire d'import peuvent utiliser les clés.
data "google_storage_project_service_account" "gcs" {}
```

- Un bloc `data` **lit** une information, il ne crée rien de durable. Voir [00-bases §6.2](00-bases-terraform.md#62-data--ce-que-terraform-lit).
- Celui-ci renvoie l'adresse du **service agent Cloud Storage** du projet, dans l'attribut `email_address`, de la forme
  `service-123456789012@gs-project-accounts.iam.gserviceaccount.com`.
- Pourquoi : lors d'un import, Gemini Enterprise passe par un **bucket temporaire** Cloud Storage. Ce bucket est
  chiffré avec la même clé : le service agent Cloud Storage doit donc pouvoir l'utiliser (règle Google, [guide du socle (docs/00) §6.1](../../docs/00-socle-securite.md#61-cmek--chiffrement-avec-les-clés-de-acme)).
- `{}` vide : aucun argument, le projet est celui du provider.

### 3.6 Les valeurs calculées : toutes les clés, tous les utilisateurs de clés

```hcl
locals {
  all_keys = var.enable_cmek ? merge(
    { main = google_kms_crypto_key.ge[0].id },
    { for loc, k in google_kms_crypto_key.regional : loc => k.id },
  ) : {}
  key_users = {
    gemini_enterprise = local.ge_sa
    storage           = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
  }
}
```

Un bloc `locals` donne un nom à un calcul pour le réutiliser (lecture : `local.all_keys`). Voir
[00-bases §6.4](00-bases-terraform.md#64-locals--les-valeurs-calculées).

**`all_keys`** : une map « nom court → identifiant de clé », pour les 4 clés.

- `{ for loc, k in google_kms_crypto_key.regional : loc => k.id }` est une **expression `for`** qui transforme une
  map en une autre map. `loc` reçoit la clé (la région), `k` la ressource ; on garde `loc => k.id`. Voir
  [00-bases §12.2](00-bases-terraform.md#122-boucles-for-transformer-une-liste-ou-une-map).
- `merge(m1, m2)` **fusionne** deux maps en une seule.
- Le ternaire renvoie `{}` (map vide) si CMEK est désactivé. Important : sans ce ternaire, `google_kms_crypto_key.ge[0]`
  provoquerait une erreur, car l'élément `[0]` n'existe pas quand `count = 0`.

Résultat avec l'exemple :

```hcl
local.all_keys = {
  "main"          = "projects/acme-gemini-enterprise-prd/locations/europe/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-data"
  "europe-west1"  = "projects/acme-gemini-enterprise-prd/locations/europe-west1/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-connectors"
  "europe-west4"  = "projects/acme-gemini-enterprise-prd/locations/europe-west4/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-connectors"
  "europe-north1" = "projects/acme-gemini-enterprise-prd/locations/europe-north1/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-connectors"
}
```

**`key_users`** : les **deux seuls comptes** autorisés à utiliser les clés.

- `gemini_enterprise = local.ge_sa` : le service agent de Gemini Enterprise, déjà au format IAM
  (`serviceAccount:...`), calculé dans [`00_foundation.tf`](../00_foundation.tf).
- `storage = "serviceAccount:${...email_address}"` : l'adresse lue au §3.5, à laquelle on ajoute le préfixe
  `serviceAccount:` exigé par IAM. `${ ... }` est une **interpolation** (insérer une valeur dans un texte).

```hcl
local.key_users = {
  "gemini_enterprise" = "serviceAccount:service-123456789012@gcp-sa-discoveryengine.iam.gserviceaccount.com"
  "storage"           = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com"
}
```

### 3.7 Les droits sur les clés : toutes les combinaisons avec `setproduct`

```hcl
resource "google_kms_crypto_key_iam_member" "key_users" {
  for_each      = { for pair in setproduct(keys(local.all_keys), keys(local.key_users)) : "${pair[0]}|${pair[1]}" => { key = local.all_keys[pair[0]], member = local.key_users[pair[1]] } }
  crypto_key_id = each.value.key
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = each.value.member
  depends_on    = [terraform_data.service_agents]
}
```

Le besoin : donner le droit à **chaque** compte sur **chaque** clé, soit 4 clés × 2 comptes = **8 droits**. La ligne
`for_each` construit ces 8 combinaisons. Décomposons-la, de l'intérieur vers l'extérieur.

1. `keys(local.all_keys)` renvoie la liste des clés de la map, **triées** :
   `["europe-north1", "europe-west1", "europe-west4", "main"]`.
2. `keys(local.key_users)` : `["gemini_enterprise", "storage"]`.
3. `setproduct(l1, l2)` renvoie **toutes les combinaisons** (produit cartésien), chaque combinaison étant une liste de
   2 éléments :
   ```hcl
   [
     ["europe-north1", "gemini_enterprise"], ["europe-north1", "storage"],
     ["europe-west1",  "gemini_enterprise"], ["europe-west1",  "storage"],
     ["europe-west4",  "gemini_enterprise"], ["europe-west4",  "storage"],
     ["main",          "gemini_enterprise"], ["main",          "storage"],
   ]
   ```
4. `{ for pair in ... : CLÉ => VALEUR }` transforme cette liste en **map**, car `for_each` a besoin d'une clé
   **stable et lisible** pour chaque élément :
   - la clé est `"${pair[0]}|${pair[1]}"`, par exemple `"main|gemini_enterprise"` (`pair[0]` = 1er élément, `pair[1]` =
     2e) ; le `|` est juste un séparateur choisi par l'auteur ;
   - la valeur est un petit objet `{ key = ..., member = ... }` qui va rechercher l'identifiant complet dans
     `local.all_keys` et le compte complet dans `local.key_users`.

Résultat (extrait) :

```hcl
{
  "europe-north1|gemini_enterprise" = {
    key    = "projects/acme-gemini-enterprise-prd/locations/europe-north1/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-connectors"
    member = "serviceAccount:service-123456789012@gcp-sa-discoveryengine.iam.gserviceaccount.com"
  }
  "europe-north1|storage" = { key = "...europe-north1...", member = "serviceAccount:service-123456789012@gs-project-accounts.iam.gserviceaccount.com" }
  "europe-west1|gemini_enterprise" = { ... }
  "europe-west1|storage"           = { ... }
  "europe-west4|gemini_enterprise" = { ... }
  "europe-west4|storage"           = { ... }
  "main|gemini_enterprise"         = { key = "...locations/europe/.../cryptoKeys/gemini-enterprise-data", member = "...gcp-sa-discoveryengine..." }
  "main|storage"                   = { ... }
}
```

Adresse d'un droit : `google_kms_crypto_key_iam_member.key_users["main|storage"]`. Si CMEK est désactivé,
`local.all_keys = {}`, donc la map est vide et aucun droit n'est créé.

Les arguments :

- `crypto_key_id = each.value.key` : la clé concernée.
- `role = "roles/cloudkms.cryptoKeyEncrypterDecrypter"` : **seulement** chiffrer et déchiffrer. Ce rôle ne permet ni de
  gérer, ni de désactiver, ni de détruire la clé (moindre privilège).
- `member = each.value.member` : le compte qui reçoit le droit.
- `depends_on = [terraform_data.service_agents]` : les service agents de Google sont créés « à la demande ». La
  ressource `terraform_data.service_agents` ([`00_foundation.tf`](../00_foundation.tf)) force leur création. Sans
  cet ordre, IAM refuserait un compte qui n'existe pas encore.

Pourquoi `google_kms_crypto_key_iam_member` (et non `..._iam_policy`) : `_member` **ajoute** un droit sans toucher aux
autres. `_policy` remplacerait **tous** les droits de la clé (dangereux si l'équipe sécurité en a ajouté).

### 3.8 L'enregistrement de la clé dans Gemini Enterprise

```hcl
# 2.4 Enregistrement de la clé dans Gemini Enterprise : AVANT toute app ou connecteur,
#     sinon ceux créés avant restent chiffrés par Google.
resource "google_discovery_engine_cmek_config" "ge" {
  count          = var.enable_cmek ? 1 : 0
  location       = var.ge_location
  cmek_config_id = "default-cmek"
  kms_key        = google_kms_crypto_key.ge[0].id
  set_default    = true

  dynamic "single_region_keys" {
    for_each = google_kms_crypto_key.regional
    content {
      kms_key = single_region_keys.value.id
    }
  }

  depends_on = [google_kms_crypto_key_iam_member.key_users]
}
```

Créer une clé KMS ne suffit pas : il faut **dire à Gemini Enterprise** de l'utiliser. C'est le rôle de ce bloc
(« Discovery Engine » est le nom technique de l'API de Gemini Enterprise).

- `location = var.ge_location` : `"eu"`, l'emplacement de l'app.
- `cmek_config_id = "default-cmek"` : nom de cette configuration.
- `kms_key = google_kms_crypto_key.ge[0].id` : la clé principale (multi-région `europe`).
- `set_default = true` : cette clé devient la clé **par défaut** pour tout ce qui sera créé ensuite dans `eu`.
- `dynamic "single_region_keys"` : **bloc dynamique**. Le sous-bloc `single_region_keys { kms_key = ... }` doit être
  répété une fois par clé régionale. `dynamic` génère ces répétitions :
  - `for_each = google_kms_crypto_key.regional` : la map des 3 clés régionales ;
  - dans `content`, l'élément en cours s'appelle **comme le bloc** : `single_region_keys.value` est l'objet clé, et
    `.id` son identifiant.

  Avec l'exemple, c'est équivalent à écrire à la main :
  ```hcl
  single_region_keys { kms_key = "projects/acme-gemini-enterprise-prd/locations/europe-north1/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-connectors" }
  single_region_keys { kms_key = "projects/.../locations/europe-west1/.../cryptoKeys/gemini-enterprise-connectors" }
  single_region_keys { kms_key = "projects/.../locations/europe-west4/.../cryptoKeys/gemini-enterprise-connectors" }
  ```
  Voir [00-bases §10](00-bases-terraform.md#10-les-blocs-imbriqués-optionnels-ou-répétés--dynamic).
- `depends_on = [google_kms_crypto_key_iam_member.key_users]` : les droits doivent exister **avant**
  l'enregistrement. Sinon Gemini Enterprise ne pourrait pas utiliser la clé au moment où on la lui confie. Cette
  dépendance est invisible dans le code (aucun attribut des droits n'est utilisé), d'où le `depends_on`.

**Point clé :** l'app ([`50_app.tf`](../50_app.tf)) et les connecteurs ([`40_connectors.tf`](../40_connectors.tf))
déclarent `depends_on = [google_discovery_engine_cmek_config.ge]`. Tout ce qui est créé **avant**
l'enregistrement reste chiffré par Google.

### 3.9 La liste des secrets cités par les connecteurs

```hcl
# 2.5 Secrets des connecteurs : JAMAIS dans le code ni dans l'état Terraform.
#     L'équipe sécurité crée les secrets (valeurs) ; Terraform ne fait que les référencer
#     et autoriser Gemini Enterprise à les lire, secret par secret.
locals {
  secret_ids = toset(flatten([for c in var.connectors : values(c.secret_params)]))
}
```

Chaque connecteur de `var.connectors` peut avoir un champ `secret_params` : une map « nom du paramètre → **nom du
secret** dans Secret Manager ». On veut la liste de **tous** les noms de secrets, sans doublon.

1. `[for c in var.connectors : ...]` : boucle sur les connecteurs (pour une map, avec une seule variable, `c` reçoit
   la **valeur** de chaque entrée).
2. `values(c.secret_params)` : les valeurs de la map, donc les noms de secrets. Pour `sharepoint` :
   `["sharepoint-client-id", "sharepoint-client-secret"]`. Pour `gdrive` (pas de `secret_params`, défaut `{}`) : `[]`.
3. On obtient une **liste de listes** :
   `[[], [], ["github-client-id", "github-client-secret"], ["sharepoint-client-id", "sharepoint-client-secret"], ["teams-client-id", "teams-client-secret"]]`.
4. `flatten(...)` l'**aplatit** en une seule liste de 6 noms.
5. `toset(...)` retire les éventuels doublons (deux connecteurs qui partagent un secret) et donne un set utilisable par
   `for_each`.

```hcl
local.secret_ids = toset([
  "github-client-id", "github-client-secret",
  "sharepoint-client-id", "sharepoint-client-secret",
  "teams-client-id", "teams-client-secret",
])
```

### 3.10 La lecture des secrets (métadonnées seulement)

```hcl
data "google_secret_manager_secret" "connector" {
  for_each  = local.secret_ids
  secret_id = each.value
}
```

- `for_each = local.secret_ids` : une lecture par secret (6 avec l'exemple).
- `secret_id = each.value` : le nom du secret, par ex. `"sharepoint-client-secret"`.
- Cette source lit le **secret** (son nom, son identifiant, sa réplication), **pas ses versions**, donc **jamais la
  valeur**. La valeur ne se retrouve ni dans le code, ni dans l'état Terraform.
- Effet secondaire utile : si un secret n'existe pas, `terraform plan` échoue tout de suite, avec un message clair.
- Attributs utilisés ensuite : `.id` (ici, dans les droits) et `.name` (dans [`40_connectors.tf`](../40_connectors.tf),
  au format `projects/<numéro>/secrets/<nom>`).

### 3.11 Le droit de lecture de Gemini Enterprise, secret par secret

```hcl
resource "google_secret_manager_secret_iam_member" "ge_reads" {
  for_each   = local.secret_ids
  secret_id  = data.google_secret_manager_secret.connector[each.value].id
  role       = "roles/secretmanager.secretAccessor"
  member     = local.ge_sa
  depends_on = [terraform_data.service_agents]
}
```

- `for_each = local.secret_ids` : un droit par secret (6 avec l'exemple).
- `secret_id = data.google_secret_manager_secret.connector[each.value].id` : l'identifiant du secret lu juste avant,
  retrouvé par sa clé (`connector["sharepoint-client-secret"]`).
- `role = "roles/secretmanager.secretAccessor"` : droit de **lire la valeur** du secret, rien d'autre.
- `member = local.ge_sa` : le service agent de Gemini Enterprise. Le droit est posé **sur chaque secret**, pas sur
  le projet : Gemini Enterprise ne peut lire **que** les secrets des connecteurs. Le choix de ce compte est
  **à vérifier** au premier déploiement ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- `depends_on = [terraform_data.service_agents]` : même raison qu'au §3.7.

---

## 4. Ce que Terraform crée concrètement

Avec `terraform.tfvars.example` (CMEK activé, app `eu`, 5 connecteurs dont 3 avec secrets) :

| Ce qui apparaît dans Google Cloud | Nombre |
|---|---|
| Trousseau KMS `gemini-enterprise` dans `europe` | 1 |
| Clé `gemini-enterprise-data` (dans `europe`) | 1 |
| Trousseaux `gemini-enterprise` dans `europe-west1`, `europe-west4`, `europe-north1` | 3 |
| Clés `gemini-enterprise-connectors` (une par région) | 3 |
| Droits « chiffrer/déchiffrer » (4 clés × 2 comptes) | 8 |
| Configuration CMEK `default-cmek` dans Gemini Enterprise (`eu`) | 1 |
| Droits « lire le secret » pour Gemini Enterprise | 6 |
| **Total ressources gérées** | **23** |

Plus 7 lectures (`data`) : le service agent Cloud Storage et les 6 secrets. **Aucun secret n'est créé** : l'équipe
sécurité les crée avant (voir [guide du socle (docs/00) §7.6](../../docs/00-socle-securite.md#76-ajouter-une-source-procédure)).

Dans la console : *Sécurité → Key Management* (trousseaux et clés), *Secret Manager → onglet Autorisations* de chaque
secret, et *Gemini Enterprise → Paramètres* pour la clé CMEK enregistrée.

Avec `enable_cmek = false` : seules les 6 autorisations de secrets sont créées.

---

## 5. Dépendances avec les autres fichiers

**Ce fichier utilise :**

| Valeur | Vient de |
|---|---|
| `var.enable_cmek`, `var.kms_key_ring`, `var.ge_location`, `var.connectors` | [`variables.tf`](../variables.tf) ([02-variables.md](02-variables.md)) et `terraform.tfvars` ([12-tfvars.md](12-tfvars.md)) |
| `local.kms_location`, `local.regional_kms_locations`, `local.ge_sa` | [`00_foundation.tf`](../00_foundation.tf) ([03-foundation.md](03-foundation.md)) |
| `google_project_service.apis`, `terraform_data.service_agents` | [`00_foundation.tf`](../00_foundation.tf) |

**Ce fichier est utilisé par :**

| Valeur | Utilisée dans |
|---|---|
| `google_kms_crypto_key.ge[0].id` | [`50_app.tf`](../50_app.tf) (`kms_key_name` de l'app, [08-app.md](08-app.md)), [`40_connectors.tf`](../40_connectors.tf) (connecteurs en ingestion, [07-connectors.md](07-connectors.md)), [`outputs.tf`](../outputs.tf) (`cmek_key`, [11-outputs.md](11-outputs.md)) |
| `google_discovery_engine_cmek_config.ge` | `depends_on` de l'app ([`50_app.tf`](../50_app.tf)) et des connecteurs ([`40_connectors.tf`](../40_connectors.tf)) |
| `data.google_secret_manager_secret.connector[...].name` | `json_params` des connecteurs ([`40_connectors.tf`](../40_connectors.tf)) |
| `google_secret_manager_secret_iam_member.ge_reads` | `depends_on` des connecteurs ([`40_connectors.tf`](../40_connectors.tf)) |

L'alerte « garde-fou modifié » de [`70_detection.tf`](../70_detection.tf) ([10-detection.md](10-detection.md))
surveille les opérations sensibles sur les clés KMS (destruction de version, changement de version primaire, droits).

---

## 6. Pour reproduire / adapter

**Besoin type : chiffrer un autre service avec une clé CMEK** (ici un bucket Cloud Storage, à adapter).

```hcl
# 1. Le trousseau : choisir le MÊME emplacement que la ressource à chiffrer.
resource "google_kms_key_ring" "mon_service" {
  name     = "mon-service"            # unique dans l'emplacement ; NE PEUT PAS être supprimé ensuite
  location = "europe-west1"
}

# 2. La clé.
resource "google_kms_crypto_key" "mon_service" {
  name     = "mon-service-data"
  key_ring = google_kms_key_ring.mon_service.id
  purpose  = "ENCRYPT_DECRYPT"
  # rotation_period = "7776000s"      # 90 jours, SI le service accepte la rotation automatique
  lifecycle {
    prevent_destroy = true            # jamais de destruction par erreur
  }
}

# 3. Le service agent du service qui chiffrera (ici Cloud Storage).
data "google_storage_project_service_account" "gcs" {}

# 4. Le droit minimal : chiffrer / déchiffrer, sur CETTE clé seulement.
resource "google_kms_crypto_key_iam_member" "mon_service" {
  crypto_key_id = google_kms_crypto_key.mon_service.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
}

# 5. La ressource chiffrée, créée APRÈS le droit.
resource "google_storage_bucket" "donnees" {
  name     = "mon-projet-donnees-chiffrees"
  location = "EUROPE-WEST1"
  encryption {
    default_kms_key_name = google_kms_crypto_key.mon_service.id
  }
  depends_on = [google_kms_crypto_key_iam_member.mon_service]
}
```

**Besoin type : donner à un service l'accès à un secret existant** (sans jamais manipuler la valeur) :

```hcl
data "google_secret_manager_secret" "s" {
  secret_id = "mon-secret"            # créé AVANT par l'équipe sécurité (gcloud secrets create ...)
}

resource "google_secret_manager_secret_iam_member" "s" {
  secret_id = data.google_secret_manager_secret.s.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:mon-compte@mon-projet.iam.gserviceaccount.com"
}
# Référence à passer au service : "${data.google_secret_manager_secret.s.name}/versions/latest"
```

**Étapes :**

1. Lire la doc CMEK **du service** à chiffrer : quel emplacement de clé (région ou multi-région) ? quel service agent ?
   rotation automatique autorisée ?
2. Créer trousseau + clé avec `prevent_destroy` :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/kms_key_ring et
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/kms_crypto_key
3. Donner `cryptoKeyEncrypterDecrypter` au service agent, sur la clé uniquement :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/kms_crypto_key_iam
4. Brancher la clé dans la ressource (argument `kms_key_name`, `encryption`… selon le service), avec un
   `depends_on` sur le droit. Pour Gemini Enterprise :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_cmek_config
5. Pour les secrets :
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/secret_manager_secret et
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/secret_manager_secret_iam
6. `terraform plan` : vérifier qu'aucune ligne `-` ou `-/+` ne touche une clé existante.

---

## 7. Pièges et bonnes pratiques

- **Enregistrer la clé AVANT l'app et les connecteurs.** Ce qui est créé avant `google_discovery_engine_cmek_config`
  reste chiffré par Google. Le `depends_on` du côté app/connecteurs le garantit. Activer CMEK **après coup** ne
  rechiffre pas l'existant : il faut le décider dès le premier `apply`.
- **CMEK impossible en `global`** : seulement `eu` ou `us` (`ge_location` est validé dans `variables.tf`).
- **`prevent_destroy` bloque aussi `terraform destroy`.** C'est voulu ([guide du socle (docs/00) §15](../../docs/00-socle-securite.md#15-compromis-assumés)).
  Pour révoquer les données, on **désactive** la version de clé (réversible 30 jours), on ne la détruit pas
  ([guide du socle (docs/00) §14.3](../../docs/00-socle-securite.md#143-révoquer-les-données-incident-majeur-fin-de-contrat)).
- **Un trousseau KMS ne peut jamais être supprimé** dans Google Cloud (une clé non plus, seules ses versions peuvent
  être détruites). Si Terraform « supprime » un trousseau, il l'oublie simplement dans l'état, et le nom reste
  **pris** pour toujours dans cet emplacement. Choisissez les noms avec soin.
- **Rotation manuelle uniquement** pour la clé de Gemini Enterprise : pas de `rotation_period`. Pour tourner :
  nouvelle version, la rendre primaire, garder l'ancienne active 30 jours. **Ne pas faire tourner les clés
  régionales** ([guide du socle (docs/00) §14.4](../../docs/00-socle-securite.md#144-rotation-de-clé)).
- **`count` et `[0]` :** toute référence à `google_kms_crypto_key.ge[0]` doit être protégée par
  `var.enable_cmek ? ... : ...`, sinon l'erreur « index 0 out of range » apparaît quand CMEK est désactivé.
- **`_iam_member`, pas `_iam_policy`** : `_member` ajoute un droit ; `_policy`/`_binding` écrasent ceux posés par
  d'autres équipes.
- **Les secrets doivent exister avant `plan`** : sinon la source `data` échoue. Ordre : l'équipe sécurité crée les
  secrets, **puis** on lance Terraform ([guide du socle (docs/00) §7.6](../../docs/00-socle-securite.md#76-ajouter-une-source-procédure)).
- **Ne jamais utiliser `google_secret_manager_secret_version` (ressource ou data) pour les secrets de connecteurs** :
  la valeur finirait en clair dans l'état Terraform. Ici on ne lit que le secret, et on passe une **référence**
  `.../versions/latest` ; une rotation ne demande aucun redéploiement ([guide du socle (docs/00) §14.5](../../docs/00-socle-securite.md#145-rotation-dun-secret-de-connecteur)).
- **Le compte qui lit les secrets** (service agent Gemini Enterprise) est une hypothèse : **à vérifier** au premier
  déploiement ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- **Clés `for_each` stables** : les clés du type `"main|storage"` ne changent pas si on ajoute une région ou un compte.
  Avec `count`, un ajout décalerait les index et Terraform voudrait recréer des droits.
