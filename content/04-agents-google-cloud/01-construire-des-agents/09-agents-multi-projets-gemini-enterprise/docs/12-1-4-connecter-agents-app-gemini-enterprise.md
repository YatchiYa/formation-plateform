# 12-1-4. Connecter les agents (projet des agents) à l'app Gemini Enterprise (projet de l'app)

**Le but :** vos agents tournent dans le projet des agents `aiml-gemini-ent-exp-0zga` (guides 12-1-1, 12-1-2 ou
12-1-3). On les rend utilisables dans l'app Gemini Enterprise `dev_gemini-entreprise-app` du projet
`acme-gemini-prod`, **un par un ou tous**, en sachant exactement **quoi** changer, **dans quel projet**, et
comment **revenir en arrière**.

**Les autres guides de cette étape :**
- [12-1-5](12-1-5-simuler-appel-gemini-enterprise.md) : **simuler** l'appel de Gemini Enterprise (sans toucher à
  l'app), à faire **avant** l'ajout en production ;
- [12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md) : le côté **console** de Gemini Enterprise, clic par clic ;
- [12-1-7](12-1-7-agents-oauth-identite-outils.md) : agents avec **OAuth** (compte de l'utilisateur), identité, outils
  de Gemini Enterprise.

> **Testé en vrai** (11 octobre 2026, deux projets de test jouant ces rôles, sans app Gemini Enterprise activée) :
> - `connecter_app.sh` : `apps`, `verifier` (jusqu'au contrôle de l'app), `droits` (plan, confirmation, droits posés,
>   relance sans effet), `retirer` (droits retirés) ;
> - les droits posés **fonctionnent** : prouvé par la simulation de [12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)
>   (refusé sans, accepté avec, refusé après retrait).
>
> **Non testable sans app :** l'ajout dans l'app (`ajouter`), l'accès Agent User, le chat. Ces étapes suivent la
> documentation Google, et passent par `add_agent_to_ge.sh`, qui refuse les doublons.

---

## Sommaire

0. [Le principe : qui appelle qui, qui change quoi](#0-le-principe--qui-appelle-qui-qui-change-quoi)
1. [Production : les règles de prudence](#1-production--les-règles-de-prudence)
2. [Remplir la configuration : chaque valeur, où la trouver](#2-remplir-la-configuration--chaque-valeur-où-la-trouver)
3. [Les droits : comprendre, voir, accorder à la souris, demander à une équipe](#3-les-droits--comprendre-voir-accorder-à-la-souris-demander-à-une-équipe)
4. [Méthode 1 : le script (recommandé)](#4-méthode-1--le-script-recommandé)
5. [Méthode 2 : à la main, une commande à la fois](#5-méthode-2--à-la-main-une-commande-à-la-fois)
6. [Méthode 3 : Terraform (agents déployés avec 12-1-2)](#6-méthode-3--terraform-agents-déployés-avec-12-1-2)
7. [Donner l'accès et tester dans le chat](#7-donner-laccès-et-tester-dans-le-chat)
8. [Revenir en arrière](#8-revenir-en-arrière)
9. [Ce qui peut arriver](#9-ce-qui-peut-arriver)

---

## 0. Le principe : qui appelle qui, qui change quoi

```
 acme-gemini-prod (523307489860) : L'APP              aiml-gemini-ent-exp-0zga (433175138344) : LES AGENTS
 ┌──────────────────────────────────────────────┐              ┌──────────────────────────────────────────────────┐
 │ App dev_gemini-entreprise-app (eu)            │   appelle    │ Cloud Run  meteo-a2a-shell  (A2A)                 │
 │   agents ajoutés : « Météo & équipement » …   │ ───────────▶ │ Agent Runtime  meteo-shell                        │
 │                                              │              │                                                  │
 │ Son compte de service (c'est LUI qui appelle) :│              │ DROITS DONNÉS ICI au compte de l'app :           │
 │ service-100000000003@gcp-sa-discoveryengine…  │ ◀─────────── │  - run.invoker sur chaque service Cloud Run       │
 │                                              │   autorise   │  - discoveryengine.serviceAgent sur le projet     │
 └──────────────────────────────────────────────┘              │    (pour les agents Agent Runtime)                │
                                                               └──────────────────────────────────────────────────┘
```

**En une phrase :** le projet des agents **autorise** le compte de l'app, et l'app **ajoute** les agents.

| Où | Ce qui change | Qui le fait |
|---|---|---|
| **Projet des agents** | 2 types de droits **pour le compte de l'app** : `roles/run.invoker` sur chaque service Cloud Run, `roles/discoveryengine.serviceAgent` sur le projet (si agents Agent Runtime) | L'équipe des agents (droit de modifier l'IAM de son projet) |
| **Projet de l'app** | Une **entrée par agent** dans l'app, puis l'accès **Agent User** pour un groupe. **Aucun** droit IAM, **aucune** API | L'administrateur Gemini Enterprise |

**Les modes possibles entre deux projets :**

| Mode d'ajout dans l'app | Entre deux projets ? | Ce que l'app demande | Droit pour le compte de l'app |
|---|---|---|---|
| **Agent Runtime** | **Oui** | Le nom de ressource `projects/100000000002/locations/europe-west1/reasoningEngines/<ID>` | `discoveryengine.serviceAgent` sur le **projet** des agents |
| **A2A** (Cloud Run) | **Oui** | La **carte** de l'agent (JSON) | `run.invoker` sur **chaque service** |
| **Agent Registry** (import) | **Non** : l'app n'importe que depuis le registre de **son** projet | — | → [12-2](12-2-agents-dans-projet-app.md) |
| **Dialogflow** | Non documenté par Google entre deux projets | — | → [12-2](12-2-agents-dans-projet-app.md) (agent dans le projet de l'app) |

---

## 1. Production : les règles de prudence

1. **Simulez d'abord** ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)) : vous prouvez que les droits marchent
   sans toucher à l'app.
2. **Un seul agent d'abord** : `AGENTS="meteo"` dans la configuration, ou la clé en argument (`… ajouter meteo`).
3. **Un petit groupe de test d'abord** pour l'accès Agent User (ou votre seule adresse), puis le groupe final.
4. **Toujours `verifier` avant** : lecture seule, il dit ce qui manque.
5. **Le script montre la liste et demande de taper l'ID** du projet (droits) ou de l'app (ajout) avant tout
   changement. N'utilisez pas `--oui` en production.
6. **Retour arrière prêt** : [partie 8](#8-revenir-en-arrière). Retirer l'accès du groupe suffit à masquer un agent
   en quelques secondes.

**Vos droits :**

| Projet | Rôle nécessaire (ou Propriétaire) | Pour |
|---|---|---|
| App `acme-gemini-prod` | **Gemini Enterprise Admin** (`roles/discoveryengine.admin`) | Lire l'app, ajouter les agents, donner l'accès |
| Agents `aiml-gemini-ent-exp-0zga` | `roles/resourcemanager.projectIamAdmin` + `roles/run.admin` | Donner les droits au compte de l'app |

---

## 2. Remplir la configuration : chaque valeur, où la trouver

Fichier : `config/12-1-agents-dans-projet-exp.env`. Les lignes du projet des agents sont déjà remplies (12-1-1).
Il reste celles de l'app :

```bash
PROJET_APP=acme-gemini-prod
NUM_APP=523307489860
APP_ID=dev_gemini-entreprise-app
GE_LOCATION=eu
AGENTS="meteo"                               # un seul agent pour commencer
PUBLIER=non                                  # Terraform seulement (partie 6)
GROUPE_UTILISATEURS=equipe-agents@acme.example
```

| Ligne | Ce que c'est | Où la trouver exactement |
|---|---|---|
| `PROJET_APP` | L'**ID** du projet où est l'app (pas son nom affiché) | Console → **sélecteur de projet** en haut → colonne **ID** |
| `NUM_APP` | Le **numéro** de ce projet (12 chiffres) | Même écran, colonne **Numéro** ; ou `gcloud projects describe acme-gemini-prod --format='value(projectNumber)'` |
| `APP_ID` | L'**ID** de l'app Gemini Enterprise (pas son nom affiché : `dev_gemini-entreprise-app`, pas « Dev Gemini Entreprise App ») | Projet de l'app → 🔎 « Gemini Enterprise » → **Apps** (Applications) → colonne **ID**, ou l'app → **Présentation** (*Overview*). En commande : `./scripts/connecter_app.sh apps` (partie 4) |
| `GE_LOCATION` | Où vit l'app : `eu`, `us` ou `global` | Même liste, colonne **Emplacement** (*Location*) ; ou 2e colonne de `connecter_app.sh apps` |
| `AGENTS` | Les agents à connecter (vide = tous) | `agents/trio/catalogue.json` |
| `GROUPE_UTILISATEURS` | L'**adresse e-mail d'un groupe Google** (ex. `equipe-agents@acme.example`) qui utilisera les agents. Une seule adresse : un groupe. Pour un 1er test, votre propre adresse convient | Le groupe se crée dans Google Workspace : [groups.google.com](https://groups.google.com) ou la console d'administration (votre administrateur). Les scripts ne s'en servent pas : c'est la valeur à saisir à l'étape « Agent User » (partie 7) |

**Le compte de l'app** est calculé à partir de `NUM_APP` : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
Vous n'avez rien à créer : Google l'a créé avec l'app.

**Charger :**

```bash
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
```

**Attendu :**

```
== Configuration chargée : config/12-1-agents-dans-projet-exp.env
   App Gemini Enterprise : dev_gemini-entreprise-app   (projet acme-gemini-prod, numéro 523307489860, eu)
   Projet des agents     : aiml-gemini-ent-exp-0zga (numéro 433175138344), région europe-west1   [même projet que l'app : non]
   Agents à déployer     : meteo
   Compte de l'app       : service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
   Terraform             : espace « scenario-12-1 », publication dans l'app : non
   …
   OK
```

---

## 3. Les droits : comprendre, voir, accorder à la souris, demander à une équipe

### 3.1 Ce qu'est un « droit » dans Google Cloud

Dans Google Cloud, un droit est **toujours** une phrase à trois morceaux :

> **QUI** (un compte) reçoit **QUEL RÔLE** (un paquet de permissions) **SUR QUOI** (un projet, ou une seule ressource).

Ici, il n'y a que **deux** phrases à écrire, toutes les deux **dans le projet des agents** :

| # | QUI | QUEL RÔLE | SUR QUOI | Ce que ça permet | Quand |
|---|---|---|---|---|---|
| ① | Le compte de l'app : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` | **Demandeur Cloud Run** (*Cloud Run Invoker*, `roles/run.invoker`) | **Un** service Cloud Run (ex. `meteo-a2a-shell`) | L'app peut **appeler cet agent** (A2A), et seulement lui | Pour chaque agent **A2A** |
| ② | Le même compte | **Agent de service Discovery Engine** (*Discovery Engine Service Agent*, `roles/discoveryengine.serviceAgent`) | **Le projet** des agents entier | L'app peut appeler les agents **Agent Runtime** de ce projet | Une fois, si au moins un agent **Agent Runtime** |

**Ce qu'il faut retenir :**
- **Le compte de l'app** est un compte de service **créé par Google** avec l'app : on ne le crée pas, on ne peut pas
  l'utiliser soi-même. Son adresse se déduit du **numéro** du projet de l'app : `service-<NUM_APP>@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
- **Celui qui donne le droit est celui qui possède la ressource** : le droit se pose **dans le projet des agents**, donc
  par l'**équipe de l'agent** (ou quelqu'un qui a le droit de modifier l'IAM de ce projet). L'administrateur de l'app
  ne peut pas le faire depuis son projet.
- **① est étroit** (un seul service). **② est large** (tous les agents Agent Runtime du projet) : c'est le rôle que
  Google documente. Si une équipe veut limiter, elle met dans un **projet à part** les agents qu'elle expose à l'app.
- **Ces droits ne donnent rien aux utilisateurs.** Qui peut **utiliser** un agent dans l'app est un autre droit,
  **Agent User**, donné dans l'app par son administrateur ([partie 7](#7-donner-laccès-et-tester-dans-le-chat)).
- **Délai :** un droit tout neuf met **2 à 3 minutes** à s'appliquer.

```
  Projet de l'app (vous, admin Gemini Enterprise)          Projet des agents (l'équipe de l'agent)
  ┌───────────────────────────────────────┐               ┌──────────────────────────────────────────────┐
  │ App : agent « Météo » ajouté          │  ① / ② :      │ ① meteo-a2a-shell : run.invoker              │
  │   ↓ appelle avec son compte           │  l'équipe     │      → pour service-100000000003@gcp-sa-…    │
  │ service-100000000003@gcp-sa-…  ───────┼──────────────▶│ ② projet : discoveryengine.serviceAgent       │
  │                                       │  autorise     │      → pour service-100000000003@gcp-sa-…    │
  │ Agent User : qui peut UTILISER l'agent│  ce compte    │                                              │
  └───────────────────────────────────────┘               └──────────────────────────────────────────────┘
```

### 3.2 Voir les droits, en lecture seule

**Dans la console**, projet **des agents** (`aiml-gemini-ent-exp-0zga`) sélectionné en haut :

**Droit ① (un service Cloud Run) :**
1. 🔎 « Cloud Run » → **Services**.
2. **Cochez** la case à gauche du service (`meteo-a2a-shell`) : un panneau s'ouvre à droite, onglet **Autorisations**
   (*Permissions*). Sinon : bouton **Autorisations** en haut de la liste.
3. Dépliez le rôle **Demandeur Cloud Run** (*Cloud Run Invoker*).

**Attendu :** `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` dans la liste. Absent : le droit
n'est pas donné.

**Droit ② (le projet) :**
1. 🔎 « IAM » → **IAM** (*IAM et administration* → *IAM*).
2. **Cochez « Inclure les attributions de rôles fournies par Google »** (*Include Google-provided role grants*), en
   haut à droite du tableau. **Indispensable** : sinon les comptes de Google ne s'affichent pas.
3. Dans **Filtrer**, tapez `gcp-sa-discoveryengine`.

**Attendu :** une ligne `service-100000000003@gcp-sa-discoveryengine…` avec le rôle **Agent de service Discovery
Engine**.

**Le test complet, sans rien changer : l'Outil de dépannage des stratégies** (*Policy Troubleshooter*). Il répond
« ce compte peut-il faire ça ? ».
1. 🔎 « Policy Troubleshooter » (*Outil de dépannage des stratégies IAM*).
2. **Compte principal** : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
3. **Ressource** : `//run.googleapis.com/projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/services/meteo-a2a-shell` ;
   **Autorisation** : `run.routes.invoke` (« appeler le service »).
4. **Vérifier l'accès**.

Pour le droit ②, la liste IAM ci-dessus suffit.

**Attendu :** « Accès accordé » (ou « refusé », avec la raison).

**En commande** (lecture seule, configuration chargée) :

```bash
# ② le projet : les rôles du compte de l'app
gcloud projects get-iam-policy $PROJET_AGENTS --flatten=bindings \
  --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
# ① un service : qui a run.invoker
gcloud run services get-iam-policy meteo-a2a-shell --region=$REGION --project=$PROJET_AGENTS
# tout d'un coup, pour les agents de AGENTS
./scripts/connecter_app.sh verifier
```

**Attendu :**
- `roles/discoveryengine.serviceAgent` (droit ②) ;
- pour le service, une politique qui contient `role: roles/run.invoker` avec `members: - serviceAccount:service-100000000003@gcp-sa-discoveryengine…`
  (droit ①) ;
- `verifier` : `OK` ou `À FAIRE` pour chacun (partie 4.2).

**Qui peut voir ?** Il faut au moins **Lecteur** (*Viewer*) ou **Examinateur de sécurité** (*Security Reviewer*) sur le
projet des agents. L'administrateur de l'app n'a souvent **aucun** accès aux projets des équipes : c'est l'équipe qui
vérifie, et vous renvoie la preuve (partie 3.5).

### 3.3 Accorder le droit ① à la souris (un service Cloud Run)

Projet **des agents** sélectionné. Il faut le droit de modifier les autorisations du service : **Administrateur Cloud
Run** (`roles/run.admin`) ou **Propriétaire**.

1. 🔎 « Cloud Run » → **Services** → **cochez** `meteo-a2a-shell` → **Autorisations** (panneau de droite, ou bouton en
   haut).
2. **Ajouter un compte principal** (*Add principal*).
3. **Nouveaux comptes principaux** : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` (copiez-le
   exactement, sans espace).
4. **Attribuer des rôles** → **Cloud Run** → **Demandeur Cloud Run** (*Cloud Run Invoker*).
5. **Enregistrer**.

**Attendu :** le compte apparaît sous **Demandeur Cloud Run**. Recommencez pour chaque service A2A exposé à l'app.

> **Ne touchez pas à l'authentification du service** (onglet **Sécurité** : elle reste **Exiger l'authentification**).
> N'ajoutez jamais `allUsers` : l'agent deviendrait public.

### 3.4 Accorder le droit ② à la souris (le projet)

Projet **des agents** sélectionné. Il faut **Administrateur IAM de projet** (`roles/resourcemanager.projectIamAdmin`)
ou **Propriétaire**.

1. 🔎 « IAM » → **IAM** → **Accorder l'accès** (*Grant access*).
2. **Nouveaux comptes principaux** : `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
3. **Attribuer des rôles** → tapez `Discovery Engine Service Agent` → **Agent de service Discovery Engine**.
4. **Enregistrer**.

**Attendu :** avec la case « Inclure les attributions de rôles fournies par Google » cochée (3.2), la ligne du compte
avec ce rôle.

**Si la console ne propose pas ce rôle** (c'est un rôle « d'agent de service », que la console masque parfois) : la
commande (Cloud Shell, icône `>_`, projet des agents) :

```bash
gcloud projects add-iam-policy-binding aiml-gemini-ent-exp-0zga --condition=None \
  --role=roles/discoveryengine.serviceAgent \
  --member=serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
```

**Retirer un droit à la souris :**
- ① : le même panneau **Autorisations** du service → la ligne du compte → icône **corbeille** ;
- ② : **IAM** → la ligne du compte → **crayon** (*Modifier*) → corbeille à côté du rôle → **Enregistrer**.

### 3.5 Le circuit avec une équipe cliente (ses agents, son projet)

Chaque équipe a ses agents dans **son** projet. Le circuit :

```
  1. Vous (admin de l'app) ──── message A ────▶ l'équipe
  2. L'équipe : donne ① et/ou ② (3.3, 3.4), vérifie (3.2), simule si possible (12-1-5)
  3. L'équipe ──── message B (la fiche) ────▶ vous
  4. Vous : vérifiez, ajoutez l'agent dans l'app (12-1-6), donnez Agent User à un groupe pilote, testez
  5. Fin : l'équipe retire ses droits, ou vous retirez l'agent (partie 8)
```

**Message A, de vous à l'équipe** (à copier, en remplaçant les valeurs) :

```
Objet : Ajout de votre agent dans Gemini Enterprise (app dev_gemini-entreprise-app)

Bonjour,

Pour que l'app Gemini Enterprise puisse appeler votre agent, merci de donner, DANS VOTRE PROJET, à ce compte :
    service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
(c'est le compte de service de notre app, créé par Google ; ce n'est pas une personne)

- Agent sur Cloud Run (A2A) : le rôle « Demandeur Cloud Run » (roles/run.invoker) sur le SERVICE de l'agent
  (Cloud Run > cocher le service > Autorisations > Ajouter un compte principal).
- Agent sur Agent Runtime : le rôle « Agent de service Discovery Engine » (roles/discoveryengine.serviceAgent)
  sur le PROJET (IAM > Accorder l'accès), ou la commande :
  gcloud projects add-iam-policy-binding <VOTRE_PROJET> --condition=None --role=roles/discoveryengine.serviceAgent \
    --member=serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com

Conditions : agent dans une région europe-* (notre app est en « eu »), service privé (authentification requise),
filtre Model Armor actif.

Puis renvoyez-nous la fiche ci-jointe (message B). Ces droits ne donnent accès à rien d'autre qu'à l'appel de votre
agent par l'app ; vous pouvez les retirer à tout moment.
```

**Message B, la fiche, de l'équipe à vous :**

```
Agent : <nom affiché souhaité>            Description : <une phrase, ce que l'agent fait>
Projet : <ID du projet>                   Numéro : <numéro>          Région : europe-west1
Type : A2A (Cloud Run)  /  Agent Runtime
  - A2A : la carte de l'agent (fichier JSON joint, champ "url" = l'adresse du service)
  - Agent Runtime : le nom de ressource projects/<NUM>/locations/europe-west1/reasoningEngines/<ID>
Droit donné : run.invoker sur <service>  /  discoveryengine.serviceAgent sur le projet   (date)
Preuve : capture de l'écran « Autorisations » ou sortie de « gcloud … get-iam-policy … »
         (et, si fait, le bilan ACCEPTÉ du simulateur, docs/12-1-5)
OAuth : non  /  oui (quelles données de l'utilisateur, quelles portées) → docs/12-1-7
Contact support : <e-mail de l'équipe>    Groupe pilote : <e-mail du groupe>
```

**Ce que vous faites en recevant la fiche :**
1. Si vous avez un accès en lecture au projet de l'équipe : vérifier (3.2, ou `verifier`) ; sinon, vous fier à la
   preuve jointe.
2. Ajouter l'agent ([12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md) : la carte ou le nom de ressource de
   la fiche).
3. **Agent User** pour le groupe pilote, tester, puis ouvrir au groupe final.

**Et si c'est vous qui avez la main sur les deux projets ?** (comme dans ces guides) Faites tout vous-même : partie 4
(script), 5 (commandes) ou 3.3 / 3.4 (souris).

**La simulation entre équipes** ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)) :
1. Vous créez **une fois** le simulateur dans le projet de l'app (`preparer`).
2. Vous donnez à l'équipe le droit de l'utiliser : **Créateur de jetons du compte de service** sur `ge-simulateur`.
3. L'équipe lui donne les **mêmes** droits ① / ② à titre de test, vérifie `ACCEPTÉ`, puis les lui retire.

Les détails sont dans [09, partie 3](09-connecter-a-gemini-enterprise.md).

---

## 4. Méthode 1 : le script (recommandé)

`scripts/connecter_app.sh` lit la configuration et fait les étapes dans l'ordre. Il **montre** chaque changement et
**demande confirmation**. Les agents déployés par la console (noms en `-console`) : ajoutez `--methode console`.

### 4.1 Trouver l'ID de l'app (lecture seule)

```bash
./scripts/connecter_app.sh apps
```

**Attendu :** une ligne par app du projet, par exemple `dev_gemini-entreprise-app   eu   Dev Gemini Entreprise App
(SOLUTION_TYPE_SEARCH)`. La 1re colonne est `APP_ID`, la 2e `GE_LOCATION`. Aucune ligne : pas d'app dans ce projet, ou
pas le droit de les lire.

### 4.2 Tout vérifier (lecture seule)

```bash
./scripts/connecter_app.sh verifier
```

**Attendu** (forme du résultat ; les « À FAIRE » dépendent de votre état) :

```
== 1. Configuration
  OK   numéro du projet de l'app : 523307489860
== 2. L'app
  OK   dev_gemini-entreprise-app existe : « … » (eu)
  OK   région des agents europe-west1 compatible avec l'app eu
== 3. Vos rôles (directs ; ceux reçus par un groupe ne s'affichent pas : vérifier dans la console)
  acme-gemini-prod : roles/discoveryengine.admin …
  aiml-gemini-ent-exp-0zga : roles/owner …
== 4. Les agents (méthode shell) et les droits du compte de l'app service-100000000003@gcp-sa-discoveryengine…
  À FAIRE  discoveryengine.serviceAgent sur aiml-gemini-ent-exp-0zga (si vous ajoutez des agents Agent Runtime)
  meteo  Cloud Run meteo-a2a-shell : À FAIRE : run.invoker ; « Météo & équipement (A2A) » : À AJOUTER
  meteo  Agent Runtime meteo-shell : « Météo & équipement » : À AJOUTER
Rien n'a été changé. Suite : ./scripts/connecter_app.sh droits, puis ajouter.
```

**Résultat obtenu sans app** (projet de test où Gemini Enterprise n'est pas activé) : le script le dit, et vérifie
quand même les agents et les droits :

```
== 2. L'app
  KO   app dev_gemini-entreprise-app introuvable en eu : Engine with name "projects/…/engines/dev_gemini-entreprise-app" does not exist.
       → pas encore d'app ? Les droits se vérifient quand même ci-dessous ; l'ajout attendra l'app.
       → pour prouver l'appel sans app : docs/12-1-5 (simulation). Liste des apps : ./scripts/connecter_app.sh apps
…
  meteo  Cloud Run meteo-a2a-shell : non déployé
  → aucun de ces agents n'est déployé (méthode shell) : déployez d'abord (docs/12-1-1, ./scripts/deployer_shell.sh).
```

**Pas d'app ?** Faites la simulation ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)) : elle prouve l'appel
entre les deux projets sans app. Gardez `ajouter` pour le projet où l'app existe.

### 4.3 Donner les droits (projet des agents)

Ce que sont ces droits, comment les voir et les donner à la souris : [partie 3](#3-les-droits--comprendre-voir-accorder-à-la-souris-demander-à-une-équipe). Le script fait la même chose.

```bash
./scripts/connecter_app.sh droits
```

Le script affiche la liste, puis demande : `Tapez « aiml-gemini-ent-exp-0zga » pour confirmer :`. **Résultat obtenu** :

```
== Droits à donner à service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com, dans le projet des agents aiml-gemini-ent-exp-0zga :
   - projet aiml-gemini-ent-exp-0zga : roles/discoveryengine.serviceAgent
   - service taille-a2a-shell : roles/run.invoker
Ces droits permettent à l'app d'APPELER ces agents. Tapez « aiml-gemini-ent-exp-0zga » pour confirmer : aiml-gemini-ent-exp-0zga
▶ gcloud projects add-iam-policy-binding aiml-gemini-ent-exp-0zga --condition=None --role=roles/discoveryengine.serviceAgent --member=serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
  fait
▶ gcloud run services add-iam-policy-binding taille-a2a-shell --region=europe-west1 --project=aiml-gemini-ent-exp-0zga --role=roles/run.invoker --member=serviceAccount:service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com
  fait
Droits donnés. Ils s'appliquent en 2 à 3 minutes. Suite : ./scripts/connecter_app.sh ajouter
```

Relancé : `Rien à faire : les droits sont déjà en place.` Une autre réponse que l'ID tapé : `Annulé : rien n'a été changé.`

**Maintenant, simulez** ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)) : vous verrez `ACCEPTÉ` avant même
d'ajouter quoi que ce soit dans l'app.

### 4.4 Ajouter les agents dans l'app (projet de l'app)

```bash
./scripts/connecter_app.sh ajouter
```

Le script liste ce qu'il va ajouter, puis demande de taper `dev_gemini-entreprise-app`. **Ce qu'il fait** pour chaque
agent déployé et pas encore dans l'app :

| Hébergement | Nom dans l'app | Ce qui est envoyé |
|---|---|---|
| Agent Runtime `meteo-shell` | « Météo & équipement » | Son nom de ressource |
| Cloud Run `meteo-a2a-shell` | « Météo & équipement (A2A) » | Sa carte (écrite dans `carte-meteo.json`) |

Chaque ajout passe par `./scripts/add_agent_to_ge.sh`. **Attendu :** `ajouté : projects/…/engines/dev_gemini-entreprise-app/assistants/default_assistant/agents/<ID>`.
Relancé : `Rien à ajouter`. Un agent de même nom déjà dans l'app n'est jamais dupliqué.

**Vérifier :** `./scripts/connecter_app.sh lister` (une ligne par agent de l'app : nom, type, ID).

Puis l'accès : [partie 7](#7-donner-laccès-et-tester-dans-le-chat).

---

## 5. Méthode 2 : à la main, une commande à la fois

Les mêmes changements, que vous tapez vous-même. Configuration chargée.

### 5.1 Le compte de l'app (vérification)

```bash
echo $GE_SA
gcloud beta services identity create --service=discoveryengine.googleapis.com --project=$PROJET_APP
```

**Attendu :** `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` deux fois (la 2e commande dit
« created » même s'il existe : rien ne change).

### 5.2 Le droit pour les agents Agent Runtime (projet des agents, une fois)

```bash
gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA
```

| Morceau | Sens |
|---|---|
| `add-iam-policy-binding $PROJET_AGENTS` | Ajoute un droit sur le **projet des agents** |
| `--role=roles/discoveryengine.serviceAgent` | Le rôle qu'il faut à l'app pour appeler les agents Agent Runtime de ce projet (documentation Google) |
| `--member=serviceAccount:$GE_SA` | À qui : le compte de l'app |
| `--condition=None` | Sans condition (évite une question de gcloud) |

**Attendu :** `Updated IAM policy for project [aiml-gemini-ent-exp-0zga].` Ce droit vaut pour **tous** les agents
Agent Runtime du projet.

### 5.3 Le droit pour chaque agent Cloud Run (projet des agents)

```bash
K=meteo
gcloud run services add-iam-policy-binding $K-a2a-shell --region=$REGION --project=$PROJET_AGENTS \
  --role=roles/run.invoker --member=serviceAccount:$GE_SA
```

**Attendu :** `Updated IAM policy for service [meteo-a2a-shell].` Un autre agent : `K=taille`, relancer.

**Vérifier les deux :**

```bash
gcloud projects get-iam-policy $PROJET_AGENTS --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
gcloud run services get-iam-policy $K-a2a-shell --region=$REGION --project=$PROJET_AGENTS \
  --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"
```

**Attendu :** `roles/discoveryengine.serviceAgent`, puis `roles/run.invoker`.

### 5.4 Ajouter un agent Agent Runtime dans l'app

```bash
K=meteo
RES=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
  | python3 -c "import json,sys; print(next(e['name'] for e in json.load(sys.stdin)['reasoningEngines'] if e['displayName']=='$K-shell'))")
echo $RES
NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
./scripts/add_agent_to_ge.sh adk "$RES" "$NOM" "$DESC"
```

**Attendu :** `projects/100000000002/locations/europe-west1/reasoningEngines/<ID>`, puis `droit accordé : …` (déjà
fait en 4.2, sans effet), puis `ajouté : projects/…/agents/<ID>`.

**Ce que fait `add_agent_to_ge.sh adk`, en clair :** un appel `POST` à l'API de l'app :
`https://eu-discoveryengine.googleapis.com/v1alpha/projects/acme-gemini-prod/locations/eu/collections/default_collection/engines/dev_gemini-entreprise-app/assistants/default_assistant/agents`,
avec le corps `{"displayName": "Météo & équipement", "description": "…", "adkAgentDefinition":
{"provisionedReasoningEngine": {"reasoningEngine": "<RES>"}}}`. C'est exactement ce que fait le bouton de la console
([12-1-6, 4.1](12-1-6-ajouter-agent-console-gemini-enterprise.md)).

### 5.5 Ajouter un agent A2A (Cloud Run) dans l'app

```bash
K=meteo
python3 scripts/carte_a2a.py $K https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app > carte-$K.json
NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
./scripts/add_agent_to_ge.sh a2a carte-$K.json "$NOM (A2A)"
./scripts/add_agent_to_ge.sh list
```

**Attendu :** `ajouté : projects/…/agents/<ID>`, puis la liste avec « Météo & équipement (A2A) » `a2aAgentDefinition`.
Le corps envoyé : `{"displayName": "Météo & équipement (A2A)", "a2aAgentDefinition": {"jsonAgentCard": "<la carte>"}}`.

---

## 6. Méthode 3 : Terraform (agents déployés avec 12-1-2)

Les agents déployés par Terraform se connectent par Terraform (noms `meteo-a2a`, `meteo-agent`).

1. **Les droits :** remplir `PROJET_APP`, `NUM_APP`, `APP_ID` (partie 2), garder `PUBLIER=non`, recharger, puis dans
   chaque dossier : `terraform plan`.

   | Dossier | Lignes nouvelles au plan |
   |---|---|
   | `01-bis-cloud-run-a2a` | une ligne `google_cloud_run_v2_service_iam_member.ge_invokes["<clé>"]` **par agent** (droit `run.invoker`) |
   | `02-bis-agent-runtime` | une ligne `google_project_iam_member.ge_uses_agents_project[0]` (droit sur le projet) |

   **Rien d'autre** (`0 to change, 0 to destroy`). `terraform apply`. Puis simulez ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)).
2. **L'ajout dans l'app :** `PUBLIER=oui`, recharger, `terraform plan` → `google_project_service.ge[0]` (API de l'app,
   déjà active : sans effet) et une ligne `terraform_data.publish["<clé>"]` par agent. `terraform apply` → une ligne
   `registered <nom>` par agent. Noms dans l'app : « Météo & équipement » (Agent Runtime), « Météo & équipement (A2A) ».
3. L'accès et le test : [partie 7](#7-donner-laccès-et-tester-dans-le-chat).

Détails et retour arrière (`PUBLIER=non` puis `apply` retire les agents de l'app) :
[12-1, B4 et B5](12-1-agents-projet-exp-vers-app.md#b5-publier-dans-lapp-donner-laccès-tester-dans-le-chat).

---

## 7. Donner l'accès et tester dans le chat

Ces deux étapes se font dans la **console** de Gemini Enterprise (pas de script : l'accès est un choix humain).
Le pas à pas complet, avec chaque clic : [12-1-6, parties 5 et 6](12-1-6-ajouter-agent-console-gemini-enterprise.md).
En bref :

1. Projet `acme-gemini-prod` → 🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` → **Agents** → l'agent.
2. **Autorisations utilisateur** (*User permissions*) → **Ajouter** → l'adresse du groupe (`GROUPE_UTILISATEURS`, ou
   votre adresse pour le 1er test) → rôle **Agent User** → **Enregistrer**.
3. Test : l'app → **Intégration** → **lien de l'app web** → connecté avec un membre du groupe (licence Gemini
   Enterprise) → **Agents** → l'agent → une question d'exemple (« Quel temps à Chamonix demain ? »).

**Attendu :** une réponse (20 à 40 s la 1re fois : l'agent démarre). Côté agents : 🔎 « Cloud Run » → le service →
**Journaux** (A2A) ou 🔎 « Agent Runtime » → l'agent → **Sessions**.

---

## 8. Revenir en arrière

| Pour… | Script | À la main |
|---|---|---|
| Masquer un agent tout de suite | — | Console : l'agent → **Autorisations utilisateur** → retirer le groupe |
| Retirer les agents de l'app **et** les droits `run.invoker` | `./scripts/connecter_app.sh retirer` (liste + confirmation) | `./scripts/add_agent_to_ge.sh delete "Météo & équipement"` ; `gcloud run services remove-iam-policy-binding meteo-a2a-shell --region=$REGION --project=$PROJET_AGENTS --role=roles/run.invoker --member=serviceAccount:$GE_SA` |
| Retirer aussi le droit sur le projet | `./scripts/connecter_app.sh retirer --tout` | `gcloud projects remove-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA` |

**Résultat obtenu** (`retirer taille --tout`) :

```
== Retour arrière :
   - retirer run.invoker de l'app sur taille-a2a-shell
   - retirer discoveryengine.serviceAgent de l'app sur le projet aiml-gemini-ent-exp-0zga (TOUS ses agents Agent Runtime)
Updated IAM policy for service [taille-a2a-shell].
retiré : run.invoker sur taille-a2a-shell
Updated IAM policy for project [aiml-gemini-ent-exp-0zga].
retiré : discoveryengine.serviceAgent sur aiml-gemini-ent-exp-0zga
```

Vérifié ensuite par la simulation : `REFUSÉ` pour Cloud Run et Agent Runtime.

> ⚠ Le droit **sur le projet** vaut pour **tous** les agents Agent Runtime de `aiml-gemini-ent-exp-0zga` : ne le retirez
> que si l'app n'en utilise plus aucun.

---

## 9. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `MANQUANT dans le fichier de configuration : PROJET_APP` | Valeurs de l'app vides | Partie 2, recharger |
| `KO NUM_APP=… mais … a le numéro …` | Mauvais numéro | Le corriger (partie 2) |
| `KO app … introuvable en eu` | Mauvais `APP_ID` ou `GE_LOCATION` | `./scripts/connecter_app.sh apps` |
| `KO région … incompatible` | Agents hors `europe-*` pour une app `eu` | Redéployer dans `europe-west1` |
| `Aucun agent déployé (méthode shell)` | Agents déployés par la console ou Terraform | `--methode console` ; Terraform : partie 6 |
| `PERMISSION_DENIED` sur `droits` | Pas le droit de modifier l'IAM du projet des agents | Rôles de la partie 1, ou envoyer à l'équipe des agents le message de la partie 3.5 |
| `curl: (22) … 403` sur `ajouter` | Pas Gemini Enterprise Admin | `roles/discoveryengine.admin` sur le projet de l'app |
| `déjà dans l'app : Nom (…)` | Agent déjà ajouté | Rien ; pour le refaire : `add_agent_to_ge.sh delete "Nom"` puis relancer |
| Dans le chat : « L'agent n'a pas pu répondre » | Droit manquant ou pas encore actif | `verifier` ; attendre 2 à 3 minutes ; simuler ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)) |
| Agent absent du chat | Pas d'Agent User pour ce compte, ou pas de licence | Partie 6 |
| Réponse « filtrée par Model Armor » | Le filtre de l'agent a bloqué la question (ou ses droits Model Armor manquent) | Tester l'agent seul (12-1-1, 7.3) |
