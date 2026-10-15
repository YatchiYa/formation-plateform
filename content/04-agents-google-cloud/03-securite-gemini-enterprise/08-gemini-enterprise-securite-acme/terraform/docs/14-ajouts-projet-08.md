# 14. Les ajouts du projet 08, fichier par fichier

> Fiche pour débutants. Les bases (resource, variable, `count`, `for_each`, `dynamic`) sont dans
> [00-bases-terraform.md](00-bases-terraform.md). Pour chaque fichier : **à quoi il sert**, **le code expliqué**,
> **comment reproduire** quelque chose de semblable.

---

## 1. Le motif qu'on retrouve partout : « option activée par une variable »

Presque tout ce que le projet 08 ajoute est **optionnel**. Le motif est toujours le même :

```hcl
resource "google_pubsub_topic" "siem" {
  count = var.enable_siem_export ? 1 : 0     # 1 exemplaire si l'option est vraie, 0 sinon
  name  = "ge-security-siem"
}
```

- `condition ? A : B` : si la condition est vraie, A, sinon B.
- `count = 0` : la ressource n'existe pas. `count = 1` : elle existe, et on la désigne avec `[0]` :
  `google_pubsub_topic.siem[0].id`.
- `[*]` (« splat ») : la liste de tous les exemplaires, vide si `count = 0`. Pratique pour les arguments
  qui acceptent une liste : `notification_channels = google_monitoring_notification_channel.security[*].id`.

Pour un **bloc** optionnel à l'intérieur d'une ressource, on utilise `dynamic` :

```hcl
dynamic "ai_platform_floor_setting" {
  for_each = var.armor_agent_platform_mode == "off" ? [] : [1]   # liste vide = pas de bloc
  content {
    inspect_only = var.armor_agent_platform_mode == "inspect"
  }
}
```

---

## 2. `30_ai_guardrails.tf` (modifié) : le plancher couvre aussi les agents

```hcl
integrated_services = var.armor_agent_platform_mode == "off" ? [] : ["AI_PLATFORM"]

dynamic "ai_platform_floor_setting" {
  for_each = var.armor_agent_platform_mode == "off" ? [] : [1]
  content {
    inspect_only         = var.armor_agent_platform_mode == "inspect"
    inspect_and_block    = var.armor_agent_platform_mode == "block"
    enable_cloud_logging = true
  }
}
```

| Ligne | Explication |
|---|---|
| `integrated_services = ["AI_PLATFORM"]` | Le plancher ne sert plus seulement de minimum pour les templates : il **filtre** chaque appel Gemini fait dans le projet (agents, notebooks) |
| `inspect_only` / `inspect_and_block` | Deux booléens, un seul vrai. On compare la variable à un texte : `==` renvoie `true` ou `false` |
| `enable_cloud_logging = true` | Sans journaux, le mode « inspect » ne sert à rien : on ne verrait pas ce qui aurait été bloqué |

**La variable et sa validation** (`variables.tf`, section 9) : `validation` refuse toute valeur autre que
`off`, `inspect`, `block` **avant** d'appeler Google. Une faute de frappe est arrêtée au `plan`.

---

## 3. `60_advanced.tf` (modifié) : périmètre élargi et niveau d'accès

```hcl
resource "google_access_context_manager_access_level" "corporate" {
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
```

- `&&` : « et ». Le niveau d'accès n'existe que si **les deux** informations sont fournies.
- `length(liste)` : nombre d'éléments.
- `replace(texte, "-", "_")` : les noms de niveaux d'accès n'acceptent pas le tiret.
- `"${...}"` : insérer une valeur dans un texte (interpolation).

Dans le périmètre : `access_levels = google_access_context_manager_access_level.corporate[*].name`. Liste vide
si pas de niveau d'accès : le code marche dans les deux cas, sans `if`.

---

## 4. `75_shadow_ai.tf` (nouveau) : empêcher et détecter

**Politiques d'organisation construites dans une `map`** :

```hcl
locals {
  org_policies = var.enforce_org_policies ? merge(
    { "run.allowedIngress" = ["internal-and-cloud-load-balancing"], "gcp.resourceLocations" = ["in:eu-locations"] },
    var.workspace_customer_id != "" ? { "iam.allowedPolicyMemberDomains" = [var.workspace_customer_id] } : {},
  ) : {}
}

resource "google_org_policy_policy" "guardrails" {
  for_each = local.org_policies            # une politique par clé de la map
  name     = "projects/${var.project_id}/policies/${each.key}"
  ...
        allowed_values = each.value
```

- `merge(map1, map2)` : fusionne deux maps. On ajoute la 3e politique **seulement** si l'ID client est connu.
- `for_each` sur une map : `each.key` = nom de la contrainte, `each.value` = valeurs autorisées.
- **Reproduire :** ajouter une contrainte = ajouter une ligne dans la map. Aucune autre ressource à écrire.

**Détection :** une *métrique basée sur les journaux* (`google_logging_metric`) compte les entrées qui
correspondent à un filtre ; une *règle d'alerte* (`google_monitoring_alert_policy`) envoie un e-mail dès que
le compteur dépasse 0 sur 5 minutes. Même motif que l'alerte « garde-fou modifié » du socle
([10-detection.md](10-detection.md)).

