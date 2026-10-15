# 09. Connecter un agent à Gemini Enterprise : tous les modes d'ajout, et le pas à pas entre projets

**Pour qui :**
- **l'admin Gemini Enterprise**, qui possède l'app (projet A) ;
- **les équipes**, qui ont chacune **leur propre projet** Google Cloud (projet B) et veulent mettre leur agent dans l'app.

**Ce document répond à deux questions :**
1. Quand on clique sur **Ajouter un agent** dans Gemini Enterprise, que veut dire chaque choix, et que faut-il remplir ?
   ([partie 1](#partie-1--la-fenêtre-ajouter-un-agent) et [partie 2](#partie-2--chaque-mode-pas-à-pas))
2. Une équipe a son agent dans **son** projet : qui fait quoi, dans quel ordre, avec quelles commandes, pour qu'il
   réponde dans **notre** app ? ([partie 3](#partie-3--le-pas-à-pas-entre-projets))

> Pour **construire** et **déployer** l'agent lui-même : [docs/08](08-tuto-trio-pas-a-pas.md), puis
> [01-bis (Cloud Run + A2A)](../01-bis-cloud-run-a2a/README.md) ou [02-bis (Agent Runtime)](../02-bis-agent-runtime/README.md).
> Ce document commence quand l'agent est déployé et qu'il répond à son propre `./test.sh`.

---

## Sommaire

- [Le vocabulaire en 1 minute](#le-vocabulaire-en-1-minute)
- [Partie 1 : la fenêtre Ajouter un agent](#partie-1--la-fenêtre-ajouter-un-agent)
- [Partie 2 : chaque mode, pas à pas](#partie-2--chaque-mode-pas-à-pas)
  - [2.1 Agent personnalisé via Agent Runtime](#21-agent-personnalisé-via-agent-runtime)
  - [2.2 Agent personnalisé via A2A](#22-agent-personnalisé-via-a2a)
  - [2.3 Agent personnalisé via Dialogflow](#23-agent-personnalisé-via-dialogflow)
  - [2.4 Agents via Marketplace](#24-agents-via-marketplace)
  - [2.5 Agents depuis Agent Registry](#25-agents-depuis-agent-registry)
  - [2.6 Après l'ajout, pour tous les modes](#26-après-lajout-pour-tous-les-modes)
- [Partie 3 : le pas à pas entre projets](#partie-3--le-pas-à-pas-entre-projets)
- [Partie 4 : diagnostic](#partie-4--diagnostic)
- [Ce qui a été testé](#ce-qui-a-été-testé)

---

## Le vocabulaire en 1 minute

```
   PROJET A : l'app (admin Gemini Enterprise)                 PROJET B : l'agent (une équipe)
  ┌──────────────────────────────────────────┐              ┌─────────────────────────────────────────┐
  │ App Gemini Enterprise (eu)               │   appelle    │ L'agent, sur Agent Runtime ou Cloud Run │
  │                                          │ ───────────▶ │                                         │
  │ Compte de service de Gemini Enterprise : │              │ IAM : B donne UN droit au compte de A   │
  │ service-NUM_A@gcp-sa-discoveryengine     │ ◀─── droit ──│ (c'est B qui décide d'ouvrir son agent) │
  │        .iam.gserviceaccount.com          │              │                                         │
  └──────────────────────────────────────────┘              └─────────────────────────────────────────┘
```

| Terme | Ce que c'est | Où le trouver |
|---|---|---|
| **Projet A** | Le projet de l'app Gemini Enterprise | Sélecteur de projet de la console |
| **NUM_A** | Le **numéro** du projet A (12 chiffres, différent de son ID) | `gcloud projects describe PROJET_A --format='value(projectNumber)'` |
| **Le compte de Gemini Enterprise** | `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com`. C'est **lui** qui appelle les agents, jamais l'utilisateur | Projet A → IAM → cocher *Inclure les attributions de rôles fournies par Google* |
| **Projet B** | Le projet de l'équipe, où tourne l'agent | — |
| **ID de l'app** | Identifiant de l'app Gemini Enterprise | Gemini Enterprise → l'app → **Présentation** |

**La règle qui résume tout :** le droit est toujours donné **par le projet de l'agent (B)**, **au compte de Gemini
Enterprise (A)**. L'équipe garde la main sur son agent ; l'admin garde la main sur son app.

---

## Partie 1 : la fenêtre Ajouter un agent

**Où :** console Google Cloud → 🔎 « Gemini Enterprise » → cliquer sur **le nom de l'app** → onglet **Agents** →
**+ Ajouter un agent** (*Add agent*). Le volet **Choisir un type d'agent** (*Choose an agent type*) propose :

| Choix dans la fenêtre | Ce que vous fournissez | L'agent tourne où | Agent dans un **autre projet** ? | Droit à donner dans le projet de l'agent | Notre recommandation |
|---|---|---|---|---|---|
| **Agent personnalisé via Agent Runtime** (*Custom agent via Agent Runtime*) | Le **chemin de ressource** `projects/…/reasoningEngines/ID` | Agent Runtime (Google) | **Oui** | `roles/discoveryengine.serviceAgent` sur le **projet** B | **Par défaut** pour un agent ADK |
| **Agent personnalisé via A2A** (*Custom agent via A2A*) | La **carte d'agent** (JSON A2A v0.3) | N'importe où en HTTPS ; Cloud Run conseillé | **Oui** | `roles/run.invoker` sur **le service** Cloud Run | Agent sur Cloud Run, ou autre framework |
| **Agent personnalisé via Dialogflow** (*Custom agent via Dialogflow*) | La **source de l'agent Dialogflow** `projects/…/locations/…/agents/ID` | Dialogflow CX | Non documenté par Google : à valider | — | Agents conversationnels existants |
| **Agents via Marketplace** (*Agents via Marketplace*) | L'agent choisi dans la liste, puis ses identifiants | Chez l'éditeur | — (achat Marketplace) | — | Agents de partenaires, après achat |
| **Agents depuis Agent Registry** | L'agent choisi dans le registre relié à l'app | Agent Runtime, Cloud Run… | **Non** : Google indique que l'accès à un registre d'un autre projet n'est pas pris en charge | `roles/iap.egressor` (passerelle) + droit du mode d'origine | Gouvernance centrale, quand Agent Gateway est en place |

**Pour les agents des équipes dans leur propre projet : deux modes fonctionnent, Agent Runtime et A2A.** Les autres
sont soit hors code (Dialogflow, Marketplace), soit limités au projet de l'app (Agent Registry).

Hors de cette fenêtre, il existe aussi **Agent Designer** (bouton *Créer un agent* dans l'app web) : un agent **sans
code**, créé par l'utilisateur lui-même ([docs/07](07-autonomie-utilisateurs.md)).

**Avant de choisir :** les libellés français de la console peuvent varier légèrement selon la version ; l'ordre des
cartes aussi. Le libellé anglais, entre parenthèses, est celui de la documentation Google.

---

## Partie 2 : chaque mode, pas à pas

**Droit nécessaire pour ajouter un agent :** *Gemini Enterprise Admin* (`roles/discoveryengine.admin`) sur le projet A.

### 2.1 Agent personnalisé via Agent Runtime

**Avant :** l'agent est déployé sur Agent Runtime ([02-bis](../02-bis-agent-runtime/README.md)), dans une région
compatible avec l'app, et le droit est posé si l'agent est dans un autre projet ([partie 3](#partie-3--le-pas-à-pas-entre-projets)).

| App | Régions d'agent acceptées |
|---|---|
| `eu` | `europe-*` (Acme : `europe-west1`) |
| `us` | `us-*` |
| `global` | toutes |

**Console :**

1. Gemini Enterprise → l'app → **Agents** → **+ Ajouter un agent**.
2. Carte **Agent personnalisé via Agent Runtime** → **Ajouter**.
3. Remplir :

   | Champ | Quoi mettre | Exemple |
   |---|---|---|
   | **Nom de l'agent** (*Agent name*) | Le nom vu par les utilisateurs | `Traduction Acme` |
   | **Décrivez votre agent** (*Describe your agent*) | Une phrase précise : **le modèle s'en sert pour choisir l'agent** | `Traduit un texte en 7 langues européennes en respectant le glossaire et les marques Acme.` |
   | **Chemin de ressource Agent Runtime** (*Agent Runtime resource path*) | `projects/PROJET_B/locations/europe-west1/reasoningEngines/ID` | sortie `terraform output agents` |
   | **Icône** (optionnel) | URL publique ou image en Base64 | — |
   | **Autorisations** (optionnel) | Seulement si l'agent agit **au nom de l'utilisateur** (OAuth : ID client, secret, URI de jeton, URI d'autorisation) | Laisser vide pour nos agents |

4. **Créer**. L'agent apparaît dans la liste avec l'état *Actif*.

**En ligne de commande** (même résultat) :

```bash
export GE_PROJECT=aiml-gemini-entreprise-ldbr GE_APP=ID_DE_L_APP GE_LOCATION=eu
./scripts/add_agent_to_ge.sh adk projects/PROJET_B/locations/europe-west1/reasoningEngines/ID \
  "Traduction Acme" "Traduit un texte en 7 langues européennes en respectant le glossaire et les marques Acme."
```

Le script vérifie la région, pose le droit cross-project s'il le peut (sinon il affiche la commande à transmettre à
l'équipe), puis ajoute l'agent par l'API (`adkAgentDefinition.provisionedReasoningEngine.reasoningEngine`).

### 2.2 Agent personnalisé via A2A

**Avant :** l'agent est déployé et **sert sa carte** ([01-bis](../01-bis-cloud-run-a2a/README.md)), le droit
`run.invoker` est posé pour le compte de Gemini Enterprise ([partie 3](#partie-3--le-pas-à-pas-entre-projets)).

**Exigences de Google sur la carte** (toutes respectées par 01-bis) :

| Exigence | Valeur |
|---|---|
| `protocolVersion` | `"0.3"` (A2A v0.3, avec streaming) |
| `url` | L'adresse où Gemini Enterprise envoie les messages. Sur Cloud Run : l'URL **par défaut** `https://SERVICE-NUM_B.REGION.run.app` (l'authentification automatique ne marche pas avec un domaine personnalisé) |
| `name`, `description`, `skills`, `defaultInputModes`, `defaultOutputModes`, `version`, `capabilities` | Présents |
| Sécurité | Les champs `security` / `securitySchemes` de la carte sont **ignorés** ; pas de clé d'API ni d'en-tête fixe |

**Comment Gemini Enterprise s'authentifie :** il envoie un jeton OIDC **de son compte de service** dans l'en-tête
`X-Serverless-Authorization`. Cloud Run le vérifie : il faut donc `roles/run.invoker` sur le service. Le service reste
**privé**.

**Console :**

1. Gemini Enterprise → l'app → **Agents** → **+ Ajouter un agent**.
2. Carte **Agent personnalisé via A2A** → **Ajouter**.
3. **Coller le contenu JSON** de la carte (le JSON lui-même, pas son URL). Pour un agent de 01-bis :
   ```bash
   terraform -chdir=01-bis-cloud-run-a2a/terraform output -json cards | python3 -c 'import json,sys; print(json.load(sys.stdin)["traduction"])'
   ```
4. **Prévisualiser les détails de l'agent** (*Preview agent details*) : vérifier le nom, la description, les compétences.
   → **Suivant**.
5. **Authentification** : **ignorer** pour un agent qui n'agit pas au nom de l'utilisateur. (Sinon : identifiants OAuth.)
6. **Terminer**.

**En ligne de commande :**

```bash
./scripts/add_agent_to_ge.sh a2a https://traduction-a2a-NUM_B.europe-west1.run.app/.well-known/agent-card.json "Traduction (A2A)"
```

**À savoir :** le trafic A2A ne passe **pas** par Agent Gateway, et Model Armor de l'app ne filtre **pas** l'agent :
c'est pour ça que nos agents ont Model Armor dans leur code.

### 2.3 Agent personnalisé via Dialogflow

1. **Avant :** l'agent Dialogflow CX est déployé (console *Conversational Agents*), l'API Discovery Engine est activée.
2. Gemini Enterprise → l'app → **Agents** → **+ Ajouter un agent** → carte **Agent personnalisé via Dialogflow** → **Ajouter**.
3. Remplir **Nom de votre agent** (*Your agent name*), **Décrivez votre agent**, **Source de l'agent Dialogflow**
   (*Dialogflow agent source*) : `projects/PROJET/locations/LOCATION/agents/ID_AGENT`.
4. **Créer**.

**Autre projet :** Google ne documente pas le droit à donner. Piste à valider : `roles/dialogflow.client` pour le compte de
Gemini Enterprise dans le projet Dialogflow. Pour les agents des équipes, préférer Agent Runtime ou A2A.

### 2.4 Agents via Marketplace

1. **Avant :** l'agent a été **acheté** (*procured*) sur Google Cloud Marketplace par le service achats.
2. Gemini Enterprise → l'app → **Agents** → **+ Ajouter un agent** → carte **Agents via Marketplace** → **Ajouter**.
3. Rechercher l'agent → le sélectionner → **Suivant** → vérifier les détails → **Suivant**.
4. Saisir l'**authentification** demandée par l'éditeur → **Terminer**.

**Ce que voient les utilisateurs** dans la galerie d'agents : réglage de l'app (*Afficher seulement les agents achetés*,
par défaut ; *seulement les agents intégrés* ; *seulement les agents accessibles*). Passer par la sécurité et le DPO
avant tout achat : l'agent tourne **chez l'éditeur**.

### 2.5 Agents depuis Agent Registry

**Conditions (toutes) :**

| Condition | App `eu` |
|---|---|
| Une **Agent Gateway** reliée à l'app (tout le trafic de l'app passe alors par elle) | Passerelle en `europe-west1` |
| L'agent est dans **le registre relié à la passerelle**, dans le **même projet** que l'app | Registre `europe-west1` ou `eu` |
| Droit de passage | `roles/iap.egressor` sur l'entrée du registre, pour le compte de Gemini Enterprise |

**Procédure :** Gemini Enterprise → l'app → **Agents** → **+ Ajouter un agent** → choisir l'agent dans la liste du
registre → **Ajouter un agent** → vérifier → **Suivant** → identifiants du fournisseur si nécessaire → **Terminer**.
Mise en place de la passerelle : [docs/03, méthode 3](03-tuto-autre-projet.md#méthode-3--agent-registry--agent-gateway).

**Pour les agents des équipes :** leur registre est dans **leur** projet ; Google n'accepte pas l'import depuis le
registre d'un autre projet. Deux possibilités :
- ajouter l'agent par **Agent Runtime** (2.1) ou **A2A** (2.2) : fonctionne aujourd'hui, c'est la [partie 3](#partie-3--le-pas-à-pas-entre-projets) ;
- **déclarer** l'agent dans **notre** registre (projet A) avec sa carte, puis l'importer : [docs/04, voie 3](04-agents-deja-dans-un-registry.md).

Le registre de chaque équipe reste utile pour **trouver** ses agents (`python scripts/registry.py PROJET_B europe-west1`) et
pour les appels **agent → agent** ([docs/06](06-appels-entre-agents.md)).

### 2.6 Après l'ajout, pour tous les modes

1. **Qui peut l'utiliser :** app → **Agents** → l'agent → onglet **Autorisations utilisateur** (*User permissions*) →
   **Ajouter** → un **groupe** (jamais une liste de personnes) → rôle **Agent User** → **Enregistrer**.
   Sans cette étape, **personne** ne voit l'agent.
2. **Les utilisateurs ont une licence** Gemini Enterprise (Gemini Enterprise → **Licences**).
3. **Tester** avec un compte du groupe : lien de l'app web → **Agents** → l'agent → une question de son `./test.sh`.
4. **Retirer** : app → **Agents** → l'agent → **Supprimer**. L'agent reste déployé dans son projet.

---

## Partie 3 : le pas à pas entre projets

Le cas de nos utilisateurs : **chaque équipe a son projet B**, l'app est dans **notre projet A**. Ce parcours a été
**exécuté de bout en bout** sur deux vrais projets ([ce qui a été testé](#ce-qui-a-été-testé)).

```
 Étape   Qui                      Quoi
 ─────   ──────────────────────   ──────────────────────────────────────────────────────────────────────
   1     Admin GE (projet A)      Donne à l'équipe : NUM_A, région, (templates Model Armor) ; prépare le simulateur
   2     Équipe (projet B)        Prépare son projet (2 API, ses droits)
   3     Équipe (projet B)        Déploie l'agent ET donne le droit au compte de Gemini Enterprise
   4     Équipe (projet B)        Vérifie avec le simulateur : refusé sans droit, accepté avec
   5     Équipe → Admin           Envoie la fiche de demande (ressource ou carte, description, résultat du test)
   6     Admin GE (projet A)      Ajoute l'agent dans l'app (2.1 ou 2.2), donne Agent User au groupe
   7     Équipe + Admin           Testent dans le chat
```

Dans les commandes, remplacez :

```bash
export PROJET_APP=aiml-gemini-entreprise-ldbr                 # projet A
export NUM_APP=98547854221                         # numéro du projet A
export PROJET_AGENT=equipe-pricing-prod             # projet B
export GE_SA=service-$NUM_APP@gcp-sa-discoveryengine.iam.gserviceaccount.com
export SIMU=ge-simulateur@$PROJET_APP.iam.gserviceaccount.com
```

### Étape 1 : l'admin GE donne les informations, une fois pour toutes les équipes

```bash
gcloud projects describe $PROJET_APP --format='value(projectNumber)'      # NUM_APP
```

| Information à publier (page interne, wiki) | Valeur Acme |
|---|---|
| Numéro du projet de l'app | `NUM_APP` |
| Compte de Gemini Enterprise | `service-NUM_APP@gcp-sa-discoveryengine.iam.gserviceaccount.com` |
| Région imposée pour les agents | `europe-west1` (app `eu`) |
| Templates Model Armor (si centraux) | `projects/…/locations/eu/templates/…` (sortie du projet 08) |
| Compte simulateur | `ge-simulateur@PROJET_APP.iam.gserviceaccount.com` |

**Préparer le simulateur** (admin, une fois) : un compte de service du projet A qui recevra, dans chaque projet d'équipe,
**exactement les mêmes droits** que le compte de Gemini Enterprise. On ne peut pas emprunter le compte de Gemini
Enterprise lui-même ; le simulateur permet donc à chaque équipe de **prouver** que son agent est joignable **avant**
l'ajout dans l'app.

```bash
GE_PROJECT=$PROJET_APP ./scripts/simuler_gemini_enterprise.sh preparer
```

Pour qu'un membre d'une équipe puisse lancer le simulateur, l'admin lui donne le rôle *Créateur de jetons du compte de
service* **sur ce seul compte** :

```bash
gcloud iam service-accounts add-iam-policy-binding $SIMU --project=$PROJET_APP \
  --role=roles/iam.serviceAccountTokenCreator --member=group:equipe-pricing@acme.example
```

### Étape 2 : l'équipe prépare son projet

```bash
gcloud auth login && gcloud auth application-default login
gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com --project=$PROJET_AGENT
```

Droits de l'équipe sur **son** projet : voir [docs/08 §3.4](08-tuto-trio-pas-a-pas.md#34-vos-droits). **Aucun droit sur le
projet A** n'est nécessaire.

### Étape 3 : l'équipe déploie l'agent et donne le droit à Gemini Enterprise

**Avec nos modèles (recommandé)** : dans `02-bis-agent-runtime/terraform/terraform.tfvars` (ou `01-bis-…`) :

```hcl
agents_project_id = "equipe-pricing-prod"   # VOTRE projet
ge_project_number = "98547854221"          # NUM_APP, donné par l'admin
region            = "europe-west1"
ge_location       = "eu"
# ge_project_id et ge_app_id : NE PAS remplir (c'est l'admin qui publie)
```

```bash
terraform init && terraform apply
```

Terraform déploie les agents **et** pose le bon droit pour le compte de Gemini Enterprise. Il ne touche **jamais** au
projet A.

**Avec votre propre agent** (déjà déployé autrement) : la commande selon le mode.

```bash
# Agent Runtime (mode 2.1) : sur le PROJET de l'agent
gcloud projects add-iam-policy-binding $PROJET_AGENT --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA

# Cloud Run / A2A (mode 2.2) : sur CHAQUE service, pas sur le projet
gcloud run services add-iam-policy-binding NOM_DU_SERVICE --region=europe-west1 --project=$PROJET_AGENT \
  --role=roles/run.invoker --member=serviceAccount:$GE_SA
```

**Vérifier que le droit est posé :**

```bash
gcloud projects get-iam-policy $PROJET_AGENT --flatten=bindings \
  --filter="bindings.members:$GE_SA" --format="value(bindings.role)"            # Agent Runtime
gcloud run services get-iam-policy NOM_DU_SERVICE --region=europe-west1 --project=$PROJET_AGENT \
  --flatten=bindings --filter="bindings.members:$GE_SA" --format="value(bindings.role)"   # Cloud Run
```

**Attendu :** `roles/discoveryengine.serviceAgent` (Agent Runtime) ou `roles/run.invoker` (Cloud Run).

### Étape 4 : l'équipe vérifie avec le simulateur (optionnel)

**4a. Sans droit, le simulateur doit être REFUSÉ** (preuve que le service est bien privé) :

```bash
export GE_PROJECT=$PROJET_APP
./scripts/simuler_gemini_enterprise.sh runtime projects/$PROJET_AGENT/locations/europe-west1/reasoningEngines/ID "Bonjour"
./scripts/simuler_gemini_enterprise.sh a2a https://NOM_DU_SERVICE-NUM_B.europe-west1.run.app "Bonjour"
```

**Attendu :** `REFUSÉ (403) : le compte de Gemini Enterprise n'a pas …`

**4b. Donner au simulateur les mêmes droits que Gemini Enterprise** (les commandes de l'étape 3, avec `$SIMU`) :

```bash
gcloud projects add-iam-policy-binding $PROJET_AGENT --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$SIMU                # Agent Runtime
gcloud run services add-iam-policy-binding NOM_DU_SERVICE --region=europe-west1 --project=$PROJET_AGENT \
  --role=roles/run.invoker --member=serviceAccount:$SIMU                                 # Cloud Run
```

**4c. Attendre 2 à 3 minutes, puis relancer les commandes de 4a.** Un droit IAM met jusqu'à quelques minutes à
s'appliquer : un `REFUSÉ` juste après 4b est normal (constaté au test : encore refusé à 60 secondes, accepté ensuite).

**Attendu :** `ACCEPTÉ (Agent Runtime) : …` ou `ACCEPTÉ (A2A v0.3) : …` avec la réponse de l'agent.

Ce test reproduit l'appel de Gemini Enterprise : même type de compte (compte de service du projet A), même droit, même
API (Agent Runtime) ou même en-tête (`X-Serverless-Authorization` pour Cloud Run).

**4d. Retirer les droits du simulateur** (il ne sert qu'au test) : mêmes commandes avec `remove-iam-policy-binding`.

```bash
gcloud projects remove-iam-policy-binding $PROJET_AGENT --condition=None \
  --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$SIMU
gcloud run services remove-iam-policy-binding NOM_DU_SERVICE --region=europe-west1 --project=$PROJET_AGENT \
  --role=roles/run.invoker --member=serviceAccount:$SIMU
```

### Étape 5 : l'équipe envoie la fiche de demande

À copier dans le ticket (ou la PR `external_adk_agents`, voir [README §4](../README.md#4-le-processus-proposé-pour-les-équipes)) :

```text
Agent à ajouter dans Gemini Enterprise
- Nom affiché             : Traduction Acme
- Description (1 phrase)  : Traduit un texte en 7 langues européennes en respectant le glossaire et les marques Acme.
- Mode d'ajout            : Agent Runtime   |   A2A
- Ressource (Agent Runtime) : projects/equipe-pricing-prod/locations/europe-west1/reasoningEngines/1234567890
  OU carte A2A (JSON)       : (pièce jointe, sortie `terraform output -json cards`)
- Projet / région         : equipe-pricing-prod / europe-west1
- Droit posé pour le compte GE : oui, le JJ/MM (commande de vérification de l'étape 3 : copie du résultat)
- Test simulateur (étape 4) : ACCEPTÉ, le JJ/MM (copie de la sortie)
- Model Armor dans l'agent : oui (templates : …)
- Données lues / actions faites par l'agent : aucune donnée personnelle ; lecture seule
- Groupe d'utilisateurs   : equipe-pricing@acme.example
- Contact                 : prenom.nom@acme.example
```

### Étape 6 : l'admin GE ajoute l'agent

1. Relire la fiche : région `europe-*`, Model Armor, données, test simulateur accepté.
2. Ajouter l'agent : [2.1](#21-agent-personnalisé-via-agent-runtime) (ressource) ou [2.2](#22-agent-personnalisé-via-a2a)
   (carte), en console ou avec `./scripts/add_agent_to_ge.sh`.
3. Donner **Agent User** au groupe indiqué ([2.6](#26-après-lajout-pour-tous-les-modes)).

### Étape 7 : tester dans le chat

1. L'équipe ouvre l'app web avec un compte du groupe → **Agents** → l'agent → les questions de son `./test.sh`.
2. **Attendu :** les mêmes réponses qu'à l'étape 4c. La première réponse peut prendre 20 à 40 secondes (démarrage).
3. **Où voir les traces :** dans le **projet B** (Agent Runtime → l'agent → **Sessions** / **Journaux** ; ou Cloud Run →
   le service → **Journaux**). L'utilisateur du chat apparaît dans la session (Agent Runtime).

---

## Partie 4 : diagnostic

| Symptôme | Où | Cause | Correction |
|---|---|---|---|
| L'agent n'apparaît pas pour l'utilisateur | Chat | Pas de rôle **Agent User** pour son groupe, ou pas de licence | 2.6 |
| Ajout refusé : région | Console | Agent hors `europe-*` pour une app `eu` | Redéployer en `europe-west1` |
| « L'agent n'a pas pu répondre » (Agent Runtime, autre projet) | Chat | `discoveryengine.serviceAgent` manquant dans le projet B | Étape 3, vérifier avec l'étape 4 |
| « L'agent n'a pas pu répondre » (A2A) ; `403` dans les journaux Cloud Run | Chat | `run.invoker` manquant **sur le service** | Étape 3, vérifier avec l'étape 4 |
| `404` dans les journaux Cloud Run | Projet B | `url` de la carte différente de l'URL du service | Corriger la carte, la remettre dans l'app |
| Prévisualisation de la carte refusée | Console | JSON tronqué, ou `protocolVersion` différent de `"0.3"` | Recopier la carte complète |
| Simulateur : `REFUSÉ (403)` après l'étape 4b | Terminal | Propagation IAM (jusqu'à quelques minutes), ou droit posé sur le mauvais projet / service | Attendre 2 à 3 min ; vérifier avec les commandes de l'étape 3 |
| Simulateur : erreur à la création du jeton | Terminal | Pas le rôle *Créateur de jetons* sur le simulateur | Étape 1 (dernier bloc) |
| Toutes les réponses : « … filtrée par Model Armor » | Chat | Model Armor bloque, ou l'agent n'a pas `modelarmor.user` sur le projet des templates | Journaux de l'agent ; droit sur le projet des templates |
| Erreur `PERMISSION_DENIED` avec `vpcServiceControlsUniqueIdentifier` | Journaux | Périmètre VPC Service Controls entre A et B | [docs/05 §3](05-droits-et-regions.md#3-si-vpc-service-controls-est-appliqué-projet-08) |

---

## Ce qui a été testé

**Test croisé réel, octobre 2026, deux projets Google Cloud :** projet A (rôle de l'app : API Gemini Enterprise activée,
son compte de service créé), projet B (rôle d'une équipe : projet neuf). L'app elle-même n'a pas pu être créée (compte
Gmail) : l'ajout dans l'app (étape 6) et le chat (étape 7) restent à constater dans l'app Acme.

| Étape | Test | Résultat |
|---|---|---|
| 2 | Projet B neuf : 2 API activées, rien d'autre | OK |
| 3 | 01-bis et 02-bis déployés dans B avec seulement `ge_project_number` ; **aucun accès** au projet A | OK : 32 et 28 ressources |
| 3 | Droit posé au **vrai** compte `service-NUM_A@gcp-sa-discoveryengine…` : `run.invoker` sur chaque service, `discoveryengine.serviceAgent` sur B | OK, vérifié par les commandes de l'étape 3 |
| 4a | Simulateur (compte de A) **sans** droit | `REFUSÉ (403)` en A2A et en Agent Runtime |
| 4b-4c | Simulateur **avec** les mêmes droits que Gemini Enterprise | `ACCEPTÉ` : réponse de l'agent, en A2A v0.3 (`X-Serverless-Authorization`) et en Agent Runtime (`discoveryengine.serviceAgent` suffit) |
| 4c | Service sans droit pour le simulateur (`meteo-a2a`) pendant que `traduction-a2a` en a un | `REFUSÉ` : le droit vaut **par service** |
| 4c | Délai d'application d'un droit | Encore refusé à 60 s, accepté ensuite (d'où « attendre 2 à 3 minutes ») |
| 4d | Retrait des droits du simulateur | OK |
| — | `terraform destroy` dans B | OK : tout supprimé |

Sources Google (octobre 2026) : [ajouter un agent ADK](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent),
[accès cross-project](https://docs.cloud.google.com/gemini/enterprise/docs/configure-cross-project-adk-agents),
[ajouter un agent A2A](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent),
[agent Dialogflow](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-a-dialogflow-agent),
[agents Marketplace](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-marketplace-agents),
[import depuis Agent Registry](https://docs.cloud.google.com/gemini/enterprise/docs/import-govern-agent-registry).
