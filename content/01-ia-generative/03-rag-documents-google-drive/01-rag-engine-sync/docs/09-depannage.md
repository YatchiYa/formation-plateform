# 09. Dépannage

**Le but :** retrouver vite la cause d'un problème. Chaque erreur ci-dessous a été **rencontrée en vrai** pendant les
tests du kit (sauf mention), avec le message exact.

**Où regarder d'abord :**

```bash
source scripts/config.sh config/test.env
gcloud storage cat gs://$BUCKET/sync/last.json                                         # dernière synchro
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE'" AND severity>=ERROR' \
  --limit=20 --freshness=1h --format='value(textPayload)'                               # erreurs du service
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="'$SYNC_JOB'"' --limit=20 \
  --format='value(textPayload)'                                                        # journaux de la synchro
```

---

## 1. Déploiement

| Message | Cause | Solution |
|---|---|---|
| `Cloud Resource Manager API has not been used in project … before or it is disabled` (Terraform, sur `google_project_service`) | Terraform a besoin de cette API pour activer les autres | `gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID`, puis relancer |
| `Publisher model is not allowed for use in Vertex RAG yet` (création du corpus) | Modèle d'embeddings non accepté par RAG Engine (vu avec `gemini-embedding-001`) | Garder `text-multilingual-embedding-002` (défaut) |
| Construction d'image : `403` au 1er essai | Droits d'un compte de construction tout neuf pas encore actifs | Rien : le déploiement réessaie 4 fois à 40 s d'intervalle |
| Après un 1er `apply` en échec : `… is tainted, so must be replaced` sur des API | Ressources marquées « à refaire » | Sans danger (`disable_on_destroy = false`) |
| Le service reçoit `CORPUS=4611686018427387904` | (corrigé dans le kit) `name` du corpus Terraform = numéro seul | Le kit utilise `id` (chemin complet) |

## 2. Interface et réponses

| Symptôme / message | Cause | Solution |
|---|---|---|
| `403 Forbidden` dans le navigateur | Vous n'avez pas `run.invoker` sur le service | Ajouter votre compte à `USERS` puis `apply` |
| L'interface s'affiche mais le chat ne répond pas ; navigateur : `403` sur `/apps/assistant_documents/users/…/sessions` | (corrigé dans le kit) ADK refuse une origine qui ne correspond pas à l'hôte : derrière le proxy, `localhost:<port>` ≠ `…run.app` | Le kit autorise `localhost` (`ALLOW_ORIGINS`) ; avec IAP ou un autre domaine, ajoutez-le à `ALLOW_ORIGINS` |
| « La recherche dans les documents a échoué (RuntimeError) » ; journal : `Permission 'discoveryengine.rankingConfigs.rank' denied` | Compte du kit sans `roles/discoveryengine.viewer` (reranking). **`discoveryengine.user` ne suffit pas** (il ne contient pas cette permission, vérifié) | Inclus dans le kit ; si vous venez de l'ajouter : attendre la propagation IAM (jusqu'à 7 min) |
| Réponse très lente puis `Erreur 500` ; journal : `429 RESOURCE_EXHAUSTED` | Quota partagé de Gemini saturé (fréquent sur un projet neuf) | L'agent réessaie 6 fois (2 à 30 s) ; si ça persiste : revenir au défaut `gemini-2.5-flash` / `europe-west4`, ou demander du débit provisionné (Provisioned Throughput) |
| `404 … Publisher model projects/…/locations/europe-west4/publishers/google/models/gemini-3.5-flash` | Modèle indisponible dans la région | Gemini 3.5 : `MODEL_LOCATION=global` ; ou le défaut `gemini-2.5-flash` en `europe-west4` |
| « Je ne trouve pas cette information » alors que le document existe | Pas encore indexé, ou mal lu | Vérifier qu'il est dans **Documents indexés** ; regarder le rapport (fichier en échec ?) ; PDF scanné : garder `LAYOUT_PARSER=true` |
| L'interface reste sur « Chargement… » | Proxy arrêté, ou service en cours de démarrage (1re requête ≈ 10 s) | Relancer `bash scripts/ouvrir_interface.sh` |
| « dépasse 30 Mo » | Limite de requête de Cloud Run (32 Mo) | Mettre le fichier dans le dossier Drive |

## 3. Synchro

