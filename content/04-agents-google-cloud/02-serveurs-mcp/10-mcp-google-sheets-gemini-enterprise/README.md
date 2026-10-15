---
type: "course"
description: "Des serveurs MCP Google Sheets (17 outils) et Google Slides (20 outils) branchés à Gemini Enterprise : local, shell, Terraform, console."
tags: ["mcp", "google-sheets", "google-slides", "gemini-enterprise", "oauth"]
level: "advanced"
duration: "6h"
usecases: ["analyse-donnees"]
platforms: ["gemini-enterprise"]
date: "2026-10-15"
updated: "2026-10-15"
authors: ["Youcef"]
---
# Projet 10 : des serveurs MCP Google Sheets et Google Slides pour Gemini Enterprise

> **Nouveau : Google Slides.** Un 2e serveur MCP (20 outils), même sécurité, même image, même client OAuth :
> [10-13](docs/10-13-serveur-mcp-google-slides.md).

Un serveur **MCP** qui donne à Gemini Enterprise une interaction **native et complète** avec Google Sheets :
- rechercher un classeur par son nom, lire, chercher, écrire ;
- formules, ajout de lignes, onglets, mise en forme, tri ;
- **toute l'API Sheets**.

Il agit toujours **au nom de l'utilisateur connecté**, avec son propre compte Google (OAuth). Il est hébergé sur Cloud
Run (privé), et branché sur Gemini Enterprise de **trois façons** :

| # | Chemin | Guide |
|---|---|---|
| 1 | **Connecteur natif « Custom MCP Server »** : les 17 outils deviennent des actions de l'assistant | [10-5](docs/10-5-gemini-enterprise-connecteur-mcp-natif.md) |
| 2 | **Agent ADK « Assistant Google Sheets »** (A2A sur Cloud Run, ou Agent Runtime) qui utilise le serveur | [10-6](docs/10-6-agent-adk-mcp-gemini-enterprise.md) |
| 3 | **Serveur officiel de Google** (`sheetsmcp.googleapis.com`, preview) : comparaison et branchement | [10-10](docs/10-10-serveur-mcp-sheets-officiel-google.md) |
| + | **Agent Registry** : le serveur et ses outils dans le catalogue de l'organisation | [10-7](docs/10-7-agent-registry-mcp.md) |

