---
title: Déploiement continu
description: GitHub Actions avec Workload Identity Federation, sans clé de compte de service.
duration: 1h30
---

## Principe

GitHub émet un jeton OIDC pour chaque exécution de workflow. Google Cloud l'échange, via un **pool Workload Identity**, contre un jeton d'accès de courte durée qui emprunte l'identité d'un compte de service de déploiement. Aucune clé JSON n'est stockée.

> [!WARNING]
> Restreignez toujours le fournisseur OIDC avec une `attribute_condition` sur le dépôt (`assertion.repository == "org/agent-adk"`). Sans condition, n'importe quel dépôt GitHub pourrait tenter l'échange de jeton.

## Le pool et le fournisseur

```hcl
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }
  attribute_condition = "assertion.repository == \"novagen/agent-adk\""
  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}
```

## Le workflow

```yaml title=".github/workflows/deploy.yml"
name: deploy
on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write

env:
  REGION: europe-west1
  IMAGE: europe-west1-docker.pkg.dev/second-project-511608/agents/assistant:${{ github.sha }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/123456789/locations/global/workloadIdentityPools/github/providers/github-oidc
          service_account: deployer@second-project-511608.iam.gserviceaccount.com
      - uses: google-github-actions/setup-gcloud@v2
      - run: gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
      - run: docker build -t $IMAGE . && docker push $IMAGE
      - uses: hashicorp/setup-terraform@v3
      - working-directory: infra
        run: |
          terraform init
          terraform apply -auto-approve -var project_id=second-project-511608 -var image=$IMAGE
```

## Vérifier le déploiement

```bash
URL=$(gcloud run services describe assistant-cloud --region europe-west1 --format 'value(status.url)')
curl -s -H "Authorization: Bearer $(gcloud auth print-identity-token)" "$URL/list-apps"
```

La réponse doit lister `app`. Vous pouvez ensuite créer une session et envoyer un message via les endpoints `/apps/app/users/{user}/sessions` et `/run` de l'API server ADK.
