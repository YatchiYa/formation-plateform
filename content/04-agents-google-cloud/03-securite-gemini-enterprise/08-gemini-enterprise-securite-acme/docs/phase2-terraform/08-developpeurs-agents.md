# 08. Développeurs : le modèle d'agent sécurisé

**Pour qui :** développeurs d'agents (ADK). **Mesures :** §1, §3, §9, §10.
**Code :** [agent/secure_agent/agent.py](../../agent/secure_agent/agent.py) (agent « service client » : consulter une
commande, préparer un remboursement).

---

## 1. Les règles, et pourquoi

| Règle | Pourquoi | Où c'est fait |
|---|---|---|
| Déployé sur **Agent Runtime**, par la **CI** | Hébergement géré, journaux, enregistrement automatique dans Agent Registry ; un déploiement hors CI déclenche l'alerte Shadow AI | `90_agents_registry.tf` |
| **Identité dédiée** par agent | Un droit donné au compte partagé d'Agent Runtime vaudrait pour **tous** les agents du projet | `google_service_account.secure_agent` |
| **ModelArmorPlugin**, mode fermé | Gemini Enterprise ne filtre **pas** les agents personnalisés | `agent.py` |
| **Refus de démarrer** sans Model Armor | Une variable oubliée ne doit jamais produire un agent non filtré | `agent.py` |
| `require_confirmation` sur les **écritures** | Mesure 9 : un humain valide avant l'exécution | `agent.py` |
| Outils MCP : `readOnlyHint` / `destructiveHint` | Gemini Enterprise demande confirmation pour les outils destructifs | serveur MCP (projet 04) |
| Sortie via **Agent Gateway** | Seuls les outils enregistrés sont joignables | `agent_gateway_config` |
| **Enregistré** dans Agent Registry | Sinon c'est du Shadow AI | automatique (Agent Runtime) |

---

## 2. Le code, expliqué

### 2.1 Validation humaine (§9)

```python
def refund_order(order_id: str, amount_eur: float, reason: str) -> dict:
    """ACTION : rembourse une commande (écriture). Exige une validation humaine."""
    ...

def needs_human(order_id: str, amount_eur: float, reason: str) -> bool:
    """Politique HITL : au-dessus du seuil, un humain confirme (ici : toujours)."""
    return amount_eur > AUTO_APPROVE_LIMIT_EUR          # 0 € par défaut

tools=[get_order, FunctionTool(refund_order, require_confirmation=needs_human)]
```

- `get_order` est en **lecture** : pas de confirmation.
- `refund_order` **modifie** : ADK met l'appel en attente et demande à l'utilisateur de confirmer. Refus → rien n'est fait.
- `require_confirmation` accepte `True` (toujours) ou une **fonction** qui reçoit les mêmes arguments que l'outil :
  on peut confirmer seulement au-delà d'un montant.

### 2.2 Model Armor dans l'agent (§3), mode fermé

```python
if os.getenv("PROMPT_TEMPLATE"):
    plugins.append(ModelArmorPlugin(config=ModelArmorConfig(
        prompt_template_name=os.environ["PROMPT_TEMPLATE"],
        response_template_name=os.environ["RESPONSE_TEMPLATE"],
        input_blocked_message="Demande bloquée par la politique de sécurité IA de Acme.",
        output_blocked_message="Réponse retenue par la politique de sécurité IA de Acme.",
        block_on_screening_failure=True,   # Model Armor injoignable => blocage
    )))
elif os.getenv("LOCAL_DEV") != "1":
    raise RuntimeError("PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants (LOCAL_DEV=1 pour un essai local).")
```

Les templates sont **les mêmes** que ceux de l'app (Terraform les passe en variables d'environnement) : une seule
politique pour tout Acme.

### 2.3 Le déploiement (`90_agents_registry.tf`)

