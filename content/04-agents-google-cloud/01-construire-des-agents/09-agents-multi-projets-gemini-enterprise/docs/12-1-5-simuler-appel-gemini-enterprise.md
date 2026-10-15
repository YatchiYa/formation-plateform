# 12-1-5. Simuler l'appel de Gemini Enterprise vers les agents (avant de toucher à l'app)

**Le but :** prouver, **avant** d'ajouter quoi que ce soit dans l'app de production, que l'app pourra appeler vos
agents :
- **refusé** quand le droit manque ;
- **accepté** quand il est en place ;
- de nouveau **refusé** après le retour arrière.

Avec un compte qui joue le rôle du compte de l'app.

**Pourquoi ça vaut un vrai test :** Gemini Enterprise appelle vos agents avec **son** compte de service
(`service-<NUM_APP>@gcp-sa-discoveryengine…`), qu'on ne peut pas emprunter. Le **simulateur** est un compte de service
`ge-simulateur`, créé dans le projet de l'app, qui reçoit **exactement les mêmes droits**, et qui appelle les agents
**exactement de la même façon** :

| | Gemini Enterprise | Le simulateur |
|---|---|---|
| Agent A2A (Cloud Run) | Jeton d'identité de son compte dans l'en-tête `X-Serverless-Authorization`, message A2A v0.3 `message/send` | Pareil |
| Agent Runtime | API Agent Runtime, avec le jeton de son compte | Pareil (`create_session` puis `stream_query`) |
| Agent avec OAuth | En plus : le jeton de **l'utilisateur** (`Authorization` pour A2A ; `authorizations` pour Agent Runtime) | Pareil, avec **votre** jeton gcloud ([partie 6](#6-agents-avec-oauth--avec-et-sans-le-jeton-de-lutilisateur)) |

Si le simulateur est accepté, Gemini Enterprise le sera ; s'il est refusé, le droit manque.

