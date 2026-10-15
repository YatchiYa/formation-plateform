# 10-12. Pas à pas : le MCP Google Sheets dans l'assistant principal de Gemini Enterprise

**Ce guide est fait pour être suivi du début à la fin, sans rien connaître à l'avance.** À la fin, n'importe quel
utilisateur Acme peut demander à l'**assistant principal** de Gemini Enterprise « lis mon classeur Ventes »,
« ajoute une ligne », « trie par prix ». L'assistant le fait avec **son compte à lui**, sur **ses** classeurs, après
un clic sur « Autoriser » la première fois.

C'est le **chemin 1** ([10-0](10-0-exploration-mcp-gemini-enterprise.md#2-les-4-chemins-vers-gemini-enterprise)) :
le serveur MCP est branché **directement** sur l'assistant, comme connecteur. Il n'y a **aucun agent** à écrire. Pour
passer par un agent (chemin 2), voir [10-6](10-6-agent-adk-mcp-gemini-enterprise.md). Les deux peuvent coexister,
avec le même serveur.

**Durée :** environ 1 heure, plus le temps des admins pour les étapes 9 et 10.

> **Ce qui a été vérifié en vrai** (14 octobre 2026, projets de test) :
> - les étapes 1 à 8 : serveur déployé ; les 17 outils sur un vrai classeur ; refus sans droit ; droits d'un projet à
>   l'autre ;
> - l'écran de l'étape 11 : vu sur **tes captures de la console Acme**.
>
> **Ce qui se vérifie la première fois chez Acme :** les étapes 9 à 14, qui demandent l'organisation et l'app.
> Chaque étape dit ce qu'on doit voir.

---

## Le plan, en une vue

| Étape | Quoi | Où | Qui | Coché ? |
|---|---|---|---|---|
| 0 | Les rôles nécessaires | – | vous | ☐ |
| 1 | Le dossier et l'environnement Python sur votre poste | terminal | vous | ☐ |
| 2 | La configuration | `config/10-mcp.env` | vous | ☐ |
| 3 | Vérifier, sans rien changer | terminal | vous | ☐ |
| 4 | Le client OAuth | console, projet **des agents** | vous | ☐ |
| 5 | Mettre l'ID client dans la configuration | `config/10-mcp.env` | vous | ☐ |
| 6 | Préparer le projet (API, comptes) | terminal | vous | ☐ |
| 7 | Déployer le serveur MCP | terminal | vous | ☐ |
| 8 | Le droit d'appel du compte de l'app | console, projet **des agents** | vous | ☐ |
| 9 | Les règles d'organisation | console, projet **de l'app** | **admin de l'organisation** | ☐ |
| 10 | (si demandé) Approuver l'ID client | Console d'administration Workspace | **admin Workspace** | ☐ |
| 11 | Le formulaire « Custom MCP Server » | console, **app** Gemini Enterprise | admin de l'app | ☐ |
| 12 | Activer les actions | console, app | admin de l'app | ☐ |
| 13 | Brancher le connecteur sur l'app | console, app | admin de l'app | ☐ |
| 14 | Le premier usage, et les tests | le chat | vous, puis tout le monde | ☐ |

Valeurs utilisées (Acme) :