```hcl
resource "google_vertex_ai_reasoning_engine" "secure_agent" {
  spec {
    service_account = google_service_account.secure_agent[0].email     # identité dédiée
    deployment_spec {
      env { name = "PROMPT_TEMPLATE"   value = google_model_armor_template.shield["ge-prompt-shield"].id }
      env { name = "RESPONSE_TEMPLATE" value = google_model_armor_template.shield["ge-response-shield"].id }
      dynamic "agent_gateway_config" {                                  # sortie gouvernée
        for_each = var.enable_agent_gateway ? [1] : []
        content { agent_to_anywhere_config { agent_gateway = google_network_services_agent_gateway.egress[0].id } }
      }
    }
  }
}
```

Rôles de l'identité dédiée, et **seulement** eux : `aiplatform.user`, `modelarmor.user`, `logging.logWriter`,
`monitoring.metricWriter`, `cloudtrace.agent`.

Publication dans l'app Gemini Enterprise : `terraform_data.register_agent` (API REST, pas encore de ressource Terraform) ;
retrait automatique au `destroy`.

---

## 3. Essayer en local (5 minutes)

```bash
cd agent
uv venv -p 3.12 .venv && source .venv/bin/activate
uv pip install -r requirements.txt

LOCAL_DEV=1 python secure_agent/agent.py      # autotest des outils, sans appel au modèle -> "secure_agent OK"
gcloud auth application-default login
LOCAL_DEV=1 adk web .                          # http://localhost:8000
```

Dans l'interface :
1. « Quel est le statut de la commande CMD-1001 ? » → réponse directe (lecture).
2. « Rembourse 10 € sur CMD-1002, colis abîmé » → l'interface affiche une **demande de confirmation** ; refuser → rien
   n'est fait ; accepter → remboursement.
3. Sans `LOCAL_DEV=1` : l'agent **refuse de démarrer** (preuve du fail closed).

Pour tester Model Armor en local : `PROMPT_TEMPLATE=projects/P/locations/eu/templates/ge-prompt-shield
RESPONSE_TEMPLATE=…/ge-response-shield adk web .` puis un jailbreak → message de blocage.

---

## 4. Déployer

```hcl
deploy_secure_agent = true          # terraform.tfvars
```

PR → plan (`+ google_service_account.secure_agent[0]`, `+ google_vertex_ai_reasoning_engine.secure_agent[0]`,
`+ terraform_data.register_agent[0]`…) → revue → apply par la CI (création : 5 à 15 minutes).

**Vérifier :** l'agent apparaît dans *Agent Platform → Déploiements*, dans **Agent Registry**, et dans l'app Gemini
Enterprise (*Agents*). Tests T08 et T11.

---

## 5. Adapter le modèle à votre agent

1. Copier `agent/secure_agent/` → `agent/mon_agent/`.
2. Remplacer les outils. **Toute** fonction qui écrit, supprime, envoie ou paie → `FunctionTool(..., require_confirmation=...)`.
3. Garder le bloc Model Armor **tel quel**.
4. Dans Terraform : dupliquer les blocs `secure_agent` (compte de service, rôles, reasoning engine, publication) avec
   `entrypoint_module = "mon_agent.agent"`, ou transformer le fichier en module si les agents se multiplient.
5. Ne donner à l'identité de l'agent **que** les rôles dont ses outils ont besoin (ex. `bigquery.dataViewer` sur **un**
   dataset, pas sur le projet).

## 6. Erreurs fréquentes

| Symptôme | Cause |
|---|---|
| `RuntimeError: PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants` | Variables non passées : voulu. En local, `LOCAL_DEV=1` |
| Toutes les réponses bloquées | Rôle `modelarmor.user` manquant pour l'identité de l'agent (mode fermé) |
| `ImportError: Model Armor support requires google-cloud-modelarmor` | Ajouter `google-cloud-modelarmor` aux dépendances |
| L'agent appelle un outil externe et échoue | Agent Gateway : l'outil n'est pas enregistré dans Agent Registry |
| La confirmation n'apparaît pas dans Gemini Enterprise | Point « à valider » : vérifier en recette ; repli = confirmation explicite par message (« répondez OUI ») |
