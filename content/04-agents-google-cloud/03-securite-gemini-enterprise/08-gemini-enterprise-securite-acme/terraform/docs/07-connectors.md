# 07. `40_connectors.tf` : connecteurs génériques

> Ce fichier transforme chaque entrée de la variable `connectors` (Google Drive, SharePoint, GitHub, Jira…) en une
> source de données de Gemini Enterprise, avec secrets référencés, CMEK si besoin, et IP fixes.
> Notions de base : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Un **connecteur** relie Gemini Enterprise à une source de données de l'entreprise (Drive, SharePoint, Teams, GitHub,
Jira…). Ce fichier contient **un seul modèle générique** : pour ajouter une source, on n'écrit pas de nouveau code, on
ajoute une entrée dans `terraform.tfvars`. Par défaut, les sources sont en mode **fédéré** : la question est envoyée
en direct à la source, avec le jeton de l'utilisateur, donc **aucune copie** chez Google et les **droits de la
source** s'appliquent. Le mode **ingestion** (copie indexée) se choisit au cas par cas ; ses données sont alors
chiffrées avec la clé CMEK du client. Le « pourquoi » complet : [guide du socle (docs/00) §7](../../docs/00-socle-securite.md#7-couche-3--connecteurs).

**Vocabulaire Google Cloud :**

| Terme | En clair |
|---|---|
| **Connecteur** (data connector) | La configuration qui relie Gemini Enterprise à une source. |
| **Collection** | Le « dossier » qui regroupe un connecteur et ses data stores. Son identifiant est ici la clé de l'entrée (`sharepoint`). |
| **Data store** | Un magasin de données que l'app interroge. Un connecteur en crée un par **entité** (type d'objet : fichier, ticket…). |
| **Fédéré / ingestion** | Fédéré : interroger la source en direct. Ingestion : copier et indexer chez Google. Voir [guide du socle (docs/00) §7.2](../../docs/00-socle-securite.md#72-fédéré-ou-ingestion--la-décision-de-sécurité-la-plus-importante). |
| **Secret Manager** | Le coffre-fort à secrets de Google Cloud. Les identifiants OAuth des sources y sont rangés. |
| **CMEK** | Chiffrement avec la clé du client (voir [05-data-protection.md](05-data-protection.md)). |
| **IP statiques** | Adresses IP fixes depuis lesquelles Gemini Enterprise appelle la source ; on les autorise côté SaaS. |

---

## 2. Vue d'ensemble

| Bloc | Type de bloc | Rôle en une phrase |
|---|---|---|
| `google_discovery_engine_data_connector.src` | `resource` (avec `for_each`) | Un connecteur par entrée de `var.connectors`. |
| `locals` (`connector_data_store_ids`) | `locals` | Liste à plat des data stores créés par les connecteurs, pour les rattacher à l'app. |

---

## 3. Le code expliqué, bloc par bloc

### 3.0 Les données d'entrée

La variable `connectors` est déclarée dans [`variables.tf`](../variables.tf) avec un type précis :

```hcl
type = map(object({
  data_source      = string # google_drive, sharepoint, github, jira, bigquery...
  display_name     = string
  modes            = optional(list(string), ["FEDERATED"]) # FEDERATED = pas de copie, droits de la source
  params           = optional(map(string), {})             # paramètres non secrets
  secret_params    = optional(map(string), {})             # clé du paramètre => ID du secret Secret Manager
  entities         = optional(list(object({ name = string, params = optional(string) })), [])
  refresh_interval = optional(string, "86400s")
  static_ip        = optional(bool, false) # IP sortantes fixes à autoriser côté SaaS (IMMUABLE)
}))
```

`optional(type, défaut)` : si le champ manque dans `terraform.tfvars`, Terraform met la valeur par défaut. Voir
[00-bases §6.3](00-bases-terraform.md#63-variable--les-entrées). Avec `terraform.tfvars.example`, Terraform voit donc,
pour `sharepoint` :

```hcl
sharepoint = {
  data_source      = "sharepoint"
  display_name     = "SharePoint"
  modes            = ["FEDERATED"]                    # défaut
  params           = { instance_uri = "https://acme.sharepoint.com", tenant_id = "00000000-0000-0000-0000-000000000000" }
  secret_params    = { client_id = "sharepoint-client-id", client_secret = "sharepoint-client-secret" }
  entities         = [{ name = "file", params = null }]
  refresh_interval = "86400s"                         # défaut (24 h)
  static_ip        = true
}
```

Et pour `gdrive` : seulement `data_source = "google_drive"` et `display_name = "Google Drive"`, tout le reste à sa
valeur par défaut (`params = {}`, `secret_params = {}`, `entities = []`, `static_ip = false`…).

### 3.1 Le connecteur générique : identité et mode

```hcl
# CONNECTEURS - un modèle générique : chaque entrée de var.connectors devient une source.
# Par défaut en FEDERATED : la question est envoyée en direct à la source avec le
# jeton de l'utilisateur => aucune copie chez Google, les droits de la source s'appliquent.

resource "google_discovery_engine_data_connector" "src" {
  for_each = var.connectors

  location                = var.ge_location
  collection_id           = each.key
  collection_display_name = each.value.display_name
  data_source             = each.value.data_source
  connector_modes         = each.value.modes
  refresh_interval        = each.value.refresh_interval
  static_ip_enabled       = each.value.static_ip
```

- `for_each = var.connectors` : **un connecteur par entrée** de la map. Avec l'exemple, 5 connecteurs : `gcalendar`,
  `gdrive`, `github`, `sharepoint`, `teams`. Adresses : `google_discovery_engine_data_connector.src["sharepoint"]`, etc.
- `each.key` = la clé de l'entrée (`"sharepoint"`) ; `each.value` = l'objet complet ci-dessus. Voir
  [00-bases §8.2](00-bases-terraform.md#82-for_each--un-exemplaire-par-élément-dune-map-ou-dun-set).
- `location = var.ge_location` : `"eu"`, comme l'app.
- `collection_id = each.key` : la clé de l'entrée devient l'**identifiant** de la collection (`"sharepoint"`).
- `collection_display_name = each.value.display_name` : nom affiché (`"SharePoint"`).
- `data_source = each.value.data_source` : le **type** de source, nom fixé par Google (`"google_drive"`,
  `"sharepoint"`, `"github"`…). Pour SharePoint, `sharepoint` ou `sharepoint_federated_search` est **à vérifier**
  ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- `connector_modes = each.value.modes` : `["FEDERATED"]` par défaut ; `["DATA_INGESTION"]` pour copier/indexer.
- `refresh_interval = each.value.refresh_interval` : fréquence de synchronisation, `"86400s"` (24 h) par défaut.
- `static_ip_enabled = each.value.static_ip` : `true` pour SharePoint, Teams et GitHub dans l'exemple. Gemini
  Enterprise appellera la source depuis des IP fixes, à autoriser côté SaaS ([guide du socle (docs/00) §7.5](../../docs/00-socle-securite.md#75-ip-statiques--nautoriser-que-gemini-enterprise-côté-saas)).
  **Immuable** : on ne peut pas l'activer après coup sans recréer le connecteur.

### 3.2 Les paramètres : valeurs normales + références de secrets

```hcl
  # Paramètres : les valeurs secrètes sont des RÉFÉRENCES Secret Manager, jamais des valeurs.
  json_params = jsonencode(merge(
    each.value.params,
    { for k, s in each.value.secret_params : k => "${data.google_secret_manager_secret.connector[s].name}/versions/latest" },
  ))
```

Chaque source attend des paramètres (URL de l'instance, tenant, identifiants OAuth…). On les passe sous forme d'un
**texte JSON** dans `json_params`. Construction, de l'intérieur vers l'extérieur :

1. `{ for k, s in each.value.secret_params : k => "..." }` : **expression `for`** sur une map. `k` reçoit le nom du
   paramètre (`client_id`), `s` le **nom du secret** (`"sharepoint-client-id"`). Pour chacun, on fabrique la
   **référence** du secret :
   - `data.google_secret_manager_secret.connector[s]` : le secret lu dans [`20_data_protection.tf`](../20_data_protection.tf) ;
   - `.name` : son nom complet, de la forme `projects/<numéro du projet>/secrets/sharepoint-client-id` ;
   - on ajoute `/versions/latest` : « la dernière version », résolue par Gemini Enterprise **au moment de l'appel**.

   Voir [00-bases §12.2](00-bases-terraform.md#122-boucles-for-transformer-une-liste-ou-une-map).
2. `merge(each.value.params, {...})` : **fusionne** les paramètres normaux et les références de secrets en une seule
   map. (Si un même nom existait dans les deux, la map de droite gagnerait.)
3. `jsonencode(...)` : transforme la map en **texte JSON**. Les clés sortent triées par ordre alphabétique.

Résultat pour `sharepoint` (numéro de projet fictif `123456789012`) :

```json
{"client_id":"projects/123456789012/secrets/sharepoint-client-id/versions/latest","client_secret":"projects/123456789012/secrets/sharepoint-client-secret/versions/latest","instance_uri":"https://acme.sharepoint.com","tenant_id":"00000000-0000-0000-0000-000000000000"}
```

Pour `gdrive` : `params = {}` et `secret_params = {}`, donc `json_params = "{}"`.

Pourquoi des références : la **valeur** du secret n'apparaît ni dans le code, ni dans l'état Terraform, ni dans le
`plan`. Une rotation (nouvelle version du secret) est prise en compte sans redéploiement
([guide du socle (docs/00) §6.2](../../docs/00-socle-securite.md#62-secrets-des-connecteurs--jamais-dans-le-code)).

Les **noms** des paramètres (`instance_uri`, `tenant_id`, `organization`…) dépendent de chaque source et sont
**à confirmer** dans la page du connecteur de la doc Google (marqués `[à confirmer]` dans `terraform.tfvars.example`).

### 3.3 La clé CMEK, seulement pour l'ingestion

```hcl
  # CMEK : seules les données COPIÉES (ingestion) sont chiffrées avec la clé du client.
  kms_key_name = var.enable_cmek && contains(each.value.modes, "DATA_INGESTION") ? google_kms_crypto_key.ge[0].id : null
```

- **Ternaire** `condition ? A : B` ([00-bases §12.1](00-bases-terraform.md#121-condition-ternaire)), avec une condition
  composée par `&&` (« et ») :
  - `var.enable_cmek` : CMEK est activé ;
  - `contains(each.value.modes, "DATA_INGESTION")` : `true` si la liste des modes contient `"DATA_INGESTION"`.
- Si les deux sont vrais : la clé principale `google_kms_crypto_key.ge[0].id` (créée dans
  [`20_data_protection.tf`](../20_data_protection.tf)).
- Sinon : `null`, ce qui veut dire « ne pas renseigner l'argument ». En fédéré, rien n'est stocké, il n'y a rien à
  chiffrer.
- Avec l'exemple : les 5 connecteurs sont en `["FEDERATED"]`, donc `kms_key_name = null` partout. Pour le `jira`
  commenté de l'exemple (`modes = ["DATA_INGESTION"]`) : 
  `projects/acme-gemini-enterprise-prd/locations/europe/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-data`.
- Les clés **régionales** (exigées pour les connecteurs tiers en ingestion) ne sont pas citées ici : elles sont
  enregistrées dans la configuration CMEK de Gemini Enterprise (`single_region_keys`, voir [05-data-protection.md](05-data-protection.md)).

### 3.4 Les entités (un bloc par type d'objet)

```hcl
  dynamic "entities" {
    for_each = each.value.entities
    content {
      entity_name = entities.value.name
      params      = entities.value.params
    }
  }
```

- `dynamic "entities"` : génère un sous-bloc `entities { ... }` **par élément** de la liste `each.value.entities`.
  Dans `content`, l'élément en cours s'appelle comme le bloc : `entities.value`. Voir
  [00-bases §10](00-bases-terraform.md#10-les-blocs-imbriqués-optionnels-ou-répétés--dynamic).
- Attention à ne pas confondre : `each` désigne le **connecteur** en cours (boucle de la ressource), `entities`
  désigne l'**entité** en cours (boucle du bloc dynamique).
- `entity_name = entities.value.name` : le type d'objet (`"file"` pour SharePoint ; `"project"`, `"issue"`,
  `"comment"` pour le Jira d'exemple).
- `params = entities.value.params` : paramètres propres à l'entité (texte), `null` si absent (l'argument est alors
  omis).
- Avec l'exemple : `sharepoint` produit **un** bloc ; `gdrive`, `gcalendar`, `teams`, `github` n'ont pas
  d'`entities` (liste vide) : **zéro** bloc.

```hcl
  # Équivalent écrit à la main pour sharepoint :
  entities {
    entity_name = "file"
  }
```

### 3.5 L'ordre de création

```hcl
  depends_on = [
    google_discovery_engine_acl_config.identity,
    google_discovery_engine_cmek_config.ge, # la clé doit être enregistrée AVANT
    google_secret_manager_secret_iam_member.ge_reads,
  ]
}
```

`depends_on` force des dépendances qui n'apparaissent dans aucun attribut ([00-bases §9](00-bases-terraform.md#9-lordre-de-création--automatique-ou-forcé-avec-depends_on)) :

- `google_discovery_engine_acl_config.identity` ([`10_identity_access.tf`](../10_identity_access.tf),
  [04-identity-access.md](04-identity-access.md)) : la configuration d'identité (qui sont les utilisateurs, quel
  fournisseur d'identité) doit exister avant les connecteurs, qui s'appuient dessus pour appliquer les droits.
- `google_discovery_engine_cmek_config.ge` ([`20_data_protection.tf`](../20_data_protection.tf)) : la clé doit être
  **enregistrée avant**, sinon les données ingérées seraient chiffrées par Google.
- `google_secret_manager_secret_iam_member.ge_reads` ([`20_data_protection.tf`](../20_data_protection.tf)) : Gemini
  Enterprise doit pouvoir **lire les secrets** au moment où il crée le connecteur.

### 3.6 La liste des data stores créés

```hcl
locals {
  # Chaque entité d'un connecteur produit un data store "<collection>_<entité>".
  connector_data_store_ids = flatten([
    for c in google_discovery_engine_data_connector.src : [
      for e in c.entities : basename(e.data_store) if try(e.data_store != null && e.data_store != "", false)
    ]
  ])
}
```

L'app ([`50_app.tf`](../50_app.tf)) doit connaître les **identifiants courts** des data stores à interroger. Google
les crée pendant la création du connecteur et les renvoie dans l'attribut `data_store` de chaque entité. Ce bloc les
récupère.

1. `for c in google_discovery_engine_data_connector.src` : boucle sur les connecteurs créés (une ressource avec
   `for_each` est une map ; avec une seule variable, `c` reçoit chaque **ressource**).
2. `for e in c.entities : ... if ...` : boucle **imbriquée** sur les entités de ce connecteur, avec un **filtre**
   `if` qui ne garde que les entités qui ont un data store.
3. `try(e.data_store != null && e.data_store != "", false)` : vaut `true` seulement si l'entité a un data store
   (ni `null`, ni vide). Si évaluer l'attribut provoque une erreur (attribut absent), `try` renvoie `false`.
   Ce filtre garantit que `basename` ne reçoit jamais `null` (ce qui ferait échouer le `plan`).
4. `basename(e.data_store)` : garde la **dernière partie** du chemin. Exemple :
   `basename("projects/123456789012/locations/eu/collections/sharepoint/dataStores/sharepoint_file")` →
   `"sharepoint_file"`.
5. On obtient une **liste de listes** (une par connecteur) ; `flatten` l'aplatit.

Avec l'exemple :

```hcl
# avant flatten (ordre alphabétique des connecteurs) :
[ [], [], [], ["sharepoint_file"], [] ]   # gcalendar, gdrive, github, sharepoint, teams
# après flatten :
local.connector_data_store_ids = ["sharepoint_file"]
```

Le format exact du chemin et du nom `<collection>_<entité>` est celui annoncé par le commentaire du code ; il est
**à vérifier** au premier déploiement. Les connecteurs **sans entités** (Workspace, Teams, GitHub dans l'exemple) ne
fournissent aucun ID ici : s'ils créent quand même des data stores, il faut ajouter leurs IDs dans
`extra_data_store_ids` ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).

---

## 4. Ce que Terraform crée concrètement

Avec `terraform.tfvars.example` : **5 connecteurs** (5 ressources), donc 5 collections dans Gemini Enterprise
(`eu`) : Google Drive, Google Agenda, SharePoint, Microsoft Teams, GitHub. Tous en **fédéré**, sans clé CMEK. Trois
ont des IP statiques (SharePoint, Teams, GitHub). SharePoint crée un data store pour l'entité `file`.

Dans la console : *Gemini Enterprise → Data stores / Connecteurs*. Après `apply` :

- `terraform output connector_static_ips` : les IP à autoriser côté Microsoft et GitHub ;
- `terraform output connector_states` : l'état de chaque connecteur ; `ALLOWLIST_STATIC_IP` tant que les IP ne sont pas
  autorisées ;
- il reste à faire l'**autorisation OAuth initiale** dans la console ([guide du socle (docs/00) §7.6](../../docs/00-socle-securite.md#76-ajouter-une-source-procédure)).

Le bloc `locals` ne crée rien : il calcule une liste.

---

## 5. Dépendances avec les autres fichiers

**Ce fichier utilise :**

| Valeur | Vient de |
|---|---|
| `var.connectors`, `var.ge_location`, `var.enable_cmek` | [`variables.tf`](../variables.tf) ([02-variables.md](02-variables.md)) et `terraform.tfvars` ([12-tfvars.md](12-tfvars.md)) |
| `google_discovery_engine_acl_config.identity` | [`10_identity_access.tf`](../10_identity_access.tf) ([04-identity-access.md](04-identity-access.md)) |
| `data.google_secret_manager_secret.connector`, `google_secret_manager_secret_iam_member.ge_reads`, `google_kms_crypto_key.ge`, `google_discovery_engine_cmek_config.ge` | [`20_data_protection.tf`](../20_data_protection.tf) ([05-data-protection.md](05-data-protection.md)) |

À noter : `20_data_protection.tf` lit lui aussi `var.connectors` pour trouver la liste des secrets (`local.secret_ids`).

**Ce fichier est utilisé par :**

| Valeur | Utilisée dans |
|---|---|
| `local.connector_data_store_ids` | `data_store_ids` de l'app : `concat(local.connector_data_store_ids, var.extra_data_store_ids)` ([`50_app.tf`](../50_app.tf), [08-app.md](08-app.md)) |
| `google_discovery_engine_data_connector.src` | sorties `connector_static_ips` et `connector_states` ([`outputs.tf`](../outputs.tf), [11-outputs.md](11-outputs.md)) |

---

## 6. Pour reproduire / adapter

**Cas 1 (le plus courant) : ajouter une source dans CE projet.** Pas de code : une entrée dans `terraform.tfvars`.
Exemple, un connecteur Jira en **ingestion** (repris de l'exemple commenté) :

```hcl
connectors = {
  # ... entrées existantes ...
  jira = {                                    # clé = ID de collection (ne plus la changer ensuite)
    data_source  = "jira"
    display_name = "Jira"
    modes        = ["DATA_INGESTION"]         # copie indexée => chiffrée avec la clé CMEK
    params = {                                # paramètres NON secrets [à confirmer dans la doc du connecteur]
      instance_uri = "https://acme.atlassian.net"
      instance_id  = "..."
      auth_type    = "OAUTH"
    }
    secret_params = {                         # paramètre => NOM du secret (créé avant par la sécurité)
      client_id     = "jira-client-id"
      client_secret = "jira-client-secret"
      refresh_token = "jira-refresh-token"
    }
    entities  = [{ name = "project" }, { name = "issue" }, { name = "comment" }]
    static_ip = true                          # à décider dès la création (immuable)
  }
}
```

**Cas 2 : reproduire le modèle dans un autre projet Terraform.** Squelette commenté :

```hcl
variable "connectors" {
  type = map(object({
    data_source   = string
    display_name  = string
    modes         = optional(list(string), ["FEDERATED"])
    params        = optional(map(string), {})
    secret_params = optional(map(string), {})   # param => nom du secret Secret Manager
    entities      = optional(list(object({ name = string, params = optional(string) })), [])
    static_ip     = optional(bool, false)
  }))
  default = {}
}

# Les secrets cités (lus, jamais leurs valeurs).
locals {
  secret_ids = toset(flatten([for c in var.connectors : values(c.secret_params)]))
}

data "google_secret_manager_secret" "s" {
  for_each  = local.secret_ids
  secret_id = each.value
}

resource "google_discovery_engine_data_connector" "src" {
  for_each = var.connectors

  location                = "eu"
  collection_id           = each.key
  collection_display_name = each.value.display_name
  data_source             = each.value.data_source
  connector_modes         = each.value.modes
  refresh_interval        = "86400s"
  static_ip_enabled       = each.value.static_ip

  # Paramètres normaux + RÉFÉRENCES de secrets, dans un seul JSON.
  json_params = jsonencode(merge(
    each.value.params,
    { for k, s in each.value.secret_params : k => "${data.google_secret_manager_secret.s[s].name}/versions/latest" },
  ))

  # Clé CMEK uniquement si des données sont copiées.
  kms_key_name = contains(each.value.modes, "DATA_INGESTION") ? "projects/.../cryptoKeys/ma-cle" : null

  dynamic "entities" {
    for_each = each.value.entities
    content {
      entity_name = entities.value.name
      params      = entities.value.params
    }
  }

  # Ajouter ici : la config d'identité, la config CMEK, les droits de lecture des secrets.
  # depends_on = [ ... ]
}
```

**Étapes :**

1. **Côté source** : créer l'application OAuth (Entra ID, GitHub App, Atlassian…) avec les permissions minimales en
   lecture et l'URL de redirection `https://vertexaisearch.cloud.google.com/oauth-redirect`.
2. **Sécurité** : créer les secrets dans Secret Manager (UE) **avant** le `plan`
   (`gcloud secrets create ...` puis `gcloud secrets versions add ...`, voir `terraform.tfvars.example`).
3. **Code** : ajouter l'entrée dans `connectors` ; trouver les noms exacts de `data_source`, des paramètres et des
   entités dans la page du connecteur de la doc Google et dans
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_data_connector
4. **Décider fédéré ou ingestion** ([guide du socle (docs/00) §7.2](../../docs/00-socle-securite.md#72-fédéré-ou-ingestion--la-décision-de-sécurité-la-plus-importante)),
   et `static_ip` (immuable).
5. `terraform plan` : vérifier qu'aucun connecteur existant n'est **recréé** (`-/+`), ni l'app.
6. Après `apply` : autoriser les IP (`terraform output connector_static_ips`), faire l'autorisation OAuth dans la
   console, puis tester qu'un utilisateur sans droit ne voit pas un document de test.

---

## 7. Pièges et bonnes pratiques

- **La clé CMEK doit être enregistrée avant les connecteurs.** Le `depends_on` sur
  `google_discovery_engine_cmek_config.ge` le garantit. Un connecteur en ingestion créé avant reste chiffré par Google.
- **`static_ip` est immuable** : le changer recrée le connecteur (et oblige à refaire l'autorisation OAuth et
  l'allowlist). Activez-le dès la création pour les sources tierces.
- **La clé de l'entrée (`sharepoint`, `jira`…) devient `collection_id`** : la renommer dans `terraform.tfvars` =
  détruire puis recréer le connecteur. Choisissez une clé définitive.
- **`json_params` plutôt que `params`** : la ressource propose aussi un argument `params` (map de textes). Le projet
  n'utilise que `json_params`, construit avec `jsonencode`. N'utilisez **qu'un des deux**, jamais les deux.
- **Jamais de valeur secrète dans `params`** : `params` finit en clair dans le code, l'état et le `plan`. Tout ce qui
  est secret va dans `secret_params` (des **noms** de secrets).
- **Les secrets doivent exister avant `plan`**, sinon la lecture `data.google_secret_manager_secret` échoue.
- **Noms de paramètres et de `data_source` à confirmer** pour certaines sources (Teams, GitHub, SharePoint fédéré,
  BigQuery en ingestion) : en cas de doute, créer une fois le connecteur dans la console et comparer
  ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- **Ajouter un connecteur modifie `data_store_ids` de l'app**, ce qui peut **recréer l'app** (bug connu du provider).
  Lisez le `plan` et ajoutez les connecteurs de préférence avant le lancement ([guide du socle (docs/00) §16](../../docs/00-socle-securite.md#16-vérifié--à-valider-en-recette)).
- **Sources sans entités** (Workspace, Teams, GitHub) : leurs data stores n'apparaissent pas dans
  `connector_data_store_ids` ; les ajouter à la main dans `extra_data_store_ids` si besoin.
- **Toujours filtrer avant d'appeler une fonction sur une valeur « connue après apply »** : `basename(null)` fait
  échouer le `plan`. Le filtre `try(e.data_store != null && e.data_store != "", false)` écarte `null`, chaîne vide
  et attribut absent.
- **BigQuery en ingestion perd les droits BigQuery** : tout utilisateur de l'app voit toutes les lignes indexées.
  N'indexer qu'un dataset curé, ou préférer le fédéré ([guide du socle (docs/00) §7.3](../../docs/00-socle-securite.md#73-les-sources-de-acme)).
- **En fédéré, la question part chez l'éditeur de la source** (Microsoft, GitHub…) et relève de ses conditions.