---

## 5. `85_siem_access.tf` (nouveau) : SIEM et Access Approval

**La chaîne SIEM en 4 ressources :**

```
journaux ──(sink: filtre)──▶ topic Pub/Sub ──▶ abonnement ──▶ connecteur du SIEM
               │                    ▲
               └─ writer_identity ──┘ roles/pubsub.publisher
```

```hcl
resource "google_logging_project_sink" "siem" {
  destination            = "pubsub.googleapis.com/${google_pubsub_topic.siem[0].id}"
  filter                 = local.security_log_filter    # le MÊME filtre que le bucket ge-security
  unique_writer_identity = true                         # Google crée un compte dédié à ce sink
}

resource "google_pubsub_topic_iam_member" "siem_writer" {
  role   = "roles/pubsub.publisher"
  member = google_logging_project_sink.siem[0].writer_identity   # attribut calculé par Google
}
```

**Point clé pour débutant :** `writer_identity` n'est connu qu'**après** la création du sink. Terraform le
comprend tout seul grâce à la référence : il crée le sink, lit l'identité, puis donne le droit. Pas besoin de
`depends_on`.

**Réutiliser un filtre :** `local.security_log_filter` est défini une fois dans `80_logging.tf` et utilisé deux
fois. Tous les fichiers d'un dossier forment **un seul module** : un `local` est visible partout.

**Access Approval :**

```hcl
resource "google_project_access_approval_settings" "this" {
  count               = length(var.access_approval_emails) > 0 ? 1 : 0
  project_id          = var.project_id
  notification_emails = var.access_approval_emails
  enrolled_services {
    cloud_product = "all"
  }
}
```

La liste vide sert d'interrupteur : pas d'e-mail, pas de ressource.

---

## 6. `90_agents_registry.tf` (nouveau) : agents et catalogue

| Bloc | Rôle |
|---|---|
| `google_project_iam_member.registry_viewers` / `registry_editors` | Lecture du catalogue pour les utilisateurs, publication pour les développeurs (`for_each` sur les groupes) |
| `google_service_account.secure_agent` | Identité **propre** à l'agent |
| `google_project_iam_member.secure_agent` | 5 rôles minimum (Gemini, Model Armor, journaux, métriques, traces) |
| `data.external.agent_source` | Lance `scripts/pack.py` qui compresse `agent/` de façon **déterministe** : même code = mêmes octets = pas de redéploiement inutile |
| `google_vertex_ai_reasoning_engine.secure_agent` | L'agent sur Agent Runtime, avec les templates Model Armor en variables d'environnement |
| `dynamic "agent_gateway_config"` | Si Agent Gateway est activé, la sortie de l'agent passe par lui |
| `terraform_data.register_agent` | Publie l'agent dans l'app GE par l'API (pas encore de ressource Terraform) ; le retire au `destroy` |

**Les deux `local-exec` de `terraform_data` :** le premier s'exécute à la création, le second (`when = destroy`)
à la suppression. `self.input` permet au provisioner de destruction de retrouver les valeurs : il ne peut pas lire
les variables, seulement ce qui a été mémorisé dans l'état.

**Le provider `external`** est déclaré dans `versions.tf` (`hashicorp/external`). Il permet d'appeler un
programme local qui lit du JSON sur l'entrée standard et écrit du JSON sur la sortie.

---

## 7. `95_secure_web_proxy.tf` (nouveau) : SWP optionnel

Une variable **objet** (`var.swp`) regroupe tous les paramètres. `null` = désactivé :

```hcl
count = var.swp == null ? 0 : 1
network = var.swp.network
```

| Ressource | Rôle |
|---|---|
| `google_compute_subnetwork.swp_proxy_only` | Sous-réseau réservé au proxy (`purpose = "REGIONAL_MANAGED_PROXY"`), exigé par Google |
| `google_network_security_url_lists.allowed` | La liste blanche (domaines, `*.` autorisé) |
| `google_network_security_gateway_security_policy` | La politique, refus par défaut |
| `..._policy_rule.allow_listed` | La règle : `inUrlList(host(), 'LISTE')` → `ALLOW` (expression CEL) |
| `google_network_services_gateway.swp` | Le proxy lui-même (`type = "SECURE_WEB_GATEWAY"`, mode explicite : les charges utilisent `HTTPS_PROXY`) |

**Reproduire pour un autre besoin :** ajouter un domaine = l'ajouter dans `allowed_hosts` (PR validée par la
sécurité). Une règle plus fine (méthode HTTP, chemin) demande l'inspection TLS : voir le commentaire `ponytail`
dans le fichier.

---

## 8. `imports.tf.example` : adopter ce qui existe

```hcl
import {
  to = google_model_armor_template.shield["ge-prompt-shield"]   # adresse dans le code
  id = "projects/PROJECT_ID/locations/eu/templates/ge-prompt-shield"   # ressource chez Google
}
```

Le `plan` affiche alors « 1 to import » au lieu de « 1 to add ». Le format de `id` de chaque type est donné en
bas de sa page dans la documentation du provider (section *Import*). Avec `for_each`, un seul bloc importe
plusieurs ressources (voir les journaux d'audit dans le fichier).