> **Vous voulez juste mettre le MCP dans l'assistant principal de Gemini Enterprise ?** Suivez **un seul guide**, du
> début à la fin : [10-12 Pas à pas : le MCP dans l'assistant principal](docs/10-12-pas-a-pas-mcp-dans-assistant-principal.md)
> (14 étapes, avec ce qu'on doit voir à chaque fois et les messages tout prêts pour les admins).

Projets à connaître avant :
- [09](../09-agents-multi-projets-gemini-enterprise/README.md) : agents dans un projet, branchés sur l'app, OAuth ;
- [04](../04-mcp-server-cloud-run-registry/README.md) : MCP sur Cloud Run, Agent Registry.

---

## Les guides, dans l'ordre

| Guide | Contenu |
|---|---|
| [10-0 Exploration](docs/10-0-exploration-mcp-gemini-enterprise.md) | MCP en 2 minutes, les 4 chemins, lequel choisir, les deux jetons, ce qui a été vérifié |
| [10-1 Le serveur en local](docs/10-1-serveur-mcp-comprendre-et-tester-en-local.md) | Le code, les 17 outils, la sécurité, l'installation, les tests (résultats réels), le piège des formules fr_FR |
| [10-2 Script](docs/10-2-deployer-shell.md) | `deployer.sh` étape par étape : verifier, preparer, mcp, agent, agent-runtime, registre, fiche, droits-app, autorisation, ajouter-app, tester, nettoyer |
| [10-3 Terraform](docs/10-3-deployer-terraform.md) | La même chose en Terraform ; plans réels (24, 26 ou 28 ressources) |
| [10-4 Console](docs/10-4-deployer-console.md) | La même chose clic par clic (une seule commande : la construction de l'image) |
| [10-5 Connecteur natif](docs/10-5-gemini-enterprise-connecteur-mcp-natif.md) | Client OAuth, règles d'organisation, data store « Custom MCP Server », actions, premier usage |
| [10-6 Agent](docs/10-6-agent-adk-mcp-gemini-enterprise.md) | Pourquoi un agent, les deux jetons dans le code, déploiement, autorisation, ajout à l'app (script et console) |
| [10-7 Agent Registry](docs/10-7-agent-registry-mcp.md) | Déclarer le serveur et ses outils ; le retrouver depuis un agent |
| [10-8 Tests](docs/10-8-tester-simuler-verifier.md) | Tous les tests, comment obtenir un jeton de test, simuler l'app, résultats obtenus |
| [10-9 Sécurité et exploitation](docs/10-9-securite-exploitation-depannage.md) | Les protections, journaux, révocation, coût, dépannage, suppression |
| [10-10 Serveur officiel](docs/10-10-serveur-mcp-sheets-officiel-google.md) | `sheetsmcp.googleapis.com` : testé, comparé, comment le brancher |
| [10-11 Les droits](docs/10-11-droits-voir-et-donner-console.md) | Tous les droits sur une page : les **voir** en lecture seule (Cloud Run, IAM, Policy Troubleshooter), les **donner** et les retirer en clics |
| [10-12 Pas à pas, assistant principal](docs/10-12-pas-a-pas-mcp-dans-assistant-principal.md) | **Le parcours complet du chemin 1, de zéro au premier « Autoriser »**, en 14 étapes, pour tout le monde |
| [10-13 Google Slides](docs/10-13-serveur-mcp-google-slides.md) | **Le serveur MCP Slides** : 20 outils, tests réels, déploiement, connecteur (ce qui change par rapport à Sheets), agent Sheets + Slides, comparaison avec le serveur officiel |
| [10-14 Un serveur à la fois](docs/10-14-un-serveur-a-la-fois.md) | **Sheets seul, Slides seul, ou l'un puis l'autre** : par script, Terraform et console, et le test de chaque serveur séparément |
| [10-15 « À la 3S »](docs/10-15-deployer-stack-3s.md) | **Déployer par le pipeline** (GitHub Actions + Terraform, état GCS, sans clé), comme sur la 3S de Acme : dossier `stack-3s/`, socle partagé avec le 09, migration d'un état local |

## Chaque étape, par chaque méthode

| Étape | Script | Terraform | Console (clic par clic) |
|---|---|---|---|
| Vérifier vos droits, la facturation, les API (lecture seule) | `deployer.sh verifier` | – | [10-11, partie 2](docs/10-11-droits-voir-et-donner-console.md#2-voir-en-lecture-seule) |
| Activer les API | `preparer` | `google_project_service` | [10-4, étape 1](docs/10-4-deployer-console.md#étape-1--les-api) |
| Comptes de service et leurs rôles | `preparer` | `google_service_account`, `…iam_member` | [10-4, étape 2](docs/10-4-deployer-console.md#étape-2--les-comptes-de-service), [10-11, 3.1](docs/10-11-droits-voir-et-donner-console.md#31-a-et-c--les-rôles-des-comptes-du-projet-avant-de-déployer) |
| Client OAuth | – (pas d'API Google) | – | [10-5, étape 1](docs/10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-1--le-client-oauth-console-projet-des-agents) |
| Construire les images | `mcp`, `agent` | `terraform_data.image` | 1 commande `gcloud builds submit` : [10-4, étape 3](docs/10-4-deployer-console.md#étape-3--les-images-la-seule-commande) |
| Serveurs MCP Sheets et Slides (Cloud Run) | `mcp` (ou `mcp sheets`, `mcp slides`) | `google_cloud_run_v2_service.mcp["sheets"]`, `["slides"]` | [10-4, étape 4](docs/10-4-deployer-console.md#étape-4--le-serveur-mcp) (2 fois ; `PRODUIT=slides` pour Slides) |
| Agent A2A (Cloud Run) | `agent` | `google_cloud_run_v2_service.agent` | [10-4, étape 5](docs/10-4-deployer-console.md#étape-5--lagent-a2a) |
| Agent sur Agent Runtime | `agent-runtime` | `google_vertex_ai_reasoning_engine` | Script seulement (pas de téléversement de code dans la console), puis à voir dans la console |
| Droit de l'agent sur le serveur (D) | `agent` | `…service_iam_member.mcp` | [10-11, 3.2](docs/10-11-droits-voir-et-donner-console.md#32-d--lagent-peut-appeler-le-serveur-mcp) |
| Agent Registry | `registre` | `google_agent_registry_service` | [10-4, étape 8](docs/10-4-deployer-console.md#étape-8--agent-registry-facultatif) |
| Droits de l'app ①a, ①b, ② | `droits-app` | `…iam_member` (avec `NUM_APP`) | [10-11, 3.3 à 3.5](docs/10-11-droits-voir-et-donner-console.md#3-donner-en-clics) |
| Règles d'organisation | – | – | [10-5, étape 2](docs/10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-2--les-règles-de-lorganisation-admin) |
| Connecteur « Custom MCP Server » | – (pas d'API publique) | – | [10-5, étapes 4 à 6](docs/10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-4--le-data-store--custom-mcp-server--console-de-lapp) |
| Autorisation OAuth de l'agent | `autorisation` | – (le secret n'entre pas dans Terraform) | Pendant l'ajout : [10-6, partie 5](docs/10-6-agent-adk-mcp-gemini-enterprise.md#5-ajouter-lagent-dans-lapp) |
| Ajouter l'agent à l'app | `ajouter-app` | – | [10-6, partie 5](docs/10-6-agent-adk-mcp-gemini-enterprise.md#5-ajouter-lagent-dans-lapp) |
| Agent User pour les utilisateurs | – | – | [10-11, 3.6](docs/10-11-droits-voir-et-donner-console.md#36-e--les-utilisateurs-voient-lagent) |
| Tout ce qu'il faut saisir dans l'app | `fiche` | `terraform output` | – |
| Tester comme l'app | `tester` | – | Le chat ([10-5, étape 7](docs/10-5-gemini-enterprise-connecteur-mcp-natif.md#étape-7--le-premier-usage)) |
| Tout supprimer | `nettoyer` | `terraform destroy` | [10-11, partie 4](docs/10-11-droits-voir-et-donner-console.md#4-retirer), [10-9, partie 4](docs/10-9-securite-exploitation-depannage.md#4-tout-supprimer) |

## Démarrage rapide (script)

```bash
cd 10-mcp-google-sheets-gemini-enterprise
# 1. Client OAuth (console, 2 min) : docs/10-5 étape 1 ; son ID dans OAUTH_CLIENT_IDS de config/10-mcp.env
source scripts/config.sh config/10-mcp.env
./scripts/deployer.sh verifier        # lecture seule : facturation, API, vos droits
./scripts/deployer.sh preparer        # API + 3 comptes de service
./scripts/deployer.sh mcp             # le serveur MCP (Cloud Build + Cloud Run privé)
./scripts/deployer.sh agent           # l'agent A2A (facultatif) ; agent-runtime pour Agent Runtime
./scripts/deployer.sh registre        # Agent Registry (facultatif)
./scripts/deployer.sh fiche           # TOUT ce qu'il faut saisir dans Gemini Enterprise
```

## Sur les projets Acme : quoi faire, où

Les tests réels ont été faits sur deux projets **sans organisation et sans Gemini Enterprise** (`second-project` pour
les agents, `main-project` pour l'app ; `config/10-mcp-test.env`). Chez Acme, il y a une organisation et une app.
Voici, dans l'ordre, ce qu'il faut faire et dans quel projet. Les numéros renvoient aux guides.

| # | Quoi | Projet | Qui | Différence avec les projets de test |
|---|---|---|---|---|
| 1 | `config/10-mcp.env` : `PROJET=aiml-gemini-ent-exp-0zga`, `NUM_PROJET=433175138344`, `ALLOWED_DOMAINS=acme.example` | – | vous | Test : `config/10-mcp-test.env` |
| 2 | `./scripts/deployer.sh verifier` : vos droits (groupes compris) | agents | vous | Test : propriétaire. Chez Acme, les rôles peuvent manquer : la ligne `MANQUANT` dit lequel demander |
| 3 | **Client OAuth** : audience **Internal**, les 4 portées, les 2 URI de redirection, ID → `OAUTH_CLIENT_IDS` (10-5, étape 1) | agents | vous | Test : pas de client. Un compte de service jouait l'utilisateur (« Internal » n'existe pas sans organisation) |
| 4 | `preparer`, `mcp`, `agent` (et/ou `agent-runtime`), `registre` (10-2) | agents | vous | Identique : testé en vrai |
| 5 | **Règles d'organisation** : « Disable custom MCP server connector » sur Off, domaines de sortie (`sheets-mcp-433175138344.europe-west1.run.app`, `accounts.google.com`, `oauth2.googleapis.com`), `custom_mcp` si la règle est appliquée (10-5, étape 2) | **app** | admin org (`roles/orgpolicy.policyAdmin`) | **N'existe pas** sur les projets de test (pas d'organisation) |
| 6 | `NUM_APP=523307489860 ./scripts/deployer.sh droits-app` : ① `run.invoker` sur `sheets-mcp` et `sheets-agent`, ② `discoveryengine.serviceAgent` (10-5, étape 3) | agents | vous | Identique : testé en vrai, d'un projet à l'autre |
| 7 | Connecteur : app → section **MCP servers** → **Custom MCP Server** → **Add MCP server** ; champs : `./scripts/deployer.sh fiche` (10-5, étapes 4 à 6) | **app** | admin de l'app | Test : pas d'app. Écran vérifié sur **tes captures Acme** |
| 8 | Agent : `autorisation` + `ajouter-app`, ou la console (10-6, parties 4 et 5) ; **Agent User** pour le groupe | **app** | admin de l'app | Test : simulé avec les mêmes appels que l'app |
| 9 | L'admin Google Workspace autorise l'ID client si l'accès des applications tierces est restreint (10-9, partie 2) | Workspace | admin Workspace | N'existe pas sur les projets de test |
| 10 | Premier usage : « Pour Google Sheets, qui suis-je ? » → **Autoriser** → votre e-mail @acme.example (10-5, étape 7) | le chat | chaque utilisateur | Test : jeton du compte de test |

**Ce qui est identique et déjà prouvé :** le code, le déploiement (script et Terraform), les droits d'un projet à
l'autre, les deux en-têtes, le contrôle du jeton et le journal d'audit. **Ce qui ne peut se vérifier que chez
Acme :** les étapes 5, 7, 8, 9 et 10 (organisation, app, consentement réel).

## Fichiers

```
mcp_server/               les serveurs : noyau.py (jeton, appels Google, audit), outils_sheets.py (17 outils),
                          outils_slides.py (20 outils), main.py (PRODUIT=sheets|slides) ; fastmcp 4.1
agent/                    l'agent ADK : sheets_agent/agent.py (McpToolset + header_provider), main.py (A2A), carte.py
cloudbuild.yaml           construction des images dans Google Cloud (pas de Docker sur le poste)
config/10-mcp.env         la configuration
scripts/                  config.sh, deployer.sh, fiche.py, gen_toolspec.py, deployer_agent_runtime.py, pack.py
terraform/                main.tf, variables.tf, outputs.tf, versions.tf, toolspec-sheets.json, toolspec-slides.json
tests/                    test_server.py, test_reel.py, test_reel_slides.py, test_agent_chaine.py, appel_a2a.py, appel_runtime.py
```

## État des vérifications (14 octobre 2026)

**Vérifié en vrai, sur Google Cloud :**
- le serveur MCP sur Cloud Run : 17 outils sur un vrai classeur, `403` sans droit ;
- les appels venant du projet de l'app (droit ①) ;
- l'agent A2A **et** l'agent Agent Runtime avec le vrai Gemini : lecture, écriture avec confirmation, suppression
  avec confirmation, message « Autoriser » ;
- Agent Registry (17 outils) ;
- `droits-app`, `nettoyer` ;
- Terraform ;
- le journal d'audit.

- **Google Slides** : les 20 outils sur une vraie présentation, en local et sur Cloud Run ; ajout à un déploiement
  Sheets existant par Terraform, sans rien détruire ; Slides seul (script et `tester`) ; l'agent qui lit un classeur
  puis construit une diapositive (vrai Gemini).

9 problèmes réels ont été trouvés et corrigés : [10-0, partie 6](docs/10-0-exploration-mcp-gemini-enterprise.md#6-ce-qui-a-été-vérifié-et-ce-qui-reste-à-faire) (5) et [10-13](docs/10-13-serveur-mcp-google-slides.md) (4 : le `Dockerfile` ne copiait que `main.py` ; un commentaire en fin de ligne dans le `Dockerfile` ; deux outils de même nom dans l'agent ; des droits Sheets que Terraform aurait recréés au lieu de les garder).

**Ce qui ne se vérifie que chez Acme :** l'organisation et l'app. Voir la section précédente.
