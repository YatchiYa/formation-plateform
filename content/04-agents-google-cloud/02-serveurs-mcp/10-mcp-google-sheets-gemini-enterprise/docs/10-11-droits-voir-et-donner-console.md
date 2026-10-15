# 10-11. Les droits : les voir et les donner dans la console, un par un

**Ce guide répond à :** quels droits le projet 10 utilise-t-il, et pourquoi ? Comment **voir** chacun dans la
console, en lecture seule, sans rien changer ? Comment le **donner** (ou le retirer) en clics, et quelle est la
commande ou la ressource Terraform qui fait la même chose ?

> **Testé en vrai** (14 octobre 2026, projets de test) : tous ces droits ont été donnés par script et par Terraform,
> puis vérifiés par des appels réels. Par exemple, le compte du projet de l'app reçoit `403` sans le droit ①, et passe
> avec. Les écrans sont ceux de la console utilisés au projet 09 et sur l'instance Acme.

---

## 1. Tous les droits, sur une page

Exemple Acme :
- projet des agents : `aiml-gemini-ent-exp-0zga` (n° `433175138344`) ;
- projet de l'app : `acme-gemini-prod` (n° `523307489860`) ;
- compte de l'app : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.

| # | Qui | Rôle | Sur quoi | Pourquoi | Nécessaire pour |
|---|---|---|---|---|---|
| A | `sheets-build-sa` | Storage Object Viewer, Artifact Registry Writer, Logs Writer | projet des agents | Construire les images (Cloud Build) | Déployer |
| B | `sheets-mcp-sa` | **Aucun** | – | Le serveur n'agit qu'avec le jeton de l'utilisateur | – |
| C | `sheets-agent-sa` | Vertex AI User, Logs Writer | projet des agents | L'agent appelle Gemini, écrit ses journaux | Chemin 2 (agent) |
| D | `sheets-agent-sa` | **Cloud Run Invoker** | service `sheets-mcp` **et** `slides-mcp` | L'agent appelle le serveur MCP | Chemin 2 (agent) |
| ①a | compte de l'app | **Cloud Run Invoker** | service `sheets-mcp` **et** `slides-mcp` (si Slides est déployé) | Le connecteur « Custom MCP Server » appelle le serveur | Chemin 1 (connecteur) |
| ①b | compte de l'app | **Cloud Run Invoker** | service `sheets-agent` | L'app appelle l'agent A2A | Chemin 2, A2A |
| ② | compte de l'app | **Discovery Engine Service Agent** | projet des agents | L'app appelle l'agent Agent Runtime | Chemin 2, Agent Runtime |
| E | les utilisateurs (un groupe) | **Agent User** | l'agent, **dans l'app** | Voir et utiliser l'agent dans le chat | Chemin 2 |
| F | l'admin de l'app | Discovery Engine Editor (ou Admin) | projet de l'app | Créer le connecteur et ajouter l'agent | Chemins 1 et 2 |
| G | l'admin de l'organisation | Organization Policy Administrator | projet de l'app | Les règles d'organisation (10-5, étape 2) | Chemin 1 |

**Ce qui n'est PAS un droit IAM :** l'accès aux **classeurs**. Il vient du consentement de chaque utilisateur
(« Autoriser ») et de ses propres partages Drive. Aucun compte de service n'a accès aux Sheets.

## 2. Voir, en lecture seule

### 2.1 Les droits sur un service Cloud Run (D, 1a, 1b)

Projet des agents → 🔎 **Cloud Run** → cliquez sur le service (`sheets-mcp`, puis `sheets-agent`) → onglet
**Security** (*Sécurité*).

**Attendu sur `sheets-mcp` :**
- *Authentication* : **Require authentication** (le service est privé) ;
- dans la liste des droits, une rubrique **Cloud Run Invoker** avec :
  - `sheets-agent-sa@…` (D) ;
  - `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` (①a).

**Attendu sur `sheets-agent` :** **Cloud Run Invoker** avec le compte de l'app (①b).

