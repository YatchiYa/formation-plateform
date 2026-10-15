# 04. Palier C : réglages d'organisation

**Pour qui :** DevOps (PR) **avec l'équipe Cloud centrale**, sécurité (revue). **Mesures :** §2 (empêcher), §4 (Access
Approval), §7 (VPC-SC).
**Prérequis :** rôles organisation pour le compte de la CI (`orgpolicy.policyAdmin`, `accesscontextmanager.policyAdmin`,
`accessapproval.configEditor`) ; Access Transparency activé sur l'organisation ; ID client Workspace ; IP de sortie Acme.

> **Avant tout :** demander à l'équipe Cloud centrale ce qui existe **déjà** au niveau organisation ou dossier
> (politiques, périmètres, Access Approval). Ne pas dupliquer : retirer la variable correspondante.
> Ce palier peut se découper en trois PR (politiques, Access Approval, VPC-SC).

---

## 1. Les variables

```hcl
enforce_org_policies   = true
workspace_customer_id  = "C0xxxxxxx"              # Admin console Google → Compte → Paramètres du compte
vpc_sc_access_policy   = "123456789012"           # gcloud access-context-manager policies list --organization=ORG
corporate_ip_ranges    = ["203.0.113.0/24"]       # IP publiques de sortie Acme (proxy, VPN)
vpc_sc_enforce         = false                    # dry-run d'abord
access_approval_emails = ["securite-gcp@acme.example"]
```

---

## 2. Politiques d'organisation (`75_shadow_ai.tf`), mesure §2

```hcl
locals {
  org_policies = var.enforce_org_policies ? merge(
    {
      "run.allowedIngress"    = ["internal-and-cloud-load-balancing"]  # pas de Cloud Run ouvert à Internet
      "gcp.resourceLocations" = ["in:eu-locations"]                    # rien hors UE
    },
    var.workspace_customer_id != "" ? { "iam.allowedPolicyMemberDomains" = [var.workspace_customer_id] } : {},  # pas de allUsers
  ) : {}
}

resource "google_org_policy_policy" "guardrails" {
  for_each = local.org_policies
  name     = "projects/${var.project_id}/policies/${each.key}"
  parent   = "projects/${var.project_id}"
  spec {
    rules {
      values {
        allowed_values = each.value
      }
    }
  }
}
```

**Pourquoi au niveau projet.** C'est le périmètre que ce dépôt possède. L'idéal est de les poser au niveau du
**dossier IA** : c'est le rôle de l'équipe Cloud centrale, dans son propre dépôt.

**Effet de bord à anticiper.** `iam.allowedPolicyMemberDomains` bloque aussi les partages externes légitimes
(prestataires sur un autre domaine). Les recenser avant, ajouter leur ID client dans la liste.

**Vérifier.** Test T18 : `gcloud run services add-iam-policy-binding <service-test> --member=allUsers --role=roles/run.invoker` → **refusé**.

---

## 3. Access Approval (`85_siem_access.tf`), mesure §4

```hcl
resource "google_project_access_approval_settings" "this" {
  count               = length(var.access_approval_emails) > 0 ? 1 : 0
  project_id          = var.project_id
  notification_emails = var.access_approval_emails
  enrolled_services {
    cloud_product = "all"    # tous les services éligibles, dont Gemini Enterprise, Agent Runtime, Model Armor, KMS
  }
}
```

**Organisation à prévoir.** Désigner au moins **deux approbateurs** (rôle `roles/accessapproval.approver`, donné hors
de ce dépôt) et une astreinte : une demande non traitée retarde le support Google en plein incident.

**Vérifier.** `gcloud access-approval settings get --project=$PROJECT_ID` → `enrolledServices: all`.

---

## 4. VPC Service Controls (`60_advanced.tf`), mesure §7

### 4.1 Le code

