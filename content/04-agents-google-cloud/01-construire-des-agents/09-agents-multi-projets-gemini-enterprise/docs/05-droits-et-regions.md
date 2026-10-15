# 05. Droits et régions : qui donne quel droit, à qui, où

**Pour qui :** DevOps, sécurité, équipes qui publient ou consomment des agents.

**Règle générale :** le droit est toujours **donné par le projet de la ressource appelée**, à **l'identité qui appelle**.
L'équipe propriétaire garde donc la main : c'est elle qui ouvre l'accès à son agent.


> **C'est la référence unique des droits.** Les tutoriels ([02](02-tuto-meme-projet.md), [03](03-tuto-autre-projet.md)) et
> le parcours « agent déjà dans un registre » ([04](04-agents-deja-dans-un-registry.md)) appliquent cette matrice.

---

## 1. La matrice des droits

| # | Scénario | Identité qui appelle | Rôle | Posé sur | Commande |
|---|---|---|---|---|---|
| 0 | L'app GE utilise un **agent Agent Runtime du MÊME projet** | compte de Gemini Enterprise | *(aucun à ajouter)* : `roles/discoveryengine.serviceAgent` déjà attribué par Google sur son projet | — | — |
| 0 bis | L'app GE utilise un **agent A2A sur Cloud Run du MÊME projet** | compte de Gemini Enterprise | `roles/run.invoker` | Le service Cloud Run | comme 2 |
| 1 | L'app GE (projet A) utilise un **agent ADK Agent Runtime** du projet B | `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` | `roles/discoveryengine.serviceAgent` | **Projet B** | `gcloud projects add-iam-policy-binding B --role=roles/discoveryengine.serviceAgent --member=serviceAccount:service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` |
| 2 | L'app GE (A) utilise un **agent A2A sur Cloud Run** du projet B | même compte GE | `roles/run.invoker` | **Le service** Cloud Run (projet B) | `gcloud run services add-iam-policy-binding SERVICE --region=R --project=B --role=roles/run.invoker --member=…` |
| 3 | Un **agent** du projet A **appelle** un agent Agent Runtime du projet B | compte de service de l'agent A | `roles/aiplatform.viewer` | **L'agent** B (ressource) | Terraform `google_vertex_ai_reasoning_engine_iam_member` |
| 4 | L'agent A **cherche** dans l'**Agent Registry** du projet B | compte de service de l'agent A | `roles/agentregistry.viewer` | Projet B | `gcloud projects add-iam-policy-binding B --role=roles/agentregistry.viewer --member=serviceAccount:…` |
| 5 | L'agent A appelle un agent **A2A sur Cloud Run** du projet B | compte de service de l'agent A | `roles/run.invoker` | Le service (B) | comme 2 |
| 6 | Un agent utilise un **template Model Armor** d'un projet C (projet sécurité) | compte de service de l'agent | `roles/modelarmor.user` | Projet C | fait par `modules/adk_agent` |
| 7 | **Agent Gateway** laisse passer vers un serveur MCP / agent du registre | identité qui appelle (GE ou agent) | `roles/iap.egressor` | La ressource du registre | `google_iap_agent_registry_*_iam_member` (projet 08) |
| 8 | Une **personne** explore le registre d'une autre équipe | groupe de l'utilisateur | `roles/agentregistry.viewer` | Projet B | — |
| 9 | Des **utilisateurs** GE voient l'agent dans l'app | groupe | **Agent User** | L'agent, dans l'app | onglet *Autorisations utilisateur* |

**Ce qu'on ne fait jamais :** donner `roles/aiplatform.user` ou `roles/editor` sur le projet d'en face « pour que ça marche ».
Cela permettrait de modifier ou de supprimer tous ses agents.

---

## 2. Les règles de région

| App Gemini Enterprise | Agents Agent Runtime | Agent Gateway | Registre (import) |
|---|---|---|---|
| `eu` | `europe-*` | `europe-west1` | `europe-west1` ou `eu` |
| `us` | `us-*` | `us-central1` | `us-central1` ou `us` |
| `global` | toutes | `us-central1` | `us-central1`, `us` ou `global` |

Un agent en `us-central1` ne peut **pas** être ajouté à une app `eu`. Pour Acme (données en UE) : tout en `europe-west1`.

---

## 3. Si VPC Service Controls est appliqué (projet 08)

Un périmètre autour du projet GE **bloque** les appels vers un projet **hors** du périmètre, et inversement. Trois options :

| Option | Quand |
|---|---|
| Mettre les deux projets **dans le même périmètre** | Équipes de même niveau de sensibilité (le plus simple) |
| **Règle de sortie** (*egress*) du périmètre GE vers le projet B, pour `aiplatform.googleapis.com`, limitée aux comptes des agents | Projet B hors périmètre, appels sortants seulement |
| **Règle d'entrée** (*ingress*) dans le périmètre de B | Projet B dans un autre périmètre |

**Toujours tester en dry-run** : les violations apparaissent dans les journaux VPC-SC avec le service et l'identité exacts à
autoriser.

---

## 4. Ce que Terraform fait pour vous (ce projet)

| Fichier | Droits posés |
|---|---|
| `modules/adk_agent` | Identité dédiée de chaque agent + rôles sur **son** projet + `modelarmor.user` sur le projet des templates (#6) |
| `20_orchestrator.tf` | #3 (`aiplatform.viewer` **sur** `stock-agent`) et #4 (`agentregistry.viewer` sur le projet agents) |
| `30_gemini_enterprise.tf` | #1 pour **chaque** projet qui héberge un agent publié (agent stock + `external_adk_agents`) |
| `01-bis-cloud-run-a2a/terraform` | Identité dédiée par agent, #6, et #0 bis / #2 (`run.invoker` **sur chaque service** Cloud Run) |
| `02-bis-agent-runtime/terraform` | Identité dédiée par agent (`modules/adk_agent`), #6, et #1 si le projet des agents n'est pas celui de l'app |

Le compte qui exécute Terraform doit avoir `resourcemanager.projectIamAdmin` (ou équivalent) **sur les deux projets**. En CI,
c'est souvent la limite : chaque équipe pose les droits de **son** projet dans **son** dépôt, et ce dépôt-ci ne fait que la
publication. Les commandes de la matrice servent alors de « demande d'accès » à transmettre.

---

## 5. Diagnostiquer un refus

| Symptôme | Cause probable | Vérification |
|---|---|---|
| Gemini Enterprise : « agent indisponible » sur un agent d'un autre projet | #1 manquant | `gcloud projects get-iam-policy B --flatten=bindings --filter="bindings.role:discoveryengine.serviceAgent"` |
| L'orchestrateur répond « Agent stock indisponible : 403 … reasoningEngines.query » | #3 manquant | API : `curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" https://europe-west1-aiplatform.googleapis.com/v1/projects/B/locations/europe-west1/reasoningEngines/ID:getIamPolicy` |
| « 'stock-agent' absent de l'Agent Registry » | #4 manquant, mauvaise région, ou nom affiché différent | `python scripts/registry.py B europe-west1` avec le compte de l'agent |
| Ajout refusé : région | App `eu` et agent hors `europe-*` | Redéployer l'agent en `europe-west1` |
| `PERMISSION_DENIED` avec `vpcServiceControlsUniqueIdentifier` | Périmètre VPC-SC | §3 |
