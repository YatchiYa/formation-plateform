# 12. `terraform.tfvars.example` : la configuration du déploiement

> Le modèle du fichier où l'on donne **ses** valeurs (projet, groupes, connecteurs). C'est le seul fichier à
> modifier pour un déploiement standard. Bases Terraform : [00-bases-terraform.md](00-bases-terraform.md).

---

## 1. À quoi sert ce fichier

Les fichiers `.tf` décrivent **comment** construire le socle ; ils utilisent des **variables**
([00-bases §6.3](00-bases-terraform.md#63-variable--les-entrées)) déclarées dans [`variables.tf`](../variables.tf).
Un fichier **`.tfvars`** donne les **valeurs** de ces variables pour un déploiement précis. `terraform.tfvars.example`
est un **modèle** : on le copie en `terraform.tfvars`, on remplace les valeurs, et Terraform le lit tout seul à chaque
`plan` et `apply`. Il ne contient **aucun secret** : seulement des noms.

---

## 2. Vue d'ensemble

Le fichier suit l'ordre de ses commentaires :

| Partie du fichier | Variables | Rôle en une phrase |
|---|---|---|
| En-tête | (aucune) | Comment créer `terraform.tfvars` et ne jamais le committer. |
| Projet et localisation | `project_id`, `ge_location` (en commentaire) | Le projet Google Cloud cible et la zone des données. |
| Groupes et alertes | `user_groups`, `admin_groups`, `security_groups`, `viewer_groups`, `alert_email` | Qui a accès à quoi, et qui reçoit les alertes. |
| Phrases interdites | `banned_phrases` (en commentaire) | Expressions que l'assistant ne doit jamais produire. |
| Connecteurs | `connectors` | Les sources de données : une entrée par source. |

Toutes les variables **absentes** du fichier prennent leur **valeur par défaut** de `variables.tf` (voir §3.6).

---

## 3. Le contenu expliqué, partie par partie

**Rappel : qu'est-ce qu'un `.tfvars` ?**
- Une simple liste `nom_de_variable = valeur`, en syntaxe HCL. Pas de blocs `resource`, pas de `var.` : uniquement
  des valeurs.
- Terraform charge **automatiquement** `terraform.tfvars` (et les fichiers `*.auto.tfvars`). Un autre nom
  (par exemple `recette.tfvars`) se passe à la main : `terraform plan -var-file=recette.tfvars`.
- Une variable **sans `default`** dans `variables.tf` est **obligatoire** : si elle manque, `plan` s'arrête. Ici :
  `project_id`, `user_groups`, `admin_groups`, `security_groups`.

### 3.1 L'en-tête

```hcl
# cp terraform.tfvars.example terraform.tfvars   (ne jamais committer terraform.tfvars)
```

- La commande à lancer dans le dossier `terraform/` pour créer **votre** fichier.
- **Pourquoi ne jamais committer `terraform.tfvars`** : il décrit un environnement réel (projet de production,
  adresses, groupes, identifiants de tenant). Ce n'est pas secret au sens « mot de passe », mais ce sont des
  informations internes qui n'ont rien à faire dans un dépôt partagé. Le `.example`, lui, est committé : c'est la
  documentation du format.
- Le projet contient un fichier [`.gitignore`](../../.gitignore) qui exclut déjà `terraform.tfvars`, `*.tfstate*`,
  `*.tfplan` et `.terraform/`. Vérifiez qu'il est bien présent si vous copiez le projet ailleurs.

### 3.2 Projet et localisation

```hcl
project_id = "acme-gemini-enterprise-prd"
# ge_location = "eu"   # IMMUABLE
```

- `project_id` : l'**ID** du projet Google Cloud (le texte, pas le numéro). **Obligatoire.** Il doit déjà exister,
  dans l'organisation de l'entreprise, avec la facturation activée (guide du socle (docs/00) §12.1).
- `ge_location` : en commentaire, donc le défaut `"eu"` s'applique (données en Union européenne). Une
  **validation** dans `variables.tf` n'accepte que `"eu"` ou `"us"` (CMEK impossible en `global`).
  **IMMUABLE** : la changer après coup recrée l'app et ses données. Décidez-la une fois pour toutes.

### 3.3 Groupes et alertes

```hcl
user_groups     = ["group:gemini-utilisateurs@acme.example"]
admin_groups    = ["group:gemini-admins@acme.example"]
security_groups = ["group:securite-ia@acme.example"]
viewer_groups   = ["group:gemini-pilotage@acme.example"]
alert_email     = "securite-ia@acme.example"
```

- Ce sont des **listes** (crochets), même avec un seul groupe : on peut en mettre plusieurs, séparés par des virgules.
- Le préfixe **`group:`** est le format IAM de Google pour désigner un groupe (les autres formats sont `user:` et
  `serviceAccount:`). Le socle n'attribue des droits **qu'à des groupes**, jamais à des personnes (guide du socle (docs/00) §5.2) :
  on ajoute ou retire quelqu'un dans l'annuaire, sans toucher à Terraform.

| Variable | Qui | Ce que ça donne |
|---|---|---|
| `user_groups` | Les utilisateurs de l'app | Rôle utilisateur Gemini Enterprise. |
| `admin_groups` | Les administrateurs de l'app (petit groupe) | Rôle administrateur Gemini Enterprise. |
| `security_groups` | L'équipe sécurité | **Seule** à gérer Model Armor, les clés KMS et à lire les journaux privés. |
| `viewer_groups` | Pilotage, DPO | Lecture seule et statistiques. Facultatif (défaut `[]`). |

- `alert_email` : la boîte qui reçoit les alertes de [`70_detection.tf`](../70_detection.tf). Vide (`""`, défaut) =
  pas de canal e-mail, donc des alertes que personne ne reçoit. Mettez une **liste de diffusion** d'équipe.

Le détail des rôles est dans [04-identity-access.md](04-identity-access.md).

### 3.4 Phrases interdites

```hcl
# banned_phrases = ["nom de code projet confidentiel"]
```

- En commentaire, donc défaut `[]` : aucune phrase interdite.
- Pour l'activer : retirer le `#` et lister les expressions (par exemple des noms de code de projets confidentiels).
  Chaque élément devient un bloc `banned_phrases` de l'assistant (voir [08-app.md](08-app.md), bloc `dynamic`).

### 3.5 Les connecteurs

L'en-tête de la section :

```hcl
# -----------------------------------------------------------------------------
# CONNECTEURS - une entrée par source. La clé (ex. "gdrive") devient l'ID de collection.
# Les secrets sont créés AVANT par l'équipe sécurité dans Secret Manager ;
# ici on ne met que le NOM du secret.
#   gcloud secrets create sharepoint-client-secret --replication-policy=user-managed --locations=europe-west1
#   printf '%s' 'VALEUR' | gcloud secrets versions add sharepoint-client-secret --data-file=-
# Les noms exacts de paramètres d'une source sont à confirmer dans la page du connecteur
# (docs.cloud.google.com/gemini/enterprise/docs/connectors/...) : marqués [à confirmer].
# -----------------------------------------------------------------------------
```

**Le principe.** `connectors` est une **map** : chaque **clé** (`gdrive`, `sharepoint`…) est un connecteur, et sa
**valeur** est un objet qui le décrit. [`40_connectors.tf`](../40_connectors.tf) crée **un connecteur par entrée**
grâce à `for_each` (voir [07-connectors.md](07-connectors.md)). La clé devient l'**ID de collection** chez Google :
choisissez-la courte, en minuscules, et **ne la changez plus** (la changer = supprimer et recréer le connecteur).

**Les champs possibles** (déclarés dans `variables.tf`) :

| Champ | Obligatoire ? | Défaut | Rôle |
|---|---|---|---|
| `data_source` | oui | | Le type de source Google (`google_drive`, `sharepoint`, `github`…). |
| `display_name` | oui | | Le nom affiché. |
| `modes` | non | `["FEDERATED"]` | `FEDERATED` = interrogation en direct, sans copie ; `DATA_INGESTION` = copie indexée chez Google. |
| `params` | non | `{}` | Paramètres **non secrets** (URL, ID de tenant…). |
| `secret_params` | non | `{}` | Paramètres **secrets** : « nom du paramètre → **nom** du secret dans Secret Manager ». |
| `entities` | non | `[]` | Les types d'objets à interroger (fichiers, tickets…), chacun avec un `name`. |
| `refresh_interval` | non | `"86400s"` | Fréquence de synchronisation (1 jour). Utile surtout en ingestion. |
| `static_ip` | non | `false` | Appeler la source depuis des IP fixes. **Immuable.** |

**Les secrets, par leur NOM.** Le principe central de la sécurité des connecteurs (guide du socle (docs/00) §6.2) :
1. **Avant** Terraform, l'équipe sécurité crée chaque secret et sa valeur avec `gcloud` :
   - `gcloud secrets create sharepoint-client-secret --replication-policy=user-managed --locations=europe-west1` :
     crée le secret (une « boîte » vide), stocké **uniquement** en `europe-west1` (UE) ;
   - `printf '%s' 'VALEUR' | gcloud secrets versions add sharepoint-client-secret --data-file=-` : met la valeur
     dedans. `printf '%s'` évite d'ajouter un retour à la ligne parasite ; `--data-file=-` lit la valeur depuis
     l'entrée standard, ce qui évite de la voir apparaître dans les arguments de la commande.
2. Dans `terraform.tfvars`, on écrit seulement le **nom** : `client_secret = "sharepoint-client-secret"`.
3. Terraform lit le secret par son nom, donne au compte de Gemini Enterprise le droit de le lire
   ([`20_data_protection.tf`](../20_data_protection.tf)), puis passe au connecteur une **référence** de la forme
   `projects/<numéro>/secrets/sharepoint-client-secret/versions/latest`. Gemini Enterprise lit la valeur au moment de
   l'appel. La valeur ne passe **jamais** par le code, ni par l'état Terraform.

**Le marqueur `[à confirmer]`** : un nom de paramètre ou de source pris dans la documentation Google, mais pas encore
vérifié sur un vrai déploiement (guide du socle (docs/00) §16). Au premier `apply`, si Google refuse le paramètre, lire la page du
connecteur (lien dans le commentaire) ou créer le connecteur une fois dans la console et comparer.

Voyons maintenant chaque entrée.

#### `gdrive` et `gcalendar` : Google Workspace

```hcl
connectors = {
  # Google Workspace : application OAuth gérée par Google, aucun paramètre.
  gdrive = {
    data_source  = "google_drive"
    display_name = "Google Drive"
  }
  gcalendar = {
    data_source  = "google_calendar"
    display_name = "Google Agenda"
  }
```

- Seuls les deux champs obligatoires. Tout le reste prend son défaut : mode fédéré, pas de secret (l'application
  OAuth est **gérée par Google**), pas d'IP fixe.
- Fédéré = chacun ne voit que les fichiers et événements auxquels il a déjà accès dans Drive / Agenda.

#### `gmail` : désactivé

```hcl
  # gmail = { data_source = "google_mail", display_name = "Gmail" }   # sur décision explicite (minimisation)
```

- En commentaire **volontairement** : la messagerie contient beaucoup de données personnelles. À activer seulement
  sur décision explicite (principe de minimisation, guide du socle (docs/00) §7.3).
- Exemple d'écriture **sur une seule ligne** : entre accolades, les champs sont alors **séparés par des virgules**.
  Sur plusieurs lignes, pas de virgule.

#### `sharepoint` : Microsoft 365

```hcl
  # Microsoft 365 : application Entra ID (mono-tenant, consentement admin).
  # Avec l'identité Google, les sources Microsoft sont en FEDERATED (l'ingestion exigerait Entra ID).
  sharepoint = {
    data_source  = "sharepoint" # [à confirmer] la doc montre aussi "sharepoint_federated_search"
    display_name = "SharePoint"
    params = {
      instance_uri = "https://acme.sharepoint.com"
      tenant_id    = "00000000-0000-0000-0000-000000000000"
    }
    secret_params = {
      client_id     = "sharepoint-client-id"
      client_secret = "sharepoint-client-secret"
    }
    entities  = [{ name = "file" }]
    static_ip = true
  }
```

- **Entra ID** (ex-Azure AD) est l'annuaire de Microsoft. On y crée une **application** (mono-tenant, avec
  consentement administrateur) que Gemini Enterprise utilise pour interroger SharePoint.
- `data_source = "sharepoint"` : **[à confirmer]**, la doc mentionne aussi `"sharepoint_federated_search"`. Repli :
  essayer l'autre valeur (guide du socle (docs/00) §16).
- `params` (non secrets) :
  - `instance_uri` : l'adresse du SharePoint de l'entreprise ;
  - `tenant_id` : l'identifiant du tenant (de l'« instance ») Microsoft 365. Les zéros sont à **remplacer** par le
    vrai ID (visible dans le portail Entra).
