---
type: "course"
description: "Une note de sécurité d'entreprise appliquée : console d'abord, puis Terraform par paliers, plan de tests et exploitation quotidienne."
tags: ["gemini-enterprise", "securite", "conformite", "siem", "vpc-sc", "terraform"]
level: "advanced"
duration: "6h"
usecases: ["assistant-interne"]
platforms: ["gemini-enterprise"]
date: "2026-10-05"
updated: "2026-10-14"
authors: ["Youcef"]
---
# Projet 08 : Gemini Enterprise conforme à la note de sécurité Acme

**Pour qui :** toute l'équipe projet. Développeurs, DevOps / plateforme, chefs de projet, sécurité, DPO.
**Objectif :** appliquer les **10 mesures** de la *Security Advice Note* Acme à l'application Gemini Enterprise.
D'abord avec ce que Google Cloud offre **nativement** (console, quelques clics, effet immédiat), puis en
**Terraform** (reproductible, relu, auditable).

> Ce projet part du **projet 06** (le socle : identité, CMEK, connecteurs, Model Armor, journaux). Le socle reste
> valable et il est documenté dans [docs/00-socle-securite.md](docs/00-socle-securite.md). Ce README ne décrit
> que **ce qui change pour la note** et **comment procéder**.

---

## Sommaire

