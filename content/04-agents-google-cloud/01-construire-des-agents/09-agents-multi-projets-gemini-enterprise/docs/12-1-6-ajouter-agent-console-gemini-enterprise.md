# 12-1-6. Ajouter un agent dans l'app Gemini Enterprise : méthode **console** (interface Google Cloud)

**Le but :** dans l'app Gemini Enterprise **de production** de Acme, **à la souris**, ajouter un agent déjà en
ligne, donner l'accès à un groupe, et le tester dans le chat. Mode par mode : Agent Runtime, A2A (Cloud Run),
Dialogflow.

**On part de là :**
- les agents sont déployés et répondent dans le projet des agents `aiml-gemini-ent-exp-0zga`
  ([12-1-1 Shell](12-1-1-deployer-agents-shell.md) · [12-1-2 Terraform](12-1-2-deployer-agents-terraform.md) ·
  [12-1-3 Console](12-1-3-deployer-agents-console.md)) ;
- l'app a le droit de les appeler ([12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md)) ;
- la simulation a répondu `ACCEPTÉ` ([12-1-5](12-1-5-simuler-appel-gemini-enterprise.md)).

**Ici, on ne touche qu'à l'app Gemini Enterprise.** Aucun rôle IAM, aucune API, aucun agent n'est créé ou modifié.

> **Pas testé en vrai.** Les projets de test n'ont pas d'app Gemini Enterprise : les écrans sont décrits d'après la
> documentation officielle de Google (liens en fin de guide). Les libellés sont donnés **en anglais**, comme dans la
> documentation, avec la traduction probable quand la console est en français : ils peuvent légèrement varier selon la
> langue et la version de la console. Les commandes citées (scripts, `curl`, `terraform output`) sont celles des
> guides 12-1-1 et 12-1-2.

---

## Sommaire

