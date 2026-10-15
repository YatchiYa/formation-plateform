# 12-1-3. Déployer les agents dans le projet des agents : méthode **console** (interface Google Cloud)

**Le but :** mettre en ligne **un**, **deux** ou **tous** les agents dans le projet des agents
`aiml-gemini-ent-exp-0zga`, **à la souris** dans la console Google Cloud
([console.cloud.google.com](https://console.cloud.google.com)), et savoir où tout retrouver.

**Pas encore d'app Gemini Enterprise.** On ne fait **que** les agents.

**Les autres méthodes, même résultat :** [12-1-1 Shell](12-1-1-deployer-agents-shell.md) ·
[12-1-2 Terraform](12-1-2-deployer-agents-terraform.md).

> **Deux choses ne se font pas à la souris**, et passent par **Cloud Shell**, le terminal intégré à la console :
> - **construire l'image** d'un agent (Cloud Run) ;
> - **envoyer le code** d'un agent à Agent Runtime.
>
> La console ne sait pas fabriquer une image à partir de notre code, ni envoyer un agent Python à Agent Runtime.
> Rien à installer : Cloud Shell a déjà gcloud et Python. Les images sont construites **dans Google Cloud** (Cloud
> Build) : ni Docker ni logiciel particulier.

> **Agents dans le projet de l'app (cas 12-2) ?** Identique, dans le projet de l'app.

> **Écrans décrits d'après la documentation Google.** Les libellés peuvent légèrement varier selon la langue et la
> version de la console. Les commandes de Cloud Shell sont celles testées en [12-1-1](12-1-1-deployer-agents-shell.md).

---

## Sommaire

0. [Ce que vous allez créer, et où le voir](#0-ce-que-vous-allez-créer-et-où-le-voir)
1. [Ouvrir la console sur le bon projet](#1-ouvrir-la-console-sur-le-bon-projet)
2. [Vérifier et activer les API](#2-vérifier-et-activer-les-api)
3. [Model Armor : les deux filtres (une fois)](#3-model-armor--les-deux-filtres-une-fois)
4. [Préparer Cloud Shell (une fois)](#4-préparer-cloud-shell-une-fois)
5. [Cloud Run (A2A) : un agent, puis plusieurs](#5-cloud-run-a2a--un-agent-puis-plusieurs)
6. [Agent Runtime : un agent, puis plusieurs](#6-agent-runtime--un-agent-puis-plusieurs)
7. [Agent Registry : le catalogue](#7-agent-registry--le-catalogue)
8. [Dialogflow (option)](#8-dialogflow-option)
9. [Vérification finale](#9-vérification-finale)
10. [Ajouter un agent plus tard, en retirer un, tout supprimer](#10-ajouter-un-agent-plus-tard-en-retirer-un-tout-supprimer)
11. [Ce qui peut arriver](#11-ce-qui-peut-arriver)

---

## 0. Ce que vous allez créer, et où le voir

Pour **chaque agent** (exemple : `meteo` ; liste des clés : `agents/trio/catalogue.json`), selon l'hébergement choisi :

| | **Cloud Run (A2A)** | **Agent Runtime** |
|---|---|---|
| Identité | compte de service `meteo-a2a-console-sa` | compte de service `meteo-console-sa` |
| Rôles du compte | Utilisateur Vertex AI, Rédacteur de journaux, Utilisateur Model Armor | les mêmes |
| L'agent | service Cloud Run `meteo-a2a-console` (image `agents-console/meteo:v1`) | agent Agent Runtime `meteo-console` |
| Catalogue | à **déclarer** dans Agent Registry | inscrit **automatiquement** |

**Une fois pour tous les agents :** les API, les 2 filtres Model Armor, le dépôt d'images `agents-console` et le compte
qui construit les images (`agents-build-sa`).

**Le vocabulaire** (agent, A2A, carte, Agent Runtime, Agent Registry, compte de service, rôle, API) :
[12-1-1, partie 0](12-1-1-deployer-agents-shell.md#0-les-mots-à-connaître).

| Quoi | 🔎 Rechercher (barre du haut) | Écran |
|---|---|---|
| API | « API et services » | **API et services activés** ; **Bibliothèque** pour en activer |
| Comptes de service | « Comptes de service » | Liste ; un clic → **Autorisations** |
| Rôles | « IAM » | Liste des comptes et de leurs rôles |
| Filtres | « Model Armor » | **Templates** |
| Images | « Artifact Registry » | Dépôts → `agents-console` |
| Cloud Run | « Cloud Run » | **Services** |
| Agent Runtime | « Agent Runtime » (anciennement « Agent Engine », dans Vertex AI) | **Déploiements** |
| Catalogue | « Agent Registry » | Région `europe-west1` |
| Dialogflow | « Conversational Agents » | Agents |
| Erreurs | « Journaux » (Logs Explorer) | Filtre par service |

---

## 1. Ouvrir la console sur le bon projet

1. [console.cloud.google.com](https://console.cloud.google.com), avec votre compte.
2. En haut, le **sélecteur de projet** → choisir `aiml-gemini-ent-exp-0zga`.
3. **Noter** son **numéro** : 🔎 « Tableau de bord » (ou **Accueil**) → carte *Informations sur le projet* →
   **Numéro du projet** : `433175138344`.
4. **Vos droits :** 🔎 « IAM » → votre adresse → **Propriétaire**, ou les rôles listés en
   [12-1-1, partie 4](12-1-1-deployer-agents-shell.md#4-se-connecter-vérifier-le-projet-et-vos-droits).

---

## 2. Vérifier et activer les API

🔎 « API et services » → **API et services activés**. Pour chaque API du tableau absente de la liste :
**+ Activer les API et les services** (ou **Bibliothèque**) → chercher son nom → **Activer** (1 à 2 minutes).

| Nom à chercher | Nom technique | Pour |
|---|---|---|
| Cloud Resource Manager API | `cloudresourcemanager.googleapis.com` | Tout |
| Service Usage API | `serviceusage.googleapis.com` | Tout |
| Identity and Access Management (IAM) API | `iam.googleapis.com` | Tout |
| Vertex AI API (Agent Platform) | `aiplatform.googleapis.com` | Tout (Gemini, Agent Runtime) |
| Model Armor API | `modelarmor.googleapis.com` | Tout |
| Cloud Logging API | `logging.googleapis.com` | Tout |
| Agent Registry API | `agentregistry.googleapis.com` | Catalogue |
| Cloud Run Admin API | `run.googleapis.com` | Cloud Run |
| Artifact Registry API | `artifactregistry.googleapis.com` | Cloud Run |
| Cloud Build API | `cloudbuild.googleapis.com` | Cloud Run (construire les images) |
| Dialogflow API | `dialogflow.googleapis.com` | Dialogflow seulement |

**Attendu :** toutes dans **API et services activés**. Une API affiche **Gérer** au lieu d'**Activer** : elle est déjà
active.

---

## 3. Model Armor : les deux filtres (une fois)

🔎 « Model Armor » → **Templates** → **Créer un template**, **deux fois** :

| Champ | 1er template | 2e template |
|---|---|---|
| ID du template | `console-prompt-shield` (les **questions**) | `console-response-shield` (les **réponses**) |
| Région | **Multirégion** → `eu` | idem |
| Détection des URL malveillantes | Activée | idem |
| Injection de prompt et jailbreak | Activée, confiance **Moyenne et supérieure** | idem |
| Protection des données sensibles | **De base**, activée | idem |
| IA responsable | Incitation à la haine, Harcèlement, Sexuellement explicite, Dangereux : **Moyenne et supérieure** | idem |
| Journalisation des opérations | Activée | idem |

**Créer.** **Attendu :** les deux dans la liste, région `eu`. Leurs chemins (ils serviront plus bas) :
`projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/console-prompt-shield` et `…/console-response-shield`.

---

## 4. Préparer Cloud Shell (une fois)

1. Icône **`>_`** en haut à droite de la console : **Activer Cloud Shell**. Un terminal s'ouvre en bas.
2. **Importer le dossier :** zippez `09-agents-multi-projets-gemini-enterprise` sur votre poste. Dans Cloud Shell, menu
   **⋮** → **Importer** → le zip. Puis :
   ```bash
   unzip -q 09-agents-multi-projets-gemini-enterprise.zip && cd 09-agents-multi-projets-gemini-enterprise
   ```
3. **Le fichier de configuration :** **Ouvrir l'éditeur** (bouton en haut de Cloud Shell) →
   `config/12-1-agents-dans-projet-exp.env`. Remplissez-le comme en
   [12-1-1, partie 3](12-1-1-deployer-agents-shell.md#3-le-fichier-de-configuration--quoi-écrire-ligne-par-ligne), avec :
   - `PROJET_APP=`, `NUM_APP=`, `APP_ID=` **vides** ;
   - `AGENTS="meteo"` (ou vos agents) ;
   - `DOSSIER=~/09-agents-multi-projets-gemini-enterprise` ;
   - deux lignes de plus, pour utiliser **vos** filtres de la partie 3 :
   ```bash
   PROMPT_TEMPLATE=projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/console-prompt-shield
   RESPONSE_TEMPLATE=projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/console-response-shield
   ```
4. **Charger :**
   ```bash
   source scripts/config.sh config/12-1-agents-dans-projet-exp.env
   ```
   **Attendu :** le résumé, `Agents à déployer : meteo`, puis `OK` (exemple complet en
   [12-1-1, partie 3](12-1-1-deployer-agents-shell.md#3-le-fichier-de-configuration--quoi-écrire-ligne-par-ligne)).

Cloud Shell se ferme après une période d'inactivité : rouvrez-le, `cd 09-agents-multi-projets-gemini-enterprise`, et
rechargez la configuration (étape 4). Vos fichiers sont conservés.

---

## 5. Cloud Run (A2A) : un agent, puis plusieurs

### 5.1 Le dépôt d'images (une fois)

🔎 « Artifact Registry » → **Dépôts** → **+ Créer un dépôt** :

| Champ | Valeur |
|---|---|
| Nom | `agents-console` |
| Format | **Docker** |
| Type d'emplacement | **Région** → `europe-west1` |

**Créer.** **Attendu :** `agents-console` dans la liste. (« Docker » est le nom du **format** des images : pas besoin du
logiciel Docker.)

**Le compte qui construit les images** (une fois) : 🔎 « Comptes de service » → **+ Créer un compte de service** →
**Nom** `agents-build-sa` → **Créer et continuer** → rôles :

| Rôle (nom affiché) | Pourquoi |
|---|---|
| **Lecteur des objets Storage** (*Storage Object Viewer*) | Lire le code envoyé |
| **Rédacteur Artifact Registry** (*Artifact Registry Writer*) | Ranger l'image dans le dépôt |
| **Rédacteur de journaux** (*Logs Writer*) | Écrire le journal de construction |

→ **OK**. Pourquoi un compte à nous : celui que Cloud Build utilise par défaut n'a souvent aucun droit (vérifié :
`… does not have storage.objects.get access`). **Attendez 1 à 2 minutes** avant la première construction.

### 5.2 L'image de l'agent (Cloud Shell)

Dans Cloud Shell, dans le dossier du projet (`cd ~/09-agents-multi-projets-gemini-enterprise`) :

```bash
K=meteo                                                                  # ← la clé de l'agent
gcloud builds submit --region=$REGION --project=$PROJET_AGENTS \
  --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
  --config=01-bis-cloud-run-a2a/cloudbuild.yaml \
  --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-console/$K:v1 .
python3 scripts/carte_a2a.py $K https://$K-a2a-console-$NUM_AGENTS.$REGION.run.app
```

- `gcloud builds submit` envoie le code des agents (le **point** final = le dossier courant, filtré par `.gcloudignore`)
  à **Cloud Build**, qui construit l'image de **cet** agent (code commun + `meteo_agent/`) et la range dans
  `agents-console`. **Attendu** (environ 1 min 20 s) : `Creating temporary archive of 20 file(s) totalling 61.4 KiB…`,
  puis une ligne qui finit par `…/agents-console/meteo:v1  SUCCESS`. Le détail de chaque option :
  [12-1-1, 7.2 a)](12-1-1-deployer-agents-shell.md#72-déployer-un-agent).
- **À la souris, le suivi :** 🔎 « Cloud Build » → **Historique** (région `europe-west1`) → la construction → son journal.
- La dernière commande affiche la **carte A2A** de l'agent, une ligne de JSON qui commence par
  `{"protocolVersion": "0.3", "name": "meteo_agent", …`. **Copiez-la** en entier : elle sert en 5.4 et en 7.

**Dans la console :** 🔎 « Artifact Registry » → `agents-console` → l'image `meteo` → étiquette `v1`.

### 5.3 Le compte de service

🔎 « Comptes de service » → **+ Créer un compte de service** :

1. **Nom** : `meteo-a2a-console-sa` → **Créer et continuer**.
2. **Attribuer des rôles** (**+ Ajouter un autre rôle** entre chaque) :

   | Rôle (nom affiché) | Pourquoi |
   |---|---|
   | **Utilisateur Vertex AI** (*Vertex AI User*) | Appeler Gemini |
   | **Rédacteur de journaux** (*Logs Writer*) | Écrire ses journaux |
   | **Utilisateur Model Armor** (*Model Armor User*) | Utiliser les filtres |

3. **Continuer** → **OK**.

**Attendu :** `meteo-a2a-console-sa@aiml-gemini-ent-exp-0zga.iam.gserviceaccount.com` dans la liste ; 🔎 « IAM » : ce
compte avec ses 3 rôles.

### 5.4 Le service Cloud Run

🔎 « Cloud Run » → **Déployer un conteneur** → **Service** (ou **Créer un service**) :

| Champ | Valeur (agent `meteo`) |
|---|---|
| **Déployer une révision à partir d'une image** → URL de l'image | **Sélectionner** → Artifact Registry → `agents-console` → `meteo` → `v1` |
| Nom du service | `meteo-a2a-console` |
| Région | `europe-west1` |
| Authentification | **Exiger l'authentification** (le service est **privé**) |
| Facturation | **Basée sur les requêtes** |
| Scaling du service | Nombre minimal d'instances **0**, maximal **1** |
| Entrée (*Ingress*) | **Tout** (l'authentification fait le tri) |
| **Conteneur(s)** → Paramètres → Ressources | Mémoire **1 Gio**, processeur **1** |
| **Conteneur(s)** → **Variables et secrets** → **+ Ajouter une variable**, 6 fois | voir le tableau ci-dessous |
| **Sécurité** → Compte de service | `meteo-a2a-console-sa` |

| Nom de la variable | Valeur |
|---|---|
| `AGENT` | `meteo_agent` |
| `AGENT_CARD` | la carte copiée en 5.2 (toute la ligne JSON) |
| `GOOGLE_CLOUD_PROJECT` | `aiml-gemini-ent-exp-0zga` |
| `MODEL` | `gemini-3.5-flash` |
| `PROMPT_TEMPLATE` | `projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/console-prompt-shield` |
| `RESPONSE_TEMPLATE` | `projects/aiml-gemini-ent-exp-0zga/locations/eu/templates/console-response-shield` |

**Créer.** **Attendu** (1 à 2 minutes) : une coche verte, et parmi les **URL** du service :
`https://meteo-a2a-console-433175138344.europe-west1.run.app` (l'adresse écrite dans la carte).

**Ce que vous voyez ensuite sur la page du service :**
- **Métriques** : appels, temps de réponse ;
- **Révisions** : les versions ;
- **Journaux** : chaque appel et chaque erreur ;
- **Sécurité** : authentification requise ;
- **Modifier et déployer une nouvelle révision** : changer une variable ou l'image.

### 5.5 Tester (Cloud Shell, 3 à 5 minutes après)

```bash
URL=https://$K-a2a-console-$NUM_AGENTS.$REGION.run.app ./01-bis-cloud-run-a2a/test.sh $K
```

**Attendu :** `== meteo  carte : meteo_agent (A2A 0.3)`, deux questions et réponses, puis
`OK : les agents répondent en A2A v0.3, avec mémoire de conversation`. Exemple réel en
[12-1-1, 7.3](12-1-1-deployer-agents-shell.md#73-tester-lagent).

### 5.6 Plusieurs agents

Refaites **5.2 à 5.5** pour chaque agent, en changeant la clé partout : `K=taille`, compte `taille-a2a-console-sa`,
service `taille-a2a-console`, variable `AGENT` = `taille_agent`, et **sa** carte. Les parties 2, 3, 4 et 5.1 ne se
refont pas.

**Pour gagner du temps** avec beaucoup d'agents : construisez toutes les images d'un coup dans Cloud Shell (liste
`AGENTS` du fichier), puis faites 5.3 et 5.4 à la souris pour chacun :

```bash
for K in $(echo $AGENTS_LISTE); do
  gcloud builds submit --region=$REGION --project=$PROJET_AGENTS \
    --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --config=01-bis-cloud-run-a2a/cloudbuild.yaml \
    --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-console/$K:v1 .
  echo "== carte de $K :"; python3 scripts/carte_a2a.py $K https://$K-a2a-console-$NUM_AGENTS.$REGION.run.app
done
```

(`for K in …; do … done` refait le bloc pour chaque agent de la liste.) Au-delà de 3 ou 4 agents, la console devient
longue : [Terraform](12-1-2-deployer-agents-terraform.md) fait tout cela avec une ligne.

---

## 6. Agent Runtime : un agent, puis plusieurs

### 6.1 Le compte de service

Comme en 5.3, avec le nom **`meteo-console-sa`** et les mêmes 3 rôles.

### 6.2 Envoyer l'agent (Cloud Shell, une commande)

```bash
K=meteo
python3 scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent --nom $K-console \
  --compte-service $K-console-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
  --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE
```

**Attendu** (3 à 5 minutes) : `en cours… 0 s`, …, puis
`déployé : projects/100000000002/locations/europe-west1/reasoningEngines/…`.

### 6.3 Tester et explorer (console)

🔎 « Agent Runtime » → **Déploiements** → `meteo-console` :

| Onglet | Ce que vous y faites |
|---|---|
| **Playground** | Poser une question (« Je cours à Lille demain matin, quoi porter ? ») et voir la réponse, avec les outils appelés |
| **Sessions** | Les conversations |
| **Journaux** | Les appels et les erreurs |
| En haut de la page | Le **nom de ressource** `projects/…/reasoningEngines/…` : **copiez-le**, Gemini Enterprise le demandera |

**Attendu :** une réponse météo et un conseil de tenue (exemple réel en
[12-1-2, 6.1](12-1-2-deployer-agents-terraform.md#61-un-agent)).

### 6.4 Plusieurs agents

Refaites 6.1 à 6.3 avec un autre `K`. Ou, après avoir créé les comptes `<clé>-console-sa` à la souris, d'un coup dans
Cloud Shell :

```bash
for K in $(echo $AGENTS_LISTE); do
  python3 scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent --nom $K-console \
    --compte-service $K-console-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
    --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE
done
```

Un agent déjà déployé (même nom) n'est **pas** recréé : le script répond `existe déjà : projects/…`. Nouvelle version : le supprimer d'abord (partie 10), puis relancer.

---

## 7. Agent Registry : le catalogue

- **Agents Agent Runtime :** déjà inscrits. 🔎 « Agent Registry » → région `europe-west1` → `meteo-console` est là.
- **Agents Cloud Run :** à déclarer, un par un. 🔎 « Agent Registry » → région `europe-west1` → **Enregistrer** (ou
  **Créer**) :

| Champ | Valeur (agent `meteo`) |
|---|---|
| Type | **Agent** (service d'agent) |
| Nom (ID) | `meteo-a2a-console` |
| Nom à afficher | `Météo & équipement` (le `nom_affiche` du catalogue) |
| Description | la description de la carte |
| Spécification | **Carte d'agent A2A** → coller la carte de 5.2 |

**Enregistrer.** **Attendu :** une ligne par agent et par hébergement. Un clic sur un agent : sa carte, ses
compétences, son adresse. (Ne remplissez pas de champ « interfaces » : l'adresse est déjà dans la carte.)

---

## 8. Dialogflow (option)

Un agent **conversationnel construit à la souris**, différent de nos agents Python.

1. 🔎 « Conversational Agents » (Dialogflow CX) → choisir le projet → **Créer un agent** → **Créer de toutes pièces**.
2. **Nom** `Accueil magasin`, **Région** `europe-west1`, **Langue** `fr`, **Fuseau horaire** `Europe/Paris` → **Créer**.
3. **Tester l'agent** (panneau de droite) → « Bonjour ». **Attendu :** une salutation (« Salutations ! »).
4. **Paramètres de l'agent** → copier le nom `projects/…/locations/europe-west1/agents/…` : la **source de l'agent
   Dialogflow** (Gemini Enterprise la demandera).

Construire ensuite le parcours : **Flux** et **Pages**, ou un **Playbook** (génératif).

---

## 9. Vérification finale

| Où | Ce que vous devez voir |
|---|---|
| 🔎 « API et services » → activés | Les API de la partie 2 |
| 🔎 « Model Armor » → Templates | `console-prompt-shield`, `console-response-shield` (`eu`) |
| 🔎 « Comptes de service » | Pour chaque agent : `<clé>-a2a-console-sa` et/ou `<clé>-console-sa` |
| 🔎 « IAM » | Chaque compte : Utilisateur Vertex AI, Rédacteur de journaux, Utilisateur Model Armor |
| 🔎 « Artifact Registry » → `agents-console` | Une image par agent Cloud Run |
| 🔎 « Cloud Run » → Services | `<clé>-a2a-console`, coche verte, **Authentification requise** |
| 🔎 « Agent Runtime » → Déploiements | `<clé>-console` ; le Playground répond |
| 🔎 « Agent Registry » | Une ligne par agent et par hébergement |
| Cloud Shell : `test.sh` | `OK : les agents répondent…` |

---

## 10. Ajouter un agent plus tard, en retirer un, tout supprimer

> **Plus simple : le script de nettoyage.** Il fait l'inventaire de tout ce que les guides créent (Cloud Run, Agent
> Runtime, Agent Registry, Dialogflow, comptes de service et leurs rôles, images, filtres Model Armor) et ne supprime
> qu'après confirmation :
>
> ```bash
> python3 scripts/nettoyer.py                         # INVENTAIRE : liste, ne supprime rien
> python3 scripts/nettoyer.py --agent meteo           # seulement ce qui appartient à meteo
> python3 scripts/nettoyer.py --supprimer             # supprime (tapez l'ID du projet pour confirmer)
> ```
>
> Ce que Terraform a créé est **ignoré** (marqué `[terraform]`) : supprimez-le avec `terraform destroy`. Testé en vrai :
> 8 types supprimés, rôles des comptes compris.

**À la souris :**

- **Ajouter** un agent du catalogue : 5.2 à 5.5 (Cloud Run), 6.1 à 6.3 (Agent Runtime), 7. Rien d'autre ne bouge.
- **Créer** un nouvel agent : [12-3, partie 1](12-3-ajouter-des-agents-un-par-un.md#1-créer-lagent-commun-aux-3-méthodes), puis comme ci-dessus.
- **Nouvelle version** d'un agent Cloud Run : nouvelle image `:v2` (5.2), puis service → **Modifier et déployer une
  nouvelle révision** → image `v2` → **Déployer**. Même adresse.
- **Retirer un agent**, dans cet ordre :
  1. 🔎 « Agent Registry » → l'entrée → **Supprimer**.
  2. 🔎 « Cloud Run » → le service → **Supprimer**.
  3. 🔎 « Agent Runtime » → l'agent → **Supprimer** (avec ses sessions).
  4. 🔎 « IAM » → le compte → **Modifier** (crayon) → supprimer ses rôles.
  5. 🔎 « Comptes de service » → le compte → **Supprimer**.
  6. 🔎 « Artifact Registry » → `agents-console` → l'image → **Supprimer**.
- **Tout supprimer :** chaque agent comme ci-dessus. Puis, quand plus rien ne s'en sert :
  - les deux templates Model Armor ;
  - le dépôt `agents-console` et le compte `agents-build-sa` ;
  - l'agent Dialogflow ;
  - le dossier dans Cloud Shell.

---

## 11. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| Un menu ou un rôle introuvable | API pas activée | Partie 2 |
| L'image n'apparaît pas dans **Sélectionner** | Construction pas finie ou en échec, ou autre dépôt / région | 🔎 « Cloud Build » → **Historique** : `Réussie` ? Refaire 5.2 ; vérifier `agents-console`, `europe-west1` |
| `PERMISSION_DENIED` à `gcloud builds submit` | API Cloud Build ou compte `agents-build-sa` tout neufs | Attendre 1 à 2 minutes, relancer |
| `does not have storage.objects.get access` | Compte `agents-build-sa` absent, sans ses 3 rôles, ou option `--service-account` oubliée | 5.1 ; garder l'option |
| Le service ne démarre pas (croix rouge) | Variable manquante ou mal copiée (souvent `AGENT_CARD` tronquée) | Service → **Journaux** ; corriger la variable → nouvelle révision |
| `test.sh` : `ÉCHEC : réponse bloquée par Model Armor` | Rôles pas encore actifs, ou mauvais chemin de template | Attendre 2 à 5 minutes ; vérifier `PROMPT_TEMPLATE` |
| `test.sh` : `ÉCHEC : 403` | Votre compte n'a pas le droit d'appeler le service | Être propriétaire, ou **Sécurité** → ajouter votre adresse avec **Demandeur Cloud Run** |
| L'URL du service ne contient pas `433175138344` | Normal : Cloud Run affiche plusieurs URL | Vérifier que `https://meteo-a2a-console-433175138344.europe-west1.run.app` est **parmi** elles |
| `Error code 13` (Agent Runtime) | Erreur interne de Google | Relancer la commande 6.2 |
| Météo : « erreur 429 » | Le service météo public limite les appels | Réessayer plus tard |
| Cloud Shell : variables vides | Session rouverte | Recharger la configuration (4.4) |

**Et après :** l'app Gemini Enterprise existe ? [12-1, C6 et C7](12-1-agents-projet-exp-vers-app.md#c6-donner-à-lapp-le-droit-dappeler-les-agents).
