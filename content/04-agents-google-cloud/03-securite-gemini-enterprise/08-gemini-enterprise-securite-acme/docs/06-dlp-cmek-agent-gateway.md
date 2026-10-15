# DLP, CMEK, Agent Gateway : ce que c'est vraiment, et comment les configurer

**Pour qui :** toute personne qui doit comprendre ces trois briques avant de les activer ou de les présenter.
Pour chacune : **ce que c'est**, **ce que ça protège (et ce que ça ne protège pas)**, **comment la configurer en console**,
**puis en Terraform**, **comment vérifier**, **les pièges**.

| | Question à laquelle elle répond | Agit sur | Analogie |
|---|---|---|---|
| **DLP** (avec Model Armor) | « Ce texte contient-il un IBAN, un NIR, un mot de passe ? » | Le **contenu** des questions et des réponses | Un douanier qui fouille chaque colis |
| **CMEK** | « Qui détient la clé qui chiffre nos données chez Google ? » | Les **données stockées** (index, conversations) | Le coffre est chez Google, mais c'est vous qui avez la clé |
| **Agent Gateway** | « Vers où les agents ont-ils le droit d'appeler ? » | Le **trafic sortant** des agents et de Gemini Enterprise | Un poste de contrôle à la sortie, avec une liste des destinations autorisées |

Les trois sont **indépendantes** : on peut activer l'une sans les autres. Elles couvrent trois risques différents :
une fuite **par le texte**, une fuite **par le stockage**, et une fuite **par les appels sortants**.

---

## 1. DLP (Sensitive Data Protection) branché sur Model Armor

### 1.1 Ce que c'est vraiment

- **Model Armor** est le pare-feu de l'IA. Pour chaque question et chaque réponse, il fait passer plusieurs filtres :
  injection de prompt, liens malveillants, contenus dangereux, et **données sensibles**.
- Pour le filtre « données sensibles », Model Armor a deux modes :
  - **basique** : une liste fixe de détecteurs Google, orientée États-Unis (cartes bancaires, numéro de sécurité sociale US,
    identifiants cloud). Il ne voit **ni IBAN, ni NIR, ni CNI** ;
  - **avancé** : Model Armor délègue la détection à un **modèle d'inspection DLP** que **vous** définissez, avec les
    détecteurs de votre choix (`FRANCE_NIR`, `IBAN_CODE`…).
- **DLP** (Sensitive Data Protection) est le service Google qui sait reconnaître plus de 150 types de données
  (*infoTypes*). Un **modèle d'inspection** est simplement une liste d'infoTypes et un seuil de confiance, enregistrée
  sous un nom.

```
Question de l'utilisateur
        │
        ▼
  Model Armor (template ge-prompt-shield)
   ├── filtre injection / jailbreak
   ├── filtre URL malveillantes
   ├── filtre IA responsable
   └── filtre données sensibles ──(mode avancé)──▶ modèle DLP ge-donnees-sensibles-fr
                                                    FRANCE_NIR, IBAN_CODE, CARTE, MOTS DE PASSE…
        │
   MATCH_FOUND ? ── oui ──▶ échange BLOQUÉ (message de politique)
        │ non
        ▼
   Gemini répond ──▶ même contrôle sur la réponse (ge-response-shield)
```

### 1.2 Ce que ça protège, et ce que ça ne protège pas

| Protège | Ne protège pas |
|---|---|
| Un salarié qui colle un IBAN, un NIR, un mot de passe dans une question | Les documents récupérés par le moteur : ils ne passent pas dans le filtre d'entrée. Mais une réponse qui en recopie un IBAN est bloquée en sortie |
| Une réponse qui ressortirait ces données | Les agents personnalisés (ADK) : il faut le plugin ou le plancher Agent Platform |
| | **Pas de masquage** dans Gemini Enterprise : une détection **bloque** l'échange, elle ne remplace pas par `****` |

**Pourquoi c'est important pour Acme :** en mode basique, le filtre laisse passer exactement les données que la CNIL
et le RGPD visent en France.

### 1.3 Configurer en console

