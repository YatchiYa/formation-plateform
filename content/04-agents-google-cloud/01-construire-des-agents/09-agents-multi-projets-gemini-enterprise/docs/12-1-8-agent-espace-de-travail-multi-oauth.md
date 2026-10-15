# 12-1-8. Agent « Espace de travail » : Gmail, Agenda, Drive, Google Sheets sans suppression ; un ou plusieurs fournisseurs OAuth

**Ce guide répond à :**
1. Je veux **un agent** qui lit les **e-mails**, l'**agenda** et le **Drive** de l'utilisateur, et qui **lit et modifie
   ses Google Sheets** comme dans Sheets. Il ne doit **jamais pouvoir supprimer** quoi que ce soit.
2. Comment le déployer et l'ajouter à l'app Gemini Enterprise avec **un seul fournisseur** d'identifiants (Google) ?
3. Et avec **plusieurs** fournisseurs, par exemple **Google + Atlassian** (Jira, Confluence) ?

**À lire avant :** [12-1-1](12-1-1-deployer-agents-shell.md) (déployer un agent), [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md)
(les droits de l'app), [12-1-7](12-1-7-agents-oauth-identite-outils.md) (comment marche OAuth dans Gemini Enterprise).

> **Testé ici :**
> - les outils, avec des réponses de Google simulées. Sheets : écrire, ajouter des lignes, modifier la structure. Les
>   suppressions sont refusées **avant** tout appel à Google : `deleteSheet`, `deleteDimension`, `updateCells`, vider
>   une cellule remplie, `repeatCell` sur les valeurs ;
> - l'agent complet en A2A, en local, avec le vrai modèle Gemini. À « Supprime l'onglet Archives », il répond qu'il ne
>   peut pas et propose de **masquer** l'onglet. Avec un jeton refusé, il demande de cliquer sur « Autoriser » ;
> - le choix du jeton quand il y a deux autorisations (`acces-google,acces-atlassian`) ;
> - le corps envoyé à l'app par `add_agent_to_ge.sh`, et le calcul Terraform : deux autorisations pour Agent Runtime ;
>   refus pour A2A.
>
> **Pas encore testé en vrai :** les appels réels à Gmail, Agenda, Drive, Sheets et Atlassian. Il faut un vrai
> utilisateur qui clique sur « Autoriser » dans votre app. C'est le test de la partie 5.8.

---

## Sommaire

0. [L'agent en 1 minute](#0-lagent-en-1-minute)
1. [Ce qu'il sait faire, et ce qu'il ne fera jamais](#1-ce-quil-sait-faire-et-ce-quil-ne-fera-jamais)
2. [Pourquoi il ne peut rien supprimer](#2-pourquoi-il-ne-peut-rien-supprimer)
3. [Un fournisseur ou plusieurs : quel hébergement ?](#3-un-fournisseur-ou-plusieurs--quel-hébergement)
4. [Préparer : copier les fichiers, tester en local](#4-préparer--copier-les-fichiers-tester-en-local)
- 4 bis. [La voie scriptée, de bout en bout](#4-bis-la-voie-scriptée-de-bout-en-bout)
5. [Cas A : un seul fournisseur (Google), étape par étape](#5-cas-a--un-seul-fournisseur-google-étape-par-étape)
6. [Cas B : plusieurs fournisseurs (Google + Atlassian)](#6-cas-b--plusieurs-fournisseurs-google--atlassian)
7. [Les mêmes étapes par script ou Terraform](#7-les-mêmes-étapes-par-script-ou-terraform)
8. [Simuler avant l'app](#8-simuler-avant-lapp)
9. [Sécurité](#9-sécurité)
10. [Si ça bloque](#10-si-ça-bloque)
11. [Ajouter un outil plus tard](#11-ajouter-un-outil-plus-tard)
12. [Soigner l'expérience : encadré « Autoriser », nom, icône, questions](#12-soigner-lexpérience--encadré-autoriser-nom-icône-questions)
13. [Le client OAuth : projet des agents ou projet de l'app ?](#13-le-client-oauth--projet-des-agents-ou-projet-de-lapp-)

---

## 0. L'agent en 1 minute

```
Utilisateur (chat Gemini Enterprise)
   │ 1re fois : bouton « Autoriser » → fenêtre Google (et Atlassian) → il accepte
   ▼
App Gemini Enterprise (projet de l'app) ── garde le jeton de l'utilisateur, l'envoie à chaque appel
   ▼
Agent « Espace de travail » (projet des agents : Cloud Run A2A ou Agent Runtime)
   │ commun.jeton_utilisateur(...) : le jeton de L'UTILISATEUR (jamais celui de l'agent)
   ▼
Gmail · Agenda · Drive · Sheets (Google)   +   Jira · Confluence (Atlassian, option)
```

- **Où est le code :**
  - `agents/trio/workspace_agent/agent.py` ;
  - la clé `workspace` dans `agents/trio/catalogue.json` (nom affiché : « Espace de travail »).
- **Les droits :** ce sont ceux de l'utilisateur. L'agent ne voit que ce que l'utilisateur voit, et ne fait que ce
  que les portées et le code lui permettent (partie 2).

## 1. Ce qu'il sait faire, et ce qu'il ne fera jamais

| Outil | Fait | Service, portée |
|---|---|---|
| `qui_suis_je` | Nom et e-mail de l'utilisateur ; Atlassian autorisé ou non | Drive (`drive.readonly`) |
| `gmail_chercher` | Liste d'e-mails (filtre Gmail : `is:unread`, `from:…`, `newer_than:7d`…) | `gmail.readonly` |
| `gmail_lire` | Texte complet d'un e-mail | `gmail.readonly` |
| `agenda_evenements` | Réunions d'une période (agenda principal) | `calendar.events.readonly` |
| `drive_chercher` | Fichiers par mots (nom ou contenu), ou les plus récents | `drive.readonly` |
| `drive_lire` | Texte d'un Google Docs, Slides ou d'un fichier texte | `drive.readonly` |
| `sheets_infos` | Titre, lien, onglets (nom, `sheetId`, taille) | `spreadsheets` |
| `sheets_lire` | Valeurs d'une plage (`Ventes!A1:F50`, ou un onglet entier) | `spreadsheets` |
| `sheets_creer` | Nouveau classeur, avec ses onglets | `spreadsheets` |
| `sheets_ecrire` | Valeurs ou formules (`=SUM(B2:B9)`) dans une plage ; renvoie les anciennes valeurs | `spreadsheets` |
| `sheets_ajouter_lignes` | Lignes à la fin des données (n'écrase rien) | `spreadsheets` |
| `sheets_modifier` | Mise en forme et structure, toute l'API Sheets **sans suppression** : nouvel onglet, renommer, figer, gras, couleurs, bordures, fusion, largeur, insérer des lignes ou colonnes, trier, validation, mise en forme conditionnelle, filtre, graphique, plage nommée, protection… | `spreadsheets` |
| `jira_chercher` | Tickets Jira (requête JQL ; par défaut : mes tickets ouverts) | Atlassian `read:jira-work` |
| `confluence_chercher` | Pages Confluence | Atlassian `search:confluence` |

**Jamais :**
- supprimer ou vider quoi que ce soit : onglet, ligne, colonne, cellule, plage, classeur, fichier, e-mail, événement ;
- envoyer un e-mail ;
- créer ou modifier une réunion ;
- modifier un fichier Drive autre qu'un classeur ;
- écrire dans Jira ou Confluence.

Si on lui demande de supprimer, il le dit et propose autre chose : masquer, insérer à côté, ou laisser l'utilisateur
le faire (testé).

## 2. Pourquoi il ne peut rien supprimer

Deux protections, l'une derrière l'autre.

**1) Les portées OAuth (protection de Google, inviolable).**

| Portée demandée | Ce que Google autorise | Supprimer ? |
|---|---|---|
| `gmail.readonly` | Lire les e-mails | **Impossible** (Google refuse : 403) |
| `calendar.events.readonly` | Lire les événements | **Impossible** |
| `drive.readonly` | Lire les fichiers Drive | **Impossible**, même pour un classeur |
| `spreadsheets` | Lire et modifier **le contenu** des classeurs de l'utilisateur | Le fichier : **impossible** (il faudrait une portée Drive en écriture). Le contenu (lignes, onglets…) : **possible pour Google**, voir 2) |

Google n'a **pas** de portée « Sheets sans suppression ». C'est donc le code qui bloque.

**2) Le code de l'agent (protection de l'agent).**
- **Aucun outil ne supprime.** Il n'y a pas de `sheets_supprimer`. Le modèle ne peut appeler que les outils de la
  liste.
- **`sheets_ecrire`** lit d'abord la plage. Si une valeur vide remplacerait une cellule remplie, il **refuse** sans
  rien écrire. Remplacer une valeur par une autre reste permis : c'est une modification. L'agent montre l'avant et
  l'après, demande confirmation, et l'outil renvoie les anciennes valeurs.
- **`sheets_modifier`** n'accepte que des requêtes de la liste `AUTORISEES`, définie dans le code (`add…`, `insert…`,
  `repeatCell` limité à la mise en forme…). Il refuse :
  - `delete…` et `clear…` ;
  - `updateCells`, `cutPaste`, `copyPaste`, `pasteData`, `findReplace`, `autoFill` ;
  - `trimWhitespace`, `randomizeRange`, `textToColumns`.

  Toutes ces requêtes peuvent effacer ou écraser des données. Le refus a lieu **avant** l'appel à Google (testé).
- **Filet de sécurité :** toute modification est dans **Fichier → Historique des versions** du classeur.

> Le bouton « Autoriser » n'accorde que ces portées. L'agent est **techniquement incapable** d'envoyer un e-mail ou de
> supprimer un fichier. Ce n'est pas une simple consigne donnée au modèle.

## 3. Un fournisseur ou plusieurs : quel hébergement ?

Une **autorisation** est une fiche dans l'app : un client OAuth, ses portées, un ID. Il en faut **une par
fournisseur**. Une seule autorisation Google couvre Gmail, Agenda, Drive et Sheets : les portées s'additionnent dans
la même fenêtre de consentement.

| Besoin | A2A (Cloud Run) | Agent Runtime |
|---|---|---|
| Un fournisseur (Google) | ✅ **1 autorisation par agent** | ✅ |
| Plusieurs (Google + Atlassian) | ❌ un seul jeton possible | ✅ **une liste d'autorisations** (une par outil ou fournisseur) |

**Pourquoi :**
- en **A2A**, l'app envoie **un** jeton, dans l'en-tête `Authorization` (`agentAuthorization`, au singulier) ;
- sur **Agent Runtime**, elle envoie un jeton **par autorisation** (`toolAuthorizations`, une liste). Chacun est rangé
  dans l'état de session sous `temp:<ID de l'autorisation>`.

**Avec plusieurs fournisseurs en A2A,** il faut **deux agents** : « Espace Google (A2A) » et « Jira (A2A) », chacun avec
son autorisation. Le chat de Gemini Enterprise passe de l'un à l'autre.

**Comment l'agent trouve le bon jeton** (`commun.jeton_utilisateur`) :
- `AUTH_ID` contient la liste des ID, séparés par des virgules : `acces-google,acces-atlassian` ;
- les outils Google prennent le jeton du **1er** ID. **Mettez donc l'autorisation Google en premier** ;
- les outils Atlassian prennent le jeton de l'ID **qui contient le mot `atlassian`**. **Nommez donc l'autorisation
  Atlassian avec ce mot.**

## 4. Préparer : copier les fichiers, tester en local

**Fichiers à copier du dépôt vers votre poste** (même chemin) :

| Fichier | Nouveau ou modifié | Utile pour |
|---|---|---|
| `agents/trio/workspace_agent/__init__.py` | nouveau (1 ligne : `from . import agent`) | tout |
| `agents/trio/workspace_agent/agent.py` | nouveau | tout |
| `agents/trio/catalogue.json` | modifié (entrée `workspace` ; remplacer tout le fichier) | tout |
| `agents/trio/commun.py` | modifié (`jeton_utilisateur(…, fournisseur)`) | tout |
| `01-bis-cloud-run-a2a/main.py` | modifié (A2A : 1re autorisation de la liste) | A2A |
| `scripts/add_agent_to_ge.sh` | modifié (plusieurs autorisations) | ajout par script |
| `scripts/register_agent.sh`, `01-bis-cloud-run-a2a/terraform/main.tf`, `02-bis-agent-runtime/terraform/main.tf` | modifiés (idem) | Terraform |
| `scripts/simuler_gemini_enterprise.sh` | modifié (idem) | simulation |
| `scripts/test_trio.py` | modifié (tests du nouvel agent) | test local |
| `scripts/deployer_shell.sh`, `scripts/fiche_ge.py` (nouveau) | actions `oauth` et `carte` | voie scriptée (4 bis) |
| `scripts/autorisation_oauth.sh`, `scripts/personnaliser_agent.sh` (nouveau) | nom affiché ; personnaliser l'agent | partie 12 |
| `01-bis-…/terraform/outputs.tf`, `02-bis-…/terraform/outputs.tf` | sortie `oauth` (+ API activées dans `main.tf`) | Terraform |

**Tester en local** (dossier du projet, `.venv` activé) :
```bash
python scripts/test_trio.py
```
**Attendu :** `tests trio OK (9 scénarios, 8 agents)`.

## 4 bis. La voie scriptée, de bout en bout

Les parties 5 et 6 montrent chaque clic. Tout ce qui peut l'être est aussi **scripté**. Il reste deux gestes
manuels :
- le **client OAuth** : Google ne publie pas d'API pour le créer. C'est 2 minutes dans la console, et le lien est
  affiché par le script ;
- si l'admin Google Workspace l'exige, son **approbation**.

**Côté projet des agents** (fichier de config chargé, rien à y modifier) :

```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
./scripts/deployer_shell.sh oauth workspace                                   # 1. API Google de l'agent + portées + lien du client OAuth
#    → créer le client OAuth (lien affiché) : Application Web, les 2 URI de redirection, noter ID et secret
AGENTS_OAUTH="workspace=acces-google" ./scripts/deployer_shell.sh cloudrun workspace   # 2. déployer (ou : runtime)
./scripts/deployer_shell.sh tester workspace                                  # 3. 3 à 5 min après : « cliquez sur Autoriser » = normal
AGENTS_OAUTH="workspace=acces-google" CLIENT_ID=<ID client> \
  ./scripts/deployer_shell.sh carte workspace                                 # 4. LA FICHE : tout ce qu'il faut coller dans l'app
```

**Ce que `oauth` affiche** (résultat réel sur le projet de test, agent `courriels`) :
```
== courriels
▶ gcloud services enable gmail.googleapis.com --project=…
  portées (A2A)           : https://www.googleapis.com/auth/gmail.readonly
  portées (Agent Runtime) : https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/cloud-platform
Client OAuth (une fois, console, 2 min) : https://console.cloud.google.com/auth/clients?project=…
```

**Ce que `carte` affiche** (résultat réel, extrait) :
```
================ courriels : Rapport e-mails ================
Description (à coller) : Lit les e-mails de l'utilisateur connecté (Gmail, lecture seule) et en fait un rapport clair…
[A2A sur Cloud Run]  https://courriels-a2a-shell-….europe-west1.run.app
  1. Carte (fichier carte-courriels.json), TOUTE la ligne ci-dessous, du 1er { au dernier } :
     {"protocolVersion": "0.3", "name": "courriels_agent", …}
  2. Nom : Rapport e-mails (A2A)
  3. Authentication (ne PAS cliquer Skip) :
      Nom de l'autorisation  : acces-gmail
      Authorization URL      : https://accounts.google.com/o/oauth2/auth?client_id=…&access_type=offline&prompt=consent
      Token URL              : https://oauth2.googleapis.com/token
      Scopes                 : https://www.googleapis.com/auth/gmail.readonly
      PKCE / HTTP Basic      : décochés
Questions proposées (starter prompts) : Fais-moi un rapport sur mes e-mails de la semaine. | …
Droits de l'app : ① roles/run.invoker sur le service courriels-a2a-shell
```
Pour un agent Agent Runtime, la fiche donne le **chemin de ressource** à coller, et une autorisation par ID, avec
`cloud-platform`. `carte` sans clé affiche la fiche de tous les agents de `AGENTS`.

**Côté app** : deux façons.
- **Console :** suivez la fiche, puis la [partie 5](#5-cas-a--un-seul-fournisseur-google-étape-par-étape), étape 7 (5.9 pour Agent Runtime).
- **Scripts :** les valeurs de l'app sont données devant les commandes. Le fichier de config n'est pas modifié.
  ```bash
  export PROJET_APP=acme-gemini-prod NUM_APP=523307489860 GE_LOCATION=eu
  export GE_PROJECT=$PROJET_APP GE_APP=gemini-enterprise-app
  ./scripts/autorisation_oauth.sh create acces-google ~/Downloads/client_secret_XXX.json \
    "<les portées affichées par oauth>" "Google Workspace (lecture, Sheets)"          # l'autorisation, avec un nom lisible
  AUTH_ID=acces-google ./scripts/add_agent_to_ge.sh a2a carte-workspace.json "Espace de travail (A2A)"   # + droit run.invoker
  ./scripts/personnaliser_agent.sh "Espace de travail (A2A)" workspace              # questions proposées, texte, langue (partie 12)
  ```
  Pour Agent Runtime : `AUTH_ID=acces-google,acces-atlassian ./scripts/add_agent_to_ge.sh adk <chemin> "Espace de travail"`.

**Terraform** ([12-1-2](12-1-2-deployer-agents-terraform.md)) :
- mettez `AGENTS="workspace"` et `AGENTS_OAUTH="workspace=acces-google"` dans le fichier, puis `terraform apply` ;
- Terraform active **aussi** les API Google de l'agent (catalogue, `oauth.apis`) ;
- deux sorties à lire après l'apply :
  - `terraform output cards` : la carte de chaque agent ;
  - `terraform output oauth` : les autorisations attendues et les portées.
- avec `PUBLIER=oui`, l'agent est ajouté à l'app **avec** son autorisation. Créez-la avant, avec
  `autorisation_oauth.sh create`.

**D'où viennent les API et les portées :** le bloc `"oauth"` de l'agent dans `agents/trio/catalogue.json`. Un nouvel
agent OAuth ? Ajoutez ce bloc, et tous les scripts et Terraform le suivent.
```json
"oauth": {"apis": ["gmail.googleapis.com"], "portees": ["https://www.googleapis.com/auth/gmail.readonly"]}
```

## 5. Cas A : un seul fournisseur (Google), étape par étape

C'est le chemin suivi avec l'agent `courriels` sur l'instance Acme, appliqué à l'agent `workspace`. Il y a
8 étapes, et pour chacune **la console** (les clics) et **le script** (la commande). Les deux mènent au même
résultat : prenez l'un ou l'autre, étape par étape.

Les valeurs utilisées :
- projet des agents `aiml-gemini-ent-exp-0zga` (n° `433175138344`), région `europe-west1` ;
- projet de l'app `acme-gemini-prod` (n° `523307489860`), app `gemini-enterprise-app` en `eu` ;
- compte de l'app : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.

| Étape | Où | Console | Script |
|---|---|---|---|
| 1. Fichiers, test local | votre poste | – | `python scripts/test_trio.py` |
| 2. Client OAuth | projet des agents | ✅ (seule voie) | – (pas d'API Google pour ça) |
| 3. API Google | projet des agents | ✅ | `deployer_shell.sh oauth workspace` |
| 4. Déployer | projet des agents | ✅ (12-1-3) | `deployer_shell.sh cloudrun workspace` |
| 5. Droit de l'app | projet des agents | ✅ | `gcloud run services add-iam-policy-binding …` |
| 6. Carte et URL d'autorisation | votre poste | – | `deployer_shell.sh carte workspace` |
| 7. Ajouter dans l'app | projet de l'app | ✅ | `autorisation_oauth.sh` + `add_agent_to_ge.sh` |
| 8. Tester | le chat | ✅ | – |

**Agent Runtime** au lieu de Cloud Run : les étapes 4 à 7 changent un peu, voir [5.9](#59-variante-agent-runtime).

### 5.1 Étape 1 : copier les fichiers, tester en local

Copiez les fichiers de la [partie 4](#4-préparer--copier-les-fichiers-tester-en-local) du PC vers le Mac, au même
chemin. Le minimum pour cet agent :

| Fichier | Action |
|---|---|
| `agents/trio/workspace_agent/__init__.py` | nouveau dossier `workspace_agent`, nouveau fichier (1 ligne : `from . import agent`) |
| `agents/trio/workspace_agent/agent.py` | nouveau fichier |
| `agents/trio/catalogue.json` | **remplacer tout le fichier** (entrées `courriels` et `workspace`, blocs `oauth`) |
| `agents/trio/commun.py` | remplacer (`jeton_utilisateur(…, fournisseur)`) |
| `01-bis-cloud-run-a2a/main.py` | remplacer |
| `scripts/deployer_shell.sh`, `scripts/fiche_ge.py` | remplacer, et nouveau (actions `oauth` et `carte`) |

Vérifier sur le Mac (dossier du projet, `.venv` activé) :
```bash
python scripts/test_trio.py
```
**Attendu :** `tests trio OK (9 scénarios, 8 agents)`. Sans le nouveau `test_trio.py`, le nombre d'agents est plus
petit : c'est normal.

### 5.2 Étape 2 : le client OAuth (console, projet des agents)

Le client OAuth se crée dans le **projet des agents**. En production, seul l'ajout de l'agent touche l'app (choix
expliqué en [partie 13](#13-le-client-oauth--projet-des-agents-ou-projet-de-lapp-)). Vous avez déjà un client pour
`courriels` ? **Réutilisez-le** : ce sont les portées de l'URL d'autorisation (étape 6) qui changent, pas le client.

**Console :**
1. En haut, projet **`aiml-gemini-ent-exp-0zga`** → 🔎 **« Google Auth Platform »**.
2. S'il n'est pas encore configuré :
   - **Commencer** → nom de l'application `Agents Acme` → votre e-mail ;
   - Audience : **Interne** (comptes Acme seulement) ;
   - **Créer**.
3. **Clients** → **+ Créer un client** → type **Application Web** → nom `ge-workspace`.
4. **URI de redirection autorisés** → **+ Ajouter un URI**, deux fois, ces deux-là exactement :
   ```
   https://vertexaisearch.cloud.google.com/oauth-redirect
   https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
   ```
5. **Créer** → notez l'**ID client** (`…apps.googleusercontent.com`) et le **code secret**. Ne les mettez dans aucun
   fichier du projet, ni dans un e-mail.
6. (Conseillé) **Accès aux données** → **Ajouter ou supprimer des niveaux d'accès** → cochez `gmail.readonly`,
   `calendar.events.readonly`, `drive.readonly`, `spreadsheets` → **Mettre à jour** → **Enregistrer**. La fenêtre
   Google les affichera en clair.

**Script :** aucun. Google ne publie pas d'API pour créer ce client. L'étape 3 affiche le lien direct vers cet écran.

### 5.3 Étape 3 : activer les API Google (projet des agents)

Les appels de l'agent à Gmail, Agenda, Drive et Sheets sont comptés sur le projet **du client OAuth**. Ces 4 API
doivent y être actives.

**Console :** projet `aiml-gemini-ent-exp-0zga` → 🔎 **« Bibliothèque d'API »**. Pour chacune, cherchez son nom →
cliquez dessus → **Activer** :
- **Gmail API** ;
- **Google Calendar API** ;
- **Google Drive API** ;
- **Google Sheets API**.

**Attendu :** chaque page affiche **Gérer** (au lieu d'**Activer**) et « API activée ».

**Script :**
```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
./scripts/deployer_shell.sh oauth workspace
```
**Attendu** (forme réelle, testée avec `courriels`) :
```
== workspace
▶ gcloud services enable gmail.googleapis.com calendar-json.googleapis.com drive.googleapis.com sheets.googleapis.com --project=aiml-gemini-ent-exp-0zga
Operation "operations/…" finished successfully.
  portées (A2A)           : https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.events.readonly …
  portées (Agent Runtime) : … https://www.googleapis.com/auth/cloud-platform
  AGENTS_OAUTH            : (aucune : mettre AGENTS_OAUTH="workspace=acces-workspace" devant cloudrun / runtime / carte)
Client OAuth (une fois, console, 2 min) : https://console.cloud.google.com/auth/clients?project=aiml-gemini-ent-exp-0zga
```
Ou seulement les API : `gcloud services enable gmail.googleapis.com calendar-json.googleapis.com drive.googleapis.com sheets.googleapis.com --project=aiml-gemini-ent-exp-0zga`.

### 5.4 Étape 4 : déployer l'agent sur Cloud Run

**Script** (le plus simple). Vous n'avez pas à modifier le fichier de config : la valeur OAuth est donnée juste pour
cette commande.
```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
AGENTS_OAUTH="workspace=acces-google" ./scripts/deployer_shell.sh cloudrun workspace
```
**Attendu :**
- la ligne `autorisation OAuth : AUTH_ID=acces-google` ;
- puis `Service URL: https://workspace-a2a-shell-433175138344.europe-west1.run.app`.

**Attendez 3 à 5 minutes**, puis :
```bash
./scripts/deployer_shell.sh tester workspace
```
**Attendu :** l'agent répond qu'il faut cliquer sur « Autoriser ». C'est **normal** : le test n'envoie pas de jeton
utilisateur. Seule l'app en enverra un.

**Terraform** : `AGENTS="… workspace"` (la liste **complète** de ce qui doit exister) et
`AGENTS_OAUTH="workspace=acces-google"` dans le fichier, recharger, puis `terraform plan` dans
`01-bis-cloud-run-a2a/terraform`. Le plan doit montrer **seulement** des lignes `["workspace"]`, plus les 4 API
(`google_project_service.agents[…]`) → `terraform apply` ([12-1-2, partie 9](12-1-2-deployer-agents-terraform.md#9-ajouter-retirer-modifier-un-agent)).
Le service s'appelle alors `workspace-a2a`, sans `-shell`.

**Console** : l'image se construit forcément depuis le terminal (Cloud Build) ; le service, ensuite, se crée en clics.
Voir [12-1-3](12-1-3-deployer-agents-console.md). Ajoutez aux variables `AUTH_ID` = `acces-google`.

### 5.5 Étape 5 : le droit de l'app sur ce service (projet des agents)

C'est le droit ①, comme pour `meteo` et `courriels`. Le droit ② (sur le projet) est déjà en place : rien à refaire.

**Console :**
1. Projet `aiml-gemini-ent-exp-0zga` → 🔎 **Cloud Run** → cochez le service **`workspace-a2a-shell`** → en haut,
   **Autorisations** (ou : ouvrir le service → onglet **Sécurité**).
2. **Ajouter un compte principal** :
   - **Nouveaux comptes principaux** : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`
     (une ligne, sans espace) ;
   - **Rôle** : tapez `Cloud Run Invoker` → **Demandeur Cloud Run** (*Cloud Run Invoker*). Pas *Cloud Run Admin*.
3. **Enregistrer**.

**Attendu :** dans la liste, une rubrique **Cloud Run Invoker** avec `service-100000000003@gcp-sa-discoveryengine…`.

**Script :**
```bash
gcloud run services add-iam-policy-binding workspace-a2a-shell \
  --region=europe-west1 --project=aiml-gemini-ent-exp-0zga --role=roles/run.invoker \
  --member=serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
```
**Attendu :** `Updated IAM policy for service [workspace-a2a-shell].` Ou, avec les valeurs de l'app dans la
configuration : `./scripts/connecter_app.sh droits workspace` (affiche le plan, demande de taper l'ID du projet).

Attendez **2 à 3 minutes** que le droit s'applique.

### 5.6 Étape 6 : la carte de l'agent et l'URL d'autorisation

**Script** (recommandé) : une seule commande donne **tout** ce qu'il faut coller à l'étape 7. Mettez votre ID client
à la place de `<ID client>` :
```bash
AGENTS_OAUTH="workspace=acces-google" CLIENT_ID=<ID client> ./scripts/deployer_shell.sh carte workspace
```
**Attendu** (forme réelle, testée avec `courriels`) :
```
================ workspace : Espace de travail ================
Description (à coller) : Lit les e-mails, l'agenda et le Drive de l'utilisateur connecté, lit et modifie ses Google Sheets…
[A2A sur Cloud Run]  https://workspace-a2a-shell-433175138344.europe-west1.run.app
  1. Carte (fichier carte-workspace.json), TOUTE la ligne ci-dessous, du 1er { au dernier } :
     {"protocolVersion": "0.3", "name": "workspace_agent", …}
  2. Nom : Espace de travail (A2A)
  3. Authentication (ne PAS cliquer Skip) :
      Nom de l'autorisation  : acces-google
      Authorization URL      : https://accounts.google.com/o/oauth2/auth?client_id=…&access_type=offline&prompt=consent
      Token URL              : https://oauth2.googleapis.com/token
      Scopes                 : https://www.googleapis.com/auth/gmail.readonly … https://www.googleapis.com/auth/spreadsheets
      PKCE / HTTP Basic      : décochés
```

**À la main**, si vous préférez :
1. La carte (le format attendu par Google) :
   ```bash
   python3 scripts/carte_a2a.py workspace https://workspace-a2a-shell-433175138344.europe-west1.run.app > carte-workspace.json
   cat carte-workspace.json
   ```
   **Attendu :** une seule longue ligne, qui commence par `{"protocolVersion": "0.3", "name": "workspace_agent", …`.
   **Pas** la carte servie par l'agent (`/.well-known/agent-card.json`) : elle a des champs en plus, et Gemini
   Enterprise la refuse. `KeyError: 'workspace'` = `catalogue.json` pas à jour (étape 1).
2. L'URL d'autorisation : remplacez `TON_CLIENT_ID` ; tout tient sur **une seule ligne** :
   ```
   https://accounts.google.com/o/oauth2/auth?client_id=TON_CLIENT_ID&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fgmail.readonly%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.events.readonly%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive.readonly%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fspreadsheets&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent
   ```
   `access_type=offline` et `prompt=consent` sont **obligatoires** : sans eux, Google refuse l'autorisation.

### 5.7 Étape 7 : ajouter l'agent dans l'app (projet de l'app)

**Console** (comme pour `meteo`, avec l'étape Authentication en plus) :
1. En haut, projet **`acme-gemini-prod`** → 🔎 **« Gemini Enterprise »** → l'app → **Agents** →
   **+ Add agent**.
2. Tuile **Custom agent via A2A** → **Add**.
3. Collez **toute** la ligne de la carte (étape 6) → **Preview agent details**.
   **Attendu :** nom `workspace_agent`, la description, 3 compétences (« Synthèse e-mails, agenda, Drive »,
   « Google Sheets », « Jira et Confluence »). → **Next**.
4. Étape **Authentication** : **ne cliquez pas sur Skip**. Remplissez :

   | Champ | Valeur |
   |---|---|
   | Nom / ID de l'autorisation | `acces-google` : lisible, car il s'affiche dans l'encadré « Autoriser » ([partie 12](#12-soigner-lexpérience--encadré-autoriser-nom-icône-questions)) |
   | Client ID | l'ID client (étape 2) |
   | Client secret | le code secret (étape 2) |
   | Authorization URL | l'URL de l'étape 6 (une seule ligne) |
   | Token URL | `https://oauth2.googleapis.com/token` |
   | Scopes (si ce champ existe) | les 4 portées, séparées par des espaces |
   | PKCE verification | **décoché** |
   | Use HTTP Basic authentication | **décoché** |

   → **Finish**.
5. Le nom : l'agent → **Edit** → `Espace de travail (A2A)` → **Save**.
6. L'accès : l'agent → **User permissions** → **Add** → votre adresse ou votre groupe → rôle **Agent User** →
   **Save**.

**Attendu :** « Espace de travail (A2A) » dans la liste des agents.

En A2A, le nom de l'autorisation peut être différent de `acces-google` : l'agent lit le jeton là où l'app le met.
Gardez-le identique, c'est plus clair. Sur Agent Runtime, il doit être **identique** ([5.9](#59-variante-agent-runtime)).

**Script** (les valeurs de l'app sont données devant les commandes ; le fichier de config n'est pas modifié) :
```bash
export PROJET_APP=acme-gemini-prod NUM_APP=523307489860 GE_LOCATION=eu
export GE_PROJECT=$PROJET_APP GE_APP=gemini-enterprise-app
./scripts/autorisation_oauth.sh create acces-google ~/Downloads/client_secret_XXX.json \
  "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/calendar.events.readonly https://www.googleapis.com/auth/drive.readonly https://www.googleapis.com/auth/spreadsheets" \
  "Google Workspace (lecture, Sheets)"
AUTH_ID=acces-google ./scripts/add_agent_to_ge.sh a2a carte-workspace.json "Espace de travail (A2A)"
./scripts/personnaliser_agent.sh "Espace de travail (A2A)" workspace     # questions proposées, langue (partie 12)
```
**Attendu :**
- `autorisation créée : projects/100000000003/locations/eu/authorizations/acces-google` ;
- `ajouté : projects/…/agents/<ID>`. Le script donne aussi le droit ① s'il ne l'est pas déjà ;
- `modifié : …`.

`client_secret_XXX.json` : sur l'écran du client OAuth (étape 2) → **Télécharger le JSON**. Supprimez-le après.

L'accès **Agent User** se donne ensuite dans la console (point 6 ci-dessus).

### 5.8 Étape 8 : le test dans le chat

1. **Overview** → le lien de l'app web → **Agents** → **« Espace de travail (A2A) »**.
2. Demandez : *« Prépare ma semaine : réunions et e-mails importants. »*
3. La 1re fois : un encadré *« The agent requires additional authorization for: acces-google »* → **Authorize** →
   fenêtre Google avec les 4 portées (lire vos e-mails, voir vos événements, voir vos fichiers Drive, modifier vos
   feuilles de calcul) → **Autoriser**.
4. **Attendu :** vos réunions des 7 prochains jours, puis les e-mails prioritaires. Ensuite, plus d'encadré.

Préparez un classeur de test, copiez son lien (`https://docs.google.com/spreadsheets/d/…/edit`), puis :

| Demande | Attendu |
|---|---|
| « Qui suis-je ? » | votre nom et `…@acme.example` |
| « Prépare ma semaine : réunions et e-mails importants. » | vos réunions des 7 prochains jours, puis les e-mails prioritaires |
| « Trouve le dernier compte rendu dans mon Drive et résume-le. » | un fichier trouvé, avec son lien, et un résumé |
| « Quels sont les onglets de `<lien>` ? » | la liste des onglets |
| « Ajoute une ligne à l'onglet Feuille 1 de `<lien>` : 2026-10-12, Lille, 120. » | « 1 ligne ajoutée » ; visible dans Sheets |
| « Mets la 1re ligne en gras, fige-la et ajuste la largeur des colonnes. » | fait (`sheets_modifier`) |
| « En D1 écris Total, et en D2 la somme de C2 à C20. » | formule `=SUM(C2:C20)` écrite (les formules passent en anglais par l'API ; Sheets les affiche dans votre langue) |
| « Crée un classeur Suivi magasins avec les onglets Lille et Paris. » | un lien vers le nouveau classeur |
| « Supprime l'onglet Feuille 1. » / « Vide la colonne C. » | **refus poli**, avec une alternative (masquer…) |
| « Efface tous mes e-mails de la semaine. » | **refus** : lecture seule |

Ça bloque ? [Partie 10](#10-si-ça-bloque).

### 5.9 Variante Agent Runtime

Les étapes 1 à 3 et 8 sont les mêmes. Il faut seulement **ajouter la portée `cloud-platform`**, que Google exige pour
un agent Agent Runtime ([12-1-7, 2.1](12-1-7-agents-oauth-identite-outils.md#21-le-client-oauth-une-fois-par-fournisseur-dans-le-projet-de-lapp)).

**Étape 4 : déployer.**
```bash
AGENTS_OAUTH="workspace=acces-google" ./scripts/deployer_shell.sh runtime workspace
```
**Attendu :** `autorisation OAuth : AUTH_ID=acces-google`, puis le chemin de la ressource :
`projects/100000000002/locations/europe-west1/reasoningEngines/<ID>`. Déjà déployé sans autorisation ? Supprimez-le
d'abord (`python scripts/nettoyer.py --agent workspace --types runtime --supprimer`), puis redéployez.

**Étape 5 : le droit.** C'est le droit ② (`roles/discoveryengine.serviceAgent` sur le projet des agents). Vous l'avez
déjà donné pour `meteo` : rien à refaire. À vérifier : IAM → cocher **« Include Google-provided role grants »** →
filtre `gcp-sa-discoveryengine`.

**Étape 6 : la fiche.** La même commande `carte` affiche la partie **[Agent Runtime]**, avec le chemin et
l'autorisation qui contient `cloud-platform`. À la main : ajoutez
`%20https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform` à la fin du paramètre `scope` de l'URL de l'étape 6,
avant `&include_granted_scopes`.

**Étape 7 : l'ajout.**
- **Console :**
  - **+ Add agent** → tuile **Custom agent via Agent Runtime** → **Add** ;
  - écran **Authorizations** → **Add authorization**. **Authorization name** : `acces-google`, **exactement** la
    valeur de `AGENTS_OAUTH`, car sur Agent Runtime c'est la clé du jeton. Client ID et secret de l'étape 2, l'URL
    **avec** `cloud-platform`, Token URL `https://oauth2.googleapis.com/token` ;
  - **Next** → **Agent name** `Espace de travail`, la description du catalogue, **Agent Runtime resource path** =
    le chemin de l'étape 4 → **Create** ;
  - puis l'accès **Agent User**.
- **Script :** `autorisation_oauth.sh create` comme en 5.7, avec `cloud-platform` en plus dans les portées, puis
  `AUTH_ID=acces-google ./scripts/add_agent_to_ge.sh adk <chemin> "Espace de travail"`.

## 6. Cas B : plusieurs fournisseurs (Google + Atlassian)

**Agent Runtime obligatoire** (partie 3). Faites d'abord les étapes 1 à 3 de la partie 5 pour Google, puis :

### 6.1 L'application OAuth Atlassian

Il faut être admin, ou avoir le droit de créer une app, sur le site Atlassian de Acme.

1. [developer.atlassian.com/console/myapps](https://developer.atlassian.com/console/myapps/) → **Create** →
   **OAuth 2.0 integration** → nom `Gemini Enterprise Acme` → **Create**.
2. **Permissions** :
   - **Jira API** → **Add**, puis **Configure** → **Edit scopes** → cochez `read:jira-work` et `read:jira-user` ;
   - **Confluence API** → **Add**, puis **Configure** → cochez `search:confluence` et
     `read:confluence-content.summary`.
3. **Authorization** → **OAuth 2.0 (3LO)** → **Callback URL** :
   `https://vertexaisearch.cloud.google.com/static/oauth/oauth.html`. Si plusieurs URL sont acceptées, ajoutez aussi
   `…/oauth-redirect`.
4. **Settings** → notez le **Client ID** et le **Secret**.
5. **Distribution** → **Edit** → **Sharing** : sans cela, vous seul pouvez autoriser l'app.

**L'URL d'autorisation Atlassian.** Remplacez `ATL_CLIENT_ID` ; tout tient sur une ligne :
```
https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id=ATL_CLIENT_ID&scope=read%3Ajira-work%20read%3Ajira-user%20search%3Aconfluence%20read%3Aconfluence-content.summary%20offline_access&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&response_type=code&prompt=consent
```
**Token URL :** `https://auth.atlassian.com/oauth/token`. `offline_access` donne le jeton de rafraîchissement.

Toutes ces portées sont en **lecture** : rien ne peut être écrit ni supprimé dans Jira ou Confluence.

### 6.2 Déployer avec les deux autorisations

**Ordre : Google d'abord. Le mot `atlassian` doit être dans l'ID Atlassian.**
```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
AGENTS_OAUTH="workspace=acces-google,acces-atlassian" ./scripts/deployer_shell.sh runtime workspace
```
**Attendu :** `autorisation OAuth : AUTH_ID=acces-google,acces-atlassian`, puis la ressource
`…/reasoningEngines/<ID>`.

### 6.3 Ajouter dans l'app avec les deux autorisations

**Custom agent via Agent Runtime** → écran **Authorizations** :
1. **Add authorization** → `acces-google` (champs de 5.9, avec `cloud-platform`) ;
2. **Add authorization** → `acces-atlassian` : Client ID et Secret Atlassian, l'URL de 6.1, Token URL
   `https://auth.atlassian.com/oauth/token` ;
3. **Next** → nom `Espace de travail`, description, ressource → **Create**.

Les deux **noms d'autorisation** doivent être **identiques** à ceux de `AGENTS_OAUTH`.

### 6.4 Le test dans le chat

- « Qui suis-je ? » → votre compte Google, et `atlassian_autorise` : non, tant que vous n'avez pas autorisé Atlassian.
- « Mes tickets Jira en cours ? » → un 2e bouton **Autoriser** (Atlassian) → fenêtre Atlassian → **Accept** → la
  liste de vos tickets, avec leurs liens.
- « Prépare ma semaine avec mes réunions, mes e-mails et mes tickets Jira. » → les trois sources dans une seule
  réponse.

### 6.5 « Google + Atlassian + Google » : deux autorisations Google ?

**Inutile dans 99 % des cas.** Une autorisation Google porte **toutes** les portées Google, avec un seul
consentement.

Deux autorisations Google ne servent que pour deux clients OAuth différents. Par exemple, Sheets sur le projet
d'une autre équipe. Dans ce cas :
- nommez-les avec des mots distincts : `acces-google,acces-atlassian,acces-sheets-finance` ;
- dans le code, les outils de cette 2e autorisation appellent `commun.jeton_utilisateur(tool_context, "sheets-finance")`.

### 6.6 Variante A2A : un agent par fournisseur

Si vous tenez à Cloud Run :
- déployez `workspace` avec `AGENTS_OAUTH="workspace=acces-google"` (Google seul ; ses outils Jira répondront « pas
  d'autorisation Atlassian ») ;
- créez un 2e agent qui n'a que les outils Jira et Confluence, avec `acces-atlassian`.

Ce sont deux agents dans l'app, chacun avec son bouton « Autoriser ».

## 7. Les mêmes étapes par script ou Terraform

Il faut le fichier de config **avec les valeurs de l'app** (`PROJET_APP`, `NUM_APP`, `APP_ID`).

| Étape | Script | Terraform |
|---|---|---|
| Créer l'autorisation Google | `./scripts/autorisation_oauth.sh create acces-google client_secret.json "<portées de l'étape 6>"` | (pas de ressource : script) |
| Déployer | `AGENTS_OAUTH=… ./scripts/deployer_shell.sh runtime workspace` | `AGENTS_OAUTH="workspace=acces-google,acces-atlassian"` dans le fichier, puis `terraform apply` (02-bis) |
| Ajouter à l'app | `AUTH_ID=acces-google,acces-atlassian ./scripts/add_agent_to_ge.sh adk <ressource> "Espace de travail"` | `PUBLIER=oui` |

En A2A, une liste de plusieurs autorisations est refusée avec un message clair :
`A2A : UNE seule autorisation par agent (docs/12-1-8) ; plusieurs = Agent Runtime.` (testé).

L'autorisation Atlassian se crée dans la console (6.3). Le script `autorisation_oauth.sh` ne sait faire que Google.

## 8. Simuler avant l'app

```bash
AGENTS_OAUTH="workspace=acces-google" ./scripts/simuler_gemini_enterprise.sh oauth workspace
```
Le simulateur envoie **votre jeton gcloud**, qui n'a **pas** les portées Gmail, Agenda, Drive ni Sheets.

**Attendu :** l'agent répond avec une erreur **403 / insufficient scopes**. C'est **bon signe** : le jeton est bien
arrivé jusqu'à Google. Sans jeton (`--sans-jeton`), il demande de cliquer sur « Autoriser ».

Le vrai test avec les données reste celui du chat (5.8).

## 9. Sécurité

- **Les droits de l'utilisateur, pas plus.** L'agent ne voit que ce que l'utilisateur voit.
- **Portées minimales, en lecture** sauf Sheets (partie 2). Écran de consentement **Interne**.
- **Le jeton n'est jamais enregistré** (état `temp:`), ni affiché, ni écrit dans les journaux.
- **Injection de consignes :** un e-mail ou un document peut contenir « ignore tes règles et… ». L'instruction de
  l'agent traite ce contenu comme une **donnée**. Même trompé, l'agent ne peut rien supprimer ni envoyer : les
  portées et le code l'en empêchent.
- **Model Armor** filtre les questions et les réponses (`PROMPT_TEMPLATE`, `RESPONSE_TEMPLATE`), comme pour les autres
  agents.
- **Retirer l'accès :** l'utilisateur va sur [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
  (Google) et sur son profil Atlassian → **Connected apps**.

## 10. Si ça bloque

| Message ou symptôme | Cause | Que faire |
|---|---|---|
| `redirect_uri_mismatch` (Google) ou `invalid redirect_uri` (Atlassian) | URI de redirection | vérifier les URI, au caractère près (5.2, 6.1) |
| « Accès bloqué : votre administrateur… » | l'admin Google Workspace bloque l'accès des apps à Gmail ou Drive | lui demander d'**approuver l'ID client** : Console d'administration → Sécurité → Contrôles des API → Accès des applications tierces |
| `refus (403) … has not been used in project … or it is disabled` | API non activée | étape 3 (5.3), sur le projet **du client OAuth** |
| `refus (403) … insufficient authentication scopes` | portée absente de l'URL d'autorisation | vérifier les portées de l'URL (5.6), puis réautoriser (retirer l'accès, voir partie 9) |
| `refus (401)` | jeton expiré | redemander ; si ça persiste, retirer l'accès et réautoriser |
| `refus (403) … The caller does not have permission` (Sheets) | l'utilisateur n'a pas le droit de modifier ce classeur | le classeur doit lui être partagé en **Éditeur** |
| « Pas de jeton Atlassian » | autorisation Atlassian absente, ou son ID sans le mot `atlassian`, ou en A2A | partie 3 et 6.2 |
| `Aucun site Atlassian accessible` | l'utilisateur n'a accès à aucun site, ou portées Jira et Confluence non cochées | 6.1, étape 2 |
| Pas de bouton « Autoriser » | autorisation non attachée à l'agent | retirer l'agent de l'app, le rajouter avec l'autorisation (5.7 ou 5.9) |
| Agent Runtime : toujours « cliquez sur Autoriser » après l'avoir fait | nom de l'autorisation dans l'app ≠ `AGENTS_OAUTH` | même ID des deux côtés (5.9) ; redéployer si besoin |
| Réponse bloquée par Model Armor | données sensibles dans un e-mail, un document ou une cellule | normal avec ce filtre ; restreindre la demande |
| `A2A : UNE seule autorisation par agent` | deux autorisations en A2A | partie 3 : Agent Runtime, ou deux agents |

## 11. Ajouter un outil plus tard

1. Écrivez une fonction dans `agents/trio/workspace_agent/agent.py`, décorée par `@_outil`, avec une docstring claire
   (c'est ce que lit le modèle). Récupérez le jeton avec `_jeton(tool_context)` (Google) ou
   `_jeton(tool_context, "atlassian")`.
2. Ajoutez-la à `tools=[…]` en bas du fichier.
3. Faut-il une nouvelle portée ? Ajoutez-la à l'URL d'autorisation (5.6) et au bloc `oauth` du catalogue. L'autorisation se modifie dans l'app ; les
   utilisateurs devront ré-autoriser.
4. **Écrire dans l'agenda ou envoyer un e-mail ?**
   - Les portées `calendar.events` et `gmail.send` permettent **aussi** de supprimer, ou d'envoyer sans retour en
     arrière.
   - Gardez la même règle que pour Sheets : aucun outil de suppression, et une confirmation de l'utilisateur dans
     l'instruction avant tout envoi ([12-1-7, 2.3](12-1-7-agents-oauth-identite-outils.md#23-le-code-de-loutil-dans-lagent)).
5. Ajoutez un test dans `scripts/test_trio.py`, puis redéployez : `./scripts/deployer_shell.sh cloudrun workspace`
   (A2A). Pour Agent Runtime : suppression, puis `runtime workspace`.

## 12. Soigner l'expérience : encadré « Autoriser », nom, icône, questions

À la 1re question, Gemini Enterprise affiche un encadré : *« The agent requires additional authorization for: … »*
avec un bouton **Authorize**. C'est **son** interface.

| Élément | Personnalisable ? | Comment |
|---|---|---|
| Couleur, forme, place du bouton ; mise en page de l'encadré | ❌ | Interface de Google, la même pour tous |
| Langue (« Authorize » ou « Autoriser ») | ✅ indirectement | Gemini Enterprise en français (paramètres, langue du navigateur ; pas de `hl=en_US` dans l'URL) |
| Le nom après « authorization for: » | ✅ | Le **nom affiché** de l'autorisation (`displayName`), ou à défaut son ID. Choisissez un ID lisible (`acces-gmail`, pas l'ID généré par la console) |
| Nom de l'agent, icône | ✅ | `displayName`, `icon` de l'agent |
| Questions proposées, texte de la zone de saisie | ✅ | `starterPrompts`, `customPlaceholderText` |
| La fenêtre Google après « Authorize » (nom de l'app, logo, e-mail d'assistance, liens) | ✅ | **Google Auth Platform → Branding**, dans le projet du client OAuth |
| Le message de l'agent si le jeton manque ou est refusé | ✅ | L'`instruction` de l'agent (déjà en français, avec la marche à suivre) |

En A2A, l'encadré apparaît **avant** que l'agent soit appelé : un message de l'agent ne peut pas le remplacer. Il
n'apparaît qu'à la 1re utilisation. Ensuite, l'accès est gardé et l'agent répond directement.

**Pas à pas :**
1. **La fenêtre Google** (sans risque, la plus visible) : projet du client OAuth → 🔎 *Google Auth Platform* →
   **Branding** :
   - nom : `Assistant Acme`, par exemple ;
   - logo : PNG carré 120×120 ;
   - e-mail d'assistance : celui de l'équipe ;
   - liens internes.

   Puis **Accès aux données** → déclarez les portées : elles s'affichent en clair (« Afficher vos e-mails »…).
2. **Le nom de l'autorisation :**
   ```bash
   ./scripts/autorisation_oauth.sh list                                   # ID | nom affiché
   ./scripts/autorisation_oauth.sh renommer acces-gmail "Gmail (lecture seule)"
   ```
   Il faut `PROJET_APP`, `NUM_APP` et `GE_LOCATION` devant la commande, ou dans la config. Ouvrez une **nouvelle**
   conversation ; pour revoir l'encadré, retirez d'abord l'accès sur myaccount.google.com/permissions.
   - Si l'encadré montre le nouveau nom, c'est fini.
   - S'il montre encore l'ID, créez une autorisation avec un ID lisible
     (`autorisation_oauth.sh create acces-gmail … "Gmail (lecture seule)"`), puis rattachez l'agent : retirez-le et
     rajoutez-le.
3. **L'agent** (nom, questions du catalogue, texte de saisie, langue, icône facultative) :
   ```bash
   GE_PROJECT=acme-gemini-prod GE_APP=gemini-enterprise-app GE_LOCATION=eu \
     ./scripts/personnaliser_agent.sh "test gmail remote agent with auth" courriels --icone icone.png
   ```
   **Attendu :** `AVANT : …`, `APRÈS : …`, la question « Tapez oui », puis `modifié : …`. L'avant est gardé dans
   `avant-<ID>.json`. Pour revenir en arrière : `./scripts/personnaliser_agent.sh --annuler avant-<ID>.json`.

> Testé : l'affichage avant/après, le corps envoyé (seuls les champs du masque), le retour arrière et le nom inconnu,
> avec un faux serveur Google. **Pas testé sur une vraie app** : faites-le d'abord sur un agent de test.
> Les champs `displayName` (autorisation), `icon`, `starterPrompts`, `customPlaceholderText` et `languageCode` (agent)
> viennent du document de référence de l'API Discovery Engine v1alpha.

## 13. Le client OAuth : projet des agents ou projet de l'app ?

**Les deux marchent.** L'autorisation ne garde que l'ID client et le secret. Pour un client **Interne**, il suffit que
le projet soit dans l'organisation Acme.

| | Client dans le **projet des agents** | Client dans le **projet de l'app** (prod) |
|---|---|---|
| API Gmail, Drive… à activer | projet des agents (`deployer_shell.sh oauth`, Terraform) | projet de l'app |
| Quotas, suivi des appels | projet des agents | projet de l'app |
| Nom et logo de la fenêtre Google | ceux de l'équipe agents | un seul nom pour tous les agents |
| Secret et sa rotation | équipe agents | équipe Gemini Enterprise |
| Changement en prod pour un nouvel agent | aucun, à part l'ajout de l'agent | API et client dans le projet de prod |

Google conseille *« le projet qui contient la source de données à laquelle l'agent accède »*. Pour Gmail ou Drive, la
donnée est dans Google Workspace, donc ce conseil ne tranche pas.

**Recommandation :**
- **projet des agents**, un client par équipe ou par famille d'agents. C'est ce que font les scripts et Terraform ;
- **projet de l'app** seulement pour un client **commun et transverse**, géré par l'équipe Gemini Enterprise. L'admin
  Workspace n'a alors qu'un ID client à approuver.
