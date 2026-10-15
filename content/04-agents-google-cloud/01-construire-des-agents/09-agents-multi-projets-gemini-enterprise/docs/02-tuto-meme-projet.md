# 02. Tutoriel : créer un agent simple dans le projet de l'app, l'ajouter, le tester

**Pour qui :** toute personne qui veut faire un premier agent de bout en bout, en 45 minutes, uniquement avec la console et
**Cloud Shell** (le terminal intégré à la console, icône `>_` en haut à droite). Rien à installer sur votre poste.
**Résultat :** un agent « Règles de congés » déployé sur **Agent Runtime**, dans le **même projet** que l'app Gemini
Enterprise, utilisable dans le chat par un groupe de testeurs.

> Ce tutoriel est la **référence** des étapes communes : les autres documents (agent dans un autre projet, agent déjà dans
> un registre) y renvoient et ne décrivent que ce qui change.

---

## Sommaire

0. [Même projet : ce qui est plus simple](#0-même-projet--ce-qui-est-plus-simple)
1. [Prérequis : l'app Gemini Enterprise](#1-prérequis--lapp-gemini-enterprise)
2. [Activer Agent Platform](#2-activer-agent-platform)
3. [Écrire l'agent](#3-écrire-lagent)
4. [Le tester avant de le déployer](#4-le-tester-avant-de-le-déployer)
5. [Le déployer sur Agent Runtime](#5-le-déployer-sur-agent-runtime)
6. [L'ajouter dans l'app](#6-lajouter-dans-lapp)
7. [Donner l'accès et tester dans le chat](#7-donner-laccès-et-tester-dans-le-chat)
8. [Le plan de test complet](#8-le-plan-de-test-complet)
9. [Retirer et nettoyer](#9-retirer-et-nettoyer)
10. [Dépannage](#10-dépannage)
11. [Variante sans code : Agent Designer](#11-variante-sans-code--agent-designer)

---

## 0. Même projet : ce qui est plus simple

```
 PROJET A : "acme-ge-demo"
 ┌───────────────────────────────────────────────────────────────┐
 │ App Gemini Enterprise (eu)          Agent Runtime (europe-west1)│
 │  └─ Agents : "Règles de congés" ──appelle──▶ conges-agent        │
 │                                                                 │
 │ Compte de service de Gemini Enterprise : a DÉJÀ le droit,       │
 │ dans son propre projet, d'appeler les agents Agent Runtime.     │
 └───────────────────────────────────────────────────────────────┘
```

| | Même projet (ce tutoriel) | Autre projet ([doc 03](03-tuto-autre-projet.md)) |
|---|---|---|
| Droit à donner pour un agent **Agent Runtime** | **Aucun** : le compte de Gemini Enterprise a déjà le rôle *Discovery Engine Service Agent* sur son projet (attribué par Google) | *Discovery Engine Service Agent* dans le projet de l'agent |
| Droit pour un agent **Cloud Run (A2A)** | *Cloud Run Invoker* sur le service (même dans le même projet) | Idem, dans l'autre projet |
| Règle de région | Agent en `europe-*` pour une app `eu` | Idem |
| Facturation, journaux, budgets | Tout au même endroit | Répartis entre les deux projets |
| Quand le choisir | Agents de l'équipe qui possède l'app ; démos ; pilote | Agents d'autres équipes, qui gardent leur projet |

**Limite du même projet :** toutes les équipes qui y déploient partagent les mêmes droits projet. Pour des agents de
plusieurs équipes, préférez un projet par équipe ([doc 03](03-tuto-autre-projet.md)).

---

## 1. Prérequis : l'app Gemini Enterprise

**Si l'app existe déjà**, passez à l'étape 2. Notez juste son **projet** (`acme-ge-demo` dans ce guide) et vérifiez
qu'elle est en **`eu`**.

**Sinon, la créer (une fois) :**

1. **Projet :** console → sélecteur de projet → **Nouveau projet** → `acme-ge-demo`, votre **organisation**, votre
   dossier → **Créer**. 🔎 « Facturation » : le projet doit être rattaché au compte de facturation.
2. **App :** 🔎 « Gemini Enterprise » → la première fois, accepter les conditions et **démarrer un essai** (ou rattacher
   l'abonnement) → **Créer une application** :
   - nom : `Acme GE démo` ;
   - **emplacement : `eu`**. Il est **définitif**, et il impose des agents en `europe-*` ;
   - entreprise : `Acme`.

   Puis **Créer**.
3. **Identité :** Gemini Enterprise → **Paramètres** → **Authentification** → pour `eu` : **Google Identity**
   (comptes Workspace / Cloud Identity). Entra ID ou Okta : décision à prendre avec la sécurité, difficile à changer ensuite.
4. **Testeurs :** 🔎 « IAM » → **Accorder l'accès** → le **groupe** des testeurs (ex. `ge-testeurs@acme.example`) → rôle
   **Gemini Enterprise User** (`roles/discoveryengine.agentspaceUser`). Puis Gemini Enterprise → **Licences** → attribuer
   une licence à chaque testeur.
5. **Lien de l'app :** Gemini Enterprise → l'app → **Intégration** → copier le **lien de l'app web**, l'ouvrir : le chat répond.

**Vos droits pour ce tutoriel :** *Gemini Enterprise Admin* et *Agent Platform Admin* (`roles/aiplatform.admin`) sur le
projet, ou *Owner* en démo.

---

## 2. Activer Agent Platform

🔎 « API et services » → **Bibliothèque** → **Agent Platform API** (ex-Vertex AI, `aiplatform.googleapis.com`) → **Activer**.
Elle sert au modèle Gemini **et** à l'hébergement Agent Runtime.

Équivalent Cloud Shell : `gcloud services enable aiplatform.googleapis.com --project=acme-ge-demo`

---

## 3. Écrire l'agent

Un agent ADK, c'est un dossier Python avec un `root_agent`. Celui-ci a **un outil** (`regle_conges`) et des consignes, dont
un **refus** : il ne parle jamais de la situation individuelle d'un salarié.

Ouvrir **Cloud Shell**, puis :

```bash
gcloud config set project acme-ge-demo
pip install --user "google-adk[a2a]==2.10.0" "google-cloud-aiplatform[agent_engines,adk]==2.2.0"
export PATH=$HOME/.local/bin:$PATH

mkdir -p ~/agents/conges_agent && cd ~/agents
echo "from . import agent" > conges_agent/__init__.py
printf 'google-adk[a2a]==2.10.0\n' > conges_agent/requirements.txt
cat > conges_agent/agent.py <<'EOF'
from google.adk.agents import Agent
from google.adk.models import Gemini

REGLES = {
    "conges payes": "25 jours ouvrés par an, acquis à raison de 2,08 jours par mois travaillé.",
    "rtt": "Selon l'accord d'entreprise : 10 jours par an pour un forfait jours.",
    "mariage": "4 jours ouvrés pour le mariage ou le PACS du salarié.",
    "naissance": "3 jours ouvrés, plus le congé de paternité de 25 jours calendaires.",
}

def regle_conges(type_conge: str) -> dict:
    """Règle Acme pour un type de congé.

    Args:
        type_conge: "conges payes", "rtt", "mariage" ou "naissance".
    """
    regle = REGLES.get(type_conge.strip().lower().replace("é", "e"))
    if regle is None:
        return {"status": "error", "error_message": f"Type inconnu. Connus : {', '.join(REGLES)}."}
    return {"status": "success", "type": type_conge, "regle": regle}

root_agent = Agent(
    name="conges_agent",
    model=Gemini(model="gemini-3.5-flash", client_kwargs={"enterprise": True, "location": "global"}),
    description="Répond aux questions générales sur les règles de congés Acme (congés payés, RTT, événements familiaux).",
    instruction=(
        "Tu réponds aux questions générales sur les congés. Appelle toujours regle_conges et cite la règle. "
        "Tu ne réponds jamais sur la situation individuelle d'un salarié (solde, demande en cours) : "
        "renvoie alors vers le RRH."
    ),
    tools=[regle_conges],
)
EOF
```

Le même code est dans le dépôt : `agents/meme_projet/conges_agent/` (avec un autotest :
`python agents/meme_projet/conges_agent/agent.py` → `conges_agent OK`).

**Pourquoi la description compte :** dans Gemini Enterprise, c'est elle qui permet à l'assistant et aux utilisateurs de
choisir le bon agent. Elle doit dire **ce que fait** l'agent, en une phrase.

---

## 4. Le tester avant de le déployer

```bash
cd ~/agents && adk web --port 8080 .
```

Cloud Shell → **Aperçu sur le Web** → **Prévisualiser sur le port 8080** → choisir `conges_agent` :

| Question | Attendu |
|---|---|
| « Combien de jours pour un mariage ? » | Appel de `regle_conges("mariage")` → « 4 jours ouvrés… » |
| « Combien de RTT ? » | « 10 jours par an pour un forfait jours » |
| « Combien de congés me reste-t-il ? » | **Refus poli**, renvoi vers le RRH |

`Ctrl+C` pour arrêter. **Pourquoi ce test :** si l'agent ne marche pas ici, il ne marchera pas dans Gemini Enterprise. On
sépare les problèmes d'agent des problèmes de droits.

---

## 5. Le déployer sur Agent Runtime

```bash
cd ~/agents
adk deploy agent_engine --project=acme-ge-demo --region=europe-west1 \
  --display_name="conges-agent" --description="Règles de congés Acme" conges_agent
```

Durée : 5 à 10 minutes. À la fin, la commande affiche le **nom de ressource** :
`projects/NUM_PROJET/locations/europe-west1/reasoningEngines/1234567890`. Notez-le.

**Dans la console :** 🔎 « Agent Runtime » (menu *Agent Platform* → **Déploiements**) → `conges-agent` :
- onglet **Playground** : reposer les questions de l'étape 4 ;
- onglets **Journaux** et **Sessions** : ce qui s'est passé.

**Pourquoi `europe-west1` :** l'app est en `eu`, et Google n'accepte que des agents en `europe-*` pour une app `eu`.

**Le droit d'appel :** rien à faire dans le même projet. Pour le constater : 🔎 « IAM » → cocher **Inclure les attributions
de rôles fournies par Google** → le compte `service-NUM_PROJET@gcp-sa-discoveryengine.iam.gserviceaccount.com` a le rôle
**Discovery Engine Service Agent**.

---

## 6. L'ajouter dans l'app

**Console :**

1. 🔎 « Gemini Enterprise » → l'app → **Agents** → **Ajouter un agent**.
2. **Agent personnalisé via Agent Runtime** (*Custom agent via Agent Runtime*) → **Ajouter**.
3. *Autorisations* : **ignorer**. L'agent n'accède à aucune donnée au nom de l'utilisateur ; sinon, on ajouterait ici une
   autorisation OAuth.
4. Nom : `Règles de congés`. Description : « Répond aux questions générales sur les règles de congés Acme ».
5. **Ressource Agent Runtime** : le nom de ressource de l'étape 5.
6. **Créer**.

**API** (même résultat, scriptable) :

```bash
GE_PROJECT=acme-ge-demo; GE_APP=ID_DE_L_APP; ENGINE=projects/NUM_PROJET/locations/europe-west1/reasoningEngines/1234567890
curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: $GE_PROJECT" \
  "https://eu-discoveryengine.googleapis.com/v1alpha/projects/$GE_PROJECT/locations/eu/collections/default_collection/engines/$GE_APP/assistants/default_assistant/agents" \
  -d '{"displayName": "Règles de congés", "description": "Répond aux questions générales sur les règles de congés Acme",
       "adkAgentDefinition": {"provisionedReasoningEngine": {"reasoningEngine": "'$ENGINE'"}}}'
```

Ou avec le script du dépôt : `GE_PROJECT=… GE_APP=… ./scripts/add_agent_to_ge.sh adk $ENGINE "Règles de congés"`.
L'ID de l'app se lit dans Gemini Enterprise → l'app → **Présentation**.

---

## 7. Donner l'accès et tester dans le chat

1. **Accès à l'agent :** app → **Agents** → `Règles de congés` → onglet **Autorisations utilisateur** → **Ajouter** → le
   groupe des testeurs → rôle **Agent User** → **Enregistrer**.
2. **Test :** ouvrir le lien de l'app web avec un compte testeur → panneau **Agents** (ou la galerie) → `Règles de congés`
   → « Combien de jours pour une naissance ? ».
3. **Attendu :** « 3 jours ouvrés, plus le congé de paternité de 25 jours calendaires ». La toute première réponse est plus
   lente (démarrage de l'agent).
4. **Ce qui s'est passé :** Agent Runtime → `conges-agent` → **Sessions** : une session par conversation, avec l'appel de
   l'outil.

---

## 8. Le plan de test complet

| # | Test | Comment | Attendu |
|---|---|---|---|
| T1 | L'outil seul | `python agents/meme_projet/conges_agent/agent.py` | `conges_agent OK` |
| T2 | L'agent en local | Étape 4 | Bonnes réponses, refus sur le cas individuel |
| T3 | L'agent déployé | Playground Agent Runtime, ou `AGENT_NAME=$ENGINE python scripts/query.py - "Combien de RTT ?"` | Même réponse qu'en local |
| T4 | L'agent dans le chat | Étape 7 | Même réponse, via l'app |
| T5 | Refus | « Combien de congés me reste-t-il ? » dans le chat | Renvoi vers le RRH |
| T6 | Accès | Un compte **hors** du groupe testeurs ouvre l'app | L'agent **n'apparaît pas** |
| T7 | Hors sujet | « Écris-moi un poème » | Refus poli ou réponse recentrée |

Les tests T1 à T3 isolent l'agent ; T4 à T6 testent l'intégration et les droits. Si T3 marche et T4 échoue, le problème
est dans l'ajout ou les droits, pas dans l'agent.

---

## 9. Retirer et nettoyer

1. **Retirer de l'app :** app → **Agents** → `Règles de congés` → **Supprimer**. L'agent n'est plus proposé, mais il existe
   toujours sur Agent Runtime.
2. **Supprimer l'agent :** Agent Runtime → `conges-agent` → **Supprimer**. Il ne coûte plus rien.

Coût de ce tutoriel : quelques centimes (Agent Runtime facture à l'usage, avec 0 instance minimum par défaut).

---

## 10. Dépannage

| Symptôme | Cause probable | Correction |
|---|---|---|
| `adk: command not found` | Le dossier `~/.local/bin` n'est pas dans le PATH | `export PATH=$HOME/.local/bin:$PATH` |
| `adk deploy` échoue : API désactivée | Agent Platform API non activée | Étape 2 |
| Ajout refusé : région | Agent hors `europe-*` pour une app `eu` | Redéployer avec `--region=europe-west1` |
| L'agent n'apparaît pas dans le chat | Pas de rôle *Agent User* ou pas de licence | Étape 7.1 ; licences (étape 1.4) |
| L'agent apparaît mais ne répond pas | Agent en erreur au démarrage | Agent Runtime → Journaux ; refaire T3 |
| Réponse « je ne sais pas » sans appel d'outil | Description ou consignes trop vagues | Préciser l'instruction (« Appelle toujours… ») |

---

## 11. Variante sans code : Agent Designer

Pour un agent de ce type (questions sur un document de règles), **aucun code n'est nécessaire** :
1. app web → **Agents** → **Créer un agent** ;
2. décrire la mission ;
3. choisir comme source le dossier Drive du guide RH ;
4. tester, publier, partager.

C'est le niveau 1 décrit dans la [doc 07](07-autonomie-utilisateurs.md).

Le code devient utile quand l'agent doit **calculer**, appeler une **API interne**, ou suivre une **logique précise** : c'est
ce que montre ce tutoriel.

**Avant la production** (Model Armor dans l'agent, identité dédiée, Terraform) : voir
[doc 03, étape 8](03-tuto-autre-projet.md#étape-8--avant-la-production).
