# 04. Votre agent est déjà dans un Agent Registry : comment l'ajouter à notre stack ?

**Pour qui :** les équipes qui ont **déjà** un agent enregistré dans **leur** Agent Registry (leur projet GCP) et veulent
qu'il soit utilisable dans **notre** app Gemini Enterprise, ou par **nos** agents.
**En une phrase :** le registre sert à **trouver** l'agent et à savoir **comment** le joindre. Ensuite, l'ajout se fait
par l'une de trois voies, selon le type d'agent et le niveau de gouvernance voulu.

> Notre stack, c'est :
> - le **projet A**, avec l'app Gemini Enterprise (`eu`), ses agents, et à terme son Agent Gateway et son registre ;
> - **votre projet B**, avec votre agent et votre registre.

---

## 1. Les trois voies, en un tableau

| | Voie 1 : par nom de ressource | Voie 2 : par carte A2A | Voie 3 : par **notre** registre + Agent Gateway |
|---|---|---|---|
| **Pour quel agent** | Agent ADK sur **Agent Runtime** (s'enregistre seul dans votre registre) | Agent **A2A** sur Cloud Run, GKE ou ailleurs (enregistré à la main dans votre registre) | Les deux |
| **Ce qu'on prend dans votre registre** | Le nom de ressource `projects/…/reasoningEngines/ID` | L'URL A2A ou la carte d'agent | La carte d'agent |
| **Droit que **vous** donnez (projet B)** | `roles/discoveryengine.serviceAgent` au compte de Gemini Enterprise | `roles/run.invoker` sur votre service | Comme 1 ou 2 |
| **Droit que **nous** posons (projet A)** | — | — | `roles/iap.egressor` sur l'entrée du registre (passerelle) |
| **Passe par Agent Gateway** | Si votre agent y est configuré | **Non** | **Oui** |
| **Délai** | Le jour même | Le jour même | Quelques jours (passerelle à mettre en place) |
| **Quand** | **Par défaut** | Agent non-Google ou hors Agent Runtime | Gouvernance centrale (cible) |

**Pourquoi on ne branche pas « directement votre registre » sur notre app.** Gemini Enterprise n'importe des agents que
depuis **le** registre relié à **son** Agent Gateway, dans la région de l'app (`europe-west1` ou `eu` pour une app `eu`).
Votre registre est dans votre projet ; le relier à notre passerelle d'un autre projet n'est pas documenté par Google (point
à valider). Les voies 1 et 2 fonctionnent aujourd'hui, et la voie 3 passe par une **déclaration** de votre agent dans notre registre.

---

## 2. Étape commune : lire votre entrée de registre

Il faut d'abord savoir **ce qu'est** votre agent dans le registre. Trois façons, au choix.

**Console (projet B) :** 🔎 « Agent Registry » → région de l'agent (souvent `europe-west1`) → onglet **Agents** → cliquer sur
l'agent → noter :
- l'**identifiant** (URN) ;
- les **interfaces** (URL, protocole) ;
- la présence d'une **carte A2A**.

**gcloud :**

```bash
gcloud agent-registry agents list --location=europe-west1 --project=VOTRE_PROJET
gcloud agent-registry agents describe NOM_AGENT --location=europe-west1 --project=VOTRE_PROJET
```

**Notre script** (il dit directement comment l'ajouter) :

```bash
python scripts/registry.py VOTRE_PROJET europe-west1
# - stock-agent: Donne le stock d'un article…
#     ajout : adk  projects/123/locations/europe-west1/reasoningEngines/456
# - pricing-a2a: Prix et promotions…
#     ajout : a2a  https://pricing-a2a-123.europe-west1.run.app/a2a/pricing/.well-known/agent-card.json  [carte A2A dans le registre]
```

**Lire l'URN :**

| URN dans le registre | Type | Voie |
|---|---|---|
| `urn:agent:projects-123:projects:123:locations:europe-west1:reasoningEngines:456` | Agent Runtime | **1** → `projects/123/locations/europe-west1/reasoningEngines/456` |
| `urn:agent:projects-123:projects:123:locations:europe-west1:run:services:pricing` | Cloud Run | **2** (si A2A) |
| Service enregistré à la main (`agent_spec` A2A) | Externe | **2** |

**Contrôles avant d'aller plus loin :**
- **Région :** notre app est en `eu`, donc l'agent doit être en `europe-*`. Sinon il faut le redéployer.
- **A2A :** la carte doit annoncer `protocolVersion: "0.3"`. Un agent Cloud Run qui ne parle pas A2A (simple API REST) ne
  peut pas être ajouté tel quel : il faut l'exposer en A2A (ADK : `adk deploy cloud_run --a2a`, voir [tutoriel 03, méthode 2](03-tuto-autre-projet.md#méthode-2--cloud-run--a2a)).

---

## 3. Voie 1 : agent Agent Runtime, par nom de ressource

| Qui | Fait quoi | Où |
|---|---|---|
| **Vous** (projet B) | Donnez `roles/discoveryengine.serviceAgent` à `service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com` | IAM du projet B |
| **Nous** (projet A), ou vous si vous êtes builder délégué ([doc 07](07-autonomie-utilisateurs.md)) | Ajoutons l'agent avec son nom de ressource | App → Agents → *Agent personnalisé via Agent Runtime* |
| **Nous** | Donnons le rôle *Agent User* au groupe cible | Onglet *Autorisations utilisateur* de l'agent |

En une commande (pose aussi le droit si vous l'exécutez avec un compte qui a l'accès IAM au projet B) :

```bash
export GE_PROJECT=acme-ge-recette GE_APP=acme-ge GE_LOCATION=eu
./scripts/add_agent_to_ge.sh adk projects/123/locations/europe-west1/reasoningEngines/456 "Stock magasin" "Stock par magasin"
```

En production, par PR (Terraform pose le droit et publie) :

```hcl
external_adk_agents = {
  stock = {
    engine       = "projects/acme-agents-supply/locations/europe-west1/reasoningEngines/456"
    display_name = "Stock magasin (Supply)"
    description  = "Stock d'un article par magasin, à partir du code article."
  }
}
```

---

## 4. Voie 2 : agent A2A, par sa carte

| Qui | Fait quoi | Où |
|---|---|---|
| **Vous** | Donnez `roles/run.invoker` sur **votre service** au compte de Gemini Enterprise (projet A). Hors Cloud Run : prévoyez une authentification OAuth | Cloud Run → service → Sécurité |
| **Nous** (ou builder délégué) | Ajoutons l'agent en collant sa carte | App → Agents → *Agent personnalisé via A2A* |
| **Nous** | Donnons *Agent User* au groupe cible | Onglet *Autorisations utilisateur* |

```bash
./scripts/add_agent_to_ge.sh a2a https://pricing-a2a-123.europe-west1.run.app/a2a/pricing/.well-known/agent-card.json "Prix et promotions"
```

**Ce qui change par rapport à la voie 1 :** Gemini Enterprise ne passe **pas** par Agent Gateway pour un agent A2A ajouté
ainsi, et le Model Armor de l'app ne le filtre pas. Votre agent doit donc **filtrer lui-même** (plugin Model Armor).

---

## 5. Voie 3 : par notre registre et notre Agent Gateway (cible)

L'idée : **notre** registre devient le catalogue de **tout** ce que notre app peut joindre, y compris vos agents ; Agent
Gateway refuse le reste.

| Étape | Qui | Quoi |
|---|---|---|
| 1 | Vous | Fournissez la **carte A2A** de votre agent (copiée de votre registre) et l'URL |
| 2 | Nous | **Déclarons** votre agent dans **notre** registre (`europe-west1`, projet A) : console *Agent Registry → Enregistrer*, ou Terraform ci-dessous |
| 3 | Nous | Autorisons le passage : `roles/iap.egressor` sur cette entrée pour le compte de Gemini Enterprise |
| 4 | Vous | `roles/run.invoker` sur votre service (comme voie 2) |
| 5 | Nous | Importons l'agent depuis le registre dans l'app (App → Agents → choisir dans la liste) |

**Déclaration en Terraform (projet A)** :

```hcl
resource "google_agent_registry_service" "pricing" {
  location     = "europe-west1"
  service_id   = "pricing-a2a"
  display_name = "Prix et promotions (équipe Pricing)"
  description  = "Prix, promotions en cours et historique de prix d'un article."
  agent_spec {
    type    = "A2A_AGENT_CARD"
    content = file("cards/pricing.json")      # la carte fournie par l'équipe ; son champ "url" donne l'adresse
  }
  # Pas de bloc interfaces avec une carte A2A : l'API le refuse (vérifié au déploiement de 01-bis).
}

resource "google_iap_agent_registry_agent_iam_member" "ge_to_pricing" {
  location = "europe-west1"
  agent_id = "pricing-a2a"                      # identifiant attribué par le registre (à vérifier après création)
  role     = "roles/iap.egressor"
  member   = "serviceAccount:service-NUM_A@gcp-sa-discoveryengine.iam.gserviceaccount.com"
}
```

Prérequis de la voie 3 : Agent Gateway liée à l'app (projet 08, `enable_agent_gateway`). **Attention :** notre projet 08 relie
aujourd'hui la passerelle au registre `global`. Pour l'import dans une app `eu`, Google demande un registre `europe-west1`
ou `eu` : à corriger avant d'ouvrir cette voie.

---

## 6. Et si c'est un de **nos agents** qui doit appeler le vôtre ?

C'est le cas de l'« Assistant magasin » qui appelle l'agent stock ([doc 06](06-appels-entre-agents.md)). Votre registre sert alors **en direct** : notre
agent y cherche le vôtre. Vous donnez à **l'identité de notre agent** :
- `roles/agentregistry.viewer` sur votre projet (pour le trouver) ;
- `roles/aiplatform.viewer` **sur votre agent** (pour l'appeler), ou `roles/run.invoker` s'il est sur Cloud Run.

Rien à ajouter dans l'app : c'est un appel d'agent à agent.

---

## 7. Ce que l'équipe doit nous fournir (modèle de demande)

| Information | Exemple |
|---|---|
| Projet et région du registre | `acme-agents-pricing`, `europe-west1` |
| Nom de l'agent dans le registre | `pricing-a2a` |
| Type | Agent Runtime / A2A sur Cloud Run / autre |
| Nom de ressource **ou** URL de la carte A2A | `projects/…/reasoningEngines/…` ou `https://…/.well-known/agent-card.json` |
| Nom affiché et description pour les utilisateurs | « Prix et promotions » |
| Groupe d'utilisateurs visé | `ge-agent-pricing@acme.example` |
| Données accédées, données personnelles ? | Prix publics, non |
| Model Armor dans l'agent ? Confirmation humaine des écritures ? | Oui / oui |
| Propriétaire et contact | `equipe-pricing@acme.example` |
| Voie souhaitée | 1, 2 ou 3 |

Avec ces informations, la voie 1 ou 2 se fait **le jour même**. La checklist de sécurité est celle de la [doc 07, §6](07-autonomie-utilisateurs.md#6-le-circuit-que-nous-recommandons-pour-acme).

---

## 8. Résumé visuel

```
 VOTRE PROJET B                                         NOTRE PROJET A
 ┌─────────────────────────────┐                        ┌───────────────────────────────────────────┐
 │ Votre Agent Registry        │  (1) on lit l'entrée   │                                           │
 │  • agent Agent Runtime ─────┼──── nom de ressource ─▶│ Voie 1 : App GE → "via Agent Runtime"     │
 │  • agent A2A (Cloud Run) ───┼──── carte A2A ────────▶│ Voie 2 : App GE → "via A2A"               │
 │                         └───┼──── carte A2A ────────▶│ Voie 3 : NOTRE registre → Agent Gateway   │
 │                             │                        │           → import dans l'app             │
 │ IAM donné par VOUS :        │                        │                                           │
 │  discoveryengine.serviceAgent / run.invoker ────────▶│ compte de service de Gemini Enterprise    │
 │  agentregistry.viewer + aiplatform.viewer ──────────▶│ identité de NOS agents (appel direct, §6) │
 └─────────────────────────────┘                        └───────────────────────────────────────────┘
```

**Voir aussi :**
- [01 – modalités d'ajout](01-comprendre-et-choisir.md) ;
- [03 – matrice des droits](05-droits-et-regions.md) ;
- [04 – pas à pas console](03-tuto-autre-projet.md) ;
- [05 – qui peut le faire](07-autonomie-utilisateurs.md).
