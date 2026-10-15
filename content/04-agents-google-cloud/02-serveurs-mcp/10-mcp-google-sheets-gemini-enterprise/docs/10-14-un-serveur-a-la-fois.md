# 10-14. Un serveur à la fois : Sheets seul, Slides seul, puis l'autre

**Ce guide répond à :** je veux déployer et tester **un seul** serveur MCP (Sheets **ou** Slides), puis **ajouter
l'autre** plus tard. Quelles commandes, quels clics, et comment tester chacun **séparément** ? Par script, par
Terraform, et dans la console.

**La règle :** les deux serveurs sont **indépendants**. Chacun a :
- son service Cloud Run (`sheets-mcp`, `slides-mcp`) ;
- son connecteur dans l'app ;
- son entrée Agent Registry ;
- son test.

Ils partagent seulement l'image (`mcp-google`), le compte du serveur (`sheets-mcp-sa`, sans rôle) et le client
OAuth. L'agent prend ceux qui existent.

> **Testé en vrai (14 octobre 2026)**, projets de test :
> - `./scripts/deployer.sh mcp slides` : seulement Slides, Sheets n'est pas touché ;
> - `./scripts/deployer.sh mcp` : les deux ;
> - Terraform : ajout de Slides à un déploiement Sheets existant, **sans rien détruire** ;
> - les plans `["sheets"]`, `["slides"]` et les deux (résultats ci-dessous) ;
> - chaque serveur testé séparément sur Cloud Run (`tests/test_reel.py`, `tests/test_reel_slides.py`).

---

## Sommaire

