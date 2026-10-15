---
type: "category"
title: "Agents IA sur Google Cloud"
icon: "🤖"
description: "Le parcours complet : agents ADK, Agent Runtime, Gemini Enterprise, serveurs MCP et sécurité, tout en Terraform."
---
# Learning path: ADK agents on Google Cloud with Terraform

Nine small, working projects. Do them in order; each builds on the previous one.

| # | Folder | You learn | Result |
|---|--------|-----------|--------|
| 01 | [01-adk-cloud-run-terraform](01-adk-cloud-run-terraform/README.md) | ADK basics, Terraform basics, containers, Cloud Run, IAM | A weather agent behind a private HTTPS API (+ dev web UI) |
| 02 | [02-agent-runtime-registry-terraform](02-agent-runtime-registry-terraform/README.md) | Agent Runtime (managed agent hosting), Agent Registry, Gemini Enterprise | A currency agent on Agent Runtime, discoverable in Agent Registry, addable to Gemini Enterprise |
| 03 | [03-google-chat-bridge](03-google-chat-bridge/README.md) | Google Chat apps (Workspace add-ons), service-to-service auth | Your agent answering in Google Chat for people in your company |
| 04 | [04-mcp-server-cloud-run-registry](04-mcp-server-cloud-run-registry/README.md) | MCP (tool servers), FastMCP, private Cloud Run, Agent Registry MCP entries, registry-driven agents | A product-catalog MCP server any agent (ADK, Claude Code, Gemini CLI) can use, discovered via Agent Registry |
| 05 | [05-gemini-enterprise-model-armor](05-gemini-enterprise-model-armor/README.md) | Full Gemini Enterprise as code (identity, licences, data, app, assistant, web UI, agents), Model Armor, threat model, detection | A secured company AI assistant: 3 layers of Model Armor, least privilege, EU residency, alerting |
| 06 | [06-gemini-enterprise-security-baseline](06-gemini-enterprise-security-baseline/README.md) | Socle de sécurité Gemini Enterprise (FR, client Acme) : 6 couches — identité, CMEK, connecteurs génériques fédérés, Model Armor + DLP FR, exposition UE, détection ; options Agent Gateway / VPC-SC | Guide pédagogique en français + deck client |
| 07 | [07-terraform-service-local](07-terraform-service-local/README.md) | Service Terraform « managé » en local : Gitea (≈ GitHub) + Atlantis + MinIO (état), politiques OPA, verrous, approbations | Circuit PR → plan → politiques → approbation → apply, simulé et vérifié automatiquement |
| 08 | [08-gemini-enterprise-securite-acme](08-gemini-enterprise-securite-acme/README.md) | Note de sécurité Acme appliquée : natif console d'abord, puis Terraform (plancher Model Armor sur les agents, Shadow AI, SIEM, Access Approval, VPC-SC élargi, SWP, Agent Registry), tests, journal quotidien | Guide FR + PDF + PPTX, agent sécurisé, scripts de conformité |
| 09 | [09-agents-multi-projets-gemini-enterprise](09-agents-multi-projets-gemini-enterprise/README.md) | Les 6 modalités d'ajout d'un agent dans Gemini Enterprise ; agents d'autres équipes / autres projets ; un agent qui en découvre (Agent Registry) et en appelle un autre ; matrice des droits cross-project | Agent stock (projet A) + orchestrateur (projet B) sur Agent Runtime, publiés dans l'app, script d'ajout de n'importe quel agent |

Tested versions (latest as of Sept 2026): `google-adk 2.10.0`, `google-cloud-aiplatform 2.2.0`,
Terraform `1.16`, provider `hashicorp/google 8.4`, model `gemini-3.5-flash`.

---

## 0. The big picture (names changed in 2026!)

**Vertex AI is now called _Gemini Enterprise Agent Platform_.** You'll still see the old names in APIs,
Terraform, and blog posts:

