# 03. Tutoriel : un agent dans un AUTRE projet, utilisable dans le chat Gemini Enterprise

**Pour qui :** toute personne qui veut le faire une première fois à la main, dans la console Google Cloud.
**Résultat :** un agent déployé dans un projet B apparaît dans l'app Gemini Enterprise du projet A, et répond normalement
dans le chat.

On utilise uniquement la **console** et **Cloud Shell**. **Faites d'abord le [tutoriel 02 (même projet)](02-tuto-meme-projet.md)** :
ce document ne décrit que **ce qui change** quand l'agent vit dans un autre projet, et les deux méthodes en plus
(Cloud Run + A2A, Agent Registry + Agent Gateway).

```
 PROJET A : "acme-ge-demo"                     PROJET B : "acme-agents-demo"
 ┌──────────────────────────────────┐               ┌────────────────────────────────────────────┐
 │ App Gemini Enterprise (eu)       │               │ Méthode 1 : Agent Runtime (Vertex AI)      │
 │  ├─ chat des utilisateurs        │──── appelle ─▶│ Méthode 2 : Cloud Run + A2A                │
 │  └─ Agents : stock (x3 méthodes) │               │ Méthode 3 : via Agent Registry + Gateway   │
 │ Compte de service GE :           │               │ IAM : droits donnés AU compte GE du projet A│
 │ service-NUM_A@gcp-sa-discovery…  │               └────────────────────────────────────────────┘
 └──────────────────────────────────┘
```

| Méthode | Héberge l'agent | Ajout dans GE | Droit dans le projet B | Difficulté | Quand la choisir |
|---|---|---|---|---|---|
| **1. Agent Runtime** (Vertex AI / Agent Platform) | Google, géré | *Agent personnalisé via Agent Runtime* | `Discovery Engine Service Agent` sur le projet B | ★☆☆ | **Par défaut** pour un agent ADK |
| **2. Cloud Run + A2A** | Cloud Run (conteneur) | *Agent personnalisé via A2A* | `Cloud Run Invoker` sur le service | ★★☆ | Agent existant sur Cloud Run, autre framework |
| **3. Agent Registry + Agent Gateway** | Agent Runtime ou Cloud Run | Import depuis le registre | Comme 1 ou 2, + autorisation de la passerelle | ★★★ | Gouvernance centrale, trafic contrôlé |

---

## Sommaire