| Nom | Valeur |
|---|---|
| Projet des agents | `aiml-gemini-ent-exp-0zga` (numéro `433175138344`) |
| Projet de l'app | `acme-gemini-prod` (numéro `523307489860`) |
| Région | `europe-west1` (app en `eu`) |
| Compte de l'app (Gemini Enterprise) | `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` |
| Adresse du serveur MCP (après l'étape 7) | `https://sheets-mcp-433175138344.europe-west1.run.app/mcp` |

---

## Étape 0 : les rôles nécessaires

| Qui | Rôle | Sur | Pour |
|---|---|---|---|
| Vous | Owner ; ou Service Usage Admin, Service Account Admin, Service Account User, Project IAM Admin, Cloud Build Editor, Artifact Registry Admin, Cloud Run Admin | projet des agents | Étapes 4 à 8 |
| Admin de l'organisation | Organization Policy Administrator | projet de l'app | Étape 9 |
| Admin de l'app | Discovery Engine Admin (ou Editor) | projet de l'app | Étapes 11 à 13 |

L'étape 3 vérifie vos droits pour vous.

## Étape 1 : le dossier et l'environnement Python

Copiez le dossier `10-mcp-google-sheets-gemini-enterprise` sur votre poste. Ensuite, dans un terminal :
```bash
cd 10-mcp-google-sheets-gemini-enterprise
gcloud auth login                                   # votre compte @acme.example
python3 -m venv .venv && source .venv/bin/activate  # Python 3.12, 3.13 ou 3.14
pip install -r mcp_server/requirements.txt          # fastmcp, uvicorn, httpx (pas de watchdog : marche sur le Mac Acme)
```
**Attendu :** `Successfully installed fastmcp-4.1.0 …`.

**Si `pip install` échoue :** voir le réseau d'entreprise et le proxy au projet 09, guide 12-1-1, partie 2.

## Étape 2 : la configuration

Ouvrez `config/10-mcp.env`. Vérifiez ces lignes : elles sont déjà remplies pour Acme.
```
PROJET=aiml-gemini-ent-exp-0zga
NUM_PROJET=433175138344
REGION=europe-west1
ALLOWED_DOMAINS=acme.example
```
Laissez `OAUTH_CLIENT_IDS` vide pour l'instant : vous le remplirez à l'étape 5.

Chargez la configuration. Les valeurs de l'app sont données devant la commande, le fichier n'est pas modifié :
```bash
PROJET_APP=acme-gemini-prod NUM_APP=523307489860 source scripts/config.sh config/10-mcp.env
```
**Attendu :**
```
== Configuration chargée : config/10-mcp.env
   Projet (MCP + agent)  : aiml-gemini-ent-exp-0zga (n° 433175138344), région europe-west1
   Serveur MCP           : https://sheets-mcp-433175138344.europe-west1.run.app/mcp
   …
   App Gemini Enterprise : acme-gemini-prod  (compte service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com)
   Clients OAuth acceptés: (AUCUN : le serveur MCP refusera de démarrer ; docs/10-5, étape 1)
```
**Dans chaque nouveau terminal**, rechargez la configuration avec cette même commande.

## Étape 3 : vérifier, sans rien changer

```bash
./scripts/deployer.sh verifier
```
**Attendu :**
- `Facturation … : active` ;
- une liste d'API (`inactive` est normal ici : l'étape 6 les active) ;
- vos droits, tous `OK`.

**Si une ligne dit `MANQUANT … -> demander roles/…`,** demandez ce rôle à l'administrateur du projet avant de
continuer. `Agent Runtime` et `Agent Registry` ne servent pas dans ce guide.

## Étape 4 : 
   - **Audience** : **Internal** (*Interne*). Seuls les comptes Acme pourront se connecter, et Google n'a rien
     à valider ;
   - **Contact information** : votre adresse ;
   - cochez l'accord → **Create**.
4. Menu de gauche → **Data access** (*Accès aux données*) → **Add or remove scopes**. Dans « Manually add scopes »,
   collez puis **Add to table** :
   ```
   openid
   https://www.googleapis.com/auth/userinfo.email
   https://www.googleapis.com/auth/spreadsheets
   https://www.googleapis.com/auth/drive.metadata.readonly
   ```
   → **Update** → **Save**.
5. Menu de gauche → **Clients** → **+ Create client** :
   - **Application type** : **Web application** ;
   - **Name** : `gemini-enterprise-sheets-mcp` ;
   - **Authorized redirect URIs** → **+ Add URI**, deux fois :
     ```
     https://vertexaisearch.cloud.google.com/oauth-redirect
     https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
     ```
   - **Create**.
6. Une fenêtre affiche le **Client ID** (`…apps.googleusercontent.com`) et le **Client secret**. **Copiez les deux**
   dans un endroit sûr, par exemple votre gestionnaire de mots de passe. Le secret ne doit aller **que** dans le
   formulaire de l'étape 11 : jamais dans un fichier, un e-mail ou un message.

**Si ça bloque :** « Internal » n'est pas proposé → le projet n'est pas dans l'organisation Acme (vérifiez le
projet sélectionné).

## Étape 5 : mettre l'ID client dans la configuration

Dans `config/10-mcp.env`, la ligne `OAUTH_CLIENT_IDS` :
```
OAUTH_CLIENT_IDS=123456789012-abcdefghijklmnop.apps.googleusercontent.com
```
Mettez **votre** Client ID (pas le secret), puis rechargez :
```bash
PROJET_APP=acme-gemini-prod NUM_APP=523307489860 source scripts/config.sh config/10-mcp.env
```
**Attendu :** `Clients OAuth acceptés: 123456789012-….apps.googleusercontent.com`.

**Pourquoi :** le serveur n'accepte que les jetons émis pour **ce** client. Un jeton d'une autre application est
refusé.

## Étape 6 : préparer le projet

