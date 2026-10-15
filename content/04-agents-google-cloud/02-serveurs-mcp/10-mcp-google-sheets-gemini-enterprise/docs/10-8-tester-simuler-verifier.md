# 10-8. Tester, simuler Gemini Enterprise, vérifier

**Ce guide répond à :** quels tests existent, que prouve chacun, comment les relancer **exactement** ? Comment obtenir
un jeton utilisateur de test, et quels résultats ont été obtenus ?

| # | Test | Il faut | Prouve | Statut |
|---|---|---|---|---|
| 1 | `tests/test_server.py` | rien (Google simulé) | Refus d'authentification, 17 outils, annotations, erreurs claires | ✅ passé |
| 2 | `tests/test_reel.py`, serveur local | jeton + classeur | Les 17 outils sur la **vraie** API Sheets | ✅ passé |
| 3 | `tests/test_agent_chaine.py` | jeton + classeur | A2A (2 en-têtes) → agent → MCP → vraie API Sheets ; sans jeton : message clair | ✅ passé (modèle simulé) |
| 4 | `./scripts/deployer.sh tester` | jeton + classeur + projet déployé | Cloud Run privé (403), serveur appelé comme le connecteur, agent A2A et Agent Runtime appelés comme l'app (vrai Gemini) | ✅ passé (14 octobre) |
| 2 bis | `tests/test_reel_slides.py` (local et Cloud Run) | jeton (portée `presentations`) + présentation | Les **20 outils Slides** sur la vraie API ; présentation rendue intacte | ✅ passé (14 octobre) |
| 4 bis | Compte « simulateur » **du projet de l'app** | idem | Le droit ① d'un projet à l'autre : 403 sans, OK avec | ✅ passé |
| 4 ter | Écriture par l'agent, sur plusieurs tours | idem | Confirmation demandée avant d'écrire **et** avant de supprimer | ✅ passé |
| 5 | Dans l'app | une app Gemini Enterprise | L'expérience réelle | ⏳ chez Acme : 10-5 partie 7, 10-6 partie 6 |

---

## 1. Préparer un classeur de test

Créez un classeur dans votre Drive, par exemple trois colonnes « Produit, Prix, Stock » et quelques lignes. Copiez son
ID : c'est la partie entre `/d/` et `/edit` dans l'URL. Le compte du jeton (partie 2) doit pouvoir le **modifier**.
Partagez-le en **Éditeur** si ce n'est pas votre compte.

Les tests 2 à 4 travaillent dans un **onglet temporaire** qu'ils suppriment : le classeur est rendu intact.

## 2. Obtenir un jeton de test

Le serveur n'accepte qu'un jeton :
- émis pour un client OAuth listé dans `OAUTH_CLIENT_IDS` ;
- d'un domaine listé dans `ALLOWED_DOMAINS` ;
- avec la portée `spreadsheets`.

Deux façons d'en obtenir un.

