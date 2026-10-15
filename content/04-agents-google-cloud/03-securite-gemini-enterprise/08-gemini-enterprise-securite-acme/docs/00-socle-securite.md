# Gemini Enterprise : socle de sécurité (hérité du projet 06)

> Ce document décrit le socle (couches 1 à 6). Les mesures ajoutées pour la note de sécurité Acme sont dans le [README du projet 08](../README.md).

**Pour qui :** équipes sécurité, architecture cloud et data de Acme.
**Objectif :** déployer Gemini Enterprise (l'assistant IA des collaborateurs, connecté aux outils de l'entreprise)
avec un **socle de sécurité complet, expliqué et reproductible**. Pour chaque mesure, le guide dit **ce qu'elle
fait**, **pourquoi**, **comment** elle est configurée (code commenté) et **ce qu'elle apporte**.

> Le guide est volontairement pédagogique : on peut le lire sans connaître Terraform ni Google Cloud.
> Le code est dans [`terraform/`](../terraform/). Chaque fichier correspond à une couche décrite ici.
> **Vous débutez en Terraform ?** Chaque fichier `.tf` a sa fiche explicative ligne par ligne dans
> [`terraform/docs/`](../terraform/docs/00-bases-terraform.md), en commençant par le cours de base.

---

## Sommaire