```bash
./scripts/deployer.sh preparer
```
Le script :
- active les API (Cloud Run, Cloud Build, Sheets, Drive…) ;
- crée 3 comptes de service : celui qui construit les images, celui du serveur (**sans aucun rôle**), et celui de
  l'agent (qui ne sert pas dans ce guide) ;
- donne leurs rôles.

**Attendu**, à la fin : `Prêt. Attendez 1 à 2 minutes (droits des nouveaux comptes), puis : ./scripts/deployer.sh mcp`.

**Attendez 2 minutes.**

**Préférez les clics ?** [10-4, étapes 1 et 2](10-4-deployer-console.md#étape-1--les-api).

## Étape 7 : déployer le serveur MCP

```bash
./scripts/deployer.sh mcp
```
Le script fait construire l'image par **Cloud Build** (pas de Docker sur votre poste), puis crée le service Cloud Run
**privé** `sheets-mcp`.

**Attendu** (2 à 4 minutes), à la fin :
```
… SUCCESS
Service URL: https://sheets-mcp-433175138344.europe-west1.run.app
Serveur MCP : https://sheets-mcp-433175138344.europe-west1.run.app/mcp (privé : sans droit run.invoker, Cloud Run répond 403).
```

**Vérifiez qu'il est bien privé :**
```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST https://sheets-mcp-433175138344.europe-west1.run.app/mcp
```
**Attendu :** `403`. Personne ne peut l'appeler sans droit.

**Si ça bloque :**

| Message | Que faire |
|---|---|
| `OAUTH_CLIENT_IDS est vide` | Étape 5 |
| `PERMISSION_DENIED` pendant la construction | Le compte de construction est tout neuf : le script réessaie seul 3 fois. Sinon, relancez dans 2 minutes |
| `container failed to start` | Cloud Run → `sheets-mcp` → **Logs** : lisez la dernière erreur. C'est souvent `OAUTH_CLIENT_IDS` |

## Étape 8 : le droit d'appel du compte de l'app (console)

Gemini Enterprise appelle le serveur avec **son** compte. Il faut l'autoriser.

1. Console, projet **`aiml-gemini-ent-exp-0zga`** → 🔎 **Cloud Run** → cliquez sur **`sheets-mcp`**.
2. Onglet **Security** (*Sécurité*) → **Add principal** (*Ajouter un compte principal*). La fenêtre
   « *Grant access to "sheets-mcp"* » s'ouvre.
3. **New principals** : collez
   `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` (une seule ligne, sans espace).
4. **Select a role** : tapez `Cloud Run Invoker` → choisissez **Cloud Run Invoker** (*Demandeur Cloud Run*). Ni
   *Cloud Run Admin*, ni un rôle « ACM… ».
5. Pas de condition → **Save**.

**Attendu :** dans la liste, une rubrique **Cloud Run Invoker (1)** avec `service-100000000003@gcp-sa-discoveryengine…`.

**En une commande, si vous préférez :** `./scripts/deployer.sh droits-app` (il affiche le plan, puis demande de taper
l'ID du projet).

**Si l'enregistrement est refusé :**

| Message | Que faire |
|---|---|
| `… does not belong to a permitted customer` / `domain restricted sharing` | Une règle de l'organisation limite les comptes autorisés : demander à l'équipe Cloud Acme d'autoriser ce compte de service Google |
| `does not exist` | Gemini Enterprise n'est pas activé dans le projet de l'app, ou le numéro est faux |

Les autres droits, et comment les voir en lecture seule : [10-11](10-11-droits-voir-et-donner-console.md).

## Étape 9 : les règles d'organisation (admin de l'organisation)

Par défaut, Gemini Enterprise **bloque** les serveurs MCP personnalisés. **Message à envoyer** à l'admin de
l'organisation (copier-coller) :

> Bonjour,
> pour brancher notre serveur MCP Google Sheets sur l'app Gemini Enterprise, merci de régler, **sur le projet
> `acme-gemini-prod` uniquement** (pas sur toute l'organisation), dans IAM & Admin → Organization
> Policies :
> 1. **« Disable custom MCP server connector for Gemini Enterprise »** : Manage policy → Override parent's policy →
>    Add rule → Enforcement **Off** → Set policy (statut attendu : « Not enforced ») ;
> 2. **« Restrict egress domains for data connectors »** (`discoveryengine.managed.allowedEgressFqdns`) : autoriser
>    ces 3 domaines :
>    `sheets-mcp-433175138344.europe-west1.run.app`, `accounts.google.com`, `oauth2.googleapis.com` ;
> 3. **si** la règle « Restrict allowed data sources for data connectors » (`discoveryengine.managed.allowedDataSources`)
>    est appliquée sur ce projet : y ajouter `custom_mcp`.
>
> Merci !

**Attendu :** l'admin confirme. Comptez 5 à 10 minutes de propagation ensuite.

**Pour vérifier vous-même** (lecture seule) : projet de l'app → **Organization Policies** → filtrez « custom MCP » →
**Not enforced**.

## Étape 10 : (si demandé) approuver l'ID client (admin Workspace)

Si, à l'étape 11 ou 14, la fenêtre Google affiche « **Accès bloqué : votre administrateur …** », c'est que
Acme restreint l'accès des applications aux données Google. **Message à l'admin Google Workspace :**

> Bonjour, merci d'autoriser l'application OAuth interne **« Gemini Enterprise - Google Sheets »**, ID client
> `<votre Client ID>`, dans la Console d'administration → Sécurité → Contrôle des accès et des données → Contrôles des
> API → Accès des applications tierces. Portées demandées : Google Sheets, noms des fichiers Drive (lecture seule),
> e-mail. Elle sert au connecteur MCP de Gemini Enterprise.

## Étape 11 : le formulaire « Custom MCP Server » (console de l'app)

1. Console, projet **`acme-gemini-prod`** → 🔎 **Gemini Enterprise** → votre app.
2. Page des sources de données → section **MCP servers** → carte **Custom MCP Server** (« Connect your own Model
   Context Protocol (MCP) server to use custom tools ») → **Add MCP server**.
3. Écran **MCP Server Configuration**, partie **1. Authentication settings**. Remplissez **exactement** :

| Champ | Valeur |
|---|---|
| Select your authentication method | **OAuth 2.0** |
| **MCP Server URL** | `https://sheets-mcp-433175138344.europe-west1.run.app/mcp` (**avec** `/mcp`, même si l'aide dit « base URL ») |
| **Authorization URL** | `https://accounts.google.com/o/oauth2/v2/auth` |
| **Authorization URL Parameters** | `&access_type=offline&prompt=consent&hd=acme.example` |
| **Token URL** | `https://oauth2.googleapis.com/token` |
| **Client ID** | votre Client ID (étape 4) |
| **Client Secret** | votre Client secret (étape 4) |
| **Scopes** | `openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly` |
| **Enable PKCE Support** | **cochez-le** (décoché par défaut) |
| **Use HTTP Basic Authentication** | laissez-le **coché** (par défaut) |

Les valeurs, déjà remplies avec votre configuration (sauf le secret) : `./scripts/deployer.sh fiche`.

4. **Verify Auth**. Une fenêtre Google s'ouvre :
   - choisissez votre compte @acme.example ;
   - lisez les accès demandés (« voir, modifier, créer et supprimer vos feuilles de calcul Google Sheets », « voir
     les informations sur vos fichiers Google Drive », votre adresse e-mail) ;
   - **Allow** (*Autoriser*).

   **Attendu :** retour au formulaire, la vérification est réussie.
5. **Continue**. Partie **2. Advanced options** : rien à changer → **Continue**.
6. **Configure your data connector** :
   - Multi-region : **eu** (celle de l'app) ;
   - nom : `Google Sheets` ;
   - **Create**.
7. **Attendu :** le data store apparaît, d'abord **Creating**, puis **Active** (quelques minutes, rafraîchissez la
   page).

**Si ça bloque :**

| Symptôme | Cause → que faire |
|---|---|
| La carte « Custom MCP Server » est absente, grisée, ou refuse de créer | Étape 9, règle 1 pas encore appliquée (attendre 10 minutes) |
| Verify Auth : `Error 400: redirect_uri_mismatch` | Étape 4.5 : l'URI `…/oauth-redirect` manque ou est mal recopiée |
| Verify Auth : « Accès bloqué : votre administrateur… » | Étape 10 |
| Verify Auth : `invalid_client` | Client ID ou secret mal recopié (un espace en trop ?) |
| Création refusée : domaine non autorisé | Étape 9, règle 2 : les 3 domaines, **sans** `https://` |

## Étape 12 : activer les actions

1. Ouvrez le data store **Google Sheets** → onglet **Actions** → **Reload custom actions**.
   **Attendu :** les **17 actions** apparaissent, toutes **désactivées**.
2. Cochez, pour commencer, les **6 de lecture** : `whoami`, `search_spreadsheets`, `get_spreadsheet_info`,
   `read_range`, `read_ranges`, `find_in_sheet` → **Enable actions**.
3. Plus tard, quand les usages sont observés, ajoutez :
   - les écritures sans perte : `append_rows`, `create_spreadsheet`, `add_sheet`, `rename_sheet`, `insert_dimension`,
     `format_range` ;
   - puis, si besoin, les destructives : `write_range`, `clear_range`, `delete_sheet`, `delete_dimension`,
     `batch_update`.

Les actions de lecture s'exécutent sans confirmation. Les autres demandent une confirmation à l'utilisateur à chaque
fois.

**Si « Reload custom actions » échoue :** l'app n'arrive pas à joindre le serveur. Vérifiez l'étape 8 (Cloud Run
Invoker), l'URL avec `/mcp`, et les domaines de l'étape 9.

## Étape 13 : brancher le connecteur sur l'app

Votre app → **Connected data stores** (*Data stores connectés*) → **Add** (ou **Connect**) → cochez **Google Sheets**
→ **Save**.

**Attendu :** « Google Sheets » apparaît dans la liste des sources de l'app.

## Étape 14 : le premier usage, et les tests

Ouvrez l'app web Gemini Enterprise : **Overview** → le lien de l'app. Dans le chat **principal**, pas dans un agent :

| Demande | Attendu |
|---|---|
| « Pour Google Sheets, qui suis-je ? » | La 1re fois : un bouton **Authorize** (*Autoriser*) → fenêtre Google → **Allow**. Puis : votre e-mail @acme.example |
| « Trouve mes classeurs qui contiennent Ventes » | La liste, avec les liens |
| « Résume l'onglet Ventes du classeur `<lien>` » | Le contenu, résumé |
| Un classeur **non partagé** avec vous (ID connu) | « accès refusé » : seuls **vos** droits Drive s'appliquent |
| (actions d'écriture activées) « Ajoute la ligne Sac à dos, 39 dans Ventes » | Demande de **confirmation**, puis la ligne est ajoutée |

**Chaque utilisateur** fait la même chose la première fois : cliquer sur « Autoriser » avec **son** compte. Il ne voit
et ne modifie que **ses** classeurs, et ceux qu'on lui a partagés.

**Voir ce qui se passe :** projet des agents → **Cloud Run** → `sheets-mcp` → **Logs**. Chaque action donne une
ligne `{"event": "tool_call", "tool": …, "user": "<e-mail de l'utilisateur>", …}`. Le contenu des cellules n'est
jamais écrit.

**Si ça bloque dans le chat :**

| Symptôme | Cause → que faire |
|---|---|
| L'assistant n'utilise jamais Sheets | Étape 13 (connecteur pas branché sur l'app), ou étape 12 (aucune action activée) |
| « Impossible de se connecter au serveur » | Étape 8 ; ou attendre 3 minutes après un droit tout neuf |
| Erreur d'authentification sur toutes les actions | Le Client ID de l'étape 11 n'est pas celui de `OAUTH_CLIENT_IDS` (étape 5), ou `./scripts/deployer.sh mcp` n'a pas été relancé après l'étape 5 |
| Refus pour un collègue | Son compte n'est pas du domaine `acme.example` (journal : `auth_rejected`) |
| Reconnexion demandée toutes les heures | Étape 11 : `&access_type=offline&prompt=consent` manquant |
| Formule en erreur (`#ERROR!`) | Classeur en français : `;` entre les arguments et `,` décimale ([10-1, partie 6](10-1-serveur-mcp-comprendre-et-tester-en-local.md#6-le-piège-des-formules--la-locale-du-classeur)) |

---

## Et après

- **Google Slides dans l'assistant principal** : les mêmes 14 étapes, un 2e connecteur ; le tableau des différences est dans [10-13, partie 5](10-13-serveur-mcp-google-slides.md#5-le-brancher-sur-lassistant-principal-connecteur).

- **Un assistant métier qui utilise le même serveur** (consignes, autres outils) : [10-6](10-6-agent-adk-mcp-gemini-enterprise.md).
  Le même client OAuth sert : la 2de URI de redirection de l'étape 4 est faite pour lui.
- **Déclarer le serveur dans le catalogue** de l'organisation : `./scripts/deployer.sh registre` ([10-7](10-7-agent-registry-mcp.md)).
- **Mettre à jour le serveur** : modifiez, `./scripts/deployer.sh mcp`, puis **Reload custom actions** (étape 12).
- **Tout retirer** : data store → **Delete** (console de l'app), puis `./scripts/deployer.sh nettoyer`.
