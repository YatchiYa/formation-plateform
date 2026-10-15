# 10-5. Chemin 1 : le connecteur natif « Custom MCP Server » de Gemini Enterprise

**Ce guide répond à :** comment brancher le serveur MCP **directement** sur l'app Gemini Enterprise ? Cela passe par
le client OAuth, les règles de l'organisation, le data store « Custom MCP Server », les actions, le premier
« Autoriser » et les droits. Le résultat : les 17 outils deviennent des **actions** de l'assistant, sans agent à
écrire.

> **Pas encore suivi en vrai :** la facturation des projets de test est fermée, et ils n'ont plus d'app.
> - Les écrans et les champs viennent de la [documentation Google](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server)
>   (consultée le 13 octobre 2026).
> - L'appel que fait l'app au serveur (deux en-têtes) est **reproduit** par `deployer.sh tester` ([10-8](10-8-tester-simuler-verifier.md)).
> - Le serveur a été testé en vrai sur la vraie API Sheets ([10-1](10-1-serveur-mcp-comprendre-et-tester-en-local.md)).

---

> **Pour le faire de bout en bout sans sauter d'étape** (déploiement compris) : [10-12](10-12-pas-a-pas-mcp-dans-assistant-principal.md).
> Ce guide-ci explique chaque réglage en détail.