| Symptôme / message | Cause | Solution |
|---|---|---|
| **À vérifier** : « Drive « … » : N fichier(s) illisible(s) pour l'agent RAG (…). Partagez le dossier (lecteur) avec service-…@gcp-sa-vertex-rag… » (journal du job : `404 Unable to find some Google Drive resource(s)`) | Agent de service RAG absent du partage du dossier (ou d'un fichier) | Ajouter l'adresse au partage du dossier ([04](04-connecter-drive.md)) |
| « Drive « … » illisible (introuvable : plus partagé avec rag-kit-sa@…, ou supprimé) » | Le compte du kit ne voit plus le dossier. **Cas vérifié : après `destroy` + `apply`**, le compte recréé est une nouvelle identité pour Drive | Repartager avec `rag-kit-sa@…`, ou retirer le dossier. Rien n'est supprimé de l'index tant que ça dure |
| `403 … service-…@gcp-sa-vertex-rag… does not have storage.objects.create access` | Agent RAG sans `objectCreator` sur le bucket (rapport d'import) | Inclus dans le kit ; vérifier `gcloud storage buckets get-iam-policy gs://$BUCKET` |
| Journal du job : `"statut": "occupe"` répété | Deux passes en même temps (RAG Engine n'accepte qu'une opération par corpus) | Normal : la passe attend 15 s et recommence (15 min au plus) |
| Fichier compté « en échec » | Type non supporté (image, vidéo…), fichier protégé, trop gros | Détail : `gcloud storage cat "gs://$BUCKET/sync/runs/*.ndjson" \| grep -v '"Status": "OK"'` |
| Synchro qui ne passe plus toute seule | Planification en pause ou en échec | `gcloud scheduler jobs describe $SYNC_JOB --location=$REGION` (état, dernier code) |
| Tout est réindexé à chaque passe | Réglage de parsing/découpage changé entre deux passes | Normal une fois après un changement ; sinon, vérifier que `LAYOUT_PARSER` est identique pour le service et le job |

## 4. Connexion Google (v2)

| Message | Cause | Solution |
|---|---|---|
| « Connexion Google pas encore configurée » | Pas de client OAuth dans le secret `rag-kit-oauth-client` | [04-bis, partie 2](04-bis-connexion-google.md#2-créer-le-client-oauth-console-une-fois) |
| Écran Google `redirect_uri_mismatch` | Interface ouverte sur un autre port que 8080, ou URI absente du client | `bash scripts/ouvrir_interface.sh` (port 8080) ; sinon ajouter l'URI dans le client OAuth |
| Écran Google `access_denied` / « app non validée » bloquant | Compte absent des **utilisateurs test** (application Externe en test) | Ajouter le compte dans Google Auth Platform → Audience |
| « L'accès en lecture à Google Drive n'a pas été accordé » | Case Drive décochée sur l'écran Google | Se reconnecter et cocher l'accès Drive |
| Synchro : « Google Drive « … » : RefreshError … invalid_grant » | Jeton expiré (7 jours en mode test) ou accès retiré dans le compte Google | Se reconnecter ; pour éviter les 7 jours : publier l'application ([04-bis, partie 5](04-bis-connexion-google.md#5-à-savoir-pièges)) |
| Le sélecteur ne s'ouvre pas ; console du navigateur : `API key not valid` / origine refusée | Clé limitée à `http://localhost:8080` | Ouvrir l'interface sur le port 8080, ou ajouter le référent à la clé `rag-kit-picker` |
| Journal `rag-kit-hook` : `403` répétés | Notifications d'un ancien canal (source retirée, passe concurrente avant le verrou) : refusées, sans effet | Rien : le canal expire seul (7 jours au plus) |
| Fichier « non récupéré : … exportSizeLimitExceeded » | Google Doc/Slides de plus de 10 Mo à l'export | Le scinder, ou l'exporter en PDF dans Drive |

## 5. En local

| Message | Cause | Solution |
|---|---|---|
| `Request had insufficient authentication scopes` (Drive) | Identifiants locaux sans le scope Drive | `gcloud auth application-default login --scopes=…cloud-platform,…drive.readonly` ([05](05-utiliser-interface.md#5-lancer-en-local)) |
| `FutureWarning: You are using a non-supported Python version (3.10…)` | Python trop ancien pour les bibliothèques Google | Python 3.12 (comme l'image) |
| `vertexai.rag module is deprecated` | Avertissement : ADK 2.10 impose `google-cloud-aiplatform` < 2 | Sans conséquence ; migrera vers `agentplatform` avec ADK |
