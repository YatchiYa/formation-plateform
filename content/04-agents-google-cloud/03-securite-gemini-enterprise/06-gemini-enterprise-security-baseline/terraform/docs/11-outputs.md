# 11. `outputs.tf` : les sorties

> Les informations utiles affichées après `terraform apply` : lien de l'app, IP à autoriser, état des connecteurs,
> identifiants des protections. Bases Terraform : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Après un déploiement, on a besoin de quelques informations que seul Google connaît : l'adresse de la console, les IP
fixes des connecteurs, l'état de chaque connecteur… Ce fichier les déclare comme **sorties** (*outputs*). Terraform
les affiche à la fin de `apply` et on peut les relire à tout moment avec `terraform output`. Il ne crée **rien** chez
Google.

---

## 2. Vue d'ensemble

| Bloc (adresse) | Type de bloc | Rôle en une phrase |
|---|---|---|
| `output.app_console_url` | `output` | Lien vers la page d'administration de l'app. |
| `output.data_store_ids` | `output` | Liste des data stores rattachés à l'app. |
| `output.connector_static_ips` | `output` | IP sortantes fixes à autoriser côté SaaS, par connecteur. |
| `output.connector_states` | `output` | État et blocages éventuels de chaque connecteur. |
| `output.cmek_key` | `output` | Identifiant de la clé de chiffrement, ou « CMEK désactivé ». |
| `output.model_armor_templates` | `output` | Identifiants des deux templates Model Armor. |
| `output.agent_gateway` | `output` | Identifiant de l'Agent Gateway, ou « désactivé ». |

---

## 3. Le code expliqué, bloc par bloc