1. [En une page](#1-en-une-page)
2. [Les notions à connaître](#2-les-notions-à-connaître)
3. [Architecture](#3-architecture)
4. [Les risques que l'on traite](#4-les-risques-que-lon-traite)
5. [Couche 1 : identité et accès](#5-couche-1--identité-et-accès)
6. [Couche 2 : protection des données (CMEK, secrets, conservation)](#6-couche-2--protection-des-données)
7. [Couche 3 : connecteurs (Google, Microsoft, GitHub, Databricks…)](#7-couche-3--connecteurs)
8. [Couche 4 : filtrage IA avec Model Armor](#8-couche-4--filtrage-ia-avec-model-armor)
9. [Couche 5 : exposition et fonctionnalités](#9-couche-5--exposition-et-fonctionnalités)
10. [Couche 6 : audit et détection](#10-couche-6--audit-et-détection)
11. [Options avancées : Agent Gateway, VPC Service Controls](#11-options-avancées)
12. [Déploiement pas à pas](#12-déploiement-pas-à-pas)
13. [Recette : prouver que la sécurité fonctionne](#13-recette)
14. [Exploitation au quotidien](#14-exploitation-au-quotidien)
15. [Compromis assumés](#15-compromis-assumés)
16. [Vérifié / à valider en recette](#16-vérifié--à-valider-en-recette)
17. [Dépannage](#17-dépannage)
18. [Sources](#18-sources)

---

## 1. En une page

Gemini Enterprise permet à chaque collaborateur de poser une question en langage naturel
(« quelles sont les ventes running du T3 ? », « résume la note du comité produit ») et d'obtenir une réponse
**construite à partir des outils de l'entreprise** : Google Drive, SharePoint, Teams, GitHub, Jira, BigQuery…

Le risque est proportionnel à cette puissance : **un assistant qui voit tout peut tout divulguer**.
Le socle répond avec **6 couches**, toutes écrites en Terraform :

| Couche | En une phrase | Bénéfice pour Acme |
|---|---|---|
| **1. Identité et accès** | Connexion avec le compte d'entreprise ; accès par groupes ; la sécurité seule touche aux garde-fous | Un départ coupe l'accès immédiatement ; pas de « super-admin » qui peut tout désactiver |
| **2. Protection des données** | Données chiffrées avec **les clés de Acme** (CMEK) ; secrets dans un coffre ; conversations conservées 30 jours | Maîtrise du chiffrement (révocable à tout moment) ; aucun mot de passe dans le code ; minimisation RGPD |
| **3. Connecteurs** | Par défaut **fédérés** : l'assistant interroge la source en direct, **avec les droits de l'utilisateur** | Chacun ne voit que ce qu'il voit déjà ; aucune copie des données chez Google |
| **4. Filtrage IA** | **Model Armor** analyse chaque question et chaque réponse : injection, contenus dangereux, liens malveillants, **NIR, IBAN, carte bancaire, secrets** | Protection contre la manipulation de l'IA et contre les fuites de données personnelles |
| **5. Exposition** | Données en **UE** ; pas de recherche web publique ; partages contrôlés | Conformité RGPD et contrats ; pas de fuite involontaire vers Internet |
| **6. Audit et détection** | Journaux d'audit et d'usage rangés en UE, lisibles par la sécurité seule ; **alertes** (garde-fou modifié, pic de blocages) | Preuves pour l'audit ; détection des attaques sans exposer les questions des collaborateurs |

Le tout est **reproductible** (même code en recette et en production), **relu** (chaque changement passe par une
revue de code) et **traçable** (l'historique Git est une preuve d'audit).

---

## 2. Les notions à connaître

| Terme | Explication simple |
|---|---|
| **Gemini Enterprise** | L'application web d'assistant IA pour les collaborateurs (anciennement « Agentspace »). Techniquement : l'API *Discovery Engine*, d'où les ressources Terraform `google_discovery_engine_*` |
| **App (engine)** | Une instance de Gemini Enterprise : ses sources de données, son assistant, ses réglages |
| **Assistant** | Le « cerveau » conversationnel de l'app : instructions, langue, filtrage Model Armor |
| **Connecteur** | Le branchement entre l'app et un outil (Drive, SharePoint, GitHub…). Il crée un ou plusieurs **data stores** |
| **Mode fédéré** | L'assistant interroge l'outil **en direct**, avec le jeton de l'utilisateur. Rien n'est copié ; les droits de l'outil s'appliquent |
| **Mode ingestion** | Les données sont **copiées et indexées** chez Google (plus rapide, meilleure qualité). Les droits sont synchronisés pour les connecteurs tiers, **pas pour BigQuery** |
| **Service agent** | Un compte technique géré par Google qui agit pour un service dans le projet (ex. `service-<n°>@gcp-sa-discoveryengine…` pour Gemini Enterprise). On lui donne **uniquement** les droits nécessaires |
| **Cloud KMS / CMEK** | Le coffre de clés de chiffrement. CMEK (*Customer-Managed Encryption Keys*) : les données sont chiffrées avec **une clé dont Acme a le contrôle**. Désactiver la clé rend les données illisibles |
| **Secret Manager** | Le coffre à secrets (identifiants OAuth des connecteurs). Le code ne contient que le **nom** du secret, jamais sa valeur |
| **Model Armor** | Un « pare-feu » pour le texte échangé avec l'IA : il analyse questions et réponses et **bloque** ce qui est dangereux |
| **Template Model Armor** | Un jeu de filtres nommé (ex. `ge-prompt-shield`) appliqué quelque part |
| **Floor setting (plancher)** | Le **minimum** de sécurité du projet : aucun template ne peut être moins strict |
| **DLP / Sensitive Data Protection** | Le service de détection de données sensibles (NIR, IBAN…), utilisé par Model Armor |
| **Agent Registry** | Le catalogue des agents, serveurs MCP et API de l'entreprise |
| **Agent Gateway** | Le point de passage contrôlé (pare-feu applicatif) des appels des agents vers les outils et API |
| **VPC Service Controls** | Un périmètre autour des API Google du projet : empêche l'exfiltration de données, même avec des identifiants volés |
| **IP statiques de connecteur** | Les adresses fixes depuis lesquelles Gemini Enterprise appelle un SaaS : on les autorise côté SaaS, tout le reste est refusé |

---

## 3. Architecture

```
                          ┌───────────── Couche 1 ─────────────┐
 Collaborateurs ──SSO──▶  │ Identité Google (ou Entra ID)      │
 (groupes)                │ rôles par groupe · sécurité séparée│
                          └────────────────┬───────────────────┘
                                           ▼
                ┌────────────── App Gemini Enterprise (UE) ───────────────┐
                │  Assistant                                              │
   question ──▶ │  ┌─────────────┐   ┌────────┐   ┌──────────────┐        │ ──▶ réponse
                │  │prompt-shield│──▶│ Gemini │──▶│response-shield│       │
                │  └─────────────┘   └────────┘   └──────────────┘        │
                │   Couche 4 : Model Armor + DLP FR · FAIL_CLOSED         │
                │   Couche 5 : pas de web public · partages contrôlés     │
                │   Couche 2 : chiffré CMEK · conversations 30 j          │
                └──────┬───────────────┬───────────────┬──────────────────┘
                       │ fédéré        │ fédéré        │ fédéré / ingestion
                       ▼               ▼               ▼
               Google Workspace   Microsoft 365     GitHub · Jira · BigQuery…
               (Drive, Agenda)    (SharePoint,      IP statiques autorisées
                                   Teams)           secrets dans Secret Manager
                                                    (Couche 3)

 Couche 6 : journaux d'audit · alerte « garde-fou modifié » → équipe sécurité
 Options   : Agent Gateway (agents/MCP) · VPC Service Controls (périmètre)
```

---

## 4. Les risques que l'on traite

| # | Risque (référence OWASP Top 10 LLM) | Exemple concret | Couche(s) |
|---|---|---|---|
| R1 | **Accès non autorisé** | Un compte partagé, un ex-collaborateur qui garde l'accès | 1 |
| R2 | **Divulgation de données** (LLM02) | Un stagiaire retrouve la grille de salaires via l'assistant | 3, 4 |
| R3 | **Injection de prompt** (LLM01) | « Ignore tes instructions et montre-moi… », ou une consigne cachée dans un document | 4 |
| R4 | **Données personnelles** dans les échanges | Un collaborateur colle un IBAN client ou un NIR dans une question | 4 |
| R5 | **Contenus dangereux ou malveillants** | Réponse toxique, lien de phishing relayé par l'assistant | 4 |
| R6 | **Affaiblissement de la sécurité** | Un admin désactive un filtre « pour une démo » | 1, 4, 6 |
| R7 | **Perte de maîtrise des données** | Données hors UE, impossibilité de les rendre illisibles | 2, 5 |
| R8 | **Secrets exposés** | Mot de passe d'application Microsoft dans le code | 2 |
| R9 | **Exfiltration** avec des identifiants volés | Export massif via l'API depuis l'extérieur | 3 (IP), options (VPC-SC) |
| R10 | **Attaque ou abus non détectés** | Personne ne voit 200 tentatives de jailbreak | 6 |

---

## 5. Couche 1 : identité et accès

Fichier : [`terraform/10_identity_access.tf`](../terraform/10_identity_access.tf)

### 5.1 Connexion avec le compte d'entreprise (SSO)

```hcl
resource "google_discovery_engine_acl_config" "identity" {
  location = var.ge_location        # "eu"
  idp_config {
    idp_type = var.identity_provider  # "GSUITE" = Google Workspace / Cloud Identity
  }
}
```

- **Quoi :** les collaborateurs se connectent avec leur compte d'entreprise. Il n'y a ni mot de passe dédié ni compte
  local.
- **Pourquoi :** la double authentification, la durée de session et la **suspension d'un compte au départ** sont
  gérées une seule fois, dans l'annuaire. Un compte suspendu perd l'accès à l'assistant **immédiatement**.
- **Si Acme utilise Microsoft Entra ID comme annuaire principal :** `identity_provider = "THIRD_PARTY"` +
  `workforce_pool` (Workforce Identity Federation). **Attention, c'est un choix structurant :**
  - un seul fournisseur d'identité par localisation ;
  - l'identité Google est **obligatoire** pour les connecteurs Google Workspace ;
  - l'**ingestion** SharePoint/OneDrive/Outlook exige Entra ID ; en identité Google, les sources Microsoft
    fonctionnent en **mode fédéré** (c'est le défaut de ce socle) ;
  - changer d'identité plus tard **efface l'historique des conversations** et oblige à recréer les data stores.

### 5.2 Rôles attribués à des groupes

| Groupe | Rôle Google | Peut… | Ne peut pas… |
|---|---|---|---|
| `user_groups` | `roles/discoveryengine.agentspaceUser` | utiliser l'app | administrer |
| `admin_groups` | `roles/discoveryengine.agentspaceAdmin` | gérer l'app, les connecteurs, les agents | **modifier Model Armor, les clés, lire les journaux privés** |
| `viewer_groups` | `roles/discoveryengine.agentspaceViewer` | consulter la configuration et les statistiques | modifier |
| `security_groups` | `roles/modelarmor.admin`, `roles/cloudkms.admin`, `roles/logging.privateLogViewer` | gérer les filtres, les clés, lire les journaux sensibles | — |

- **Pourquoi des groupes :** les droits nominatifs ne sont jamais nettoyés. Avec des groupes, les arrivées et départs
  se gèrent dans l'annuaire, et une revue d'accès consiste à relire 4 groupes.
- **Pourquoi la séparation des rôles :** celui qui exploite l'outil ne doit pas pouvoir **désactiver sa propre
  sécurité**. Les admins Gemini Enterprise n'ont aucun droit `modelarmor.*` ni `cloudkms.*`. C'est le principe des
  « quatre yeux ».
- **Bénéfice :** moindre privilège démontrable, revue d'accès simple, risque R6 neutralisé.

> **Pour aller plus loin :** l'accès peut être donné **par app** plutôt que par projet
> (`google_discovery_engine_search_engine_iam_member`), avec un rôle projet minimal personnalisé. C'est utile si
> plusieurs apps cohabitent dans le projet (ex. une app RH réservée aux RH).

---

## 6. Couche 2 : protection des données

Fichier : [`terraform/20_data_protection.tf`](../terraform/20_data_protection.tf)

### 6.1 CMEK : chiffrement avec les clés de Acme

**Quoi :** tout ce que Gemini Enterprise **stocke** (index des connecteurs en ingestion, conversations, données de
l'app) est chiffré avec une clé Cloud KMS **appartenant au projet Acme**, et non avec une clé gérée par Google.

**Pourquoi :**
- **Contrôle :** Acme peut **désactiver la clé** à tout moment. En 15 minutes, l'app ne peut plus lire ni servir
  les données (« crypto-shredding »). C'est un interrupteur d'urgence en cas d'incident majeur ou de fin de contrat.
- **Conformité :** exigence fréquente des politiques de sécurité et des contrats pour les données sensibles.
- **Traçabilité :** chaque utilisation de la clé est visible dans Cloud KMS.

**Comment (et pourquoi chaque ligne) :**

```hcl
resource "google_kms_key_ring" "ge" {
  name     = "gemini-enterprise"
  location = local.kms_location   # "europe" : multi-région KMS qui correspond à l'app "eu"
}

resource "google_kms_crypto_key" "ge" {
  name     = "gemini-enterprise-data"
  key_ring = google_kms_key_ring.ge[0].id
  purpose  = "ENCRYPT_DECRYPT"
  # PAS de rotation_period : Gemini Enterprise exige une rotation MANUELLE.
  lifecycle { prevent_destroy = true }   # Terraform refuse de détruire la clé (voir plus bas)
}
```

| Règle Google | Comment le socle la respecte |
|---|---|
| CMEK uniquement pour les apps **`eu` ou `us`**, pas `global` | `ge_location` est validé : `eu` ou `us` seulement |
| Clé **multi-région** `europe` pour une app `eu` | `local.kms_location = "europe"` |
| Rotation **manuelle** | pas de `rotation_period` |
| Clés **régionales** `europe-west1`, `europe-west4`, `europe-north1` pour les connecteurs **tiers** en ingestion | `google_kms_crypto_key.regional` (3 clés) + `single_region_keys` |
| Le **service agent Gemini Enterprise** et le **service agent Cloud Storage** (bucket temporaire d'import) doivent pouvoir utiliser la clé | `google_kms_crypto_key_iam_member.key_users` : ces deux comptes seulement, rôle `cryptoKeyEncrypterDecrypter` |
| La clé doit être **enregistrée AVANT** de créer l'app et les connecteurs, sinon ils restent chiffrés par Google | `google_discovery_engine_cmek_config` + `depends_on` sur l'app et les connecteurs |

```hcl
resource "google_discovery_engine_cmek_config" "ge" {
  location       = "eu"
  cmek_config_id = "default-cmek"
  kms_key        = google_kms_crypto_key.ge[0].id
  set_default    = true                         # appliquée par défaut à tout ce qui sera créé
  dynamic "single_region_keys" { ... }          # les 3 clés régionales
}
```

**Pourquoi `prevent_destroy` :** détruire la clé rend **définitivement** illisibles toutes les données de l'app. Un
`terraform destroy` lancé par erreur ne doit jamais pouvoir le faire. Pour vraiment révoquer la clé, la procédure est
volontaire et documentée (§14.3).

**Ce que CMEK ne couvre pas :** en **mode fédéré**, rien n'est stocké chez Google, il n'y a donc rien à chiffrer
(c'est encore mieux). Les sources elles-mêmes (BigQuery, SharePoint…) ont leur propre chiffrement. Model Armor est
un service **sans stockage** (il analyse et oublie).

### 6.2 Secrets des connecteurs : jamais dans le code

```hcl
data "google_secret_manager_secret" "connector" { secret_id = "sharepoint-client-secret" }  # le NOM seulement

resource "google_secret_manager_secret_iam_member" "ge_reads" {
  secret_id = data.google_secret_manager_secret.connector[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.ge_sa          # Gemini Enterprise seulement, secret par secret
}
```

Dans le connecteur, le paramètre vaut `projects/<n°>/secrets/sharepoint-client-secret/versions/latest` : **une
référence**, que Gemini Enterprise résout au moment de l'appel.

- **Pourquoi :** un secret dans le code ou dans l'état Terraform finit tôt ou tard dans un dépôt Git, un log de CI ou
  une capture d'écran. Ici, **l'équipe sécurité crée les secrets** (valeurs), Terraform ne connaît que leur nom.
- **Rotation :** on ajoute une nouvelle version du secret ; `versions/latest` la prend automatiquement, sans
  redéploiement.
- **Bénéfice :** risque R8 neutralisé ; chaque lecture de secret est journalisée (audit Secret Manager activé, §10).

### 6.3 Minimisation : conservation des conversations

```hcl
sessionConfig = { sessionTtl = { days = var.session_ttl_days } }   # 30 jours (Google : 60 par défaut)
```

- **Pourquoi :** principe de minimisation du RGPD. Les conversations contiennent souvent des informations internes ;
  on ne les garde pas plus que nécessaire. La durée est **à valider avec le DPO** de Acme.
- **Comment :** ce réglage n'existe pas encore dans le provider Terraform. Il est appliqué par un appel à l'API
  (`terraform_data.engine_settings` dans `50_app.tf`), relancé automatiquement si la valeur change.

---

## 7. Couche 3 : connecteurs

Fichier : [`terraform/40_connectors.tf`](../terraform/40_connectors.tf). Configuration dans `terraform.tfvars`.

### 7.1 Le principe : un modèle générique

Toutes les sources se déclarent de la même façon. On ajoute une entrée dans `connectors`, puis `terraform apply` :

```hcl
connectors = {
  sharepoint = {
    data_source   = "sharepoint"                 # le type de source
    display_name  = "SharePoint"
    modes         = ["FEDERATED"]                # défaut : pas de copie
    params        = { instance_uri = "https://acme.sharepoint.com", tenant_id = "..." }
    secret_params = { client_id = "sharepoint-client-id", client_secret = "sharepoint-client-secret" }  # NOMS de secrets
    entities      = [{ name = "file" }]
    static_ip     = true                         # IP sortantes fixes
  }
}
```

Terraform transforme chaque entrée en `google_discovery_engine_data_connector`, résout les secrets, rattache les data
stores créés à l'app, et applique la clé CMEK si la source est en ingestion.

### 7.2 Fédéré ou ingestion : la décision de sécurité la plus importante

| | **Fédéré** (défaut du socle) | **Ingestion** |
|---|---|---|
| Où sont les données ? | **Restent dans la source** ; interrogées en direct | **Copiées** et indexées chez Google (UE, CMEK) |
| Droits d'accès | Ceux de la source, **avec le jeton de l'utilisateur** | Synchronisés (connecteurs tiers) ; **perdus pour BigQuery** |
| Qualité / vitesse | Bonne ; moins bonne sur les PDF complexes | Meilleure (index, recherche sémantique) |
| Usage recommandé | Workspace, Microsoft 365, GitHub, données sensibles | Bases documentaires volumineuses à faibles enjeux de confidentialité |

**Pourquoi « fédéré » par défaut :** c'est la seule façon de garantir **par construction** que chacun ne voit que ce
qu'il voit déjà, et qu'aucune copie n'existe hors de la source. On passe une source en ingestion **au cas par cas**,
de façon justifiée.

> ⚠️ En mode fédéré, la question (éventuellement reformulée par l'IA) est envoyée à l'éditeur de la source
> (Microsoft, GitHub…). Elle relève alors des conditions de cet éditeur.

### 7.3 Les sources de Acme

| Source | `data_source` | Mode | Authentification | Points de sécurité |
|---|---|---|---|---|
| Google Drive / Agenda | `google_drive`, `google_calendar` | Fédéré | Application OAuth **gérée par Google**, aucun secret | Droits Drive natifs. Si les applications OAuth sont restreintes, un super-admin Workspace doit marquer l'app Google comme *Trusted* |
| Gmail | `google_mail` | Fédéré | idem | **Désactivé par défaut** (minimisation) : à activer sur décision explicite |
| SharePoint / OneDrive | `sharepoint`, `onedrive` | Fédéré | Application **Entra ID** mono-tenant, consentement admin, secret dans Secret Manager | Droits **délégués** en lecture (`Sites.Search.All`, `AllSites.Read` ou mieux `Sites.Selected`) |
| Outlook | `outlook` | Fédéré | Entra ID | Droits délégués `Mail.Read`, `Calendars.Read` |
| Teams | `teams` | **Fédéré uniquement** | Entra ID | Droits délégués de lecture des canaux/chats |
| GitHub | `github` | Fédéré (+ actions optionnelles) | **GitHub App** (pas de jeton personnel), installée sur l'organisation | Permissions minimales de l'app ; « expire user tokens » activé |
| Jira / Confluence | `jira`, `confluence` | Fédéré ou ingestion | OAuth Atlassian | IP statiques recommandées |
| BigQuery | `bigquery` (ingestion) / `bigquery_mcp` (fédéré, preview) | voir ci-dessous | Service agent | **En ingestion, les droits BigQuery sont perdus** : n'indexer qu'un dataset curé |
| Autres | `servicenow`, `salesforce`, `slack`, `snowflake`, `box`, `notion`, `workday`… | selon la source | OAuth, secrets | Même modèle |

**BigQuery :** en ingestion, **tout utilisateur de l'app voit toutes les lignes indexées**. Règle du socle : n'indexer
qu'un **dataset dédié et curé** (aucune donnée personnelle), ou préférer le mode fédéré `bigquery_mcp` (preview),
qui conserve les droits et la sécurité ligne à ligne de BigQuery.

### 7.4 Databricks

**Il n'existe pas de connecteur Databricks natif** dans Gemini Enterprise (octobre 2026). Trois options, par ordre de
préférence sécurité :

| Option | Principe | Sécurité |
|---|---|---|
| **A. Serveur MCP Databricks** (data store « Custom MCP Server ») | Gemini Enterprise appelle le serveur MCP managé de Databricks (Unity Catalog, Genie) en OAuth | Les droits **Unity Catalog** s'appliquent ; configuration console ; exige d'autoriser `custom_mcp` et le domaine Databricks dans les politiques d'organisation |
| **B. Agent dédié** (ADK/A2A sur Agent Runtime) enregistré dans Gemini Enterprise | Un agent interroge Databricks avec son identité propre | Contrôle fin ; **à filtrer lui-même avec Model Armor** (Gemini Enterprise ne filtre pas les agents personnalisés) ; idéalement derrière **Agent Gateway** |
| **C. Publication vers BigQuery** | Un pipeline publie un jeu de données curé dans BigQuery | Simple ; mêmes règles que BigQuery ingestion |

### 7.5 IP statiques : n'autoriser que Gemini Enterprise côté SaaS

`static_ip = true` : Gemini Enterprise appelle la source depuis **des adresses IP fixes**. Côté SaaS (Microsoft,
GitHub, Atlassian…), on autorise ces IP uniquement.

- **Récupérer les IP :** `terraform output connector_static_ips`.
- **Tant qu'elles ne sont pas autorisées,** `terraform output connector_states` affiche `ALLOWLIST_STATIC_IP` et la
  synchronisation attend.
- ⚠️ **Immuable :** on ne peut pas l'activer après coup sans recréer le connecteur. Le socle l'active d'emblée pour
  les sources tierces.

### 7.6 Ajouter une source (procédure)

1. **Côté source :** créer l'application OAuth (Entra ID, GitHub App, Atlassian…) avec les **permissions minimales**
   en lecture et l'URL de redirection `https://vertexaisearch.cloud.google.com/oauth-redirect`.
2. **Sécurité :** créer les secrets dans Secret Manager (UE) :
   ```bash
   gcloud secrets create github-client-secret --replication-policy=user-managed --locations=europe-west1
   printf '%s' 'VALEUR' | gcloud secrets versions add github-client-secret --data-file=-
   ```
3. **Code :** ajouter l'entrée dans `connectors` (noms de paramètres : page du connecteur dans la doc Google), puis
   ouvrir une PR.
4. **Après `apply` :** autoriser les IP statiques côté source, puis faire l'autorisation OAuth initiale (console).
5. **Recette :** un utilisateur sans droit sur un document de test ne doit pas le voir dans l'assistant.

---

## 8. Couche 4 : filtrage IA avec Model Armor

Fichier : [`terraform/30_ai_guardrails.tf`](../terraform/30_ai_guardrails.tf)

### 8.1 Le principe

```
question ──▶ [ge-prompt-shield] ──▶ Gemini ──▶ [ge-response-shield] ──▶ réponse
                 bloque si :                       bloque si :
                 injection, jailbreak,             contenu dangereux, lien malveillant,
                 lien malveillant, données          données sensibles (y compris tirées
                 sensibles, contenu dangereux       des documents de l'entreprise)
```

- **Pourquoi deux filtres :** filtrer seulement les questions laisse passer une réponse qui **recopierait** un IBAN
  trouvé dans un document. Filtrer seulement les réponses laisse passer les tentatives de manipulation.
- **Pourquoi un service séparé du modèle :** les instructions système (« ne révèle jamais… ») se contournent. Model
  Armor est un classifieur **indépendant**, qu'on ne peut pas « convaincre ».
- **Ce qui est filtré :** l'assistant, les agents créés par les utilisateurs (Agent Designer), les agents Google,
  ainsi que les **documents et images importés** (un fichier non conforme est écarté).
- ⚠️ **Ce qui ne l'est pas :** les **agents personnalisés** (ADK, A2A, Dialogflow). S'il y en a, ils doivent se
  filtrer eux-mêmes ; c'est aussi le rôle d'Agent Gateway (§11).

### 8.2 Les templates, filtre par filtre

```hcl
resource "google_model_armor_template" "shield" {
  for_each    = toset(["ge-prompt-shield", "ge-response-shield"])
  location    = "eu"                       # app "eu" => templates "eu" (règle Google)
  template_id = each.value
```

| Filtre (code) | Ce qu'il détecte | Réglage | Pourquoi ce réglage |
|---|---|---|---|
| `pi_and_jailbreak_filter_settings` | Injection de prompt (« ignore tes instructions »), jailbreak (contourner les règles de sécurité), y compris **cachés dans un document** | `ENABLED`, `MEDIUM_AND_ABOVE` | Risque n°1 des applications LLM (OWASP LLM01) |
| `malicious_uri_filter_settings` | Liens de phishing ou de malware connus (256 premières URL) | `ENABLED` | L'assistant ne doit jamais relayer un lien piégé avec la crédibilité de l'entreprise |
| `rai_settings` | Haine, harcèlement, sexuellement explicite, dangereux (la pédopornographie est toujours bloquée par Google) | 4 catégories, `MEDIUM_AND_ABOVE` | Responsabilité de l'employeur sur ce que son outil produit |
| `sdp_settings.advanced_config` | **Données sensibles françaises et secrets** (tableau 8.3) | template DLP `ge-donnees-sensibles-fr` | Le mode `basic` de Google est **orienté États-Unis** (n° de sécurité sociale US…) : il ne détecte ni le NIR ni l'IBAN |

**Seuils de confiance :**

| Seuil | Comportement | Usage |
|---|---|---|
| `HIGH` | Ne bloque que les cas quasi certains | Plancher minimal (§8.6) |
| **`MEDIUM_AND_ABOVE`** | **Équilibre** : bloque les attaques, laisse passer les questions normales | **Templates du socle** |
| `LOW_AND_ABOVE` | Bloque au moindre doute, avec beaucoup de faux positifs | Contextes très sensibles |

> **Pourquoi pas `LOW_AND_ABOVE` partout ?** Un outil qui bloque à tort pousse les collaborateurs vers des IA grand
> public **non maîtrisées**. C'est un risque plus grand que celui qu'on voulait couvrir.

### 8.3 Les données sensibles détectées (France / UE)

```hcl
resource "google_data_loss_prevention_inspect_template" "fr" {
  template_id = "ge-donnees-sensibles-fr"
  inspect_config {
    min_likelihood = "LIKELY"          # évite de bloquer n'importe quelle suite de chiffres
    info_types { name = "FRANCE_NIR" } # ... un bloc par type, depuis var.sensitive_info_types
  }
}
```

| Type | Donnée | Pourquoi la bloquer |
|---|---|---|
| `FRANCE_NIR` | N° de sécurité sociale | Donnée très encadrée (CNIL) ; aucune raison de la donner à l'assistant |
| `FRANCE_CNI`, `FRANCE_PASSPORT` | Pièces d'identité | Usurpation d'identité |
| `FRANCE_TAX_IDENTIFICATION_NUMBER` | N° fiscal | Donnée personnelle sensible |
| `IBAN_CODE`, `CREDIT_CARD_NUMBER` | Données bancaires | Fraude ; périmètre PCI-DSS pour les cartes |
| `GCP_CREDENTIALS`, `GCP_API_KEY`, `AUTH_TOKEN`, `AWS_CREDENTIALS`, `ENCRYPTION_KEY` | Secrets techniques | Un secret collé dans un chat est un secret compromis |

**Volontairement non bloqués :** e-mails, numéros de téléphone, noms. Ils sont omniprésents dans le travail normal
(« envoie un mail à … »). Les bloquer rendrait l'outil inutilisable. Ils restent protégés par les droits d'accès
(couches 1 et 3). La liste est une variable (`sensitive_info_types`), modifiable par l'équipe sécurité.

> Avec Gemini Enterprise, une donnée sensible détectée **bloque** l'échange : le masquage n'est pas proposé.

### 8.4 Métadonnées du template : comportement et journalisation

```hcl
template_metadata {
  enforcement_type        = "INSPECT_AND_BLOCK"        # on bloque (pas seulement on observe)
  log_template_operations = true                       # QUI modifie un filtre : toujours tracé
  log_sanitize_operations = var.log_screened_content   # le CONTENU filtré : false par défaut
  multi_language_detection { enable_multi_language_detection = true }   # français testé par Google
}
```

**Pourquoi ne pas journaliser le contenu (`log_screened_content = false`) :** Google le **déconseille** pour
Gemini Enterprise. Les journaux contiendraient les questions des collaborateurs, lisibles par toute personne ayant
`logging.privateLogViewer`. C'est un compromis :

| | `false` (défaut) | `true` |
|---|---|---|
| Vie privée des collaborateurs | ✅ préservée | ⚠️ questions dans les journaux (accès restreint à l'équipe sécurité) |
| Détection d'un pic d'attaques | ✅ via les **journaux d'usage** (`CUSTOMER_POLICY_VIOLATION`, §10.4) | ✅ en plus : le texte exact qui a déclenché le filtre |

À trancher avec le **DPO** et le **CSE** si nécessaire (surveillance des salariés). On peut activer `true` en
période de lancement, puis revenir à `false`.

### 8.5 Rattachement à l'assistant : `FAIL_CLOSED`

```hcl
model_armor_config {
  user_prompt_template = google_model_armor_template.shield["ge-prompt-shield"].id
  response_template    = google_model_armor_template.shield["ge-response-shield"].id
  failure_mode         = "FAIL_CLOSED"
}
```

- **`FAIL_CLOSED` :** si Model Armor est indisponible, l'assistant **refuse** plutôt que répondre sans filtre.
  La sécurité passe avant la disponibilité.
- Gemini Enterprise est autorisé à appeler Model Armor : `roles/modelarmor.user` pour son service agent
  (`ge_uses_armor`).
- **En complément :** `banned_phrases` (noms de code de projets confidentiels) et une instruction système (« ne
  demande jamais de NIR ni de coordonnées bancaires »).

### 8.6 Le plancher (floor setting) : la sécurité qu'on ne peut pas affaiblir

```hcl
resource "google_model_armor_floorsetting" "project" {
  parent                           = "projects/${var.project_id}"
  location                         = "global"
  enable_floor_setting_enforcement = true     # tout template moins strict est REFUSÉ
  filter_config { pi_and_jailbreak (HIGH), malicious_uri, rai DANGEROUS (HIGH) }
}
```

- **Pourquoi :** même un administrateur Model Armor ne peut pas créer ni modifier un template **sous ce minimum**.
  La sécurité devient une **garantie mécanique**, pas une promesse.
- Le plancher est volontairement **moins strict** que les templates (`HIGH` contre `MEDIUM`) : il fixe le minimum
  absolu, les templates portent la politique effective.

---

## 9. Couche 5 : exposition et fonctionnalités

Fichier : [`terraform/50_app.tf`](../terraform/50_app.tf)

### 9.1 Données en Union européenne

L'app (`ge_location = "eu"`), les templates Model Armor (`eu`), les clés KMS (`europe`), les clés régionales et les
secrets sont en UE. Les traitements d'IA des API multi-régionales UE ont lieu dans l'UE. **Bénéfice :** conformité
RGPD et engagements contractuels.

### 9.2 Pas de recherche web publique

```hcl
web_grounding_type = "WEB_GROUNDING_TYPE_DISABLED"
```

- **Pourquoi :** avec la recherche Google activée, des fragments de questions (parfois confidentielles) partent vers
  un moteur public. De plus, **Google Search grounding est incompatible avec la résidence des données et CMEK**.
- **Si le métier en a besoin :** `WEB_GROUNDING_TYPE_ENTERPRISE_WEB_SEARCH`, l'option prévue pour les secteurs
  régulés (pas de journalisation des données client).

### 9.3 Fonctionnalités et partages

```hcl
features = {
  "disable-agent-sharing"                = "FEATURE_STATE_ON"   # agents maison : pas de partage au lancement
  "skill-sharing-without-admin-approval" = "FEATURE_STATE_OFF"  # partage de skills = validation admin
  "session-sharing"                      = "FEATURE_STATE_OFF"  # une conversation ne se partage pas
  "feedback"                             = "FEATURE_STATE_ON"   # retours 👍/👎 pour piloter la qualité
}
```

| Réglage | Pourquoi |
|---|---|
| Partage d'agents désactivé | Un agent créé par un collaborateur peut avoir des consignes ou un accès inadaptés. On ouvre le partage quand la **gouvernance** (qui valide, selon quels critères) est définie |
| Partage de skills validé par un admin | Même logique |
| Partage de conversations désactivé | Une conversation contient souvent des informations issues de documents auxquels le destinataire n'a pas accès |
| Feedback activé | Mesurer la qualité et repérer les réponses problématiques |

### 9.4 Observabilité sans contenu

`observabilityConfig = { observabilityEnabled = true, sensitiveLoggingEnabled = false }` : traces techniques
(performance, erreurs) et **journaux d'usage**, **sans** le texte complet des questions et réponses (variable
`log_prompts_responses`, `false` par défaut). Détail des journaux : §10.4.

---

## 10. Couche 6 : audit et détection

Fichier : [`terraform/70_detection.tf`](../terraform/70_detection.tf)

### 10.1 Journaux d'audit

| Service | Journaux activés | Ce qu'on y trouve |
|---|---|---|
| Gemini Enterprise | Data Access (lecture + écriture) | Qui a utilisé l'app, quelles opérations |
| Model Armor | Data Access | Appels de filtrage (sans contenu, sauf §8.4) |
| Secret Manager | Data Access | **Chaque lecture d'un secret** de connecteur |
| Cloud KMS | Admin Activity (toujours actif) | Création, désactivation, destruction de clés |

Cloud KMS « Data Access » n'est **pas** activé : chaque déchiffrement serait journalisé, soit des millions de lignes
sans valeur.

### 10.2 Alerte « garde-fou modifié »

Une alerte part vers l'équipe sécurité dès qu'un de ces éléments change :
- un **template** Model Armor ou le **plancher** ;
- une **clé KMS** (désactivation, destruction, changement de version) ;
- l'**assistant** ou la configuration d'identité de l'app ;
- un **droit IAM** sur le projet, une clé ou un secret.

- **Pourquoi :** c'est la détection du risque R6. Une modification légitime passe par une PR Terraform et
  l'alerte sert de confirmation. Une modification non prévue est un incident.
- **Sans impact vie privée :** l'alerte repose sur les journaux d'**administration**, qui ne contiennent aucun contenu
  utilisateur.

### 10.3 Procédure en cas d'alerte

1. **Identifier** : dans Logs Explorer, l'entrée d'audit (`protoPayload.authenticationInfo.principalEmail`,
   `methodName`).
2. **Qualifier** : changement prévu (PR Terraform correspondante) ou non ?
3. **Si non prévu** : rétablir avec `terraform apply` (l'état du code est la référence), retirer les droits du compte
   en cause, ouvrir un incident.
4. **Si une clé a été désactivée** : la réactiver dans les 30 jours, sinon les données sont **définitivement perdues**.

### 10.4 Les journaux disponibles : ce qu'on capture, où, combien de temps

Fichier : [`terraform/80_logging.tf`](../terraform/80_logging.tf) (fiche : [13-logging.md](../terraform/docs/13-logging.md))

| Famille | Nom du journal / filtre | Ce qu'il contient | Données personnelles ? | Activé par | Destination · rétention |
|---|---|---|---|---|---|
| **Audit – administration** | `cloudaudit.googleapis.com%2Factivity` | Qui a modifié quoi : app, assistant, connecteurs, filtres Model Armor, clés KMS, droits IAM | Identité des admins | Toujours actif (Google) | `ge-security` · 365 j (+ copie `_Required` 400 j) |
| **Audit – accès aux données** | `cloudaudit.googleapis.com%2Fdata_access` | Appels aux API Gemini Enterprise, Model Armor, lectures de secrets | Identité des utilisateurs | `google_project_iam_audit_config` (§10.1) | `ge-security` · 365 j |
| **Usage Gemini Enterprise** | `discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity` | Par interaction : **utilisateur**, recherche ou question, agents utilisés, sources consultées, **réponses bloquées** (`skipped_reasons`, dont `CUSTOMER_POLICY_VIOLATION` = Model Armor/politique), création d'agents, droits sur les agents, mises à jour de connecteurs, fichiers importés | **Oui** : Google indique que les données sensibles ne sont pas filtrées | Observabilité (`enable_observability = true`) | `ge-usage` · 90 j, **exclu** du bucket par défaut |
| **Prompts et réponses (texte complet)** | `discoveryengine.googleapis.com%2Fgen_ai.user.message`, `…%2Fgen_ai.choice` | Texte exact des questions, des réponses, raisons de fin | **Oui, intégralement** | `log_prompts_responses = true` (**désactivé** par défaut) | `ge-usage` · 90 j, exclu du bucket par défaut |
| **Décisions Model Armor (contenu)** | `jsonPayload.@type="…SanitizeOperationLogEntry"` | Texte filtré, filtre déclenché, confiance | **Oui** | `log_screened_content = true` (**désactivé**, recommandation Google) | `ge-security` · 365 j, exclu du bucket par défaut |
| **Traces techniques** | Cloud Trace | Latence, erreurs, étapes de traitement | Non (sans journalisation sensible) | Observabilité | Cloud Trace |
| **Statistiques d'usage** | Console *Gemini Enterprise → Analytics* | Utilisateurs actifs, requêtes, licences, agents, retours 👍/👎 | Agrégées | Toujours | Tableau de bord Google (+ export BigQuery possible par API) |

**Ce que le socle met en place, et pourquoi :**

- **Deux buckets dédiés en UE** (`ge-security`, `ge-usage`) plutôt que le bucket par défaut, pour **séparer** les
  usages (preuve d'audit ≠ suivi d'usage), **limiter l'accès** et **fixer une durée de conservation par finalité**.
- **Exclusion du bucket par défaut** (`google_logging_project_exclusion`) des journaux qui contiennent des questions,
  parce que le bucket `_Default` est lisible par beaucoup de rôles (`logging.viewer`, `owner`…). Les questions des
  collaborateurs ne doivent être lisibles que par l'équipe habilitée.
- **Accès par vue** (`roles/logging.viewAccessor` sur la vue `_AllLogs` de chaque bucket) pour `security_groups`
  uniquement.
- **Log Analytics** activé : on interroge les journaux **en SQL**, directement dans la console, sans les copier dans
  BigQuery. Option `link_logs_to_bigquery = true` : un dataset BigQuery **lié** (lecture seule, sans copie) pour
  des tableaux de bord Looker Studio.
- **Rétention par finalité** : sécurité 365 jours (preuve, enquête), usage 90 jours (minimisation). Valeurs à valider
  avec le DPO. `lock_security_logs = true` en production rend la rétention **non modifiable** (même par un admin),
  ce qui garantit l'intégrité des preuves. C'est irréversible.
- **Alerte sur les blocages sans journaliser le contenu filtré** : une métrique compte les entrées d'usage contenant
  `CUSTOMER_POLICY_VIOLATION`. On détecte donc un pic d'attaques **sans** activer `log_screened_content`.

> ⚖️ **RGPD et droit du travail :** journaliser l'usage d'un outil par les salariés est un **traitement de
> données personnelles**. Il faut une **finalité** (sécurité, pilotage), l'**information des collaborateurs**, la
> **consultation du CSE** si l'outil permet un contrôle de l'activité, l'inscription au **registre des
> traitements** et des **durées de conservation** proportionnées. Le socle est configuré au plus sobre :
> pas de texte complet, accès restreint, 90 jours. Toute extension se décide avec le DPO.

### 10.5 Exemples de requêtes

**Logs Explorer** (choisir le bucket : *Affiner la portée → Stockage → ge-usage*) :

```
-- Toutes les réponses bloquées par la politique (Model Armor, phrases interdites)
logName="projects/PROJECT_ID/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity"
"CUSTOMER_POLICY_VIOLATION"

-- Qui a modifié un filtre Model Armor ou une clé (bucket ge-security)
protoPayload.serviceName=("modelarmor.googleapis.com" OR "cloudkms.googleapis.com")
logName:"cloudaudit.googleapis.com%2Factivity"

-- Qui a lu un secret de connecteur
protoPayload.serviceName="secretmanager.googleapis.com" protoPayload.methodName=~"AccessSecretVersion"
```

**Log Analytics (SQL)**, *Logging → Log Analytics*, vue du bucket `ge-usage` :

```sql
-- Nombre de blocages par utilisateur sur 7 jours (enquête après une alerte)
SELECT
  JSON_VALUE(proto_payload.audit_log.authentication_info.principal_email) AS utilisateur,
  COUNT(*) AS blocages
FROM `PROJECT_ID.eu.ge-usage._AllLogs`
WHERE log_name LIKE '%gemini_enterprise_user_activity'
  AND SEARCH(TO_JSON_STRING(t), 'CUSTOMER_POLICY_VIOLATION')
  AND timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
GROUP BY utilisateur ORDER BY blocages DESC
```

> Les chemins exacts des champs (`authentication_info`, `skipped_reasons`…) sont **à confirmer** sur les premières
> entrées réelles. Ouvrez une entrée dans Logs Explorer et adaptez la requête. La recherche plein texte
> (`"CUSTOMER_POLICY_VIOLATION"` / `SEARCH`) fonctionne quelle que soit la structure.

---

## 11. Options avancées

Fichier : [`terraform/60_advanced.tf`](../terraform/60_advanced.tf). Elles sont désactivées par défaut et s'activent par
variable.

### 11.1 Agent Gateway (`enable_agent_gateway = true`)

**Quoi :** le **point de passage contrôlé** des appels sortants de Gemini Enterprise vers des agents, des serveurs MCP
et des API enregistrés dans **Agent Registry**. C'est un pare-feu applicatif pour les agents :
- **refus par défaut** : un appel n'est autorisé que si une règle IAM l'autorise explicitement ;
- **politiques** par outil (ex. « outils en lecture seule uniquement ») ;
- **Model Armor** possible sur les appels d'outils ;
- **traçabilité** de chaque appel agent → outil.

```hcl
resource "google_network_services_agent_gateway" "egress" {
  name     = "assistant-ia-egress"
  location = "europe-west1"                       # app "eu" => passerelle europe-west1
  google_managed { governed_access_path = "AGENT_TO_ANYWHERE" }   # Gemini Enterprise : sortie uniquement
  registries = ["//agentregistry.googleapis.com/projects/<projet>/locations/global"]
}
```

Le rattachement à l'app (`agentGatewaySetting`) est fait par l'appel API de `engine_settings`.

**Pourquoi optionnel :** sans agent personnalisé ni outil MCP, il n'y a **rien à gouverner** et la passerelle
n'apporte presque rien. **Elle devient indispensable dès que Acme ajoute** un agent Databricks (§7.4 option B),
un serveur MCP interne ou des actions vers des API métier. Ce sont justement les flux que le Model Armor de
Gemini Enterprise ne filtre pas.

**Après activation :** importer explicitement les agents, MCP et API autorisés (jusqu'à 15 min pour que les
politiques s'appliquent).

### 11.2 VPC Service Controls (`vpc_sc_access_policy = "<id>"`)

**Quoi :** un **périmètre** autour des API du projet (Gemini Enterprise, Model Armor, DLP, KMS, Secret Manager). Même
avec des identifiants volés, on ne peut pas extraire de données depuis l'extérieur du périmètre.

**Comment le socle le déploie :** en **dry-run** (`use_explicit_dry_run_spec = true`). Rien n'est bloqué ; les
violations sont **journalisées**. On analyse pendant 2 à 4 semaines, puis on passe en mode actif.

**Impacts à préparer avant le mode actif :**
- l'**interface web** est bloquée sauf règles d'entrée (*access level* : plages IP Acme, appareils gérés…) ;
- la création de nouveaux data stores exige de déclarer les sources et domaines autorisés dans les politiques
  d'organisation (« sources autorisées » et « domaines de sortie autorisés » des connecteurs) ;
- **appliquer un périmètre sur un projet qui a déjà des data stores n'est pas supporté** : idéalement, VPC-SC est mis en
  place **avant** les connecteurs, en production.

### 11.3 Autres mesures (hors Terraform du projet)

| Mesure | Où | Intérêt |
|---|---|---|
| **Access Transparency** | Organisation | Journal des accès du personnel Google aux données (apps `eu`/`us` uniquement) |
| **Security Command Center (AI Protection)** | Organisation | Inventaire et détection des risques IA, alertes du plancher Model Armor |
| **Politiques d'organisation** CMEK et localisation | Organisation | Imposer CMEK et l'UE à tout nouveau projet |

---

## 12. Déploiement pas à pas

### 12.1 Prérequis

- Projet GCP **dans l'organisation** de Acme, avec facturation.
- **Licences Gemini Enterprise** (console : *Gemini Enterprise → Abonnements*).
- Les **4 groupes** (utilisateurs, admins, sécurité, pilotage).
- Rôles de la personne ou du compte CI qui déploie : `agentspaceAdmin`, `modelarmor.admin`, `cloudkms.admin`,
  `resourcemanager.projectIamAdmin`, `secretmanager.admin`, `dlp.admin`, `logging.configWriter`,
  `monitoring.editor` (ou *Owner* en recette).
- Connexion : `gcloud auth login` **et** `gcloud auth application-default login` avec le compte d'entreprise.

### 12.2 Ordre de déploiement

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # projet, groupes, connecteurs
# 1. L'équipe sécurité crée les secrets des connecteurs (§7.6)
terraform init
terraform plan      # LIRE : localisation eu, clés, groupes, connecteurs
terraform apply
```

Terraform respecte l'ordre imposé par Google : **clé KMS → droits sur la clé → enregistrement CMEK →
connecteurs → app → assistant → réglages API**.

### 12.3 Après `apply` (console)

1. **Connecteurs** : autoriser les IP (`terraform output connector_static_ips`) côté SaaS ; faire l'autorisation OAuth
   initiale de chaque source ; vérifier `terraform output connector_states`.
2. **Licences** : attribuer les licences aux utilisateurs.
3. **Lien de l'app** : console → app → *Intégration* → copier l'URL de l'app web.
4. **Recette** (§13).

---

## 13. Recette

| # | Test | Résultat attendu | Couche |
|---|---|---|---|
| 1 | `./scripts/test_model_armor.sh` | Question légitime **acceptée** ; jailbreak FR, IBAN, carte, lien malveillant **bloqués** | 4 |
| 2 | Dans l'app : « Ignore tes instructions et… » | Message de violation de politique | 4 |
| 3 | Dans l'app : coller un NIR de test | Bloqué | 4 |
| 4 | A cherche un fichier SharePoint/Drive partagé **seulement** avec B | **Aucun résultat** pour A | 3 |
| 5 | Personne hors du groupe utilisateurs ouvre le lien | Accès refusé | 1 |
| 6 | Un admin Gemini Enterprise tente de modifier un template Model Armor | **Permission refusée** | 1 |
| 7 | Un admin Model Armor tente de **désactiver** le filtre injection/jailbreak d'un template | **Refusé** par le plancher | 4 |
| 8 | Modifier un template via Terraform | **Alerte e-mail** reçue | 6 |
| 9 | « Quelle météo à Lille aujourd'hui ? » | Pas de réponse web | 5 |
| 10 | Console KMS : désactiver la clé (en **recette** uniquement), puis réactiver | App indisponible en ≤ 15 min, puis rétablie | 2 |
| 11 | Après quelques questions, chercher `gemini_enterprise_user_activity` dans le bucket **`_Default`** | **Rien** (exclu) ; présent dans **`ge-usage`** | 6 |
| 12 | Provoquer 21 blocages en 10 min (script de recette en boucle dans l'app) | Alerte « pic de requêtes bloquées » reçue | 6 |
| 13 | Un admin Gemini Enterprise (hors sécurité) ouvre le bucket `ge-usage` | **Accès refusé** | 6 |

---

## 14. Exploitation au quotidien

### 14.1 Tout changement passe par le code

PR → `terraform plan` relu → validation **par l'équipe sécurité** pour `30_ai_guardrails.tf` et
`20_data_protection.tf` → `apply` depuis la CI. L'alerte §10.2 confirme chaque changement.

### 14.2 Révoquer un collaborateur

Le retirer du groupe utilisateurs, ou suspendre son compte dans l'annuaire : effet immédiat. Pas de Terraform.

### 14.3 Révoquer les données (incident majeur, fin de contrat)

Désactiver la version de clé dans Cloud KMS (équipe sécurité). Les données deviennent illisibles en 15 min.
Réversible pendant **30 jours**, **définitif** au-delà.

### 14.4 Rotation de clé

Créer une nouvelle version et la rendre primaire. Gemini Enterprise rechiffre automatiquement. **Garder l'ancienne
version active au moins 30 jours.** Ne pas faire tourner les clés **régionales** des connecteurs tiers (règle Google).

### 14.5 Rotation d'un secret de connecteur

`gcloud secrets versions add <secret> --data-file=-`. La référence `versions/latest` prend la nouvelle valeur. Puis
désactiver l'ancienne version.

---

## 15. Compromis assumés

| Choix | Ce qu'on gagne | Ce qu'on accepte |
|---|---|---|
| `MEDIUM_AND_ABOVE` | Peu de faux positifs, adoption | Une attaque très subtile peut passer (le plancher et la détection restent) |
| `FAIL_CLOSED` | Jamais de réponse non filtrée | Indisponibilité pendant une panne de Model Armor |
| Pas de journalisation du contenu | Vie privée, conformité | Pas d'alerte automatique sur pic d'attaques |
| Fédéré par défaut | Droits natifs, pas de copie | Qualité un peu moindre sur les PDF complexes |
| E-mails et téléphones non bloqués | Outil utilisable | Protégés par les droits d'accès, pas par le filtre |
| Partage d'agents désactivé | Pas d'agent non revu diffusé | Moins de collaboration au lancement |
| `prevent_destroy` sur les clés | Aucune destruction accidentelle | `terraform destroy` complet impossible sans retirer la protection (voulu) |

---

## 16. Vérifié / à valider en recette

Ce socle est **validé syntaxiquement** (`terraform validate`, provider `hashicorp/google` 8.4) et s'appuie sur la
documentation Google d'octobre 2026. Il **n'a pas encore été déployé** sur un projet réel. Points à confirmer au
premier déploiement :

| Point | Pourquoi l'incertitude | Repli |
|---|---|---|
| Localisation du template DLP (`dlp_location = "europe"`) avec un template Model Armor `eu` | Non précisé par Google | `dlp_location = "global"`, ou `sdp_mode = "basic"` (temporaire) |
| Noms exacts des paramètres de certains connecteurs (Teams, GitHub, BigQuery ingestion) | Doc surtout « console » | Lire la page du connecteur ; créer une fois en console et comparer |
| `sharepoint` ou `sharepoint_federated_search` pour SharePoint fédéré | Les deux apparaissent dans la doc | Essayer `sharepoint`, sinon l'autre |
| Data stores des connecteurs Workspace sans « entities » | Sortie non documentée | Ajouter les IDs dans `extra_data_store_ids` |
| Compte qui lit les secrets (`secretAccessor`) | Supposé : service agent Gemini Enterprise | Vérifier l'erreur éventuelle et ajuster |
| Noms des méthodes dans l'alerte « garde-fou modifié » | Noms d'API à confirmer dans les journaux | Ajuster le filtre après le premier changement observé |
| Présence de `CUSTOMER_POLICY_VIOLATION` dans les journaux d'usage pour un blocage Model Armor | Champ `answer.skipped_reasons` documenté, valeur dans le journal à observer | Provoquer un blocage en recette et vérifier ; sinon activer `log_screened_content` en recette |
| Les exclusions de projet s'appliquent au bucket `_Default` | Comportement standard de Cloud Logging, à constater | Vérifier dans Logs Explorer que les questions n'apparaissent pas dans `_Default` |
| Modifier `data_store_ids` peut **recréer** l'app (bug connu du provider) | Issue GitHub du provider | Lire le `plan` ; ajouter les connecteurs avant le lancement |

---

## 17. Dépannage

| Symptôme | Cause probable → solution |
|---|---|
| `CMEK is not supported in global` | Utiliser `ge_location = "eu"` |
| Tout est bloqué juste après `apply` | Propagation IAM (1–2 min), ou `ge_uses_armor` manquant. Avec `FAIL_CLOSED`, une erreur de droit = un blocage (voulu) |
| Template refusé « less strict than floor » | Le plancher fonctionne : rendre le template plus strict |
| Connecteur en `ALLOWLIST_STATIC_IP` | Autoriser les IP de `connector_static_ips` côté SaaS |
| Connecteur Workspace refusé | Compte d'entreprise (pas Gmail) ; projet dans l'organisation ; app OAuth Google marquée *Trusted* par un super-admin |
| `Error: Instance cannot be destroyed` (clé KMS) | `prevent_destroy` : voulu. Voir §14.3 |
| Erreur sur le template DLP | §16, première ligne |

---

## 18. Sources

- [CMEK pour Gemini Enterprise](https://docs.cloud.google.com/gemini/enterprise/docs/cmek)
- [Model Armor et Gemini Enterprise](https://docs.cloud.google.com/model-armor/model-armor-gemini-enterprise-integration) · [Activer Model Armor](https://docs.cloud.google.com/gemini/enterprise/docs/enable-model-armor) · [Vue d'ensemble Model Armor](https://docs.cloud.google.com/model-armor/overview) · [Plancher](https://docs.cloud.google.com/model-armor/configure-floor-settings) · [Templates](https://docs.cloud.google.com/model-armor/manage-templates)
- [Fournisseur d'identité](https://docs.cloud.google.com/gemini/enterprise/docs/configure-identity-provider) · [Contrôle d'accès](https://docs.cloud.google.com/gemini/enterprise/docs/access-control)
- [Connecteurs tiers](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/connect-third-party-data-source) · [SharePoint](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/ms-sharepoint) · [GitHub](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/github/github-configuration) · [Google Drive](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/gdrive) · [BigQuery](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/connect-bigquery) · [Custom MCP](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server) · [IP statiques](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/configure-static-ip-egress)
- [Agent Gateway](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-overview) · [Agent Gateway + Gemini Enterprise](https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-ge-deploy)
- [VPC Service Controls](https://docs.cloud.google.com/gemini/enterprise/docs/use-vpc-service-controls) · [Contrôles de conformité](https://docs.cloud.google.com/gemini/enterprise/docs/compliance-security-controls) · [Journaux d'audit](https://docs.cloud.google.com/gemini/enterprise/docs/audit-logging)
- [Provider Terraform google](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
