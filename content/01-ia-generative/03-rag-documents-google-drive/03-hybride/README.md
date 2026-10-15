# 03. Hybride : le kit 1 comme socle, les connecteurs Gemini Enterprise en plus

**Le but :** un seul kit, déployable chez des clients différents :
- client **sans** Gemini Enterprise → le [kit 1](../01-rag-engine-sync/README.md) seul (RAG Engine, ses sources) ;
- client **avec** Gemini Enterprise → **le même kit 1**, plus une ligne de configuration : l'agent cherche **aussi**
  dans l'app Gemini Enterprise du client (ses data stores et connecteurs, montés avec le [kit 2](../02-gemini-enterprise-natif/README.md)).

Même interface, même agent, même CLI, mêmes citations : les réponses mélangent les deux mondes.

```
                       ┌──────────── kit 1 ─────────────────────────────┐
 Drive connecté, dossier partagé, dépôts ─► corpus RAG Engine « rag-kit »   ├──┐
                       └────────────────────────────────────────────────┘  │  l'agent cherche dans les deux,
 Data stores Gemini Enterprise (kit 2) ─► corpus adossé à l'app GE (lecture) ├──┤  entrelace les résultats par rang,
   (dépôts GE, SharePoint, OneDrive…)     « rag-kit-gemini-enterprise »      │  cite chaque source
                                                                             └──► interface du kit 1
```

> **Testé en vrai** le 14/10/2026 sur `main-project-511608` : kit 1 déployé avec `GE_SERVING_CONFIG` pointant sur
> une app Vertex AI Search / Gemini Enterprise de test (data store des dépôts du kit 2). Question dont la réponse
> n'existe que côté Gemini Enterprise (« offre Albatros : 990 € », PDF du kit 2) → réponse juste et citée ; question
> dont la réponse n'existe que dans le Drive du kit 1 (« indemnité : 47 € ») → réponse juste et citée ;
> `test_e2e.py` complet : **TOUT EST OK**. Corpus `europe-west4` adossé à une app `eu` : accepté.

## Activer

Sur un kit 1 déjà déployé ([03-2](../01-rag-engine-sync/docs/03-2-deployer-terraform.md)) :

```bash
cd gcp_rag/01-rag-engine-sync
./ragkit set GE_SERVING_CONFIG "projects/<NUMÉRO>/locations/eu/collections/default_collection/engines/<APP_ID>/servingConfigs/default_search"
./ragkit deploy --plan      # + 1 corpus « rag-kit-gemini-enterprise », service et job mis à jour
./ragkit deploy
./ragkit status             # « Hybride : + app Gemini Enterprise <APP_ID> »
```

Désactiver : `./ragkit set GE_SERVING_CONFIG ""` puis `./ragkit deploy` (le corpus adossé est supprimé ; l'app
Gemini Enterprise n'est pas touchée).

`<NUMÉRO>` : numéro du projet de l'app ; `<APP_ID>` : console Gemini Enterprise → Apps → ID.

## Ce qu'il faut savoir

| Sujet | Détail |
|---|---|
| Lecture seule | Le kit **cherche** dans l'app ; il n'y écrit rien. La synchro des sources Gemini Enterprise reste celle de Google (kit 2) |
| Identité | La recherche part du **compte de service du kit** (`rag-kit-sa`), pas de la personne : les data stores **liés aux identités Workspace** (Drive fédéré, sources avec ACL par utilisateur) refusent les comptes de service (documenté : 403). En hybride, n'en attendez que les sources **sans droits par personne** (dépôts GE, sites, SharePoint/OneDrive ingérés sans ACL…). Pour les droits par personne : l'app Gemini Enterprise elle-même |
| Panne côté GE | Si l'app Gemini Enterprise ne répond pas, l'agent continue avec le seul corpus du kit (avertissement dans les journaux : « recherche Gemini Enterprise en échec ») |
| Droits | `rag-kit-sa` a déjà `roles/discoveryengine.viewer` (même projet). **App dans un autre projet** : donnez-lui ce rôle sur le projet de l'app (non testé en multi-projets ; si la recherche est refusée, donnez-le aussi à l'agent de service RAG `service-<n°>@gcp-sa-vertex-rag…`) |
| Doublons | Un même document présent des deux côtés ressort deux fois : évitez de brancher la même source dans les deux |
| Coût | En plus du kit 1 : chaque question fait une recherche dans l'app (tarif Vertex AI Search / Gemini Enterprise de votre contrat) |

## Choisir entre 1, 2, 3 et 4

| Situation | Kit |
|---|---|
| Pas de Workspace ni de licences, un corpus commun à l'équipe | **1** |
| Workspace / Microsoft 365 + licences, chacun ne voit que ses documents | **2** |
| Un kit à déployer chez plusieurs clients, avec ou sans Gemini Enterprise | **3** (= 1 + `GE_SERVING_CONFIG`) |
| Sur un poste, sans Google Cloud, avec Claude | **4** |
