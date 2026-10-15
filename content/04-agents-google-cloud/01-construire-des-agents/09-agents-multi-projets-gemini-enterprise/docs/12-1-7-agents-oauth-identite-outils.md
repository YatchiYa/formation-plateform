# 12-1-7. Agents avec OAuth, identité de l'utilisateur, outils de Gemini Enterprise (et ce qui arrive)

**Les questions de ce guide :**
1. Un agent du **projet des agents** a des outils qui doivent agir **avec le compte de l'utilisateur** (OAuth : lire
   son Drive, envoyer un e-mail en son nom…). Comment l'exposer dans l'app du **projet de l'app**, avec le bouton
   « Autoriser », la fenêtre de consentement, le jeton ?
2. Et si l'agent a besoin de **savoir qui est l'utilisateur** (identité) ?
3. Mon agent peut-il utiliser les **outils déjà dans Gemini Enterprise** (l'e-mail, Outlook, Slack, Jira…) ?
4. Les nouveautés annoncées (« Gemini agent », Spark) répondront-elles à tout ça ?

> **Testé en vrai** (10 et 11 octobre 2026) :
> - le jeton de l'utilisateur arrive bien dans l'outil de l'agent `identite`, qui le fait vérifier par Google, par
>   les deux chemins : A2A sur Cloud Run, et Agent Runtime avec l'appel `streaming_agent_run_with_events` que fait
>   Gemini Enterprise ;
> - sans jeton, l'agent dit « non authentifié » ;
> - tout cela entre deux projets, avec le simulateur ([12-1-5, partie 6](12-1-5-simuler-appel-gemini-enterprise.md#6-agents-avec-oauth--avec-et-sans-le-jeton-de-lutilisateur)) ;
> - la création d'une autorisation : format accepté par l'API Google.
>
> **Non testable sans votre app :** l'écran « Autoriser » et la fenêtre de consentement dans le chat.

> **Exemple complet** (Gmail, Agenda, Drive, Sheets sans suppression ; Google + Atlassian) :
> [12-1-8](12-1-8-agent-espace-de-travail-multi-oauth.md).

---

## Sommaire

0. [Les trois identités d'un appel](#0-les-trois-identités-dun-appel)
1. [OAuth : comment ça se passe pour l'utilisateur](#1-oauth--comment-ça-se-passe-pour-lutilisateur)
2. [OAuth pas à pas : un agent du projet des agents, exposé dans l'app](#2-oauth-pas-à-pas--un-agent-du-projet-des-agents-exposé-dans-lapp)
3. [L'identité de l'utilisateur (identity access)](#3-lidentité-de-lutilisateur-identity-access)
4. [Utiliser les outils de Gemini Enterprise (e-mail, Outlook, Slack) ?](#4-utiliser-les-outils-de-gemini-enterprise-e-mail-outlook-slack-)
5. [Les nouveautés : Gemini agent, Spark… répondront-elles à tout ?](#5-les-nouveautés--gemini-agent-spark-répondront-elles-à-tout-)
6. [Ce qui peut arriver](#6-ce-qui-peut-arriver)

---

## 0. Les trois identités d'un appel

Quand un utilisateur parle à votre agent dans l'app, **trois** identités entrent en jeu :

| Identité | Qui | Sert à | Où elle est réglée |
|---|---|---|---|
| **1. Le compte de l'app** | `service-100000000003@gcp-sa-discoveryengine…` | **Appeler** l'agent (le « droit d'entrer ») | Droits dans le projet des agents ([12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md)) |
| **2. Le compte de l'agent** | `meteo-a2a-shell-sa@aiml-gemini-ent-exp-0zga…` | Ce que l'agent fait **pour lui-même** : appeler Gemini, Model Armor, ses propres ressources | Ses rôles dans le projet des agents (12-1-1) |
| **3. Le compte de l'utilisateur** (OAuth, optionnel) | `prenom.nom@acme.example` | Ce que l'agent fait **au nom de l'utilisateur** : son Drive, ses e-mails, ses données dans un outil | Une **autorisation** dans l'app + le consentement de l'utilisateur (partie 2) |

Sans OAuth, l'agent ne connaît **pas** l'utilisateur et ne peut rien faire en son nom. Il n'agit qu'avec son propre
compte (identité 2).

---

## 1. OAuth : comment ça se passe pour l'utilisateur

```
 1. L'utilisateur, dans l'app, pose une question à l'agent « Mes documents »
 2. 1re fois : l'app affiche un bouton « Autoriser »
 3. Clic → fenêtre Google (ou Jira, Salesforce…) : « L'application … veut : voir vos fichiers Drive » → Autoriser
 4. L'app garde un jeton de rafraîchissement POUR CET UTILISATEUR (lui seul, révocable)
 5. À chaque message, l'app envoie à l'agent un jeton d'accès de CET utilisateur :
      A2A (Cloud Run) : en-tête Authorization: Bearer <jeton>      (le droit d'entrer, lui, est dans X-Serverless-Authorization)
      Agent Runtime   : dans « authorizations » → l'état de session « temp:<ID de l'autorisation> »
 6. L'outil de l'agent lit le jeton (commun.jeton_utilisateur) et appelle l'API avec : l'API voit L'UTILISATEUR
 7. Les fois suivantes : plus de fenêtre ; le jeton est renouvelé par l'app
```

**Entre deux projets, rien de spécial :** l'autorisation vit dans l'app (projet de l'app), le jeton voyage **dans
l'appel**, et l'agent (projet des agents) le reçoit. Prouvé avec le simulateur
([12-1-5, partie 6](12-1-5-simuler-appel-gemini-enterprise.md#6-agents-avec-oauth--avec-et-sans-le-jeton-de-lutilisateur)).

---

## 2. OAuth pas à pas : un agent du projet des agents, exposé dans l'app

Exemple réel du projet : l'agent **`identite`**. Il a un outil `qui_suis_je` qui utilise le jeton de l'utilisateur
pour dire qui il est. Le même chemin sert à tout outil OAuth (Drive, Gmail, Airtable…).

### 2.1 Le client OAuth (une fois par fournisseur), dans le projet de l'app

Le **client OAuth** est la « carte d'identité » de votre application auprès de Google : c'est son nom que
l'utilisateur voit dans la fenêtre de consentement.

1. Projet **`acme-gemini-prod`** → 🔎 « Google Auth Platform » (ou « Écran de consentement OAuth ») :
   - type **Interne** : seuls les comptes Acme ;
   - nom de l'application (ex. « Agents Acme ») ;
   - e-mail d'assistance ;
   - **Enregistrer**.
2. 🔎 « Identifiants » → **+ Créer des identifiants** → **ID client OAuth** → type **Application Web** → nom
   `gemini-enterprise-agents` → **URI de redirection autorisés**, ces deux-là exactement :
   ```
   https://vertexaisearch.cloud.google.com/oauth-redirect
   https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
   ```
   → **Créer** → **Télécharger le JSON** (`client_secret_….json`). **Jamais** dans le dépôt, ni par e-mail.
3. Les **portées** (ce que l'agent pourra faire) : le minimum.

   | Pour… | Portée |
   |---|---|
   | savoir qui est l'utilisateur (agent `identite`) | `openid email` |
   | un agent sur **Agent Runtime** (exigé par Google) | `https://www.googleapis.com/auth/cloud-platform` |
   | lire le Drive | `https://www.googleapis.com/auth/drive.readonly` |
   | envoyer un e-mail en son nom | `https://www.googleapis.com/auth/gmail.send` |

4. Activer l'API visée dans le projet de l'app (ex. `gcloud services enable gmail.googleapis.com --project=$PROJET_APP`).

**Fournisseur non Google** (Jira, Salesforce, Airtable…) : créer l'application OAuth chez lui, avec les deux mêmes URI.
Noter l'ID client, le secret, l'URL d'autorisation, l'URL du jeton ([12-3, 6.2](12-3-ajouter-des-agents-un-par-un.md#62-exemple--airtable)).

### 2.2 L'autorisation dans l'app (projet de l'app)

Une **autorisation** = le client OAuth + les portées, enregistrés dans l'app sous un **ID** (ex. `acces-identite`).
Cet ID est le lien entre l'app et l'agent.

**Script** (configuration chargée) :

```bash
./scripts/autorisation_oauth.sh create acces-identite ~/Downloads/client_secret_XXXX.json \
  "openid email https://www.googleapis.com/auth/cloud-platform"
./scripts/autorisation_oauth.sh list
```

**Attendu :** `autorisation créée : projects/100000000003/locations/eu/authorizations/acces-identite`, puis ce nom
dans la liste. Le script construit l'URL d'autorisation avec ce que Google exige (`access_type=offline`,
`prompt=consent`, `response_type=code`). Sans `access_type=offline`, Google répond
`The authorization URI must contain 'access_type=offline' for Google authorization servers.` (vérifié).

**Console :** l'autorisation se crée **en ajoutant l'agent** dans l'app : écran *Authorizations* (Agent Runtime) ou
étape *Authentification* (A2A). Mêmes champs : ID client, secret, URI d'autorisation, URI du jeton, portées
([12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md)).

### 2.3 Le code de l'outil (dans l'agent)

```python
def mon_outil(question: str, tool_context) -> dict:
    """Ce que fait l'outil (le modèle lit ce texte)."""
    jeton = commun.jeton_utilisateur(tool_context)          # le jeton de L'UTILISATEUR, ou None
    if not jeton:
        return {"status": "error", "error_message": "Autorisation manquante : cliquez sur « Autoriser » dans Gemini Enterprise."}
    # appeler l'API avec l'en-tête  Authorization: Bearer <jeton>
```

`commun.jeton_utilisateur` lit le jeton là où Gemini Enterprise le met :
- **Agent Runtime :** l'état `temp:<AUTH_ID>`, rempli par la plateforme ;
- **A2A :** l'en-tête `Authorization`, recopié dans ce même état par `01-bis-cloud-run-a2a/main.py`.

Il marche donc sur les deux hébergements. Le jeton n'est **jamais** enregistré (`temp:`). Exemples complets :
`agents/trio/identite_agent/agent.py`, `commun.recherche_gemini_enterprise`.

**Exemple : envoyer un e-mail au nom de l'utilisateur** (portée `gmail.send` ; **non testé** ici) :

```python
import base64, email.message, json, urllib.request

def envoyer_email(destinataire: str, sujet: str, texte: str, tool_context) -> dict:
    """Envoie un e-mail AU NOM de l'utilisateur connecté (depuis sa boîte Gmail). Toujours demander confirmation avant."""
    jeton = commun.jeton_utilisateur(tool_context)
    if not jeton:
        return {"status": "error", "error_message": "Autorisation manquante : cliquez sur « Autoriser »."}
    m = email.message.EmailMessage(); m["To"], m["Subject"] = destinataire, sujet; m.set_content(texte)
    corps = json.dumps({"raw": base64.urlsafe_b64encode(m.as_bytes()).decode()}).encode()
    req = urllib.request.Request("https://gmail.googleapis.com/gmail/v1/users/me/messages/send", corps,
                                 {"Authorization": f"Bearer {jeton}", "Content-Type": "application/json"})
    return {"status": "success", "id": json.load(urllib.request.urlopen(req))["id"]}
```

Dans l'instruction de l'agent : « Avant d'envoyer, montre le message et demande confirmation. » Un e-mail envoyé ne se
rattrape pas.

### 2.4 Déployer l'agent avec son autorisation (projet des agents)

Dans le fichier de configuration, puis recharger :

```bash
AGENTS_OAUTH="identite=acces-identite"          # plusieurs : "identite=acces-identite docs=acces-drive"
```

**Shell** ([12-1-1](12-1-1-deployer-agents-shell.md)) :

```bash
./scripts/deployer_shell.sh cloudrun identite
./scripts/deployer_shell.sh runtime identite        # déjà déployé sans OAuth ? le supprimer d'abord (nettoyer.py)
```

**Résultat obtenu :** `autorisation OAuth : AUTH_ID=acces-identite` pour chacun. L'agent reçoit les variables
`AUTH_ID` (l'ID de l'autorisation) et `GE_ENGINE` (le chemin de l'app).

**Terraform** ([12-1-2](12-1-2-deployer-agents-terraform.md)) : `terraform plan` → l'agent `["identite"]`
`updated in-place` (les 2 variables). Les autres agents ne bougent pas.

### 2.5 Simuler (avant l'app)

```bash
./scripts/simuler_gemini_enterprise.sh droits identite
./scripts/simuler_gemini_enterprise.sh oauth identite                 # comme après « Autoriser »
./scripts/simuler_gemini_enterprise.sh oauth identite --sans-jeton    # comme avant « Autoriser »
```

**Résultat obtenu :** avec jeton : « Oui, vous êtes authentifié… Compte : … Portées : … » (Cloud Run **et** Agent
Runtime). Sans jeton : « Non, vous n'êtes pas authentifié… Cliquez sur le bouton « Autoriser » ». Détails :
[12-1-5, partie 6](12-1-5-simuler-appel-gemini-enterprise.md#6-agents-avec-oauth--avec-et-sans-le-jeton-de-lutilisateur).

### 2.6 Ajouter l'agent dans l'app **avec** l'autorisation (projet de l'app)

L'autorisation se rattache à l'agent **au moment de l'ajout** :

| Méthode | Commande / clics |
|---|---|
| Script | `AUTH_ID=acces-identite ./scripts/add_agent_to_ge.sh a2a carte-identite.json "Identité utilisateur (A2A)"` ; Agent Runtime : `AUTH_ID=acces-identite ./scripts/add_agent_to_ge.sh adk <ressource> "Identité utilisateur"` |
| Terraform | `AGENTS_OAUTH` rempli + `PUBLIER=oui` : la publication inclut l'autorisation |
| Console | A2A : étape *Authentification* → les champs du client OAuth ; Agent Runtime : écran *Authorizations* → **Ajouter une autorisation** ([12-1-6](12-1-6-ajouter-agent-console-gemini-enterprise.md)) |

Ce qui est envoyé à l'app (documentation Google) :
- **A2A :** `"authorizationConfig": {"agentAuthorization": "projects/100000000003/locations/eu/authorizations/acces-identite"}` ;
- **Agent Runtime :** `"authorizationConfig": {"toolAuthorizations": ["projects/…/authorizations/acces-identite"]}`.

Un agent **déjà ajouté sans** autorisation : le retirer (`add_agent_to_ge.sh delete "Nom"`), puis le rajouter avec.

### 2.7 Dans le chat

1. Accès **Agent User** pour le groupe ([12-1-6, partie 5](12-1-6-ajouter-agent-console-gemini-enterprise.md)).
2. Un utilisateur ouvre « Identité utilisateur », demande « Suis-je authentifié ? Avec quel compte ? ».
3. 1re fois : bouton **Autoriser** → fenêtre Google avec les portées → **Autoriser**.
4. **Attendu :** « Oui, vous êtes authentifié… Compte : prenom.nom@acme.example (domaine : acme.example)… ».

L'utilisateur peut retirer son accord : [myaccount.google.com/permissions](https://myaccount.google.com/permissions).

### 2.8 Sécurité

- L'agent ne peut **rien** faire que l'utilisateur ne puisse faire : c'est **son** jeton.
- Portées **minimales** ; écran de consentement **Interne**.
- Le secret du client OAuth : dans l'app seulement (2.2), jamais dans le dépôt, ni dans Terraform.
- Le jeton n'est jamais enregistré, ni écrit dans les journaux (ne le loggez pas).
- Actions irréversibles (e-mail, suppression) : toujours une confirmation de l'utilisateur dans l'instruction.

---

## 3. L'identité de l'utilisateur (identity access)

Deux besoins différents :

| Besoin | Solution | Statut |
|---|---|---|
| **Savoir qui parle** (e-mail, domaine) pour adapter la réponse ou vérifier un droit métier | Une autorisation OAuth avec la portée `openid email` (partie 2) ; l'outil lit le jeton et demande à Google à qui il appartient. C'est exactement l'agent **`identite`** (`qui_suis_je`), qui renvoie compte, domaine, portées, durée restante | Testé (Cloud Run et Agent Runtime) |
| **Agir avec les droits de l'utilisateur** sur des données Google (Drive, recherche de l'app…) | Même autorisation, avec les portées de l'API ; l'API applique **ses** droits (il ne voit que ce qu'il peut voir) | Mécanisme testé ; appel réel : selon l'API |
| **Connaître l'identité de l'agent** (son compte, pour l'audit) | Rien à faire : l'administrateur la voit dans l'app (page de détail de l'agent, *agent identity*, disponible depuis juin 2026). C'est le compte de service de l'identité 2 | Documentation Google |

**Pourquoi pas sans OAuth ?** Sans autorisation, Gemini Enterprise n'envoie à l'agent **aucune** information fiable
sur l'utilisateur. Seul le jeton OAuth, vérifiable auprès de Google, l'est.

**Diagnostic en production :** déployez `identite` avec l'autorisation, ajoutez-le pour un groupe pilote. S'il répond
« Oui, … acme.example », toute la chaîne OAuth fonctionne. Vos autres agents OAuth utiliseront la même.

---

## 4. Utiliser les outils de Gemini Enterprise (e-mail, Outlook, Slack) ?

**Réponse courte : non, pas directement.** Les **actions** des connecteurs de l'app sont exécutées par l'**assistant**
de l'app et par le **Workflow Builder**. Exemples d'actions disponibles :
- envoyer un message Slack ;
- répondre à un e-mail Outlook (Microsoft Outlook, disponible depuis septembre 2026) ;
- créer un ticket Jira ou ServiceNow ;
- mettre à jour Airtable…

Google ne documente **aucun moyen** pour un agent personnalisé (A2A ou Agent Runtime) d'appeler ces actions.

**Ce que votre agent personnalisé peut faire à la place :**

| Besoin | Solution | Section |
|---|---|---|
| **Lire** les données des sources connectées à l'app (Drive, SharePoint, Confluence…) avec les droits de l'utilisateur | Outil `commun.recherche_gemini_enterprise` (recherche de l'app avec le jeton de l'utilisateur) | [12-3, partie 6](12-3-ajouter-des-agents-un-par-un.md#6-partie-b--utiliser-les-sources-et-connecteurs-de-gemini-enterprise) |
| **Envoyer un e-mail** (Gmail) au nom de l'utilisateur | L'API Gmail avec son jeton (portée `gmail.send`) | Partie 2.3 |
| Agir dans un outil tiers (Outlook, Slack, Jira, Airtable…) | Son API ou son **serveur MCP**, avec le jeton OAuth de l'utilisateur pour ce fournisseur | [12-3, 6.2](12-3-ajouter-des-agents-un-par-un.md#62-exemple--airtable) |
| Enchaîner des actions de l'app **sans code** | Un agent **Workflow Builder** dans l'app, qui utilise les actions des connecteurs | Console de l'app |
| Combiner les deux | L'utilisateur parle à l'assistant de l'app (actions) et à votre agent (logique métier Acme) | — |

---

## 5. Les nouveautés : Gemini agent, Spark… répondront-elles à tout ?

État au **11 octobre 2026**, d'après les annonces publiques (à revérifier dans les notes de version au moment de
décider) :

| Nouveauté | Ce que c'est | Disponibilité |
|---|---|---|
| **Gemini agent** (annoncé le 8 octobre 2026, Gemini at Work) | Un agent **universel** pour le travail : on lui donne des objectifs, il décompose en sous-agents, agit dans les apps Google Workspace (Gmail, Docs, Sheets, Chat…) et des outils tiers, avec de la mémoire. Il peut être appelé par **API** depuis d'autres applications | **Préversion privée** ; « bientôt » plus largement pour certains forfaits Workspace Business et Enterprise. **Aucune date de novembre trouvée** dans les sources publiques |
| **Gemini Spark** (Google I/O, mai 2026) | Agent personnel qui travaille en arrière-plan ; pour Gemini Enterprise, il utilise les **connecteurs existants** (SharePoint, OneDrive, ServiceNow…) et demande une **approbation explicite** avant les actions à risque comme l'envoi d'e-mails | Annoncé en mai 2026 |
| Déjà disponibles et utiles ici | Enregistrement des agents **A2A** (GA, 17 août 2026) ; **import** d'agents A2A et ADK (3 septembre 2026) ; **Agent Registry** dans l'app (25 juin 2026) ; serveurs **MCP personnalisés** comme sources (7 août 2026) ; actions Outlook (29 septembre 2026) | Disponibles |

**Est-ce que ça répondra à tous vos cas ?** Honnêtement : **en partie.**

| Votre cas | Avec Gemini agent / Spark | Reste à faire vous-même |
|---|---|---|
| Actions courantes (e-mail, agenda, documents, connecteurs de l'app) au nom de l'utilisateur | **Oui, probablement** : c'est leur cœur (avec approbation de l'utilisateur) | Rien, si l'agent universel suffit |
| **Logique métier Acme** (tailles, retours, règles internes, vos systèmes et API) | Non : ces agents ne connaissent pas vos règles | Vos agents personnalisés (A2A / Agent Runtime), comme dans ces guides |
| Un agent personnalisé qui **appelle les actions** des connecteurs de l'app | **Rien d'annoncé** en ce sens | Partie 4 : API ou MCP avec le jeton OAuth de l'utilisateur |
| Exposer vos agents dans l'app, entre deux projets | Inchangé | [12-1-4](12-1-4-connecter-agents-app-gemini-enterprise.md) |

**Conseil :** gardez vos agents personnalisés pour **votre** valeur métier, branchés en OAuth pour agir au nom de
l'utilisateur. Laissez l'assistant de l'app (et bientôt le Gemini agent) faire les actions génériques. Le jour où
le Gemini agent sera disponible pour Acme, vérifiez dans les notes de version s'il peut **appeler vos agents A2A**
(il sait déléguer à des sous-agents) : vos agents deviendraient alors ses spécialistes.

**Sources :**
- [Google Cloud : le Gemini agent](https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/gemini-at-work/)
- [9to5Google, 8 octobre 2026](https://9to5google.com/2026/10/08/gemini-agent-google-cloud/)
- [Spark pour Gemini Enterprise](https://epinium.com/en/blog/gemini-spark-arrives-google-declares-the-agentic-enterprise-era-at-i-o-2026/)
- [Gemini agent ou Spark](https://www.aiagentslibrary.com/blog/gemini-agent-vs-gemini-spark/)
- [Notes de version de Gemini Enterprise](https://docs.cloud.google.com/gemini/enterprise/docs/release-notes)
- [Agents A2A et OAuth](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent)
- [Agents ADK et autorisations](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent)

---

## 6. Ce qui peut arriver

| Ce que vous voyez | Cause | Que faire |
|---|---|---|
| L'agent répond « agent déployé sans autorisation OAuth (AUTH_ID absent) » | `AGENTS_OAUTH` vide pour cet agent, ou pas redéployé | 2.4 |
| « aucun jeton reçu » dans le chat | Agent ajouté **sans** l'autorisation, ou l'utilisateur n'a pas cliqué « Autoriser » | 2.6 (retirer puis rajouter avec `AUTH_ID`) |
| Pas de bouton « Autoriser » | Agent ajouté sans autorisation | 2.6 |
| Erreur dans la fenêtre de consentement (`redirect_uri_mismatch`) | URI de redirection absentes du client OAuth | 2.1, les deux URI exactes |
| « Accès bloqué : cette application est réservée… » | Écran de consentement **Interne**, utilisateur d'un autre domaine | Normal ; utiliser un compte Acme |
| « jeton reçu, mais Google ne le reconnaît pas » | Jeton d'un autre fournisseur (Airtable, Jira…), ou expiré | Normal pour un fournisseur tiers ; sinon redemander l'autorisation |
| `403` de l'API appelée par l'outil (Gmail, Drive…) | Portée manquante dans l'autorisation, ou API non activée | 2.1 (portée, API) ; recréer l'autorisation ; l'utilisateur ré-autorise |
| `ÉCHEC : TenantProject … does not exist` (`autorisation_oauth.sh`) | Pas d'app Gemini Enterprise dans ce projet / cette localisation | Vérifier `PROJET_APP`, `NUM_APP`, `GE_LOCATION` |
