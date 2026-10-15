# 12-3. Ajouter des agents un par un : un service par agent, une entrée par agent dans Gemini Enterprise

**Le but :** passer de 6 agents à 7, puis 10, puis 20, **sans jamais toucher aux agents déjà en place** :
- chaque agent a **son** service Cloud Run (ou **son** agent Agent Runtime), **sa** carte A2A et **son** identité ;
- chaque agent est ajouté **séparément** dans l'app `dev_gemini-entreprise-app`, avec **son** propre accès ;
- ajouter, modifier ou retirer un agent ne change rien aux autres.

**Le chemin, en 4 étapes :**

| # | Étape | Où |
|---|---|---|
| 1 | **Créer** l'agent : son dossier, ses outils, sa fiche dans le catalogue | [Partie 1](#1-créer-lagent-commun-aux-3-méthodes) (commun) |
| 2 | Le **tester sur votre poste** | [1.4](#14-le-tester-sur-votre-poste) |
| 3 | Le **déployer** et le tester en ligne | [Terraform](#2-méthode-b--terraform-recommandée), [shell](#3-méthode-a--shell-un-agent) ou [console](#4-méthode-c--console-un-agent) |
| 4 | L'**ajouter à l'app**, donner l'accès, tester dans le chat | Dans chaque méthode |

Deux questions qu'on pose ensuite, traitées ici :
- **Partie B :** vos agents peuvent-ils utiliser les **sources, connecteurs et MCP** déjà branchés sur Gemini Enterprise ?
- **Partie C :** un outil qui a besoin du **compte de l'utilisateur** (OAuth, comme un connecteur) : comment le faire
  marcher depuis Gemini Enterprise ?

**Avant de commencer** (une fois) :
- outils, dossier, Python, fichier de configuration, connexion, droits, API :
  [12-1-1, parties 2 à 5](12-1-1-deployer-agents-shell.md#2-préparer-votre-poste-une-fois) ;
- au moins un déploiement déjà fait, avec la méthode que vous allez réutiliser :
  - Terraform : [12-1-2](12-1-2-deployer-agents-terraform.md) ;
  - shell : [12-1-1](12-1-1-deployer-agents-shell.md) ;
  - console : [12-1-3](12-1-3-deployer-agents-console.md).

  Les éléments communs (filtres Model Armor, dépôt d'images, compte de construction des images) existent alors déjà.

Valable pour 12-1 (agents dans `aiml-gemini-ent-exp-0zga`) comme pour 12-2 (agents dans le projet de l'app) : seul le
fichier de configuration chargé change.

> **Testé en vrai** (9 et 10 octobre 2026, projets de test) :
> - **Cloud Run :** un 7e agent ajouté avec Terraform ; plan limité au nouvel agent ; modification et retrait d'un seul
>   agent ; test A2A.
> - **Agent Runtime :** ajout d'un agent (`7 to add`), modification d'un seul (mise à jour sur place).
> - **Test local :** un agent, avant tout déploiement.
> - **OAuth :** l'agent **Identité utilisateur** a reçu le vrai jeton Google de l'utilisateur et l'a fait vérifier par
>   Google, par les deux chemins. Côté A2A : serveur local, mêmes en-têtes que Gemini Enterprise. Côté Agent Runtime :
>   l'appel que fait Gemini Enterprise. Le format de la création d'autorisation est accepté par l'API Google.
>
> **Non testable sans votre app :** l'ajout dans l'app, le consentement OAuth dans le chat, la recherche dans les
> sources de l'app.

---

## Sommaire

0. [Le principe : le catalogue décide](#0-le-principe--le-catalogue-décide)
1. [Créer l'agent (commun aux 3 méthodes)](#1-créer-lagent-commun-aux-3-méthodes)
2. [Méthode B : Terraform (recommandée)](#2-méthode-b--terraform-recommandée)
3. [Méthode A : shell, un agent](#3-méthode-a--shell-un-agent)
4. [Méthode C : console, un agent](#4-méthode-c--console-un-agent)
5. [Ce que Terraform garantit (et ce qui demande de l'attention)](#5-ce-que-terraform-garantit-et-ce-qui-demande-de-lattention)
6. [Partie B : utiliser les sources et connecteurs de Gemini Enterprise](#6-partie-b--utiliser-les-sources-et-connecteurs-de-gemini-enterprise)
7. [Partie C : outils avec le compte de l'utilisateur (OAuth)](#7-partie-c--outils-avec-le-compte-de-lutilisateur-oauth)
8. [Ce qui peut arriver](#8-ce-qui-peut-arriver)

---

## 0. Le principe : le catalogue décide

```
 agents/trio/catalogue.json                 Projet des agents                       App Gemini Enterprise
 ┌──────────────────────────┐      ┌─────────────────────────────────────┐      ┌───────────────────────────┐
 │ meteo      -> meteo_agent │ ───▶ │ meteo-a2a       (Cloud Run, image   │ ───▶ │ « Météo & équipement »    │
 │ redaction  -> …           │      │   meteo:<empreinte>, compte         │      │ « Rédaction … »           │
 │ traduction -> …           │      │   meteo-a2a-sa)                     │      │ « Traduction … »          │
 │ taille     -> taille_agent│      │ taille-a2a      (son image, son     │      │ « Conseil taille »        │
 │ retour     -> retour_agent│      │   compte, sa carte A2A)             │      │ « Retours produits »      │
 │ identite   -> …           │      │ identite-a2a    (…)                 │      │ « Identité utilisateur »  │
 │ velo       -> velo_agent  │ NEW  │ velo-a2a        ← seul créé         │ NEW  │ « Atelier vélo » ← seule  │
 └──────────────────────────┘      └─────────────────────────────────────┘      └───────────────────────────┘
```

| Mot | En clair |
|---|---|
| **Catalogue** | Le fichier `agents/trio/catalogue.json` : la liste de tous les agents, chacun avec sa fiche (dossier, nom affiché, description, compétences, exemples) |
| **Clé** | Le nom court d'un agent dans le catalogue : `velo`. Elle donne **tous** ses noms dans Google Cloud |
| **Dossier de l'agent** | `agents/trio/velo_agent/` : son code (`agent.py`) |
| **Code commun** | `agents/trio/commun.py` : le modèle Gemini, le filtre Model Armor, le jeton OAuth. Partagé par tous |

**Les noms que donne la clé `velo` :**

| Méthode | Cloud Run | Son compte | Agent Runtime | Son compte | Dans l'app |
|---|---|---|---|---|---|
| Terraform | `velo-a2a` | `velo-a2a-sa` | `velo-agent` | `velo-agent-sa` | « Atelier vélo » / « Atelier vélo (A2A) » |
| Shell | `velo-a2a-shell` | `velo-a2a-shell-sa` | `velo-shell` | `velo-shell-sa` | « Atelier vélo (shell) » / « (A2A shell) » |
| Console | `velo-a2a-console` | `velo-a2a-console-sa` | `velo-console` | `velo-console-sa` | le nom que vous tapez |

**Pourquoi rien ne touche aux autres :** l'image (Cloud Run) et l'archive (Agent Runtime) d'un agent ne contiennent
que **son** dossier et le code commun, avec une étiquette qui est l'empreinte de ce contenu. Modifier `velo_agent` ne
change que `velo`. Modifier `commun.py` change tout le monde : c'est voulu, ils l'utilisent tous.

**Les 6 agents fournis :** météo, rédaction, traduction, **conseil taille** (`taille`), **retours produits**
(`retour`), **identité utilisateur** (`identite` : vérifie la chaîne OAuth, voir
[C7](#c7-lagent-identité-utilisateur--vérifier-loauth-de-bout-en-bout)). L'exemple ajoute un **7e agent, `velo`**.

---

## 1. Créer l'agent (commun aux 3 méthodes)

### 1.1 Ouvrir un terminal prêt

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise && source .venv/bin/activate
source scripts/config.sh config/12-1-agents-dans-projet-exp.env          # ou config/12-2-agents-dans-projet-app.env
```

**Attendu :** l'invite commence par `(.venv)`, et le résumé de la configuration finit par `OK`.

### 1.2 Le squelette

```bash
python scripts/nouvel_agent.py velo "Atelier vélo" "Diagnostique une panne de vélo simple et dit si l'atelier est nécessaire."
```

**Résultat obtenu :**

```
créé : agents/trio/velo_agent/agent.py et l'entrée « velo » du catalogue
à faire : écrire les outils dans velo_agent/agent.py, mettre de vrais exemples dans le catalogue, tester.
```

| Argument | Règle | Pourquoi |
|---|---|---|
| Clé (`velo`) | minuscules et chiffres, commence par une lettre, **2 à 15 caractères** | Elle forme les noms Google (un compte de service : 30 caractères max) |
| Nom affiché (`"Atelier vélo"`) | **unique** dans le catalogue | C'est par ce nom que l'app reconnaît l'agent : deux agents du même nom s'écraseraient |
| Description | une phrase claire | Gemini Enterprise la montre aux utilisateurs |

Le script **refuse** une clé ou un nom déjà pris, par exemple :
`Le nom « Atelier vélo » est déjà pris par un autre agent : choisir un nom affiché unique.`

**Ce qu'il a créé :**
- le dossier `agents/trio/velo_agent/`, avec `__init__.py` et `agent.py` (un outil d'exemple, `exemple_outil`) ;
- une entrée `"velo"` à la fin de `agents/trio/catalogue.json`.

### 1.3 Écrire les vrais outils

Ouvrez `agents/trio/velo_agent/agent.py` dans un éditeur. Remplacez `exemple_outil` par vos fonctions. Modèle à
copier : `agents/trio/taille_agent/agent.py` (deux outils, des tables, des contrôles d'entrée).

**Un outil, c'est une fonction Python, par exemple :**

```python
def diagnostic(symptome: str) -> dict:
    """Donne la cause probable d'une panne de vélo et dit si l'atelier est nécessaire.

    Args:
        symptome: Ce que le client constate, ex. « la chaîne saute », « le frein couine ».
    """
    pannes = {"chaîne": ("dérailleur mal réglé", False), "frein": ("plaquettes usées", True)}
    for mot, (cause, atelier) in pannes.items():
        if mot in symptome.lower():
            return {"status": "success", "cause": cause, "atelier_necessaire": atelier}
    return {"status": "error", "error_message": "Symptôme inconnu : demander plus de détails."}
```

| Règle | Pourquoi |
|---|---|
| Une **docstring** claire (le texte entre `"""`) | Le modèle la lit pour savoir **quand** appeler l'outil |
| Des **arguments typés** (`symptome: str`) décrits sous `Args:` | Le modèle sait quoi passer |
| Renvoie un `dict` avec `"status": "success"` ou `"status": "error"` + `"error_message"` | Le modèle sait si ça a marché |

Puis, dans le même fichier :
- `tools=[exemple_outil]` → `tools=[diagnostic]` ;
- l'`instruction` : dites quand appeler l'outil (« Appelle toujours diagnostic… ») ;
- les trois dernières lignes ne changent **pas** : `root_agent = Agent(…)`, `app = commun.app_securisee(root_agent)`,
  `agent_runtime_app = AdkApp(app=app)`.

**Dans `agents/trio/catalogue.json`**, entrée `"velo"` : remplacez `"Que sais-tu faire ?"` par **de vraies questions
d'exemple** (ex. `"Ma chaîne saute quand je pédale fort, je dois aller à l'atelier ?"`). Elles apparaissent dans la carte
de l'agent, et les scripts de test posent la première.

**Vérifier que le catalogue est valide** (une virgule oubliée suffit à le casser) :

```bash
python3 -m json.tool agents/trio/catalogue.json > /dev/null && echo "catalogue OK"
```

### 1.4 Le tester sur votre poste

```bash
cd agents/trio
PROMPT_TEMPLATE= RESPONSE_TEMPLATE= LOCAL_DEV=1 adk web
```

Sans `watchdog` (Mac Acme installé avec `requirements-poste.txt`, voir [12-1-1, partie 2](12-1-1-deployer-agents-shell.md#2-préparer-votre-poste-une-fois)),
`adk web` ne démarre pas : utilisez `PROMPT_TEMPLATE= RESPONSE_TEMPLATE= LOCAL_DEV=1 adk run velo_agent` (on discute
dans le terminal, `exit` pour quitter).

Ouvrez **http://localhost:8000** → en haut à gauche, choisir **`velo_agent`** → poser une question d'exemple. **Attendu :**
une réponse, et dans le panneau de gauche l'appel de votre outil (`diagnostic`). **Ctrl+C** dans le terminal pour
arrêter, puis `cd ../..`.

| Morceau | Pourquoi |
|---|---|
| `LOCAL_DEV=1` | Autorise l'agent à tourner **sans** filtre Model Armor, en local seulement (déployé, il refuse) |
| `PROMPT_TEMPLATE= RESPONSE_TEMPLATE=` | Vide les chemins de filtres chargés par la configuration. Sinon, si ces filtres n'existent pas encore, **toutes** les réponses sont « filtrée par Model Armor » (vérifié) |

**Tests automatiques des agents fournis** (sans appel au modèle) :

```bash
python scripts/test_trio.py
```

**Résultat obtenu :** `tests trio OK (9 scénarios, 6 agents)`. Ce script vérifie aussi que **chaque** entrée du catalogue
a son dossier et une clé de 15 caractères au plus : votre `velo` y passe.

Ensuite, **une** des trois méthodes.

---

## 2. Méthode B : Terraform (recommandée)

Rien à écrire dans Terraform : il lit le catalogue. Les mêmes commandes servent pour le 7e agent comme pour le 20e.

**La ligne `AGENTS` du fichier de configuration :**

| Votre fichier | À faire |
|---|---|
| `AGENTS=""` (tous les agents du catalogue) | Rien : `velo` est déjà dedans |
| `AGENTS="meteo taille"` (une liste) | **Ajouter** `velo` à la liste : `AGENTS="meteo taille velo"`, puis recharger (`source scripts/config.sh …`) |

⚠ Ne mettez **pas** `AGENTS="velo"` seul : la liste dit **ce qui doit exister**, Terraform supprimerait les autres. Le
mécanisme (`for_each`) est expliqué en
[12-1-2, partie 2](12-1-2-deployer-agents-terraform.md#2-for_each--comment-une-ligne-de-configuration-donne-n-agents).

### 2.1 Cloud Run (A2A), dossier 01-bis

Configuration chargée (pas de Docker : l'image est construite dans Google Cloud par Cloud Build) :

```bash
cd $DOSSIER/01-bis-cloud-run-a2a/terraform
terraform plan
```

**Résultat obtenu (le point à vérifier avant tout `apply`) :**

```
  # google_agent_registry_service.agent["velo"] will be created
  # google_cloud_run_v2_service.agent["velo"] will be created
  # google_cloud_run_v2_service_iam_member.ge_invokes["velo"] will be created
  # google_project_iam_member.agent["velo roles/aiplatform.user"] will be created
  # google_project_iam_member.agent["velo roles/logging.logWriter"] will be created
  # google_project_iam_member.armor["velo"] will be created
  # google_service_account.agent["velo"] will be created
  # terraform_data.image["velo"] will be created
Plan: 8 to add, 0 to change, 0 to destroy.
```

**Comment le lire :**
- **uniquement** des lignes `["velo"]`, et **`0 to change, 0 to destroy`** : les 6 autres agents ne sont pas touchés ;
- `ge_invokes["velo"]` : le droit de l'app d'appeler ce service. Il n'apparaît que si l'app est renseignée dans la
  configuration ; sans app : `7 to add` ;
- avec `PUBLIER=oui` : une ligne de plus, `terraform_data.publish["velo"]` (l'ajout dans l'app) : `9 to add`.

> Si le plan montre **autre chose** (des `destroy`, ou des `create` pour des agents qui existent déjà), répondez
> **`no`** : voir [5. Ce que Terraform garantit](#5-ce-que-terraform-garantit-et-ce-qui-demande-de-lattention).

```bash
terraform apply       # relit le plan, tapez yes ; 3 à 5 minutes (Cloud Build construit la seule image velo, ~1 min 20 s)
terraform output -json urls
```

**Résultat obtenu :** `Apply complete! Resources: 8 added, 0 changed, 0 destroyed.`, puis dans `urls` la ligne
`"velo": "https://velo-a2a-….a.run.app"` à côté des 6 autres, inchangées.

**Attendre 3 à 5 minutes** (les droits du nouveau compte s'appliquent), puis tester **ce seul agent** :

```bash
cd .. && URL=$(terraform -chdir=terraform output -json urls | python3 -c 'import json,sys; print(json.load(sys.stdin)["velo"])') ./test.sh velo
```

(La partie `URL=$(…)` lit l'adresse de `velo` dans les sorties de Terraform.) **Résultat obtenu** (agent tout juste
créé, outil d'exemple encore en place) :

```
== velo  carte : velo_agent (A2A 0.3)
   Q1 > Que sais-tu faire ?
   R1 < Bonjour ! En tant que spécialiste vélo, je peux vous aider à diagnostiquer des pannes simples sur votre
        bicyclette (freins, chaîne, pneus, etc.). Je vous indiquerai également s'il est nécessaire de vous rendre dans un atelier…
   Q2 > Peux-tu résumer ta réponse en une phrase ?
   R2 < Je peux diagnostiquer les pannes simples de votre vélo et vous dire si une visite en atelier de réparation est nécessaire.

OK : les agents répondent en A2A v0.3, avec mémoire de conversation
```

Testé trop tôt, le script le dit : `ÉCHEC : réponse bloquée par Model Armor. Juste après le premier apply, attendre 2 à
5 minutes…`. Attendez et relancez. `./test.sh` **sans** argument teste tous les agents.

### 2.2 Agent Runtime, dossier 02-bis

```bash
cd $DOSSIER/02-bis-agent-runtime/terraform
terraform plan
```

**Résultat obtenu** (même mécanisme, ici pour l'agent `taille`) :

```
  # module.agent["taille"].google_project_iam_member.agent["roles/aiplatform.user"] will be created
  # module.agent["taille"].google_project_iam_member.agent["roles/cloudtrace.agent"] will be created
  # module.agent["taille"].google_project_iam_member.agent["roles/logging.logWriter"] will be created
  # module.agent["taille"].google_project_iam_member.agent["roles/monitoring.metricWriter"] will be created
  # module.agent["taille"].google_project_iam_member.armor will be created
  # module.agent["taille"].google_service_account.agent will be created
  # module.agent["taille"].google_vertex_ai_reasoning_engine.agent will be created
Plan: 7 to add, 0 to change, 0 to destroy.
```

Pour `velo` : les mêmes 7 lignes avec `module.agent["velo"]` (+1 `terraform_data.publish["velo"]` si `PUBLIER=oui`).
Le droit de l'app sur Agent Runtime vaut pour **tout le projet** : rien de plus par agent.

```bash
terraform apply       # yes ; 5 à 10 minutes
cd .. && ./test.sh velo
```

**Résultat attendu :** `== velo  (projects/…/reasoningEngines/…)`, les outils appelés (`-> outil : …`), puis la réponse.

### 2.3 L'ajouter dans l'app, séparément

- **`PUBLIER=oui` déjà dans le fichier :** l'`apply` ci-dessus a déjà ajouté « Atelier vélo » (Agent Runtime) et
  « Atelier vélo (A2A) » (Cloud Run) dans l'app. Ligne `registered Atelier vélo` dans la sortie.
- **Sinon :**
  1. passez `PUBLIER=oui` et rechargez la configuration ;
  2. lancez `terraform plan` dans chaque dossier. Vous voyez `terraform_data.publish["velo"]`, plus celles des agents
     pas encore publiés ;
  3. lancez `terraform apply`.

**Donner l'accès, agent par agent :**
1. 🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` → **Agents** → « Atelier vélo ».
2. **Autorisations utilisateur** → **Ajouter** → le groupe → **Agent User** → **Enregistrer**.

Vous pouvez ouvrir un agent à un groupe pilote et un autre à tout le monde.

**Tester dans le chat :** l'app → **Intégration** → lien de l'app web, avec un compte du groupe → **Agents** →
« Atelier vélo » → une question d'exemple.

**Publier un seul agent sans publier les autres :** méthode A, étape [3.6](#36-lajouter-dans-lapp).

### 2.4 Modifier un agent, retirer un agent

| Vous faites | `terraform plan` montre (testé) |
|---|---|
| Modifier `velo_agent/agent.py` | Cloud Run : `terraform_data.image["velo"] must be replaced` + `google_cloud_run_v2_service.agent["velo"] will be updated in-place` → **Plan: 1 to add, 1 to change, 1 to destroy**. La ligne « destroy » est l'ancienne étiquette d'image, rien dans Google Cloud. Même URL, nouvelle révision. Agent Runtime : `module.agent["velo"]…reasoning_engine.agent will be updated in-place` → **0 to add, 1 to change, 0 to destroy**. Même ID. |
| Retirer `velo` | Voir ci-dessous → **Plan: 0 to add, 0 to change, 8 to destroy**, uniquement `["velo"]` (`because key ["velo"] is not in for_each map`). Avec `PUBLIER=oui` : il est aussi retiré de l'app. |
| Modifier `commun.py` ou `requirements.txt` | Tous les agents : nouvelle image (ou archive), mise à jour **sur place**. Même URL, même ID Agent Runtime. |

**Retirer `velo`** :
- si `AGENTS` est une liste, enlevez-en `velo` ;
- si `AGENTS=""`, retirez-le du catalogue :
  ```bash
  python3 -c 'import json; p="agents/trio/catalogue.json"; c=json.load(open(p)); c.pop("velo"); open(p,"w").write(json.dumps(c, ensure_ascii=False, indent=2) + "\n")'
  rm -r agents/trio/velo_agent
  ```

Puis rechargez la configuration, `terraform plan` (vérifier : seulement `["velo"]` en `destroy`), et `terraform apply`
dans chaque dossier.

---

## 3. Méthode A : shell, un agent

Les commandes de [12-1-1](12-1-1-deployer-agents-shell.md), pour **un seul** agent. Dans le terminal de 1.1
(configuration chargée) :

```bash
K=velo
NOM=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['nom_affiche'])")
echo "$K / $NOM"
```

**Attendu :** `velo / Atelier vélo`. `K` est la clé de l'agent : toutes les commandes suivantes l'utilisent.

### 3.1 Son image

Pas de Docker : l'image est construite **dans Google Cloud** par Cloud Build, depuis le dossier du projet (`cd $DOSSIER`).
Le compte de construction `agents-build-sa` existe déjà si vous avez déployé un agent Cloud Run en shell
([12-1-1, partie 7](12-1-1-deployer-agents-shell.md#7-cloud-run-a2a--un-agent-puis-plusieurs)) ; sinon, créez-le d'abord
comme indiqué là, puis attendez 1 à 2 minutes.

```bash
cd $DOSSIER
gcloud artifacts repositories describe agents-shell --location=$REGION >/dev/null 2>&1 || \
  gcloud artifacts repositories create agents-shell --repository-format=docker --location=$REGION
IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K:v1
gcloud builds submit --region=$REGION --service-account=projects/$PROJET_AGENTS/serviceAccounts/agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com \
  --config=01-bis-cloud-run-a2a/cloudbuild.yaml --substitutions=_AGENT_DIR=${K}_agent,_IMAGE=$IMAGE .
```

La 1re commande crée le dépôt d'images **seulement s'il n'existe pas** (`||` = « sinon »). **Résultat attendu**
(~1 min 20 s) : `Creating temporary archive of … file(s)…`, `Uploading tarball of [.] to [gs://…_cloudbuild/…]`,
`Created [https://cloudbuild.googleapis.com/…/builds/…]`, puis une ligne qui finit par
`europe-west1-docker.pkg.dev/…/agents-shell/velo:v1  SUCCESS`. `_AGENT_DIR=velo_agent` : l'image ne contient que cet
agent et le code commun. Le journal de la construction : 🔎 « Cloud Build » → **Historique** (région `europe-west1`).

### 3.2 Son compte de service

```bash
SA=$K-a2a-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
gcloud iam service-accounts create $K-a2a-shell-sa --display-name="Agent $K (Cloud Run A2A, méthode shell)"
for R in aiplatform.user logging.logWriter modelarmor.user; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R --member=serviceAccount:$SA >/dev/null \
    && echo "  $K-a2a-shell-sa : roles/$R"
done
```

**Résultat attendu :** `Created service account [velo-a2a-shell-sa].`, puis ses 3 rôles (appeler Gemini, écrire ses
journaux, utiliser Model Armor).

### 3.3 Son service Cloud Run

```bash
URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app
python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml
gcloud run deploy $K-a2a-shell --image=$IMAGE --region=$REGION --service-account=$SA --no-allow-unauthenticated \
  --env-vars-file=env-$K.yaml --memory=1Gi --cpu=1 --min-instances=0 --max-instances=1 --quiet
```

**Résultat attendu :** `Service URL: https://velo-a2a-shell-433175138344.europe-west1.run.app`, **identique** à `$URL`.
Le sens de chaque option : [12-1-1, 7.2 c)](12-1-1-deployer-agents-shell.md#72-déployer-un-agent).

### 3.4 Le tester (3 à 5 minutes après)

```bash
URL=$URL ./01-bis-cloud-run-a2a/test.sh $K
```

**Résultat attendu :** comme en [2.1](#21-cloud-run-a2a-dossier-01-bis), `OK : les agents répondent en A2A v0.3…`.

### 3.5 Le droit de l'app sur ce service (si l'app existe)

```bash
gcloud run services add-iam-policy-binding $K-a2a-shell --region=$REGION \
  --member=serviceAccount:$GE_SA --role=roles/run.invoker
```

**Résultat attendu :** la politique affichée, avec `service-100000000003@gcp-sa-discoveryengine…` sous `roles/run.invoker`.
(`$GE_SA` vide = pas d'app dans la configuration : sautez 3.5 et 3.6.)

### 3.6 L'ajouter dans l'app

```bash
python3 scripts/carte_a2a.py $K $URL > carte-$K.json
./scripts/add_agent_to_ge.sh a2a carte-$K.json "$NOM (A2A shell)"
./scripts/add_agent_to_ge.sh list
```

**Résultat attendu :**
1. `droit accordé : …` : le droit de 3.5, déjà en place, sans effet ;
2. `ajouté : projects/…/agents/<ID>` ;
3. la liste, avec « Atelier vélo (A2A shell) ».

Donner l'accès et tester : comme en [2.3](#23-lajouter-dans-lapp-séparément).

### 3.7 Agent Runtime à la place (ou en plus) de Cloud Run

```bash
SA_RT=$K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
gcloud iam service-accounts create $K-shell-sa --display-name="Agent $K (Agent Runtime, méthode shell)"
for R in aiplatform.user logging.logWriter modelarmor.user; do
  gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/$R --member=serviceAccount:$SA_RT >/dev/null \
    && echo "  $K-shell-sa : roles/$R"
done
DESC=$(python3 -c "import json; print(json.load(open('agents/trio/catalogue.json'))['$K']['description'])")
python scripts/deployer_agent_runtime.py --projet $PROJET_AGENTS --region $REGION --agent ${K}_agent --nom $K-shell \
  --description "$DESC" --compte-service $SA_RT \
  --env PROMPT_TEMPLATE=$PROMPT_TEMPLATE --env RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE
```

**Résultat attendu :** `déployé : projects/100000000002/locations/europe-west1/reasoningEngines/<ID>`. Puis, 3 à 5
minutes après :

```bash
AGENT_NAME=projects/$NUM_AGENTS/locations/$REGION/reasoningEngines/<ID> python scripts/query.py - "Ma chaîne saute, je dois aller à l'atelier ?"
./scripts/add_agent_to_ge.sh adk projects/$NUM_AGENTS/locations/$REGION/reasoningEngines/<ID> "$NOM (shell)" "$DESC"
```

(Remplacez `<ID>` par le nombre affiché après `déployé :`.) **Attendu :**
1. la réponse de l'agent, avec `-> outil : …` ;
2. `ajouté : …`. Dans le scénario 12-1, avant `ajouté`, le script donne aussi à l'app le droit sur le projet (si ce
   n'est pas déjà fait).

### 3.8 Retirer cet agent

```bash
./scripts/add_agent_to_ge.sh delete "$NOM (A2A shell)"         # de l'app (et "$NOM (shell)" pour Agent Runtime)
python scripts/nettoyer.py --agent $K                          # inventaire de ce qui appartient à velo
python scripts/nettoyer.py --agent $K --supprimer              # suppression, après confirmation (tapez l'ID du projet)
rm -f env-$K.yaml carte-$K.json
```

`nettoyer.py --agent velo` ne touche **qu'aux** éléments de `velo` :
- son service Cloud Run ;
- son agent Agent Runtime ;
- ses entrées du registre ;
- ses comptes de service et leurs rôles.

Les autres agents et les éléments communs ne sont pas concernés. Son image reste dans le dépôt `agents-shell` :
`gcloud artifacts docker images delete $REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K --delete-tags --quiet`.

---

## 4. Méthode C : console, un agent

Les écrans détaillés, champ par champ, sont dans [12-1-3](12-1-3-deployer-agents-console.md) ; ici, pour `velo` :

1. **L'image et la carte** (Cloud Shell, configuration chargée) :
   [12-1-3, 5.2](12-1-3-deployer-agents-console.md#52-limage-de-lagent-cloud-shell) avec `K=velo`. Copiez la carte affichée.
2. **Son compte de service :** [12-1-3, 5.3](12-1-3-deployer-agents-console.md#53-le-compte-de-service), nom
   `velo-a2a-console-sa`, 3 rôles : **Utilisateur Vertex AI**, **Rédacteur de journaux**, **Utilisateur Model Armor**.
3. **Son service :** [12-1-3, 5.4](12-1-3-deployer-agents-console.md#54-le-service-cloud-run) avec :

   | Champ | Valeur |
   |---|---|
   | Image | `agents-console/velo:v1` |
   | Nom | `velo-a2a-console` |
   | `AGENT` | `velo_agent` |
   | `AGENT_CARD` | la carte de l'étape 1 |
   | Compte de service | `velo-a2a-console-sa` |

   Les autres champs sont identiques. **Créer**, puis tester (Cloud Shell, 3 à 5 minutes après) :
   `URL=https://velo-a2a-console-$NUM_AGENTS.$REGION.run.app ./01-bis-cloud-run-a2a/test.sh velo`.
4. **Le droit de l'app :**
   1. Service `velo-a2a-console` → **Sécurité** → **Ajouter un compte principal**.
   2. `service-100000000003@gcp-sa-discoveryengine.iam.gserviceaccount.com` → rôle **Demandeur Cloud Run** →
      **Enregistrer**.
5. **Le registre :** [12-1-3, 7](12-1-3-deployer-agents-console.md#7-agent-registry--le-catalogue), nom `velo-a2a-console`.
6. **L'app :**
   1. Projet `acme-gemini-prod` → 🔎 « Gemini Enterprise » → `dev_gemini-entreprise-app` → **Agents** →
      **+ Ajouter un agent** → **Agent personnalisé via A2A**.
   2. Coller la carte → **Prévisualiser les détails de l'agent** → **Suivant**.
   3. *Authentification* : **Ignorer et terminer**, sauf si l'agent utilise le compte de l'utilisateur
      ([partie C](#7-partie-c--outils-avec-le-compte-de-lutilisateur-oauth)).
   4. **Autorisations utilisateur** → le groupe → **Agent User** → **Enregistrer**.
7. **Tester dans le chat :** l'app web → **Agents** → votre agent.

**Agent Runtime à la place :** [12-1-3, partie 6](12-1-3-deployer-agents-console.md#6-agent-runtime--un-agent-puis-plusieurs)
avec `K=velo`. Puis dans l'app : **Agent personnalisé via Agent Runtime** → nom, description, **chemin de ressource**
(copié dans la console Agent Runtime) → **Créer**.

Les agents existants ne sont jamais ouverts : rien ne peut les modifier.

---

## 5. Ce que Terraform garantit (et ce qui demande de l'attention)

| Situation | Ce qui se passe | Vérifié |
|---|---|---|
| Ajouter un agent | Seules ses ressources sont créées (`0 to change, 0 to destroy`) | Oui, plan et apply |
| Modifier le code d'**un** agent Cloud Run | Seuls son image et son service changent ; même URL | Oui, plan |
| Modifier le code d'un agent Agent Runtime | Seul cet agent est mis à jour, **sur place** : même ID, l'entrée dans l'app reste valable (`Plan: 0 to add, 1 to change, 0 to destroy`) | Oui, plan |
| Retirer un agent | Seules ses ressources sont supprimées | Oui, plan et apply |
| Deux agents avec le même nom affiché | `nouvel_agent.py` refuse ; Terraform refuse de publier (`Deux agents du catalogue ont le même nom_affiche`) | Oui, script |
| Relancer `apply` sans rien changer | `No changes. Your infrastructure matches the configuration.` | Oui |
| Lancer Terraform depuis un autre dossier ou un autre poste (avec le même état) | Rien n'est republié : le chemin du dossier n'entre pas dans ce que Terraform compare | Par construction (publication non testable sans l'app) |
| Oublier `source scripts/config.sh …` | Terraform demande `var.agents_project_id … Enter a value:` (Ctrl+C), ou mauvais espace de travail : le plan montre **tout** en `create`. **Ne pas appliquer.** Si on applique quand même, Google refuse les doublons (`already exists`) | Comportement Google |
| Une clé de `AGENTS` mal tapée | Refusé au chargement de la configuration : `ATTENTION : agent « … » absent de agents/trio/catalogue.json` | Oui |

**Ce qui demande de l'attention :**

- **Renommer une clé** (`velo` → `atelier`) = retirer un agent et en créer un autre : nouvelle URL, nouvelle entrée
  dans l'app (accès à redonner). Changez plutôt le **nom affiché**.
- **Changer le nom affiché, la description ou les exemples** d'un agent publié : son entrée dans l'app est
  **recréée**. Redonnez l'accès **Agent User** à cet agent (les autres ne bougent pas).
- **L'état Terraform est sur votre poste** (`terraform.tfstate.d/scenario-12-1/`, un par dossier). Toujours depuis le même
  dossier, et sauvegardez-le. Si plusieurs personnes déploient : mettre l'état dans un bucket Cloud Storage (bloc
  `backend "gcs"`), sinon chacun croit les agents de l'autre inexistants.
- **La règle d'or :** lire la ligne `Plan:` **avant** chaque `apply`. Ajout d'un agent : `N to add, 0 to change,
  0 to destroy`.

---

## 6. Partie B : utiliser les sources et connecteurs de Gemini Enterprise

**Question :** mes agents (Cloud Run, Agent Runtime, A2A) peuvent-ils utiliser les MCP, outils et connecteurs déjà
connectés à Gemini Enterprise ?

**Réponse courte :** **les données, oui** (avec les droits de l'utilisateur). **Les actions et les serveurs MCP,
non** pas « à travers » Gemini Enterprise : votre agent s'y connecte lui-même.

| Ce qui est branché sur l'app | Votre agent peut-il s'en servir ? | Comment |
|---|---|---|
| **Sources de données** (connecteurs Drive, SharePoint, Confluence, Jira, Cloud Storage, BigQuery, sites…) | **Oui** | L'outil `commun.recherche_gemini_enterprise` interroge la recherche de l'app **avec le jeton de l'utilisateur** : il ne voit que ce que l'utilisateur a le droit de voir. Demande la [partie C](#7-partie-c--outils-avec-le-compte-de-lutilisateur-oauth). |
| Les mêmes, avec l'identité de l'agent | Oui, déconseillé | Outil ADK `VertexAiSearchTool` ou `DiscoveryEngineSearchTool` : l'agent voit **tout** ce que son compte de service voit, sans tenir compte des droits de l'utilisateur. Acceptable seulement pour des sources publiques en interne. |
| **Actions** des connecteurs (envoyer un e-mail, créer un ticket Jira…) | **Non** (Google ne documente aucun moyen) | Votre agent appelle lui-même l'API (Gmail, Jira…) avec le jeton OAuth de l'utilisateur ([partie C](#7-partie-c--outils-avec-le-compte-de-lutilisateur-oauth)). |
| **Serveur MCP** ajouté à l'app | **Non** à travers l'app | Branchez le **même** serveur MCP sur votre agent : `McpToolset` d'ADK, avec son URL et son authentification. |
| **Airtable** (et les connecteurs du même type : Jira, Salesforce, ServiceNow…) | Données : **peut-être** (recherche fédérée). Actions : **non** à travers l'app | [6.2](#62-exemple--airtable) : votre agent se branche lui-même sur le serveur MCP officiel d'Airtable, avec le compte Airtable de l'utilisateur |
| Les autres agents de l'app | Non à travers l'app | Votre agent les appelle directement en A2A (voir [06](06-appels-entre-agents.md)). |

### 6.1 Brancher la recherche de l'app sur un agent

1. Dans `agents/trio/<clé>_agent/agent.py`, ajoutez l'outil commun :
   ```python
   tools=[mes_outils, commun.recherche_gemini_enterprise],
   ```
   Et dans l'instruction : « Pour une question sur nos documents internes, appelle recherche_gemini_enterprise. »
2. Faites la [partie C](#7-partie-c--outils-avec-le-compte-de-lutilisateur-oauth) avec la portée
   `https://www.googleapis.com/auth/cloud-platform`.
3. Les utilisateurs doivent avoir accès à l'app (licence) : c'est **leur** recherche, avec **leurs** droits.

L'outil appelle `https://eu-discoveryengine.googleapis.com/v1/projects/100000000003/locations/eu/collections/default_collection/engines/dev_gemini-entreprise-app/servingConfigs/default_search:search`.
Il renvoie au maximum 5 documents (titre, lien, extrait), que le modèle cite. Sans autorisation configurée, il répond
`Recherche indisponible : autorisation OAuth (AUTH_ID) ou app (GE_ENGINE) non configurée.` : l'agent fonctionne, sans
cette capacité.

> Les connecteurs **fédérés** (données lues en direct chez l'éditeur, sans copie dans l'app) peuvent ne pas répondre à
> cette recherche comme dans le chat de l'app. Testez avec une question dont vous connaissez le document.

**Alternative :** le **serveur MCP géré de Discovery Engine** (`https://discoveryengine.googleapis.com/mcp`, outil
`search`), à brancher avec `McpToolset` et le même jeton utilisateur dans l'en-tête. Même résultat, avec une dépendance
de plus ; l'appel direct ci-dessus suffit.

### 6.2 Exemple : Airtable

Le connecteur Airtable de Gemini Enterprise (recherche fédérée et actions : créer une table, un champ, un commentaire…)
sert **l'assistant de l'app et le Workflow Builder** de l'app. Vos agents A2A ou Agent Runtime ne l'appellent pas :
Google ne documente aucun moyen. Votre agent fait donc **comme le connecteur** : il parle lui-même à Airtable, **avec
le compte Airtable de l'utilisateur**, que Gemini Enterprise lui transmet.

| Étape | Quoi |
|---|---|
| 1. Application OAuth chez Airtable | airtable.com → **Builder hub** → **OAuth integrations** → **Register new OAuth integration**. URI de redirection : les deux de [C1](#c1-le-client-oauth-une-fois-par-fournisseur). Portées : le minimum (ex. `data.records:read`, `data.records:write`, `schema.bases:read`). Générez un **client secret**. |
| 2. Autorisation dans l'app | Comme [C2](#c2-lautorisation-dans-lapp), console ou API, avec : URI d'autorisation `https://airtable.com/oauth2/v1/authorize?…` (ID client, portées, `response_type=code`), URI du jeton `https://airtable.com/oauth2/v1/token`. `autorisation_oauth.sh` est fait pour Google : pour Airtable, utilisez la console. |
| 3. L'agent | Le serveur MCP officiel d'Airtable, avec le jeton de l'utilisateur (code ci-dessous) |
| 4. Déployer | `AGENTS_OAUTH="airtable=acces-airtable"` ([C4](#c4-déployer-avec-lautorisation-lajouter-dans-lapp)) |

```python
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

import commun


def entetes_airtable(ctx) -> dict:
    """À chaque appel : le jeton Airtable de CET utilisateur (transmis par Gemini Enterprise)."""
    jeton = commun.jeton_utilisateur(ctx)
    return {"Authorization": f"Bearer {jeton}"} if jeton else {}


airtable = McpToolset(connection_params=StreamableHTTPConnectionParams(url="https://mcp.airtable.com/mcp"),
                      header_provider=entetes_airtable)
# root_agent = Agent(…, tools=[airtable])
```

L'agent voit alors les bases **que l'utilisateur a autorisées**, avec **ses** droits Airtable.

> **À vérifier chez vous (non testé : pas de compte Airtable ici) :**
> - Airtable impose **PKCE** dans son OAuth. Google ne dit pas si les autorisations de Gemini Enterprise le gèrent. Si
>   le consentement échoue, vous avez deux solutions :
>   - un serveur MCP intermédiaire qui gère lui-même l'OAuth d'Airtable ;
>   - un **jeton d'accès personnel** Airtable dans Secret Manager, comme la clé d'API du modèle. Avec ce jeton, tous
>     les utilisateurs agissent avec **le même** compte Airtable : réservez-le à des bases partagées.
> - Commencez par l'agent **Identité utilisateur** ([C7](#c7-lagent-identité-utilisateur--vérifier-loauth-de-bout-en-bout))
>   branché sur l'autorisation Airtable. Il doit répondre « jeton reçu, mais Google ne le reconnaît pas (… d'un autre
>   fournisseur OAuth) » : c'est normal (un jeton Airtable), et cela prouve que le jeton arrive.

---

## 7. Partie C : outils avec le compte de l'utilisateur (OAuth)

**Question :** mon agent a un outil qui doit agir **au nom de l'utilisateur** (lire son Drive, chercher avec ses
droits, créer un ticket dans un outil externe). Comment le faire marcher dans Gemini Enterprise ?

**Le mécanisme (le même que pour les connecteurs de l'app) :**

```
 1. L'utilisateur parle à l'agent dans l'app
 2. Première fois : l'app affiche « Autoriser » → écran de consentement (Google, ou Jira, Salesforce…) → accepter
 3. À chaque message, l'app envoie le jeton OAuth DE L'UTILISATEUR à l'agent :
      Agent Runtime : dans l'état de session « temp:AUTH_ID »  (AdkApp s'en charge)
      A2A / Cloud Run : dans l'en-tête Authorization            (01-bis/main.py le range sous « temp:AUTH_ID »)
 4. L'outil lit le jeton :  commun.jeton_utilisateur(tool_context)  → appelle l'API avec
 5. « temp: » : le jeton n'est jamais enregistré dans la session, ni dans les journaux
```

`AUTH_ID` est l'**ID de l'autorisation** créée dans l'app (étape C2). Le même code marche aux deux endroits.

> **A2A sur Cloud Run :** l'app s'authentifie auprès de Cloud Run avec l'en-tête `X-Serverless-Authorization`, que
> Cloud Run consomme, et laisse `Authorization` (le jeton de l'utilisateur) au conteneur. `main.py` ne prend le jeton
> que si `X-Serverless-Authorization` est présent : sans lui, `Authorization` est le jeton d'appel Cloud Run, pas celui
> d'un utilisateur. Testé en local avec ces deux en-têtes : le jeton arrive dans l'outil ; sans
> `X-Serverless-Authorization`, l'outil reçoit `AUCUN`. URL `.run.app` par défaut requise (Google n'envoie pas cet
> en-tête aux domaines personnalisés).

### C1. Le client OAuth (une fois par fournisseur)

Pour une API **Google** (Drive, Gmail, Agenda, la recherche de l'app…), dans le projet de l'app
`acme-gemini-prod` :

1. 🔎 « Écran de consentement OAuth » (ou **Google Auth Platform**) → type **Interne** (seuls les comptes Acme) →
   nom de l'application, e-mail d'assistance → **Enregistrer**.
2. 🔎 « Identifiants » → **+ Créer des identifiants** → **ID client OAuth** → type **Application Web** → nom
   `gemini-enterprise-agents` → **URI de redirection autorisés**, les deux :
   ```
   https://vertexaisearch.cloud.google.com/oauth-redirect
   https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
   ```
   → **Créer** → **Télécharger le JSON** (`client_secret_….json`). Ne le mettez **jamais** dans le dépôt.
3. Activez l'API visée (ex. `gcloud services enable drive.googleapis.com --project=$PROJET_APP`).

Pour un **autre fournisseur** (Jira, Salesforce, ServiceNow…) : créez l'application OAuth chez lui, avec les deux URI de
redirection ci-dessus. Notez l'ID client, le secret, l'URL d'autorisation, l'URL de jeton.

**Portées (scopes)** : le minimum utile. Exemples : recherche dans l'app ou agent sur Agent Runtime →
`https://www.googleapis.com/auth/cloud-platform` (Google l'exige pour Agent Runtime) ; lire le Drive →
`https://www.googleapis.com/auth/drive.readonly`.

### C2. L'autorisation dans l'app

**Shell :**

```bash
cd $DOSSIER && source scripts/config.sh config/12-1-agents-dans-projet-exp.env
./scripts/autorisation_oauth.sh create acces-drive ~/Downloads/client_secret_XXXX.json "https://www.googleapis.com/auth/cloud-platform"
./scripts/autorisation_oauth.sh list
```

**Résultat attendu :** `autorisation créée : projects/100000000003/locations/eu/authorizations/acces-drive`, puis ce
nom dans la liste. Le script ajoute à l'URL d'autorisation ce que Google exige (`access_type=offline`,
`prompt=consent`, `response_type=code`) : sans `access_type=offline`, Google répond
`The authorization URI must contain 'access_type=offline' for Google authorization servers.` (vérifié).

Pas de Terraform pour cette étape : Google ne propose pas de ressource Terraform pour les autorisations. C'est aussi mieux
ainsi : le secret du client ne se retrouve pas dans l'état Terraform.

**Console :** l'autorisation se crée **au moment d'ajouter l'agent** (étape C4, méthode C).

### C3. Le code de l'outil

```python
def mon_outil(question: str, tool_context) -> dict:
    """…"""
    jeton = commun.jeton_utilisateur(tool_context)
    if not jeton:
        return {"status": "error", "error_message": "Autorisation manquante : cliquez sur « Autoriser » dans Gemini Enterprise."}
    # appeler l'API avec l'en-tête  Authorization: Bearer <jeton>
```

`tool_context` est fourni par ADK (ne pas le décrire dans la docstring : le modèle ne le voit pas). Exemple complet :
`commun.recherche_gemini_enterprise` dans `agents/trio/commun.py`.

### C4. Déployer avec l'autorisation, l'ajouter dans l'app

**Terraform** (01-bis et 02-bis) : dans le fichier de configuration,

```bash
AGENTS_OAUTH="velo=acces-drive"            # plusieurs : "velo=acces-drive retour=acces-jira"
```

puis `source scripts/config.sh …` et `terraform plan`. **Résultat attendu :** le service (ou l'agent Agent Runtime)
`["velo"]` `updated in-place` (variables `AUTH_ID` et `GE_ENGINE` ajoutées) et, si `PUBLIER=oui`,
`terraform_data.publish["velo"] must be replaced` (l'entrée dans l'app est refaite avec l'autorisation : redonnez
l'accès **Agent User**). Les autres agents : rien. `apply`.

Ce que Terraform envoie à l'app :
- **A2A :** `"authorizationConfig": {"agentAuthorization": "projects/100000000003/locations/eu/authorizations/acces-drive"}` ;
- **Agent Runtime :** `"authorizationConfig": {"toolAuthorizations": ["projects/…/authorizations/acces-drive"]}`.

C'est le format de la documentation Google.

**Shell :**

```bash
K=velo
AUTH_ID=acces-drive python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml     # + AUTH_ID et GE_ENGINE
gcloud run deploy $K-a2a-shell --image=$IMAGE --region=$REGION --env-vars-file=env-$K.yaml --quiet
./scripts/add_agent_to_ge.sh delete "Atelier vélo (A2A shell)"
AUTH_ID=acces-drive ./scripts/add_agent_to_ge.sh a2a carte-$K.json "Atelier vélo (A2A shell)"
```

Agent Runtime : `--env AUTH_ID=acces-drive --env GE_ENGINE=$TF_VAR_ge_engine` dans `deployer_agent_runtime.py`, puis
`AUTH_ID=acces-drive ./scripts/add_agent_to_ge.sh adk …`.

**Console :**
- **Cloud Run** → `velo-a2a-console` → **Modifier et déployer une nouvelle révision** → variables `AUTH_ID` =
  `acces-drive`, `GE_ENGINE` = `projects/100000000003/locations/eu/collections/default_collection/engines/dev_gemini-entreprise-app`
  → **Déployer**.
- **App** → **Agents** → **+ Ajouter un agent** :
  - **Via A2A :** coller la carte → **Prévisualiser** → **Suivant** → *Authentification* : **ID client**, **Code secret
    du client**, **URI d'autorisation**, **URI du jeton**, **Portées** (les valeurs du JSON de C1) → **Terminer**.
  - **Via Agent Runtime :** page **Autorisations** → **Ajouter une autorisation** → **Nom** (`acces-drive` : l'ID qui
    en découle est définitif ; c'est la valeur de `AUTH_ID`) → les mêmes champs → **OK** → **Suivant**.

  Vérifiez l'ID réellement créé (`./scripts/autorisation_oauth.sh list`) : il doit être **identique** à `AUTH_ID`.

### C5. Ce que voit l'utilisateur

1. Il ouvre « Atelier vélo » dans l'app et pose une question qui demande l'outil.
2. Première fois : un bouton **Autoriser** → la fenêtre de consentement (Google, avec les portées demandées) → **Autoriser**.
3. L'agent répond, avec **ses** données. Les fois suivantes, plus de consentement (jeton rafraîchi par l'app).

### C6. Sécurité

- Le jeton est celui de l'utilisateur : l'agent **ne peut rien faire que l'utilisateur ne puisse faire**.
- Il n'est jamais écrit dans la session (`temp:`), ni dans les journaux (ne le loggez pas dans vos outils).
- Écran de consentement **Interne** : seuls les comptes de l'organisation.
- Portées **minimales**. `cloud-platform` est large : réservez-le aux agents qui en ont besoin.
- Le secret du client OAuth : seulement dans l'app (C2), jamais dans le dépôt ni dans Terraform.

### C7. L'agent Identité utilisateur : vérifier l'OAuth de bout en bout

Avant de brancher de vrais outils, vérifiez la chaîne avec l'agent fourni `identite`. Son outil `qui_suis_je` lit le
jeton transmis par Gemini Enterprise, demande à Google à qui il appartient (`oauth2.googleapis.com/tokeninfo`) et répond :
authentifié ou non, le compte, le domaine (`acme.example`), les portées, la durée restante. Il n'affiche jamais le
jeton lui-même.

1. **Autorisation** (C1, C2) avec les portées `openid email https://www.googleapis.com/auth/cloud-platform`.
   `cloud-platform` est exigée par Google pour Agent Runtime ; pour Cloud Run seul, `openid email` suffit.
   ```bash
   ./scripts/autorisation_oauth.sh create acces-identite ~/Downloads/client_secret_XXXX.json "openid email https://www.googleapis.com/auth/cloud-platform"
   ```
2. **Configuration :** `AGENTS_OAUTH="identite=acces-identite"`, puis `source scripts/config.sh …`, `terraform plan`
   (seul `["identite"]` change) et `terraform apply`, dans 01-bis et/ou 02-bis, avec `PUBLIER=oui`.
3. **Dans l'app :** **Agent User** sur « Identité utilisateur », puis dans le chat : « Suis-je authentifié ? Avec quel
   compte ? » → **Autoriser** → consentement.

**Résultats obtenus** (projets de test, compte de test ; chez vous : `prenom.nom@acme.example`, domaine `acme.example`) :

- **Agent Runtime.** L'agent a été déployé, puis appelé comme Gemini Enterprise l'appelle
  (`streaming_agent_run_with_events`, jeton dans `authorizations`). Ce que l'outil a renvoyé :
  ```
  <- outil : {"status": "success", "authentifie": true, "verifie_par_google": true, "compte": "…@gmail.com",
              "domaine": "gmail.com", "portees": ["email", "…/auth/cloud-platform", "…/auth/userinfo.email", "openid", …],
              "expire_dans_secondes": 1391, "autorisation": "acces-identite"}
  agent : Oui, vous êtes authentifié avec le compte …@gmail.com (domaine : gmail.com).
          Vos portées de droits sont : email, cloud-platform, userinfo.email, openid…
          La durée restante de votre session est d'environ 23 minutes.
  ```
- **Même appel sans jeton** (l'utilisateur n'a pas encore cliqué sur « Autoriser ») :
  ```
  <- outil : {"status": "success", "authentifie": false, "raison": "aucun jeton reçu : l'utilisateur n'a pas encore
              cliqué sur « Autoriser », ou l'agent n'est pas appelé depuis Gemini Enterprise"}
  agent : Non, vous n'êtes pas authentifié. […] connectez-vous via Gemini Enterprise et autorisez l'application.
  ```
- **A2A (serveur Cloud Run en local, en-têtes de Gemini Enterprise)** : la même réponse « Oui, vous êtes authentifié… ».
  Avec un jeton invalide : « Le jeton reçu n'est pas reconnu par Google (il est expiré ou provient d'un autre
  fournisseur OAuth) ». Le jeton n'apparaît **jamais** dans les journaux du serveur (vérifié).

| L'agent répond | Ce que ça veut dire |
|---|---|
| « agent déployé sans autorisation OAuth (AUTH_ID absent) » | `AGENTS_OAUTH` ne contient pas `identite=…`, ou pas redéployé |
| « aucun jeton reçu » | Agent ajouté dans l'app **sans** l'autorisation, ou l'utilisateur n'a pas cliqué « Autoriser » |
| « jeton reçu, mais Google ne le reconnaît pas » | Jeton expiré, ou d'un autre fournisseur (normal pour Airtable, Jira…) |
| « authentifié, compte …@acme.example » | Chaîne complète : vos outils peuvent utiliser ce jeton |

---

## 8. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| `Clé invalide` / `existe déjà` / `nom … déjà pris` (`nouvel_agent.py`) | Règles de 1.1 | Autre clé, ou autre nom affiché |
| Le plan montre des `destroy` ou recrée des agents existants | Mauvaise configuration chargée, autre dossier, état perdu | **Ne pas appliquer.** `echo $TF_WORKSPACE` (doit être `scenario-12-1` ou `scenario-12-2`) ; recharger la configuration |
| `PERMISSION_DENIED` à la construction de l'image (`gcloud builds submit` ou `terraform apply`) | API Cloud Build ou compte de construction tout neufs : droits pas encore actifs | Attendre 1 à 2 minutes, relancer (Terraform réessaie déjà seul jusqu'à 4 fois) |
| `… does not have storage.objects.get access to the Google Cloud Storage object` | Compte de construction `agents-build-sa` absent, ou `--service-account` oublié | [12-1-1, partie 7](12-1-1-deployer-agents-shell.md#7-cloud-run-a2a--un-agent-puis-plusieurs) |
| Construction `FAILURE` | Erreur dans l'image (souvent le code ou `requirements.txt` de l'agent) | Lien du journal affiché par gcloud ; 🔎 « Cloud Build » → **Historique** (région `europe-west1`) ; corriger puis relancer : seules les images manquantes sont refaites |
| `is tainted, so must be replaced` au plan suivant | Une construction d'image a échoué | Normal : relancer `apply` |
| `ÉCHEC : réponse bloquée par Model Armor` juste après l'ajout | Droit du nouveau compte pas encore actif | Attendre 2 à 5 minutes |
| Agent absent du chat | Pas d'accès **Agent User** sur **cet** agent | [2.3](#23-lajouter-dans-lapp-séparément) |
| `Recherche indisponible : autorisation OAuth (AUTH_ID) …` | `AGENTS_OAUTH` vide pour cet agent, ou pas redéployé | C4 |
| `Recherche refusée (403)` | Portée insuffisante, API non activée, ou l'utilisateur n'a pas accès à l'app | C1 (portée, API), licence de l'utilisateur |
| `ÉCHEC : TenantProject with location eu … does not exist` (`autorisation_oauth.sh`) | Pas d'app Gemini Enterprise dans ce projet / cette localisation | Vérifier `PROJET_APP`, `NUM_APP`, `GE_LOCATION` |
| Pas de bouton « Autoriser » dans le chat | Agent ajouté sans autorisation | C4 : supprimer et rajouter l'agent avec l'autorisation |

**Sources Google :** [Agents ADK (Agent Runtime) dans Gemini Enterprise, autorisations](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent),
[Agents A2A dans Gemini Enterprise, OAuth et Cloud Run](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent).