- `secret_params` : l'**ID** et le **secret** de l'application Entra. On range aussi `client_id` dans Secret Manager,
  par prudence et pour tout gérer au même endroit. Les valeurs à droite sont des **noms de secrets**.
- `entities = [{ name = "file" }]` : interroger les **fichiers**. Une liste d'objets : on peut en ajouter d'autres.
- `static_ip = true` : IP fixes, à autoriser côté Microsoft (`terraform output connector_static_ips`,
  [11-outputs.md](11-outputs.md)).
- Pas de `modes` : défaut `["FEDERATED"]`. Le commentaire explique pourquoi : avec l'identité Google, l'ingestion
  des sources Microsoft exigerait Entra ID comme fournisseur d'identité.

#### `teams`

```hcl
  teams = {
    data_source  = "teams" # recherche fédérée uniquement
    display_name = "Microsoft Teams"
    params       = { tenant_id = "00000000-0000-0000-0000-000000000000" } # [à confirmer]
    secret_params = {
      client_id     = "teams-client-id"
      client_secret = "teams-client-secret"
    }
    static_ip = true
  }
```

- Teams n'existe qu'en mode **fédéré** chez Google.
- `params` : seulement le `tenant_id`, **[à confirmer]** (nom exact du paramètre à vérifier).
- Ses propres secrets (`teams-client-id`, `teams-client-secret`) : on peut utiliser une application Entra
  différente de SharePoint, avec ses propres droits minimaux.
