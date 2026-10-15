# 03-1. Déployer avec le **script shell** (gcloud)

**Le but :** tout créer avec `gcloud` seul, sans Terraform, en une commande relançable.

**Les autres méthodes, même résultat :** [03-2 Terraform](03-2-deployer-terraform.md) · [03-3 Console](03-3-deployer-console.md).

> **Ne mélangez pas** les méthodes sur un même `PREFIX` : Terraform ne connaît pas ce que crée le script, et
> inversement. Pour essayer les deux dans un projet, utilisez deux préfixes (`config/test.env` : `rag-kit`,
> `config/test-shell.env` : `rag-sh`).

> **Testé en vrai** le 14/10/2026 sur `main-project-511608` avec `config/test-shell.env` (préfixe `rag-sh`,
> `LAYOUT_PARSER=false`) : déploiement depuis zéro (5 min 09), relance (1 min 50, image réutilisée), `test_e2e.py`
> (TOUT EST OK), `supprimer_shell.sh`. Sorties réelles ci-dessous.

---

## 1. Ce que fait le script, étape par étape

`scripts/deployer_shell.sh` — 12 étapes, chacune vérifie ce qui existe avant d'agir :

| Étape | Commande principale | Si ça existe déjà |
|---|---|---|
| 1. API | `gcloud services enable …` (16 API, dont `cloudresourcemanager`) | Sans effet |
| 2. Comptes | `gcloud iam service-accounts create` ×3 | Ignoré |
| 3. Droits projet | `gcloud projects add-iam-policy-binding` | Sans effet |
| 4. Bucket | `gcloud storage buckets create` + `config.json` (dossiers de `DRIVE_FOLDERS`) | `config.json` existant **gardé** |
| 5. Corpus | API REST `ragCorpora` (pas de commande gcloud pour RAG Engine) | Retrouvé par son nom |
| 6. Agent RAG | droits sur le bucket | Sans effet |
| 7. Layout parser | API REST Document AI (`eu`) | Retrouvé par son nom |
| 8. Image | `gcloud builds submit` (étiquette = hachage du code) | **Pas reconstruite** si le code n'a pas changé |
| 9. Job | `gcloud run jobs deploy` + droits | Mis à jour |
| 10. Planification | `gcloud scheduler jobs create/update http` | Mise à jour |
| 11. Service | `gcloud run deploy --no-allow-unauthenticated --max-instances=1` | Nouvelle révision |
| 12. Accès | `gcloud run services add-iam-policy-binding` pour chaque `USERS` | Sans effet |

## 2. Pas à pas

```bash
cd gcp_rag/01-rag-engine-sync
source scripts/config.sh config/test-shell.env
bash scripts/deployer_shell.sh
```

Fin obtenue :

```
== 1/12 API
== 2/12 Comptes de service
== 3/12 Droits sur le projet
   rag-sh-sa@main-project-511608.iam.gserviceaccount.com et rag-sh-build-sa@main-project-511608.iam.gserviceaccount.com : rôles en place
== 4/12 Bucket gs://main-project-511608-rag-sh
== 5/12 Corpus RAG « rag-sh »
   projects/main-project-511608/locations/europe-west4/ragCorpora/2882303761517117440
== 6/12 Agent de service RAG sur le bucket
   service-100000000005@gcp-sa-vertex-rag.iam.gserviceaccount.com : lecture + écriture des rapports
== 7/12 Layout parser (Document AI, eu)
   (désactivé)
== 8/12 Image (Cloud Build)
   nouvel essai dans 40 s
== 9/12 Job de synchro « rag-sh-sync »
== 10/12 Planification « */10 * * * * »
   OK
== 11/12 Service « rag-sh » (privé)
== 12/12 Accès à l'interface
   user:noreply.syctra@gmail.com

== Terminé.
   Partagez chaque dossier Drive (Lecteur) avec :
     rag-sh-sa@main-project-511608.iam.gserviceaccount.com
     service-100000000005@gcp-sa-vertex-rag.iam.gserviceaccount.com
   Ouvrir l'interface :
     gcloud run services proxy rag-sh --region=europe-west4 --project=main-project-511608 --port=8080   puis http://localhost:8080
```

Durée : **5 min 09** depuis zéro (« nouvel essai dans 40 s » à l'étape 8 = le compte de construction tout neuf
n'avait pas encore ses droits : normal, le script réessaie). **Relance sans changement : 1 min 50**, image
réutilisée (« …/rag-sh/app:73a849db53c4 existe déjà (code inchangé) »).

Puis, comme pour Terraform : partager le dossier Drive avec les 2 adresses affichées ([04](04-connecter-drive.md)),
`bash scripts/ouvrir_interface.sh`, **Synchroniser maintenant**.

## 3. Tester

```bash
PORT=8081 bash scripts/ouvrir_interface.sh &          # proxy en arrière-plan
python3 scripts/test_e2e.py http://localhost:8081 "Quelle est l'indemnité mensuelle de télétravail ?" "47"
```

```
[1] l'API répond
    OK  corpus projects/main-project-511608/locations/europe-west4/ragCorpora/2882303761517117440
[2] dépôt de e2e-gicq-7459.txt (code GICQ-7459) puis synchro
    OK  déposé : ['e2e-gicq-7459.txt'] (synchro lancee)
    OK  synchro ok en 25.7 s
    OK  e2e-gicq-7459.txt indexé (origine dépôt)
    OK  l'agent répond GICQ-7459  (réponse : "Le code d'accès du local à vélos du bâtiment Héron est GICQ-7459.\n\nSources :\n* [e2e-gicq-7459.txt](https://storage.c…")
    OK  et cite le fichier
[3] modification : nouveau code GFWM-9036
    OK  réindexé ({'source': 'Fichiers déposés', 'importes': 1, 'inchanges': 0, 'echecs': 0})
    OK  l'agent répond GFWM-9036 (plus GICQ-7459)  (réponse : "Le code d'accès du local à vélos du bâtiment Héron est GFWM-9036.\n\nSources :\n[e2e-gicq-7459.txt](ht…")
[4] suppression
    OK  1 fichier(s) retiré(s) de l'index
    OK  e2e-gicq-7459.txt absent de l'index
    OK  l'agent ne connaît plus le code
[5] Drive : « Quelle est l'indemnité mensuelle de télétravail ? »
    OK  réponse contient « 47 »  ("L'indemnité mensuelle de télétravail est de 47 euros [politique-teletravail](https://docs.google.com/document/d/1iSBUTTFqDhKCNFC0H…")
    OK  avec un lien Drive

TOUT EST OK
```

## 4. Modifier

Modifiez le `.env` ou le code, `source scripts/config.sh …`, relancez `bash scripts/deployer_shell.sh`. Seul ce qui a
changé change (nouvelle image seulement si le code a changé).

## 5. Supprimer

```bash
bash scripts/supprimer_shell.sh      # tapez « oui »
```

Puis [10-tout-supprimer, parties 3 et 4](10-tout-supprimer.md#3-arrêter-le-coût-fixe-ragmanageddb).