**Ça marche même si Gemini Enterprise n'est pas activé** dans le projet de l'app de test : le simulateur n'en a pas
besoin. Sur le projet de production (où l'app existe), c'est la même chose.

> **Testé en vrai** (11 octobre 2026) : toutes les commandes de ce guide, dans l'ordre, entre deux projets de test (un
> « projet de l'app » sans Gemini Enterprise, un « projet des agents »), avec les agents `taille` et `identite`
> déployés par `deployer_shell.sh`. Les résultats ci-dessous sont les vrais : refusé, accepté, OAuth avec et sans jeton,
> refusé après retrait, nettoyage. Les noms des projets de test sont remplacés par les vôtres.

---

## Sommaire

0. [Ce que la simulation prouve, et ce qu'elle ne prouve pas](#0-ce-que-la-simulation-prouve-et-ce-quelle-ne-prouve-pas)
1. [Préparer (une fois)](#1-préparer-une-fois)
2. [Avoir des agents déployés](#2-avoir-des-agents-déployés)
3. [Étape A : sans droit, l'appel doit être REFUSÉ](#3-étape-a--sans-droit-lappel-doit-être-refusé)
4. [Étape B : donner au simulateur les droits de l'app](#4-étape-b--donner-au-simulateur-les-droits-de-lapp)
5. [Étape C : avec les droits, l'appel doit être ACCEPTÉ](#5-étape-c--avec-les-droits-lappel-doit-être-accepté)
6. [Agents avec OAuth : avec et sans le jeton de l'utilisateur](#6-agents-avec-oauth--avec-et-sans-le-jeton-de-lutilisateur)
7. [Étape D : retirer les droits, vérifier le refus, nettoyer](#7-étape-d--retirer-les-droits-vérifier-le-refus-nettoyer)
8. [Les mêmes appels à la main (pour comprendre)](#8-les-mêmes-appels-à-la-main-pour-comprendre)
9. [Quand ça marche, quand ça ne marche pas](#9-quand-ça-marche-quand-ça-ne-marche-pas)

---

## 0. Ce que la simulation prouve, et ce qu'elle ne prouve pas

| Prouvé par la simulation | **Pas** prouvé (à vérifier dans l'app, [12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md)) |
|---|---|
| L'agent est joignable depuis un compte d'un autre projet | Que l'app accepte la carte ou le nom de ressource (prévisualisation, région) |
| Les droits `run.invoker` et `discoveryengine.serviceAgent` suffisent, et leur absence bloque | L'accès **Agent User** et la **licence** des utilisateurs |
| Le protocole A2A v0.3 et l'API Agent Runtime répondent comme pour Gemini Enterprise | L'écran de consentement OAuth (« Autoriser ») lui-même |
| Un agent OAuth reçoit et utilise le jeton de l'utilisateur ; sans jeton, il le dit | Les quotas et limites propres à l'app |
| Les filtres Model Armor de l'agent, ses outils, sa réponse | |

---

## 1. Préparer (une fois)

Configuration chargée, avec **les valeurs de l'app** remplies ([12-1-4, partie 2](12-1-4-connecter-agents-app-gemini-enterprise.md#2-remplir-la-configuration--chaque-valeur-où-la-trouver)) :

```bash
cd ~/Desktop/09-agents-multi-projets-gemini-enterprise && source .venv/bin/activate
source scripts/config.sh config/12-1-agents-dans-projet-exp.env
echo $GE_PROJECT          # le projet de l'app : acme-gemini-prod
./scripts/simuler_gemini_enterprise.sh preparer
```

**Résultat obtenu :**

```
Created service account [ge-simulateur].
Service account email: ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com
Updated IAM policy for serviceAccount [ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com].
simulateur prêt : ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com
Les jetons peuvent mettre 1 à 2 minutes à fonctionner après la création.
```

| Ce que fait `preparer` | Où |
|---|---|
| Crée le compte `ge-simulateur` (s'il n'existe pas) | **Projet de l'app** |
| Vous donne le rôle « Créateur de jetons » sur ce compte, pour parler **en son nom** pendant le test | Sur ce compte seulement |

Rien d'autre : ni l'app, ni les agents ne sont touchés. **Attendez 1 à 2 minutes.**

> **Production :** créer un compte dans le projet de l'app demande le droit de le faire. Si ce n'est pas permis, le
> simulateur peut vivre dans un autre projet de la même organisation : `export GE_PROJECT=<ce projet>` avant les
> commandes. Seuls les **droits** donnés au compte comptent pour le test, pas le projet où il vit.

---

## 2. Avoir des agents déployés

Ceux de `AGENTS` (fichier de configuration), déployés par [12-1-1](12-1-1-deployer-agents-shell.md), par exemple :

```bash
./scripts/deployer_shell.sh preparer           # si pas déjà fait
./scripts/deployer_shell.sh cloudrun taille
./scripts/deployer_shell.sh runtime taille
```

Le simulateur cherche `<clé>-a2a-shell` (Cloud Run) et `<clé>-shell` (Agent Runtime). Agents de la console :
ajoutez `--methode console` à chaque commande. (Pour Terraform, mêmes principes : commandes `a2a` / `runtime` de la
[partie 8](#8-les-mêmes-appels-à-la-main-pour-comprendre), avec leurs URL et noms.)

---

## 3. Étape A : sans droit, l'appel doit être REFUSÉ

```bash
./scripts/simuler_gemini_enterprise.sh tout taille
```

`tout` appelle chaque agent (ici `taille`), en Cloud Run **et** en Agent Runtime, avec la 1re question d'exemple du
catalogue, **comme Gemini Enterprise**. **Résultat obtenu :**

```
REFUSÉ (403) : le compte de Gemini Enterprise n'a pas roles/run.invoker sur ce service.

== taille, Agent Runtime taille-shell : « Je fais 98 cm de tour de poitrine, quelle taille de veste ? »
REFUSÉ (403) : le compte de Gemini Enterprise n'a pas roles/discoveryengine.serviceAgent sur le projet de l'agent.

== Bilan (compte simulateur ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com)
   REFUSÉ   taille  Cloud Run (A2A)
   REFUSÉ   taille  Agent Runtime
```

**C'est le résultat attendu :** vos agents sont **privés**. Si c'était `ACCEPTÉ` ici, le service serait ouvert à
d'autres comptes : à corriger avant d'aller plus loin.

---

## 4. Étape B : donner au simulateur les droits de l'app

```bash
./scripts/simuler_gemini_enterprise.sh droits taille
```

**Résultat obtenu :**

```
▶ gcloud projects add-iam-policy-binding aiml-gemini-ent-exp-0zga --role=roles/discoveryengine.serviceAgent --member=serviceAccount:ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com
  fait
▶ gcloud run services add-iam-policy-binding taille-a2a-shell --role=roles/run.invoker --member=serviceAccount:ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com
  fait
Attendez 2 à 3 minutes (les droits s'appliquent), puis : ./scripts/simuler_gemini_enterprise.sh tout
```

Ce sont **exactement** les droits que [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md) donne au compte de
l'app, mais pour le simulateur. **Rien** n'est donné au vrai compte de l'app à cette étape.

**Attendez 2 à 3 minutes** : un droit tout neuf met ce temps à s'appliquer.

---

## 5. Étape C : avec les droits, l'appel doit être ACCEPTÉ

```bash
./scripts/simuler_gemini_enterprise.sh tout taille
```

**Résultat obtenu :**

```
ACCEPTÉ (A2A v0.3) : Pour votre tour de poitrine de 98 cm, je vous conseille une veste en taille M, ou L pour plus d'aisance.
L'essai en magasin reste cependant le moyen le plus sûr pour trouver la coupe idéale.

== taille, Agent Runtime taille-shell : « Je fais 98 cm de tour de poitrine, quelle taille de veste ? »
ACCEPTÉ (Agent Runtime) : Pour un tour de poitrine de 98 cm, je vous conseille une taille M (ou L pour plus d'aisance).
L'idéal reste tout de même de l'essayer en magasin pour valider votre choix.

== Bilan (compte simulateur ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com)
   ACCEPTÉ  taille  Cloud Run (A2A)
   ACCEPTÉ  taille  Agent Runtime
```

**Ce que ça prouve :** un compte d'un **autre projet**, avec ces deux droits, appelle vos agents par les mêmes
chemins que Gemini Enterprise. Les mêmes droits donnés au compte de l'app ([12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md))
donneront le même résultat.

Encore `REFUSÉ` juste après l'étape B : attendez 2 minutes de plus et relancez (propagation des droits).

---

## 6. Agents avec OAuth : avec et sans le jeton de l'utilisateur

Pour un agent qui agit **avec le compte de l'utilisateur** ([12-1-7](12-1-7-agents-oauth-identite-outils.md)). Exemple :
l'agent fourni `identite`, qui dit si l'utilisateur est authentifié et avec quel compte.

**1. Déclarer l'autorisation de l'agent** dans le fichier de configuration, puis recharger :

```bash
AGENTS_OAUTH="identite=acces-identite"
```

**2. Le déployer avec elle** (les variables `AUTH_ID` et `GE_ENGINE` sont ajoutées à l'agent) :

```bash
./scripts/deployer_shell.sh cloudrun identite
./scripts/deployer_shell.sh runtime identite
./scripts/simuler_gemini_enterprise.sh droits identite
```

**Résultat obtenu :** pour chacun `autorisation OAuth : AUTH_ID=acces-identite`, puis le déploiement ; dans
`env-identite.yaml` : `AUTH_ID: "acces-identite"` et `GE_ENGINE: "projects/100000000003/locations/eu/…/engines/dev_gemini-entreprise-app"`.

**3. Comme un utilisateur qui a cliqué « Autoriser »** (2 à 3 minutes après) :

```bash
./scripts/simuler_gemini_enterprise.sh oauth identite
```

Le simulateur envoie, en plus, **votre** jeton gcloud, là où Gemini Enterprise envoie celui de l'utilisateur.
**Résultat obtenu :**

```
== identite, Cloud Run, AUTH_ID=acces-identite, jeton utilisateur : oui
ACCEPTÉ (A2A v0.3) : Oui, vous êtes authentifié auprès de Gemini Enterprise.
Compte : prenom.nom@… (domaine : …)
Portées : email, …, cloud-platform, …, userinfo.email, openid
Durée restante : 48 minutes.

== identite, Agent Runtime, AUTH_ID=acces-identite, jeton utilisateur : oui
ACCEPTÉ (Agent Runtime, OAuth) : Oui, vous êtes authentifié auprès de Gemini Enterprise.
Compte : prenom.nom@… (domaine : …).
…
```

**4. Comme un utilisateur qui n'a pas encore autorisé :**

```bash
./scripts/simuler_gemini_enterprise.sh oauth identite --sans-jeton
```

**Résultat obtenu :**

```
== identite, Cloud Run, AUTH_ID=acces-identite, jeton utilisateur : non
ACCEPTÉ (A2A v0.3) : Non, vous n'êtes pas authentifié.
Raison : Aucun jeton d'authentification n'a été reçu.
Que faire : Cliquez sur le bouton « Autoriser » s'il apparaît, …

== identite, Agent Runtime, AUTH_ID=acces-identite, jeton utilisateur : non
ACCEPTÉ (Agent Runtime, OAuth) : Non, vous n'êtes pas authentifié.
Raison : Aucun jeton reçu (vous n'avez pas cliqué sur « Autoriser » …).
```

`ACCEPTÉ` veut dire « l'appel est passé » ; la **réponse** dit si l'utilisateur est authentifié. Avec votre compte
Acme, le domaine affiché est `acme.example`.

---

## 7. Étape D : retirer les droits, vérifier le refus, nettoyer

```bash
./scripts/simuler_gemini_enterprise.sh retirer-droits taille identite
```

**Résultat obtenu :** les commandes `remove-iam-policy-binding`, chacune `fait`. **3 minutes après**,
`./scripts/simuler_gemini_enterprise.sh tout taille` :

```
== Bilan (compte simulateur ge-simulateur@acme-gemini-prod.iam.gserviceaccount.com)
   REFUSÉ   taille  Cloud Run (A2A)
   REFUSÉ   taille  Agent Runtime
```

Le retour arrière fonctionne. **Supprimer le simulateur** quand vous n'en avez plus besoin :

```bash
gcloud iam service-accounts delete ge-simulateur@$GE_PROJECT.iam.gserviceaccount.com --project=$GE_PROJECT
```

Les agents de test : `python scripts/nettoyer.py --agent taille --supprimer` (idem `identite`).

---

## 8. Les mêmes appels à la main (pour comprendre)

**Un agent A2A :**

```bash
URL=https://taille-a2a-shell-$NUM_AGENTS.$REGION.run.app
./scripts/simuler_gemini_enterprise.sh a2a $URL "Je fais 98 cm de tour de poitrine, quelle taille de veste ?"
```

Ce qu'il fait, en deux commandes :
1. `gcloud auth print-identity-token --impersonate-service-account=ge-simulateur@… --audiences=$URL --include-email` :
   un **jeton d'identité** du simulateur, pour cette adresse. Gemini Enterprise fait pareil avec son compte.
2. Un `POST` A2A sur `$URL/`, avec ce jeton dans l'en-tête **`X-Serverless-Authorization`**. Cloud Run vérifie
   `run.invoker` sur cet en-tête, ce qui laisse `Authorization` libre pour le jeton de l'utilisateur.

**Un agent Agent Runtime :**

```bash
NAME=$(curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
  | python3 -c "import json,sys; print(next(e['name'] for e in json.load(sys.stdin)['reasoningEngines'] if e['displayName']=='taille-shell'))")
./scripts/simuler_gemini_enterprise.sh runtime $NAME "Mon pied mesure 27 cm, quelle pointure pour courir ?"
```

Ce qu'il fait :
1. un **jeton d'accès** du simulateur (`gcloud auth print-access-token --impersonate-service-account=…`) ;
2. `POST …/reasoningEngines/ID:query` (`create_session`), puis `:streamQuery` (`stream_query`) : l'API Agent Runtime.

**Agents déployés par Terraform** (`taille-a2a`, `taille-agent`) : ces deux commandes avec leur URL
(`terraform -chdir=01-bis-cloud-run-a2a/terraform output -json urls`) et leur nom de ressource
(`terraform -chdir=02-bis-agent-runtime/terraform output agents`), et les droits donnés à la main
(`gcloud run services add-iam-policy-binding taille-a2a … --member=serviceAccount:ge-simulateur@…`).

---

## 9. Quand ça marche, quand ça ne marche pas

| Ce que vous voyez | Ce que ça veut dire | Que faire |
|---|---|---|
| `REFUSÉ (403) … run.invoker` à l'étape A | **Normal** : le service est privé | Continuer (étape B) |
| `ACCEPTÉ` à l'étape A | Le service accepte des comptes sans droit (ouvert, ou droit trop large déjà donné) | Vérifier : 🔎 « Cloud Run » → le service → **Sécurité** : authentification **requise** ; pas de `allUsers` |
| `REFUSÉ (403)` juste après l'étape B | Droits pas encore actifs | Attendre 2 à 3 minutes, relancer |
| `REFUSÉ (403)` 10 minutes après l'étape B | Droit donné au mauvais service / projet | `./scripts/connecter_app.sh verifier` ; [partie 8](#8-les-mêmes-appels-à-la-main-pour-comprendre) |
| Le script s'arrête **sans message** | Le jeton du simulateur n'a pas pu être créé : `preparer` pas fait, ou il y a moins de 2 minutes | `preparer`, attendre, relancer |
| `ERREUR 404` | Mauvaise adresse ou mauvais nom de ressource (agent supprimé ?) | `gcloud run services list …` ; [12-1-1, 8.2](12-1-1-deployer-agents-shell.md#82-tester-lagent) |
| `ACCEPTÉ … filtrée par Model Armor` | L'appel passe, mais le filtre de l'agent bloque (ou l'agent n'a pas encore ses droits Model Armor) | Attendre 2 à 5 minutes après un déploiement ; tester l'agent seul |
| Météo : « erreur 429 » | Le service météo public limite les appels | Réessayer plus tard |
| `Aucun agent déployé (méthode shell)` | Agents déployés autrement | `--methode console` ; Terraform : partie 8 |
| `pas d'autorisation dans AGENTS_OAUTH` (oauth) | Ligne `AGENTS_OAUTH` vide pour cet agent | [Partie 6](#6-agents-avec-oauth--avec-et-sans-le-jeton-de-lutilisateur) |
| OAuth : « agent déployé sans autorisation OAuth (AUTH_ID absent) » | Agent déployé avant d'ajouter `AGENTS_OAUTH` | Redéployer : Cloud Run `deployer_shell.sh cloudrun identite` ; Agent Runtime : le supprimer d'abord (`nettoyer.py --agent identite --types runtime --supprimer`), puis `runtime identite` |

**Suite :** tout est `ACCEPTÉ` → donner les vrais droits et ajouter les agents ([12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md)),
puis la console de l'app ([12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md)).