> **Google Slides :** même procédure, un 2e connecteur ; ce qui change : [10-13, partie 5](10-13-serveur-mcp-google-slides.md#5-le-brancher-sur-lassistant-principal-connecteur).

## Ce que l'utilisateur verra

1. Dans l'assistant : « Liste mes classeurs Ventes ».
2. La 1re fois : un bouton **Autoriser** → la fenêtre Google (compte @acme.example, portées en clair) → **Autoriser**.
3. Les actions de lecture s'exécutent directement. Avant une action qui modifie, l'assistant **demande
   confirmation**.

## Les rôles nécessaires

| Qui | Rôle | Pour |
|---|---|---|
| Vous, dans le projet **des agents** | ceux de [10-2](10-2-deployer-shell.md#0-avant-de-commencer) | Client OAuth, serveur, droits |
| Admin de l'**organisation** (ou du projet de l'app) | `roles/orgpolicy.policyAdmin` | Étape 2 : règles d'organisation |
| Admin de l'**app** | `roles/discoveryengine.editor` (ou admin) | Étapes 4 à 6 : data store, actions, app |

---

## Étape 1 : le client OAuth (console, projet des agents)

Le **client OAuth** est la « carte d'identité » de l'application auprès de Google. Son nom s'affiche dans la fenêtre
de consentement. **Le même client** sert au connecteur (chemin 1) et à l'agent (chemin 2).

Pourquoi dans le projet **des agents** :
- l'API Sheets y est déjà active ;
- les quotas y sont comptés ;
- la prod de l'app ne change pas.

Les autres choix possibles : projet 09, guide 12-1-8, partie 13.

1. Projet `aiml-gemini-ent-exp-0zga` → 🔎 **Google Auth Platform**. S'il n'est pas configuré :
   - **Get started** (*Commencer*) → nom `Gemini Enterprise - Google Sheets` → e-mail d'assistance d'équipe ;
   - **Audience** : **Internal** (*Interne*) : seuls les comptes Acme pourront se connecter, sans validation
     Google ;
   - **Create**.
2. **Branding** (*Image de marque*) : logo, domaine autorisé `acme.example`.
3. **Data access** (*Accès aux données*) → **Add or remove scopes** → ajoutez :
   - `openid`
   - `https://www.googleapis.com/auth/userinfo.email`
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/drive.metadata.readonly`

   → **Update** → **Save**.
4. **Clients** → **+ Create client** → **Web application** → nom `gemini-enterprise-sheets-mcp`.
   **Authorized redirect URIs**, les deux :
   ```
   https://vertexaisearch.cloud.google.com/oauth-redirect
   https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
   ```
   - La 1re sert au connecteur.
   - La 2de sert à l'autorisation de l'agent (chemin 2).

   → **Create**.
5. Notez :
   - **Client ID** (`…apps.googleusercontent.com`) : mettez-le dans `OAUTH_CLIENT_IDS` de `config/10-mcp.env`,
     rechargez la configuration, puis `./scripts/deployer.sh mcp`. Le serveur n'accepte que les jetons émis pour ce
     client ;
   - **Client secret** : pour la console de l'app (étape 4) seulement. Jamais dans un fichier du dépôt, ni dans
     Terraform.

> **Pourquoi pas un compte de service avec délégation à l'échelle du domaine (DWD) ?** Le serveur pourrait alors lire
> **n'importe quel** classeur de l'entreprise. Avec OAuth par utilisateur, il n'a aucun pouvoir propre.

## Étape 2 : les règles de l'organisation (admin)

Par défaut, Gemini Enterprise **bloque** les connecteurs MCP personnalisés. Dans le **projet de l'app** :
🔎 **IAM & Admin → Organization Policies** :

| Règle (nom affiché) | Réglage |
|---|---|
| **Disable custom MCP server connector for Gemini Enterprise** (`constraints/gcp.disableCustomMcpServer` selon un guide tiers : filtrez par le nom) | **Manage policy** → **Override parent's policy** → **Add rule** → Enforcement **Off** → **Set policy**. Attendu : « Not enforced » |
| **Restrict egress domains for data connectors** (`discoveryengine.managed.allowedEgressFqdns`) | Ajouter les 3 domaines **sans** `https://` : `sheets-mcp-433175138344.europe-west1.run.app`, `accounts.google.com`, `oauth2.googleapis.com` |
| **Restrict allowed data sources for data connectors** (`discoveryengine.managed.allowedDataSources`) | Si la règle est appliquée sur le projet (ou si VPC Service Controls est actif) : ajouter `custom_mcp` |

Faites ces changements **sur le projet de l'app**, pas sur toute l'organisation. Comptez 5 à 10 minutes de propagation.

La liste des domaines est aussi dans `./scripts/deployer.sh fiche` et dans la sortie Terraform
`domaines_de_sortie_a_autoriser`.

## Étape 3 : le droit d'appel du compte de l'app (projet des agents)

Le connecteur appelle le serveur avec un jeton d'identité du compte de l'app, dans l'en-tête
`X-Serverless-Authorization`. Ce compte a besoin de `roles/run.invoker` sur `sheets-mcp`.

- **Script :** `NUM_APP=523307489860 ./scripts/deployer.sh droits-app` (plan, puis confirmation).
- **Console :** Cloud Run → `sheets-mcp` → **Security** → **Add principal** →
  `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` → **Cloud Run Invoker** → **Save**.

**Voir ce droit, et tous les autres, en lecture seule ; les donner clic par clic :** [10-11](10-11-droits-voir-et-donner-console.md).

> Le jeton d'identité n'est envoyé que pour une URL `*.run.app` par défaut, pas pour un domaine personnalisé
> (documentation Google). Gardez l'URL `run.app`.

## Étape 4 : le data store « Custom MCP Server » (console de l'app)

**L'écran, tel qu'il est dans la console Gemini Enterprise de Acme** (captures du 14 octobre 2026) : projet de
l'app → 🔎 **Gemini Enterprise** → votre app → page des sources de données → section **« MCP servers »**.

Cette section affiche deux choses :
- *« MCP servers from your project's configured Agent Gateway registries, or a custom … »*, avec le bandeau
  « Configure Agent Gateway to discover and use MCP servers from your … » (voir [10-7, partie 4 bis](10-7-agent-registry-mcp.md#4-bis-la-découverte-par-agent-gateway-vue-dans-la-console-acme)) ;
- la carte **Custom MCP Server** (« Connect your own Model Context Protocol (MCP) server to use custom tools »). Cliquez
  sur **Add MCP server**.

Autre accès, selon la version de la console : **Data stores** → **Create data store** → cherchez **Custom MCP
Server**.

Écran **MCP Server Configuration**, partie **1. Authentication settings** :

| Champ (tel qu'affiché) | Ce que vous mettez | Remarque |
|---|---|---|
| Select your authentication method | **OAuth 2.0** | « No authentication » : jamais pour ce serveur (il exige le jeton de l'utilisateur) |
| **MCP Server URL** * | `https://sheets-mcp-433175138344.europe-west1.run.app/mcp` | L'aide dit « base URL (e.g. https://mcp.example.com) », mais notre serveur répond sur **`/mcp`** : mettez l'URL **avec** `/mcp` (la doc Google dit « typically ending in /mcp ») |
| **Authorization URL** * | `https://accounts.google.com/o/oauth2/v2/auth` | **Sans** paramètres : l'app ajoute `client_id`, `redirect_uri`, `scope` |
| **Authorization URL Parameters** | `&access_type=offline&prompt=consent&hd=acme.example` | Format demandé par l'écran : **commence par `&`** |
| **Token URL** * | `https://oauth2.googleapis.com/token` | |
| **Client ID** * | l'ID du client OAuth de l'étape 1 | Doit être dans `OAUTH_CLIENT_IDS` du serveur |
| **Client Secret** | le secret de l'étape 1 | Jamais dans un fichier |
| **Scopes** | `openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly` | Séparées par des espaces |
| **Enable PKCE Support** | **Cocher** (décoché par défaut) | Google prend en charge PKCE : protection en plus |
| **Use HTTP Basic Authentication** | **Laisser coché** (coché par défaut) | Google accepte l'ID et le secret dans l'en-tête (Basic) comme dans le corps : les deux marchent |

→ **Verify Auth** : une fenêtre Google s'ouvre. Connectez-vous avec votre compte @acme.example et acceptez. Puis
**Continue**.

Partie **2. Advanced options** : rien à changer. C'est là que se règle l'envoi des appels par **Agent Gateway**,
facultatif. → **Continue**.

**Configure your data connector :**
- Multi-region `eu` (celle de l'app) ;
- nom `Google Sheets` ;
- **Create**.

Attendez que l'état passe de **Creating** à **Active**.

Pourquoi ces paramètres :
- `access_type=offline` + `prompt=consent` : Google donne un **jeton de rafraîchissement**. L'app renouvelle seule le
  jeton : l'utilisateur ne se reconnecte pas toutes les heures ;
- `hd=acme.example` : le sélecteur propose directement le compte professionnel. C'est un **confort**, pas une
  barrière : la barrière est le contrôle de domaine du serveur ;
- **PKCE** : protège l'échange du code d'autorisation.

Tous ces champs sont aussi affichés par `./scripts/deployer.sh fiche`, avec vos valeurs.

## Étape 5 : les actions

Le data store → **Actions** → **Reload custom actions**. L'app appelle `tools/list` : les **17 outils** apparaissent,
tous **désactivés**. Cochez puis **Enable actions**. Il y a 100 actions au maximum.

Ordre conseillé :
1. **Lecture** (sans confirmation, grâce à `readOnlyHint`) : `whoami`, `search_spreadsheets`, `get_spreadsheet_info`,
   `read_range`, `read_ranges`, `find_in_sheet` ;
2. **Écriture sans perte** : `append_rows`, `create_spreadsheet`, `add_sheet`, `rename_sheet`, `insert_dimension`,
   `format_range` ;
3. **Destructif**, une fois les usages observés : `write_range`, `clear_range`, `delete_sheet`, `delete_dimension`,
   `batch_update`.

Par défaut, l'app demande une confirmation avant **chaque** action, sauf celles marquées en lecture seule.

## Étape 6 : brancher le data store sur l'app

L'app → **Connected data stores** (*Data stores connectés*) → **Add** → `Google Sheets` → **Save**.

Le connecteur ne peut pas être rattaché après coup à un data store existant : créez-le **depuis** l'app que vous
visez (documentation Google).

## Étape 7 : le premier usage

| Demande dans l'assistant | Attendu |
|---|---|
| « Pour Google Sheets, qui suis-je ? » | 1re fois : **Autoriser** → consentement → votre e-mail @acme.example |
| « Trouve mes classeurs Ventes » | La liste, avec les liens |
| « Résume l'onglet Ventes du classeur … » | Le contenu, résumé |
| Un classeur **non partagé** avec vous (ID connu) | « accès refusé » : vos droits Drive s'appliquent |
| « Ajoute la ligne Sac à dos, 39 dans Ventes » | Demande de confirmation, puis la ligne est ajoutée |
| « Efface la colonne C » | Demande de confirmation (destructif) |
| Un compte d'un autre domaine | Connexion impossible (consentement interne) ; le serveur refuse aussi |

## Si ça bloque

| Symptôme | Cause → solution |
|---|---|
| « Custom MCP Server » absent ou refusé à la création | Étape 2 : règle « Disable custom MCP server connector » pas désactivée sur ce projet |
| **Verify Auth** : `redirect_uri_mismatch` | Étape 1 : `https://vertexaisearch.cloud.google.com/oauth-redirect` absent du client |
| « Impossible de se connecter au serveur » | `run.invoker` manquant pour le compte de l'app (étape 3) ; URL sans `/mcp` ; domaine `*.run.app` absent des domaines de sortie (étape 2) |
| Toutes les actions renvoient une erreur d'authentification (401) | L'ID du client de l'étape 1 n'est pas dans `OAUTH_CLIENT_IDS` : corriger, recharger, `./scripts/deployer.sh mcp` |
| Refus pour un utilisateur légitime | Domaine absent de `ALLOWED_DOMAINS`. Le journal Cloud Run dit `auth_rejected`, avec la raison |
| `search_spreadsheets` : accès refusé | Portée `drive.metadata.readonly` absente : l'ajouter (client **et** data store), puis se reconnecter |
| Reconnexion toutes les heures | `access_type=offline&prompt=consent` absent des paramètres |
| Formules en erreur (`#ERROR!`) | La locale du classeur : `;` et `,` en fr_FR ([10-1, partie 6](10-1-serveur-mcp-comprendre-et-tester-en-local.md#6-le-piège-des-formules--la-locale-du-classeur)) |

**Sources :**
- [Set up a custom MCP server](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server)
- [Override the organization policy for Custom MCP data stores](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/override-constraint-for-custom-mcp-data-stores)
- [Allowed egress FQDNs](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/configure-allowed-egress-fqdns)
- [Allowed data sources](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/configure-allowed-data-sources)
- [Managed policy constraints](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/managed-policy-constraints-overview)