0. [Prérequis](#étape-0--prérequis)
1. [Projet A : l'app Gemini Enterprise et son compte de service](#étape-1--projet-a--lapp-et-son-compte-de-service)
2. [Projet B : créer le projet et écrire l'agent](#étape-2--projet-b--le-projet-et-lagent)
3. [Méthode 1 : Agent Runtime](#méthode-1--agent-runtime-vertex-ai)
4. [Méthode 2 : Cloud Run + A2A](#méthode-2--cloud-run--a2a)
5. [Méthode 3 : Agent Registry + Agent Gateway](#méthode-3--agent-registry--agent-gateway)
6. [Donner l'accès aux utilisateurs et tester dans le chat](#étape-6--donner-laccès-et-tester-dans-le-chat)
7. [Dépannage](#étape-7--dépannage)
8. [Avant la production](#étape-8--avant-la-production)

---

## Étape 0 : prérequis

| Besoin | Pourquoi |
|---|---|
| Un compte **Google d'entreprise** (Workspace ou Cloud Identity), pas un Gmail | Gemini Enterprise est réservé aux organisations |
| Une **organisation** Google Cloud et un **compte de facturation** | Les deux projets doivent être rattachés à l'organisation et facturés |
| Rôles : *Project Creator*, *Billing Account User* ; puis *Owner* sur les deux projets (en démo) | Créer les projets, activer les services, poser les droits |
| Des **licences** Gemini Enterprise (ou un essai) | Pour utiliser le chat |

Dans tout le guide, remplacez :
- `acme-ge-demo` par l'ID de votre projet A, et `NUM_A` par son **numéro** (page d'accueil du projet, carte *Informations sur le projet*) ;
- `acme-agents-demo` par l'ID du projet B, et `NUM_B` par son numéro.

---

## Étape 1 : projet A : l'app et son compte de service

1. Créer (si besoin) le projet A et l'app Gemini Enterprise en `eu`, l'identité et les testeurs :
   **[tutoriel 02, étape 1](02-tuto-meme-projet.md#1-prérequis--lapp-gemini-enterprise)**.
2. Noter le **compte de service de Gemini Enterprise** du projet A. C'est **lui** qui appellera l'agent du projet B, et c'est
   **à lui** que le projet B donnera des droits :

```
service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com
```

(Visible dans 🔎 « IAM » du projet A, en cochant *Inclure les attributions de rôles fournies par Google*.)

---

## Étape 2 : projet B : le projet et l'agent

### 2.1 Créer le projet B et activer les API

1. **Nouveau projet** → `acme-agents-demo`, même organisation, même facturation.
2. 🔎 « API et services » → **Bibliothèque** → activer :
   - **Agent Platform API** (ex-Vertex AI, `aiplatform.googleapis.com`) : modèle Gemini et Agent Runtime ;
   - **Cloud Run Admin API**, **Cloud Build API**, **Artifact Registry API** : méthode 2 ;
   - **Agent Registry API** : méthode 3.

### 2.2 Écrire et tester l'agent

Exactement comme dans le **[tutoriel 02, étapes 3 et 4](02-tuto-meme-projet.md#3-écrire-lagent)**, avec deux différences :
- dans Cloud Shell : `gcloud config set project acme-agents-demo` (projet **B**) ;
- les exemples ci-dessous utilisent un agent `stock_agent` (code dans le dépôt : `agents/specialist/stock_agent`). L'agent
  `conges_agent` du tutoriel 02 convient tout aussi bien : remplacez simplement le nom du dossier.

---

## Méthode 1 : Agent Runtime (Vertex AI)

**Le principe :** Google héberge l'agent (pas de serveur à gérer), avec des sessions et des journaux. Gemini Enterprise
l'appelle par son **nom de ressource**.

### M1.1 Déployer l'agent (projet B)

```bash
cd ~/agents
adk deploy agent_engine --project=acme-agents-demo --region=europe-west1 \
  --display_name="stock-agent" --description="Stock d'un article par magasin" stock_agent
```

Durée : 5 à 10 minutes. À la fin, la commande affiche le nom de ressource :
`projects/NUM_B/locations/europe-west1/reasoningEngines/1234567890`.

**Dans la console :** 🔎 « Agent Runtime » (menu *Agent Platform* → **Déploiements**) → `stock-agent` apparaît.
Cliquer dessus : onglets *Playground* (pour tester), *Journaux*, *Sessions*. Copier le **nom de la ressource**.

**Pourquoi `europe-west1` :** l'app est en `eu`. Google n'accepte que des agents en `europe-*` pour une app `eu`.

### M1.2 Autoriser Gemini Enterprise (projet A) dans le projet B

C'est l'étape qu'on oublie. Sans elle, l'agent s'ajoute, mais ne répond pas dans le chat.

1. Sélectionner le **projet B** → 🔎 « IAM » → **Accorder l'accès**.
2. *Nouveaux comptes principaux* : `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` (le compte de l'**app**,
   donc du projet **A**).
3. Rôle : **Discovery Engine Service Agent** (`roles/discoveryengine.serviceAgent`).
4. **Enregistrer**.

> Si la console refuse de sélectionner un rôle d'« agent de service », utiliser Cloud Shell :
> ```bash
> gcloud projects add-iam-policy-binding acme-agents-demo --condition=None \
>   --role=roles/discoveryengine.serviceAgent \
>   --member=serviceAccount:service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com
> ```

### M1.3 Ajouter l'agent dans l'app (projet A)

Identique au **[tutoriel 02, étape 6](02-tuto-meme-projet.md#6-lajouter-dans-lapp)**, dans le **projet A**, avec le nom de
ressource de l'agent du **projet B** (`projects/NUM_B/locations/europe-west1/reasoningEngines/…`).

→ [Étape 6](#étape-6--donner-laccès-et-tester-dans-le-chat) pour le tester dans le chat.

---

## Méthode 2 : Cloud Run + A2A

**Le principe :** l'agent tourne dans un conteneur Cloud Run et parle le protocole ouvert **A2A**. Il publie une **carte
d'agent** (JSON), que l'on colle dans Gemini Enterprise. Gemini Enterprise appelle le service avec un jeton de **son** compte
de service : le service reste **privé**.

### M2.1 Préparer la carte d'agent (projet B)

L'adresse d'un service Cloud Run est prévisible : `https://NOM-NUM_B.REGION.run.app`. ADK expose l'agent A2A sous
`/a2a/<dossier>`.

```bash
cd ~/agents
NUM_B=$(gcloud projects describe acme-agents-demo --format='value(projectNumber)')
URL="https://stock-agent-a2a-$NUM_B.europe-west1.run.app/a2a/stock_agent"
cat > stock_agent/agent.json <<EOF
{
  "protocolVersion": "0.3",
  "name": "stock_agent",
  "description": "Donne le stock d'un article Acme par magasin, à partir de son code article.",
  "url": "$URL",
  "preferredTransport": "JSONRPC",
  "version": "1.0.0",
  "capabilities": {"streaming": true},
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"],
  "skills": [{"id": "stock", "name": "Stock magasin",
              "description": "Stock d'un article par magasin", "tags": ["stock", "magasin"],
              "examples": ["Stock de 8771234 ?"]}]
}
EOF
cat stock_agent/agent.json
```

### M2.2 Déployer sur Cloud Run, en privé

```bash
adk deploy cloud_run --project=acme-agents-demo --region=europe-west1 \
  --service_name=stock-agent-a2a --a2a stock_agent -- --no-allow-unauthenticated
```

Tout ce qui suit `--` est transmis à `gcloud run deploy`. `--no-allow-unauthenticated` signifie : **pas d'accès public**.
Durée : 5 à 10 minutes (construction du conteneur).

**Vérifier la carte**, avec votre propre jeton. Le serveur ADK la renvoie dans le format A2A le plus récent, et il accepte aussi les appels **v0.3** (`message/send`) qu'utilise Gemini Enterprise (vérifié en local avec ADK 2.10 / a2a-sdk 1.2) :

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  "$URL/.well-known/agent-card.json" | head -c 400
```

**Dans la console :** 🔎 « Cloud Run » → `stock-agent-a2a` → l'URL affichée doit être `https://stock-agent-a2a-NUM_B.europe-west1.run.app`.
Si elle est différente (ancien format d'URL), corriger `url` dans `agent.json` et redéployer.

### M2.3 Autoriser Gemini Enterprise à appeler le service

1. **Projet B** → 🔎 « Cloud Run » → cliquer sur `stock-agent-a2a` → onglet **Sécurité** (ou **Autorisations** selon la
   version) → **Ajouter un compte principal**.
2. Compte : `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com`.
3. Rôle : **Demandeur Cloud Run** (*Cloud Run Invoker*, `roles/run.invoker`) → **Enregistrer**.

On donne le droit **sur ce service uniquement**, pas sur tout le projet B.

### M2.4 Ajouter l'agent dans l'app (projet A)

1. **Projet A** → Gemini Enterprise → l'app → **Agents** → **Ajouter un agent** → **Agent personnalisé via A2A** → **Ajouter**.
2. Coller **le contenu** de `agent.json` (le JSON, pas l'URL).
3. **Prévisualiser les détails de l'agent** → vérifier le nom, la description, les compétences → **Suivant**.
4. *Authentification* : **ignorer** (le jeton du compte Gemini Enterprise suffit pour Cloud Run).
5. **Terminer**.

**À savoir :**
- un agent A2A ajouté ainsi n'est **pas** filtré par le Model Armor de l'app ;
- il ne passe **pas** par Agent Gateway.

En production, il doit donc se filtrer lui-même (plugin Model Armor dans son code).

---

## Méthode 3 : Agent Registry + Agent Gateway

**Le principe :** au lieu d'ajouter l'agent « en direct », l'app le prend dans un **catalogue** (Agent Registry), et tous les
appels passent par un **poste de contrôle** (Agent Gateway) qui refuse tout ce qui n'est pas autorisé.
C'est la méthode cible pour une gouvernance centrale. Elle demande plus de mise en place.

### M3.1 Règles à respecter (app `eu`)

| Élément | Valeur imposée |
|---|---|
| Agent Gateway | Région **`europe-west1`** |
| Registre utilisé pour l'import | **`europe-west1`** (ou `eu`) |
| L'app | Liée à la passerelle **avant** l'import |

### M3.2 Mettre l'agent du projet B dans le registre du projet A

Le plus simple et le plus sûr en multi-projets : **déclarer** l'agent du projet B dans le registre du **projet A** (celui de
l'app).

1. **Projet A** → activer **Agent Registry API**, **Network Services API**, **IAP API**.
2. 🔎 « Agent Registry » → région **europe-west1** → **Enregistrer** (*Register*) → type **Agent**.
3. Nom `stock-agent-b`, description, spécification **Carte d'agent A2A** : coller le JSON de la méthode 2 (son `url` pointe
   vers le Cloud Run du projet B).
4. **Enregistrer**.

> Les agents Agent Runtime du projet B sont déjà dans le registre **du projet B**, automatiquement. Les importer
> directement depuis ce registre dans une app du projet A dépend de la liaison passerelle ↔ registre d'un autre projet :
> point à valider. La déclaration dans le registre du projet A fonctionne dans tous les cas.

### M3.3 Créer l'Agent Gateway (projet A)

Cloud Shell, **projet A** :

```bash
gcloud config set project acme-ge-demo
cat > ge-egress.yaml <<EOF
name: ge-egress
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
- //agentregistry.googleapis.com/projects/acme-ge-demo/locations/europe-west1
EOF
gcloud network-services agent-gateways import ge-egress --location=europe-west1 --source=ge-egress.yaml
```

### M3.4 Autoriser le passage

La passerelle **refuse tout par défaut**.
1. 🔎 « Agent Registry » → `stock-agent-b` → **Autorisations** → **Ajouter un compte principal** :
   `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` → rôle **IAP-secured Egressor** (`roles/iap.egressor`).
2. Et, comme en M2.3, **Cloud Run Invoker** sur le service du projet B pour ce même compte.

### M3.5 Lier la passerelle à l'app, puis importer

1. **Projet A** → Gemini Enterprise → l'app → **Sécurité** → **Configuration** → *Configuration Agent Gateway* :
   `projects/acme-ge-demo/locations/europe-west1/agentGateways/ge-egress` → **Enregistrer**.
   ⚠ À partir de là, **tout** le trafic de l'app passe par la passerelle, y compris les appels au modèle.
2. L'app → **Agents** → **Ajouter un agent** → choisir `stock-agent-b` dans la liste du registre → **Ajouter** →
   authentification : ignorer → terminer.

---

## Étape 6 : donner l'accès et tester dans le chat

Identique au **[tutoriel 02, étape 7](02-tuto-meme-projet.md#7-donner-laccès-et-tester-dans-le-chat)** (rôle *Agent User* au
groupe, test dans l'app web). Seule différence : les traces de l'agent sont dans le **projet B**.

### 6.1 Voir ce qui s'est passé (projet B)

| Méthode | Où regarder |
|---|---|
| 1 | 🔎 « Agent Runtime » → l'agent → **Journaux** et **Sessions** (une session par conversation) |
| 2 | 🔎 « Cloud Run » → le service → **Journaux** (requête `POST /a2a/stock_agent`, code 200) |
| 3 | Journaux de l'Agent Gateway (projet A) + ceux de la méthode 1 ou 2 |

---

## Étape 7 : dépannage

| Symptôme dans le chat | Cause la plus fréquente | Correction |
|---|---|---|
| L'agent n'apparaît pas dans la liste | Pas de rôle **Agent User** pour l'utilisateur, ou pas de licence | [Tutoriel 02, étape 7](02-tuto-meme-projet.md#7-donner-laccès-et-tester-dans-le-chat) |
| L'agent apparaît mais « n'a pas pu répondre » (méthode 1) | Rôle **Discovery Engine Service Agent** manquant dans le projet B | M1.2 |
| Ajout refusé : région | Agent hors `europe-*` pour une app `eu` | Redéployer en `europe-west1` |
| Erreur 403 dans les journaux Cloud Run (méthode 2) | **Cloud Run Invoker** manquant pour le compte GE | M2.3 |
| Erreur 404 dans les journaux Cloud Run | `url` de la carte fausse (chemin `/a2a/stock_agent` ou ancienne URL) | M2.1, puis redéployer et remettre la carte dans l'app |
| « Preview » de la carte impossible | JSON invalide, ou `protocolVersion` différent de `0.3` | Valider le JSON (`python3 -m json.tool stock_agent/agent.json`) |
| L'agent est absent de la liste d'import (méthode 3) | Registre d'une autre région, ou passerelle non liée | M3.1, M3.5 |
| Tout le chat est bloqué après M3.5 | Autorisation `iap.egressor` manquante | M3.4 ; retirer la liaison pour revenir en arrière |
| L'agent répond « Article inconnu » | L'agent marche, la donnée n'existe pas | Normal |

---

## Étape 8 : avant la production

Ce guide est une **démo** : il va au plus court. Avant d'ouvrir à de vrais utilisateurs :

| Point | Pourquoi | Où c'est fait |
|---|---|---|
| **Model Armor dans l'agent** (plugin) | Model Armor de l'app ne filtre pas les agents ajoutés (méthodes 1 à 3) | `agents/specialist` de ce projet, projet 08 |
| **Identité dédiée** pour l'agent Agent Runtime | Par défaut, il tourne avec le compte partagé du projet B | `modules/adk_agent` |
| **Confirmation humaine** des actions qui modifient | Mesure 9 de la note | projet 08, fiche 08 |
| Accès par **groupe**, agent par agent | Moindre privilège | [Tutoriel 02, étape 7](02-tuto-meme-projet.md#7-donner-laccès-et-tester-dans-le-chat) |
| Tout repris en **Terraform** | Relu, reproductible, détection des dérives | `terraform/` de ce projet (`external_adk_agents`) |
| Journaux d'audit activés dans **les deux** projets | Enquête possible | projet 08, phase 1 étape 1 |

Le même résultat, en code : [README du projet 09](../README.md) (deux projets, droits, publication), et
[05 – droits et régions](05-droits-et-regions.md) pour la matrice complète des droits.