1. [En une page](#1-en-une-page)
2. [Qui fait quoi](#2-qui-fait-quoi)
3. [Les 10 mesures et notre réponse](#3-les-10-mesures-et-notre-réponse)
4. [Comment procéder : 4 phases](#4-comment-procéder--4-phases)
5. [Ce que le projet contient](#5-ce-que-le-projet-contient)
6. [Démarrage rapide](#6-démarrage-rapide)
7. [Pourquoi d'abord la console, puis Terraform ?](#7-pourquoi-dabord-la-console-puis-terraform-)
8. [Corrections à apporter à la note](#8-corrections-à-apporter-à-la-note)
9. [Vérifié / à valider](#9-vérifié--à-valider)
10. [Documentation détaillée](#10-documentation-détaillée)

---

## 1. En une page

**Le constat.** La note Acme fixe 10 mesures pour l'IA générative. Le socle 06 en couvrait le cœur
(Model Armor, audit, identité). Il manquait la protection des **agents personnalisés**, la lutte contre le
**Shadow AI**, l'export **SIEM**, **Access Approval**, l'analyse des documents **avant indexation**, le
contrôle de **sortie**, le **niveau d'accès VPC-SC** et l'usage réel d'**Agent Registry**.

**Ce que fait le projet 08.**

| Ajout | Mesure | Comment |
|---|---|---|
| Model Armor sur **tous** les appels Gemini du projet, agents compris | §1, §3 | Plancher Model Armor étendu à *Agent Platform* (`AI_PLATFORM`), en observation puis en blocage |
| Agent exemple sur **Agent Runtime** : identité dédiée, Model Armor, **validation humaine** des actions | §1, §9 | `agent/` + `90_agents_registry.tf` |
| **Shadow AI** : empêcher (politiques d'org), détecter (alerte), inventorier (script) | §2 | `75_shadow_ai.tf` + `scripts/shadow_ai_inventory.sh` |
| Journaux `aiplatform` + `agentregistry`, **export SIEM**, **Access Approval** | §4 | `70_detection.tf`, `85_siem_access.tf` |
| **Secure Web Proxy** (option) pour les agents qui sortent par le VPC | §5 | `95_secure_web_proxy.tf` |
| **Analyse Model Armor des documents avant indexation** (quarantaine) | §6 | `scripts/scan_before_ingest.py` |
| VPC-SC : `aiplatform` et `agentregistry` dans le périmètre, **niveau d'accès** IP Acme | §7 | `60_advanced.tf` |
| Agent Registry : catalogue officiel, droits lecture / publication | §10 | `90_agents_registry.tf` |
| **Journal quotidien** et **contrôle de conformité** automatiques | exploitation | `scripts/daily_report.sh`, `scripts/verify_controls.sh` |

**Le principe.** Chaque mesure est d'abord **activée dans la console** (phase 1) pour voir son effet sur des
cas réels. Elle est ensuite **reprise dans Terraform** (phase 2), qui devient la seule source de vérité.
Rien n'est construit « à côté » de Google : chaque brique est un service Google Cloud natif.

---

## 2. Qui fait quoi

| Rôle | Ce qu'il fait dans ce projet | À lire en priorité |
|---|---|---|
| **Chef de projet / PM** | Planifie les 4 phases, obtient les décisions (DPO, SOC, identité), suit le tableau de conformité | §1, §3, §4, [docs/05](docs/05-correspondance-note.md) |
| **Sécurité (RSSI, SOC)** | Possède Model Armor, les clés, les journaux ; valide chaque PR sur les garde-fous ; reçoit les alertes et le flux SIEM | §3, §8, [docs/03](docs/03-plan-de-tests.md), [docs/04](docs/04-exploitation-journaliere.md) |
| **DevOps / plateforme** | Active la phase 1, écrit et applique la phase 2 via la CI Terraform, importe ce qui a été créé en console | [docs/01](docs/01-phase1-console.md), [docs/phase2-terraform/](docs/phase2-terraform/README.md) |
| **Développeurs d'agents** | Déploient sur Agent Runtime, avec plugin Model Armor et confirmation humaine ; enregistrent dans Agent Registry | [agent/](agent/secure_agent/agent.py), [fiche développeurs](docs/phase2-terraform/08-developpeurs-agents.md) |
| **DPO** | Décide de la journalisation du contenu et des durées de conservation | [docs/00 §10](docs/00-socle-securite.md#10-couche-6--audit-et-détection) |
| **Admins Google Workspace / Entra** | Groupes, ID client Workspace, fournisseur d'identité | [docs/01 étape 0](docs/01-phase1-console.md#étape-0--préparer) |

**Règle de séparation des rôles (mesure 8) :** un administrateur Gemini Enterprise **ne peut pas** affaiblir
Model Armor, toucher aux clés ou lire les journaux privés. Seul le groupe sécurité le peut.

---

## 3. Les 10 mesures et notre réponse

Légende : 🟢 natif console (phase 1), 🔷 Terraform (phase 2), 🧰 script fourni, ⚪ hors périmètre de l'app.

| # | Mesure de la note | Natif console | Terraform | Script | Statut |
|---|---|---|---|---|---|
| 1 | Agents sur Agent Runtime (ex-Agent Engine) | 🟢 Plancher Model Armor *Agent Platform* | 🔷 `90_agents_registry.tf`, `30_ai_guardrails.tf` | | ✅ |
| 2 | Shadow AI : quarantaine + inventaire | 🟢 Politiques d'org, Asset Inventory, SCC AI Protection | 🔷 `75_shadow_ai.tf` | 🧰 `shadow_ai_inventory.sh` | ✅ (Wiz : ⚪) |
| 3 | Model Armor Inspect & Block, URL, SDP | 🟢 Templates + réglage de l'app | 🔷 `30_ai_guardrails.tf` (DLP **FR**) | 🧰 `test_model_armor.sh` | ✅ plus strict que la note |
| 4 | Journaux d'accès, AxT, Access Approval, SIEM | 🟢 Audit Logs, Access Transparency, Access Approval | 🔷 `70_detection.tf`, `80_logging.tf`, `85_siem_access.tf` | 🧰 `daily_report.sh` | ✅ (AxT : réglage d'org) |
| 5 | Filtrage de sortie (SWP) | 🟢 Agent Gateway, IP fixes des connecteurs | 🔷 `60_advanced.tf`, `95_secure_web_proxy.tf` | | ✅ voir correction §8.6 |
| 6 | RAG : droits + analyse avant indexation | 🟢 Connecteurs fédérés | 🔷 `40_connectors.tf` | 🧰 `scan_before_ingest.py` | ✅ |
| 7 | VPC Service Controls | 🟢 Périmètre en dry-run | 🔷 `60_advanced.tf` (+ `aiplatform`, niveau d'accès) | | ✅ dry-run → enforcement |
| 8 | Identité (WIF), un projet par domaine, séparation des rôles | 🟢 Fournisseur d'identité de l'app | 🔷 `10_identity_access.tf` | | ✅ (choix IdP : §8.7) |
| 9 | Validation humaine des actions | 🟢 Confirmation des actions GE | 🔷 agent `require_confirmation` | | ✅ |
| 10 | Agent Registry central, partage encadré | 🟢 Agent Registry, partage d'agents désactivé | 🔷 `90_agents_registry.tf`, `50_app.tf` | | ✅ |

Le détail mesure par mesure (ce que la note demande, ce qu'on fait, la preuve) est dans
[docs/05-correspondance-note.md](docs/05-correspondance-note.md).

---

## 4. Comment procéder : 4 phases

```
 Semaine 1         Semaine 2-3                 Semaine 3-4             Ensuite, chaque jour
┌──────────┐    ┌──────────────────┐    ┌─────────────────────┐    ┌────────────────────┐
│ PHASE 1  │───▶│ PHASE 2          │───▶│ PHASE 3             │───▶│ PHASE 4            │
│ Console  │    │ Terraform        │    │ Tests (recette)     │    │ Exploitation       │
│ natif    │    │ paliers A→D      │    │ 22 tests + preuves  │    │ journal quotidien  │
│ observer │    │ importer, figer  │    │ verify_controls.sh  │    │ revue mensuelle    │
└──────────┘    └──────────────────┘    └─────────────────────┘    └────────────────────┘
  Effet immédiat,   Seule source de       Chaque mesure prouvée    Détecter, réagir,
  sans risque       vérité ensuite        par un test et un log    prouver à l'audit
```

### Phase 1 : activer le natif (console), semaine 1

But : obtenir **tout de suite** la protection que Google fournit, et **observer** avant de bloquer.
Toutes ces actions sont **réversibles** et sans effet sur les utilisateurs, sauf mention contraire.

| Ordre | Action console | Mesure | Effet |
|---|---|---|---|
| 1 | Journaux d'audit « accès aux données » sur Gemini Enterprise, Agent Platform, Model Armor | §4 | On voit qui fait quoi |
| 2 | Templates Model Armor + Model Armor dans l'app GE | §3 | Questions et réponses filtrées |
| 3 | Plancher Model Armor, avec *Agent Platform* en **inspection seule** | §1, §3 | On mesure ce qui serait bloqué dans les agents |
| 4 | Agent Registry activé ; partage d'agents désactivé dans l'app | §10 | Un seul catalogue |
| 5 | Asset Inventory : lancer l'inventaire Shadow AI | §2 | Liste des agents et services exposés |
| 6 | Access Transparency (org) puis Access Approval (projet) | §4 | Accès de Google tracés et soumis à accord |
| 7 | VPC-SC en **dry-run** | §7 | On voit ce qui serait bloqué, sans rien bloquer |

Pas à pas, avec le chemin exact dans la console et la vérification : [docs/01-phase1-console.md](docs/01-phase1-console.md).

### Phase 2 : figer en Terraform, semaines 2 et 3

But : tout ce qui a été activé à la main devient du **code relu**, déployé par la CI (même circuit que le
projet 07 : PR → plan → validation sécurité → apply). Les réglages faits en console sont **importés** :
Terraform les reprend sans les recréer.

| Palier | Contenu | Prérequis |
|---|---|---|
| **A** (projet seul) | Socle 06 + `aiplatform` dans l'audit + plancher *Agent Platform* + Agent Registry + alerte Shadow AI | Droits sur le projet |
| **B** (avec le SOC) | Export SIEM Pub/Sub | Le SOC fournit l'identité de son connecteur |
| **C** (droits organisation) | Politiques d'org, VPC-SC + niveau d'accès (dry-run, puis `vpc_sc_enforce = true`), Access Approval | Rôles org ; Access Transparency ; ID client Workspace |
| **D** (si agents dans le VPC) | Secure Web Proxy | Réseau, sous-réseaux, liste blanche validée |

Détails, fichiers et commandes, une fiche par palier : [docs/phase2-terraform/](docs/phase2-terraform/README.md).

### Phase 3 : prouver, semaines 3 et 4

22 tests, chacun avec **le résultat attendu et le journal qui le prouve**. Deux scripts automatisent l'essentiel :

```bash
./scripts/test_model_armor.sh       # filtrage : légitime accepté, attaques bloquées
./scripts/verify_controls.sh        # conformité : chaque mesure est-elle réellement en place ?
```

Plan complet : [docs/03-plan-de-tests.md](docs/03-plan-de-tests.md).

### Phase 4 : exploiter, chaque jour

| Fréquence | Qui | Quoi | Durée |
|---|---|---|---|
| Chaque jour | Sécurité (ou SOC) | `./scripts/daily_report.sh` : changements, blocages, Shadow AI, accès refusés | 10 min |
| Chaque semaine | Sécurité + plateforme | Faux positifs Model Armor, agents ajoutés au registre, alertes reçues | 30 min |
| Chaque mois | Sécurité + PM | `verify_controls.sh` + `shadow_ai_inventory.sh` archivés (preuve d'audit) | 1 h |
| Chaque trimestre | Sécurité + DPO | Revue des droits, de la liste blanche de sortie et des durées de conservation | 2 h |

Où trouver chaque journal, requêtes prêtes à l'emploi, réponses aux incidents :
[docs/04-exploitation-journaliere.md](docs/04-exploitation-journaliere.md).

---

## 5. Ce que le projet contient

```
08-gemini-enterprise-securite-acme/
├── README.md                      ← ce guide
├── docs/
│   ├── 00-socle-securite.md       le socle hérité du 06 (6 couches, détaillées)
│   ├── 01-phase1-console.md       activer le natif, pas à pas : clics, valeurs, gcloud, vérifier, annuler
│   ├── phase2-terraform/          8 fiches : import, paliers A→D, CI/CD, mesure par mesure, développeurs
│   ├── 03-plan-de-tests.md        22 tests + preuves
│   ├── 04-exploitation-journaliere.md  journal quotidien, requêtes, incidents
│   ├── 05-correspondance-note.md  les 10 mesures une par une + corrections
│   └── 06-dlp-cmek-agent-gateway.md  les 3 briques expliquées : console puis Terraform
├── terraform/                     socle 06 + fichiers 75, 85, 90, 95 (nouveaux)
│   └── docs/                      une fiche par fichier .tf (débutant)
├── agent/secure_agent/            agent exemple : Model Armor + validation humaine
├── scripts/
│   ├── test_model_armor.sh        recette du filtrage
│   ├── verify_controls.sh         contrôle de conformité (lecture seule)
│   ├── daily_report.sh            journal quotidien (Markdown)
│   ├── shadow_ai_inventory.sh     inventaire Shadow AI (Asset Inventory)
│   ├── scan_before_ingest.py      analyse des documents avant indexation
│   ├── register_agent.sh, pack.py publication de l'agent
│   └── build_pdf.py, build_pptx.js  génération du PDF et du deck
├── Gemini-Enterprise-Note-securite-Acme.pdf
└── Gemini-Enterprise-Note-securite-Acme.pptx
```

---

## 6. Démarrage rapide

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars    # projet, groupes, connecteurs, paliers
terraform init
terraform plan                                   # LIRE le plan
terraform apply

cd ..
./scripts/test_model_armor.sh
PROJECT_ID=... APP_ID=... ./scripts/verify_controls.sh
./scripts/daily_report.sh > rapport-$(date +%F).md
```

Agent exemple, en local (sans Model Armor) puis sur Agent Runtime :

```bash
cd agent && LOCAL_DEV=1 python secure_agent/agent.py      # autotest des outils
LOCAL_DEV=1 adk web .                                      # essai : « rembourse 10 € sur CMD-1002 »
# puis deploy_secure_agent = true dans terraform.tfvars et terraform apply
```

---

## 7. Pourquoi d'abord la console, puis Terraform ?

C'est la question qu'on nous posera. La réponse tient en quatre points :

1. **La protection n'attend pas le code.** Activer les journaux d'audit ou Model Armor prend dix minutes en
   console. Attendre deux semaines de développement, c'est rester deux semaines sans protection.
2. **Observer avant de bloquer.** Le plancher *Agent Platform* en mode inspection et VPC-SC en dry-run montrent
   ce qui **serait** bloqué. On règle les seuils sur des cas réels, sans casser un service en production.
3. **Le code ensuite, pour durer.** Un réglage manuel se perd, se modifie sans trace, ne se reproduit pas dans
   le projet du domaine suivant. Terraform le rend **relu** (PR), **traçable** (Git), **reproductible**
   (un projet par domaine, mesure 8) et **vérifiable** (le `plan` montre toute dérive).
4. **Rien n'est perdu entre les deux.** Les ressources créées en console sont **importées** dans Terraform
   (blocs `import`, [fiche 01](docs/phase2-terraform/01-preparer-et-importer.md#5-reprendre-ce-qui-a-été-créé-en-console-import)).
   Après la phase 2, **plus aucun changement en console** : l'alerte « garde-fou modifié » signale toute exception.

---

## 8. Corrections à apporter à la note

La note est solide sur le fond. Six points sont inexacts techniquement et méritent d'être corrigés avant
qu'elle serve de référence d'audit. Le détail et les sources sont dans [docs/05 §2](docs/05-correspondance-note.md#2-corrections-à-apporter-à-la-note).

| # | La note dit | La réalité | Ce qu'on fait |
|---|---|---|---|
| 8.1 | Exemple JSON Model Armor | Noms de champs invalides (`enforcement`, `raiSettings.hateSpeech`) : l'API le refuse | Syntaxe correcte dans `30_ai_guardrails.tf` |
| 8.2 | `basicConfig` détecte les données Acme | Détecteurs orientés US : ni IBAN, ni NIR, ni CNI | Configuration **avancée** avec modèle DLP FR |
| 8.3 | « Detect and redact » | Dans Gemini Enterprise, une détection **bloque** : pas de masquage | Message clair à l'utilisateur, tests adaptés |
| 8.4 | Le filtre d'URL couvre « Echo Leak » | Il ne bloque que les URL **connues** comme malveillantes | Test de recette dédié (T09) + contrôle de sortie |
| 8.5 | Model Armor protège tous les modèles | Dans GE, il ne filtre **pas** les agents personnalisés | Plugin dans l'agent **et** plancher *Agent Platform* |
| 8.6 | SWP filtre la sortie de l'IA | Gemini Enterprise est un SaaS : il ne sort pas par le VPC Acme | Agent Gateway + politiques d'org pour GE ; SWP pour les charges du VPC |
| 8.7 | WIF Entra/Okta (mesure 8) | Avec un IdP tiers, les connecteurs **Workspace** ne fonctionnent pas ; changer d'IdP efface l'historique | **Décision à prendre avant la production** |

---

## 9. Vérifié / à valider

**Vérifié :** `terraform validate` OK (provider `hashicorp/google` 8.5) ; tous les types et champs Terraform
contrôlés dans le schéma du provider ; Access Approval couvre Gemini Enterprise, Agent Runtime, Model Armor et KMS (doc Google, GA) ; autotests de l'agent (`secure_agent OK`), du scanner (`self-test OK`) et
du contrôle de conformité. **Pas encore déployé** sur un projet Acme.

| À valider au premier déploiement | Repli |
|---|---|
| Le Secure Web Proxy exige-t-il un certificat même sans inspection TLS ? | Ajouter `certificate_urls` (Certificate Manager) si l'API le demande |
| Affichage de la demande de confirmation d'un agent ADK dans l'interface GE | Sinon : confirmation dans l'agent par un message explicite (« répondez OUI ») |
| Taille maximale d'un document pour l'analyse Model Armor | Le script met en quarantaine au-delà de 4 Mo (revue manuelle) |
| Filtre de l'alerte Shadow AI (noms de méthodes exacts) | Ajuster après le premier événement observé |
| Points du socle 06 | [docs/00 §16](docs/00-socle-securite.md#16-vérifié--à-valider-en-recette) |

---

## 10. Documentation détaillée

| Document | Pour |
|---|---|
| [01 – Phase 1 : activer le natif dans la console](docs/01-phase1-console.md) | DevOps, sécurité |
| [Phase 2 : Terraform (dossier, 8 fiches)](docs/phase2-terraform/README.md) | DevOps, sécurité, développeurs |
| [03 – Plan de tests](docs/03-plan-de-tests.md) | Sécurité, PM, recette |
| [04 – Exploitation journalière, journaux, incidents](docs/04-exploitation-journaliere.md) | Sécurité, SOC |
| [05 – Correspondance avec la note, mesure par mesure](docs/05-correspondance-note.md) | Tous, audit |
| [06 – DLP, CMEK, Agent Gateway : ce que c'est, comment les configurer](docs/06-dlp-cmek-agent-gateway.md) | Tous |
| [00 – Socle de sécurité (projet 06)](docs/00-socle-securite.md) | Tous |
| [terraform/docs/](terraform/docs/00-bases-terraform.md) | Débutants Terraform |
| PDF / PPTX à la racine | Présentation à l'équipe |


## Supports

![Gemini Enterprise Note securite Acme](./Gemini-Enterprise-Note-securite-Acme.pdf)