**Étape A : le modèle DLP**
1. 🔎 « Sensitive Data Protection » → onglet **Configuration** → **Modèles** → onglet **Inspection** → **Créer un modèle**.
2. ID : `ge-donnees-sensibles-fr` ; emplacement : **multirégional → europe**.
3. **Gérer les infoTypes** → cocher `FRANCE_NIR`, `FRANCE_CNI`, `FRANCE_PASSPORT`, `FRANCE_TAX_IDENTIFICATION_NUMBER`,
   `IBAN_CODE`, `CREDIT_CARD_NUMBER`, `GCP_CREDENTIALS`, `AUTH_TOKEN`, `PASSWORD`.
4. Seuil de confiance : **Probable** (en dessous : trop de faux positifs sur des numéros quelconques) → **Créer**.
5. 🔎 « IAM » → donner **DLP User** et **DLP Reader** au compte
   `service-NUMÉRO_PROJET@gcp-sa-modelarmor.iam.gserviceaccount.com`. C'est Model Armor qui lit le modèle :
   sans ces rôles, la création du template échoue.

**Étape B : le template Model Armor qui l'utilise**
1. 🔎 « Model Armor » → **Templates** → **Créer** → région **eu** (même zone que l'app).
2. **Protection des données sensibles** → **Avancée** → modèle d'inspection :
   `projects/PROJET/locations/europe/inspectTemplates/ge-donnees-sensibles-fr`.
3. Les autres filtres, puis le type d'application : **Inspecter et bloquer** → **Créer**.
4. Brancher le template sur l'app : Gemini Enterprise → l'app → **Configurations** → **Assistant** → *Activer Model Armor*.

Le pas à pas complet, avec les commandes, est dans [01-phase1-console.md, étape 2](01-phase1-console.md#étape-2--templates-model-armor--modèle-dlp-france).

### 1.4 Puis en Terraform (`terraform/30_ai_guardrails.tf`)

```hcl
# Le modèle DLP : une liste d'infoTypes, venant d'une variable
resource "google_data_loss_prevention_inspect_template" "fr" {
  count       = var.sdp_mode == "advanced" ? 1 : 0
  parent      = "projects/${var.project_id}/locations/${var.dlp_location}"   # europe
  template_id = "ge-donnees-sensibles-fr"
  inspect_config {
    min_likelihood = "LIKELY"
    dynamic "info_types" {
      for_each = var.sensitive_info_types          # FRANCE_NIR, IBAN_CODE, ...
      content { name = info_types.value }
    }
  }
}

# Model Armor a le droit de lire ce modèle
resource "google_project_iam_member" "armor_reads_dlp" {
  for_each = var.sdp_mode == "advanced" ? toset(["roles/dlp.user", "roles/dlp.reader"]) : toset([])
  role     = each.value
  member   = "serviceAccount:service-${local.project_number}@gcp-sa-modelarmor.iam.gserviceaccount.com"
  project  = var.project_id
}

# Dans chaque template Model Armor : mode avancé -> le modèle DLP
sdp_settings {
  dynamic "advanced_config" {
    for_each = var.sdp_mode == "advanced" ? [1] : []
    content { inspect_template = google_data_loss_prevention_inspect_template.fr[0].id }
  }
}
```

**Ajouter un détecteur** (ex. numéro SIRET) = ajouter une ligne dans `sensitive_info_types` : une PR validée par la sécurité.

### 1.5 Vérifier

```bash
./scripts/test_model_armor.sh      # IBAN, carte -> MATCH_FOUND ; question normale -> NO_MATCH_FOUND
```

Dans l'app : coller un NIR de test → message de violation de politique.

### 1.6 Pièges

- Un modèle DLP en `europe` avec un template Model Armor en `eu` : point à confirmer au premier déploiement.
  Repli : modèle DLP en `global`.
- Seuil **Possible** ou plus bas : beaucoup de faux positifs, donc des utilisateurs bloqués, donc des contournements.
- Les **e-mails et téléphones** ne sont volontairement pas dans la liste : ils sont partout dans les documents internes.
  Ils sont protégés par les droits d'accès, pas par le filtre.

---

## 2. CMEK (Customer-Managed Encryption Keys)

### 2.1 Ce que c'est vraiment

Chez Google, **tout est déjà chiffré**, toujours, avec des clés gérées par Google. CMEK ne rajoute donc pas un
chiffrement : il change **qui détient la clé**. Les données de Gemini Enterprise sont chiffrées avec une clé qui vit dans
**Cloud KMS, dans votre projet**, et que **vous** contrôlez.

```
 Données Gemini Enterprise (index, conversations, préférences)
        │ chiffrées avec
        ▼
 Clé "gemini-enterprise-data"  (Cloud KMS, multirégion europe, projet Acme)
        │ utilisable uniquement par
        ▼
 Compte de service Gemini Enterprise  (rôle cryptoKeyEncrypterDecrypter)
        │
 Vous désactivez la clé ──▶ en 15 minutes, l'app ne peut plus rien lire ni indexer
```

**Le vrai bénéfice : le bouton d'arrêt.** Désactiver la clé rend les données **illisibles**, y compris pour Google, en
15 minutes. C'est **réversible pendant 30 jours** ; au-delà, la destruction est définitive (*crypto-shredding*).
Utile en cas d'incident majeur, de fin de contrat, ou pour répondre à une exigence d'audit (« qui peut lire nos données ? »).

### 2.2 Ce que ça protège, et ce que ça ne protège pas

| Protège | Ne protège pas |
|---|---|
| Les données **stockées** par Gemini Enterprise : index des connecteurs en ingestion, conversations, personnalisation | Un utilisateur légitime qui pose une question : CMEK n'est pas un contrôle d'accès |
| La capacité de **couper** l'accès à tout instant | Les sources en mode **fédéré** (Drive, SharePoint…) : rien n'est copié chez Gemini Enterprise, donc rien à chiffrer. Elles restent protégées par leur propre chiffrement |
| La preuve d'audit : chaque utilisation de la clé est journalisable | |

### 2.3 Les règles de Google à connaître avant de commencer

| Règle | Conséquence |
|---|---|
| App en **`eu`** ou **`us`** seulement, pas `global` | Choisir `eu` à la création de l'app (immuable) |
| Clé **multirégion** (`europe` pour une app `eu`) | Pas une clé régionale `europe-west1` |
| Clé enregistrée **avant** de créer l'app et les connecteurs | Ce qui est créé avant reste chiffré par Google, **sans retour possible** |
| Connecteurs **tiers** en ingestion (Jira, SharePoint…) : 3 clés **régionales** en plus | `europe-west1`, `europe-west4`, `europe-north1` |
| Rotation **manuelle** ; pas de rotation des clés régionales | Pas de rotation automatique sur ces clés |
| On ne change pas de clé sur une app existante | On peut seulement créer une nouvelle version de la même clé |

### 2.4 Configurer en console

1. 🔎 « Key Management » → **Créer un trousseau** : nom `gemini-enterprise`, emplacement **Multirégional → europe**.
2. **Créer une clé** : nom `gemini-enterprise-data`, **logicielle**, **symétrique chiffrement/déchiffrement**,
   rotation **Jamais (manuelle)**.
3. *(Si connecteurs tiers en ingestion)* créer 3 trousseaux et clés **régionaux** en `europe-west1`, `europe-west4`,
   `europe-north1`.
4. Sur chaque clé → **Autorisations** → **Accorder l'accès** → rôle **Chiffreur/Déchiffreur de CryptoKey Cloud KMS** à :
   - `service-NUMÉRO_PROJET@gcp-sa-discoveryengine.iam.gserviceaccount.com` (Gemini Enterprise) ;
   - le compte de service Cloud Storage du projet (utilisé pour les imports).
5. 🔎 « Gemini Enterprise » → **Paramètres** → onglet **CMEK** → **Ajouter une clé** pour `eu` → choisir la clé →
   **OK** → **Enregistrer**. Pour les connecteurs tiers : **Définir les clés régionales** et ajouter les 3 clés.
6. **Seulement ensuite**, créer l'app et les connecteurs.

**En ligne de commande :**

```bash
gcloud kms keyrings create gemini-enterprise --location=europe
gcloud kms keys create gemini-enterprise-data --keyring=gemini-enterprise --location=europe --purpose=encryption
gcloud kms keys add-iam-policy-binding gemini-enterprise-data --keyring=gemini-enterprise --location=europe \
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role=roles/cloudkms.cryptoKeyEncrypterDecrypter
# enregistrement dans Gemini Enterprise
curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://eu-discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/eu/cmekConfigs/default-cmek?set_default=true" \
  -d '{"kmsKey":"projects/'$PROJECT_ID'/locations/europe/keyRings/gemini-enterprise/cryptoKeys/gemini-enterprise-data"}'
```

### 2.5 Puis en Terraform (`terraform/20_data_protection.tf`)

```hcl
resource "google_kms_key_ring" "ge" {
  name     = var.kms_key_ring
  location = local.kms_location            # "europe" pour une app "eu"
}

resource "google_kms_crypto_key" "ge" {
  name     = "gemini-enterprise-data"
  key_ring = google_kms_key_ring.ge[0].id
  purpose  = "ENCRYPT_DECRYPT"             # pas de rotation_period : rotation manuelle (exigence GE)
  lifecycle { prevent_destroy = true }     # Terraform REFUSE de détruire la clé (= détruire les données)
}

resource "google_kms_crypto_key_iam_member" "key_users" {   # seuls GE et le stockage d'import
  role   = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member = local.ge_sa
  ...
}

resource "google_discovery_engine_cmek_config" "ge" {       # l'enregistrement (étape 5 de la console)
  location       = var.ge_location
  cmek_config_id = "default-cmek"
  kms_key        = google_kms_crypto_key.ge[0].id
  set_default    = true
  dynamic "single_region_keys" { ... }                      # les 3 clés régionales
  depends_on = [google_kms_crypto_key_iam_member.key_users]
}
```

Terraform respecte l'ordre imposé par Google sans qu'on ait à y penser. L'app (`50_app.tf`) référence la clé, donc Terraform
fait **clé → droits → enregistrement → connecteurs → app**.

**Séparation des rôles :** seul le groupe sécurité a `roles/cloudkms.admin`. Un administrateur Gemini Enterprise ne peut
ni désactiver ni détruire la clé.

### 2.6 Vérifier

```bash
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "X-Goog-User-Project: $PROJECT_ID" \
  "https://eu-discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/eu/cmekConfigs"   # state: ACTIVE
```

En **recette uniquement** : désactiver la version de clé → l'app cesse de répondre en 15 minutes ; réactiver → elle revient.

### 2.7 Pièges

- **Créer l'app avant d'enregistrer la clé** : c'est l'erreur la plus coûteuse, car il faut recréer l'app.
- **Rotation automatique** activée par réflexe sur la clé : refusée par Gemini Enterprise.
- **Détruire** une version de clé croyant la « désactiver » : au bout de 30 jours, c'est définitif.
- Coût : quelques euros par mois par clé, plus les opérations. Négligeable.

---

## 3. Agent Gateway

### 3.1 Ce que c'est vraiment

Un **point de passage géré par Google** pour tout le trafic **sortant** de Gemini Enterprise et des agents vers d'autres
agents, des serveurs MCP et des API. C'est un pare-feu applicatif conçu pour les agents.

- **Refus par défaut** : rien ne passe tant qu'une règle IAM ne l'autorise pas.
- L'autorisation se donne **par destination**, sur les ressources déclarées dans **Agent Registry** : rôle
  **`roles/iap.egressor`** (« IAP-secured Egressor ») pour l'identité qui appelle.
- Option : un **template Model Armor** appliqué au trafic qui traverse la passerelle.
- Chaque appel est **journalisé** : qui a appelé quel outil, quand, avec quel résultat.

```
 Gemini Enterprise / agent ADK
        │ "appelle l'outil MCP sheets-mcp"
        ▼
 Agent Gateway (europe-west1, géré par Google)
   ├── la destination est-elle dans Agent Registry ?
   ├── l'appelant a-t-il roles/iap.egressor sur cette destination ?   ── non ──▶ REFUSÉ + journal
   └── (option) Model Armor sur le contenu
        │ oui
        ▼
 Serveur MCP / agent / API autorisé
```

### 3.2 Pourquoi pas le Secure Web Proxy de la note ?

Gemini Enterprise est un **SaaS** : ses appels sortent de l'infrastructure Google, **pas** du réseau Acme. Un Secure
Web Proxy placé dans notre VPC ne les voit jamais. Agent Gateway est placé **sur le chemin** de Gemini Enterprise. Le SWP
reste utile pour **nos** charges qui sortent par notre VPC (fiche [phase 2 / 05](phase2-terraform/05-palier-d-reseau.md)).

### 3.3 Ce que ça protège, et ce que ça ne protège pas

| Protège | Ne protège pas |
|---|---|
| Un agent manipulé (injection indirecte) qui tente d'appeler un outil non prévu, ou d'envoyer des données vers un serveur inconnu | Le contenu échangé avec un outil **autorisé** (pour cela : Model Armor sur la passerelle, et la confirmation humaine) |
| La prolifération d'outils non déclarés (Shadow AI) : non enregistré = non joignable | Les connecteurs de données (Drive, SharePoint…), qui ont leurs propres contrôles |

### 3.4 Les règles de Google à connaître

| Règle | Conséquence |
|---|---|
| Mode **AGENT_TO_ANYWHERE** (sortie) uniquement pour Gemini Enterprise | Pas de contrôle d'entrée par cette voie |
| App `eu` → passerelle en **`europe-west1`** ; app `global` ou `us` → `us-central1` | La région de la passerelle découle de l'app |
| Registres : `global`, `eu` ou `europe-west1` pour une app `eu`. Les registres multirégion `eu` / `us` n'acceptent **pas** l'enregistrement manuel | On utilise le registre **`global`** |
| L'activer fait passer **tout** le trafic de Gemini Enterprise par la passerelle, **y compris les appels au modèle** | Tester en dev d'abord : une autorisation manquante peut tout bloquer |
| Après la liaison, les serveurs MCP et agents A2A doivent être **importés** dans l'app depuis Agent Registry | Étape à prévoir pour chaque outil |

### 3.5 Configurer en console / gcloud

1. Activer les API **Network Services**, **Agent Registry**, **IAP**.
2. Créer la passerelle. En ligne de commande, la création passe par un fichier YAML (`import`) :

```bash
cat > ge-egress.yaml <<YAML
name: ge-egress
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
- //agentregistry.googleapis.com/projects/$PROJECT_ID/locations/global
YAML
gcloud network-services agent-gateways import ge-egress --location=europe-west1 --source=ge-egress.yaml
gcloud network-services agent-gateways describe ge-egress --location=europe-west1
```

3. Enregistrer chaque serveur MCP dans **Agent Registry** (🔎 « Agent Registry » → *Enregistrer*), registre **global**.
4. **Autoriser** : sur chaque serveur MCP du registre → **Autorisations** → donner **IAP-secured Egressor**
   (`roles/iap.egressor`) au compte de Gemini Enterprise (`service-NUMÉRO@gcp-sa-discoveryengine…`) et à l'identité
   de chaque agent qui doit l'appeler.
5. Lier la passerelle à l'app : 🔎 « Gemini Enterprise » → l'app → **Sécurité** → **Configuration** → *Configuration
   Agent Gateway* : `projects/PROJET/locations/europe-west1/agentGateways/ge-egress` → **Enregistrer**.
6. Importer les serveurs MCP et agents dans l'app depuis Agent Registry.

**Liaison par l'API** (équivalent de l'étape 5) :

```bash
curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  -H "X-Goog-User-Project: $PROJECT_ID" \
  "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_NUMBER/locations/eu/collections/default_collection/engines/$APP_ID?updateMask=agentGatewaySetting.defaultEgressAgentGateway.name" \
  -d '{"agentGatewaySetting":{"defaultEgressAgentGateway":{"name":"projects/'$PROJECT_ID'/locations/europe-west1/agentGateways/ge-egress"}}}'
```

### 3.6 Puis en Terraform (`terraform/60_advanced.tf`, `50_app.tf`, `90_agents_registry.tf`)

```hcl
# La passerelle
resource "google_network_services_agent_gateway" "egress" {
  count    = var.enable_agent_gateway ? 1 : 0
  name     = "${var.app_id}-egress"
  location = var.region                                   # europe-west1
  google_managed { governed_access_path = "AGENT_TO_ANYWHERE" }
  registries = ["//agentregistry.googleapis.com/projects/${var.project_id}/locations/global"]
}

# Les autorisations : refus par défaut, on ouvre serveur MCP par serveur MCP
resource "google_iap_agent_registry_mcp_server_iam_member" "egress" {
  for_each      = local.gateway_grants                    # (serveur MCP autorisé) x (GE, agent exemple)
  location      = "global"
  mcp_server_id = each.value.mcp_server_id
  role          = "roles/iap.egressor"
  member        = each.value.member
}

# La liaison à l'app : 50_app.tf, champ agentGatewaySetting (API REST)
# L'agent ADK sur Agent Runtime : 90_agents_registry.tf
dynamic "agent_gateway_config" {
  for_each = var.enable_agent_gateway ? [1] : []
  content { agent_to_anywhere_config { agent_gateway = google_network_services_agent_gateway.egress[0].id } }
}
```

```hcl
# terraform.tfvars
enable_agent_gateway              = true
agent_gateway_allowed_mcp_servers = ["sheets-mcp"]     # ID du serveur dans Agent Registry
```

**Ouvrir un nouvel outil** = l'enregistrer dans Agent Registry, puis ajouter son ID dans la liste : une PR relue par la sécurité.

### 3.7 Vérifier

1. `curl …/engines/$APP_ID | jq .agentGatewaySetting` → le nom de la passerelle.
2. Dans l'app, une question qui utilise l'outil autorisé → fonctionne.
3. Retirer l'autorisation en recette → la même question échoue, et le refus apparaît dans les journaux de la passerelle.

### 3.8 Pièges

- **Tout bloqué après la liaison** : l'autorisation `iap.egressor` manque, ou l'outil n'est pas importé dans l'app.
  Tester en dev.
- Identité exacte présentée par Gemini Enterprise à la passerelle : **à confirmer en recette** (le code utilise le compte
  de service Gemini Enterprise ; ajuster si les journaux de refus montrent un autre principal).
- Une **règle d'organisation** peut interdire de lier une app à une passerelle : vérifier avec l'équipe Cloud centrale.

---

## 4. Dans quel ordre, et quand ?

| Ordre | Brique | Quand | Pourquoi à ce moment |
|---|---|---|---|
| 1 | **CMEK** | **Avant** de créer l'app et les connecteurs | Impossible à ajouter après coup |
| 2 | **DLP + Model Armor** | Dès le niveau 1, en dev | Effet immédiat, se règle sans rien casser |
| 3 | **Agent Gateway** | Dès qu'il y a un agent maison ou un serveur MCP | Sans agent, il n'y a rien à contrôler en sortie |

**À dire en une phrase :** « DLP contrôle **ce qu'on dit**, CMEK contrôle **qui peut lire ce qu'on stocke**, et Agent
Gateway contrôle **où les agents ont le droit d'aller**. »

## Sources Google

- CMEK pour Gemini Enterprise : https://docs.cloud.google.com/gemini/enterprise/docs/cmek
- Model Armor et Gemini Enterprise : https://docs.cloud.google.com/gemini/enterprise/docs/enable-model-armor
- Plancher et templates Model Armor : https://docs.cloud.google.com/model-armor/overview
- Agent Gateway avec Gemini Enterprise : https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/agent-gateway-ge-deploy
- Mise en place d'Agent Gateway (autorisations) : https://docs.cloud.google.com/gemini-enterprise-agent-platform/govern/gateways/set-up-agent-gateway
