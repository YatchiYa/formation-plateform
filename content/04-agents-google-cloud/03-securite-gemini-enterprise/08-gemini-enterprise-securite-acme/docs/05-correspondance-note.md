# Correspondance avec la note de sécurité Acme, mesure par mesure

**Pour qui :** tous, et l'audit. Pour chaque mesure : **ce que la note demande** (résumé), **ce que nous
mettons en place**, en natif puis en Terraform, **la preuve** (test et journal), et **ce qui reste**.

> La note est classée « Secret & Internal ». Ce document la résume sans la reproduire. Ne pas le diffuser
> hors de l'équipe projet.

---

## 1. Les 10 mesures

### Mesure 1 : héberger les agents sur Agent Runtime (ex-Vertex AI Agent Engine)

| | |
|---|---|
| **Demande** | Agents IA sur la plateforme gérée de Google plutôt que sur Cloud Run / GKE « maison » |
| **Natif** | Agent Runtime (console *Agent Platform → Déploiements*) ; plancher Model Armor appliqué à *Agent Platform* |
| **Terraform** | `90_agents_registry.tf` (agent, identité dédiée, sortie Agent Gateway), `30_ai_guardrails.tf` (plancher `AI_PLATFORM`) |
| **Preuve** | T08, T09, T10 ; `verify_controls.sh` ligne « Plancher étendu aux appels Gemini » |
| **Reste** | Migrer les agents existants (inventaire : mesure 2). **Exception encadrée** pour les serveurs MCP sur Cloud Run (recommandés par Google pour GE) : privés, enregistrés, déployés par la CI |

**Pourquoi le plancher compte autant que l'hébergement :** héberger sur Agent Runtime ne filtre rien en soi.
Model Armor de Gemini Enterprise **ne s'applique pas** aux agents personnalisés. Deux protections
complémentaires : le plugin dans l'agent (défense par conception) et le plancher du projet (filet de sécurité,
même si un développeur oublie le plugin).

### Mesure 2 : Shadow AI (quarantaine, inventaire, AI-SPM)

| | |
|---|---|
| **Demande** | Repérer et mettre en quarantaine les IA non gouvernées ; posture de sécurité IA |
| **Natif** | Cloud Asset Inventory ; politiques d'organisation ; Security Command Center *AI Protection* |
| **Terraform** | `75_shadow_ai.tf` : `run.allowedIngress`, `iam.allowedPolicyMemberDomains`, `gcp.resourceLocations` ; alerte « service public / agent créé » |
| **Script** | `shadow_ai_inventory.sh` : ressources IA, ressources publiques, ressources sans propriétaire |
| **Preuve** | T18, T19 ; inventaire mensuel archivé |
| **Reste** | Quarantaine réseau et Wiz : décisions d'organisation, hors périmètre de l'app |

### Mesure 3 : Model Armor (Inspect & Block, URL malveillantes, données sensibles)

| | |
|---|---|
| **Demande** | Filtrer prompts et réponses, bloquer, détecter les données sensibles |
| **Natif** | Templates Model Armor ; réglage Model Armor de l'app ; plancher |
| **Terraform** | `30_ai_guardrails.tf` : 2 templates `INSPECT_AND_BLOCK`, injection/jailbreak, URL, IA responsable, **DLP FR** (NIR, CNI, passeport, IBAN…), multilingue ; `50_app.tf` : `FAIL_CLOSED` |
| **Preuve** | T01–T07 ; `test_model_armor.sh` |
| **Écart avec la note** | Plus strict : sortie filtrée aussi, mode fermé, détecteurs français. Corrections : §2.1 à §2.5 |

### Mesure 4 : journaux, Access Transparency, Access Approval, SIEM

| | |
|---|---|
| **Demande** | Journaux d'accès aux données (dont Vertex AI), AxT, Access Approval, envoi au SIEM |
| **Natif** | Audit Logs ; Access Transparency (org) ; Access Approval (couvre Gemini Enterprise, Agent Runtime, Model Armor, KMS) ; Log Router |
| **Terraform** | `70_detection.tf` (audit + `aiplatform`, `agentregistry`), `80_logging.tf` (buckets UE, 365 j, accès restreint), `85_siem_access.tf` (Pub/Sub → SIEM, Access Approval) |
| **Script** | `daily_report.sh` |
| **Preuve** | T21 ; `verify_controls.sh` ; journal quotidien |
| **Reste** | Access Transparency : activation organisation (support Enhanced/Premium) |

