# 01. Comprendre et choisir : les façons d'ajouter un agent à Gemini Enterprise

**Pour qui :** administrateurs Gemini Enterprise, équipes qui publient des agents, sécurité, PM.
**Ce document ne contient pas de pas à pas :** il aide à choisir, puis renvoie au bon tutoriel.


---

## 1. Les six façons, en un tableau

| # | Modalité | Qui la fait | L'agent tourne où | Code ? | Cross-project | Model Armor de l'app s'applique ? | Passe par Agent Gateway ? |
|---|---|---|---|---|---|---|---|
| 1 | **Agent Designer** (sans code) | Utilisateur ou admin, dans l'app web | Dans Gemini Enterprise | Non | — | Oui | Selon config de l'app |
| 2 | **Agent ADK sur Agent Runtime** (*Custom agent via Agent Runtime*) | Admin GE ou builder | Agent Runtime, même projet ou **n'importe quel projet** | Oui (ADK) | **Oui** : rôle `discoveryengine.serviceAgent` | **Non** → plugin dans l'agent + plancher *Agent Platform* | Si l'agent est configuré pour (`agent_gateway_config`) |
| 3 | **Agent A2A** (*Custom agent via A2A*) | Admin GE ou builder | N'importe où en HTTPS (Cloud Run, GKE, autre cloud) | Oui (tout framework parlant A2A v0.3) | **Oui** : `run.invoker` si Cloud Run | **Non** → filtrage dans l'agent | **Non** (doc Google : le trafic A2A ajouté ainsi ne passe pas par la passerelle) |
| 4 | **Import depuis Agent Registry** | Admin GE | Agent Runtime, Cloud Run… (enregistré au registre) | Oui | Selon le registre relié à la passerelle (à valider) | Non → filtrage dans l'agent | **Oui, obligatoire** : le registre doit être relié à l'Agent Gateway de l'app |
| 5 | **Agent Dialogflow** | Admin GE | Dialogflow CX | Non / peu | Selon projet Dialogflow | — | — |
| 6 | **Agent Marketplace / partenaire** | Admin GE | Chez l'éditeur | Non | — | Non | — |

**Lecture sécurité :** Model Armor de l'app ne couvre que l'**assistant** et Agent Designer. Tout agent apporté de
l'extérieur (2, 3, 4) doit **se filtrer lui-même**. C'est pour ça que nos agents refusent de démarrer sans template Model Armor.

---

## 2. Quelle modalité choisir ?

```
L'agent existe-t-il déjà ?
├── Non, et c'est un besoin simple (FAQ, résumé, rédaction sur nos données) ──▶ 1. Agent Designer
└── Oui, ou il faut du code (outils, API, logique)
    ├── Écrit en ADK et hébergeable chez Google ─────────────────────────────▶ 2. ADK sur Agent Runtime  (RECOMMANDÉ)
    ├── Autre framework, ou hébergé hors Agent Runtime (Cloud Run, autre cloud) ▶ 3. A2A
    └── Gouvernance centrale avec Agent Gateway en place ──────────────────────▶ 4. Import depuis Agent Registry
```

Pourquoi **2** par défaut : hébergement géré, identité dédiée, journaux, sessions, enregistrement automatique dans Agent
Registry, et c'est la mesure 1 de la note de sécurité Acme.

---

## 3. Même projet que l'app, ou autre projet ?

| | Même projet | Autre projet |
|---|---|---|
| Droit à donner (agent Agent Runtime) | **Aucun** | *Discovery Engine Service Agent* dans le projet de l'agent |
| Droit à donner (agent Cloud Run / A2A) | *Cloud Run Invoker* sur le service | Idem |
| Pour qui | L'équipe qui possède l'app, démos, pilote | Les autres équipes, qui gardent la maîtrise de leur projet |
| Tutoriel | [02 – même projet](02-tuto-meme-projet.md) | [03 – autre projet](03-tuto-autre-projet.md) |

Toutes les règles de droits et de régions sont dans un seul document : [05 – droits et régions](05-droits-et-regions.md).

---

## 4. Où trouver le pas à pas

| Je veux… | Document |
|---|---|
| Créer un premier agent, l'ajouter, le tester (le plus simple) | [02 – tutoriel même projet](02-tuto-meme-projet.md) |
| Ajouter un agent déployé dans **un autre projet** (Agent Runtime, Cloud Run + A2A, Agent Registry + Gateway) | [03 – tutoriel autre projet](03-tuto-autre-projet.md) |
| Ajouter un agent qui est **déjà dans l'Agent Registry** d'une équipe | [04 – agents déjà dans un registre](04-agents-deja-dans-un-registry.md) |
| Savoir **qui donne quel droit** à qui, et les règles de région | [05 – droits et régions](05-droits-et-regions.md) |
| Faire **appeler un agent par un autre agent** | [06 – appels entre agents](06-appels-entre-agents.md) |
| Savoir ce que les **utilisateurs** peuvent faire seuls, et le rôle « builder » | [07 – autonomie des utilisateurs](07-autonomie-utilisateurs.md) |
| Remplir **chaque mode** de la fenêtre *Ajouter un agent*, et connecter l'agent d'une équipe **depuis son projet** | [09 – connecter à Gemini Enterprise](09-connecter-a-gemini-enterprise.md) |
| Construire **6 vrais agents** et les publier **en code**, sur Cloud Run (A2A) **ou** Agent Runtime, même projet ou autre projet | [08 – tutoriel trio](08-tuto-trio-pas-a-pas.md), puis [01-bis](../01-bis-cloud-run-a2a/README.md) ou [02-bis](../02-bis-agent-runtime/README.md) |
| Faire tout cela **en code** (Terraform, PR) | [README du projet](../README.md) |

---

## 5. Après l'ajout, toujours

- **Qui peut utiliser l'agent :** rôle **Agent User** donné à un **groupe**, dans l'onglet *Autorisations utilisateur* de
  l'agent ([02, étape 7](02-tuto-meme-projet.md#7-donner-laccès-et-tester-dans-le-chat)).
- **La description** de l'agent est précise : c'est elle qui le fait choisir.
- **Retirer un agent** de l'app ne le supprime pas de son projet ([02, étape 9](02-tuto-meme-projet.md#9-retirer-et-nettoyer)).
- **Avant la production :** Model Armor dans l'agent, identité dédiée, confirmation humaine des actions, Terraform
  ([03, étape 8](03-tuto-autre-projet.md#étape-8--avant-la-production)).
