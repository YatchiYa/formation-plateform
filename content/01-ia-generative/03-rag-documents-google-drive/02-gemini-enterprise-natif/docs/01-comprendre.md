# 01. Comprendre : comment Gemini Enterprise branche vos documents

## 1. Deux façons de connecter une source

| | **Fédéré** (recherche en direct) | **Ingestion** (copie indexée) |
|---|---|---|
| Où sont les données | Restent dans la source ; la question y est envoyée avec **votre** jeton | Copiées dans l'index Gemini Enterprise |
| Droits | Ceux de la source, à chaque question | ACL copiées avec les documents (synchro d'identité) |
| Fraîcheur | Toujours à jour | Selon la synchro (complète 3 h → 7 j, incrémentale 3 h → 7 j ; OneDrive : temps réel en préversion) |
| Qualité de recherche | Celle de la source | Meilleure (index Google, découpage, reranking) |
| Ici | Google Drive, SharePoint | OneDrive (au choix), fichiers déposés |

## 2. Ce que fait chaque brique

| Source | Mode | Qui la crée | Synchro |
|---|---|---|---|
| Google Drive | Fédéré | Console (pas de Terraform documenté ; Workspace obligatoire) | Rien à faire : interrogé en direct |
| SharePoint Online | Fédéré (`sharepoint_federated_search`) | **Terraform** (forme documentée par Google) | Idem |
| OneDrive | Ingestion ou fédéré | Console | Google (planifiée, ou temps réel en préversion) |
| Fichiers déposés | Ingestion (bucket GCS) | **Terraform** | Import `FULL` du bucket toutes les 15 min par Cloud Scheduler : ajouts, modifications **et suppressions** (vérifié) |

Le kit ne contient **aucun code applicatif** : Google fait la synchro, la recherche, les droits et l'interface.
Le kit crée, branche, vérifie et documente.

## 3. Identité et droits

- Chaque personne se connecte à Gemini Enterprise avec son compte (Google Workspace, ou fédération d'identité
  Entra ID). Une **licence** Gemini Enterprise est nécessaire par utilisateur.
- **Les sources Workspace refusent les comptes de service** (`403`, documenté) : on interroge toujours avec une
  vraie personne (`question.sh` utilise votre `gcloud auth login`).
- Drive fédéré ne renvoie que les documents **du domaine** de la personne qui cherche ; les comptes Gmail personnels
  ne sont pas pris en charge (pas d'identifiant client Workspace).
- Fichiers déposés : tous les utilisateurs de l'app les voient (pas d'ACL sur le bucket). Pour des documents
  restreints, utilisez Drive ou SharePoint.

## 4. Les deux pièges vérifiés en construisant le kit

| Piège | Effet | Ce que fait le kit |
|---|---|---|
| L'agent de service `…@gcp-sa-discoveryengine…` créé à la main n'a **aucun rôle** | Import GCS : `403 … does not have storage.buckets.create` | Donne `roles/discoveryengine.serviceAgent` |
| `document_processing_config` non déclaré dans Terraform | Au 2e `apply`, Terraform **recrée** le data store (index perdu, ID bloqué plusieurs heures) | Le déclare (layout parser + découpage) et l'ignore ensuite |

Le second piège concerne **tout Terraform** qui crée un `google_discovery_engine_data_store` sans ce bloc (y
compris les dossiers 05 et 06 de ce dépôt).
