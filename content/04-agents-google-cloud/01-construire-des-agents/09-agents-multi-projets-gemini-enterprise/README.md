---
type: "course"
description: "Les 6 façons d'ajouter un agent à Gemini Enterprise, des agents d'autres projets GCP, un orchestrateur qui découvre et appelle les autres."
tags: ["gemini-enterprise", "a2a", "agent-registry", "multi-projets", "oauth"]
level: "advanced"
duration: "6h"
usecases: ["assistant-interne", "automatisation-processus"]
platforms: ["gemini-enterprise", "vertex-ai"]
date: "2026-10-15"
updated: "2026-10-15"
authors: ["Youcef"]
references:
  - title: "Ajouter un agent ADK"
    url: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent
  - title: "Accès cross-project"
    url: https://docs.cloud.google.com/gemini/enterprise/docs/configure-cross-project-adk-agents
  - title: "Ajouter un agent A2A"
    url: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent
  - title: "Importer depuis Agent Registry"
    url: https://docs.cloud.google.com/gemini/enterprise/docs/import-govern-agent-registry
  - title: "Agent Registry, concepts"
    url: https://docs.cloud.google.com/agent-registry/concepts
---
# Projet 09 : ajouter des agents à Gemini Enterprise et les faire collaborer, entre projets GCP

**Pour qui :** équipes qui construisent des agents (développeurs, DevOps), administrateurs Gemini Enterprise, sécurité.
**Les questions reçues, et les réponses de ce projet :**

