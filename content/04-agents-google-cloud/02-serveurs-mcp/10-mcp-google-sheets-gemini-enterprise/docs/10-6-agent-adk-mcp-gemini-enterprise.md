# 10-6. Chemin 2 : un agent ADK qui utilise le serveur MCP (A2A ou Agent Runtime)

**Ce guide répond à :** pourquoi mettre un agent entre Gemini Enterprise et le serveur MCP ? Comment l'agent
transmet-il le jeton de l'utilisateur ? Comment le déployer, créer son autorisation et l'ajouter à l'app, par script
et dans la console ?

> **Testé en vrai (14 octobre 2026)**, sur Cloud Run **et** sur Agent Runtime, avec le vrai Gemini. Les appels
> sont faits comme ceux de Gemini Enterprise (deux en-têtes pour A2A, `authorizations` pour Agent Runtime), y compris
> depuis un compte du projet de l'app :
> - lecture : « Tente : 149 €, stock 30 », « Le stock du Vélo est de 12 » ;
> - écriture et suppression d'onglet, **chacune après demande de confirmation** ;
> - sans jeton : « cliquez sur Autoriser ».
>
> **Pas fait** (il faut une app) : `autorisation` et `ajouter-app`, ni le bouton « Autoriser » réel.

---

> **Sheets et Slides dans le même agent** (outils Slides préfixés `slides_`, autorisation avec la portée `presentations`) : [10-13, partie 6](10-13-serveur-mcp-google-slides.md#6-lagent--sheets-et-slides-ensemble).

## 1. Pourquoi un agent, alors que le connecteur natif existe ?

| | Connecteur natif (10-5) | Agent (ce guide) |
|---|---|---|
| Consignes métier (« rapport de stock hebdomadaire », format, ton) | Non : l'assistant général | **Oui** : l'instruction de l'agent |
| Combiner Sheets avec d'autres outils (Gmail, Drive, une API interne) | Non | **Oui** |
| Model Armor | Celui de l'app, s'il est configuré | Celui de l'app, **plus** le filtre propre à l'agent (`PROMPT_TEMPLATE`, comme au projet 09) |
| Confirmation avant une action destructive | Par l'app (annotations) | Par l'instruction de l'agent (« annonce et demande confirmation ») |
| Code à maintenir | Le serveur seulement | Le serveur et l'agent |

Les deux chemins utilisent **le même serveur** et **le même client OAuth** : vous pouvez faire les deux.

## 2. Comment l'agent passe les deux jetons

`agent/sheets_agent/agent.py` :
```python
def entetes(ctx: ReadonlyContext) -> dict[str, str]:
    """Appelé par ADK avant chaque connexion au serveur MCP."""
    h = {"X-Serverless-Authorization": f"Bearer {jeton_identite(MCP_URL.removesuffix('/mcp'))}"}   # l'AGENT, pour Cloud Run
    if jeton := jeton_utilisateur(ctx):                                                              # l'UTILISATEUR, pour le serveur
        h["Authorization"] = f"Bearer {jeton}"
    return h

tools=[OutilsSheets(connection_params=StreamableHTTPConnectionParams(url=MCP_URL), header_provider=entetes)]
```
- **`jeton_identite`** : le jeton d'identité Google du compte de l'agent (`sheets-agent-sa`). Il vient du serveur de
  métadonnées sur Cloud Run et sur Agent Runtime, et de `gcloud` en local. Il est gardé 45 minutes. Cloud Run le
  vérifie : `sheets-agent-sa` doit avoir `run.invoker` sur `sheets-mcp` (le script le donne).
- **`jeton_utilisateur`** : le jeton OAuth que Gemini Enterprise a confié à l'agent, rangé dans l'état
  `temp:<AUTH_ID>`. Le préfixe `temp:` veut dire qu'il n'est **jamais enregistré**.
  - **A2A :** l'app l'envoie dans l'en-tête `Authorization`, et `agent/main.py` le range dans l'état.
  - **Agent Runtime :** l'app l'envoie dans `authorizations`, et Agent Runtime le range lui-même.
- **`OutilsSheets`** : sans jeton utilisateur, le serveur refuserait même la liste des outils (401). L'agent reçoit
  alors un seul outil, `autorisation_requise`, qui dit de cliquer sur « Autoriser ». C'est vérifié par le test.

## 3. Déployer

| Hébergement | Script | Terraform | Console |
|---|---|---|---|
| A2A (Cloud Run) | `./scripts/deployer.sh agent` | `deploy_agent_cloudrun = true` (par défaut) | [10-4, étape 5](10-4-deployer-console.md#étape-5--lagent-a2a) |
| Agent Runtime | `./scripts/deployer.sh agent-runtime` | `TF_VAR_deploy_agent_runtime=true` | Script seulement (pas de téléversement de code dans la console) |

Dans les deux cas, `sheets-agent-sa` reçoit `run.invoker` sur `sheets-mcp`.

**Ensuite, tout ce qu'il faut pour l'app :**
```bash
./scripts/deployer.sh fiche
```

## 4. L'autorisation OAuth de l'agent

C'est la fiche, dans l'app, qui dit « pour cet agent, demande à l'utilisateur l'accès Sheets, avec ce client OAuth ».

| | A2A | Agent Runtime |
|---|---|---|
| ID de l'autorisation | `acces-sheets` | `acces-sheets-runtime` (doit être **identique** dans l'app) |
| Portées | `openid`, `userinfo.email`, `spreadsheets`, `drive.metadata.readonly` | les mêmes + `cloud-platform` (exigé par Google pour Agent Runtime) |
| Client OAuth | celui de 10-5, étape 1. Son ID doit être dans `OAUTH_CLIENT_IDS` | le même |

**Script** (valeurs de l'app données devant la commande, `client_secret.json` téléchargé depuis l'écran du client OAuth) :
```bash
PROJET_APP=acme-gemini-prod NUM_APP=523307489860 APP_ID=gemini-enterprise-app \
  source scripts/config.sh config/10-mcp.env
./scripts/deployer.sh autorisation ~/Downloads/client_secret_XXX.json a2a        # ou : runtime
```
**Attendu :** `autorisation créée : projects/100000000003/locations/eu/authorizations/acces-sheets`. Le nom affiché
est « Google Sheets » : c'est ce que l'encadré « Autoriser » montrera.

**Console :** l'autorisation se crée **pendant l'ajout** de l'agent (partie 5). Les champs sont dans la fiche.

## 5. Ajouter l'agent dans l'app

**Script :**
```bash
./scripts/deployer.sh droits-app            # droit ① sur sheets-agent (A2A) ; ② sur le projet (Agent Runtime)
./scripts/deployer.sh ajouter-app a2a       # ou : runtime
```
**Attendu :** `ajouté : projects/…/agents/<ID>`. L'agent est ajouté avec :
- son autorisation ;
- 2 questions proposées ;
- la langue `fr`.

Il n'y a pas de doublon : relancé, le script dit `déjà dans l'app : …`.

**Les droits dans la console** (au lieu de `droits-app`) :
- ① sur `sheets-agent` (A2A) : [10-11, partie 3.4](10-11-droits-voir-et-donner-console.md#34-droit-1b--lapp-peut-appeler-lagent-a2a) ;
- ② sur le projet (Agent Runtime) : [10-11, partie 3.5](10-11-droits-voir-et-donner-console.md#35-droit-2--lapp-peut-appeler-lagent-agent-runtime) ;
- les voir en lecture seule : [10-11, partie 2](10-11-droits-voir-et-donner-console.md#2-voir-en-lecture-seule).

**Console, agent A2A** (comme au projet 09, guide 12-1-8, partie 5.7) :
1. Projet de l'app → **Gemini Enterprise** → l'app → **Agents** → **+ Add agent** → **Custom agent via A2A** → **Add**.
2. Collez **toute** la carte (une ligne, venue de `fiche` ou de `python3 agent/carte.py $AGENT_URL`) → **Preview
   agent details**. **Attendu :** `sheets_agent`, 2 compétences.
3. **Authentication** : **ne cliquez pas sur Skip**. Remplissez les champs de la fiche :
   - nom `acces-sheets` ;
   - Client ID et secret ;
   - Authorization URL (une seule ligne, avec `access_type=offline&prompt=consent`) ;
   - Token URL `https://oauth2.googleapis.com/token` ;
   - les portées ;
   - PKCE et HTTP Basic **décochés**.

   → **Finish**.
4. Nom : l'agent → **Edit** → `Assistant Google Sheets (A2A)`.

**Console, agent Agent Runtime :**
1. **+ Add agent** → **Custom agent via Agent Runtime** → **Authorizations** → **Add authorization** : nom
   `acces-sheets-runtime`, portées avec `cloud-platform`.
2. **Next** → nom `Assistant Google Sheets`, la description, le **chemin** (`projects/…/reasoningEngines/…`) →
   **Create**.

**Puis, dans les deux cas :** l'agent → **User permissions** → **Add** → votre groupe → **Agent User** → **Save**.

## 6. Le test dans le chat

| Demande | Attendu |
|---|---|
| « Trouve le classeur Ventes 2026 et résume l'onglet Ventes » | 1re fois : encadré **Authorize** (« Google Sheets ») → consentement → le résumé |
| « Ajoute la ligne Sac à dos, 39 € dans Ventes, puis trie par prix » | L'agent annonce le fichier et la plage, **demande confirmation**, puis le fait et donne le lien |
| « Supprime l'onglet Archive » | Annonce, puis confirmation, puis suppression (outil destructif) |
| Une demande avant d'avoir autorisé | « cliquez sur Autoriser » (outil `autorisation_requise`) |

Pour tester avant l'app, comme l'app le fait : `./scripts/deployer.sh tester` ([10-8](10-8-tester-simuler-verifier.md)).

## 7. Si ça bloque

| Symptôme | Cause → solution |
|---|---|
| L'agent dit toujours « cliquez sur Autoriser », même après | A2A : agent ajouté sans autorisation (Skip). Agent Runtime : nom de l'autorisation ≠ `acces-sheets-runtime` |
| Erreur 401 dans les journaux de l'agent, côté MCP | L'ID du client OAuth de l'autorisation n'est pas dans `OAUTH_CLIENT_IDS` du serveur MCP |
| Erreur 403 à l'appel du serveur MCP | `sheets-agent-sa` n'a pas `run.invoker` sur `sheets-mcp` (relancer `agent` ou `agent-runtime`) |
| « The agent couldn't respond » dans l'app | Droit ① ou ② manquant pour le compte de l'app : `droits-app` |
| `part_metadata parameter is only supported…` | Déjà corrigé dans l'agent (`GOOGLE_GENAI_USE_ENTERPRISE`, comme au projet 09) |