```hcl
locals {
  vpc_sc_services = [
    "discoveryengine.googleapis.com",
    "aiplatform.googleapis.com",      # ajouté par le projet 08 (exigé par la note)
    "agentregistry.googleapis.com",   # ajouté par le projet 08
    "modelarmor.googleapis.com", "dlp.googleapis.com", "cloudkms.googleapis.com", "secretmanager.googleapis.com",
  ]
}

resource "google_access_context_manager_access_level" "corporate" {   # qui a le droit d'entrer
  count  = var.vpc_sc_access_policy != "" && length(var.corporate_ip_ranges) > 0 ? 1 : 0
  parent = "accessPolicies/${var.vpc_sc_access_policy}"
  name   = "accessPolicies/${var.vpc_sc_access_policy}/accessLevels/acme_corporate_${replace(var.project_id, "-", "_")}"
  title  = "acme-corporate-${var.project_id}"
  basic {
    conditions {
      ip_subnetworks = var.corporate_ip_ranges
    }
  }
}

resource "google_access_context_manager_service_perimeter" "ge" {
  count                     = var.vpc_sc_access_policy == "" ? 0 : 1
  ...
  use_explicit_dry_run_spec = true

  dynamic "status" {                            # ce qui est BLOQUÉ : vide tant que vpc_sc_enforce = false
    for_each = var.vpc_sc_enforce ? [1] : []
    content {
      resources           = ["projects/${local.project_number}"]
      access_levels       = google_access_context_manager_access_level.corporate[*].name
      restricted_services = local.vpc_sc_services
    }
  }

  spec {                                        # ce qui est OBSERVÉ (dry-run) : toujours présent
    resources           = ["projects/${local.project_number}"]
    access_levels       = google_access_context_manager_access_level.corporate[*].name
    restricted_services = local.vpc_sc_services
  }
}
```

**Pourquoi `spec` reste toujours.** Une fois le périmètre appliqué, `spec` sert à tester une **évolution**
(un service de plus) en dry-run avant de l'appliquer à son tour.

### 4.2 Étape 1 : dry-run (`vpc_sc_enforce = false`)

1. PR, apply. **Aucun effet sur le trafic.**
2. Pendant 2 semaines, chaque jour (le journal quotidien le compte) :

```
protoPayload.metadata.@type="type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata"
protoPayload.metadata.dryRun=true
```

3. Pour chaque violation : `protoPayload.metadata.violationReason`, l'appelant, le service. Légitime ? → ajouter une
   règle d'entrée/sortie ou une IP au niveau d'accès (PR). Illégitime ? → c'est exactement ce que le périmètre bloquera.

### 4.3 Étape 2 : appliqué (`vpc_sc_enforce = true`)

**Conditions :** deux semaines sans violation légitime non traitée ; connecteurs déjà créés ; test T22 préparé ; fenêtre
de changement validée.

```hcl
vpc_sc_enforce = true
```

Plan attendu : une seule modification, `~ google_access_context_manager_service_perimeter.ge[0]` (ajout du bloc `status`).

**Retour arrière immédiat** en cas de blocage inattendu : `vpc_sc_enforce = false`, apply (quelques minutes).

### 4.4 Pièges VPC-SC

| Piège | Conséquence | Parade |
|---|---|---|
| Pas de niveau d'accès | L'interface GE (qui passe par `discoveryengine`) est **bloquée pour tous** | `corporate_ip_ranges` renseigné avant `vpc_sc_enforce = true` |
| Connecteurs créés après l'application | Création refusée | Créer les connecteurs avant |
| CI hors réseau Acme | Terraform lui-même est bloqué | Ajouter les IP de sortie de la CI au niveau d'accès, ou une règle d'entrée pour son compte |
| Télétravail sans VPN | Utilisateurs bloqués | IP du VPN dans le niveau d'accès ; à terme, niveau « appareil géré » (Endpoint Verification) |

---

## 5. Appliquer le palier

```bash
terraform plan -out=tfplan
# + google_project_service.orgpolicy[0]
# + google_org_policy_policy.guardrails["run.allowedIngress"]      (+ gcp.resourceLocations, iam.allowedPolicyMemberDomains)
# + google_project_access_approval_settings.this[0]
# + google_access_context_manager_access_level.corporate[0]
# + google_access_context_manager_service_perimeter.ge[0]           (dry-run seulement)
```

## 6. Vérifier

```bash
PROJECT_ID=... APP_ID=... ./scripts/verify_controls.sh
# OK   §2    Politique d'organisation run.allowedIngress effective
# OK   §2    Politique d'organisation iam.allowedPolicyMemberDomains effective
# OK   §2    Politique d'organisation gcp.resourceLocations effective
# OK   §4    Access Approval (accès Google soumis à approbation)
```

Tests T18 et T22 du [plan de tests](../03-plan-de-tests.md).
