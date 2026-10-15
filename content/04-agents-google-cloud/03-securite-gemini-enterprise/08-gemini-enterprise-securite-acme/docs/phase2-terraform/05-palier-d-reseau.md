# 05. Palier D : contrôle de sortie (Agent Gateway, Secure Web Proxy)

**Pour qui :** DevOps + équipe réseau, sécurité (liste blanche). **Mesure :** §5.

---

## 1. D'abord, la bonne question : qui sort vers Internet, et par où ?

| Qui appelle Internet | Par où ça sort | Le bon contrôle |
|---|---|---|
| **Gemini Enterprise** (connecteurs, recherche web, appels d'agents) | Infrastructure Google (SaaS), **pas** le VPC Acme | **Agent Gateway** + politiques d'org sur les destinations + IP fixes des connecteurs |
| **Agents sur Agent Runtime** (géré) | Infrastructure Google | **Agent Gateway** (`agent_to_anywhere_config`) |
| Agents Agent Runtime **reliés au VPC** (interface PSC), Cloud Run avec sortie VPC, VM | **VPC Acme** | **Secure Web Proxy** |

C'est la correction 2.6 de la note : un Secure Web Proxy ne voit pas le trafic de Gemini Enterprise. Les deux
outils sont complémentaires, pas concurrents.

---

## 2. Agent Gateway (recommandé dès qu'il y a des agents ou des outils MCP)

**Ce que c'est.** Un point de passage géré par Google pour les appels des agents et de Gemini Enterprise vers d'autres
agents, outils MCP et API. **Refus par défaut** : seuls les éléments enregistrés dans **Agent Registry** sont joignables.

**Variables.**

```hcl
enable_agent_gateway = true
```

**Code** (`60_advanced.tf`, déjà dans le socle 06) :

```hcl
resource "google_network_services_agent_gateway" "egress" {
  count    = var.enable_agent_gateway ? 1 : 0
  name     = "${var.app_id}-egress"
  location = var.region                       # app 'eu' -> europe-west1
  google_managed {
    governed_access_path = "AGENT_TO_ANYWHERE"
  }
  registries = ["//agentregistry.googleapis.com/projects/${var.project_id}/locations/global"]
}
```

L'app Gemini Enterprise y est reliée par `agentGatewaySetting` (`50_app.tf`), et l'agent exemple par
(`90_agents_registry.tf`) :

```hcl
dynamic "agent_gateway_config" {
  for_each = var.enable_agent_gateway ? [1] : []
  content {
    agent_to_anywhere_config {
      agent_gateway = google_network_services_agent_gateway.egress[0].id
    }
  }
}
```

**Vérifier.** Un agent tente d'appeler un outil **non enregistré** → refusé ; enregistré → accepté.

---

## 3. Secure Web Proxy (seulement si des charges sortent par votre VPC)

**Ce que c'est.** Un proxy HTTPS géré, placé dans votre VPC : les charges l'utilisent comme `HTTPS_PROXY`, il ne laisse
passer que les **domaines de la liste blanche**.

**Variables.**

```hcl
swp = {
  network         = "projects/acme-ge-prod/global/networks/agents"
  subnetwork      = "projects/acme-ge-prod/regions/europe-west1/subnetworks/agents"
  proxy_only_cidr = "10.129.0.0/23"     # plage libre, réservée au proxy (demande à l'équipe réseau)
  address         = "10.128.0.99"       # IP du proxy dans le sous-réseau des charges
  allowed_hosts   = ["*.googleapis.com", "api.github.com", "*.acme.example"]
}
```

**Code** (`95_secure_web_proxy.tf`), 5 ressources :

| Ressource | Rôle |
|---|---|
| `google_compute_subnetwork.swp_proxy_only` | Sous-réseau réservé au proxy (`purpose = "REGIONAL_MANAGED_PROXY"`), exigé par Google |
| `google_network_security_url_lists.allowed` | La liste blanche |
| `google_network_security_gateway_security_policy.swp` | La politique (refus implicite de tout le reste) |
| `google_network_security_gateway_security_policy_rule.allow_listed` | `session_matcher = "inUrlList(host(), '<liste>')"` → `ALLOW` |
| `google_network_services_gateway.swp` | Le proxy (`type = "SECURE_WEB_GATEWAY"`, `routing_mode = "EXPLICIT_ROUTING_MODE"`, port 443) |

**Côté charges.** Variables d'environnement `HTTPS_PROXY=https://10.128.0.99:443` (valeur : `terraform output swp_proxy`),
et une règle de pare-feu qui interdit la sortie directe vers Internet (sinon le proxy est contournable).

**Vérifier.**

```bash
curl -x https://10.128.0.99:443 --proxy-insecure https://api.github.com     # autorisé -> 200
curl -x https://10.128.0.99:443 --proxy-insecure https://example.org        # refusé  -> 403
```

**Limites assumées.**
- Filtrage par **nom d'hôte** seulement : pas d'inspection TLS (elle exige une autorité de certification, CA Service).
- **À valider au premier déploiement :** si l'API exige un certificat même sans inspection TLS, ajouter
  `certificate_urls` (Certificate Manager).

**Gouvernance de la liste blanche.** Ajouter un domaine = une PR validée par la sécurité ; revue trimestrielle.

---

## 4. Appliquer et revenir en arrière

```bash
terraform plan -out=tfplan      # + 5 ressources SWP, + éventuellement Agent Gateway
```

Retour arrière : `swp = null` / `enable_agent_gateway = false`. **Attention** : retirer le proxy coupe les charges qui
l'utilisent ; retirer Agent Gateway rouvre la sortie des agents.
