# 07. Mesure par mesure : ce que la note demande, ce que nous faisons

**Pour qui :** tous, et l'audit. Pour chaque mesure : **la demande**, la réponse **native** (phase 1), la réponse
**Terraform / code** (phase 2), la **preuve** (test et journal), le **pourquoi**, et ce qui **reste**.

> La note est classée « Secret & Internal » : ce document la résume sans la reproduire. Les corrections apportées à la
> note sont détaillées dans [docs/05 §2](../05-correspondance-note.md#2-corrections-à-apporter-à-la-note).

| # | Mesure | Natif | Terraform / code | Preuve |
|---|---|---|---|---|
| 1 | Agents sur Agent Runtime | Plancher Agent Platform | `30`, `90` | T08–T10 |
| 2 | Shadow AI | Asset Inventory, politiques d'org, SCC | `75`, inventaire | T18, T19 |
| 3 | Model Armor | Templates, app, plancher | `30`, `50` | T01–T07 |
| 4 | Journaux, AxT, Access Approval, SIEM | Audit Logs, AxT, AA, routeur | `70`, `80`, `85` | T21 |
| 5 | Filtrage de sortie | Agent Gateway, IP fixes | `60`, `90`, `95` | T13 |
| 6 | RAG | Connecteurs fédérés | `40`, scanner | T14, T15 |
| 7 | VPC-SC | Dry-run, niveau d'accès | `60` | T22 |
| 8 | Identité, domaines, rôles | IdP, groupes | `10`, `envs/` | T16, T17 |
| 9 | Validation humaine | Confirmations GE | agent, MCP | T11, T12 |
| 10 | Agent Registry, partage | Registre, partage désactivé | `90`, `50` | T19 |

---

## 1. Agents sur Agent Runtime (ex-Agent Engine)

| | |
|---|---|
| **La note demande** | Héberger les agents sur la plateforme gérée de Google plutôt que sur des serveurs « maison » |
| **Natif (console)** | Agent Runtime ; plancher Model Armor appliqué à Agent Platform ([phase 1, étape 4](../01-phase1-console.md#étape-4--plancher-model-armor--agent-platform-en-observation)) |
| **Terraform / code** | `90_agents_registry.tf` : agent sur Agent Runtime (`google_vertex_ai_reasoning_engine`), identité dédiée, `ModelArmorPlugin` en mode fermé, refus de démarrer sans Model Armor, sortie via Agent Gateway. `30_ai_guardrails.tf` : `integrated_services = ["AI_PLATFORM"]` |
| **Preuve** | T08 (jailbreak bloqué par l'agent), T09–T10 (plancher), `verify_controls.sh` |
| **Pourquoi** | Héberger sur Agent Runtime ne filtre rien en soi. Plugin (par conception) + plancher (filet de sécurité) : deux protections indépendantes |
| **Reste / limite** | Exception encadrée pour les serveurs MCP sur Cloud Run, recommandés par Google pour Gemini Enterprise : privés, enregistrés, déployés par la CI. Migration des agents existants (inventaire §2) |

## 2. Shadow AI

| | |
|---|---|
| **La note demande** | Repérer et mettre en quarantaine les IA non gouvernées ; posture de sécurité IA |
| **Natif (console)** | Cloud Asset Inventory ; politiques d'organisation ; Security Command Center AI Protection |
| **Terraform / code** | `75_shadow_ai.tf` : Cloud Run non public (`run.allowedIngress`), partage limité au domaine (`iam.allowedPolicyMemberDomains`), UE (`gcp.resourceLocations`) ; alerte « service public / agent créé ». `scripts/shadow_ai_inventory.sh` mensuel |
| **Preuve** | T18 (allUsers refusé ou alerte), T19 (agent hors CI détecté), inventaire archivé |
| **Pourquoi** | Empêcher coûte moins cher que détecter ; détecter rattrape ce qui passe ; l'inventaire prouve l'état au comité |
| **Reste / limite** | Quarantaine réseau et Wiz : décisions d'organisation, hors périmètre de l'app |

## 3. Model Armor (Inspect & Block, URL, données sensibles)

| | |
|---|---|
| **La note demande** | Filtrer prompts et réponses, bloquer, détecter les données sensibles |
| **Natif (console)** | Templates, réglage Model Armor de l'app, plancher |
| **Terraform / code** | `30_ai_guardrails.tf` : deux templates `INSPECT_AND_BLOCK` ; détecteurs DLP France (NIR, CNI, passeport, IBAN…) ; multilingue. `50_app.tf` : `failure_mode = "FAIL_CLOSED"` |
| **Preuve** | T01–T07 ; `scripts/test_model_armor.sh` |
| **Pourquoi** | Plus strict que la note : sortie filtrée aussi, mode fermé, détecteurs français. Le filtre « de base » ne voit ni IBAN ni NIR |

## 4. Journaux, Access Transparency, Access Approval, SIEM

| | |
|---|---|
| **La note demande** | Journaux d'accès aux données (dont Vertex AI), AxT, Access Approval, envoi au SIEM |
| **Natif (console)** | Audit Logs ; Access Transparency (organisation) ; Access Approval ; routeur de journaux |
| **Terraform / code** | `70_detection.tf` : audit étendu à `aiplatform` et `agentregistry`. `80_logging.tf` : buckets UE (365 j sécurité, 90 j usage, accès restreint). `85_siem_access.tf` : Pub/Sub vers le SIEM ; Access Approval sur tous les services éligibles |
| **Preuve** | T21 (changement visible côté SIEM) ; journal quotidien ; `verify_controls.sh` |
| **Pourquoi** | Access Approval couvre Gemini Enterprise, Agent Runtime, Model Armor et Cloud KMS (GA) : aucun ingénieur Google n'accède aux données sans accord |
| **Reste / limite** | Access Transparency : activation par l'équipe Cloud centrale (support Enhanced / Premium) |

## 5. Filtrage de sortie

| | |
|---|---|
| **La note demande** | Contrôler les destinations Internet appelées par l'IA (Secure Web Proxy) |
| **Natif (console)** | Agent Gateway (sortie gouvernée, refus par défaut) ; IP fixes des connecteurs ; politiques d'org sur les destinations |
| **Terraform / code** | `60_advanced.tf` : Agent Gateway ; `90_agents_registry.tf` : agent relié à la passerelle ; `95_secure_web_proxy.tf` : SWP optionnel avec liste blanche |
| **Preuve** | T13 (lien externe inconnu) ; journaux de la passerelle et du proxy |
| **Pourquoi** | Gemini Enterprise est un SaaS : il ne sort pas par le VPC Acme. Le SWP filtre nos charges ; Agent Gateway filtre GE et les agents ([fiche 05](05-palier-d-reseau.md)) |

## 6. RAG : droits et contenu indexé

| | |
|---|---|
| **La note demande** | Respecter les droits des sources ; éviter l'empoisonnement des documents |
| **Natif (console)** | Connecteurs fédérés : les droits de la source s'appliquent à chaque requête |
| **Terraform / code** | `40_connectors.tf` (fédéré par défaut). `scripts/scan_before_ingest.py` : Model Armor analyse PDF, Word, Excel, PowerPoint, CSV, texte ; quarantaine ; fail closed |
| **Preuve** | T14 (A ne voit pas le fichier de B), T15 (PDF piégé en quarantaine) |
| **Pourquoi** | Model Armor filtre la question et la réponse, pas les documents récupérés : l'analyse en amont ferme cette porte pour les dépôts que l'on alimente |
| **Reste / limite** | Sources fédérées (Drive, SharePoint) : protection par les droits, le filtre de sortie et la confirmation humaine |

**Utiliser le scanner dans un circuit de publication :**

```bash
gcloud storage rsync gs://depot-a-publier ./a_publier
python3 scripts/scan_before_ingest.py --template projects/P/locations/eu/templates/ge-prompt-shield \
  --src ./a_publier --clean ./publie --quarantine ./quarantaine > rapport.csv
gcloud storage rsync ./publie gs://bucket-indexe-par-ge     # seul ce bucket est connecté à Gemini Enterprise
```

## 7. VPC Service Controls

| | |
|---|---|
| **La note demande** | Périmètre anti-exfiltration autour des services IA |
| **Natif (console)** | Périmètre en dry-run ; niveaux d'accès |
| **Terraform / code** | `60_advanced.tf` : `discoveryengine`, `aiplatform`, `agentregistry`, `modelarmor`, `dlp`, `cloudkms`, `secretmanager` ; niveau d'accès IP Acme ; `vpc_sc_enforce` |
| **Preuve** | T22 (accès hors réseau Acme journalisé, puis refusé) |
| **Pourquoi** | Le dry-run évite la coupure ; le niveau d'accès évite de bloquer les utilisateurs |
| **Reste / limite** | Passage en appliqué après deux semaines ; niveau « appareil géré » si Endpoint Verification est déployé |

## 8. Identité, un projet par domaine, séparation des rôles

| | |
|---|---|
| **La note demande** | Fédération d'identité, isolation par domaine, rôles séparés |
| **Natif (console)** | Fournisseur d'identité de l'app ; groupes |
| **Terraform / code** | `10_identity_access.tf` : rôles par groupes ; sécurité seule maître des filtres, clés et journaux. Un `tfvars` et un état par domaine ([fiche 06 §4](06-ci-cd.md#4-un-projet-par-domaine-mesure-8)) |
| **Preuve** | T16 (hors groupe refusé), T17 (admin GE ne touche pas aux filtres) ; contrôle « aucun utilisateur individuel » |
| **Pourquoi** | Un domaine compromis n'expose pas les autres ; un administrateur ne peut pas désactiver sa propre sécurité |
| **Reste / limite** | Décision IdP : avec Entra / Okta, pas de connecteurs Workspace ; changer plus tard efface l'historique |

## 9. Validation humaine des actions

| | |
|---|---|
| **La note demande** | Un humain confirme toute action qui modifie des données |
| **Natif (console)** | Gemini Enterprise demande confirmation pour les actions et les outils MCP marqués destructifs |
| **Terraform / code** | Agent : `require_confirmation` sur les outils d'écriture ([fiche 08](08-developpeurs-agents.md)) ; MCP : annotations `destructiveHint` (projet 04) |
| **Preuve** | T11 (remboursement confirmé ou refusé), T12 (outil MCP destructif) |
| **Pourquoi** | Dernier rempart contre l'injection indirecte : même manipulé, l'agent ne peut rien modifier sans accord |

## 10. Agent Registry et partage

| | |
|---|---|
| **La note demande** | Catalogue central des agents ; partage encadré |
| **Natif (console)** | Agent Registry ; partage d'agents désactivé ; skills sur approbation |
| **Terraform / code** | `90_agents_registry.tf` : lecture pour les utilisateurs, publication pour les développeurs. `50_app.tf` : fonctionnalités de l'app (`disable-agent-sharing`, partage des skills sur approbation) |
| **Preuve** | `verify_controls.sh` ; T19 |
| **Pourquoi** | Ce qui n'est pas au registre n'est pas gouverné ; avec Agent Gateway, il n'est même pas joignable |
