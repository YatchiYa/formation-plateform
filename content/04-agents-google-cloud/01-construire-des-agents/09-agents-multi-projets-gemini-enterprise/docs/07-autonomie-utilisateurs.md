# 07. Les utilisateurs peuvent-ils ajouter un agent eux-mêmes, sans nous ?

**Pour qui :** admins Gemini Enterprise, sécurité, équipes métier et « builders » qui veulent connecter leurs agents.
**Question :** un utilisateur peut-il connecter lui-même un agent à notre app, depuis l'**interface web Gemini Enterprise**,
sans accès à la console GCP et sans notre aide ? Ou faut-il que l'équipe admin le fasse dans la console ?

---

## 1. Réponse courte

**Ça dépend du type d'agent.**

| Ce que l'utilisateur veut faire | Seul, dans l'app web ? | Qui doit intervenir |
|---|---|---|
| **Créer un agent sans code** (instructions, sources, étapes, planification) avec *Workflow Builder* / *Agent Designer* | ✅ **Oui** | Personne, si la fonctionnalité est activée |
| Utiliser dans cet agent les **connecteurs** (Drive, Jira…) et **serveurs MCP** déjà en place | ✅ Oui | L'admin les a ajoutés avant |
| **Réutiliser un agent ADK ou A2A déjà publié** dans l'app, comme une étape de son workflow | ✅ Oui | L'admin l'a publié avant |
| **Partager** son agent avec des collègues ou des groupes | ✅ Oui, ou ⏳ après validation | L'admin valide, si la validation est activée |
| **Connecter un agent qui tourne ailleurs** (Agent Runtime, Cloud Run / A2A, autre projet GCP) | ❌ **Non** | Un **admin** GE, ou un **builder délégué** (§4) |
| **Connecter son propre serveur MCP** | ❌ Non | Un admin (source de données « MCP personnalisé ») |

En une phrase : **l'app web permet de construire et de composer des agents avec ce qui existe déjà. Faire entrer
quelque chose de nouveau** (un agent de code, un serveur MCP, une source) **passe par la configuration de l'app**,
c'est-à-dire la console GCP ou l'API.

Google l'écrit ainsi : *« les actions et outils disponibles pour un agent ou un workflow sont limités aux connecteurs,
outils et autorisations mis en place par l'administrateur Gemini Enterprise. »*

---

## 2. Les trois niveaux d'autonomie

```
 Niveau 1 : UTILISATEUR               Niveau 2 : BUILDER DÉLÉGUÉ             Niveau 3 : ADMIN GEMINI ENTERPRISE
 (app web uniquement)                 (rôle limité aux agents)               (console GCP du projet de l'app)
 ─────────────────────────            ─────────────────────────              ─────────────────────────────────
 • crée des agents sans code          • publie SES agents ADK / A2A          • tout : connecteurs, MCP, sécurité,
 • compose avec les agents et           (Agent Runtime, Cloud Run,             Model Armor, Agent Gateway, agents
   outils déjà publiés                  autre projet) dans l'app            • valide les partages
 • partage (avec ou sans validation)  • gère qui peut les utiliser          • contrôle tout le reste
 ✗ ne fait rien entrer de neuf        ✗ ne touche pas à la sécurité
 Rôle : Gemini Enterprise User        Rôle : Agent Admin (+ Viewer)          Rôle : Gemini Enterprise Admin
```

| | Rôle IAM (projet de l'app) | Accès console GCP ? | Ce qu'il **ne peut pas** faire |
|---|---|---|---|
| **1. Utilisateur** | `roles/discoveryengine.agentspaceUser` (Gemini Enterprise User) | Non | Ajouter un agent externe, un MCP, une source ; changer un réglage |
| **2. Builder délégué** | `roles/discoveryengine.agentAdmin` (**Agent Admin** : 15 permissions, **uniquement** sur les agents) + `roles/discoveryengine.agentspaceViewer` pour voir l'app en console | Oui, en lecture + agents | Model Armor, connecteurs, identité, CMEK, réglages de l'app, Agent Gateway |
| **3. Admin** | `roles/discoveryengine.agentspaceAdmin` (Gemini Enterprise Admin, 472 permissions) | Oui | — |

Rôles et permissions vérifiés dans IAM. *Agent Admin* contient `discoveryengine.agents.create / update / delete / manage /
setIamPolicy`, et rien d'autre de significatif. C'est exactement « ajouter et partager des agents ».

---

## 3. Niveau 1 : ce que l'utilisateur fait seul, dans l'app web

### 3.1 Créer un agent sans code

1. Ouvrir l'app web Gemini Enterprise → **Agents** → **Créer un agent** (*Workflow Builder*).
2. Décrire l'agent en langage naturel (« un agent qui résume chaque lundi les tickets Jira de mon équipe ») : le
   concepteur propose les instructions et les étapes.
3. Ajouter des **sources** et **outils** : uniquement ceux déjà connectés par l'admin (Drive, Jira, serveurs MCP…).
4. Ajouter une **étape « agent existant »** : choisir un agent **ADK** ou **A2A** déjà publié dans l'app (ex.
   « Stock magasin (Supply) »). C'est ainsi qu'un utilisateur **compose** avec les agents de code, sans les connecter lui-même.
