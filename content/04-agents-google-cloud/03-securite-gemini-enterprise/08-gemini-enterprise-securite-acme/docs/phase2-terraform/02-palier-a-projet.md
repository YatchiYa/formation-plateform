# 02. Palier A : le projet (aucun prérequis organisation)

**Pour qui :** DevOps (PR), sécurité (revue). **Mesures :** §1, §2 (détection), §3, §4 (audit), §10.
**Prérequis :** droits sur le projet, fiche [01](01-preparer-et-importer.md) faite.

---

## 1. Ce que le palier apporte

| Ajout | Fichier | Mesure | Effet |
|---|---|---|---|
| Socle 06 complet | `00` à `80` | toutes | Identité, CMEK, connecteurs, Model Armor sur l'app, journaux |
| Audit élargi | `70_detection.tf` | §4 | Les appels aux agents (`aiplatform`) et au catalogue (`agentregistry`) sont tracés |
| Plancher sur Agent Platform | `30_ai_guardrails.tf` | §1 §3 | Chaque appel Gemini du projet passe par Model Armor (observation, puis blocage) |
| Droits Agent Registry | `90_agents_registry.tf` | §10 | Utilisateurs en lecture, développeurs en publication |
| Alerte Shadow AI | `75_shadow_ai.tf` | §2 | E-mail si un service devient public ou si un agent est créé/modifié |
| Agent exemple (option) | `90_agents_registry.tf` | §1 §9 | Modèle à suivre par les développeurs |

## 2. Les variables

```hcl
# terraform.tfvars
armor_agent_platform_mode = "inspect"                              # 2 semaines, puis "block"
agent_developer_groups    = ["group:gcp-ia-developpeurs@acme.example"]
deploy_secure_agent       = false                                  # true pour l'agent exemple
alert_email               = "securite-ia@acme.example"            # reçoit les alertes
```

## 3. Le code, expliqué

### 3.1 Le plancher étendu aux agents (`30_ai_guardrails.tf`)

```hcl
resource "google_model_armor_floorsetting" "project" {
  parent                           = "projects/${var.project_id}"
  location                         = "global"
  enable_floor_setting_enforcement = true

  integrated_services = var.armor_agent_platform_mode == "off" ? [] : ["AI_PLATFORM"]

  dynamic "ai_platform_floor_setting" {
    for_each = var.armor_agent_platform_mode == "off" ? [] : [1]
    content {
      inspect_only         = var.armor_agent_platform_mode == "inspect"
      inspect_and_block    = var.armor_agent_platform_mode == "block"
      enable_cloud_logging = true
    }
  }
  # filter_config : injection/jailbreak HIGH, URL malveillantes, Dangereux HIGH (inchangé depuis le 06)
}
```

**Pourquoi.** Model Armor de Gemini Enterprise ne filtre **pas** les agents personnalisés. Le plancher avec
`AI_PLATFORM` filtre **chaque appel Gemini** du projet, que l'agent ait ou non son plugin. Deux protections
indépendantes : si l'une est oubliée, l'autre tient.

**Pourquoi `inspect` d'abord.** Un blocage à l'aveugle peut casser un agent en production. Deux semaines
d'observation montrent les faux positifs réels.

### 3.2 L'audit élargi (`70_detection.tf`)

```hcl
resource "google_project_iam_audit_config" "audit" {
  for_each = toset(["discoveryengine.googleapis.com", "modelarmor.googleapis.com", "secretmanager.googleapis.com",
                    "aiplatform.googleapis.com", "agentregistry.googleapis.com"])
  project  = var.project_id
  service  = each.value
  audit_log_config { log_type = "DATA_READ" }
  audit_log_config { log_type = "DATA_WRITE" }
}
```

La note exige explicitement les journaux d'accès de Vertex AI (`aiplatform`). Pas de KMS en lecture (volume).

### 3.3 Le catalogue (`90_agents_registry.tf`)

```hcl
resource "google_project_iam_member" "registry_viewers" {
  for_each = toset(var.user_groups)            # tous les utilisateurs GE voient le catalogue
  role     = "roles/agentregistry.viewer"
  member   = each.value
  project  = var.project_id
}
resource "google_project_iam_member" "registry_editors" {
  for_each = toset(var.agent_developer_groups) # seuls les développeurs publient
  role     = "roles/agentregistry.editor"
  member   = each.value
  project  = var.project_id
}
```

### 3.4 L'alerte Shadow AI (`75_shadow_ai.tf`)

Une **métrique basée sur les journaux** compte les événements suspects ; une **règle d'alerte** envoie un e-mail
dès qu'il y en a un :

```hcl
filter = <<-EOT
  logName:"cloudaudit.googleapis.com%2Factivity"
  (
    (protoPayload.methodName=~"SetIamPolicy" AND protoPayload.serviceName="run.googleapis.com"
      AND (protoPayload.request.policy.bindings.members:"allUsers" OR protoPayload.request.policy.bindings.members:"allAuthenticatedUsers"))
    OR (protoPayload.serviceName="aiplatform.googleapis.com" AND protoPayload.methodName=~"ReasoningEngineService.(Create|Update)ReasoningEngine")
    OR (protoPayload.serviceName="agentregistry.googleapis.com" AND protoPayload.methodName=~"(Create|Update|Delete)")
  )
EOT
```

Les déploiements faits par la CI alertent aussi : **c'est voulu**. La sécurité vérifie qu'une PR correspond.
Les politiques d'organisation du même fichier (qui **empêchent**) sont au palier C.

## 4. Appliquer

```bash
git checkout -b palier-a
# modifier terraform.tfvars (dans le dépôt des tfvars de l'environnement, ou variables de la CI)
terraform plan -out=tfplan
```

**Plan attendu (projet déjà doté du socle 06) :**

```
~ google_model_armor_floorsetting.project            integrated_services, ai_platform_floor_setting
+ google_project_iam_audit_config.audit["aiplatform.googleapis.com"]
+ google_project_iam_audit_config.audit["agentregistry.googleapis.com"]
+ google_project_iam_member.registry_viewers[...]
+ google_project_iam_member.registry_editors[...]
+ google_logging_metric.shadow_ai
+ google_monitoring_alert_policy.shadow_ai
+ google_project_service.apis["aiplatform.googleapis.com"] (+ agentregistry, cloudasset)
Plan: N to add, 1 to change, 0 to destroy.
```

Aucun `-` ni `-/+`. PR → revue sécurité → apply par la CI.

## 5. Vérifier

```bash
PROJECT_ID=... APP_ID=... ./scripts/verify_controls.sh
# OK   §1    Plancher étendu aux appels Gemini du projet (agents)
# OK   §4    Journaux d'accès aux données : discoveryengine, aiplatform, modelarmor
# OK   §10   Agent Registry activé
```

Puis les tests T07, T09, T19 du [plan de tests](../03-plan-de-tests.md).

## 6. Deux semaines plus tard : passer en blocage

1. Revue des journaux du plancher (requête dans [docs/04](../04-exploitation-journaliere.md)) : aucun faux positif
   bloquant, ou faux positifs corrigés.
2. PR d'**une ligne** :

```hcl
armor_agent_platform_mode = "block"
```

3. Plan attendu : **une seule** modification, `~ google_model_armor_floorsetting.project` (`inspect_only` → false,
   `inspect_and_block` → true).
4. Test T10 : un jailbreak envoyé directement à Gemini dans le projet est **bloqué**.

## 7. Revenir en arrière

`armor_agent_platform_mode = "inspect"` (ou `"off"`), PR, apply. Effet en quelques minutes.