1. [Ce qui est commun, ce qui est propre à chaque serveur](#1-ce-qui-est-commun-ce-qui-est-propre-à-chaque-serveur)
2. [Par script](#2-par-script)
3. [Par Terraform](#3-par-terraform)
4. [Dans la console](#4-dans-la-console)
5. [Tester chaque serveur séparément](#5-tester-chaque-serveur-séparément)
6. [Brancher chaque serveur sur l'app, séparément](#6-brancher-chaque-serveur-sur-lapp-séparément)
7. [Retirer un seul serveur](#7-retirer-un-seul-serveur)

---

## 1. Ce qui est commun, ce qui est propre à chaque serveur

| | Commun (une fois) | Sheets | Slides |
|---|---|---|---|
| Préparation (API, comptes) | `preparer` : active **les deux** API (Sheets, Slides) et crée les 3 comptes | – | – |
| Client OAuth | **Un seul** client, ses 2 URI de redirection | portée `spreadsheets` dans **Data access** | portée `presentations` dans **Data access** |
| Image | `mcp-google` (construite une fois) | `PRODUIT=sheets` | `PRODUIT=slides` |
| Service Cloud Run | – | `sheets-mcp` | `slides-mcp` |
| Droit ① du compte de l'app | – | Cloud Run Invoker sur `sheets-mcp` | Cloud Run Invoker sur `slides-mcp` |
| Domaine de sortie (règle d'organisation) | `accounts.google.com`, `oauth2.googleapis.com` | `sheets-mcp-<NUM>.europe-west1.run.app` | `slides-mcp-<NUM>.europe-west1.run.app` |
| Connecteur dans l'app | – | « Google Sheets » | « Google Slides » |
| Agent Registry | – | « Google Sheets (MCP) » | « Google Slides (MCP) » |
| Test | – | `tests/test_reel.py` + un **classeur** | `tests/test_reel_slides.py` + une **présentation** |

## 2. Par script

Configuration chargée (`source scripts/config.sh config/10-mcp.env`), dans le dossier du projet 10.

**Sheets seul :**
```bash
./scripts/deployer.sh preparer          # une fois
./scripts/deployer.sh mcp sheets        # construit l'image, déploie sheets-mcp, ne touche à rien d'autre
```
**Attendu :** `Serveur MCP sheets : https://sheets-mcp-<NUM>.europe-west1.run.app/mcp (privé …)`.

**Slides seul :**
```bash
./scripts/deployer.sh preparer          # une fois
./scripts/deployer.sh mcp slides        # déploie slides-mcp seulement
```
**Résultat obtenu** (projet de test, Sheets déjà déployé et **pas touché**) :
```
… europe-west1-docker.pkg.dev/second-project-511608/sheets-mcp/mcp-google:20261014-121736  SUCCESS
Service URL: https://slides-mcp-872505552973.europe-west1.run.app
Serveur MCP slides : https://slides-mcp-872505552973.europe-west1.run.app/mcp (privé : sans droit run.invoker, Cloud Run répond 403).
  serviceAccount:sheets-agent-sa@… : roles/run.invoker sur sheets-mcp
  serviceAccount:sheets-agent-sa@… : roles/run.invoker sur slides-mcp
```
Les deux dernières lignes n'apparaissent que si l'agent existe déjà : il garde ainsi l'accès à chaque serveur.

**L'un, puis l'autre :** `mcp sheets` aujourd'hui, `mcp slides` le jour voulu. **Les deux d'un coup :**
`./scripts/deployer.sh mcp`.

**Ensuite, pour le serveur ajouté** (chaque action traite ce qui existe, et saute le reste) :
```bash
./scripts/deployer.sh registre          # déclare chaque serveur déployé (« déjà déclaré » pour l'autre)
./scripts/deployer.sh droits-app        # droit ① sur chaque serveur déployé (le plan l'affiche avant)
./scripts/deployer.sh agent             # si vous utilisez l'agent : il reçoit l'adresse du nouveau serveur
./scripts/deployer.sh fiche             # le formulaire du connecteur de CHAQUE serveur déployé
```

**L'agent avec un seul serveur :** il prend ceux qui existent. Avec Sheets seul, il a 17 outils. Avec Slides seul,
il a 20 outils `slides_…`. Avec les deux, 37.

## 3. Par Terraform

La variable **`produits_mcp`** dit quels serveurs doivent **exister**, comme `AGENTS` au projet 09. Par défaut :
`["sheets", "slides"]`.

```bash
export TF_VAR_produits_mcp='["sheets"]'            # Sheets seul
export TF_VAR_produits_mcp='["slides"]'            # Slides seul
export TF_VAR_produits_mcp='["sheets","slides"]'   # les deux (= défaut)
cd terraform && terraform plan                     # LIRE la ligne Plan: avant « yes »
terraform apply
```

**Ajouter le 2e serveur plus tard :** passez de `'["sheets"]'` à `'["sheets","slides"]'`, puis `plan`. Le plan ne
doit montrer que des **créations** `["slides"]` :
```
  # google_cloud_run_v2_service.mcp["slides"] will be created
  # google_cloud_run_v2_service_iam_member.mcp["slides serviceAccount:…"] will be created
  # google_agent_registry_service.mcp["slides"] will be created
```
Une mise à jour sur place de l'agent (`…agent[0] will be updated in-place`) est normale : il reçoit `MCP_SLIDES_URL`.

**⚠ La liste décrit ce qui doit EXISTER.** Le retirer de la liste le **supprime**. Résultats réels des plans, sur un
projet où les deux serveurs existent :

| `produits_mcp` | Plan obtenu |
|---|---|
| `["sheets","slides"]` | rien de détruit (seulement des mises à jour d'image) |
| `["sheets"]` | `mcp["slides"] will be destroyed`, son entrée Agent Registry et ses 2 droits aussi (`6 to destroy`, dont les 2 anciennes images) |
| `["slides"]` | `mcp["sheets"] will be destroyed`, son entrée Agent Registry et ses 2 droits aussi |

Si un `destroy` apparaît alors que vous vouliez **ajouter** : répondez **`no`** et corrigez la liste.

**Un déploiement Sheets fait avant l'arrivée de Slides** passe sans rien détruire : Terraform le déplace (`has moved
to …mcp["sheets"]`) et garde ses droits. C'est testé ([10-13, partie 4](10-13-serveur-mcp-google-slides.md#4-déployer)).

## 4. Dans la console

L'image se construit une fois, avec **une** commande (Cloud Shell ou votre terminal ; [10-4, étape 3](10-4-deployer-console.md#étape-3--les-images-la-seule-commande)) :
```bash
gcloud builds submit mcp_server --config=cloudbuild.yaml \
  --substitutions=_IMAGE=europe-west1-docker.pkg.dev/<PROJET>/sheets-mcp/mcp-google:v1 \
  --region=europe-west1 --project=<PROJET> --service-account=projects/<PROJET>/serviceAccounts/sheets-build-sa@<PROJET>.iam.gserviceaccount.com
```

Puis, **pour chaque serveur voulu**, l'écran 🔎 **Cloud Run** → **Deploy container** ([10-4, étape 4](10-4-deployer-console.md#étape-4--le-serveur-mcp)) :

| Champ | Sheets | Slides |
|---|---|---|
| Container image URL | `…/sheets-mcp/mcp-google:v1` | **la même** |
| Service name | `sheets-mcp` | `slides-mcp` |
| Authentication | **Require authentication** | **Require authentication** |
| Variables | `PRODUIT` = `sheets`, `OAUTH_CLIENT_IDS`, `ALLOWED_DOMAINS` | `PRODUIT` = **`slides`**, `OAUTH_CLIENT_IDS`, `ALLOWED_DOMAINS` |
| Service account | `sheets-mcp-sa` | `sheets-mcp-sa` (le même, sans rôle) |

**Ajouter le 2e plus tard :** refaites seulement l'écran **Deploy container** avec la colonne de l'autre serveur.
L'image est déjà là.

Le droit d'appel de chaque serveur : **Cloud Run** → le service → **Security** → **Add principal**
([10-11, partie 3](10-11-droits-voir-et-donner-console.md#3-donner-en-clics)).

## 5. Tester chaque serveur séparément

**En local** (sans Cloud Run) : un terminal par serveur.

| | Sheets | Slides |
|---|---|---|
| Lancer | `cd mcp_server && PRODUIT=sheets OAUTH_CLIENT_IDS=<aud> ALLOWED_DOMAINS=<dom> PORT=8091 python main.py` | `cd mcp_server && PRODUIT=slides OAUTH_CLIENT_IDS=<aud> ALLOWED_DOMAINS=<dom> PORT=8095 python main.py` |
| Tester | `MCP_URL=http://localhost:8091/mcp SPREADSHEET_ID=<ID> python tests/test_reel.py` | `MCP_URL=http://localhost:8095/mcp PRESENTATION_ID=<ID> python tests/test_reel_slides.py` |
| Jeton (portée) | `spreadsheets` | `presentations` |
| Attendu | `tools/list : 17 outils` … `OK : test réel terminé` | `tools/list : 20 outils` … `OK : test réel Slides terminé` |

Comment obtenir le jeton et `<aud>` : [10-8, partie 2](10-8-tester-simuler-verifier.md#2-obtenir-un-jeton-de-test).

**Sur Cloud Run**, `./scripts/deployer.sh tester` teste **ce que vous lui donnez** :
```bash
export USER_TOKEN=…                                   # portée spreadsheets et/ou presentations
SPREADSHEET_ID=<ID> ./scripts/deployer.sh tester      # Sheets seul (+ l'agent s'il existe)
PRESENTATION_ID=<ID> ./scripts/deployer.sh tester     # Slides seul
SPREADSHEET_ID=<ID> PRESENTATION_ID=<ID> ./scripts/deployer.sh tester   # les deux
```
Dans chaque cas :
- l'étape 1 vérifie que **chaque** serveur déployé refuse un appel sans jeton (`403`) ;
- un serveur sans fichier de test est sauté, avec le message `(sauté : …)`.

**Résultat obtenu** (Slides seul : `PRESENTATION_ID` seulement) :
```
== 1. Sans aucun jeton : Cloud Run doit refuser (403)
   403  https://sheets-mcp-872505552973.europe-west1.run.app/mcp
   403  https://slides-mcp-872505552973.europe-west1.run.app/mcp
== 2. Le serveur MCP Sheets, comme le connecteur de Gemini Enterprise (2 en-têtes), les 17 outils sur le vrai classeur
   (sauté : SPREADSHEET_ID vide, ou sheets-mcp pas déployé)
== 2 bis. Le serveur MCP Slides, comme le connecteur, les 20 outils sur la vraie présentation
tools/list : 20 outils
…
présentation rendue intacte : 1 diapositive(s)
OK : test réel Slides terminé
```

**Un appel à la main**, sans script, comme le connecteur (remplacez `sheets` par `slides` pour l'autre) :
```bash
curl -s -X POST https://sheets-mcp-<NUM>.europe-west1.run.app/mcp \
  -H "X-Serverless-Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"whoami","arguments":{}}}'
```
**Résultat obtenu** (Slides) :
- avec les deux en-têtes : `{"email":"sheets-utilisateur-test@…","scopes":[…,"https://www.googleapis.com/auth/presentations",…]}` ;
- sans `Authorization` (jeton utilisateur) : **`401`**, refusé par le serveur ;
- sans `X-Serverless-Authorization` : **`403`**, refusé par Cloud Run, avant même le serveur.

## 6. Brancher chaque serveur sur l'app, séparément

Un **connecteur « Custom MCP Server » par serveur**. Ajouter le second plus tard ne change rien au premier.

| Étape ([10-12](10-12-pas-a-pas-mcp-dans-assistant-principal.md)) | Sheets | Slides |
|---|---|---|
| 4. Data access du client OAuth | `…/auth/spreadsheets` | `…/auth/presentations` (ajoutez-la au même client) |
| 8. Droit d'appel | sur `sheets-mcp` | sur `slides-mcp` |
| 9. Domaine de sortie | `sheets-mcp-…run.app` | `slides-mcp-…run.app` |
| 11. MCP Server URL | `https://sheets-mcp-<NUM>.europe-west1.run.app/mcp` | `https://slides-mcp-<NUM>.europe-west1.run.app/mcp` |
| 11. Scopes | `openid …/userinfo.email …/spreadsheets …/drive.metadata.readonly` | `openid …/userinfo.email …/presentations …/drive.metadata.readonly` |
| 11. Nom du data connector | `Google Sheets` | `Google Slides` |
| 12. Actions de lecture d'abord | 6 | 7 |
| 13. Connected data stores | Google Sheets | Google Slides |

Le reste du formulaire est identique : même Authorization URL, mêmes paramètres, même Token URL, même client, PKCE
coché. `./scripts/deployer.sh fiche` affiche chaque formulaire, rempli, pour chaque serveur déployé.

Chaque utilisateur clique sur « Autoriser » **une fois par connecteur** (deux consentements, chacun avec ses propres
portées).

## 7. Retirer un seul serveur

| Méthode | Comment |
|---|---|
| Console de l'app | Data stores → `Google Slides` (ou `Google Sheets`) → **Delete** |
| Script | `gcloud run services delete slides-mcp --region=europe-west1 --project=<PROJET>` et `gcloud agent-registry services delete slides-mcp --location=europe-west1 --project=<PROJET>`. `./scripts/deployer.sh nettoyer` retire **tout** |
| Terraform | Retirez-le de `produits_mcp`, `plan` (vérifiez que seul ce serveur part), `apply` |
| Console Google Cloud | Cloud Run → le service → **Delete** ; Agent Registry → l'entrée → **Delete** |

Si l'agent était déployé, relancez `./scripts/deployer.sh agent` pour qu'il oublie le serveur retiré. Terraform le
fait tout seul.
