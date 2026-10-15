---
title: Aide-mémoire gcloud
description: Les commandes gcloud du quotidien, une par diapositive.
type: slides
tags: [gcloud, cli, aide-memoire]
level: beginner
date: 2026-09-10
---

# Aide-mémoire gcloud

Les commandes à garder sous la main

---

## Configuration

```bash
gcloud init
gcloud config set project second-project-511608
gcloud config set run/region europe-west1
gcloud config list
```

---

## Configurations multiples

```bash
gcloud config configurations create perso
gcloud config configurations activate perso
gcloud config configurations list
```

---

## Authentification

```bash
gcloud auth login
gcloud auth application-default login
gcloud auth print-access-token
gcloud auth list
```

---

## Activer des API

```bash
gcloud services list --enabled
gcloud services enable aiplatform.googleapis.com run.googleapis.com
```

---

## Cloud Run

```bash
gcloud run deploy assistant --source . --region europe-west1
gcloud run services list
gcloud run services logs read assistant --limit 50
```

---

## IAM

```bash
gcloud projects get-iam-policy second-project-511608 \
  --flatten="bindings[].members" --format="table(bindings.role, bindings.members)"
gcloud projects add-iam-policy-binding second-project-511608 \
  --member="serviceAccount:agent@second-project-511608.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

---

## Cloud Storage

```bash
gcloud storage buckets create gs://mon-bucket --location europe-west1
gcloud storage cp -r ./docs gs://mon-bucket/docs
gcloud storage ls -l gs://mon-bucket/docs
```

---

## Logs

```bash
gcloud logging read 'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --limit 20 --freshness 1h
```

---

## Formats et filtres

```bash
gcloud run services list --format="value(metadata.name)"
gcloud compute instances list --filter="status=RUNNING" --format=json
```

> Ajoutez `--format=json` à n'importe quelle commande pour la scripter avec `jq`.