- Pas d'`entities` : défaut `[]`.

#### `github`

```hcl
  # GitHub : une GitHub App (pas de jeton personnel), installée sur l'organisation.
  github = {
    data_source   = "github"
    display_name  = "GitHub"
    params        = { organization = "acme" } # [à confirmer]
    secret_params = { client_id = "github-client-id", client_secret = "github-client-secret" }
    static_ip     = true
  }
```

- Une **GitHub App** (pas un jeton personnel, qui serait lié à une personne et souvent trop puissant), installée
  sur l'organisation GitHub, avec les permissions minimales.
- `params = { organization = "acme" }` : l'organisation GitHub. Nom du paramètre **[à confirmer]**.
- `secret_params` écrit sur une ligne : deux noms de secrets, séparés par une virgule.

#### `jira` : un exemple d'ingestion (en commentaire)

```hcl
  # Jira : exemple d'ingestion (copie indexée, chiffrée CMEK, droits Jira synchronisés).
  # jira = {
  #   data_source  = "jira"
  #   display_name = "Jira"
  #   modes        = ["DATA_INGESTION"]
  #   params       = { instance_uri = "https://acme.atlassian.net", instance_id = "...", auth_type = "OAUTH" }
  #   secret_params = { client_id = "jira-client-id", client_secret = "jira-client-secret", refresh_token = "jira-refresh-token" }
  #   entities     = [{ name = "project" }, { name = "issue" }, { name = "comment" }]
  #   static_ip    = true
  # }
```

