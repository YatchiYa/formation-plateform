# Phase 2 : figer la sécurité en Terraform

**Pour qui :** DevOps / plateforme (exécution), sécurité (revue), développeurs d'agents (fiche 08), PM (suivi).
**Durée :** semaines 2 et 3. **Prérequis :** la [phase 1](../01-phase1-console.md) est faite (ou pas : Terraform sait
aussi tout créer de zéro).

> **Débutant en Terraform ?** Lire d'abord [terraform/docs/00-bases-terraform.md](../../terraform/docs/00-bases-terraform.md)
> (30 minutes). Chaque fichier `.tf` a sa fiche ligne par ligne dans [terraform/docs/](../../terraform/docs/).

---

## Pourquoi cette phase

Ce qui a été activé à la main en phase 1 protège déjà. Mais un réglage manuel :

| Problème du réglage manuel | Ce que Terraform apporte |
|---|---|
| Un clic non tracé peut désactiver un filtre | Tout changement = une **PR relue**, validée par la sécurité |
| Impossible de prouver l'état exact à une date | L'**historique Git** est la preuve |
| À refaire à la main pour chaque domaine (mesure 8) | **Même code**, un fichier `tfvars` par domaine |
| Les dérives passent inaperçues | `terraform plan` montre **toute** différence avec le code |

Après cette phase, la règle est simple : **plus aucune modification de sécurité en console**. L'alerte
« garde-fou modifié » signale toute exception.

---

## Le parcours, fiche par fiche

| # | Fiche | Pour qui | Contenu |
|---|---|---|---|
| 01 | [Préparer et importer la console](01-preparer-et-importer.md) | DevOps | État distant, `terraform.tfvars`, adopter ce que la phase 1 a créé (`import`), lire un plan |
| 02 | [Palier A : projet](02-palier-a-projet.md) | DevOps + sécurité | Socle 06, audit élargi, plancher Agent Platform (inspect → block), Agent Registry, alerte Shadow AI |
| 03 | [Palier B : SOC](03-palier-b-soc.md) | DevOps + SOC | Export Pub/Sub vers le SIEM |
| 04 | [Palier C : organisation](04-palier-c-organisation.md) | DevOps + Cloud central | Politiques d'org, VPC-SC (dry-run → appliqué), niveau d'accès, Access Approval |
| 05 | [Palier D : réseau](05-palier-d-reseau.md) | DevOps + réseau | Secure Web Proxy, liste blanche ; Agent Gateway |
| 06 | [CI/CD et revue](06-ci-cd.md) | DevOps + sécurité | Circuit PR → plan → validation → apply, CODEOWNERS, pipeline GitHub, contrôle de conformité |
| 07 | [Mesure par mesure](07-mesure-par-mesure.md) | Tous | Les 10 mesures : ce que la note demande, le code qui y répond, la preuve |
| 08 | [Développeurs d'agents](08-developpeurs-agents.md) | Développeurs | Le modèle d'agent sécurisé, règles, essai local, déploiement |

---

## Les quatre paliers en un coup d'œil

Chaque palier = **une PR**, testée (phase 3) avant le suivant.

| Palier | Contenu | Prérequis | Variables (`terraform.tfvars`) |
|---|---|---|---|
| **A · Projet** | Socle 06 ; audit `aiplatform` + `agentregistry` ; plancher Agent Platform ; droits Agent Registry ; alerte Shadow AI | Droits sur le projet | `armor_agent_platform_mode`, `agent_developer_groups` |
| **B · SOC** | Export Pub/Sub vers le SIEM (même filtre que le bucket sécurité) | Identité du connecteur SIEM | `enable_siem_export`, `siem_subscriber` |
| **C · Organisation** | Politiques d'org ; VPC-SC + niveau d'accès ; Access Approval | Rôles org ; Access Transparency ; ID client Workspace | `enforce_org_policies`, `workspace_customer_id`, `vpc_sc_access_policy`, `vpc_sc_enforce`, `corporate_ip_ranges`, `access_approval_emails` |
| **D · Réseau** | Secure Web Proxy, liste blanche de domaines | VPC, sous-réseaux, liste validée | `swp` |

## Ce qui change par rapport au socle 06

| Fichier | Ajout | Mesure | Fiche débutant |
|---|---|---|---|
| `00_foundation.tf` | API `aiplatform`, `agentregistry`, `cloudasset` ; `pubsub`, `accessapproval`, réseau selon options | — | [03-foundation](../../terraform/docs/03-foundation.md) |
| `30_ai_guardrails.tf` | Plancher étendu : `integrated_services = ["AI_PLATFORM"]`, mode `inspect` ou `block` | §1 §3 | [14 §2](../../terraform/docs/14-ajouts-projet-08.md#2-30_ai_guardrailstf-modifié--le-plancher-couvre-aussi-les-agents) |
| `60_advanced.tf` | `aiplatform` et `agentregistry` dans le périmètre ; niveau d'accès IP ; bascule `vpc_sc_enforce` | §7 | [14 §3](../../terraform/docs/14-ajouts-projet-08.md#3-60_advancedtf-modifié--périmètre-élargi-et-niveau-daccès) |
| `70_detection.tf` | Journaux d'accès aux données pour `aiplatform` et `agentregistry` | §4 | [10-detection](../../terraform/docs/10-detection.md) |
| `75_shadow_ai.tf` *(nouveau)* | 3 politiques d'organisation ; alerte service public / agent créé hors circuit | §2 | [14 §4](../../terraform/docs/14-ajouts-projet-08.md#4-75_shadow_aitf-nouveau--empêcher-et-détecter) |
| `85_siem_access.tf` *(nouveau)* | Topic + abonnement Pub/Sub, sink, droit du writer ; Access Approval | §4 | [14 §5](../../terraform/docs/14-ajouts-projet-08.md#5-85_siem_accesstf-nouveau--siem-et-access-approval) |
| `90_agents_registry.tf` *(nouveau)* | Droits du registre ; agent exemple sur Agent Runtime, identité dédiée, sortie Agent Gateway | §1 §9 §10 | [14 §6](../../terraform/docs/14-ajouts-projet-08.md#6-90_agents_registrytf-nouveau--agents-et-catalogue) |
| `95_secure_web_proxy.tf` *(nouveau)* | Proxy, politique, liste blanche, sous-réseau dédié | §5 | [14 §7](../../terraform/docs/14-ajouts-projet-08.md#7-95_secure_web_proxytf-nouveau--swp-optionnel) |
| `imports.tf.example` *(nouveau)* | Blocs `import` pour adopter les ressources créées en console | — | [14 §8](../../terraform/docs/14-ajouts-projet-08.md#8-importstfexample--adopter-ce-qui-existe) |

## Les commandes que vous taperez

```bash
cd terraform
terraform init                          # une fois (ou après changement de version / backend)
terraform fmt -check && terraform validate
terraform plan -out=tfplan              # LIRE le plan
terraform apply tfplan                  # en recette ; en production : seulement la CI
terraform output                        # templates, buckets, abonnement SIEM, agent…
cd .. && PROJECT_ID=... APP_ID=... ./scripts/verify_controls.sh
```

**Fin de la phase 2 :** paliers A et B (au minimum) appliqués par la CI, `plan` sans écart, `verify_controls.sh` au vert.
On passe à la [phase 3](../03-plan-de-tests.md).