Autre écran, même information : liste **Cloud Run** → cochez la case du service → **Permissions** (panneau de droite).

En commande, en lecture seule :
```bash
gcloud run services get-iam-policy sheets-mcp --region=europe-west1 --project=aiml-gemini-ent-exp-0zga
gcloud run services get-iam-policy sheets-agent --region=europe-west1 --project=aiml-gemini-ent-exp-0zga
```

### 2.2 Les droits sur le projet (A, C, 2)

Projet des agents → 🔎 **IAM** → onglet **View by principals** (*Afficher par compte principal*).

1. **Cochez « Include Google-provided role grants »** (*Inclure les attributions de rôles fournies par Google*).
   **Sans cette case, le compte de l'app est caché** : c'est un compte de service géré par Google.
2. Filtre : `sheets-` → `sheets-build-sa` (A) et `sheets-agent-sa` (C), avec leurs rôles.
3. Filtre : `gcp-sa-discoveryengine` → le compte de l'app, avec **Discovery Engine Service Agent** (②).

En commande :
```bash
gcloud projects get-iam-policy aiml-gemini-ent-exp-0zga --flatten="bindings[].members" \
  --filter="bindings.members~(sheets-|gcp-sa-discoveryengine)" --format="table(bindings.members,bindings.role)"
```

### 2.3 « Ce compte a-t-il vraiment le droit ? » : Policy Troubleshooter

🔎 **Policy Troubleshooter** (*Outil de dépannage des stratégies*) :
- **Principal** : le compte, par exemple `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` ;
- **Resource** : `//run.googleapis.com/projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/services/sheets-mcp` ;
- **Permission** : `run.routes.invoke`.

