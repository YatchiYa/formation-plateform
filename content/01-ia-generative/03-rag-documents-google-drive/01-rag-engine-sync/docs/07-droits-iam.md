# 07. Droits : qui peut faire quoi (matrice IAM)

**Le but :** savoir exactement quelle identité a quel droit, pourquoi, et ce qui casse sans lui. Chaque ligne
« vérifié » a été constatée en vrai sur le projet de test (erreur obtenue sans le droit).

---

## 1. Les identités

| Identité | Créée par | Sert à |
|---|---|---|
| `rag-kit-sa@<projet>.iam.gserviceaccount.com` | le kit | Identité du **service** (interface + agent) et du **job** de synchro |
| `service-<numéro>@gcp-sa-vertex-rag.iam.gserviceaccount.com` | **Google** (1re utilisation de RAG Engine) | **Importe** les fichiers (Drive, bucket) dans le corpus, appelle le layout parser |
| `rag-kit-scheduler-sa@…` | le kit | Lance le job toutes les 10 min (Cloud Scheduler) |
| `rag-kit-build-sa@…` | le kit | Construit l'image (Cloud Build) |
| Vous et vos collègues | — | Ouvrent l'interface |

(`rag-kit` = valeur de `PREFIX`.)

## 2. La matrice

| Identité | Ressource | Rôle | Pourquoi | Sans lui |
|---|---|---|---|---|
| `rag-kit-sa` | projet | `roles/aiplatform.user` | Appeler Gemini ; chercher, importer, supprimer dans le corpus | Aucune réponse, aucune synchro |
| | projet | `roles/discoveryengine.viewer` | **Reranking** : permission `discoveryengine.rankingConfigs.rank` (API Ranking). **Piège vérifié : `discoveryengine.user` ne la contient PAS**, `viewer` (et `editor`) oui | **Vérifié** : `403 Permission 'discoveryengine.rankingConfigs.rank' denied`, l'agent ne trouve rien |
| | projet | `logging.logWriter`, `monitoring.metricWriter`, `cloudtrace.agent`, `telemetry.writer` | Journaux, métriques, traces | Pas d'observabilité |
| | bucket | `roles/storage.objectAdmin` | Écrire les dépôts, `config.json`, les rapports de synchro | Dépôt et synchro en échec |
| | job `rag-kit-sync` | `roles/run.jobsExecutorWithOverrides` | Lancer le job avec `TRIGGER=auto/manuel` (bouton, webhook). **`run.invoker` ne suffit pas** (pas de `run.jobs.runWithOverrides`, vérifié) | Bouton en erreur 403 |
| | secrets `rag-kit-oauth-client`, `rag-kit-google-tokens` | `secretAccessor` (+ `secretVersionManager` sur les jetons) | Lire le client OAuth ; ranger/détruire les jetons des comptes connectés | Connexion Google impossible |
| | job `rag-kit-sync` | `roles/run.viewer` | Savoir si une synchro tourne (« Synchronisation en cours… ») | État inconnu |
| | **dossier Drive** | **Lecteur** (partage Drive) | Lister les fichiers → **détecter les suppressions**, vérifier un dossier à l'ajout | L'interface refuse le dossier : « Le kit ne voit pas ce dossier » |
| Agent de service RAG | bucket | `roles/storage.objectViewer` | Lire les fichiers déposés | Dépôts jamais indexés |
| | bucket | `roles/storage.objectCreator` | Écrire le rapport détaillé d'import (`sync/runs/…`) | **Vérifié** : `403 … does not have storage.objects.create access`, la synchro échoue |
| | **dossier Drive** | **Lecteur** (partage Drive) | Importer les fichiers | **Vérifié** : import par dossier = 0 fichier **sans erreur** ; import par fichier (ce que fait le kit) = `404 Unable to find some Google Drive resource(s)`. Le kit l'affiche : « N fichier(s) illisible(s) pour l'agent RAG… » |
| | Document AI | *(rien à ajouter)* | Layout parser | Vérifié : fonctionne avec le rôle `aiplatform.ragServiceAgent` donné par Google |
| `rag-kit-scheduler-sa` | job | `roles/run.jobsExecutorWithOverrides` | Lancer le job avec `TRIGGER=auto` | Plus de synchro planifiée |
| **Tout le monde** (`allUsers`) | service `rag-kit-hook` | `roles/run.invoker` | Google doit pouvoir envoyer les notifications push. Le service n'accepte que les canaux ouverts par le kit (identifiant + jeton secret, sinon 403) et ne fait que lancer une synchro | Pas de push (`PUSH=false` : synchro planifiée seule) |
| Comptes Google connectés | leur Drive | portée OAuth `drive.readonly` | Lecture seule, accordée par la personne sur l'écran Google | — |
| `rag-kit-build-sa` | projet | `storage.objectViewer`, `artifactregistry.writer`, `logging.logWriter` | Lire le code envoyé, ranger l'image, écrire ses journaux | Construction en échec |
| Utilisateurs (`USERS`) | service `rag-kit` | `roles/run.invoker` | Ouvrir l'interface (via le proxy) | `403 Forbidden` |