### Mesure 5 : filtrage de sortie (Secure Web Proxy)

| | |
|---|---|
| **Demande** | Contrôler les destinations Internet appelées par l'IA |
| **Natif** | **Agent Gateway** (sortie gouvernée de GE et des agents, deny par défaut) ; IP fixes des connecteurs ; politiques d'org sur les destinations des connecteurs |
| **Terraform** | `60_advanced.tf` (Agent Gateway), `90_agents_registry.tf` (agent → gateway), `95_secure_web_proxy.tf` (SWP, liste blanche) |
| **Preuve** | T13 ; journaux Agent Gateway / SWP |
| **Correction** | Le SWP ne voit pas le trafic de Gemini Enterprise : §2.6 |

### Mesure 6 : RAG (droits et contenu indexé)

| | |
|---|---|
| **Demande** | Respecter les droits des sources ; éviter l'empoisonnement des documents indexés |
| **Natif** | Connecteurs **fédérés** par défaut : les droits de la source s'appliquent à chaque requête |
| **Terraform** | `40_connectors.tf` |
| **Script** | `scan_before_ingest.py` : Model Armor analyse PDF, Word, Excel, PowerPoint, CSV, texte ; quarantaine des fichiers suspects ; **fail closed** |
| **Preuve** | T14, T15 |
| **Limite** | Le script s'applique aux dépôts que l'on alimente (bucket, dossier de publication). Pour les sources fédérées (Drive, SharePoint), le contenu n'est pas copié : la protection repose sur les droits, le filtre de sortie et la confirmation humaine |

### Mesure 7 : VPC Service Controls

| | |
|---|---|
| **Demande** | Périmètre anti-exfiltration autour des services IA |
| **Natif** | Périmètre en dry-run ; niveaux d'accès (Access Context Manager) |
| **Terraform** | `60_advanced.tf` : `discoveryengine`, **`aiplatform`**, **`agentregistry`**, `modelarmor`, `dlp`, `cloudkms`, `secretmanager` ; niveau d'accès IP Acme |
| **Preuve** | T22 ; requête VPC-SC |
| **Reste** | Passage dry-run → appliqué après 2 semaines d'observation ; niveau d'accès « appareil géré » si Endpoint Verification est déployé |

### Mesure 8 : identité, un projet par domaine, séparation des rôles

