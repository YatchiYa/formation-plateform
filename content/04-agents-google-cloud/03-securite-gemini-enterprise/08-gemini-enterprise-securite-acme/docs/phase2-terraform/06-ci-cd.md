# 06. CI/CD : du commit à la production, sans clic

**Pour qui :** DevOps (mise en place), sécurité (validation), PM (compréhension du circuit).

---

## 1. Le circuit

```
 Développeur          GitHub                         Service Terraform (CI)            Google Cloud
 ───────────         ────────                        ──────────────────────            ────────────
 branche + PR ──▶  PR ouverte ──(webhook)──▶  terraform plan  ──▶ commentaire dans la PR
                     │                                         (lecture seule sur GCP)
                     ▼
              Revue + CODEOWNERS
              (sécurité obligatoire sur les garde-fous)
                     │ approuvée + fusion dans main
                     ▼
                  main ──────────────────▶  terraform apply  ──────────────────▶ ressources
                                              │
                                              ▼
                                   verify_controls.sh   ── KO ──▶ pipeline en échec + alerte
                                              │ OK
                                              ▼
                              alerte « garde-fou modifié » reçue ── la sécurité la rapproche de la PR
```

**Quatre règles :**
1. **Personne** n'exécute `apply` depuis son poste en production. Seul le compte de la CI a les droits d'écriture.
2. Les fichiers garde-fous exigent l'**approbation de l'équipe sécurité** (CODEOWNERS).
3. Le `plan` publié dans la PR est **celui qui sera appliqué** (pas de recalcul surprise).
4. Le contrôle de conformité clôt chaque déploiement.

---

## 2. CODEOWNERS : la sécurité valide ce qui la concerne

Fichier `.github/CODEOWNERS` du dépôt :

```
# Par défaut : l'équipe plateforme
*                                   @acme/plateforme-cloud

# Garde-fous : approbation de la sécurité OBLIGATOIRE
terraform/20_data_protection.tf     @acme/securite-ia
terraform/30_ai_guardrails.tf       @acme/securite-ia
terraform/60_advanced.tf            @acme/securite-ia
terraform/70_detection.tf           @acme/securite-ia
terraform/75_shadow_ai.tf           @acme/securite-ia
terraform/80_logging.tf             @acme/securite-ia @acme/dpo
terraform/85_siem_access.tf         @acme/securite-ia
terraform/95_secure_web_proxy.tf    @acme/securite-ia
envs/*.tfvars                       @acme/securite-ia
```

Dans GitHub : *Settings* → *Branches* → règle sur `main` → **Require a pull request**, **Require review from Code Owners**,
**Require status checks** (le job `plan`), **Do not allow bypassing**.

---

## 3. Pipeline GitHub Actions (exemple complet)

Si Acme utilise son **service Terraform managé** (Atlantis, Terraform Enterprise, Spacelift…), c'est lui qui joue ce
rôle : le circuit est le même (voir le projet 07, simulé en local). Sinon, ce workflow suffit.

L'authentification se fait par **Workload Identity Federation** : aucun secret ni clé JSON dans GitHub.

```yaml
# .github/workflows/terraform.yml
name: terraform
on:
  pull_request:
    paths: ["terraform/**", "envs/**"]
  push:
    branches: [main]
    paths: ["terraform/**", "envs/**"]

permissions:
  contents: read
  id-token: write          # jeton OIDC pour la fédération d'identité
  pull-requests: write     # publier le plan en commentaire

env:
  TF_IN_AUTOMATION: "true"
  ENV: recette             # un job par environnement / domaine en pratique

jobs:
  plan:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: terraform } }
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/123456/locations/global/workloadIdentityPools/github/providers/acme
          service_account: tf-plan@acme-ge-recette.iam.gserviceaccount.com     # LECTURE seule
      - uses: hashicorp/setup-terraform@v3
        with: { terraform_version: "1.16.3" }
      - run: terraform init -input=false -backend-config="prefix=securite-acme/${ENV}"
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - id: plan
        run: terraform plan -input=false -no-color -var-file=../envs/${ENV}.tfvars -out=tfplan | tee plan.txt
      - name: Refuser toute destruction non annoncée
        run: |
          if grep -E "^\s+# .* (will be destroyed|must be replaced)" plan.txt && \
             ! grep -q "destruction-approuvee" <<< "${{ join(github.event.pull_request.labels.*.name, ' ') }}"; then
            echo "::error::Le plan détruit ou remplace des ressources. Ajouter le label 'destruction-approuvee' après revue."
            exit 1
          fi
      - uses: actions/github-script@v7
        with:
          script: |
            const plan = require('fs').readFileSync('terraform/plan.txt', 'utf8').slice(-60000);
            github.rest.issues.createComment({ ...context.repo, issue_number: context.issue.number,
              body: "### terraform plan (" + process.env.ENV + ")\n```\n" + plan + "\n```" });

  apply:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: recette      # protection d'environnement GitHub : approbation manuelle possible
    defaults: { run: { working-directory: terraform } }
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/123456/locations/global/workloadIdentityPools/github/providers/acme
          service_account: tf-apply@acme-ge-recette.iam.gserviceaccount.com    # ÉCRITURE
      - uses: hashicorp/setup-terraform@v3
        with: { terraform_version: "1.16.3" }
      - uses: google-github-actions/setup-gcloud@v2
      - run: terraform init -input=false -backend-config="prefix=securite-acme/${ENV}"
      - run: terraform apply -input=false -auto-approve -var-file=../envs/${ENV}.tfvars
      - name: Contrôle de conformité
        working-directory: .
        run: PROJECT_ID=$(terraform -chdir=terraform output -raw project_id 2>/dev/null || echo acme-ge-recette) APP_ID=acme-ge ./scripts/verify_controls.sh
```

**Deux comptes de service, deux niveaux de droits :** `tf-plan` (lecture, utilisé sur les PR, donc sur du code non
encore relu) et `tf-apply` (écriture, utilisé seulement sur `main`). La fédération d'identité limite `tf-apply` à la
branche `main` du dépôt (condition d'attribut `assertion.ref == 'refs/heads/main'`).

> Le plan est recalculé au moment de l'apply : entre-temps, un autre changement a pu passer. Avec un service type
> Atlantis, le plan relu **est** celui appliqué (verrou par PR). C'est un argument pour le service managé.

---

## 4. Un projet par domaine (mesure 8)

```
envs/
├── recette.tfvars
├── rh.tfvars          project_id = "acme-ge-rh",      user_groups = ["group:ge-rh@acme.example"]
└── finance.tfvars     project_id = "acme-ge-finance", user_groups = ["group:ge-finance@acme.example"]
```

Même code, **un état par domaine** (`-backend-config="prefix=securite-acme/rh"`), une matrice de jobs dans le
pipeline. Un domaine compromis ou mal configuré n'expose pas les autres.

---

## 5. Après l'apply : rapprocher l'alerte de la PR

Chaque modification d'un garde-fou déclenche l'alerte « Gemini Enterprise : modification d'un garde-fou de sécurité ».
La sécurité vérifie : **auteur = compte `tf-apply`**, **heure = fin du job**, **PR fusionnée correspondante**. Toute alerte
sans PR est un incident ([docs/04 §5](../04-exploitation-journaliere.md#5-que-faire-quand-une-alerte-sonne)).

## 6. Dérive : détecter les clics en console

Planifier un job quotidien `terraform plan -detailed-exitcode` (code 2 = différences). Une différence = quelqu'un a
modifié en console : on remet le code (`apply`) et on cherche l'auteur dans l'audit.