→ **Check access**. **Attendu :** **Has access** (*A l'accès*), avec le rôle qui le donne. C'est la réponse sûre :
elle tient compte des groupes, des conditions et des règles héritées.

### 2.4 Dans l'app (E)

Projet de l'app → **Gemini Enterprise** → l'app → **Agents** → l'agent → **User permissions** : la liste des
groupes ou personnes avec **Agent User**.

### 2.5 Les règles d'organisation (G)

Projet de l'app → 🔎 **Organization Policies** → filtrez « custom MCP » : **Disable custom MCP server connector for
Gemini Enterprise** doit être **Not enforced** ; puis « egress » : les 3 domaines (10-5, étape 2).

## 3. Donner, en clics

Faites-le **dans cet ordre**. Après chaque droit, attendez **2 à 3 minutes** avant de tester : c'est le temps de
propagation.

### 3.1 A et C : les rôles des comptes du projet (avant de déployer)

Projet des agents → **IAM** → **Grant access** (*Accorder l'accès*) :
- **New principals** : `sheets-build-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com` ;
- **Role** : **Storage Object Viewer** → **+ Add another role** → **Artifact Registry Writer** → **+ Add another
  role** → **Logs Writer** ;
- **Save**.

Recommencez pour `sheets-agent-sa@…`, avec **Vertex AI User** et **Logs Writer**.

(Les comptes eux-mêmes se créent dans **IAM & Admin → Service Accounts** : [10-4, étape 2](10-4-deployer-console.md#étape-2--les-comptes-de-service).)

### 3.2 D : l'agent peut appeler le serveur MCP

**Cloud Run** → `sheets-mcp` → onglet **Security** → **Add principal**. La fenêtre « *Grant access to "sheets-mcp"* »
s'ouvre :
- **New principals** : `sheets-agent-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com` (une ligne, sans espace) ;
- **Select a role** : tapez `Cloud Run Invoker` → **Cloud Run Invoker** (*Demandeur Cloud Run*). **Pas** *Cloud Run
  Admin*, ni un rôle « ACM… » ;
- pas de condition ;
- **Save**.

**Attendu :** dans la liste, **Cloud Run Invoker (1)** avec `sheets-agent-sa@…`.

### 3.3 Droit 1a : le connecteur peut appeler le serveur MCP

Même écran, sur **`sheets-mcp`** → **Add principal** :
- **New principals** : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` ;
- **Role** : **Cloud Run Invoker** → **Save**.

**Attendu :** **Cloud Run Invoker (2)**, avec `sheets-agent-sa@…` et `service-100000000003@…`.

Ce compte n'existe que si Gemini Enterprise est **activé** dans le projet de l'app (c'est le cas chez Acme).
Sinon, l'enregistrement est refusé avec « … does not exist ».

**Google Slides :** refaites 3.2 et 3.3 sur le service **`slides-mcp`** (même écran, mêmes comptes).

### 3.4 Droit 1b : l'app peut appeler l'agent A2A

**Cloud Run** → **`sheets-agent`** → **Security** → **Add principal** → le compte de l'app → **Cloud Run Invoker** →
**Save**.

### 3.5 Droit 2 : l'app peut appeler l'agent Agent Runtime

Projet des agents → **IAM** → **Grant access** :
- **New principals** : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` ;
- **Role** : tapez `Discovery Engine Service Agent` → **Discovery Engine Service Agent** ;
- **Save**.

**Si ce rôle n'apparaît pas dans la liste** (la console masque parfois les rôles d'agent de service, vu au projet
09), une seule commande :
```bash
gcloud projects add-iam-policy-binding aiml-gemini-ent-exp-0zga --condition=None \
  --role=roles/discoveryengine.serviceAgent \
  --member=serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
```
**Vérifier :** partie 2.2, avec la case « Include Google-provided role grants » cochée.

### 3.6 E : les utilisateurs voient l'agent

Projet de l'app → **Gemini Enterprise** → l'app → **Agents** → l'agent → **User permissions** → **Add** → le groupe
(par exemple `equipe-agents@acme.example`) → rôle **Agent User** → **Save**.

Le connecteur « Google Sheets » (chemin 1) n'a pas besoin de ce droit. Il est disponible pour tous les utilisateurs
de l'app une fois branché (10-5, étape 6).

## 4. Retirer

| Droit | Console | Commande |
|---|---|---|
| D, ①a, ①b | Cloud Run → le service → **Security** → la ligne du compte → icône **corbeille** (*Remove principal*) → **Confirm** | `gcloud run services remove-iam-policy-binding <service> --region=europe-west1 --role=roles/run.invoker --member=serviceAccount:<compte>` |
| A, C, ② | IAM → la ligne du compte → **crayon** (*Edit principal*) → corbeille sur le rôle → **Save** | `gcloud projects remove-iam-policy-binding <projet> --role=<rôle> --member=serviceAccount:<compte> --condition=None` |
| E | App → l'agent → **User permissions** → retirer | – |
| Tout | – | `./scripts/deployer.sh nettoyer` (le projet des agents) |

**Couper l'accès en urgence :** retirez ①a et ①b. L'app ne peut plus rien appeler, avec un effet en 1 à 2 minutes.

## 5. Les mêmes droits par script ou Terraform

| Droit | Script | Terraform (`terraform/main.tf`) |
|---|---|---|
| A, C | `./scripts/deployer.sh preparer` | `google_project_iam_member.build`, `.agent` |
| D | `./scripts/deployer.sh agent` (ou `agent-runtime`) | `google_cloud_run_v2_service_iam_member.mcp` (membre : compte de l'agent) |
| ①a, ①b, ② | `./scripts/deployer.sh droits-app` (affiche le plan, puis confirmation) | `google_cloud_run_v2_service_iam_member.mcp`, `.agent`, `google_project_iam_member.ge_runtime` (si `NUM_APP` est rempli) |
| E, F, G | console seulement | – |

Vous pouvez mélanger les méthodes : par exemple, tout déployer par script et donner ①, ② dans la console pour voir
chaque écran. Le résultat est le même. Évitez seulement de gérer le **même** droit à la fois par Terraform et à la
main : Terraform remettrait son état.
