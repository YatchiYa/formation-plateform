# 03. Palier B : export vers le SIEM du SOC

**Pour qui :** DevOps (PR), SOC (consommation). **Mesure :** §4.
**Prérequis :** palier A appliqué ; le SOC fournit l'**identité de son connecteur** (compte de service qui lira les messages).

---

## 1. Ce que le palier apporte

Les journaux de sécurité partent **en temps réel** vers le SIEM du SOC (Splunk, Chronicle / Google SecOps, Sentinel…),
en plus du bucket `ge-security` (365 jours, UE).

```
journaux du projet ──(récepteur : filtre sécurité)──▶ sujet Pub/Sub ──▶ abonnement ──▶ connecteur du SIEM
                         │                                 ▲
                         └── identité du rédacteur ────────┘  rôle Pub/Sub Publisher
```

**Ce qui part :** audit (administration et accès aux données) de Gemini Enterprise, Agent Platform, Model Armor, KMS,
Secret Manager, DLP, IAM ; verdicts Model Armor si leur journalisation est activée.
**Ce qui ne part pas :** les questions des utilisateurs (journaux d'usage, bucket `ge-usage`). Choix RGPD :
minimisation. À revoir avec le DPO si le SOC en a besoin.

## 2. Les variables

```hcl
enable_siem_export = true
siem_subscriber    = "serviceAccount:siem-connector@soc-projet.iam.gserviceaccount.com"
```

## 3. Le code, expliqué (`85_siem_access.tf`)

```hcl
resource "google_pubsub_topic" "siem" {
  count                      = var.enable_siem_export ? 1 : 0
  name                       = "ge-security-siem"
  message_retention_duration = "604800s"   # 7 jours de rattrapage si le SIEM est en panne
}

resource "google_pubsub_subscription" "siem" {
  count                      = var.enable_siem_export ? 1 : 0
  name                       = "ge-security-siem-pull"
  topic                      = google_pubsub_topic.siem[0].id
  ack_deadline_seconds       = 60
  message_retention_duration = "604800s"
  expiration_policy { ttl = "" }            # ne jamais expirer, même sans lecteur
}

resource "google_logging_project_sink" "siem" {
  count                  = var.enable_siem_export ? 1 : 0
  name                   = "ge-security-to-siem"
  destination            = "pubsub.googleapis.com/${google_pubsub_topic.siem[0].id}"
  filter                 = local.security_log_filter   # le MÊME filtre que le bucket ge-security
  unique_writer_identity = true                         # Google crée un compte dédié à ce récepteur
}

resource "google_pubsub_topic_iam_member" "siem_writer" {
  count  = var.enable_siem_export ? 1 : 0
  topic  = google_pubsub_topic.siem[0].id
  role   = "roles/pubsub.publisher"
  member = google_logging_project_sink.siem[0].writer_identity   # connu seulement après création du récepteur
}

resource "google_pubsub_subscription_iam_member" "siem_reader" {
  count        = var.enable_siem_export && var.siem_subscriber != "" ? 1 : 0
  subscription = google_pubsub_subscription.siem[0].id
  role         = "roles/pubsub.subscriber"
  member       = var.siem_subscriber
}
```

**Pourquoi le même filtre que le bucket.** Une seule définition (`local.security_log_filter` dans `80_logging.tf`) :
ce que la sécurité garde un an et ce que le SOC reçoit ne peuvent pas diverger.

**Pourquoi pull plutôt que push.** Le SIEM tire les messages à son rythme ; aucune URL du SOC n'est exposée.

## 4. Appliquer

```bash
terraform plan -out=tfplan
# + google_project_service.apis["pubsub.googleapis.com"]
# + google_pubsub_topic.siem[0]
# + google_pubsub_subscription.siem[0]
# + google_logging_project_sink.siem[0]
# + google_pubsub_topic_iam_member.siem_writer[0]
# + google_pubsub_subscription_iam_member.siem_reader[0]
```

Après l'apply, transmettre au SOC :

```bash
terraform output siem_subscription     # projects/P/subscriptions/ge-security-siem-pull
```

## 5. Vérifier

```bash
gcloud pubsub subscriptions pull ge-security-siem-pull --limit=3 --auto-ack --project=$PROJECT_ID
```

Puis le test T21 : modifier un template par PR → l'événement apparaît **dans le SIEM** en quelques minutes.

> `--auto-ack` consomme les messages : à ne faire qu'une fois, avant que le SIEM soit branché.

## 6. Pièges

| Symptôme | Cause |
|---|---|
| Rien n'arrive dans le sujet | Rôle *Publisher* du rédacteur manquant (ne pas le créer à la main : il est dans le code) |
| Le SIEM reçoit, puis plus rien | Abonnement plein (7 jours) → le connecteur est arrêté : alerte côté SOC |
| Doublons dans le SIEM | Normal avec Pub/Sub (livraison « au moins une fois ») : dédoublonner sur `insertId` |

## 7. Variante : projet de journalisation central

Si Acme centralise les journaux dans un projet SOC, remplacer la destination par un **bucket de journaux central**
(`logging.googleapis.com/projects/SOC/locations/eu/buckets/...`) et donner au rédacteur le rôle
`roles/logging.bucketWriter` sur ce bucket. Le reste est identique.