| Today's name | Older name(s) | Where the old name still shows up |
|---|---|---|
| Gemini Enterprise Agent Platform | Vertex AI | `aiplatform.googleapis.com`, `google_vertex_ai_*` Terraform resources |
| **Agent Runtime** (console: *Deployments*) | Agent Engine, Reasoning Engine | `reasoningEngines/…` resource names, `google_vertex_ai_reasoning_engine` |
| `agentplatform` Python package | `vertexai` package | both ship in `google-cloud-aiplatform` |
| **Agent Registry** | (new) | `agentregistry.googleapis.com`, `gcloud agent-registry` |
| **Gemini Enterprise** (the app employees use) | Agentspace | `discoveryengine.googleapis.com` |

```
             build                      host                     govern / discover            use
  ┌───────────────────┐   ┌──────────────────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
  │ ADK (Python lib)  │──▶│ Cloud Run  (you run the API) │──▶│  Agent Registry  │──▶│ Gemini Enterprise app│
  │ agent + tools     │   │ Agent Runtime (Google runs it)│  │  (catalog of all │   │ Google Chat          │
  └───────────────────┘   └──────────────────────────────┘   │  agents & tools) │   │ other agents (A2A)   │
                                    ▲                        └──────────────────┘   └──────────────────────┘
                                    │ everything created by Terraform
```

**Cloud Run vs Agent Runtime: which one should you use?**

| | Cloud Run (01) | Agent Runtime (02) |
|---|---|---|
| What you deploy | A container you build (FastAPI server made by ADK) | Just your Python source; Google builds and serves it |
| Sessions / memory | You bring them (in-memory, SQL DB…) | Managed sessions + Memory Bank included |
| Gemini Enterprise | Via A2A / Agent Registry | Native: "Add agent → Custom agent via Agent Runtime" |
| Agent Registry | Manual registration (or alpha auto-registration) | Registered automatically |
| Control / cost | Full control; scale to zero; cheap | Less plumbing; paid per use |
| Pick it when | You need custom HTTP routes, a web UI, or other frameworks | You want the enterprise path (Gemini Enterprise, governance) |

---

## 1. One-time setup (on your laptop, or on the `syctra` VM)

```bash
# Tools (already installed on this laptop): gcloud, terraform >= 1.9, python 3.12 (via uv), docker
gcloud --version && terraform version && uv --version && docker --version

# 1. Log in. Two different logins, both needed:
gcloud auth login                         # for the gcloud CLI
gcloud auth application-default login     # "ADC": used by Terraform and Python SDKs  ← was missing here!

# 2. Choose the project
gcloud config set project YOUR_PROJECT_ID
export PROJECT_ID=$(gcloud config get project)

# 3. Billing must be enabled on the project (Cloud Run / Gemini are paid, with free tiers)
gcloud billing projects describe $PROJECT_ID --format='value(billingEnabled)'   # → True
```

> **If you work from the `syctra` VM:** it's **arm64** and Cloud Run needs **amd64** images. The build step uses
> `docker build --platform linux/amd64`, which needs QEMU there: `docker run --privileged --rm tonistiigi/binfmt --install amd64`.
> The simplest option is to run everything from your laptop (x86_64).

A Python environment for local runs (shared by all projects):

```bash
cd ~/Bureau/trash
uv venv -p 3.12 .venv && source .venv/bin/activate
uv pip install "google-adk[a2a,agent-identity]==2.10.0" "google-cloud-aiplatform[agent_engines,adk]==2.2.0" mcp fastmcp==4.0.10 fastapi uvicorn
```

---

## 2. Terraform in 10 minutes (read this before project 01)

Terraform = **you describe the infrastructure you want** in `.tf` files; Terraform works out what to create, change, or delete
to get there.

### The vocabulary

| Concept | Example in these projects | Meaning |
|---|---|---|
| **provider** | `hashicorp/google` | A plugin that knows how to talk to one API (GCP) |
| **resource** | `google_cloud_run_v2_service.agent` | Something Terraform creates and owns. Address = `TYPE.NAME` |
| **data source** | `data.google_project.this` | Something Terraform only **reads** |
| **variable** | `var.project_id` | An input. Set in `terraform.tfvars` or with `-var` |
| **local** | `local.image` | A computed value, like a local variable |
| **output** | `url` | A value printed after apply; read it with `terraform output -raw url` |
| **state** | `terraform.tfstate` | Terraform's memory of what it created. **Never edit it by hand, never commit it** |
| **module** | (each folder is one) | A folder of `.tf` files. All files in a folder are merged; file names are just for humans |