Rappel : un bloc `output` a une `value` (obligatoire) et une `description` (facultative, mais utile)
([00-bases §6.5](00-bases-terraform.md#65-output--les-sorties)).

### 3.1 `app_console_url`

```hcl
output "app_console_url" {
  description = "Page d'administration ; lien de l'app web dans l'onglet Intégration."
  value       = "https://console.cloud.google.com/gemini-enterprise/locations/${var.ge_location}/engines/${var.app_id}/overview?project=${var.project_id}"
}
```

- `value` : une URL construite par **interpolation** (`${...}` insère une valeur dans le texte).
- Avec le `terraform.tfvars.example` (`project_id = "acme-gemini-enterprise-prd"`, et les défauts
  `ge_location = "eu"`, `app_id = "assistant-ia"`) :
  `https://console.cloud.google.com/gemini-enterprise/locations/eu/engines/assistant-ia/overview?project=acme-gemini-enterprise-prd`
- Ce n'est **pas** le lien que les utilisateurs ouvrent : c'est la page d'administration. Le lien de l'app web se
  copie dans l'onglet *Intégration* de cette page (README §12.3).
- Cette sortie ne dépend que de variables : elle est connue dès le `plan`.

### 3.2 `data_store_ids`

```hcl
output "data_store_ids" {
  value = google_discovery_engine_search_engine.app.data_store_ids
}
```

- Relit l'attribut `data_store_ids` de l'app ([`50_app.tf`](../50_app.tf)) : la liste réellement rattachée.
- Sert à vérifier que chaque connecteur a bien produit son data store. Exemple possible avec le
  `terraform.tfvars.example` : `["sharepoint_file"]` (l'entité `file` de SharePoint). Les connecteurs sans
  `entities` (Drive, Agenda, Teams, GitHub) pourraient ne rien produire ici : point **à vérifier** au premier
  déploiement (README §16). S'il manque des data stores, ajoutez leurs ID dans `extra_data_store_ids`.

### 3.3 `connector_static_ips` : une boucle `for` avec filtre `if`

```hcl
output "connector_static_ips" {
  description = "IP sortantes à autoriser côté SaaS (connecteurs avec static_ip = true)."
  value       = { for k, c in google_discovery_engine_data_connector.src : k => c.static_ip_addresses if var.connectors[k].static_ip }
}
```

C'est une **expression `for`** qui fabrique une map
([00-bases §12.2](00-bases-terraform.md#122-boucles-for-transformer-une-liste-ou-une-map)). Lisons-la morceau par
morceau :

| Morceau | Signification |
|---|---|
| `{ … }` | Le résultat sera une **map** (des accolades). Avec des crochets `[ … ]`, ce serait une liste. |
| `for k, c in google_discovery_engine_data_connector.src` | Parcourir tous les connecteurs. Comme ils sont créés avec `for_each`, `src` est une map : `k` = la clé (`"gdrive"`, `"sharepoint"`…), `c` = le connecteur. |
| `k => c.static_ip_addresses` | Pour chaque connecteur, une entrée « nom → liste de ses IP fixes ». `=>` sépare la clé de la valeur. |
| `if var.connectors[k].static_ip` | **Filtre** : ne garder que les connecteurs dont `static_ip = true` dans `terraform.tfvars`. Les autres sont **ignorés** (pas d'entrée du tout). |

Exemple avec le `terraform.tfvars.example` : `sharepoint`, `teams` et `github` ont `static_ip = true` ; `gdrive` et
`gcalendar` non. Le résultat a donc cette forme (IP d'exemple) :

```hcl
{
  github     = ["34.0.0.1", "34.0.0.2"]
  sharepoint = ["34.0.0.1", "34.0.0.2"]
  teams      = ["34.0.0.1", "34.0.0.2"]
}
```

Ce sont ces adresses qu'on autorise côté Microsoft, GitHub… (README §7.5).

### 3.4 `connector_states`

```hcl
output "connector_states" {
  description = "État et blocages éventuels (ex. ALLOWLIST_STATIC_IP)."
  value       = { for k, c in google_discovery_engine_data_connector.src : k => { state = c.state, blocking = c.blocking_reasons } }
}
```

- Même boucle que 3.3, **sans filtre** : tous les connecteurs apparaissent.
- La valeur de chaque entrée est un **objet** à deux champs, construit sur place :
  - `state = c.state` : l'état du connecteur (actif, en création, en erreur…) ;
  - `blocking = c.blocking_reasons` : la liste des raisons de blocage. Exemple typique :
    `["ALLOWLIST_STATIC_IP"]` tant que les IP fixes ne sont pas autorisées côté SaaS.
- Forme du résultat :

  ```hcl
  {
    gdrive     = { state = "ACTIVE", blocking = [] }
    sharepoint = { state = "...",    blocking = ["ALLOWLIST_STATIC_IP"] }
    ...
  }
  ```

  (Les valeurs exactes de `state` sont celles de l'API Google : à lire dans votre propre sortie.)
- Attention : comme toutes les sorties, c'est la valeur **au moment du dernier `apply` ou `refresh`**. Pour voir un
  état à jour, relancer `terraform apply -refresh-only` (ou `terraform plan`) avant `terraform output`.

### 3.5 `cmek_key`

```hcl
output "cmek_key" {
  value = var.enable_cmek ? google_kms_crypto_key.ge[0].id : "CMEK désactivé"
}
```

- Une **condition ternaire** ([00-bases §12.1](00-bases-terraform.md#121-condition-ternaire)) : l'ID de la clé si
  CMEK est activé, sinon un texte explicite. `[0]` car la clé est créée avec `count`
  ([`20_data_protection.tf`](../20_data_protection.tf)).
- Les deux branches sont des **textes** : la sortie a toujours le même type.
- Avec le `terraform.tfvars.example` (`enable_cmek` absent, donc `true`), forme :
  `projects/acme-gemini-enterprise-prd/locations/europe/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-data`.

### 3.6 `model_armor_templates`

```hcl
output "model_armor_templates" {
  value = { for k, t in google_model_armor_template.shield : k => t.id }
}
```

- Boucle `for` sur les deux templates créés avec `for_each` ([`30_ai_guardrails.tf`](../30_ai_guardrails.tf)).
  Résultat : une map « nom → ID ».
- Forme : `{ "ge-prompt-shield" = "projects/…/locations/eu/templates/ge-prompt-shield", "ge-response-shield" = "…" }`.
- Utile pour le script de test (`scripts/test_model_armor.sh`) ou pour vérifier dans la console.

### 3.7 `agent_gateway`

```hcl
output "agent_gateway" {
  value = var.enable_agent_gateway ? google_network_services_agent_gateway.egress[0].id : "désactivé"
}
```

- Même principe que `cmek_key` : l'ID de la passerelle si l'option est active ([`60_advanced.tf`](../60_advanced.tf)),
  sinon `"désactivé"`. Avec le `terraform.tfvars.example` : `"désactivé"`.

### 3.7 bis `log_buckets`

```hcl
output "log_buckets" {
  description = "Buckets de journaux dédiés (Logs Explorer > Affiner la portée > Stockage)."
  value       = { for k, b in local.log_buckets : k => "projects/${var.project_id}/locations/${var.ge_location}/buckets/${b}" }
}
```

- Boucle `for` sur la map `local.log_buckets` (définie dans [`80_logging.tf`](../80_logging.tf)) : pour chaque nom
  court (`security`, `usage`), on construit le **chemin complet** du bucket. Avec l'exemple :
  `{ security = "projects/acme-gemini-enterprise-prd/locations/eu/buckets/ge-security", usage = ".../ge-usage" }`.
- **Usage :** dans *Logs Explorer → Affiner la portée → Stockage*, on choisit ce bucket pour y chercher. Détails :
  [13-logging.md](13-logging.md).

### 3.8 Lire les sorties

```bash
terraform output                                   # toutes les sorties, format lisible
terraform output connector_states                  # une seule sortie
terraform output -raw app_console_url              # le texte brut, sans guillemets (pour copier ou pour un script)
terraform output -json connector_static_ips        # au format JSON (pour un outil comme jq)
terraform output -json connector_static_ips | jq -r '.[][]' | sort -u   # liste unique des IP, une par ligne
```

- **`-raw`** ne marche que pour une sortie **simple** (texte, nombre, booléen). Sur une map, utilisez `-json`.
- **`-json`** donne un format stable, lisible par un programme (CI, script).
- Les sorties sont lues depuis l'**état** (`terraform.tfstate`, [00-bases §3](00-bases-terraform.md#3-létat--state-)) :
  pas besoin de recontacter Google, mais il faut avoir fait au moins un `apply`.

---

## 4. Ce que Terraform crée concrètement

**Aucune ressource.** Les sorties sont seulement **stockées dans l'état** et affichées. Avec le
`terraform.tfvars.example`, les 7 sorties existent : `connector_static_ips` contient 3 entrées (`github`,
`sharepoint`, `teams`), `connector_states` 5 entrées, `cmek_key` un ID de clé et `agent_gateway` le texte
`"désactivé"`.

---

## 5. Dépendances avec les autres fichiers

| Sortie | Lit… | Fichier | Fiche |
|---|---|---|---|
| `app_console_url` | variables | [`variables.tf`](../variables.tf) | [02-variables.md](02-variables.md) |
| `cmek_key` | `google_kms_crypto_key.ge` | [`20_data_protection.tf`](../20_data_protection.tf) | [05-data-protection.md](05-data-protection.md) |
| `model_armor_templates` | `google_model_armor_template.shield` | [`30_ai_guardrails.tf`](../30_ai_guardrails.tf) | [06-ai-guardrails.md](06-ai-guardrails.md) |
| `connector_static_ips`, `connector_states` | `google_discovery_engine_data_connector.src`, `var.connectors` | [`40_connectors.tf`](../40_connectors.tf) | [07-connectors.md](07-connectors.md) |
| `data_store_ids` | `google_discovery_engine_search_engine.app` | [`50_app.tf`](../50_app.tf) | [08-app.md](08-app.md) |
| `agent_gateway` | `google_network_services_agent_gateway.egress` | [`60_advanced.tf`](../60_advanced.tf) | [09-advanced.md](09-advanced.md) |

---

## 6. Pour reproduire / adapter

**Besoin type : ajouter une sortie.**

```hcl
# Une valeur simple (attribut d'une ressource unique)
output "nom_de_la_sortie" {
  description = "À quoi sert cette valeur, et quoi en faire."
  value       = google_xxx.ma_ressource.attribut
}

# Une ressource optionnelle (count) : toujours protéger le [0] par la même condition
output "mon_option" {
  value = var.enable_mon_option ? google_xxx.mon_option[0].id : "désactivé"
}

# Plusieurs exemplaires (for_each) : une map "clé -> attribut", avec un filtre facultatif
output "mes_elements" {
  value = { for k, r in google_xxx.mes_elements : k => r.attribut if r.attribut != null }
}

# Une valeur secrète : masquée dans l'affichage (mais toujours en clair dans l'état !)
output "valeur_sensible" {
  value     = google_xxx.ma_ressource.secret
  sensitive = true
}
```

1. Chercher l'attribut voulu dans la section *Attributes Reference* de la doc de la ressource, par exemple
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_data_connector
   (attributs `state`, `blocking_reasons`, `static_ip_addresses`).
2. Ajouter le bloc `output` dans `outputs.tf`, avec une `description` qui dit **quoi faire** de la valeur.
3. Tester l'expression avant : `terraform console`, puis taper l'expression.
4. `terraform apply` (une nouvelle sortie seule ne modifie aucune ressource), puis `terraform output nom_de_la_sortie`.

---

## 7. Pièges et bonnes pratiques

- **`[0]` sans condition plante** quand la ressource a `count = 0`. Toujours `condition ? x[0].id : "désactivé"`,
  ou `x[*].id` (liste, éventuellement vide).
- **Une sortie peut être périmée** : elle reflète le dernier `apply`. Pour `connector_states`, faites
  `terraform apply -refresh-only` avant de conclure.
- **`sensitive = true` masque l'affichage, pas l'état** : la valeur reste lisible dans `terraform.tfstate`. Ce
  projet n'expose volontairement **aucun secret** en sortie (les secrets ne sont jamais connus de Terraform).
- **Le filtre `if` retire l'entrée**, il ne met pas une valeur vide : un connecteur sans IP fixe est absent de
  `connector_static_ips`, pas présent avec `[]`.
- **`var.connectors[k]`** dans le filtre suppose que chaque connecteur créé vient bien de `var.connectors` (c'est le
  cas : `for_each = var.connectors`). Si vous changez la source du `for_each`, adaptez le filtre.
- Le lien `app_console_url` est construit à la main : si Google change le format des URL de la console, il faudra
  l'adapter (aucune erreur Terraform ne le signalera).