| Question | Réponse courte | Où |
|---|---|---|
| Quelles sont les **façons d'ajouter** un agent, et laquelle choisir ? | 6 façons : Agent Designer (sans code), ADK sur Agent Runtime, A2A, import depuis Agent Registry, Dialogflow, Marketplace. Par défaut : ADK sur Agent Runtime | [docs/01](docs/01-comprendre-et-choisir.md) |
| Un agent **dans le même projet** que l'app : comment le créer, l'ajouter, le tester ? | Le cas le plus simple : **aucun droit à donner** pour un agent Agent Runtime. Tutoriel complet de 45 min, avec plan de test | [docs/02](docs/02-tuto-meme-projet.md) |
| Un agent dans **un autre projet GCP** ? | Ça marche. Le projet de l'agent donne **1 rôle** au compte de Gemini Enterprise. 3 méthodes : Agent Runtime, Cloud Run + A2A, Agent Registry + Agent Gateway | [docs/03](docs/03-tuto-autre-projet.md) |
| ⭐ Une équipe a déjà son agent **dans son Agent Registry** : comment l'ajouter à notre stack ? | On lit l'entrée du registre (`scripts/registry.py` dit comment l'ajouter), puis 3 voies : **nom de ressource**, **carte A2A**, ou **déclaration dans notre registre + Agent Gateway**. Le jour même pour les voies 1 et 2 | [docs/04](docs/04-agents-deja-dans-un-registry.md) |
| **Qui donne quel droit** à qui, et quelles régions ? | Le droit est toujours donné **par le projet de la ressource appelée**. Matrice unique, régions, VPC-SC, diagnostic des refus | [docs/05](docs/05-droits-et-regions.md) |
| Un agent qui **appelle un autre agent** (Vertex AI / Agent Runtime) ? | Il le **trouve** dans Agent Registry, puis l'**appelle**. Son identité reçoit un droit **sur cet agent seulement** | [docs/06](docs/06-appels-entre-agents.md), code `agents/orchestrator` |
| ⭐ Comment construire de **vrais agents** (outils) et les mettre dans Gemini Enterprise **en code**, sur **Cloud Run (A2A)** ou **Agent Runtime**, même projet ou autre projet ? | 6 agents prêts (météo réelle, rédaction, traduction, taille, retours, identité), 2 hébergements, tout en Terraform, testé à chaque étape | [docs/08](docs/08-tuto-trio-pas-a-pas.md), [01-bis](01-bis-cloud-run-a2a/README.md), [02-bis](02-bis-agent-runtime/README.md) |
| ⭐ Dans **Ajouter un agent**, que veut dire chaque mode ? Une équipe a son agent dans **son** projet : comment le **connecter à notre app**, pas à pas ? | 5 modes expliqués champ par champ ; procédure en 7 étapes (admin / équipe), commandes, **simulateur** pour prouver l'accès avant l'ajout, fiche de demande. Testé entre deux vrais projets | [docs/09](docs/09-connecter-a-gemini-enterprise.md) |
| ⭐⭐⭐ **Mes deux projets** : agents dans `aiml-gemini-ent-exp-0zga` → app de `acme-gemini-prod` (12-1), ou tout dans `acme-gemini-prod` avec Agent Registry et Dialogflow (12-2). Trois méthodes (shell, Terraform, console), chacune de bout en bout | Un fichier de configuration par scénario (`config/`), chargé par `source scripts/config.sh …` ; pages interactives `parcours-12-1.html` (parcours guidé 12-1-1 → 12-1-7, exercice pas à pas) et `parcours-12.html` | [docs/12-1](docs/12-1-agents-projet-exp-vers-app.md), [docs/12-2](docs/12-2-agents-dans-projet-app.md) |
| ⭐⭐⭐ **Ajouter des agents un par un** (un service Cloud Run et une entrée dans l'app par agent), utiliser les sources de l'app, outils avec le compte de l'utilisateur (OAuth) | `scripts/nouvel_agent.py`, `scripts/autorisation_oauth.sh`, `AGENTS_OAUTH` dans la configuration | [docs/12-3](docs/12-3-ajouter-des-agents-un-par-un.md) |
| ⭐⭐ **Chez Acme** : mes projets existent déjà ; je crée des agents dans un projet et je les utilise dans l'app `aiml-gemini-entreprise-ldbr` | Pas à pas depuis le poste (`~/Desktop`), droits et API vérifiés, comptes de service, 3 façons de publier, les 5 modes d'ajout | [docs/11](docs/11-acme-agents-vers-app-gemini-enterprise.md) |
| ⭐ Je veux **rejouer tout le flux** moi-même (projet X puis projet A, tests, appels entre projets) en voyant **le résultat attendu de chaque commande** | Guide Markdown commande par commande, sorties réelles commentées, problèmes rencontrés et solutions | [docs/10](docs/10-rejouer-le-flux-complet.md) |
| Un **utilisateur** peut-il ajouter un agent **lui-même**, depuis l'app web ? | Il **crée** des agents sans code et **réutilise** ceux déjà publiés. **Connecter** un agent externe passe par un admin ou un **builder délégué** (rôle *Agent Admin*) | [docs/07](docs/07-autonomie-utilisateurs.md) |

---

> **Première fois ?** Suivez les tutoriels **100 % console**, sans Terraform, dans l'ordre :
> [02 – même projet](docs/02-tuto-meme-projet.md) (le plus simple), puis [03 – autre projet](docs/03-tuto-autre-projet.md).

> **En code, avec de vrais agents ?** [docs/08](docs/08-tuto-trio-pas-a-pas.md) puis [01-bis (Cloud Run + A2A)](01-bis-cloud-run-a2a/README.md)
> ou [02-bis (Agent Runtime)](02-bis-agent-runtime/README.md). Version PDF : `Gemini-Enterprise-Agents-Tutoriel-Pas-a-Pas.pdf`.

> **Pour les PM et l'équipe RH** (sans technique) : `Gemini-Enterprise-Agents-Guide-Equipes.pdf` et `.pptx` à la racine du dossier.

> **Deux sites HTML interactifs (EN/FR), à ouvrir dans un navigateur ou à publier sur l'intranet :**
> - `guide-interactif.html` : **manuel interne** (admin Gemini Enterprise, développeurs, RH) : mise en place du projet de l'app
>   `aiml-gemini-entreprise-ldbr`, déploiement pas à pas, Terraform exécuté **en local** et ses règles, ajout d'un nouvel agent,
>   traitement des demandes partenaires, FAQ ;
> - `portail-agents-partenaires.html` : **portail des équipes et partenaires** qui veulent connecter leur agent à notre
>   Gemini Enterprise depuis leur projet : modes, comptes de service, sécurité, test, formulaire de demande, FAQ.
>
> Avant diffusion, compléter le bloc `var CONFIG` en bas de chaque fichier (numéro du projet, ID de l'app, contact).

## 1. Ce que le projet déploie (et teste)

```
 Projet AGENTS (équipe Supply)                         Projet GEMINI ENTERPRISE (équipe Magasins)
┌────────────────────────────────────┐               ┌──────────────────────────────────────────────┐
│ Agent Runtime : "stock-agent"      │◀── appel ─────│ Agent Runtime : "assistant-magasin"          │
│  (ADK, identité stock-agent-sa,    │   (2) API     │  (ADK, identité assistant-magasin-sa)        │
│   Model Armor)                     │   Agent       │   outil ask_stock_agent                      │
│        │ enregistrement auto       │   Runtime     │        │                                     │
│        ▼                           │               │        │ (1) découverte                      │
│ Agent Registry (europe-west1) ◀────┼───────────────┼────────┘                                     │
│                                    │               │                                              │
│ IAM accordé par CE projet :        │               │ App Gemini Enterprise (eu)                   │
│  • aiplatform.viewer SUR stock-agent ─▶ assistant-magasin-sa     ├─ "Assistant magasin"             │
│  • agentregistry.viewer ─────────────▶ assistant-magasin-sa     └─ "Stock magasin (Supply)" ◀─ ajout │
│  • discoveryengine.serviceAgent ─────▶ compte de Gemini Enterprise              cross-project    │
└────────────────────────────────────┘               └──────────────────────────────────────────────┘
```

Trois scénarios réels, couverts par le même code :
1. **Ajout cross-project** : l'agent de l'équipe Supply apparaît dans l'app Gemini Enterprise de l'équipe Magasins.
2. **Agent qui appelle un agent** : l'assistant magasin délègue le stock à l'agent Supply.
3. **Découverte par le registre** : aucun identifiant en dur. Si Supply redéploie son agent, l'orchestrateur le retrouve.

Pour un essai, les deux projets peuvent être **le même** (`agents_project_id = ge_project_id`).

---

## 2. Le contenu

```
09-agents-multi-projets-gemini-enterprise/
├── README.md
├── docs/                                lire dans l'ordre ; chaque sujet n'est traité qu'à un seul endroit
│   ├── 01-comprendre-et-choisir.md      les 6 façons d'ajouter un agent, comment choisir, même projet ou autre projet
│   ├── 02-tuto-meme-projet.md           TUTORIEL : agent simple dans le projet de l'app → ajout → test (étapes de référence)
│   ├── 03-tuto-autre-projet.md          TUTORIEL : agent dans un autre projet ; Cloud Run + A2A ; Agent Registry + Gateway
│   ├── 04-agents-deja-dans-un-registry.md ⭐ agent déjà dans le registre d'une équipe → notre stack (3 voies, modèle de demande)
│   ├── 05-droits-et-regions.md          matrice unique des droits, régions, VPC-SC, diagnostic des refus
│   ├── 06-appels-entre-agents.md        un agent qui appelle un autre agent : 3 modèles, code, choix
│   ├── 07-autonomie-utilisateurs.md     ce que l'utilisateur fait seul, le « builder délégué », l'admin
│   ├── 08-tuto-trio-pas-a-pas.md        TUTORIEL EN CODE : 3 agents, prérequis, test local, choix de l'hébergement
│   ├── 09-connecter-a-gemini-enterprise.md  ⭐ les modes « Ajouter un agent », pas à pas entre projets, simulateur
│   ├── 10-rejouer-le-flux-complet.md    TOUT le flux, commande par commande, avec les sorties réelles commentées
│   ├── 11-acme-agents-vers-app-gemini-enterprise.md  projets existants, poste local, les 5 modes (version générale)
│   ├── 12-1-1-deployer-agents-shell.md      ⭐ déployer seulement les agents (un, plusieurs, tous), commandes
│   ├── 12-1-2-deployer-agents-terraform.md  ⭐ idem avec Terraform (ligne AGENTS, for_each expliqué)
│   ├── 12-1-3-deployer-agents-console.md    ⭐ idem dans la console Google Cloud
│   ├── 12-1-4-connecter-agents-app-gemini-enterprise.md  ⭐ connecter les agents à l'app : valeurs, droits, ajout, retour arrière
│   ├── 12-1-5-simuler-appel-gemini-enterprise.md         ⭐ simuler l'appel de l'app (refusé / accepté / OAuth) avant la production
│   ├── 12-1-6-ajouter-agent-console-gemini-enterprise.md ⭐ côté console Gemini Enterprise, clic par clic
│   ├── 12-1-7-agents-oauth-identite-outils.md            ⭐ OAuth (« Autoriser »), identité, outils de l'app, nouveautés
│   ├── 12-1-8-agent-espace-de-travail-multi-oauth.md     ⭐ Agent Gmail, Agenda, Drive, Sheets (sans suppression) ; un ou plusieurs fournisseurs OAuth (Google + Atlassian)
│   ├── 12-1-9-deployer-agents-stack-3s.md               ⭐ « à la 3S » Acme : GitHub Actions + Terraform (état GCS, WIF sans clé), PR puis merge
│   ├── 12-1-agents-projet-exp-vers-app.md   ⭐ agents dans aiml-gemini-ent-exp-0zga → app de acme-gemini-prod, 3 méthodes
│   ├── 12-2-agents-dans-projet-app.md       ⭐ tout dans acme-gemini-prod : Agent Runtime, A2A, Agent Registry, Dialogflow
│   └── 12-3-ajouter-des-agents-un-par-un.md ⭐ un service et une entrée d'app par agent ; sources de l'app ; OAuth
├── .gcloudignore                        ce que Cloud Build reçoit pour construire une image : seulement le code des agents
├── config/                              ⭐ 12-1-…env, 12-2-…env : vos projets, le seul fichier à modifier
├── gemini-enterprise-agents-acme-en-fr.html  ⭐⭐⭐ La même page, en anglais (par défaut) et en français, onglets sans défilement horizontal
├── gemini-enterprise-agents-acme.html    ⭐⭐⭐ LA page à présenter : déployer, connecter, OAuth, plusieurs fournisseurs, expérience, sécurité, dépannage, parcours à cocher (vos valeurs remplissent les commandes)
├── parcours-12-1.html                   ⭐⭐ LE parcours 12-1 guidé : vos valeurs → fichier de configuration, comprendre, les guides 12-1-1 à 12-1-7 en onglets, exercice final pas à pas (cases « vérifié »)
├── parcours-12.html                     ⭐ page interactive des parcours 12-1 / 12-2, méthodes A / B / C
├── 04-bis-dialogflow/                   agent Dialogflow CX (Terraform) + test.sh
├── 01-bis-cloud-run-a2a/                les agents du trio sur Cloud Run en A2A, une image par agent construite dans Google Cloud, sans Docker (Dockerfile, cloudbuild.yaml, main.py, terraform/, test.sh, README pas à pas)
├── 03-bis-stack-3s/                    les agents du 01-bis déployés par un pipeline « à la 3S » : socle (bucket d'état, compte de déploiement, WIF GitHub), deploy/ (01-bis en module), workflow GitHub Actions
├── 02-bis-agent-runtime/                les agents du trio sur Agent Runtime (terraform/, test.sh, README pas à pas)
├── agents/
│   ├── trio/                            météo réelle, rédaction, traduction, taille, retours, identité (catalogue.json ; code partagé par 01-bis et 02-bis)
│   ├── meme_projet/conges_agent/        agent du tutoriel 02 (règles de congés)
│   ├── specialist/stock_agent/          agent de l'équipe Supply (projet agents)
│   └── orchestrator/orchestrator_agent/ agent de l'équipe Magasins : découvre et appelle le spécialiste
├── terraform/
│   ├── modules/adk_agent/               un agent Agent Runtime + son identité (stock, orchestrateur, trio)
│   ├── modules/armor_templates/         une paire de templates Model Armor (01-bis, 02-bis, si pas ceux du projet 08)
│   ├── 10_specialist.tf                 projet agents
│   ├── 20_orchestrator.tf               projet GE + les 2 droits cross-project
│   ├── 30_gemini_enterprise.tf          publication dans l'app (+ agents d'autres équipes)
│   └── terraform.tfvars.example
└── scripts/                             ⭐ README.md : la carte de tous les scripts (à quoi sert chacun, quand, exemple) ; chaque script a un en-tête détaillé
    ├── add_agent_to_ge.sh               ajouter à l'app N'IMPORTE QUEL agent existant (ADK ou A2A, tout projet)
    ├── registry.py                      explorer l'Agent Registry d'un projet (et dire comment ajouter chaque agent)
    ├── query.py                         appeler un agent Agent Runtime (preuve des droits)
    ├── test_agents.py                   tests hors ligne (5 scénarios)
    ├── test_trio.py                     tests hors ligne des 6 agents du trio (9 scénarios)
    ├── simuler_gemini_enterprise.sh     prouve qu'un agent (A2A ou Agent Runtime) est joignable avec les droits de Gemini Enterprise
    ├── config.sh                        charge config/*.env (gcloud, scripts, Terraform via TF_VAR_*)
    ├── verifier_api.sh                  vérifie les API, active seulement celles qui manquent
    ├── deployer_agent_runtime.py        déploie / supprime un agent Agent Runtime sans Terraform (méthode shell)
    ├── carte_a2a.py                     carte A2A et variables d'un service Cloud Run (méthode shell)
    ├── nouvel_agent.py                  crée le squelette d'un nouvel agent du trio (docs/12-3)
    ├── autorisation_oauth.sh            crée / liste / supprime une autorisation OAuth de l'app (docs/12-3)
    ├── deployer_shell.sh                méthode shell sans rien taper : preparer / cloudrun / runtime / registre / tester, agents lus dans AGENTS (docs/12-1-1)
    ├── connecter_app.sh                 connecter les agents à l'app : apps / verifier / droits / ajouter / lister / retirer, avec confirmation (docs/12-1-4)
    ├── nettoyer.py                      inventaire du projet des agents, et nettoyage après confirmation (Cloud Run, Agent Runtime, registre, Dialogflow, comptes…)
    ├── autoriser_passerelle.sh          droit de passage iap.egressor sur une entrée du registre (mode Agent Registry)
    ├── build_pdf.py, build_pptx.js      génèrent le guide PM / RH (PDF + PPTX) à la racine
    ├── build_pdf_tuto.py                génère le tutoriel pas à pas (PDF) à la racine
    └── pack.py, register_agent.sh       utilisés par Terraform (register_agent.sh : agents ADK et A2A)
```

---

## 3. Démarrage rapide

**Prérequis :** une app Gemini Enterprise (projets 06/08) et ses templates Model Armor ; `gcloud auth login` et
`gcloud auth application-default login` ; dans chaque projet, `gcloud services enable cloudresourcemanager.googleapis.com
serviceusage.googleapis.com` (Terraform en a besoin avant tout le reste). **Pas besoin de Docker** : les images
Cloud Run sont construites dans Google Cloud (Cloud Build) ; gcloud, Terraform et Python suffisent (ou Cloud Shell).

```bash
# 0. Tests hors ligne (aucun appel Google)
uv venv -p '>=3.12' .venv && source .venv/bin/activate
uv pip install -r agents/orchestrator/requirements.txt
python scripts/test_agents.py                       # -> tests agents OK (5 scénarios)

# 1. Déployer
cd terraform && cp terraform.tfvars.example terraform.tfvars    # 2 projets, app, templates
terraform init && terraform plan && terraform apply             # 10 à 20 min (2 agents)

# 2. Prouver l'appel inter-agents, cross-project
cd .. && python scripts/query.py orchestrator "Il reste des tentes 8771234 à Lyon ?"
#   -> outil : ask_stock_agent(...)   agent : ... 0 à Lyon, 12 à Lille ...

# 3. Voir ce que le registre de l'équipe Supply expose
python scripts/registry.py acme-agents-supply europe-west1

# 4. Dans Gemini Enterprise : app -> Agents -> "Assistant magasin" et "Stock magasin (Supply)"
#    -> onglet Autorisations utilisateur : donner le rôle Agent User au groupe concerné.
```

**Ajouter l'agent d'une autre équipe, à la main** (pour un essai) **ou par PR** (en production) :

```bash
export GE_PROJECT=acme-ge-recette GE_APP=acme-ge GE_LOCATION=eu
./scripts/add_agent_to_ge.sh adk projects/acme-pricing/locations/europe-west1/reasoningEngines/123 "Prix et promotions"
./scripts/add_agent_to_ge.sh a2a https://pricing-agent-xyz.a.run.app/.well-known/agent-card.json "Prix (A2A)"
./scripts/add_agent_to_ge.sh list
```

En production, on passe par Terraform (`external_adk_agents` dans `terraform.tfvars`) : une PR par agent, relue par la sécurité.

---

## 4. Le processus proposé pour les équipes

| Étape | Qui | Quoi |
|---|---|---|
| 1 | Équipe qui publie | Déploie son agent sur **Agent Runtime** dans **son** projet, avec Model Armor et une identité dédiée (modèle `agents/specialist`). Il s'enregistre seul dans **son** Agent Registry |
| 2 | Équipe qui publie | Ouvre une **PR** sur ce dépôt : une entrée dans `external_adk_agents` (nom de ressource, nom affiché, description) |
| 3 | Sécurité | Relit : Model Armor présent ? identité dédiée ? actions d'écriture avec confirmation humaine ? données accédées ? |
| 4 | CI | `terraform apply` : droit cross-project + publication dans l'app |
| 5 | Admin Gemini Enterprise | Donne le rôle **Agent User** aux bons groupes (onglet *Autorisations utilisateur* de l'agent) |

Pour un agent qui en appelle un autre : même circuit, avec en plus **un** droit sur l'agent appelé
(`google_vertex_ai_reasoning_engine_iam_member`), accordé **par l'équipe propriétaire** de l'agent appelé.

---

## 5. Vérifié / à valider

**Vérifié :** `terraform validate` OK (provider google 8.5). Types et champs contrôlés dans le schéma du provider. Rôles
contrôlés dans IAM (`roles/aiplatform.viewer` contient `reasoningEngines.query` ; `roles/discoveryengine.serviceAgent`
existe). API ADK `AgentRegistry` contrôlée dans le paquet installé (`list_agents`, `search_agents`, `get_remote_a2a_agent`).
Tests hors ligne au vert. Règles Google relues dans la documentation (octobre 2026). **Pas encore déployé** sur un projet Acme.
`terraform plan` lancé sur un projet réel pour 01-bis et 02-bis : il a révélé (et on a corrigé) un défaut du module
`adk_agent`, qui lisait son projet via une source de données différée par `depends_on` (`project` inconnu au plan).
Le module reçoit maintenant `project` explicitement.

**01-bis et 02-bis déployés de bout en bout sur un vrai projet** (agents, Agent Registry, Model Armor, tests A2A et
Agent Runtime), puis supprimés. Ce déploiement a corrigé 5 défauts, dont 3 dans le code commun de ce projet :
module `adk_agent` (sortie `name` incomplète, `destroy` impossible après usage), orchestrateur (client Agent Platform
détruit avant l'appel). Détail : [docs/08 §6](docs/08-tuto-trio-pas-a-pas.md#6-ce-qui-est-vérifié).

| À valider au premier déploiement | Repli |
|---|---|
| ~~Nom affiché dans Agent Registry = `display_name` ; registre de la région de l'agent~~ | **Confirmé** au déploiement de 02-bis (`meteo-agent` dans `europe-west1`) |
| `aiplatform.viewer` posé **sur l'agent** suffit pour créer une session et l'interroger | Donner `roles/aiplatform.user` sur l'agent |
| Import depuis Agent Registry quand le registre est dans **un autre projet** que l'Agent Gateway | Ajout par nom de ressource (ADK) ou par carte (A2A), qui fonctionnent en cross-project |

Sources : [Ajouter un agent ADK](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent) ·
[Accès cross-project](https://docs.cloud.google.com/gemini/enterprise/docs/configure-cross-project-adk-agents) ·
[Ajouter un agent A2A](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent) ·
[Importer depuis Agent Registry](https://docs.cloud.google.com/gemini/enterprise/docs/import-govern-agent-registry) ·
[Agent Registry, concepts](https://docs.cloud.google.com/agent-registry/concepts)


## Supports

![Gemini Enterprise Agents Guide Equipes](./Gemini-Enterprise-Agents-Guide-Equipes.pdf)

![Gemini Enterprise Agents Tutoriel Pas a Pas](./Gemini-Enterprise-Agents-Tutoriel-Pas-a-Pas.pdf)
