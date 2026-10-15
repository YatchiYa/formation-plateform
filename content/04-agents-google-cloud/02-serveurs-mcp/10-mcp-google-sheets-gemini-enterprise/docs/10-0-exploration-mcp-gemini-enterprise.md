# 10-0. Exploration : MCP, Google Sheets et Gemini Enterprise

**Ce guide répond à :**
1. Qu'est-ce que MCP, et qu'apporte un serveur MCP Google Sheets par rapport aux agents du projet 09 ?
2. Par quels **chemins** Gemini Enterprise peut-il utiliser un serveur MCP ? Lequel choisir ?
3. Qui appelle qui, avec quel jeton ? Qu'est-ce qui empêche un accès non voulu ?
4. Qu'est-ce qui a été **vérifié en vrai**, et qu'est-ce qui reste à faire sur votre projet ?

Les guides suivants (10-1 à 10-10) font chaque étape, pas à pas.

---

## Sommaire

1. [MCP en 2 minutes](#1-mcp-en-2-minutes)
2. [Les 4 chemins vers Gemini Enterprise](#2-les-4-chemins-vers-gemini-enterprise)
3. [Lequel choisir ?](#3-lequel-choisir-)
4. [Les jetons : qui prouve quoi](#4-les-jetons--qui-prouve-quoi)
5. [Ce que contient ce dossier](#5-ce-que-contient-ce-dossier)
6. [Ce qui a été vérifié, et ce qui reste à faire](#6-ce-qui-a-été-vérifié-et-ce-qui-reste-à-faire)
7. [L'ordre des guides](#7-lordre-des-guides)
8. [Sources](#8-sources)

---

## 1. MCP en 2 minutes

Au projet 09, chaque outil (`lire_emails`, `sheets_ecrire`…) était une fonction Python **dans** l'agent. Pour
qu'un autre agent, Claude, Gemini CLI ou Gemini Enterprise lui-même utilise les mêmes outils, il faudrait les recopier.

**MCP** (Model Context Protocol) est un standard ouvert qui met les outils dans un **serveur à part**. Tout client MCP
peut alors :
- demander `tools/list` : « quels outils as-tu ? » (nom, description, paramètres, et indications lecture ou
  destructif) ;
- demander `tools/call` : « exécute `read_range` avec `{spreadsheet_id, range_a1}` ».

```
  Gemini Enterprise (connecteur) ─┐
  Agent ADK (A2A / Agent Runtime) ─┼── MCP, JSON-RPC sur HTTPS ──▶ serveur MCP « sheets-mcp » ──▶ API Google Sheets
  Claude, Gemini CLI, Inspector  ─┘     (Streamable HTTP, /mcp)      Cloud Run, PRIVÉ             (jeton de l'utilisateur)
```

Les mots à connaître :
- **Outil** (*tool*), qui s'appelle **action** dans Gemini Enterprise : une fonction que le modèle peut appeler.
- **Streamable HTTP** : le transport réseau de MCP, une URL qui finit en `/mcp`. Gemini Enterprise n'accepte **que**
  celui-là (l'ancien SSE est refusé).
- **Annotations** : `readOnlyHint` (lecture) et `destructiveHint` (écrase ou supprime). Gemini Enterprise demande
  une **confirmation** avant chaque action, sauf pour celles marquées en lecture seule.

Un **2e serveur, Google Slides** (20 outils), suit exactement les mêmes chemins : [10-13](10-13-serveur-mcp-google-slides.md).

Notre serveur Sheets a **17 outils** : il peut lire, chercher, écrire, ajouter des lignes, effacer,
créer des classeurs, gérer les onglets, mettre en forme, et appeler **toute l'API Sheets** avec `batch_update`.
Chaque appel se fait **avec le jeton de l'utilisateur** : il ne voit et ne modifie que ce que ses droits Drive
permettent.

## 2. Les 4 chemins vers Gemini Enterprise

| # | Chemin | Comment Gemini Enterprise l'utilise | Guide |
|---|---|---|---|
| **1** | **Connecteur natif « Custom MCP Server »** | L'app parle MCP directement à notre serveur. Les 17 outils deviennent des **actions** dans l'assistant. Aucun agent à écrire | [10-5](10-5-gemini-enterprise-connecteur-mcp-natif.md) |
| **2** | **Agent ADK qui utilise le serveur MCP** (A2A sur Cloud Run, ou Agent Runtime) | Un agent « Assistant Google Sheets » est ajouté à l'app (comme au projet 09). Il a ses consignes et appelle le serveur MCP avec le jeton de l'utilisateur | [10-6](10-6-agent-adk-mcp-gemini-enterprise.md) |
| **3** | **Serveur MCP Sheets officiel de Google** (`sheetsmcp.googleapis.com`) | Même branchement que le chemin 1, mais vers le serveur de Google : rien à héberger. **En preview**, sur inscription | [10-10](10-10-serveur-mcp-sheets-officiel-google.md) |
| **4** | **Agent Registry** | Le catalogue de l'entreprise : le serveur et ses outils y sont **déclarés** pour être trouvés et gouvernés. Les agents ADK peuvent le retrouver par son nom | [10-7](10-7-agent-registry-mcp.md) |

```
                         ┌──────────────── chemin 1 : connecteur natif (actions) ────────────────┐
 Utilisateur ─▶ App GE ──┤                                                                       ├─▶ sheets-mcp ─▶ Sheets
   (chat)    (projet app)└─ chemin 2 : agent « Assistant Google Sheets » (A2A / Agent Runtime) ─┘   (projet des agents)
                         └──────────── chemin 3 : sheetsmcp.googleapis.com (Google, preview) ───────────────────▶ Sheets
                                                    chemin 4 : Agent Registry = le catalogue (déclare sheets-mcp)
```

## 3. Lequel choisir ?

| Besoin | Chemin conseillé |
|---|---|
| « Je veux que l'assistant sache lire et modifier Sheets, sans écrire d'agent » | **1** (connecteur natif) |
| Un assistant **métier** avec ses consignes (« rapport de stock », « suivi des ventes »), qui combine Sheets avec d'autres outils, ou Model Armor | **2** (agent) |
| Ne rien héberger, accepter une preview et ses limites (6 outils, pas de recherche par nom) | **3** (officiel), quand vous êtes inscrits |
| Que les équipes **trouvent** le serveur et sachent ce qu'il fait (gouvernance) | **4**, en plus de 1 ou 2 |

Notre recommandation pour Acme :
- **Chemin 1** pour tout le monde. Activez d'abord les 6 outils de lecture, puis les écritures, une fois les usages
  observés.
- **Chemin 2** pour les assistants métier.
- **Chemin 4** dans tous les cas.

Les chemins 1 et 2 partagent **le même serveur** et **le même client OAuth**.

## 4. Les jetons : qui prouve quoi

À chaque appel au serveur MCP, **deux jetons** voyagent, avec deux rôles différents :

| En-tête | Contient | Vérifié par | Garantit |
|---|---|---|---|
| `X-Serverless-Authorization` | Jeton d'identité Google de **l'appelant** : le compte de l'app (chemin 1) ou le compte de l'agent (chemin 2) | **Cloud Run** (`roles/run.invoker`) | Seuls l'app et l'agent atteignent le serveur. Sans ce jeton : `403` |
| `Authorization: Bearer …` | **Jeton OAuth de l'utilisateur** | **Le serveur MCP** | Le jeton vient de **notre** client OAuth, avec la portée Sheets, et d'un compte e-mail vérifié du domaine autorisé |

Ensuite, le serveur appelle Google Sheets **avec le jeton de l'utilisateur**. Le compte du serveur n'a **aucun rôle**.

- **Chemin 1 :** Gemini Enterprise met lui-même les deux en-têtes pour une URL `*.run.app` (documentation Google).
- **Chemin 2 :** c'est l'agent qui les met. Son code (`header_provider`) ajoute son propre jeton d'identité, et
  transmet le jeton de l'utilisateur que l'app lui a confié.

## 5. Ce que contient ce dossier

```
10-mcp-google-sheets-gemini-enterprise/
├── mcp_server/              le serveur MCP (17 outils, vérification du jeton, journal d'audit) + Dockerfile
├── agent/                   l'agent ADK « Assistant Google Sheets » : sheets_agent/, main.py (A2A), carte.py
├── config/10-mcp.env        la configuration (projet, région, app, clients OAuth, domaines)
├── scripts/                 config.sh, deployer.sh (toutes les étapes), fiche.py, gen_toolspec.py, deployer_agent_runtime.py
├── terraform/               la même chose en Terraform (Cloud Build, Cloud Run, Agent Runtime, IAM, Agent Registry)
├── tests/                   test_server.py (simulé), test_reel.py, test_agent_chaine.py, appel_a2a.py, appel_runtime.py
└── docs/                    10-0 … 10-10 (ce guide et les suivants)
```

Repris et amélioré depuis `04-mcp-server-cloud-run-registry/sheets-mcp` (le serveur) et le projet 09 (A2A, Agent
Runtime, OAuth, Cloud Build sans Docker).

## 6. Ce qui a été vérifié, et ce qui reste à faire

**Vérifié en vrai** (13 et 14 octobre 2026). Deux projets de test : `second-project` (agents) et `main-project`
(app). Ils n'ont pas d'organisation et pas d'app Gemini Enterprise.

| Quoi | Résultat |
|---|---|
| Serveur MCP déployé sur **Cloud Run** (`deployer.sh mcp`, Cloud Build) | Construit en 39 s ; sans jeton : `403` ; avec les deux en-têtes du connecteur : **les 17 outils passent sur un vrai classeur** |
| Le même appel, fait par un compte **du projet de l'app** (simule le compte de Gemini Enterprise) | Sans droit : `403`. Avec le droit ① : les 17 outils passent. **Les droits d'un projet à l'autre marchent** |
| **Agent A2A** sur Cloud Run, **vrai Gemini**, appelé comme l'app | « Tente : 149 €, stock 30 » ; écriture **avec demande de confirmation** ; suppression d'onglet **avec demande de confirmation** ; sans jeton : « cliquez sur Autoriser » |
| **Agent sur Agent Runtime** (`deployer.sh agent-runtime`), appelé comme l'app (`authorizations`) | « Le stock du Vélo est de 12 » ; sans autorisation : « cliquez sur Autoriser ». Le jeton d'identité de l'agent est accepté par Cloud Run |
| **Agent Registry** (`deployer.sh registre`) | « Google Sheets (MCP) » enregistré, avec ses 17 outils et leurs annotations |
| `droits-app` (compte de l'app, d'un projet à l'autre) | ① sur les deux services, ② sur le projet : OK |
| Journal d'audit sur Cloud Run | `tool_call` : outil, plage, **e-mail de l'utilisateur** (jamais le contenu) |
| `nettoyer` | Tout supprimé : services, agent Agent Runtime, registre, rôles, comptes, dépôt |
| Terraform (`apply`, avec app et Agent Runtime) | Voir [10-3](10-3-deployer-terraform.md) |
| Serveur officiel de Google | 6 outils listés ; appels refusés sans inscription à la preview |

**Problèmes réels trouvés et corrigés en déployant** (ils n'apparaissaient pas en local) :
1. **Image de l'agent :** `McpToolset` ne s'importait pas, parce que `google-adk` n'installe pas le paquet `mcp`.
   Il est maintenant dans `agent/requirements.txt`.
2. **Agent Registry :** chaque outil doit avoir son `inputSchema`. `gen_toolspec.py` l'ajoute maintenant, en JSON
   compact, sous les 10 Ko.
3. **Terraform sur un projet neuf :** il faut l'API Cloud Resource Manager active **avant** Terraform. C'est une
   commande ([10-3, 2.1 bis](10-3-deployer-terraform.md#21-bis-une-commande-une-seule-fois-avant-terraform)), et le
   numéro du projet est maintenant donné et non plus lu.
4. **Locale fr_FR :** les formules utilisent `;` et `,` (10-1, partie 6).
5. **fastmcp 4.x :** le cache maison du serveur du dossier 04 était en conflit avec la bibliothèque. C'est corrigé.

**Ce qui ne se vérifie que chez Acme** (organisation et app) :
- les règles d'organisation ;
- le client OAuth « Interne » ;
- le connecteur dans l'app ;
- l'ajout de l'agent ;
- le premier « Autoriser ».

La liste exacte, projet par projet, est dans le [README](../README.md#sur-les-projets-acme--quoi-faire-où).

## 7. L'ordre des guides

| Guide | Pour |
|---|---|
| [10-1](10-1-serveur-mcp-comprendre-et-tester-en-local.md) | Comprendre le serveur, le lancer et le tester sur votre poste |
| [10-2](10-2-deployer-shell.md) | Tout déployer avec `deployer.sh` (le plus simple) |
| [10-3](10-3-deployer-terraform.md) | La même chose avec Terraform |
| [10-4](10-4-deployer-console.md) | La même chose dans la console, clic par clic |
| [10-5](10-5-gemini-enterprise-connecteur-mcp-natif.md) | **Chemin 1** : le client OAuth, les politiques, le connecteur « Custom MCP Server » |
| [10-6](10-6-agent-adk-mcp-gemini-enterprise.md) | **Chemin 2** : l'agent (A2A, Agent Runtime), son autorisation, l'ajout à l'app |
| [10-7](10-7-agent-registry-mcp.md) | **Chemin 4** : Agent Registry |
| [10-8](10-8-tester-simuler-verifier.md) | Tous les tests, et comment obtenir un jeton de test |
| [10-9](10-9-securite-exploitation-depannage.md) | Sécurité, journaux, révocation, coût, dépannage, suppression |
| [10-10](10-10-serveur-mcp-sheets-officiel-google.md) | **Chemin 3** : le serveur officiel de Google |
| [10-12](10-12-pas-a-pas-mcp-dans-assistant-principal.md) | **Le parcours complet du chemin 1** (MCP dans l'assistant principal), de zéro au premier usage, en 14 étapes |
| [10-13](10-13-serveur-mcp-google-slides.md) | **Google Slides** : le 2e serveur MCP (20 outils), même sécurité, même chemins |
| [10-14](10-14-un-serveur-a-la-fois.md) | **Un serveur à la fois** : Sheets seul, Slides seul, puis l'autre (script, Terraform, console) |
| [10-11](10-11-droits-voir-et-donner-console.md) | **Tous les droits** : les voir en lecture seule, les donner et les retirer dans la console, un par un |

## 8. Sources

- [Custom MCP Server dans Gemini Enterprise](https://docs.cloud.google.com/gemini/enterprise/docs/connectors/custom-mcp-server/set-up-custom-mcp-server)
- [Enregistrer des serveurs MCP dans Agent Registry](https://docs.cloud.google.com/agent-registry/register-mcp-servers)
- [ADK : configuration avancée des outils MCP (`header_provider`)](https://adk.dev/tools-custom/mcp-tools/advanced/)
- [Serveur MCP Google Sheets (officiel, preview)](https://developers.google.com/workspace/sheets/api/guides/configure-mcp-server)
- [Produits Google avec serveur MCP](https://docs.cloud.google.com/mcp/supported-products)
- [API Google Sheets v4](https://developers.google.com/sheets/api/reference/rest)
