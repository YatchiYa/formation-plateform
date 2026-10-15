# Phase 1 : activer chaque mesure dans la console Google Cloud, pas à pas

**Pour qui :** DevOps / plateforme et sécurité. **Durée :** semaine 1 (étapes 1 à 6 en une journée ;
7, 8, 10 et 11 avec l'équipe Cloud centrale).
**Principe :** on active d'abord ce que Google fournit **nativement**, en mode **observation** quand c'est possible.
Tout sera repris en Terraform en phase 2 ([phase2-terraform/](phase2-terraform/README.md)).

Chaque étape suit le même plan :

| Rubrique | Contenu |
|---|---|
| **Pourquoi** | Le risque couvert, en deux lignes |
| **Droits nécessaires** | Le rôle de la personne qui clique |
| **Dans la console** | Les clics, dans l'ordre |
| **Valeurs à saisir** | Exactement quoi mettre dans chaque champ |
| **En ligne de commande** | L'équivalent `gcloud` / API, pour aller plus vite ou scripter |
| **Vérifier** | Comment prouver que c'est actif |
| **Revenir en arrière** | Comment annuler sans casse |
| **Pièges** | Ce qui fait perdre une demi-journée |
| **Journal de bord** | Ce qu'il faut noter (sert à l'import Terraform) |

> **Trouver une page.** Les menus de la console changent souvent. Le plus fiable est la **barre de recherche** en haut
> de la console (🔎). Chaque étape donne le terme à taper, puis le chemin de menu habituel.
> **Toujours vérifier le projet** sélectionné en haut à gauche avant de cliquer.

---

## Sommaire