- Désactivé : c'est un **modèle** pour le cas où l'on choisit l'ingestion.
- `modes = ["DATA_INGESTION"]` : les données sont **copiées** chez Google. Elles sont alors chiffrées avec la clé
  CMEK de l'entreprise (automatique dans `40_connectors.tf` dès que le mode contient `DATA_INGESTION`).
- `params` : l'adresse Atlassian, l'ID de l'instance (à remplir) et le type d'authentification.
- `secret_params` : trois secrets, dont un `refresh_token` (jeton qui permet d'obtenir de nouveaux accès).
- `entities` : trois types d'objets (projets, tickets, commentaires) : en ingestion, il faut dire quoi copier.
- Pourquoi l'ingestion n'est pas le défaut : voir guide du socle (docs/00) §7.2.

#### Databricks

```hcl
  # Databricks : pas de connecteur natif. Voir le guide, section "Databricks".
}
```

- Il n'existe pas de `data_source` Databricks : les options (serveur MCP, agent dédié, publication vers BigQuery)
  sont décrites dans le guide du socle (docs/00) §7.4. L'accolade `}` ferme la map `connectors`.

### 3.5 bis Journalisation

```hcl
# -----------------------------------------------------------------------------
# JOURNALISATION (voir guide §10.4)
# -----------------------------------------------------------------------------
# log_prompts_responses       = false  # texte complet des questions/réponses : décision DPO/CSE
# security_log_retention_days = 365
# usage_log_retention_days    = 90
# lock_security_logs          = false  # true en production : rétention non modifiable (irréversible)
# link_logs_to_bigquery       = false  # true pour des tableaux de bord Looker Studio
```

Tout est **commenté** : les valeurs par défaut s'appliquent (le plus sobre). Pour activer un réglage, retirez le `#`
et changez la valeur. Chaque réglage est une **décision** à tracer (DPO pour les deux premiers, sécurité pour le
verrouillage). Explications : [13-logging.md](13-logging.md) et [02-variables.md](02-variables.md#38-section-8--journalisation-usage-et-sécurité).

### 3.6 Les variables absentes : leurs valeurs par défaut

Tout ce qui n'est pas dans le fichier prend la valeur de `variables.tf`. Les principales :

| Variable | Défaut | Effet |
|---|---|---|
| `region` | `"europe-west1"` | Région des ressources régionales (Agent Gateway). |
| `app_id` / `app_display_name` / `company_name` | `"assistant-ia"` / `"Assistant IA"` / `"Acme"` | Identité de l'app. |
| `enable_cmek` | `true` | Chiffrement avec les clés de l'entreprise. |
| `session_ttl_days` | `30` | Conservation des conversations (à valider avec le DPO). |
| `armor_confidence` | `"MEDIUM_AND_ABOVE"` | Sévérité des filtres Model Armor. |
| `sdp_mode` | `"advanced"` | Détecteurs de données sensibles français / UE. |
| `log_screened_content` | `false` | Pas de contenu filtré dans les journaux. |
| `web_grounding` | `"WEB_GROUNDING_TYPE_DISABLED"` | Pas de recherche web. |
| `features` | 4 réglages (partages désactivés, feedback activé) | Voir [08-app.md](08-app.md). |
| `enable_observability` | `true` | Traces sans contenu. |
| `enable_agent_gateway` / `vpc_sc_access_policy` | `false` / `""` | Options avancées désactivées ([09-advanced.md](09-advanced.md)). |

Pour en changer une, ajoutez simplement la ligne dans `terraform.tfvars`, par exemple `session_ttl_days = 15`.

---

## 4. Ce que Terraform crée concrètement

Ce fichier ne crée rien lui-même : il **paramètre** les autres. Avec ces valeurs, les points marquants :
- **5 connecteurs** (`gdrive`, `gcalendar`, `sharepoint`, `teams`, `github`), tous en mode fédéré, dont 3 avec IP
  fixes ;
- **6 secrets** référencés (2 par source tierce) ; ils doivent **déjà exister** dans Secret Manager ;
- des droits pour **4 groupes** ;
- un **canal d'alerte** vers `securite-ia@acme.example` ;
- tout le reste selon les défauts (CMEK activé, conservation 30 jours, pas de web, options avancées désactivées).

---

## 5. Dépendances avec les autres fichiers

| Valeur | Déclarée dans | Utilisée dans | Fiche |
|---|---|---|---|
| Toutes | [`variables.tf`](../variables.tf) (types, défauts, validations) | | [02-variables.md](02-variables.md) |
| Groupes | | [`10_identity_access.tf`](../10_identity_access.tf) | [04-identity-access.md](04-identity-access.md) |
| Noms des secrets | | [`20_data_protection.tf`](../20_data_protection.tf), [`40_connectors.tf`](../40_connectors.tf) | [05-data-protection.md](05-data-protection.md) |
| `connectors` | | [`40_connectors.tf`](../40_connectors.tf), [`outputs.tf`](../outputs.tf) | [07-connectors.md](07-connectors.md), [11-outputs.md](11-outputs.md) |
| `banned_phrases` | | [`50_app.tf`](../50_app.tf) | [08-app.md](08-app.md) |
| `alert_email` | | [`70_detection.tf`](../70_detection.tf) | [10-detection.md](10-detection.md) |

---

## 6. Pour reproduire / adapter

**Besoin type : ajouter un nouveau connecteur.**

```hcl
connectors = {
  # ... connecteurs existants ...

  confluence = {                                   # clé = ID de collection : courte, stable, minuscules
    data_source   = "confluence"                   # type de source (page du connecteur dans la doc Google)
    display_name  = "Confluence"
    # modes       = ["FEDERATED"]                  # défaut ; "DATA_INGESTION" seulement sur décision justifiée
    params        = { instance_uri = "https://monentreprise.atlassian.net" }   # NON secret [à confirmer]
    secret_params = {                              # paramètre => NOM du secret (jamais la valeur)
      client_id     = "confluence-client-id"
      client_secret = "confluence-client-secret"
    }
    # entities    = [{ name = "page" }]            # si la source en exige [à confirmer]
    static_ip     = true                           # IMMUABLE : décider dès la création
  }
}
```

1. **Côté source** : créer l'application OAuth (Entra ID, GitHub App, Atlassian…) avec les **permissions minimales**
   en lecture et l'URL de redirection `https://vertexaisearch.cloud.google.com/oauth-redirect` (guide du socle (docs/00) §7.6).
2. **Équipe sécurité** : créer les secrets en UE, **avant** Terraform :
   ```bash
   gcloud secrets create confluence-client-secret --replication-policy=user-managed --locations=europe-west1
   printf '%s' 'VALEUR' | gcloud secrets versions add confluence-client-secret --data-file=-
   ```
3. **Code** : ajouter l'entrée dans `terraform.tfvars` ; reporter le format (sans valeurs réelles) dans
   `terraform.tfvars.example` pour documenter. Noms des paramètres : page du connecteur
   (docs.cloud.google.com/gemini/enterprise/docs/connectors/…) et doc Terraform
   https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/discovery_engine_data_connector
4. `terraform plan` : vérifier qu'il n'y a qu'un connecteur **ajouté** (`+`), et lire si l'app est recréée (voir §7).
5. Après `apply` : autoriser les IP (`terraform output connector_static_ips`) côté source, faire l'autorisation
   OAuth initiale dans la console, vérifier `terraform output connector_states`.
6. **Recette** : un utilisateur sans droit sur un document de test ne doit pas le voir dans l'assistant.

---

## 7. Pièges et bonnes pratiques

- **Ne jamais committer `terraform.tfvars`** (ni `terraform.tfstate`). Ajoutez-les à un `.gitignore`.
- **Jamais de valeur secrète dans ce fichier** : seulement des **noms** de secrets. Une valeur ici finirait dans Git,
  dans l'état et dans les journaux de CI.
- **Les secrets doivent exister avant `plan`** : Terraform les lit par leur nom ; un secret absent fait échouer le
  `plan` (« secret not found »). Vérifiez l'orthographe exacte.
- **Clé de connecteur = immuable en pratique** : la renommer supprime et recrée le connecteur (et ses data stores).
- **`static_ip` et `ge_location` sont immuables** : les décider dès la création.
- **Ajouter un connecteur modifie `data_store_ids` de l'app**, ce qui peut **recréer l'app** (bug connu du provider,
  guide du socle (docs/00) §16). Lisez le `plan` ; idéalement, déclarez tous les connecteurs avant l'ouverture aux utilisateurs.
- **`[à confirmer]`** = à vérifier au premier déploiement. Retirez le marqueur une fois le nom validé, pour que la
  prochaine personne sache que c'est sûr.
- **Les ID de tenant `00000000-…` sont des exemples** : les laisser ferait échouer le connecteur.
- **Préfixe `group:` obligatoire** dans les listes de groupes : sans lui, Google refuse le membre IAM.
- **Plusieurs environnements** (recette, production) : un fichier par environnement (`recette.tfvars`,
  `prod.tfvars`) passé avec `-var-file=…`, et un état séparé pour chacun.