**Propriétaires du projet** : ils ont déjà `run.invoker` partout, inutile de les lister.

## 3. Pourquoi un seul compte pour le service et le job

Ils touchent les mêmes ressources (corpus, bucket, Drive), et RAG Engine n'a pas de rôle « lecture seule » sur un
corpus : `aiplatform.user` sert à chercher **et** à importer. Deux comptes ajouteraient une adresse de plus à mettre
dans chaque partage Drive, sans vraie séparation.

**Variante plus stricte** (si votre sécurité l'exige) : un compte `rag-kit-web-sa` pour le service, sans accès Drive,
avec `aiplatform.user`, `discoveryengine.viewer`, `objectAdmin` sur le bucket et `run.invoker`/`run.viewer` sur le job ;
le compte `rag-kit-sa` reste celui du job (seul à lire Drive). Conséquence : l'interface ne peut plus vérifier un
dossier à l'ajout (elle l'accepte, et c'est le rapport de synchro qui signale un problème de partage).

## 4. Qui déploie : droits minimaux

Propriétaire du projet = le plus simple. Sinon, ces rôles suffisent pour `terraform apply` ou `deployer_shell.sh` :

| Rôle | Pour |
|---|---|
| `roles/serviceusage.serviceUsageAdmin` | Activer les API |
| `roles/iam.serviceAccountAdmin` + `roles/iam.serviceAccountUser` | Créer les comptes et les attacher au service/job |
| `roles/resourcemanager.projectIamAdmin` | Donner les rôles projet aux comptes |
| `roles/storage.admin` | Bucket et ses droits |
| `roles/aiplatform.admin` | Corpus RAG (+ palier RagManagedDb) |
| `roles/documentai.admin` | Layout parser |
| `roles/run.admin` | Service, job et leurs droits |
| `roles/cloudscheduler.admin` | Planification |
| `roles/artifactregistry.admin` | Dépôt d'images |
| `roles/cloudbuild.builds.editor` | Lancer la construction |

## 5. Accès à l'interface : proxy ou IAP

**Par défaut : service privé + proxy.** `gcloud run services proxy rag-kit …` ouvre `http://localhost:8080` en
ajoutant votre jeton : seuls les comptes qui ont `run.invoker` passent. **Vérifié avec un compte Gmail, projet sans
organisation.** Rien n'est exposé sur Internet sans authentification.

**Origines autorisées (`ALLOW_ORIGINS`).** ADK refuse les appels d'une page dont l'origine ne correspond pas à
l'hôte (protection contre les attaques inter-sites). Derrière le proxy, la page est sur `http://localhost:<port>` et
l'hôte vu par le service est `…run.app` : le kit autorise donc `localhost` et `127.0.0.1` (tout port) par défaut.
Le service restant privé, une page locale ne passe qu'avec un proxy ouvert par un compte autorisé.

**Option : IAP** (une vraie URL https, connexion Google dans le navigateur, pas de proxy). Il faut une
**organisation** Google Cloud (écran de consentement interne). Non activée dans le kit car impossible à tester sur
le projet de test (sans organisation) ; pour l'activer (commandes **non testées** ici, à valider sur un projet
avec organisation) :

```bash
gcloud beta run services update rag-kit --region=europe-west4 --iap
gcloud beta iap web add-iam-policy-binding --resource-type=cloud-run --service=rag-kit --region=europe-west4 \
  --member=group:equipe@exemple.com --role=roles/iap.httpsResourceAccessor
```

(En Terraform : `iap_enabled = true` sur `google_cloud_run_v2_service.app` et `google_iap_web_cloud_run_service_iam_member`.)

## 6. Ce qu'un utilisateur de l'interface peut faire

Toute personne qui ouvre l'interface peut : interroger **tout** le corpus, ajouter/retirer un dossier Drive (s'il
est partagé avec le kit), déposer et supprimer des fichiers **déposés**, lancer une synchro. Elle ne peut **pas**
supprimer un fichier de Drive (le kit n'a que la lecture). Donnez l'accès en conséquence.