0. [Avant de commencer](#0-avant-de-commencer)
1. [Production : les règles de prudence](#1-production--les-règles-de-prudence)
2. [Ouvrir l'app et noter ses valeurs](#2-ouvrir-lapp-et-noter-ses-valeurs)
3. [Récupérer, dans le projet des agents, ce que l'app demande](#3-récupérer-dans-le-projet-des-agents-ce-que-lapp-demande)
4. [Ajouter l'agent dans l'app, mode par mode](#4-ajouter-lagent-dans-lapp-mode-par-mode)
5. [Donner l'accès aux utilisateurs](#5-donner-laccès-aux-utilisateurs)
6. [Tester dans le chat](#6-tester-dans-le-chat)
7. [Modifier ou retirer un agent](#7-modifier-ou-retirer-un-agent)
8. [Ce qui peut arriver](#8-ce-qui-peut-arriver)

---

## 0. Avant de commencer

**Les valeurs de ce guide :**

| | Projet de l'**app** | Projet des **agents** |
|---|---|---|
| ID du projet | `acme-gemini-prod` | `aiml-gemini-ent-exp-0zga` |
| Numéro du projet | `523307489860` | `433175138344` |
| Emplacement | `eu` (multirégion de l'app) | `europe-west1` (région des agents) |
| Ce qu'on y trouve | l'app `dev_gemini-entreprise-app` | les services Cloud Run, les agents Agent Runtime |

**Les noms des agents** (exemple `meteo`), selon la méthode de déploiement :

| Méthode | Service Cloud Run (A2A) | Agent Agent Runtime |
|---|---|---|
| Shell (12-1-1) | `meteo-a2a-shell` | `meteo-shell` |
| Terraform (12-1-2) | `meteo-a2a` | `meteo-agent` |
| Console (12-1-3) | `meteo-a2a-console` | `meteo-console` |

**La liste à cocher :**

| ✔ | Quoi | Comment le vérifier |
|---|---|---|
| ☐ | L'agent est en ligne et répond | Cloud Run : coche verte ; Agent Runtime : le **Playground** répond ([12-1-3, partie 9](12-1-3-deployer-agents-console.md)) |
| ☐ | L'app a le droit de l'appeler | [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md) fait ; `./scripts/connecter_app.sh verifier` ne signale rien |
| ☐ | La simulation est passée | [12-1-5](12-1-5-simuler-appel-gemini-enterprise.md) : `ACCEPTÉ (A2A v0.3) : …` ou `ACCEPTÉ (Agent Runtime) : …` |
| ☐ | **Vous** êtes admin de l'app | 🔎 « IAM » dans le projet **de l'app** : votre adresse a **Gemini Enterprise Admin** (`roles/discoveryengine.agentspaceAdmin`) ou **Discovery Engine Admin** (`roles/discoveryengine.admin`) |
| ☐ | Les **utilisateurs** ont une **licence** Gemini Enterprise | Demander à l'administrateur des licences ; sans licence, l'agent ne s'affiche pas |
| ☐ | Le **groupe** existe | Ex. `equipe-agents@acme.example`, sur [groups.google.com](https://groups.google.com) ou dans la console d'administration Google Workspace |

---

## 1. Production : les règles de prudence

C'est l'app **que les collaborateurs utilisent**. Quatre règles :

1. **Un seul agent d'abord.** Ajoutez `meteo` seul, testez-le jusqu'au bout (parties 4 à 6), **puis** les autres.
2. **Un petit groupe de test d'abord.** Donnez l'accès à **votre adresse** ou à un groupe de 2 ou 3 testeurs.
   Le groupe de toute l'équipe (`equipe-agents@acme.example`) seulement quand tout marche.
3. **Savoir retirer vite** (partie 7) :
   - **le plus rapide :** retirer le groupe dans **User permissions** de l'agent : l'agent disparaît pour eux, il reste
     dans l'app ;
   - **définitif :** supprimer l'agent de l'app (`./scripts/add_agent_to_ge.sh delete "Météo & équipement"`). L'agent
     lui-même (Cloud Run, Agent Runtime) n'est **pas** touché.
4. **Rien ici ne change l'IAM.** Ajouter un agent ou donner **Agent User** ne crée aucun rôle sur les projets. Les
   droits de l'app sur les agents se donnent (et se retirent) en [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md).

Et : **jamais deux agents du même nom** dans l'app (les utilisateurs ne sauraient pas lequel choisir, et les scripts
retrouvent les agents par leur nom).

> **Quota.** Chaque ajout consomme une unité du quota quotidien de création d'agents du projet de l'app (documentation
> Google). En cas d'erreur `429 RESOURCE_EXHAUSTED`, réessayez le lendemain.

---

## 2. Ouvrir l'app et noter ses valeurs

1. [console.cloud.google.com](https://console.cloud.google.com), avec votre compte.
2. En haut, le **sélecteur de projet** → choisir **`acme-gemini-prod`** (le projet **de l'app**, pas celui
   des agents).
3. 🔎 « Gemini Enterprise » → la page **Apps** (*Applications*) s'ouvre : la liste des apps du projet.
4. **Repérer l'app** et noter :

| Valeur | Où la lire | Ici |
|---|---|---|
| **APP_ID** (ID de l'app) | Colonne **ID** de la liste, ou l'app → **Overview** (*Aperçu*) | `dev_gemini-entreprise-app` |
| **Emplacement** | Colonne **Location** (*Emplacement*) de la liste | `eu` |
| **Numéro du projet** | 🔎 « Tableau de bord » (ou **Accueil**) → carte *Informations sur le projet* → **Numéro du projet** | `523307489860` |
| **Compte de service de l'app** | Se déduit du numéro : `service-<numéro>@gcp-sa-discoveryengine.iam.gserviceaccount.com` | `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` |

**Où voir ce compte :** c'est lui qui appelle les agents. Dans le projet **des agents**, 🔎 « IAM » : il y figure
(après [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md)) avec **Discovery Engine Service Agent** et/ou, sur
chaque service Cloud Run, **Demandeur Cloud Run** (*Cloud Run Invoker*). Dans le projet de l'app, cochez **Inclure les
attributions de rôles fournies par Google** pour le voir. Vous n'avez **rien** à faire avec ce compte ici.

**Les mêmes valeurs en commandes** (configuration chargée, comme en 12-1-4) :

```bash
./scripts/connecter_app.sh apps                    # LECTURE SEULE : APP_ID (1re colonne), emplacement (2e), nom
gcloud projects describe acme-gemini-prod --format='value(projectNumber)'    # 523307489860
```

**Accès direct à la page des agents de l'app** (le lien que Terraform affiche dans `ge_agents_page`) :
`https://console.cloud.google.com/gemini-enterprise/locations/eu/engines/dev_gemini-entreprise-app/agents?project=acme-gemini-prod`

---

## 3. Récupérer, dans le projet des agents, ce que l'app demande

Changez de projet en haut : **`aiml-gemini-ent-exp-0zga`**. Ce que l'app demandera dépend du mode :

| Mode dans l'app | Ce qu'il faut | Ressemble à |
|---|---|---|
| Agent Runtime | le **nom de ressource** de l'agent | `projects/100000000002/locations/europe-west1/reasoningEngines/5685752748113395712` |
| A2A (Cloud Run) | la **carte d'agent** (JSON) | `{"protocolVersion": "0.3", "name": "meteo_agent", …}` |
| Dialogflow | la **source de l'agent** | `projects/…/locations/europe-west1/agents/…` |

### 3.1 Agent Runtime : le nom de ressource

**Console :** 🔎 « Agent Runtime » (anciennement « Agent Engine », dans Vertex AI) → **Déploiements** → l'agent
(`meteo-shell`, `meteo-agent` ou `meteo-console`) → **en haut de la page**, le **nom de ressource**
`projects/100000000002/locations/europe-west1/reasoningEngines/<ID>` → **copier**.

**Ou en commande** (12-1-1, 8.2) :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://europe-west1-aiplatform.googleapis.com/v1/projects/aiml-gemini-ent-exp-0zga/locations/europe-west1/reasoningEngines" \
  | python3 -c 'import json,sys; [print(e["displayName"], e["name"]) for e in json.load(sys.stdin).get("reasoningEngines",[])]'
```

**Attendu :** une ligne par agent, `meteo-shell projects/100000000002/locations/europe-west1/reasoningEngines/…`.
Copiez la 2e colonne.

**Ou, déployé par Terraform** (12-1-2) :

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform && terraform output agents
```

La région doit commencer par `europe-` : l'app est en `eu` (règle Google : app `eu` → agents en `europe-*`).

### 3.2 A2A (Cloud Run) : la carte de l'agent

La carte se fabrique avec le script du dépôt, à partir de l'**URL du service** (🔎 « Cloud Run » → le service → URL
qui contient `433175138344`) :

```bash
python3 scripts/carte_a2a.py meteo https://meteo-a2a-shell-433175138344.europe-west1.run.app > carte-meteo.json
cat carte-meteo.json
```

**Attendu :** **une seule ligne** de JSON, qui commence par `{"protocolVersion": "0.3", "name": "meteo_agent", …`.
**Copiez-la en entier**, du premier `{` au dernier `}` (une ligne : rien à couper par erreur). Remplacez
`meteo-a2a-shell` par `meteo-a2a-console` si l'agent a été déployé par la console.

**Ou, déployé par Terraform** (12-1-2 ; la sortie `cards` contient une carte par agent) :

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
terraform output -json cards | python3 -c 'import json,sys; print(json.load(sys.stdin)["meteo"])'
```

**Ou la lire sur l'agent en ligne** (c'est la même, servie par l'agent) :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://meteo-a2a-shell-433175138344.europe-west1.run.app/.well-known/agent-card.json
```

(Elle contient en plus un champ `supportedInterfaces`, sans effet. Préférez `carte-meteo.json`.)

**Les champs qui comptent** (détail : [12-1-1, 7.6](12-1-1-deployer-agents-shell.md#76-la-carte-de-lagent-pour-gemini-enterprise)) :

| Champ | Doit valoir |
|---|---|
| `protocolVersion` | `"0.3"` : la version d'A2A que Gemini Enterprise attend |
| `url` | **exactement** l'URL du service : `https://meteo-a2a-shell-433175138344.europe-west1.run.app` |
| `name`, `description` | ce que l'app affiche ; la description sert au modèle pour choisir l'agent |
| `skills` | les compétences, chacune avec `id`, `name`, `description`, `tags` |

### 3.3 Dialogflow : la source de l'agent

🔎 « Conversational Agents » → l'agent (ex. `Accueil magasin`) → **Paramètres de l'agent** (*Agent settings*) → copier
le nom `projects/…/locations/europe-west1/agents/<ID>`.

> **Où créer l'agent Dialogflow :** la documentation Google le décrit dans le projet **de l'app** ; un agent Dialogflow
> dans un autre projet n'y est pas documenté. Pour ce mode, créez-le dans `acme-gemini-prod` :
> [12-2](12-2-agents-dans-projet-app.md).

### 3.4 Agent Registry : import depuis le catalogue

La tuile **Agents from Agent Registry** de l'app ne lit que le catalogue **du projet de l'app** : les agents du projet
`aiml-gemini-ent-exp-0zga` n'y apparaissent pas. Pour ce mode : [12-2](12-2-agents-dans-projet-app.md). Ici, utilisez
Agent Runtime ou A2A.

---

## 4. Ajouter l'agent dans l'app, mode par mode

**Le chemin commun, pour tous les modes :**

1. Sélecteur de projet en haut : **`acme-gemini-prod`**.
2. 🔎 « Gemini Enterprise » → **Apps** → cliquer sur le **nom** de l'app (`dev_gemini-entreprise-app`).
3. Menu de gauche de l'app : **Agents**.
4. **+ Add agent** (*+ Ajouter un agent*). Le panneau **Choose an agent type** (*Choisir un type d'agent*) s'ouvre,
   avec des tuiles :

| Tuile | Pour | Ici |
|---|---|---|
| **Custom agent via Agent Runtime** (*Agent personnalisé via Agent Runtime*) | Un agent ADK sur Agent Runtime | 4.1 |
| **Custom agent via A2A** (*Agent personnalisé via A2A*) | Un agent A2A (nos services Cloud Run) | 4.2 |
| **Custom agent via Dialogflow** (*Agent personnalisé via Dialogflow*) | Un agent Dialogflow | 4.3 |
| **Agents from Agent Registry** | Le catalogue du projet de l'app | [12-2](12-2-agents-dans-projet-app.md) |
| Marketplace / agents Google | Des agents tout faits | Hors sujet ici |

**Les noms à donner** (les mêmes que les scripts et Terraform, pour s'y retrouver) :

| Agent | Mode Agent Runtime | Mode A2A |
|---|---|---|
| `meteo` | `Météo & équipement` | `Météo & équipement (A2A)` |
| `taille` | `Conseil taille` | `Conseil taille (A2A)` |
| Les autres | le `nom_affiche` de `agents/trio/catalogue.json` | le même + ` (A2A)` |

Si l'agent est déjà dans l'app sous ce nom (via le script ou Terraform) : **ne l'ajoutez pas une deuxième fois**.

### 4.1 Agent Runtime

5. Sur la tuile **Custom agent via Agent Runtime** → **Add** (*Ajouter*).
6. Écran **Authorizations** (*Autorisations*) : **n'ajoutez rien** (nos agents n'agissent pas au nom de l'utilisateur).
   → **Next** (*Suivant*). Agent qui doit agir avec le compte de l'utilisateur (OAuth) :
   [12-1-7](12-1-7-agents-oauth-identite-outils.md).
7. Écran de configuration :

| Champ | Valeur |
|---|---|
| **Agent name** (*Nom de l'agent*) | `Météo & équipement` |
| **Describe your agent** (*Décrivez votre agent*) | La `description` du catalogue : `Météo réelle d'une ville (jusqu'à 7 jours) et équipement conseillé pour faire du sport dehors.` |
| **Agent Runtime** (chemin de la ressource) | Le nom copié en 3.1 : `projects/100000000002/locations/europe-west1/reasoningEngines/<ID>` |

8. **Create** (*Créer*).

**Attendu :** retour à la liste **Agents**, avec `Météo & équipement` (type Agent Runtime / ADK).

### 4.2 A2A (Cloud Run)

5. Sur la tuile **Custom agent via A2A** → **Add** (*Ajouter*).
6. Champ **Agent card JSON** (*JSON de la carte d'agent*) : **coller** toute la carte copiée en 3.2.
7. **Preview agent details** (*Prévisualiser les détails de l'agent*). **Attendu :** le nom, la description et les
   compétences de la carte s'affichent (pour `meteo` : « Météo d'une ville », « Quoi porter »). Sinon : partie 8.
8. **Next** (*Suivant*).
9. Écran d'autorisation (Client ID, Client secret…) : **ne remplissez rien** → **Skip & Finish** (*Ignorer et terminer*).
   Les champs OAuth ne servent que si l'agent agit avec le compte de l'utilisateur :
   [12-1-7](12-1-7-agents-oauth-identite-outils.md).

**Attendu :** l'agent dans la liste **Agents**, type **A2A (Custom)**.

**Le nom affiché :** l'app reprend celui de la carte (`meteo_agent`). Pour le renommer en `Météo & équipement (A2A)` :
partie 7 (**Edit**), ou ajoutez-le par le script, qui prend le nom en paramètre :
`./scripts/add_agent_to_ge.sh a2a carte-meteo.json "Météo & équipement (A2A)"`.

### 4.3 Dialogflow

5. Sur la tuile **Custom agent via Dialogflow** → **Add** (*Ajouter*). Le panneau **Configuration** s'ouvre.

| Champ | Valeur |
|---|---|
| **Your agent name** (*Nom de votre agent*) | `Accueil magasin` |
| **Describe your agent** (*Décrivez votre agent*) | Une phrase : ce qu'il sait faire (le modèle s'en sert pour choisir l'agent) |
| **Dialogflow agent source** (*Source de l'agent Dialogflow*) | Le nom copié en 3.3 : `projects/…/locations/europe-west1/agents/<ID>` |
| **Agent availability** (*Disponibilité*) | Laisser **When selected** (*Lorsqu'il est sélectionné*) |

6. **Create** (*Créer*). **Attendu :** `Accueil magasin` dans la liste **Agents**.

---

## 5. Donner l'accès aux utilisateurs

Un agent ajouté n'est visible **de personne** tant qu'on ne l'a pas partagé.

1. App → **Agents** → cliquer sur le **nom** de l'agent (`Météo & équipement`).
2. Onglet **User permissions** (*Autorisations utilisateur*). La page **Permissioned users** s'affiche.
3. **Add user** (*Ajouter un utilisateur*). La fenêtre « Add user permissions roles to agent » s'ouvre.
4. Remplir :

| Champ | Valeur |
|---|---|
| Type de membre | **Group** (*Groupe*) ; **User** (*Utilisateur*) pour un premier test avec votre adresse |
| Membre | `equipe-agents@acme.example` (ou votre adresse pour le test) |
| **Assign role** (*Attribuer un rôle*) | **Agent User** (« Grants access to use agents ») |

5. **Save** (*Enregistrer*).

**Attendu :** le groupe dans la liste **Permissioned users**, avec **Agent User**.

| À savoir | |
|---|---|
| Le groupe | Un **groupe Google** (Google Workspace / [groups.google.com](https://groups.google.com)) : on gère les membres là-bas, sans retoucher l'agent |
| La licence | Chaque membre doit avoir une **licence Gemini Enterprise** ; sans elle, rien ne s'affiche |
| `GROUPE_UTILISATEURS` | Dans le fichier de configuration, c'est **seulement** cette adresse, notée pour mémoire et affichée par les scripts. Aucun script ne donne ce rôle : il se donne ici |
| Délai | Comptez quelques minutes avant que l'agent apparaisse chez les utilisateurs |

---

## 6. Tester dans le chat

1. App → menu de gauche **Integration** (*Intégration*) → copier le **lien de l'app web**.
2. L'ouvrir dans une **fenêtre de navigation privée**, connecté avec un **membre du groupe** (ou votre adresse, si c'est
   elle qui a reçu **Agent User**).
3. Dans l'app web : **Agents** → l'agent → poser la question d'exemple :

| Agent | Question (exemple du catalogue) |
|---|---|
| `meteo` | « Quel temps à Chamonix demain ? » |
| `taille` | « Je fais 98 cm de tour de poitrine, quelle taille de veste ? » |
| `traduction` | « Traduis en espagnol : Votre tente Quechua est disponible en retrait en magasin. » |
| `retour` | « J'ai acheté des chaussures il y a 40 jours, je peux les rendre ? » |
| `redaction` | « Reformule ce message pour un e-mail client : … » |
| `identite` | « Suis-je authentifié ? Avec quel compte ? » (agent OAuth : [12-1-7](12-1-7-agents-oauth-identite-outils.md)) |

**Attendu :** une réponse en **20 à 40 secondes** la première fois (l'agent démarre : *cold start*), plus vite ensuite.
Pour `meteo` : la météo de la ville et un conseil de tenue.

**Voir l'appel côté agents** (sélecteur de projet → `aiml-gemini-ent-exp-0zga`) :

| Mode | Où |
|---|---|
| A2A | 🔎 « Cloud Run » → `meteo-a2a-shell` → **Journaux** : une requête `POST` à l'heure du test |
| Agent Runtime | 🔎 « Agent Runtime » → **Déploiements** → `meteo-shell` → **Sessions** (une nouvelle conversation) et **Journaux** |

Rien dans les journaux alors que le chat affiche une erreur : l'app n'a pas pu appeler l'agent (partie 8).

**Ensuite :** les autres agents, **un par un** (parties 3 à 6), puis le groupe de toute l'équipe (partie 1).

---

## 7. Modifier ou retirer un agent

**Modifier** (nom, description, chemin, carte) : app → **Agents** → le **nom** de l'agent → **Edit** (*Modifier*) →
changer les champs (Agent Runtime : **Display name**, **Description**, chemin ; A2A : **Agent card JSON**) → **Save**
(*Enregistrer*).

**Retirer l'accès** (le plus rapide) : l'agent → **User permissions** → le groupe → supprimer (icône corbeille ou
**Remove**) → **Save**. L'agent reste dans l'app, invisible pour ce groupe.

**Supprimer de l'app :** la documentation Google ne décrit la suppression que par l'API. Dans la console, selon la
version : la liste **Agents** → le menu **⋮** de la ligne → **Delete** (*Supprimer*). Sinon, et pour être sûr, le script
(configuration chargée) :

```bash
./scripts/add_agent_to_ge.sh list                                # les agents de l'app : nom affiché, type, ID
./scripts/add_agent_to_ge.sh delete "Météo & équipement"         # nom affiché EXACT ; l'agent lui-même reste
```

**Tout défaire pour un agent** (le retirer de l'app **et** retirer les droits de l'app sur lui, demande confirmation) :

```bash
./scripts/connecter_app.sh retirer meteo
```

Les droits : voir [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md). L'agent (Cloud Run, Agent Runtime) se
supprime ensuite, s'il le faut, avec [12-1-3, partie 10](12-1-3-deployer-agents-console.md#10-ajouter-un-agent-plus-tard-en-retirer-un-tout-supprimer).

---

## 8. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| Pas de menu **Agents**, ou `403` / « permission denied » en ajoutant | Vous n'êtes pas admin de l'app, ou mauvais projet en haut | Projet `acme-gemini-prod` ; demander **Gemini Enterprise Admin** sur ce projet |
| L'app n'apparaît pas dans **Apps** | Mauvais projet sélectionné | Sélecteur → `acme-gemini-prod` ; `./scripts/connecter_app.sh apps` |
| **Preview agent details** refuse la carte | JSON **tronqué** (copie incomplète) | Recopier `cat carte-meteo.json` du premier `{` au dernier `}` |
| Carte refusée : version | `protocolVersion` différent de `"0.3"` | Regénérer avec `scripts/carte_a2a.py` (3.2) |
| L'agent A2A ne répond jamais | `url` de la carte différente de l'URL du service | Regénérer la carte avec l'URL **exacte** contenant `433175138344` ; partie 7 → **Edit** |
| Erreur de région à **Create** (Agent Runtime) | Agent hors Europe : une app `eu` n'accepte que des agents `europe-*` | Utiliser l'agent en `europe-west1` |
| Deux agents du même nom | Ajouté deux fois (console + script ou Terraform) | `./scripts/add_agent_to_ge.sh list`, puis supprimer le doublon (partie 7) |
| `429 RESOURCE_EXHAUSTED` | Quota quotidien de création d'agents atteint | Réessayer le lendemain |
| L'agent n'apparaît pas dans le chat | Pas d'**Agent User**, mauvais groupe, utilisateur hors du groupe, ou **pas de licence** | Partie 5 ; vérifier le groupe et la licence ; attendre quelques minutes |
| « The agent couldn't respond » (*l'agent n'a pas pu répondre*), rien dans les journaux de l'agent | L'app n'a pas le droit d'appeler l'agent : **Demandeur Cloud Run** (`run.invoker`) manquant (A2A) ou **Discovery Engine Service Agent** manquant (Agent Runtime) | [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md) ; attendre **2 à 3 minutes** ; rejouer la simulation [12-1-5](12-1-5-simuler-appel-gemini-enterprise.md) |
| Erreur, et une erreur dans les journaux de l'agent | Problème de l'agent lui-même (Model Armor, météo `429`…) | [12-1-3, partie 11](12-1-3-deployer-agents-console.md#11-ce-qui-peut-arriver) |
| Première réponse très lente | Démarrage de l'agent (*cold start*) | Normal : 20 à 40 s la première fois |
| Écrans ou libellés différents | Langue ou version de la console | Chercher l'équivalent ; même logique |

**Les sources Google :**
[ajouter un agent ADK (Agent Runtime)](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent) ·
[ajouter un agent A2A](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent) ·
[ajouter un agent Dialogflow](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-a-dialogflow-agent) ·
[partager un agent](https://docs.cloud.google.com/gemini/enterprise/docs/share-custom-agents) ·
[rôles et licences](https://docs.cloud.google.com/gemini/enterprise/docs/access-control).

**Les autres guides :** [12-1-4 Connecter (droits + script)](12-1-4-connecter-agents-app-gemini-enterprise.md) ·
[12-1-5 Simuler l'appel](12-1-5-simuler-appel-gemini-enterprise.md) ·
[12-1-7 Agents OAuth](12-1-7-agents-oauth-identite-outils.md) ·
[12-2 Agents dans le projet de l'app](12-2-agents-dans-projet-app.md) ·
[12-3 Ajouter des agents un par un](12-3-ajouter-des-agents-un-par-un.md).
