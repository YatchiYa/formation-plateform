# MCP Google Sheets pour Gemini Enterprise (OAuth, Cloud Run, Terraform)

Un serveur **MCP** qui donne à Gemini Enterprise une interaction **native et complète** avec Google Sheets : rechercher,
lire, écrire, ajouter des lignes, créer des classeurs, gérer les onglets, mettre en forme, et toute l'API Sheets via
`batch_update`. **Chaque action est faite au nom de l'utilisateur connecté, avec son propre compte Google (OAuth).**

> Exemples dans Gemini Enterprise :
> - « Trouve le classeur *Ventes 2026* et résume l'onglet *Ventes* »
> - « Ajoute une ligne Sac à dos, 39 € dans *Ventes* »
> - « Crée un classeur *Inventaire Lille* avec les onglets Rayon et Réserve, puis mets la ligne d'en-tête en gras »
> - « Trie l'onglet *Ventes* par prix décroissant »

Contexte : ce sous-projet complète le [projet 04](../README.md) (MCP sur Cloud Run + Agent Registry) et s'intègre au
socle de sécurité du [projet 06](../../06-gemini-enterprise-security-baseline/README.md).

---

## Sommaire

1. [Architecture : comment la connexion fonctionne](#1-architecture--comment-la-connexion-fonctionne)
2. [Sécurité : les contrôles, et pourquoi](#2-sécurité--les-contrôles-et-pourquoi)
3. [Les 17 outils](#3-les-17-outils)
4. [Mise en place pas à pas](#4-mise-en-place-pas-à-pas)
5. [Tester](#5-tester)
6. [Exploiter](#6-exploiter)
7. [Dépannage](#7-dépannage)
8. [Fichiers](#8-fichiers)

---

## 1. Architecture : comment la connexion fonctionne

```
 Utilisateur (alice@acme.example)
     │  1ère utilisation : « Autoriser Google Sheets » → écran de consentement Google (une fois)
     ▼
 Gemini Enterprise ── stocke le jeton OAuth d'Alice (et son refresh token), le renouvelle seul
     │
     │  POST https://sheets-mcp-xxxx.europe-west1.run.app/mcp
     │    X-Serverless-Authorization: <jeton du service Gemini Enterprise>   → vérifié par Cloud Run (IAM)
     │    Authorization: Bearer <jeton OAuth d'Alice>                       → vérifié par le serveur MCP
     ▼
 Cloud Run « sheets-mcp » (PRIVÉ, aucun droit propre)
     │  vérifie le jeton d'Alice : émis pour NOTRE client OAuth, scope Sheets, e-mail @acme.example
     │
     │  appelle l'API avec le jeton d'Alice  →  Alice ne voit et ne modifie que SES fichiers
     ▼
 Google Sheets API / Drive API
```

**Deux jetons, deux rôles :**

| En-tête | Contient | Vérifié par | Garantit |
|---|---|---|---|
| `X-Serverless-Authorization` | Jeton signé par Google du **service agent Gemini Enterprise** | **Cloud Run** (IAM `roles/run.invoker`) | Seul Gemini Enterprise peut atteindre le serveur |
| `Authorization: Bearer …` | **Jeton OAuth de l'utilisateur** | **Le serveur** (`CompanyGoogleTokenVerifier`) | L'utilisateur est authentifié, appartient au domaine, et a consenti au scope Sheets |

Gemini Enterprise ajoute le premier en-tête automatiquement pour les URL `*.run.app`, et transmet le second intact
(documentation Google). **Le serveur reste donc privé**, sans clé API ni secret côté Cloud Run.

---

## 2. Sécurité : les contrôles, et pourquoi

| # | Contrôle | Pourquoi | Où |
|---|---|---|---|
| 1 | **Cloud Run privé**, `run.invoker` réservé au service agent Gemini Enterprise | Le serveur n'est pas joignable depuis Internet, même avec un jeton Google valide | `terraform/main.tf` (§5) |
| 2 | **Délégation stricte** : toutes les API sont appelées avec **le jeton de l'utilisateur** | Le serveur n'a **aucun** droit propre (compte de service sans rôle). Impossible d'accéder à un fichier que l'utilisateur ne peut pas ouvrir | `server/main.py` (`google()`) |
| 3 | **Vérification de l'audience** du jeton (`aud` = notre client OAuth) | Empêche le « confused deputy » : un jeton émis pour une autre application ne peut pas être rejoué ici | `GoogleTokenVerifier(audience=…)` |
| 4 | **Scope Sheets obligatoire**, e-mail **vérifié** et **domaine autorisé** (`acme.example`) | Les comptes Gmail personnels et les autres organisations sont refusés, même s'ils obtiennent un jeton | `CompanyGoogleTokenVerifier` |
| 5 | **Écran de consentement OAuth « Interne »** + paramètre `hd=acme.example` | Seuls les comptes de l'organisation peuvent se connecter ; le sélecteur de compte propose directement le compte professionnel | Console, étape 1 |
| 6 | **Annotations MCP** : `readOnlyHint` (lecture), `destructiveHint` (écrasement, suppression) | Gemini Enterprise exécute les lectures sans friction et **demande confirmation** avant toute écriture destructive | Chaque `@mcp.tool` |
| 7 | **Journal d'audit structuré** : utilisateur, outil, classeur, plage. **Jamais le contenu des cellules** | Traçabilité sans exposer les données | `audit()` → Cloud Logging |
| 8 | **Garde-fou de volume** : 20 000 cellules max par lecture (`truncated: true` au-delà) | Évite d'envoyer un classeur entier au modèle | `MAX_CELLS_PER_READ` |
| 9 | **Démarrage refusé sans audience configurée** | Une erreur de configuration ne peut pas produire un serveur qui accepte n'importe quel jeton | `main.py`, début |
| 10 | **Scopes minimaux** : `spreadsheets` + `drive.metadata.readonly` (recherche par nom uniquement) | Pas d'accès au contenu des autres fichiers Drive | Formulaire Gemini Enterprise |

> **Pourquoi pas un compte de service avec délégation domaine (DWD) ?** Ce serait plus simple à configurer, mais le
> serveur pourrait alors lire **n'importe quel** classeur de l'entreprise. Avec OAuth par utilisateur, le serveur n'a
> **aucun** pouvoir propre : les droits Google Drive de chacun font foi. C'est le bon modèle pour un assistant ouvert
> à tous.

---

## 3. Les 17 outils

| Outil | Rôle | Type (confirmation) |
|---|---|---|
| `whoami` | Utilisateur connecté (test de la connexion) | Lecture |
| `search_spreadsheets` | Trouver des classeurs par nom (Mon Drive + Drive partagés) | Lecture |
| `get_spreadsheet_info` | Titre, lien, onglets (taille, lignes figées) | Lecture |
| `read_range` | Lire une plage (valeurs affichées, brutes ou formules) | Lecture |
| `read_ranges` | Lire jusqu'à 20 plages en un appel | Lecture |
| `find_in_sheet` | Trouver les cellules contenant un texte | Lecture |
| `write_range` | Écrire en **remplaçant** une plage (formules acceptées) | **Destructif** |
| `append_rows` | Ajouter des lignes à la fin d'un tableau | Écriture |
| `clear_range` | Effacer les valeurs d'une plage | **Destructif** |
| `create_spreadsheet` | Créer un classeur (avec onglets) | Écriture |
| `add_sheet` / `rename_sheet` | Ajouter / renommer un onglet | Écriture |
| `delete_sheet` | Supprimer un onglet et son contenu | **Destructif** |
| `insert_dimension` | Insérer des lignes ou colonnes | Écriture |
| `delete_dimension` | Supprimer des lignes ou colonnes | **Destructif** |
| `format_range` | Gras, italique, couleurs, format de nombre, alignement | Écriture |
| `batch_update` | **Toute l'API Sheets** : tri, filtres, fusion, mise en forme conditionnelle, graphiques, validation, protection… | **Destructif** |

Les plages s'écrivent en notation A1 : `Ventes!A1:D20`, `'Mon onglet'!A:A`, `B2`.

**Recommandation au lancement :** dans Gemini Enterprise, activez d'abord les 6 outils de lecture, puis
`append_rows`, `create_spreadsheet` et `format_range`. Activez les outils destructifs une fois les usages observés.

---

## 4. Mise en place pas à pas

### Étape 1 : créer le client OAuth (console, une fois)

Dans le projet GCP de Gemini Enterprise : **APIs et services → Google Auth Platform** (ou *Écran de consentement OAuth*).

1. **Image de marque (Branding)** : nom de l'application `Gemini Enterprise - Google Sheets`, e-mail d'assistance,
   domaine autorisé `acme.example`.
2. **Audience** : **Interne**. Seuls les comptes de l'organisation peuvent se connecter, et aucune validation Google
   n'est nécessaire.
3. **Accès aux données (scopes)** : ajoutez
   `openid`, `.../auth/userinfo.email`, `.../auth/spreadsheets`, `.../auth/drive.metadata.readonly`.
4. **Clients → Créer un client** : type **Application Web**, nom `gemini-enterprise-sheets-mcp`,
   **URI de redirection autorisé** : `https://vertexaisearch.cloud.google.com/oauth-redirect`.
5. Notez le **Client ID** (pour Terraform et Gemini Enterprise) et le **Client secret** (pour Gemini Enterprise
   uniquement : ne le mettez ni dans Terraform ni dans Git).

> Le client OAuth ne peut pas être créé par Terraform pour des comptes Google (pas de ressource dans le provider) :
> c'est une étape console documentée.

### Étape 2 : déployer le serveur (Terraform)

```bash
cd sheets-mcp/terraform
cp terraform.tfvars.example terraform.tfvars   # project_id, oauth_client_ids, allowed_domains
terraform init
terraform plan
terraform apply
terraform output mcp_server_url
terraform output gemini_enterprise_oauth_settings
terraform output egress_fqdns_to_allow
```

Ce que Terraform crée : les API (Cloud Run, Sheets, Drive), l'image, un compte de service **sans rôle**, le service
Cloud Run **privé**, le droit d'appel pour le service agent Gemini Enterprise, et l'entrée **Agent Registry** avec la
liste des 17 outils (générée depuis le code par `scripts/gen_toolspec.py`).

### Étape 3 : politiques d'organisation (admin de l'organisation)

Gemini Enterprise bloque par défaut les serveurs MCP personnalisés. Dans **IAM et administration → Règles
d'administration**, sur le projet :

1. Autoriser la **création de data stores « Custom MCP Server »** (règle qui bloque les MCP personnalisés).
2. **Sources de données autorisées pour les connecteurs** : ajouter `custom_mcp`.
3. **Domaines de sortie autorisés pour les connecteurs** : ajouter les 3 domaines de
   `terraform output egress_fqdns_to_allow` (le domaine `*.run.app` du service, `accounts.google.com`,
   `oauth2.googleapis.com`).

### Étape 4 : ajouter le serveur dans Gemini Enterprise

Console : **Gemini Enterprise → Data stores → Créer un data store → Custom MCP Server → Add MCP server**.

| Champ | Valeur |
|---|---|
| Authentification | **OAuth 2.0** |
| MCP server URL | `terraform output mcp_server_url` (se termine par `/mcp`) |
| Authorization URL | `https://accounts.google.com/o/oauth2/v2/auth` |
| Authorization URL parameters | `access_type=offline&prompt=consent&hd=acme.example` |
| Token URL | `https://oauth2.googleapis.com/token` |
| Client ID / Client secret | ceux de l'étape 1 |
| Enable PKCE | ✅ activé |
| Scopes | `openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly` |
| Localisation | celle de l'app (`eu`) |
| Nom du data connector | `Google Sheets` |

Pourquoi ces paramètres :
- `access_type=offline` + `prompt=consent` : Google délivre un **refresh token**. Gemini Enterprise renouvelle le
  jeton seul, et l'utilisateur ne se reconnecte pas toutes les heures.
- `hd=acme.example` : le sélecteur de compte propose directement le compte professionnel. Ce n'est **qu'un confort** :
  la vraie barrière est le contrôle de domaine côté serveur (contrôle n° 4).
- **PKCE** : protège l'échange du code d'autorisation contre l'interception.

Puis :
1. **Actions** : les outils apparaissent comme actions, **désactivées par défaut**. Activez-les (voir la recommandation
   au §3 ; 100 actions maximum).
2. **App → Connected data stores** : ajoutez le data store *Google Sheets* à l'app.

### Étape 5 : première utilisation (chaque utilisateur, une fois)

L'utilisateur demande par exemple « Liste mes classeurs Ventes ». Gemini Enterprise affiche **Autoriser** : écran de
consentement Google (compte @acme.example, scopes listés), puis retour dans l'assistant. C'est terminé : les appels
suivants sont directs.

---

## 5. Tester

### 5.1 Test de bout en bout, sans compte Google (déjà exécuté)

```bash
cd sheets-mcp
pip install -r server/requirements.txt
python tests/test_server.py
```

Le serveur tourne en HTTP comme sur Cloud Run. Un client MCP l'appelle avec `Authorization: Bearer`, et Google est
simulé. Le test vérifie :
- **4 refus** : jeton invalide, jeton d'une autre application, compte hors domaine, scope absent ;
- les **17 outils**, et leurs annotations lecture / destructif ;
- que **chaque appel Google porte le jeton de l'utilisateur** ;
- la traduction des erreurs Google en messages clairs.

Résultat actuel : `OK : tous les tests passent (23 appels Google simulés, tous avec le jeton de l'utilisateur).`

### 5.2 Test réel en local, avec votre compte

```bash
# Un jeton avec les bons scopes (son audience = le client OAuth de gcloud)
gcloud auth application-default login \
  --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.metadata.readonly,https://www.googleapis.com/auth/cloud-platform
TOKEN=$(gcloud auth application-default print-access-token)
AUD=$(curl -s "https://oauth2.googleapis.com/tokeninfo?access_token=$TOKEN" | python3 -c 'import json,sys; print(json.load(sys.stdin)["aud"])')

# Serveur local qui accepte CETTE audience (uniquement en local, jamais en production)
OAUTH_CLIENT_IDS=$AUD ALLOWED_DOMAINS=acme.example python server/main.py &

# Appel MCP
curl -s -X POST localhost:8080/mcp -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"whoami","arguments":{}}}'
```

Vous pouvez aussi connecter **MCP Inspector** (`npx @modelcontextprotocol/inspector`) à `http://localhost:8080/mcp`
en ajoutant l'en-tête `Authorization: Bearer $TOKEN`.

### 5.3 Recette dans Gemini Enterprise

| Test | Attendu |
|---|---|
| « Qui suis-je pour Google Sheets ? » | Votre e-mail @acme.example |
| Lire un classeur partagé avec vous | Contenu résumé |
| Lire un classeur **non** partagé avec vous (ID connu) | « accès refusé » : les droits Drive font foi |
| « Ajoute une ligne … » | Ligne ajoutée |
| « Efface la colonne C » | **Demande de confirmation**, puis effacement |
| Compte d'un autre domaine | Connexion impossible (consentement interne) ; et refus serveur en défense |
| `curl` sans jeton sur l'URL Cloud Run | `403` (Cloud Run) |

---

## 6. Exploiter

**Journaux** (Cloud Logging, ressource Cloud Run `sheets-mcp`) :
```
jsonPayload.event="tool_call"                      -- qui a utilisé quel outil, sur quel classeur
jsonPayload.event="auth_rejected"                  -- tentatives refusées (domaine, e-mail non vérifié)
```
Le contenu des cellules n'est **jamais** journalisé.

**Révoquer un accès :**
- un utilisateur : *myaccount.google.com → Sécurité → Applications tierces* ;
- un administrateur Workspace : *Admin console → Sécurité → Contrôle des API → Accès des applications* (bloquer
  le client OAuth) ;
- tout le monde, d'urgence : désactiver le client OAuth (étape 1), ou retirer `run.invoker` au service agent.

**Mettre à jour le serveur :** modifier `server/main.py`, lancer `python tests/test_server.py` puis
`python scripts/gen_toolspec.py` (liste des outils du registre), et `terraform apply`. L'image est reconstruite
seulement si le code change.

**Quotas :** l'API Sheets impose des quotas par minute, par utilisateur et par projet. Le serveur traduit le `429`
en message clair (« réessayez dans une minute »). Augmentez les quotas dans la console si l'usage le justifie.

**Coût :** `min_instances = 1` garde une instance chaude (réponses immédiates, coût fixe modéré). `0` réduit le coût,
au prix d'un démarrage à froid de quelques secondes.

---

## 7. Dépannage

| Symptôme | Cause → solution |
|---|---|
| Gemini Enterprise : « impossible de se connecter au serveur » | `run.invoker` manquant pour le service agent (`terraform apply`) ; ou URL sans `/mcp` ; ou domaine `*.run.app` non autorisé dans la politique de sortie |
| L'écran de consentement affiche « erreur redirect_uri_mismatch » | L'URI `https://vertexaisearch.cloud.google.com/oauth-redirect` n'est pas dans le client OAuth |
| Tous les appels renvoient 401 | `oauth_client_ids` ne contient pas l'ID du client configuré dans Gemini Enterprise |
| Refus pour un utilisateur légitime | Domaine absent de `allowed_domains`, ou compte sans e-mail vérifié (journal `auth_rejected`) |
| `search_spreadsheets` : accès refusé | Scope `drive.metadata.readonly` absent : l'ajouter au client OAuth **et** dans Gemini Enterprise, puis se reconnecter |
| Reconnexion demandée toutes les heures | `access_type=offline&prompt=consent` absent des paramètres d'autorisation |
| Data store « Custom MCP Server » introuvable ou bloqué | Politiques d'organisation de l'étape 3 |
| Réponse tronquée (`truncated: true`) | Plage trop grande : lire une plage plus petite, ou ajuster `MAX_CELLS_PER_READ` |

---

## 8. Fichiers

```
sheets-mcp/
├── server/
│   ├── main.py            ← le serveur : authentification, 17 outils, journal d'audit
│   ├── requirements.txt   ← fastmcp 4.0.10, uvicorn, httpx
│   └── Dockerfile
├── tests/test_server.py   ← test de bout en bout (HTTP réel, Google simulé)
├── scripts/gen_toolspec.py← génère terraform/toolspec.json depuis le code
└── terraform/
    ├── main.tf            ← APIs, image, compte sans rôle, Cloud Run privé, invoker, Agent Registry
    ├── variables.tf · outputs.tf · versions.tf · terraform.tfvars.example
    └── toolspec.json      ← les 17 outils publiés dans Agent Registry
```

**Sources :**
- [Custom MCP Server dans Gemini Enterprise](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server)
- [Configurer Gemini Enterprise avec un MCP personnalisé](https://medium.com/google-cloud/how-to-configure-gemini-enterprise-to-connect-to-a-custom-mcp-server-2e28adc96420)
- [API Google Sheets v4](https://developers.google.com/sheets/api/reference/rest)
- [OAuth 2.0 pour applications Web](https://developers.google.com/identity/protocols/oauth2/web-server)