| | |
|---|---|
| **Demande** | Fédération d'identité (Entra/Okta), isolation par domaine, rôles séparés |
| **Natif** | Fournisseur d'identité de l'app ; groupes |
| **Terraform** | `10_identity_access.tf` (`identity_provider`, groupes, séparation sécurité / admins) ; un `tfvars` par domaine ([phase 2, fiche 06 §4](phase2-terraform/06-ci-cd.md#4-un-projet-par-domaine-mesure-8)) |
| **Preuve** | T16, T17 ; contrôle « aucun utilisateur individuel » |
| **Décision à prendre** | §2.7 |

### Mesure 9 : validation humaine des actions

| | |
|---|---|
| **Demande** | Un humain confirme toute action qui modifie des données |
| **Natif** | Gemini Enterprise demande confirmation pour les actions et les outils MCP marqués destructifs |
| **Code** | Agent exemple : `FunctionTool(..., require_confirmation=needs_human)` ; serveur MCP Sheets : annotations `destructiveHint` |
| **Preuve** | T11, T12 |

### Mesure 10 : Agent Registry et partage

| | |
|---|---|
| **Demande** | Catalogue central des agents ; partage encadré |
| **Natif** | Agent Registry ; partage d'agents désactivé ; partage des compétences sur approbation |
| **Terraform** | `90_agents_registry.tf` (viewer / editor), `50_app.tf` (fonctionnalités) |
| **Preuve** | `verify_controls.sh` ; T19 |

---

## 2. Corrections à apporter à la note

### 2.1 L'exemple JSON de Model Armor n'est pas valide

Les noms de champs ne sont pas ceux de l'API (`enforcement` au lieu de `filterEnforcement` ;
`raiSettings.hateSpeech` au lieu d'une liste `raiFilters` de `{filterType, confidenceLevel}`). Copié tel quel,
il est refusé. Forme correcte (extrait) :

```json
{
  "filterConfig": {
    "piAndJailbreakFilterSettings": { "filterEnforcement": "ENABLED", "confidenceLevel": "MEDIUM_AND_ABOVE" },
    "maliciousUriFilterSettings":   { "filterEnforcement": "ENABLED" },
    "raiSettings": { "raiFilters": [
      { "filterType": "HATE_SPEECH", "confidenceLevel": "MEDIUM_AND_ABOVE" },
      { "filterType": "DANGEROUS",   "confidenceLevel": "MEDIUM_AND_ABOVE" } ] },
    "sdpSettings": { "advancedConfig": {
      "inspectTemplate": "projects/P/locations/europe/inspectTemplates/ge-donnees-sensibles-fr" } }
  },
  "templateMetadata": { "enforcementType": "INSPECT_AND_BLOCK" }
}
```

### 2.2 La configuration « de base » ne voit pas les données françaises

`sdpSettings.basicConfig` utilise des détecteurs génériques orientés États-Unis (cartes, numéro de sécurité
sociale US, identifiants cloud). Ni IBAN, ni NIR, ni CNI. → configuration **avancée** avec un modèle DLP.

### 2.3 Pas de masquage dans Gemini Enterprise

Model Armor ne renvoie pas de texte masqué à Gemini Enterprise : une détection **bloque** l'échange.
Formulation à corriger : « détecter et bloquer ».

### 2.4 Le filtre d'URL ne couvre qu'une partie d'« Echo Leak »

Il bloque les URL **connues** comme malveillantes (listes Google). Un domaine d'attaquant tout neuf passe.
Compléments : test T13 sur l'affichage des images externes, contrôle de sortie (mesure 5), confirmation
humaine (mesure 9).

### 2.5 Model Armor ne protège pas « tous les modèles » automatiquement

Dans Gemini Enterprise, il protège l'assistant, **pas** les agents personnalisés (ADK, A2A). → plugin dans
l'agent + plancher *Agent Platform* (mesure 1).

### 2.6 Le Secure Web Proxy ne s'applique pas à Gemini Enterprise

Gemini Enterprise est un service géré par Google : ses connecteurs et son moteur ne sortent pas par le VPC
Acme. Le SWP filtre **vos** charges (agents reliés au VPC, Cloud Run, VM). Pour Gemini Enterprise :
Agent Gateway, politiques d'organisation sur les destinations, IP fixes des connecteurs.

### 2.7 Point de décision : fournisseur d'identité

Avec un fournisseur tiers (Entra ID / Okta via Workforce Identity Federation), les connecteurs **Google
Workspace** (Drive, Gmail, Agenda) ne sont pas pris en charge. Changer de fournisseur plus tard efface
l'historique des conversations. → **Décision à prendre avant la production**, par l'architecture et la sécurité.

### 2.8 Injection indirecte (documents piégés)

Model Armor filtre la question et la réponse, pas le contenu des documents récupérés au moment de la réponse.
D'où l'analyse avant indexation (mesure 6), le filtre de sortie et la confirmation humaine : aucune des trois
ne suffit seule.

---

## 3. Sources Google

- Model Armor et Gemini Enterprise : https://docs.cloud.google.com/model-armor/model-armor-gemini-enterprise-integration
- Plancher Model Armor (dont *Agent Platform*) : https://docs.cloud.google.com/model-armor/configure-floor-settings
- Analyse de documents par Model Armor : https://docs.cloud.google.com/model-armor/sanitize-prompts-responses
- Access Approval, services couverts : https://docs.cloud.google.com/assured-workloads/access-approval/docs/supported-services
- Access Transparency, services couverts : https://docs.cloud.google.com/assured-workloads/access-transparency/docs/supported-services
- VPC Service Controls et Gemini Enterprise : https://docs.cloud.google.com/gemini/enterprise/docs/configure-vpc-sc
- Agent Registry : https://docs.cloud.google.com/agent-registry
- Agent Runtime + Terraform : https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/use-terraform
- Secure Web Proxy : https://docs.cloud.google.com/secure-web-proxy/docs/overview
- Cloud Asset Inventory, recherche : https://docs.cloud.google.com/asset-inventory/docs/searching-resources
- Confirmation des outils dans ADK : https://adk.dev
