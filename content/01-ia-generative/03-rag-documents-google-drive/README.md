---
type: "course"
description: "Quatre kits RAG testés en vrai sur vos documents Drive, SharePoint et OneDrive : RAG Engine + synchro, Gemini Enterprise natif, hybride, et 100 % local avec Claude."
tags: ["rag", "rag-engine", "gemini-enterprise", "google-drive", "sharepoint", "claude"]
level: "intermediate"
duration: "8h"
usecases: ["recherche-documentaire"]
platforms: ["vertex-ai", "gemini-enterprise", "claude"]
date: "2026-10-14"
updated: "2026-10-14"
authors: ["Youcef"]
---
# RAG sur vos documents Google Drive (puis OneDrive, SharePoint) — sur Google Cloud

**Le but :** j'arrive, je donne mon dossier Drive, et j'ai un assistant qui répond à partir de ces documents, avec
les sources, **à jour tout seul**. Je peux aussi déposer des fichiers par glisser-déposer.

Quatre sous-projets : trois sur Google Cloud, du plus simple au plus intégré, et un 100 % local. Chacun est complet (code, Terraform, scripts, tutos, tests).

| # | Dossier | Moteur | Pour qui | État |
|---|---|---|---|---|
| 1 | [01-rag-engine-sync](01-rag-engine-sync/README.md) | **Vertex AI RAG Engine** + synchro maison + agent ADK + interface | Tout projet GCP, même un compte Gmail sans Workspace ; pas de licence | **Livré, testé en vrai** |
| 2 | [02-gemini-enterprise-natif](02-gemini-enterprise-natif/README.md) | Connecteurs **Gemini Enterprise** (Drive fédéré, SharePoint fédéré par Terraform, OneDrive), dépôts GCS synchronisés, droits par utilisateur | Entreprise avec Google Workspace (ou Entra ID) et licences Gemini Enterprise | **Livré** ; testé en vrai : dépôts, synchro (suppressions), rattachement, questions. À dérouler chez vous : Drive, SharePoint, OneDrive (Workspace, Entra) |
| 3 | [03-hybride](03-hybride/README.md) | Le kit 1 + **une ligne** (`GE_SERVING_CONFIG`) : l'agent cherche aussi dans l'app Gemini Enterprise | Kit unique déployable chez des clients différents | **Livré, testé en vrai** |
| 4 | [04-rag-local-claude](04-rag-local-claude/README.md) | **Local, sans GCP** : index SQLite (recherche hybride), embeddings locaux ou Voyage, **Claude** pour les réponses ; Google Drive (OAuth), dossiers du disque (dont OneDrive/SharePoint synchronisés), dépôt | Un poste, vos clés API, rien à déployer | **Livré, testé en vrai** (sauf réponse Claude : pas de clé ici) |

**Par où commencer :** [01-rag-engine-sync/docs/01-comprendre-et-choisir.md](01-rag-engine-sync/docs/01-comprendre-et-choisir.md)
compare les solutions du marché et les 3 approches, puis le [README du 1](01-rag-engine-sync/README.md) le
déploie en 5 commandes.