5. Tester → **Publier** → le **partager** (personnes ou groupes).

**Limites à connaître :**
- d'après la documentation Google, le sélecteur d'« agent existant » n'affiche **pas les agents d'autres projets**. Un
  agent cross-project doit donc d'abord être **publié dans l'app** (niveau 2 ou 3) ; il apparaît alors comme un agent de
  l'app (point à vérifier en recette) ;
- si l'agent réutilisé demande une connexion OAuth, l'utilisateur doit s'authentifier avant de lancer le workflow.

### 3.2 Les réglages admin qui ouvrent ou ferment ce niveau

Console → Gemini Enterprise → l'app → **Configurations** → fonctionnalités de l'app web :

| Réglage | Effet | Recommandation Acme |
|---|---|---|
| **Enable chat agents** (création d'agents) | Les utilisateurs peuvent construire des agents | ✅ Activé (pilote), pour un groupe d'abord |
| **Enable agent sharing** | Les utilisateurs peuvent partager leurs agents | ✅ Activé |
| **Enable agent sharing without admin approval** | Partage **sans** validation | ❌ **Désactivé** : l'admin valide chaque partage (`disable-agent-sharing` du projet 08 va dans ce sens) |
| **Enable End Users to share with Groups** | Partage à des groupes entiers | Avec validation uniquement |
| **Enable Agent Gallery** | Galerie des agents disponibles | ✅ Activé (c'est la vitrine) |
| **Enable skills / skill sharing** | Compétences réutilisables | Partage sur approbation |

Avec la validation activée, l'admin traite les demandes dans app → **Agents** → colonne *Autorisations utilisateur* →
**Examiner la demande de partage** (*Review share request*).

---

## 4. Niveau 2 : le « builder délégué », la bonne réponse pour les équipes qui ont des agents de code

**Le besoin :** une équipe (ex. Supply) a son agent sur Agent Runtime, dans **son** projet, et veut le connecter à l'app sans
ouvrir un ticket à chaque version.

**La solution :** lui donner le rôle **Agent Admin** sur le projet de l'app. Elle peut alors ajouter, modifier, retirer et
partager **des agents**, sans pouvoir toucher à la sécurité de l'app.

### 4.1 Ce que l'admin fait une fois

**Projet A (app)** → 🔎 « IAM » → **Accorder l'accès** → groupe `ge-builders-supply@acme.example` → rôles :
- **Agent Admin** (`roles/discoveryengine.agentAdmin`) ;
- **Gemini Enterprise Viewer** (`roles/discoveryengine.agentspaceViewer`), pour ouvrir l'app en console.

Recommandé : une **condition IAM** de date d'expiration (accès revu chaque trimestre).

### 4.2 Ce que l'équipe builder fait ensuite, seule

1. Dans **son** projet B : déployer l'agent ([tutoriel 03](03-tuto-autre-projet.md), méthode 1 ou 2) et donner au compte de Gemini Enterprise du projet A le
   droit cross-project (*Discovery Engine Service Agent* ou *Cloud Run Invoker*). Elle peut le faire : **c'est son projet**.
2. Dans le projet A : console → Gemini Enterprise → l'app → **Agents** → **Ajouter un agent** → Agent Runtime ou A2A
   ([tutoriel 02, étape 6](02-tuto-meme-projet.md#6-lajouter-dans-lapp) ; A2A : [tutoriel 03, M2.4](03-tuto-autre-projet.md#m24-ajouter-lagent-dans-lapp-projet-a)). Ou en ligne de commande : `./scripts/add_agent_to_ge.sh adk|a2a …`.
3. Onglet **Autorisations utilisateur** de l'agent → donner **Agent User** au groupe cible.

**À valider en recette :** que la page *Agents* de la console s'ouvre bien avec ces deux rôles seulement. Repli : l'équipe
passe par l'API ou le script, qui n'ont besoin que d'*Agent Admin*.

### 4.3 Les garde-fous qui rendent la délégation acceptable

| Garde-fou | Pourquoi | Comment |
|---|---|---|
| Le builder **ne peut pas** désactiver Model Armor, la passerelle, les connecteurs | Séparation des rôles | Agent Admin ne contient pas ces permissions |
| **Charte builder** signée : Model Armor dans l'agent, identité dédiée, confirmation humaine des écritures, données en UE | Model Armor de l'app ne filtre pas les agents ajoutés | Modèle `agents/specialist` ; checklist §6 |
| **Alerte** à chaque ajout ou modification d'agent | La sécurité voit tout, sans bloquer | Journal d'audit `discoveryengine`, méthodes `CreateAgent` / `UpdateAgent` (§6) |
| Partage aux groupes **validé** par l'admin | Le builder ne s'ouvre pas tout Acme seul | Réglage §3.2 |
| Revue trimestrielle des builders et de leurs agents | Les droits ne s'accumulent pas | Condition IAM d'expiration |

---

## 5. Niveau 3 : l'admin, ou la PR Terraform

Pour tout ce qui fait **entrer du neuf** autre qu'un agent (serveur MCP, source de données, Agent Gateway, Model Armor), et
pour les équipes qui ne sont pas builders : l'admin Gemini Enterprise, dans la console du projet de l'app ([tutoriels 02 et 03](02-tuto-meme-projet.md)), ou une
**PR** dans `external_adk_agents` (Terraform, README §4). La PR est le mode recommandé en production : relue, tracée, réversible.

---

## 6. Le circuit que nous recommandons pour Acme

| Phase | Qui ajoute les agents de code | Utilisateurs |
|---|---|---|
| **Pilote** (maintenant) | **Admin** uniquement (console ou PR) | Niveau 1 pour un groupe pilote, partage **avec validation** |
| **Généralisation** | **Builders délégués** pour 2-3 équipes certifiées (Supply, Magasins…) + PR pour les autres | Niveau 1 pour tous, partage avec validation |
| **Cible** | Builders + **Agent Registry / Agent Gateway** : seuls les agents du registre sont joignables | Niveau 1 pour tous |

**Checklist avant d'accepter un agent (admin ou builder) :**
- [ ] Hébergé en `europe-*` (app `eu`), sur Agent Runtime de préférence
- [ ] Model Armor dans l'agent (refuse de démarrer sans)
- [ ] Identité dédiée, droits minimum
- [ ] Les actions qui modifient demandent une confirmation humaine
- [ ] Description claire (c'est elle qui fait choisir l'agent)
- [ ] Partagé à un **groupe** précis, pas à toute l'entreprise
- [ ] Propriétaire et contact indiqués (label `owner`)

**Voir qui ajoute quoi** (Logs Explorer, projet de l'app) :

```
logName:"cloudaudit.googleapis.com%2Factivity"
protoPayload.serviceName="discoveryengine.googleapis.com"
protoPayload.methodName=~"(Create|Update|Delete)Agent"
```

Pour en faire une alerte e-mail : métrique basée sur les journaux + règle d'alerte, même modèle que l'alerte
« Shadow AI » du projet 08 (`75_shadow_ai.tf`).

---

## 7. Questions fréquentes

| Question | Réponse |
|---|---|
| Un utilisateur sans accès GCP peut-il coller l'URL de son agent dans l'app web ? | **Non.** Il n'existe pas de bouton « connecter un agent externe » côté utilisateur. Il passe par un builder ou un admin. |
| Un utilisateur peut-il utiliser un agent de code dans son propre agent sans code ? | **Oui**, s'il est déjà publié dans l'app et partagé avec lui (étape « agent existant »). |
| Le builder délégué peut-il casser la sécurité de l'app ? | Non : *Agent Admin* ne donne accès qu'aux agents. Il peut publier un agent mal conçu, d'où la checklist et l'alerte. |
| Le rôle « Gemini Enterprise User » contient pourtant `agents.create` ? | Oui : c'est ce qui permet à chacun de créer **ses** agents sans code dans l'app. Ce rôle sert aux agents de l'utilisateur, pas à connecter un agent externe à toute l'app ; ne pas s'appuyer dessus pour ça. |
| Faut-il donner l'accès au projet B (celui de l'agent) aux utilisateurs ? | **Non.** Les utilisateurs n'ont besoin que de l'app. C'est le **compte de service de Gemini Enterprise** qui appelle l'agent. |
| Et pour un serveur MCP ? | Toujours l'admin (source de données « MCP personnalisé »). Une fois en place, les utilisateurs l'utilisent dans leurs agents sans code. |

---

## Sources

- [Workflow Builder (création d'agents sans code)](https://docs.cloud.google.com/gemini/enterprise/docs/agent-designer)
- [Ajouter un agent existant dans un workflow](https://docs.cloud.google.cn/gemini/enterprise/docs/workflow-builder/add-existing-agents)
- [Connecter des serveurs MCP dans Workflow Builder](https://docs.cloud.google.cn/gemini/enterprise/docs/workflow-builder/connect-mcp-servers)
- [Gérer les fonctionnalités de l'app web](https://docs.cloud.google.com/gemini/enterprise/docs/manage-web-app-features)
- [Partager un agent](https://docs.cloud.google.com/gemini/enterprise/docs/agent-designer/share-agent)
- Rôles IAM vérifiés avec `gcloud iam roles describe` (octobre 2026)