**A. Votre compte Acme** (le plus parlant). `gcloud` sait demander un jeton avec les portées Sheets :
```bash
gcloud auth application-default login \
  --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.metadata.readonly,https://www.googleapis.com/auth/cloud-platform
export USER_TOKEN=$(gcloud auth application-default print-access-token)
curl -s "https://oauth2.googleapis.com/tokeninfo?access_token=$USER_TOKEN"      # lire "aud" et "email"
```
Ce jeton est émis pour le client OAuth **de gcloud** (`aud` = `764086051850-….apps.googleusercontent.com`). Le
serveur ne l'accepte que si cet ID est dans `OAUTH_CLIENT_IDS`. Deux cas :
- **en local**, lancez le serveur avec `OAUTH_CLIENT_IDS=<aud>` ([10-1, 5.2](10-1-serveur-mcp-comprendre-et-tester-en-local.md#52-sur-un-vrai-classeur-en-local)) ;
- **sur Cloud Run**, ajoutez-le **temporairement** :
  1. `OAUTH_CLIENT_IDS="<client de l'app>,<aud de gcloud>"` ;
  2. `./scripts/deployer.sh mcp` ;
  3. lancez le test ;
  4. retirez-le, puis relancez `mcp`.

Si l'admin Workspace bloque le client gcloud pour les portées Sheets, prenez la façon B.

**B. Un compte de service de test** (c'est ce qui a été utilisé pour les résultats de ce guide). Un compte de service
peut jouer l'utilisateur. Son jeton contient tout ce que le serveur vérifie :
- `aud` et `sub` : l'ID numérique du compte ;
- `email`, `email_verified` ;
- les portées.

```bash
gcloud iam service-accounts create sheets-utilisateur-test --project=$PROJET
gcloud iam service-accounts add-iam-policy-binding sheets-utilisateur-test@$PROJET.iam.gserviceaccount.com \
  --member=user:$(gcloud config get-value account) --role=roles/iam.serviceAccountTokenCreator
export USER_TOKEN=$(gcloud auth print-access-token --impersonate-service-account=sheets-utilisateur-test@$PROJET.iam.gserviceaccount.com \
  --scopes=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/spreadsheets,https://www.googleapis.com/auth/drive.metadata.readonly)
curl -s "https://oauth2.googleapis.com/tokeninfo?access_token=$USER_TOKEN"
```
**Résultat obtenu :**
```
{ "azp": "103672306044954377295", "aud": "103672306044954377295", "sub": "103672306044954377295",
  "scope": "email https://www.googleapis.com/auth/drive.metadata.readonly https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/userinfo.email openid",
  "expires_in": "3599", "email": "sheets-utilisateur-test@<PROJET>.iam.gserviceaccount.com", "email_verified": "true" }
```
Ensuite :
- le serveur doit accepter `OAUTH_CLIENT_IDS=<aud>` et `ALLOWED_DOMAINS=<PROJET>.iam.gserviceaccount.com` (en local,
  ou dans un déploiement de test) ;
- **partagez le classeur** avec l'e-mail du compte, en Éditeur.

Un compte de service **ne peut pas créer** de classeur (il n'a pas d'espace Drive) : `create_spreadsheet` est
refusé. C'est le seul outil concerné.

Le jeton vit 1 heure : redemandez-le si un test renvoie 401.

## 3. Les tests locaux (1, 2, 3)

```bash
python tests/test_server.py                                         # 1 : Google simulé

OAUTH_CLIENT_IDS=<aud> ALLOWED_DOMAINS=<domaine> PORT=8091 python mcp_server/main.py &
MCP_URL=http://localhost:8091/mcp SPREADSHEET_ID=<ID> python tests/test_reel.py              # 2

OAUTH_CLIENT_IDS=<aud> ALLOWED_DOMAINS=<domaine> SPREADSHEET_ID=<ID> GOOGLE_CLOUD_PROJECT=$PROJET \
  python tests/test_agent_chaine.py                                                          # 3 (google-adk requis)
```
- **Résultats obtenus (1 et 2) :** [10-1, partie 5](10-1-serveur-mcp-comprendre-et-tester-en-local.md#5-tester).
- **Résultat obtenu (3) :**
  ```
  outils vus par le modèle : 17 (add_sheet, append_rows, batch_update, clear_range…)
  réponse de l'agent        : RÉSULTAT {"content": [{"type": "text", "text": "{\"range\":\"Untitled!A1:C4\",\"values\":[[\"Produit\",\"Prix\",\"Stock\"],[\"Vélo\",\"299\",\"12\"],[\"Tente\",…
  sans jeton utilisateur    : outils ['autorisation_requise'] -> RÉSULTAT {"status": "error", "error_message": "Pas de jeton Google de l'utilisateur : il doit cliquer sur « Autoriser » …
  OK : A2A -> agent -> MCP -> Google Sheets, avec le jeton de l'utilisateur ; sans jeton, message clair.
  ```
  Le journal du serveur MCP montre l'appel fait **au nom de l'utilisateur** :
  `{"event": "tool_call", "tool": "read_range", "user": "sheets-utilisateur-test@…", "spreadsheet_id": "1H-w96…", "range": "A1:C4"}`.

Le test 3 remplace Gemini par un « faux Gemini » qui appelle `read_range`. Tout le reste est réel :
- l'appel A2A avec les deux en-têtes ;
- `agent/main.py` ;
- l'agent ADK ;
- `McpToolset` avec `header_provider` ;
- le serveur MCP ;
- la vraie API Sheets.

C'est ce qui permet de le lancer **sans Vertex AI et sans facturation**.

## 4. Sur Cloud Run : comme Gemini Enterprise

Une fois `mcp` (et `agent`, `agent-runtime`) déployés ([10-2](10-2-deployer-shell.md)) :
```bash
export USER_TOKEN=… SPREADSHEET_ID=…
./scripts/deployer.sh tester
```
| Étape | Ce que fait le script | Attendu |
|---|---|---|
| 1 | `POST $MCP_URL` **sans** jeton | `403` : Cloud Run refuse, le service est privé |
| 2 | `tests/test_reel.py` avec `X-Serverless-Authorization` = **votre** jeton d'identité, et `Authorization` = le jeton utilisateur. Ce sont les deux en-têtes du connecteur | La même sortie qu'en local, plus `OK : test réel terminé` |
| 3 | `tests/appel_a2a.py` appelle l'agent A2A déployé, **avec Gemini**, comme l'app (2 en-têtes) | `état : completed` et la liste des onglets |
| 4 | `tests/appel_runtime.py` : `streaming_agent_run_with_events` avec `authorizations: {acces-sheets-runtime: jeton}`, comme l'app | Les 3 premières lignes du classeur |

**Résultat obtenu, l'écriture par l'agent** (agent A2A sur Cloud Run, vrai Gemini, même conversation avec `CONTEXTE`) :
```
tour 1 > Dans le classeur …, ajoute un onglet nommé essai-agent et écris dedans en A1:B2 : Produit, Prix ; Gourde, 9
       < Je m'apprête à effectuer les actions suivantes … 1. Ajouter un nouvel onglet essai-agent. 2. Écrire … dans
         'essai-agent'!A1:B2 … Confirmez-vous vouloir procéder à ces modifications ?
tour 2 > Oui, vas-y.
       < C'est fait ! L'onglet « essai-agent » a été ajouté … données inscrites dans A1:B2. [lien du classeur]
tour 3 > Maintenant supprime l'onglet essai-agent.
       < Je m'apprête à supprimer définitivement l'onglet essai-agent … Confirmez-vous la suppression de cet onglet ?
tour 4 > Oui, je confirme la suppression.
       < L'onglet « essai-agent » a bien été supprimé du classeur.
```
Commande, tour par tour :
```bash
o=$(QUESTION="…" python tests/appel_a2a.py); echo "$o"
CTX=$(sed -n 's/.*CONTEXTE=\([^ ]*\).*/\1/p' <<<"$o")
CONTEXTE=$CTX QUESTION="Oui, vas-y." python tests/appel_a2a.py
```
Le journal d'audit du serveur montre chaque action **au nom de l'utilisateur** :
```
2026-10-14T08:25:40Z  delete_sheet          sheets-utilisateur-test@…
2026-10-14T08:25:34Z  write_range           sheets-utilisateur-test@…  essai-agent!A1:B2
2026-10-14T08:25:33Z  add_sheet             sheets-utilisateur-test@…
2026-10-14T08:25:28Z  get_spreadsheet_info  sheets-utilisateur-test@…
```

**Simuler le compte de l'app lui-même.** Le droit ① se donne au compte de l'app, que vous ne pouvez pas utiliser. Pour
le reproduire, créez un compte « simulateur » avec `run.invoker`, comme au projet 09 (guide 12-1-5) :
```bash
gcloud iam service-accounts create ge-simulateur --project=$PROJET
gcloud iam service-accounts add-iam-policy-binding ge-simulateur@$PROJET.iam.gserviceaccount.com \
  --member=user:$(gcloud config get-value account) --role=roles/iam.serviceAccountTokenCreator
gcloud run services add-iam-policy-binding sheets-mcp --region=$REGION --project=$PROJET \
  --role=roles/run.invoker --member=serviceAccount:ge-simulateur@$PROJET.iam.gserviceaccount.com
ID_TOKEN=$(gcloud auth print-identity-token --impersonate-service-account=ge-simulateur@$PROJET.iam.gserviceaccount.com \
  --audiences=$MCP_BASE --include-email)
MCP_URL=$MCP_URL ID_TOKEN=$ID_TOKEN python tests/test_reel.py
```
**Résultat obtenu** (simulateur dans `main-project`, serveur dans `second-project`) : sans le droit, `403` ; avec le droit, `tools/list : 17 outils … OK : test réel terminé`, et l'agent répond normalement. C'est exactement ce que voit le connecteur.

## 5. Ce qu'on regarde dans les journaux

Cloud Run → `sheets-mcp` → **Logs** :

| Filtre | Ce que ça montre |
|---|---|
| `jsonPayload.event="tool_call"` | Qui a appelé quel outil, sur quel classeur et quelle plage. Jamais le contenu des cellules |
| `jsonPayload.event="auth_rejected"` | Un refus : domaine non autorisé, ou e-mail non vérifié |
| `httpRequest.status=401` | Un jeton refusé : audience, portée, ou jeton expiré |
| `httpRequest.status=403` | Un appel sans le droit `run.invoker` (bloqué par Cloud Run, avant le serveur) |

## 6. Le serveur officiel de Google (comparaison)

Testé le même jour : [10-10](10-10-serveur-mcp-sheets-officiel-google.md).
- `initialize` et `tools/list` marchent (6 outils) ;
- les appels d'outils sont refusés sans inscription au Workspace Developer Preview.