| # | Étape | Mesure | Rechercher | Qui | Réversible |
|---|---|---|---|---|---|
| 0 | [Préparer : variables, API, droits](#étape-0--préparer) | — | API et services | Plateforme | oui |
| 1 | [Journaux d'audit « accès aux données »](#étape-1--journaux-daudit-des-accès-aux-données) | §4 | Audit Logs | Plateforme | oui |
| 2 | [Templates Model Armor (+ modèle DLP France)](#étape-2--templates-model-armor--modèle-dlp-france) | §3 | Model Armor | Sécurité | oui |
| 3 | [Model Armor dans l'app Gemini Enterprise](#étape-3--model-armor-dans-lapp-gemini-enterprise) | §3 | Gemini Enterprise | Admin GE + sécurité | oui |
| 4 | [Plancher Model Armor + Agent Platform](#étape-4--plancher-model-armor--agent-platform-en-observation) | §1 §3 | Model Armor | Sécurité | oui |
| 5 | [Agent Registry et partage des agents](#étape-5--agent-registry-et-partage-des-agents) | §10 | Agent Registry | Plateforme + admin GE | oui |
| 6 | [Inventaire Shadow AI](#étape-6--inventaire-shadow-ai) | §2 | Asset Inventory | Sécurité | lecture seule |
| 7 | [Politiques d'organisation](#étape-7--politiques-dorganisation) | §2 | Règles d'administration | Cloud central | oui |
| 8 | [Access Transparency et Access Approval](#étape-8--access-transparency-et-access-approval) | §4 | Access Transparency / Access Approval | Cloud central + sécurité | oui |
| 9 | [Journaux dédiés et export SIEM](#étape-9--journaux-dédiés-et-export-siem) | §4 | Routeur de journaux | Plateforme | oui |
| 10 | [VPC Service Controls en dry-run](#étape-10--vpc-service-controls-en-dry-run) | §7 | VPC Service Controls | Cloud central | oui |
| 11 | [Security Command Center : AI Protection](#étape-11--security-command-center--ai-protection) | §2 | Security Command Center | Sécurité centrale | oui |
| — | [Récapitulatif et journal de bord](#récapitulatif--où-trouver-quoi) | | | | |

---

## Étape 0 : préparer

### Variables utilisées dans les commandes

À coller une fois dans le terminal (Cloud Shell convient très bien : 🔎 icône `>_` en haut à droite de la console).

```bash
export PROJECT_ID="acme-ge-recette"                       # projet Gemini Enterprise
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export APP_ID="acme-ge"                                   # ID de l'app GE (console GE → l'app → ID)
export GE_LOCATION="eu"                                        # localisation de l'app
export ORG_ID=$(gcloud projects get-ancestors $PROJECT_ID --format='value(id)' | tail -1)
export SECU_GROUP="securite-ia@acme.example"
gcloud config set project $PROJECT_ID
```

### API à activer

**Console :** 🔎 « API et services » → *Bibliothèque* → chercher chaque API → *Activer*.

| API (nom affiché) | Nom technique | Pourquoi |
|---|---|---|
| Discovery Engine API | `discoveryengine.googleapis.com` | Gemini Enterprise |
| Model Armor API | `modelarmor.googleapis.com` | Filtrage IA |
| Agent Platform API (ex-Vertex AI) | `aiplatform.googleapis.com` | Agents, appels Gemini, plancher |
| Agent Registry API | `agentregistry.googleapis.com` | Catalogue des agents |
| Cloud Asset API | `cloudasset.googleapis.com` | Inventaire Shadow AI |
| Cloud Data Loss Prevention (DLP) API | `dlp.googleapis.com` | Détecteurs France |
| Cloud Pub/Sub API | `pubsub.googleapis.com` | Export SIEM |

```bash
gcloud services enable discoveryengine.googleapis.com modelarmor.googleapis.com aiplatform.googleapis.com \
  agentregistry.googleapis.com cloudasset.googleapis.com dlp.googleapis.com pubsub.googleapis.com
```

### Comptes de service gérés par Google (à faire exister)

Gemini Enterprise et Model Armor agissent avec leurs propres comptes. Ils n'existent qu'après un premier usage :
on force leur création pour pouvoir leur donner des droits.

```bash
gcloud beta services identity create --service=discoveryengine.googleapis.com
gcloud beta services identity create --service=modelarmor.googleapis.com
# Comptes obtenus :
#   service-$PROJECT_NUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com   (Gemini Enterprise)
#   service-$PROJECT_NUMBER@gcp-sa-modelarmor.iam.gserviceaccount.com        (Model Armor)
```

### Droits de la personne qui active

| Étapes | Rôles projet | Rôles organisation |
|---|---|---|
| 1, 9 | Logging Admin, Security Reviewer, Project IAM Admin | — |
| 2, 4 | Model Armor Admin, DLP Administrator | — |
| 3, 5 | Gemini Enterprise Admin (`discoveryengine.admin`), Agent Registry Admin | — |
| 6 | — | Cloud Asset Viewer |
| 7 | — | Organization Policy Administrator |
| 8 | — | Access Transparency Admin, Access Approval Config Editor |
| 10 | — | Access Context Manager Admin |
| 11 | — | Security Center Admin |

En recette, *Owner* du projet suffit pour les étapes 1 à 6 et 9.

---

## Étape 1 : journaux d'audit des accès aux données

**Pourquoi.** Par défaut, Google ne journalise que l'**administration** (qui a créé ou modifié quoi). Les **usages**
(qui a interrogé Gemini Enterprise, qui a appelé un agent, qui a lu un secret) ne sont **pas** tracés. Sans eux,
aucune enquête n'est possible après un incident. C'est la première chose à activer, avant les utilisateurs.

**Droits nécessaires.** Project IAM Admin (ou Owner).

**Dans la console.**
1. 🔎 « Audit Logs » → *IAM et administration* → **Journaux d'audit**.
2. Dans le tableau *Configuration des journaux d'audit pour l'accès aux données*, filtrer et **cocher** la ligne de
   chaque service de la liste ci-dessous (plusieurs cases à la fois).
3. Dans le panneau de droite, onglet *Types de journaux* : cocher **Lecture de données** et **Écriture de données**.
   Laisser *Lecture d'administration* tel quel.
4. Cliquer sur **Enregistrer**.

**Valeurs à saisir.**

| Service (libellé console) | Lecture admin | Lecture de données | Écriture de données |
|---|---|---|---|
| Discovery Engine API (Gemini Enterprise) | — | ✅ | ✅ |
| Agent Platform API / Vertex AI API | — | ✅ | ✅ |
| Model Armor API | — | ✅ | ✅ |
| Secret Manager API | — | ✅ | ✅ |
| Agent Registry API | — | ✅ | ✅ |
| Cloud KMS | — | ❌ **ne pas cocher** | ❌ |

**En ligne de commande.** Pas de commande dédiée : les journaux d'audit sont une section de la politique IAM du projet.
À faire en console, ou en Terraform (phase 2). Pour lire la configuration actuelle :

```bash
gcloud projects get-iam-policy $PROJECT_ID --format=json | python3 -c \
  'import json,sys; [print(c["service"], [l["logType"] for l in c["auditLogConfigs"]]) for c in json.load(sys.stdin).get("auditConfigs",[])]'
```

**Vérifier.** Poser une question dans l'app, puis 🔎 « Logs Explorer », coller la requête et *Exécuter* :

```
logName:"cloudaudit.googleapis.com%2Fdata_access"
protoPayload.serviceName="discoveryengine.googleapis.com"
```

Une entrée apparaît en moins de 2 minutes, avec `protoPayload.authenticationInfo.principalEmail` = votre compte.

**Revenir en arrière.** Décocher les cases, *Enregistrer*. Les journaux déjà écrits restent.

**Pièges.**
- **KMS en lecture** : chaque déchiffrement (des milliers par heure) serait journalisé. Volume et coût inutiles.
- Le coût est au volume ingéré : quelques euros par mois pour un pilote de quelques centaines d'utilisateurs.
- Le service peut apparaître sous deux noms (*Agent Platform API* / *Vertex AI API*) : c'est le même (`aiplatform`).

**Journal de bord.** « Audit Data Read/Write sur discoveryengine, aiplatform, modelarmor, secretmanager, agentregistry ».
Terraform : `google_project_iam_audit_config.audit[...]`.

---

## Étape 2 : templates Model Armor (+ modèle DLP France)

**Pourquoi.** Model Armor est le pare-feu de l'IA : il analyse chaque question (injection de prompt, jailbreak, liens
malveillants, données sensibles, contenus dangereux) et chaque réponse. Un **template** est un jeu de règles. On en crée
deux : un pour les questions, un pour les réponses.

**Droits nécessaires.** Model Armor Admin, DLP Administrator.

### 2a. Le modèle DLP « données sensibles France »

Le filtre de données sensibles **de base** de Model Armor est orienté États-Unis : il ne reconnaît ni IBAN, ni NIR,
ni CNI. On crée donc d'abord un **modèle d'inspection DLP** avec les détecteurs français.

**Dans la console.**
1. 🔎 « Sensitive Data Protection » → *Sécurité* → **Sensitive Data Protection** → onglet **Configuration** →
   **Modèles** → onglet **Inspection** → **Créer un modèle**.
2. *Définir le modèle* :
   - Type de modèle : **Inspection**
   - ID du modèle : `ge-donnees-sensibles-fr`
   - Nom à afficher : `Gemini Enterprise - données sensibles FR/UE`
   - Type d'emplacement : **Multirégional** → **europe**
3. *Continuer* → *Configurer la détection* → **Gérer les infoTypes** → cocher la liste ci-dessous → *OK*.
4. *Seuil de confiance* (probabilité minimale) : **Probable**.
5. **Créer**.
6. 🔎 « IAM » → **Accorder l'accès** → compte principal :
   `service-NUMÉRO_PROJET@gcp-sa-modelarmor.iam.gserviceaccount.com` → rôles **DLP User** et **DLP Reader** → *Enregistrer*.
   (Cocher en haut à droite « Inclure les attributions de rôles fournies par Google » pour voir ce compte.)

**InfoTypes à cocher.**

| InfoType | Détecte |
|---|---|
| `FRANCE_NIR` | Numéro de sécurité sociale |
| `FRANCE_CNI` | Carte nationale d'identité |
| `FRANCE_PASSPORT` | Passeport français |
| `FRANCE_TAX_IDENTIFICATION_NUMBER` | Numéro fiscal |
| `IBAN_CODE` | IBAN |
| `CREDIT_CARD_NUMBER` | Carte bancaire |
| `GCP_CREDENTIALS`, `AUTH_TOKEN`, `PASSWORD` | Secrets techniques |

**En ligne de commande.**

```bash
curl -fsS -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://dlp.googleapis.com/v2/projects/$PROJECT_ID/locations/europe/inspectTemplates" -d '{
  "templateId": "ge-donnees-sensibles-fr",
  "inspectTemplate": {
    "displayName": "Gemini Enterprise - données sensibles FR/UE",
    "inspectConfig": {
      "minLikelihood": "LIKELY",
      "infoTypes": [{"name":"FRANCE_NIR"},{"name":"FRANCE_CNI"},{"name":"FRANCE_PASSPORT"},
                    {"name":"FRANCE_TAX_IDENTIFICATION_NUMBER"},{"name":"IBAN_CODE"},{"name":"CREDIT_CARD_NUMBER"},
                    {"name":"GCP_CREDENTIALS"},{"name":"AUTH_TOKEN"},{"name":"PASSWORD"}]
    }
  }
}'
for r in roles/dlp.user roles/dlp.reader; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --condition=None --role=$r \
    --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-modelarmor.iam.gserviceaccount.com"
done
```

### 2b. Les deux templates

**Dans la console.**
1. 🔎 « Model Armor » → *Sécurité* → **Model Armor** → onglet **Templates** → **Créer un template**.
2. Remplir selon le tableau, puis **Créer**. Recommencer pour le second template.

**Valeurs à saisir.**

| Champ | `ge-prompt-shield` (questions) | `ge-response-shield` (réponses) |
|---|---|---|
| ID du template | `ge-prompt-shield` | `ge-response-shield` |
| Région | **Multirégion → eu** | **eu** |
| Libellés | `app=acme-ge`, `owner=security` | idem |
| Détection d'URL malveillantes | ✅ | ✅ |
| Détection d'injection de prompt et de jailbreak | ✅ niveau **Moyen et supérieur** | ✅ Moyen et supérieur |
| Protection des données sensibles | **Avancée** → modèle d'inspection : `projects/PROJECT_ID/locations/europe/inspectTemplates/ge-donnees-sensibles-fr` | idem |
| IA responsable : haine, harcèlement, sexuellement explicite, dangereux | **Moyen et supérieur** pour les 4 | idem |
| Type d'application (*enforcement*) | **Inspecter et bloquer** | **Inspecter et bloquer** |
| Prise en charge multilingue | ✅ | ✅ |
| Journaliser les opérations de template | ✅ (qui modifie les règles) | ✅ |
| Journaliser les opérations d'assainissement | ❌ en production (contenu des questions ; décision DPO) ; ✅ en recette | idem |

**En ligne de commande.** L'API REST couvre tous les champs (la commande `gcloud model-armor templates create` ne
couvre pas le type d'application ni le multilingue) :

```bash
for T in ge-prompt-shield ge-response-shield; do
curl -fsS -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://modelarmor.eu.rep.googleapis.com/v1/projects/$PROJECT_ID/locations/eu/templates?templateId=$T" -d '{
  "labels": {"app": "acme-ge", "owner": "security"},
  "filterConfig": {
    "piAndJailbreakFilterSettings": {"filterEnforcement": "ENABLED", "confidenceLevel": "MEDIUM_AND_ABOVE"},
    "maliciousUriFilterSettings":   {"filterEnforcement": "ENABLED"},
    "raiSettings": {"raiFilters": [
      {"filterType": "HATE_SPEECH",       "confidenceLevel": "MEDIUM_AND_ABOVE"},
      {"filterType": "HARASSMENT",        "confidenceLevel": "MEDIUM_AND_ABOVE"},
      {"filterType": "SEXUALLY_EXPLICIT", "confidenceLevel": "MEDIUM_AND_ABOVE"},
      {"filterType": "DANGEROUS",         "confidenceLevel": "MEDIUM_AND_ABOVE"}]},
    "sdpSettings": {"advancedConfig": {
      "inspectTemplate": "projects/'$PROJECT_ID'/locations/europe/inspectTemplates/ge-donnees-sensibles-fr"}}
  },
  "templateMetadata": {
    "enforcementType": "INSPECT_AND_BLOCK",
    "logTemplateOperations": true,
    "logSanitizeOperations": false,
    "multiLanguageDetection": {"enableMultiLanguageDetection": true}
  }
}'; echo; done
```

**Vérifier.** Dans le template → onglet **Tester** (ou *Essayer*), ou en une commande :

```bash
cd ~/08-gemini-enterprise-securite-acme
TEMPLATE=projects/$PROJECT_ID/locations/eu/templates/ge-prompt-shield ./scripts/test_model_armor.sh
```

Attendu : question métier → `NO_MATCH_FOUND` ; jailbreak, IBAN, carte, URL de test → `MATCH_FOUND`.

**Revenir en arrière.** Supprimer le template (il ne doit plus être utilisé par l'app, étape 3).

**Pièges.**
- **Région** : app GE en `eu` → templates en **`eu`** (règle Google). Un template en `europe-west1` sera refusé par l'app.
- Erreur à la création « inspect template not found / permission » : le compte Model Armor n'a pas les rôles DLP (2a, point 6).
- Si le modèle DLP en `europe` est refusé avec un template `eu` : essayer un modèle DLP en `global`
  (point listé « à valider »).

**Journal de bord.** IDs des templates et du modèle DLP. Terraform : `google_model_armor_template.shield["ge-prompt-shield"]`,
`google_data_loss_prevention_inspect_template.fr[0]`.

---

## Étape 3 : Model Armor dans l'app Gemini Enterprise

**Pourquoi.** Les templates ne servent à rien tant que l'app ne les appelle pas. Cette étape branche le filtrage sur
**chaque** question et **chaque** réponse de l'assistant.

**Droits nécessaires.** Gemini Enterprise Admin (+ Project IAM Admin pour le rôle du compte GE).

**Dans la console.**
1. 🔎 « IAM » → **Accorder l'accès** → compte principal
   `service-NUMÉRO_PROJET@gcp-sa-discoveryengine.iam.gserviceaccount.com` → rôle **Model Armor User** → *Enregistrer*.
   **À faire en premier** : sans ce rôle, en mode fermé, **tout** est bloqué.
2. 🔎 « Gemini Enterprise » → cliquer sur le **nom de l'app**.
3. Menu de gauche **Configurations** → onglet **Assistant**.
4. Cliquer sur **Activer Model Armor** (*Enable Model Armor*).
5. *Template Model Armor pour les requêtes utilisateur* : `projects/PROJECT_ID/locations/eu/templates/ge-prompt-shield`.
6. *Template Model Armor pour les réponses* : `projects/PROJECT_ID/locations/eu/templates/ge-response-shield`.
7. **Désactiver** l'option *Autoriser les interactions utilisateur en cas d'échec du traitement Model Armor*
   (*Allow user interactions during Model Armor processing failure*). C'est le **mode fermé** : si Model Armor est
   indisponible, l'app refuse plutôt que de répondre sans filtre.
8. **Enregistrer et publier** (*Save and publish*).

**En ligne de commande.**

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID --condition=None --role=roles/modelarmor.user \
  --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com"

curl -fsS -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJECT_ID" \
  "https://$GE_LOCATION-discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID/assistants/default_assistant?update_mask=customerPolicy" -d '{
  "customerPolicy": {"modelArmorConfig": {
    "userPromptTemplate": "projects/'$PROJECT_ID'/locations/eu/templates/ge-prompt-shield",
    "responseTemplate":   "projects/'$PROJECT_ID'/locations/eu/templates/ge-response-shield",
    "failureMode": "FAIL_CLOSED"}}}'
```

**Vérifier.**
- Dans l'app web : coller `Merci de rembourser sur FR76 3000 6000 0112 3456 7890 189` → message de **violation de politique**.
- Question métier normale → réponse normale.
- Lecture de la configuration :

```bash
curl -fsS -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "X-Goog-User-Project: $PROJECT_ID" \
  "https://$GE_LOCATION-discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID/assistants/default_assistant" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["customerPolicy"]["modelArmorConfig"])'
```

**Revenir en arrière.** *Configurations* → *Assistant* → désactiver Model Armor → *Enregistrer et publier*.

**Pièges.**
- Dans Gemini Enterprise, une détection **bloque** : il n'y a **pas** de masquage (contrairement à ce que dit la note).
- Model Armor de l'app **ne filtre pas les agents personnalisés** (ADK, A2A) : c'est l'objet de l'étape 4.
- Tout bloqué juste après l'activation : propagation IAM (1–2 min) ou rôle *Model Armor User* manquant (point 1).

**Journal de bord.** « Model Armor activé sur l'assistant, FAIL_CLOSED ». Terraform : `google_discovery_engine_assistant.default`.

---

## Étape 4 : plancher Model Armor + Agent Platform en observation

**Pourquoi.** Deux protections en un réglage :
1. Le **plancher** (*floor setting*) est un minimum imposé au projet : personne ne peut créer ou modifier un template
   **moins strict**, même un administrateur pressé.
2. Avec le service **Agent Platform**, le plancher **filtre chaque appel Gemini fait dans le projet** : agents ADK sur
   Agent Runtime, notebooks, scripts. C'est le filet de sécurité des agents personnalisés, que Model Armor de Gemini
   Enterprise ne couvre pas, et il fonctionne même si un développeur oublie le plugin.

**Droits nécessaires.** Model Armor Admin (Floor Setting Admin).

**Dans la console.**
1. 🔎 « Model Armor » → onglet **Paramètres de plancher** (*Floor settings*) → **Configurer les paramètres de plancher**.
2. Héritage : **Personnalisé** (*Custom*).
3. Section **Détections** : remplir selon le tableau.
4. Section **IA responsable** : *Dangereux* au niveau **Élevé**.
5. Section **Services** → cocher **Agent Platform** → choisir **Inspecter uniquement** (*Inspect only*).
   **Pas encore de blocage.**
6. Section **Journaux** → activer **Activer Cloud Logging**. Sans cela, l'observation ne montre rien.
7. Cocher **Activer la prise en charge multilingue**.
8. **Enregistrer les paramètres de plancher**. L'activation prend quelques minutes.

**Valeurs à saisir.**

| Champ | Valeur | Pourquoi ce niveau |
|---|---|---|
| Application du plancher | Activée | Sinon le plancher n'est qu'indicatif |
| Injection de prompt et jailbreak | Activé, **Élevé** | Minimum absolu ; les templates sont plus stricts (Moyen) |
| URL malveillantes | Activé | |
| IA responsable : Dangereux | **Élevé** | Minimum commun à tous les usages du projet |
| Services → Agent Platform | **Inspecter uniquement** (2 semaines), puis **Inspecter et bloquer** | Observer avant de bloquer |
| Cloud Logging | Activé | Voir ce qui **aurait** été bloqué |

**En ligne de commande.**

```bash
curl -fsS -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
  "https://modelarmor.googleapis.com/v1/projects/$PROJECT_ID/locations/global/floorSetting" -d '{
  "enableFloorSettingEnforcement": true,
  "filterConfig": {
    "piAndJailbreakFilterSettings": {"filterEnforcement": "ENABLED", "confidenceLevel": "HIGH"},
    "maliciousUriFilterSettings":   {"filterEnforcement": "ENABLED"},
    "raiSettings": {"raiFilters": [{"filterType": "DANGEROUS", "confidenceLevel": "HIGH"}]}
  },
  "integratedServices": ["AI_PLATFORM"],
  "aiPlatformFloorSetting": {"inspectOnly": true, "enableCloudLogging": true},
  "floorSettingMetadata": {"multiLanguageDetection": {"enableMultiLanguageDetection": true}}
}'
```

**Vérifier.**
1. Lecture : `curl -fsS -H "Authorization: Bearer $(gcloud auth print-access-token)" https://modelarmor.googleapis.com/v1/projects/$PROJECT_ID/locations/global/floorSetting`
   → `integratedServices: ["AI_PLATFORM"]`, `inspectOnly: true`.
2. Le plancher fonctionne : dans *Templates*, modifier `ge-prompt-shield` et **désactiver** l'injection/jailbreak →
   la sauvegarde est **refusée** (« less strict than floor »). Annuler.
3. Pendant 2 semaines, 🔎 « Logs Explorer » :

```
jsonPayload.@type="type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry"
jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"
```

Chaque résultat est un appel qui **aurait** été bloqué. Faux positif ? On ajuste. Puis bascule en
**Inspecter et bloquer** (phase 2 : `armor_agent_platform_mode = "block"`).

**Revenir en arrière.** Section *Services* → décocher *Agent Platform* ; ou *Héritage* → **Désactiver**.

**Pièges.**
- La journalisation Cloud Logging du plancher contient les prompts : la limiter à la période d'observation si le DPO
  le demande.
- Le plancher est au niveau **projet** ici. L'équipe Cloud centrale peut aussi en poser un au niveau dossier ou organisation :
  dans ce cas, choisir *Hériter* si celui du parent est au moins aussi strict.

**Journal de bord.** « Plancher personnalisé, Agent Platform en inspect ». Terraform : `google_model_armor_floorsetting.project`.

---

## Étape 5 : Agent Registry et partage des agents

**Pourquoi.** Un seul catalogue officiel des agents, serveurs MCP et API. Ce qui n'y est pas n'est pas gouverné, donc
c'est du Shadow AI. Avec Agent Gateway (phase 2), ce qui n'y est pas n'est même **pas joignable**. Et on évite qu'un
utilisateur diffuse à toute l'entreprise un agent non revu.

**Droits nécessaires.** Agent Registry Admin, Project IAM Admin, Gemini Enterprise Admin.

**Dans la console.**
1. 🔎 « Agent Registry » (menu *Agent Platform*). Vérifier que les agents **Agent Runtime** existants apparaissent :
   ils s'enregistrent automatiquement.
2. Pour chaque serveur MCP sur Cloud Run (ex. projet 04) : **Enregistrer** → type **Serveur MCP** → nom, description,
   URL `https://…run.app/mcp` → *Créer*.
3. 🔎 « IAM » → **Accorder l'accès** :
   - groupe développeurs d'agents → **Agent Registry API Editor** ;
   - groupe utilisateurs Gemini Enterprise → **Agent Registry API Viewer**.
4. 🔎 « Gemini Enterprise » → l'app → **Configurations** → onglet des **fonctionnalités** (*Feature management*) :
   - **désactiver le partage d'agents** entre utilisateurs ;
   - **partage des compétences (skills)** : soumis à **approbation d'un administrateur** ;
   - *Enregistrer et publier*.

**En ligne de commande.**

```bash
gcloud agent-registry agents list --location=global                 # agents connus
gcloud agent-registry mcp-servers list --location=global            # serveurs MCP connus
gcloud projects add-iam-policy-binding $PROJECT_ID --condition=None \
  --role=roles/agentregistry.editor --member="group:gcp-ia-developpeurs@acme.example"
gcloud projects add-iam-policy-binding $PROJECT_ID --condition=None \
  --role=roles/agentregistry.viewer --member="group:gemini-utilisateurs@acme.example"
```

L'enregistrement d'un serveur MCP en ligne de commande est détaillé dans le projet 04
(`gcloud agent-registry services create … --mcp-server-spec-type=…`).

**Vérifier.** Les listes ci-dessus contiennent tous les agents et MCP en service. Un utilisateur test ne voit plus
l'option de partage d'un agent dans l'app.

**Revenir en arrière.** Retirer les rôles ; réactiver le partage dans *Configurations*.

**Pièges.** Les serveurs MCP sur Cloud Run doivent rester **privés** (pas `allUsers`) : Gemini Enterprise les appelle avec
son propre compte (`run.invoker` donné au compte `gcp-sa-discoveryengine`).

**Journal de bord.** Liste des agents et MCP enregistrés. Terraform : `google_project_iam_member.registry_*`,
`google_discovery_engine_search_engine.app` (fonctionnalités).

---

## Étape 6 : inventaire Shadow AI

**Pourquoi.** On ne protège pas ce qu'on ne connaît pas. Cloud Asset Inventory voit **toutes** les ressources de
l'organisation, sans agent à installer : agents, endpoints de modèles, services Cloud Run, apps Gemini Enterprise.

**Droits nécessaires.** Cloud Asset Viewer sur l'organisation (ou le dossier).

**Dans la console.**
1. Sélecteur en haut à gauche → choisir l'**organisation** (pas un projet).
2. 🔎 « Asset Inventory » → *IAM et administration* → **Inventaire des éléments** → onglet **Ressources**.
3. Filtre *Type de ressource* : `aiplatform.googleapis.com/ReasoningEngine`, `aiplatform.googleapis.com/Endpoint`,
   `run.googleapis.com/Service`, `discoveryengine.googleapis.com/Engine`.
4. Onglet **Stratégie IAM** → rechercher `allUsers` puis `allAuthenticatedUsers` : ce sont les ressources **publiques**.
5. **Exporter** (bouton en haut) en CSV.

**En ligne de commande (recommandé).**

```bash
./scripts/shadow_ai_inventory.sh organizations/$ORG_ID
# -> shadow-ai-AAAA-MM-JJ/ressources.csv, publiques.csv, sans-owner.csv
```

**Vérifier / exploiter.** Pour chaque ligne : est-elle dans Agent Registry ? a-t-elle un propriétaire (label `owner`) ?
est-elle publique ? Sinon : régulariser (identité dédiée, Model Armor, registre, CI) ou arrêter.

**Revenir en arrière.** Lecture seule : rien à annuler.

**Pièges.** La quarantaine réseau demandée par la note est une décision d'organisation (hors app) : l'inventaire
fournit la liste, la décision revient à la sécurité centrale.

**Journal de bord.** Fichiers CSV datés, archivés chaque mois.

---

## Étape 7 : politiques d'organisation

**Pourquoi.** Empêcher coûte moins cher que détecter. Trois règles ferment les portes les plus courantes du Shadow AI :
un service ouvert à Internet, un droit donné à n'importe qui, une ressource hors UE.

**Droits nécessaires.** Organization Policy Administrator (souvent : équipe Cloud centrale).

**Dans la console.**
1. Sélectionner le **projet** (test) — plus tard le dossier IA.
2. 🔎 « Règles d'administration » (*Organization policies*) → *IAM et administration*.
3. Chercher la contrainte (tableau) → cliquer → **Gérer la règle**.
4. *S'applique à* : **Remplacer la règle du parent** (*Override parent's policy*).
5. *Règles* → **Ajouter une règle** → *Valeurs de règle* : **Personnalisées** → *Type* : **Autoriser** → saisir la valeur.
6. **Tester les modifications** (simulateur, si proposé) → **Définir la règle**.

| Contrainte (nom affiché) | ID | Valeur autorisée | Effet |
|---|---|---|---|
| Allowed ingress settings (Cloud Run) | `run.allowedIngress` | `internal-and-cloud-load-balancing` | Aucun Cloud Run ouvert directement à Internet |
| Domain restricted sharing | `iam.allowedPolicyMemberDomains` | ID client Workspace (`C0xxxxxxx`) | Impossible de donner un droit à `allUsers` ou à un compte externe |
| Resource Location Restriction | `gcp.resourceLocations` | `in:eu-locations` | Aucune ressource hors UE |

L'ID client Workspace se trouve dans la console d'administration Google : *Compte* → *Paramètres du compte* → *ID client*.

**En ligne de commande.**

```bash
cat > run-ingress.yaml <<EOF
name: projects/$PROJECT_ID/policies/run.allowedIngress
spec:
  rules:
  - values:
      allowedValues: ["internal-and-cloud-load-balancing"]
EOF
gcloud org-policies set-policy run-ingress.yaml
gcloud org-policies describe run.allowedIngress --project=$PROJECT_ID --effective
```

(Même fichier pour les deux autres, en changeant le nom et la valeur.)

**Vérifier.** Tenter `gcloud run services add-iam-policy-binding <service> --member=allUsers --role=roles/run.invoker`
sur un service de test → **refusé**.

**Revenir en arrière.** *Gérer la règle* → **Hériter de la règle du parent**, ou `gcloud org-policies reset <contrainte> --project=$PROJECT_ID`.

**Pièges.**
- Vérifier avec l'équipe Cloud centrale que ces règles **n'existent pas déjà** au niveau organisation (ne pas les dupliquer).
- `iam.allowedPolicyMemberDomains` bloque aussi les partages externes légitimes : recenser les exceptions avant.
- Les services Cloud Run appelés par Gemini Enterprise restent joignables : ils sont privés et autorisés par IAM.

**Journal de bord.** Contraintes posées et niveau. Terraform : `google_org_policy_policy.guardrails[...]`.

---

## Étape 8 : Access Transparency et Access Approval

**Pourquoi.** **Access Transparency** journalise chaque accès d'un ingénieur Google à vos données (support, incident).
**Access Approval** va plus loin : l'accès **attend votre accord**. Gemini Enterprise, Agent Runtime, Model Armor et Cloud KMS
sont couverts (GA).

**Droits nécessaires.** Organisation : Access Transparency Admin. Projet : Access Approval Config Editor.
**Prérequis :** support Google Cloud **Enhanced** ou **Premium**.

**Dans la console.**
1. **Access Transparency** (une fois pour l'organisation) : sélectionner l'**organisation** → 🔎 « Paramètres IAM »
   (*IAM et administration* → **Paramètres**) → **Activer Access Transparency pour l'organisation**.
2. **Access Approval** (projet) : sélectionner le **projet** → 🔎 « Access Approval » → **Enrôler** →
   *Services* : **Tous les services éligibles** → *E-mails de notification* : boîte de l'équipe sécurité → *Enregistrer*.
3. 🔎 « IAM » : donner **Access Approval Approver** à **2 personnes** de l'équipe sécurité minimum.

**En ligne de commande.**

```bash
gcloud access-approval settings update --project=$PROJECT_ID \
  --enrolled_services=all --notification_emails="$SECU_GROUP"
gcloud access-approval settings get --project=$PROJECT_ID
```

**Vérifier.** `settings get` affiche `enrolledServices: all`. Logs Explorer (souvent vide, c'est bon signe) :

```
logName:"cloudaudit.googleapis.com%2Faccess_transparency"
```

**Revenir en arrière.** `gcloud access-approval settings delete --project=$PROJECT_ID`.

**Pièges.** Une demande non traitée **retarde** le support Google pendant un incident : prévoir l'astreinte des approbateurs.

**Journal de bord.** Date d'activation AxT, approbateurs. Terraform : `google_project_access_approval_settings.this[0]`.

---

## Étape 9 : journaux dédiés et export SIEM

**Pourquoi.** Les journaux d'usage contiennent des **questions de salariés** : ils ne doivent pas rester dans le bucket
par défaut, lisible par beaucoup de monde. Les journaux de sécurité doivent être gardés **un an** en UE et partir
**en temps réel** vers le SOC.

> **Raccourci accepté :** ces réglages sont nombreux et Terraform les fait mieux. Il est acceptable de faire **seulement
> l'étape 1** en phase 1 et de laisser cette étape au palier A/B de la phase 2.

**Droits nécessaires.** Logging Admin, Pub/Sub Admin.

**Dans la console.**
1. 🔎 « Stockage des journaux » (*Logging* → **Stockage des journaux**) → **Créer un bucket de journaux** :
   - `ge-security`, région **eu**, conservation **365 jours**, **Mettre à niveau pour utiliser Log Analytics** coché ;
   - `ge-usage`, région **eu**, conservation **90 jours**, Log Analytics coché.
2. 🔎 « Routeur de journaux » (*Log Router*) → **Créer un récepteur** :
   - `ge-security-logs` → destination *Bucket Cloud Logging* → `ge-security` → filtre d'inclusion : celui de
     `terraform/80_logging.tf` (`security_log_filter`) ;
   - `ge-usage-logs` → `ge-usage` → filtre `usage_log_filter`.
3. Récepteur **`_Default`** → *Modifier* → **Ajouter une exclusion** → nom `ge-usage`, filtre = celui de `ge-usage-logs`.
4. **SIEM** : 🔎 « Pub/Sub » → **Créer un sujet** `ge-security-siem` (conservation des messages 7 jours) → créer un
   **abonnement** pull `ge-security-siem-pull`. Puis un récepteur `ge-security-to-siem` → destination **Sujet Cloud Pub/Sub**
   → filtre = celui de `ge-security`.
5. Copier l'**identité du rédacteur** (*writer identity*) affichée par ce récepteur → sur le sujet, **Ajouter un compte
   principal** → rôle **Diffuseur Pub/Sub** (*Pub/Sub Publisher*).
6. Donner au compte du connecteur SIEM le rôle **Abonné Pub/Sub** sur l'abonnement.

**En ligne de commande.**

```bash
gcloud logging buckets create ge-security --location=eu --retention-days=365 --enable-analytics
gcloud logging buckets create ge-usage    --location=eu --retention-days=90  --enable-analytics

USAGE='logName="projects/'$PROJECT_ID'/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity" OR logName=~"projects/'$PROJECT_ID'/logs/discoveryengine.googleapis.com%2Fgen_ai\."'
gcloud logging sinks create ge-usage-logs \
  logging.googleapis.com/projects/$PROJECT_ID/locations/eu/buckets/ge-usage --log-filter="$USAGE"
gcloud logging sinks update _Default --add-exclusion=name=ge-usage,filter="$USAGE"

gcloud pubsub topics create ge-security-siem --message-retention-duration=7d
gcloud pubsub subscriptions create ge-security-siem-pull --topic=ge-security-siem --expiration-period=never
gcloud logging sinks create ge-security-to-siem pubsub.googleapis.com/projects/$PROJECT_ID/topics/ge-security-siem \
  --log-filter='logName:"cloudaudit.googleapis.com" AND protoPayload.serviceName=("discoveryengine.googleapis.com" OR "modelarmor.googleapis.com" OR "aiplatform.googleapis.com" OR "cloudkms.googleapis.com" OR "secretmanager.googleapis.com")'
WRITER=$(gcloud logging sinks describe ge-security-to-siem --format='value(writerIdentity)')
gcloud pubsub topics add-iam-policy-binding ge-security-siem --member="$WRITER" --role=roles/pubsub.publisher
```

**Vérifier.**
- Logs Explorer → *Affiner la portée* → *Stockage* → `_Default` : **aucune** entrée `gemini_enterprise_user_activity`.
  Même requête sur `ge-usage` : les entrées sont là.
- `gcloud pubsub subscriptions pull ge-security-siem-pull --limit=3 --auto-ack` : des messages arrivent.

**Revenir en arrière.** Supprimer les récepteurs (les buckets se suppriment après 7 jours de délai).

**Pièges.**
- Oublier le droit *Pub/Sub Publisher* du rédacteur : le récepteur est créé mais **rien** n'arrive.
- Un bucket **verrouillé** ne peut plus être raccourci ni supprimé : ne verrouiller qu'en production (phase 2).

**Journal de bord.** Noms des buckets, récepteurs, sujet. Terraform : `google_logging_project_bucket_config.*`,
`google_logging_project_sink.*`, `google_pubsub_topic.siem[0]`.

---

## Étape 10 : VPC Service Controls en dry-run

**Pourquoi.** VPC-SC est l'anti-exfiltration : même avec des identifiants volés, on ne peut pas copier les données
hors du périmètre. En **dry-run**, rien n'est bloqué : on voit seulement ce qui **le serait**.

**Droits nécessaires.** Access Context Manager Admin (organisation), donc souvent l'équipe Cloud centrale.

**Dans la console.**
1. Sélectionner l'**organisation**.
2. **Niveau d'accès** : 🔎 « Access Context Manager » → **Créer un niveau d'accès** :
   - titre `acme_corporate` ;
   - *Conditions* → **Sous-réseaux IP** → IP publiques de sortie Acme (proxy, VPN), ex. `203.0.113.0/24` ;
   - *Enregistrer*.
3. **Périmètre** : 🔎 « VPC Service Controls » → vérifier que le **mode simulation** (*Dry run mode*) est sélectionné en
   haut → **Nouveau périmètre** :
   - titre `gemini_enterprise_<projet>`, type **Standard** ;
   - *Projets* → ajouter le projet Gemini Enterprise ;
   - *Services restreints* → ajouter les 7 services ci-dessous ;
   - *Niveaux d'accès* → `acme_corporate` ;
   - **Créer un périmètre**.
4. Observer **2 semaines** (requête ci-dessous), corriger chaque violation légitime, puis passer en appliqué (phase 2).

**Services restreints.** `discoveryengine.googleapis.com`, `aiplatform.googleapis.com`, `agentregistry.googleapis.com`,
`modelarmor.googleapis.com`, `dlp.googleapis.com`, `cloudkms.googleapis.com`, `secretmanager.googleapis.com`.

**En ligne de commande.**

```bash
POLICY=$(gcloud access-context-manager policies list --organization=$ORG_ID --format='value(name)')
cat > level.yaml <<'EOF'
- ipSubnetworks:
  - 203.0.113.0/24
EOF
gcloud access-context-manager levels create acme_corporate --policy=$POLICY \
  --title=acme_corporate --basic-level-spec=level.yaml

gcloud access-context-manager perimeters dry-run create gemini_enterprise --policy=$POLICY \
  --perimeter-title=gemini_enterprise --perimeter-type=regular \
  --perimeter-resources=projects/$PROJECT_NUMBER \
  --perimeter-restricted-services=discoveryengine.googleapis.com,aiplatform.googleapis.com,agentregistry.googleapis.com,modelarmor.googleapis.com,dlp.googleapis.com,cloudkms.googleapis.com,secretmanager.googleapis.com \
  --perimeter-access-levels=acme_corporate
```

**Vérifier.** Depuis un réseau **hors** Acme (partage 4G), ouvrir l'app, puis Logs Explorer :

```
protoPayload.metadata.@type="type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata"
protoPayload.metadata.dryRun=true
```

Une violation **journalisée**, mais l'accès a fonctionné : c'est le comportement attendu du dry-run.

**Revenir en arrière.** Supprimer le périmètre en dry-run (aucun effet sur le trafic).

**Pièges.**
- L'interface de Gemini Enterprise passe par `discoveryengine` : **sans niveau d'accès**, un périmètre appliqué **bloque
  les utilisateurs**.
- Créer les **connecteurs avant** d'appliquer le périmètre.
- Ne **jamais** passer en appliqué depuis la console sans revue : c'est la PR de la phase 2 qui le fait
  (`gcloud access-context-manager perimeters dry-run enforce` en dernier recours, avec la sécurité).

**Journal de bord.** Nom de la politique, du niveau et du périmètre. Terraform :
`google_access_context_manager_access_level.corporate[0]`, `google_access_context_manager_service_perimeter.ge[0]`.

---

## Étape 11 : Security Command Center : AI Protection

**Pourquoi.** Vue consolidée des risques IA de l'organisation : inventaire des modèles et agents, données sensibles exposées,
menaces détectées. C'est l'alternative native à l'AI-SPM de Wiz citée par la note.

**Droits nécessaires.** Security Center Admin (organisation). **Prérequis :** SCC **Enterprise** ou **Premium** (coût :
décision de la sécurité centrale).

**Dans la console.**
1. Sélectionner l'**organisation** → 🔎 « Security Command Center ».
2. Si SCC n'est pas activé : *Démarrer* → choisir le niveau → suivre l'assistant (décision centrale).
3. Menu **AI Protection** (ou *Risques → Sécurité de l'IA* selon la version) → consulter l'inventaire IA et les
   résultats (*findings*).
4. *Paramètres* → **Notifications** : envoyer les résultats « critiques » et « élevés » vers le sujet Pub/Sub du SOC.

**Vérifier.** Les agents Agent Runtime et l'app Gemini Enterprise apparaissent dans l'inventaire IA.

**Pièges.** Si **Wiz** est déjà le standard Acme, le connecter au projet suffit : pas besoin des deux.

**Journal de bord.** Niveau SCC, date, destination des notifications. (Pas de Terraform dans ce projet : réglage organisation.)

---

## Récapitulatif : où trouver quoi

| Je cherche | 🔎 Taper | Menu | Niveau |
|---|---|---|---|
| Activer les journaux d'accès | Audit Logs | IAM et administration → Journaux d'audit | Projet |
| Lire les journaux | Logs Explorer | Logging → Explorateur de journaux | Projet |
| Requêtes SQL sur les journaux | Log Analytics | Logging → Log Analytics | Projet |
| Buckets, récepteurs, exclusions | Routeur de journaux | Logging → Routeur / Stockage | Projet |
| Modèle DLP France | Sensitive Data Protection | Sécurité → SDP → Configuration → Modèles | Projet |
| Templates et plancher | Model Armor | Sécurité → Model Armor | Projet |
| Réglages de sécurité de l'app | Gemini Enterprise | App → Configurations | Projet |
| Agents et outils déclarés | Agent Registry | Agent Platform → Agent Registry | Projet |
| Agents déployés | Agent Runtime | Agent Platform → Déploiements | Projet |
| Toutes les ressources | Asset Inventory | IAM et administration → Inventaire | Org |
| Règles d'organisation | Règles d'administration | IAM et administration | Projet / org |
| Accès de Google | Access Transparency, Access Approval | IAM → Paramètres ; Sécurité | Org / projet |
| Niveaux d'accès | Access Context Manager | Sécurité | Org |
| Périmètre anti-exfiltration | VPC Service Controls | Sécurité | Org |
| Alertes et canaux | Alerting | Monitoring → Alertes | Projet |
| Clés de chiffrement | Key Management | Sécurité → KMS | Projet |
| Risques IA consolidés | Security Command Center | Sécurité | Org |

## Modèle de journal de bord

| Date | Qui | Étape | Action exacte | Valeur / ID créé | Preuve | Adresse Terraform à importer |
|---|---|---|---|---|---|---|
| 2026-10-06 | J. D. (plateforme) | 1 | Audit Data Read/Write | discoveryengine, aiplatform, modelarmor, secretmanager, agentregistry | capture | `google_project_iam_audit_config.audit["…"]` |
| 2026-10-06 | S. M. (sécurité) | 2 | Template créé | `projects/…/locations/eu/templates/ge-prompt-shield` | test MATCH_FOUND | `google_model_armor_template.shield["ge-prompt-shield"]` |
| | | 4 | Plancher, Agent Platform inspect | `projects/…/locations/global/floorSetting` | lecture API | `google_model_armor_floorsetting.project` |

**Fin de la phase 1 :** les étapes 1 à 5 faites, `./scripts/test_model_armor.sh` au vert, le journal de bord rempli.
On passe à la [phase 2](phase2-terraform/README.md).