### The files (same layout in every project)

```
terraform/
├── versions.tf               # which Terraform/provider versions + provider config (+ backend)
├── variables.tf              # inputs
├── main.tf                   # the resources
├── outputs.tf                # what you want to read afterwards
└── terraform.tfvars.example  # copy to terraform.tfvars and fill in
```

### The loop you'll repeat forever

```bash
terraform init       # download providers (once, or after changing versions.tf)
terraform fmt        # format files
terraform validate   # syntax/type check, no cloud calls
terraform plan       # DRY RUN: shows + create, ~ update, - destroy, -/+ replace. READ IT.
terraform apply      # does it (asks "yes")
terraform output     # show outputs
terraform destroy    # delete everything this folder created
```

Useful extras:

```bash
terraform state list                     # what Terraform manages
terraform state show google_cloud_run_v2_service.agent
terraform plan -var model=gemini-3.7-flash    # override a variable once
terraform apply -replace=terraform_data.image # force-rebuild one resource
terraform console                        # try out expressions: > local.image
```

### Patterns used here (and why)

- `for_each = toset([...])` → one resource per item (enable N APIs, grant N roles) without copy-pasting.
- `count = var.public ? 1 : 0` → an **optional** resource.
- `depends_on` → an ordering Terraform can't infer on its own (e.g. IAM must exist before the service starts).
- `google_project_service` with `disable_on_destroy = false` → enabling APIs is part of the code, and destroy never switches off an API
  something else still uses.
- The **image tag = hash of the source files** → no code change means no rebuild and no new revision. Deploys stay reproducible.

### Best practices

1. **Remote state for teams**: uncomment the `backend "gcs"` block in `versions.tf` (bucket with versioning enabled).
   Local state is fine while you learn alone.
2. **Pin versions** (`~> 8.4` = any 8.x ≥ 8.4) and commit `.terraform.lock.hcl`.
3. **Never put secrets in `.tf` / `.tfvars`**. Use Secret Manager and reference it (`secret_env` / `value_source`).
4. **Always read `plan`**, especially lines with `-/+` (replace) or `-` (destroy).
5. **Least privilege**: each workload gets its own service account with only the roles it needs (done in every project here).
6. **One folder = one state = one lifecycle.** That's why 01/02/03 are separate: you can destroy one without touching the others.
7. In CI/CD: `terraform plan -out=tfplan` on the PR, then `terraform apply tfplan` after review.

---

## 3. Costs and cleanup

Everything scales to zero, so idle cost is almost nil (Artifact Registry storage costs a few cents). When you're done:

```bash
(cd 09-agents-multi-projets-gemini-enterprise/terraform && terraform destroy)
(cd 08-gemini-enterprise-securite-acme/terraform && terraform destroy)
(cd 06-gemini-enterprise-security-baseline/terraform && terraform destroy)
(cd 05-gemini-enterprise-model-armor/terraform && terraform destroy)
(cd 04-mcp-server-cloud-run-registry/terraform && terraform destroy)
(cd 03-google-chat-bridge/terraform && terraform destroy)
(cd 02-agent-runtime-registry-terraform/terraform && terraform destroy)
(cd 01-adk-cloud-run-terraform/terraform && terraform destroy)
```

## 4. Official docs

- ADK: https://adk.dev · Cloud Run deploy: https://adk.dev/deploy/cloud-run/ · Agent Runtime deploy: https://adk.dev/deploy/agent-runtime/
- Agent Runtime + Terraform: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/use-terraform
- Agent Registry: https://docs.cloud.google.com/agent-registry
- Register an ADK agent in Gemini Enterprise: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent
- Google Chat + ADK: https://developers.google.com/workspace/add-ons/chat/quickstart-adk-agent
- Terraform google provider: https://registry.terraform.io/providers/hashicorp/google/latest/docs
