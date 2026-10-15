# 10-4. Tout déployer dans la console Google Cloud, clic par clic

**Ce guide répond à :** comment faire les mêmes étapes que [10-2](10-2-deployer-shell.md) **dans la console**, en
sachant où cliquer et quoi remplir ?

Un point honnête : la console ne sait pas construire une image à partir d'un dossier de votre poste. **Une seule
commande** reste donc nécessaire, `gcloud builds submit` (étape 3). Elle se lance depuis votre terminal, ou depuis
**Cloud Shell** (bouton `>_` en haut de la console, rien à installer). Tout le reste se fait en clics.

> **Pas encore suivi en vrai** sur ce projet : la facturation du projet de test est fermée. Les écrans sont ceux
> utilisés au projet 09 (12-1-3 et 12-1-6). Les libellés sont donnés en anglais et en français.

---

## Étape 1 : les API

Projet des agents en haut de la console → 🔎 **« API Library »** (*Bibliothèque d'API*). Pour chacune : cherchez
son nom, ouvrez-la, cliquez sur **Enable** (*Activer*) :
- Cloud Run Admin API ;
- Cloud Build API ;
- Artifact Registry API ;
- Identity and Access Management (IAM) API ;
- Google Sheets API ;
- Google Drive API ;
- Vertex AI API ;
- Agent Registry API (facultatif).

**Attendu :** chaque page affiche **Manage** (*Gérer*).

## Étape 2 : les comptes de service

🔎 **IAM & Admin → Service Accounts** (*Comptes de service*) → **+ Create service account**, trois fois :

| Nom | Description | Rôles (écran « Grant this service account access to project ») |
|---|---|---|
| `sheets-build-sa` | Construction des images | **Storage Object Viewer**, **Artifact Registry Writer**, **Logs Writer** |
| `sheets-mcp-sa` | Serveur MCP Google Sheets | **Aucun** → **Done** directement |
| `sheets-agent-sa` | Agent Assistant Google Sheets | **Vertex AI User**, **Logs Writer** |

## Étape 3 : les images (la seule commande)

Dans le dossier du projet 10, ou dans Cloud Shell après y avoir téléversé le dossier (menu ⋮ → **Upload**) :
```bash
P=aiml-gemini-ent-exp-0zga; R=europe-west1
gcloud artifacts repositories create sheets-mcp --repository-format=docker --location=$R --project=$P
for d in mcp_server:mcp-google agent:sheets-agent; do
  gcloud builds submit ${d%%:*} --config=cloudbuild.yaml --substitutions=_IMAGE=$R-docker.pkg.dev/$P/sheets-mcp/${d#*:}:v1 \
    --region=$R --project=$P --service-account=projects/$P/serviceAccounts/sheets-build-sa@$P.iam.gserviceaccount.com
done
```
**Attendu :** chaque construction se termine par `SUCCESS`. Les images sont visibles dans 🔎 **Artifact Registry** →
`sheets-mcp`.

## Étape 4 : le serveur MCP

🔎 **Cloud Run** → **Deploy container** (*Déployer un conteneur*) → **Service** :

| Champ | Valeur |
|---|---|
| Container image URL | **Select** → `sheets-mcp` → `mcp-google:v1` |
| Service name | `sheets-mcp` |
| Region | `europe-west1` |
| Authentication | **Require authentication** (*Exiger l'authentification*) : le service est PRIVÉ |
| Container(s) → **Variables & Secrets** | `PRODUIT` = `sheets` ; `OAUTH_CLIENT_IDS` = l'ID du client OAuth ; `ALLOWED_DOMAINS` = `acme.example` |
| **Security** → Service account | `sheets-mcp-sa` |
| Resources | Memory 512 MiB ; Request timeout 120 |
| Revision scaling | Min 0, Max 5 |

→ **Create**. **Attendu :** l'URL `https://sheets-mcp-433175138344.europe-west1.run.app`, avec une coche verte.

**Google Slides :** refaites cet écran avec la **même image**, le nom **`slides-mcp`** et **`PRODUIT` = `slides`** ([10-13](10-13-serveur-mcp-google-slides.md)).
L'adresse du serveur MCP est cette URL suivie de **`/mcp`**.

## Étape 5 : l'agent A2A

Même écran : **Deploy container** :

| Champ | Valeur |
|---|---|
| Image | `sheets-agent:v1` |
| Service name | `sheets-agent` |
| Authentication | **Require authentication** |
| Variables | `MCP_URL` = `https://sheets-mcp-433175138344.europe-west1.run.app/mcp` ; `AGENT_URL` = `https://sheets-agent-433175138344.europe-west1.run.app` ; `AUTH_ID` = `acces-sheets` ; `MODEL` = `gemini-3.5-flash` ; `GOOGLE_CLOUD_PROJECT` = l'ID du projet |
| Service account | `sheets-agent-sa` |
| Resources | Memory 1 GiB ; Request timeout 300 |
| Revision scaling | Min 0, **Max 1** (les sessions sont en mémoire) |

## Étape 6 : l'agent peut appeler le serveur MCP

🔎 **Cloud Run** → cochez **`sheets-mcp`** → **Permissions** (ou ouvrez le service → onglet **Security**) →
**Add principal** :
- **New principals** : `sheets-agent-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com` ;
- **Role** : **Cloud Run Invoker** (*Demandeur Cloud Run*).

→ **Save**.

## Étape 7 : l'agent sur Agent Runtime (facultatif)

La console ne téléverse pas de code vers Agent Runtime. Utilisez `./scripts/deployer.sh agent-runtime` ([10-2](10-2-deployer-shell.md#5-agent-et-agent-runtime--lagent)),
puis retrouvez l'agent dans 🔎 **Vertex AI → Agent Runtime** (*Agent Engine*) : il s'appelle `sheets-agent`. Copiez
son **Resource name**.

## Étape 8 : Agent Registry (facultatif)

🔎 **Agent Registry** → région `europe-west1` → onglet **MCP servers** → **Add MCP server** :
- Display name `Google Sheets (MCP)`, une description ;
- **Tool specification** : endpoint `https://sheets-mcp-…/mcp`, et collez le contenu de `terraform/toolspec.json`.
  Générez-le d'abord avec `python3 scripts/gen_toolspec.py`. **Import tools** ne marche pas ici, car le serveur est
  privé ;
- **Next** → cochez les 17 outils → **Save**.

## Étape 9 : vérifier

| Où | Ce qu'on doit voir |
|---|---|
| Cloud Run → `sheets-mcp` → **Security** | **Require authentication** ; **Cloud Run Invoker** pour `sheets-agent-sa` (et, plus tard, pour le compte de l'app) |
| Cloud Run → `sheets-mcp` → **Logs** | Au démarrage : `Uvicorn running on http://0.0.0.0:8080` ; à chaque appel : `{"event": "tool_call", "tool": …, "user": …}` |
| Cloud Run → `sheets-agent` → **Logs** | `Application startup complete` |
| Terminal | `curl -s -o /dev/null -w '%{http_code}' -X POST https://sheets-mcp-…/mcp` → `403` |

Ensuite : le branchement sur Gemini Enterprise, [10-5](10-5-gemini-enterprise-connecteur-mcp-natif.md) et
[10-6](10-6-agent-adk-mcp-gemini-enterprise.md).
