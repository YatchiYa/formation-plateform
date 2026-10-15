---
type: "article"
description: "Un premier agent ADK (météo) derrière une API HTTPS privée sur Cloud Run, déployé de bout en bout avec Terraform."
tags: ["adk", "cloud-run", "terraform", "iam"]
level: "beginner"
duration: "2h"
usecases: ["assistant-interne", "automatisation-processus"]
platforms: ["vertex-ai"]
date: "2026-09-29"
updated: "2026-10-14"
authors: ["Youcef"]
---
# Project 01: an ADK agent on Cloud Run, deployed with Terraform

**Goal:** write a small AI agent in Python with Google's **ADK**, try it on your machine, then have **one**
`terraform apply` build it, push it, and run it on **Cloud Run** behind a private HTTPS URL. Then call it,
test it, watch it, and delete it.

**You'll understand:** what an "agent" really is in code · how ADK turns it into a web API · what a container
is · what Cloud Run does · what every Terraform line does · how Google Cloud IAM protects the agent.

> Start with the root [README](../../index.md) sections 1 (setup) and 2 (Terraform in 10 minutes).

---

## Contents

1. [Concepts first (for beginners)](#1-concepts-first)
2. [The files, and what each one does](#2-the-files)
3. [The agent code, explained line by line](#3-the-agent-code-explained)
4. [The web server (`main.py`), explained](#4-the-web-server-mainpy)
5. [The container (`Dockerfile`), explained](#5-the-container-dockerfile)
6. [The Terraform, explained block by block](#6-the-terraform-explained)
7. [Step by step: run locally → deploy → call](#7-step-by-step)
8. [Calling the agent (API reference)](#8-calling-the-agent-api-reference)
9. [Testing](#9-testing)
10. [Monitoring: logs, traces, metrics](#10-monitoring)
11. [Change the agent and redeploy](#11-change-and-redeploy)
12. [Sessions: why only 1 instance](#12-sessions)
13. [Best practices and next steps](#13-best-practices)
14. [Troubleshooting](#14-troubleshooting)
15. [Clean up](#15-clean-up)

---

## 1. Concepts first

**LLM (Gemini).** A model that takes text and returns text. On its own it can't *do* anything: it can't look up the
weather, query a database, or send an email.

**Agent.** An LLM plus **instructions** (its job) plus **tools** (Python functions it may call). The loop is:

```
user: "Weather in Paris?"
  │
  ▼
LLM reads instruction + question + the list of available tools
  │  decides: "I should call get_weather(city='Paris')"
  ▼
ADK runs YOUR Python function get_weather("Paris") → {"status":"success","report":"...sunny, 24°C"}
  │
  ▼
LLM reads the tool result → writes the final answer: "It's sunny and 24°C in Paris."
```

The LLM **never runs code itself**. It *asks* ADK to call the function, and ADK sends the result back to it.
That's why a tool's **docstring and type hints matter so much**: they are the only thing the LLM reads to decide
when to call the tool and with which arguments.

**ADK (Agent Development Kit).** Google's Python library (`pip install google-adk`) that provides:
- the `Agent` class (the loop above),
- **sessions** (the conversation history, so the agent remembers the previous message),
- a ready-made **web API** + dev **web UI** (`get_fast_api_app`),
- CLI tools: `adk web`, `adk run`, `adk deploy`.

**Container / Docker image.** A packaged box holding Python + your libraries + your code. It runs the same way
everywhere. The `Dockerfile` is the recipe; `docker build` bakes the image; `docker push` uploads it to
**Artifact Registry** (Google's private image store).

**Cloud Run.** "Give me a container image and I'll run it as an HTTPS service." It handles HTTPS, scaling
(0 → N instances by traffic), and revisions (each deploy is a new immutable version). You pay only while requests
are being handled.

**Service account (SA).** An identity for a *program* (not a person). Our container runs as
`weather-agent-sa@…`, and we give that SA only the permissions it needs (call Gemini, write logs).
That's **least privilege**.

**IAM.** "Who can do what on which resource." Example: `roles/run.invoker` on the service = "may call it".

**Terraform.** Describes all of the above as code, so one command can create, update, or delete it.

---

## 2. The files

```
01-adk-cloud-run-terraform/
├── agents/                      ← every sub-folder here = one agent "app"
│   └── weather_agent/
│       ├── __init__.py          ← makes it a Python package, loads agent.py
│       ├── agent.py             ← THE AGENT: tool + instructions + model
│       └── .env.example         ← env vars for local runs (copy to .env)
├── main.py                      ← web server: turns agents/ into an HTTP API
├── requirements.txt             ← Python dependencies (pinned)
├── Dockerfile                   ← how to build the container image
├── .dockerignore                ← files NOT to put in the image
├── test.sh                      ← end-to-end smoke test (works locally and on Cloud Run)
└── terraform/
    ├── versions.tf              ← Terraform + provider versions, provider config
    ├── variables.tf             ← inputs (project, region, model, public?, web UI?)
    ├── main.tf                  ← APIs, registry, build, SA + IAM, Cloud Run
    ├── outputs.tf               ← URL, image, SA
    └── terraform.tfvars.example ← copy to terraform.tfvars
```

How they connect:

```
agent.py ──imported by──▶ main.py ──run by──▶ Dockerfile (uvicorn) ──built/pushed by──▶ terraform/main.tf
                                                                                         └─▶ Cloud Run runs that image
```

---

## 3. The agent code explained

File: [agents/weather_agent/agent.py](agents/weather_agent/agent.py)

```python
def get_weather(city: str) -> dict:
    """Returns the current weather report for a city.

    Args:
        city: Name of the city, e.g. "Paris".
    ...
    """
```

- This is a **tool**: a normal Python function. ADK reads its **name**, **type hints** (`city: str`), and
  **docstring**, and sends them to Gemini as a "function declaration". Gemini then knows it exists and what it's for.
- It returns a **dict** with a `status` key. That's the ADK convention: Gemini can read `"status": "error"` and tell
  the user politely instead of inventing an answer.
- The data is hard-coded (the `ponytail:` comment marks this). In real life you'd call a weather API here, or a
  database, or your company's internal API. The agent doesn't care.

```python
root_agent = Agent(
    name="weather_agent",
```
- ADK looks for a variable named **exactly `root_agent`** in each agent package. `name` must be a valid identifier and
  becomes the **app name** in the API URLs (`/apps/weather_agent/...`).

```python
    model=Gemini(
        model=os.getenv("MODEL", "gemini-3.5-flash"),
        client_kwargs={"enterprise": True, "location": "global"},
    ),
```
- Which LLM to use. The model ID comes from the `MODEL` env var (Terraform sets it), so switching models needs no
  code change.
- `enterprise: True` → call Gemini through **Google Cloud** (Agent Platform) with your project's billing and IAM,
  not through an AI Studio API key. No API key to leak.
- `location: "global"` → use Google's **global** Gemini endpoint. New models are available there first, and it works
  whatever region Cloud Run runs in.
- The GCP project is read from the `GOOGLE_CLOUD_PROJECT` env var.

```python
    description="Answers questions about the current weather in a city.",
```
- A description *for other agents and humans*: when this agent is a sub-agent or appears in a registry, this is how
  others know what it does.

```python
    instruction=("You are a friendly weather assistant. When the user asks about the weather in a city, call get_weather. ..."),
    tools=[get_weather],
)
```
- `instruction` = the **system prompt**: the agent's job description. Be explicit about **when to use which tool** and
  **what to do on errors**.
- `tools` = the list of functions the model may call.

File: [agents/weather_agent/__init__.py](agents/weather_agent/__init__.py) contains `from . import agent`, so that
when ADK imports the package `weather_agent`, `agent.py` (and `root_agent`) get loaded.

---

## 4. The web server (`main.py`)

File: [main.py](main.py)

```python
app = get_fast_api_app(
    agents_dir=".../agents",
```
- `get_fast_api_app` is ADK's built-in server. It scans `agents/`; **each sub-folder with a `root_agent` becomes an
  app**. You get a complete REST API for free (see [section 8](#8-calling-the-agent-api-reference)).
- It returns a **FastAPI** app (FastAPI = a popular Python web framework), and **uvicorn** is the program that
  actually serves it over HTTP.

```python
    session_service_uri=os.getenv("SESSION_SERVICE_URI"),
```
- Where conversation history is stored. Not set → **in memory** (lost on restart; see [section 12](#12-sessions)).
  Set it to a DB URL to make sessions durable.

```python
    web=os.getenv("SERVE_WEB_UI", "false") == "true",
```
- Turns on the **ADK dev UI** (a chat page with an event inspector) at `/dev-ui/`. Great for learning. Terraform
  controls it with `serve_web_ui`.

```python
    otel_to_cloud=os.getenv("OTEL_TO_CLOUD", "false") == "true",
)
```
- Sends **OpenTelemetry** data (traces of every LLM call and tool call, plus logs and metrics) to Cloud Trace,
  Logging, and Monitoring. Terraform sets it to `true` on Cloud Run; locally it stays off.

```python
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
```
- Lets you run `python main.py` locally. Cloud Run always provides a `PORT` env var, and the server must listen on it.

---

## 5. The container (`Dockerfile`)

File: [Dockerfile](Dockerfile)

| Line | Why |
|---|---|
| `FROM python:3.12-slim` | Start from an official small image with Python 3.12 |
| `ENV PYTHONUNBUFFERED=1` | Print logs immediately (otherwise they're buffered and show up late in Cloud Logging) |
| `COPY requirements.txt .` then `RUN pip install ...` | Install dependencies **before** copying the code. Docker caches each step, so changing `agent.py` doesn't reinstall everything (much faster builds) |
| `COPY main.py .` / `COPY agents/ agents/` | Add your code |
| `RUN adduser ... && chown` / `USER app` | Don't run as root: if the app is ever compromised, the attacker isn't root in the container |
| `CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}` | Start the server. `main:app` = "the `app` object in `main.py`". `exec` lets Cloud Run's stop signal reach uvicorn cleanly |

[.dockerignore](.dockerignore) keeps `terraform/`, `.env` (secrets!), caches, and docs out of the image.

---

## 6. The Terraform explained

### `versions.tf`

```hcl
terraform {
  required_version = ">= 1.9"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 8.4" }
  }
  # backend "gcs" { ... }
}
provider "google" {
  project = var.project_id
  region  = var.region
}
```
- Pins the Terraform and provider versions so the code behaves the same next year. `~> 8.4` means ≥ 8.4 and < 9.0.
- `backend "gcs"` (commented out) = where the **state** is stored. Commented → a local file `terraform.tfstate`.
- The `provider` block sets defaults: every `google_*` resource uses this project and region unless told otherwise.
  Authentication comes from **ADC** (`gcloud auth application-default login`).

### `variables.tf`

The inputs you can change without touching code: `project_id` (required), `region`, `service_name`, `model`,
`public`, `serve_web_ui`. You set them in `terraform.tfvars`.

### `main.tf`, block by block

**`locals`: computed values**

```hcl
src_files = concat(["Dockerfile","main.py","requirements.txt"], sort(tolist(fileset(local.src_dir, "agents/**/*.py"))))
src_hash  = sha1(join("", [for f in local.src_files : filesha1("${local.src_dir}/${f}")]))
image     = ".../${var.service_name}:${substr(local.src_hash, 0, 12)}"
```
- Lists every file that goes into the image, hashes each one, and hashes all the hashes together.
- The **image tag is that hash**. Change one character in `agent.py` → new hash → new tag → Terraform sees the image
  changed → rebuild + new Cloud Run revision. Nothing changed → `plan` says "No changes".
  (Using `:latest` instead would break this: Terraform couldn't tell anything changed.)

**① `google_project_service.apis`: enable the APIs**
A fresh project has most APIs off. `for_each` creates one resource per API: Cloud Run, Artifact Registry,
aiplatform (Gemini), and the observability APIs.

**② `google_artifact_registry_repository.agents`: the image store**
A private Docker repository at `europe-west1-docker.pkg.dev/PROJECT/agents`.
`depends_on = [google_project_service.apis]` because the API must be enabled first.

**③ `terraform_data.image`: build and push**

```hcl
resource "terraform_data" "image" {
  triggers_replace = local.image
  provisioner "local-exec" { command = "gcloud auth configure-docker ...; docker build ...; docker push ..." }
}
```
- `terraform_data` is a do-nothing resource that exists to **run a command**. `local-exec` runs it **on your machine**.
- `triggers_replace = local.image` → re-run it only when the image tag (the source hash) changes.
- `--platform linux/amd64` because Cloud Run runs x86-64.
- Honest note: Terraform isn't a build tool. In a real team, CI (Cloud Build / GitHub Actions) builds the image and
  Terraform only receives the tag. For learning, "one command does everything" is easier to follow.

**④ `google_service_account.agent` + `google_project_iam_member.agent`: the agent's identity**
Creates `weather-agent-sa` and grants it exactly 4 roles: call Gemini (`aiplatform.user`) and write
logs, metrics, and traces. It can't read your buckets, databases, or anything else. If you add a tool that reads
BigQuery, you add `roles/bigquery.dataViewer` here, and only that.

**⑤ `google_cloud_run_v2_service.agent`: the service**

```hcl
template {
  service_account = google_service_account.agent.email   # run as our SA
  scaling { min_instance_count = 0, max_instance_count = 1 }
  containers {
    image = local.image
    resources { limits = { cpu = "1", memory = "1Gi" } }
    env { name = "GOOGLE_CLOUD_PROJECT" ... }  env { name = "MODEL" ... } ...
  }
}
depends_on = [terraform_data.image, google_project_iam_member.agent]
```
- `template` = what each **revision** looks like. Any change inside it creates a new revision, and Cloud Run
  shifts 100% of traffic to it once it's healthy (a zero-downtime deploy).
- `min 0` → scale to zero when idle (cost ≈ 0; the first request after idle takes a few seconds: a "cold start").
- `max 1` → see [Sessions](#12-sessions).
- The `env` blocks are how configuration reaches `agent.py` / `main.py`.
- `depends_on`: the image must be pushed and the IAM granted **before** the service starts, or it fails.
- `deletion_protection = false` so `terraform destroy` works (keep it `true` in production).

**⑥ `google_cloud_run_v2_service_iam_member.public`: who can call it**
With `count = var.public ? 1 : 0` this only exists if you set `public = true`. By default the service is
**private**: requests without a valid Google identity token get `403`. You're the project owner, so you can call it.
To let a colleague call it:
```bash
gcloud run services add-iam-policy-binding weather-agent --region europe-west1 \
  --member=user:colleague@your-company.com --role=roles/run.invoker
```

### `outputs.tf`
`url`, `image`, `service_account`. Read one with `terraform -chdir=terraform output -raw url`.

### What `terraform apply` does, in order

Terraform builds a dependency graph from the references (`google_service_account.agent.email` in the service
means "SA first") plus the `depends_on` lines:

```
APIs ─▶ Artifact Registry repo ─▶ build+push image ─┐
     └▶ service account ─▶ IAM roles ───────────────┴─▶ Cloud Run service ─▶ (public IAM, optional)
```

---

## 7. Step by step

### 7.1 Run locally (no cloud deploy yet: fastest feedback)

```bash
cd ~/Bureau/trash && source .venv/bin/activate      # see root README §1
cd 01-adk-cloud-run-terraform
gcloud services enable aiplatform.googleapis.com     # the local agent calls Gemini in your project
cp agents/weather_agent/.env.example agents/weather_agent/.env   # then put your project ID in it

# Option A: the ADK dev UI (best for learning: shows every event, tool call, and state change)
adk web agents            # open http://localhost:8000, pick "weather_agent", ask "weather in Tokyo?"

# Option B: terminal chat
adk run agents/weather_agent

# Option C: exactly what Cloud Run will run
export $(cat agents/weather_agent/.env | xargs) && SERVE_WEB_UI=true python main.py
URL=http://localhost:8080 ./test.sh                 # in another terminal
```

In the dev UI, click an event to see the **function call** that Gemini requested and the **function response** your
code returned. That's the agent loop from section 1, live.

### 7.2 Deploy

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars    # set project_id
terraform init
terraform plan        # read it: ~12 resources to add
terraform apply       # type "yes"; the first run takes ~3-5 min (docker build + push)
terraform output url
```

### 7.3 Open the dev UI on the deployed agent (private service, no public URL needed)

```bash
gcloud run services proxy weather-agent --region europe-west1 --port 8080
# open http://localhost:8080/dev-ui/   (the proxy adds your identity token to every request)
```

---

## 8. Calling the agent (API reference)

Every request to the private service needs `Authorization: Bearer $(gcloud auth print-identity-token)`.

```bash
URL=$(terraform -chdir=terraform output -raw url)
TOKEN=$(gcloud auth print-identity-token)
```

| Method + path | What |
|---|---|
| `GET /list-apps` | Agents served: `["weather_agent"]` |
| `POST /apps/{app}/users/{user}/sessions/{session}` | Create a session with your own ID (body = initial state, `{}`) |
| `POST /apps/{app}/users/{user}/sessions` | Create a session with a generated ID |
| `GET /apps/{app}/users/{user}/sessions/{session}` | Read a session: full history + state |
| `GET /apps/{app}/users/{user}/sessions` | List a user's sessions |
| `DELETE /apps/{app}/users/{user}/sessions/{session}` | Delete a session |
| `POST /run` | Send a message and get **all events** as a JSON list when the run finishes |
| `POST /run_sse` | Same, but **streamed** as Server-Sent Events (for chat UIs) |
| `GET /docs` | Interactive OpenAPI docs (Swagger) |

```bash
# 1. create a session
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  $URL/apps/weather_agent/users/u1/sessions/s1 -d '{}'

# 2. ask something
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" $URL/run -d '{
  "app_name": "weather_agent", "user_id": "u1", "session_id": "s1",
  "new_message": {"role": "user", "parts": [{"text": "What is the weather in London?"}]}}'

# 3. follow-up in the same session: the agent remembers "London"
curl ... $URL/run -d '{... "session_id": "s1", "new_message": {"role":"user","parts":[{"text":"And tomorrow?"}]}}'

# streaming
curl -N -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" $URL/run_sse -d '{
  "app_name":"weather_agent","user_id":"u1","session_id":"s1","streaming":true,
  "new_message":{"role":"user","parts":[{"text":"weather in Tokyo?"}]}}'
```

The `/run` response is a list of **events**, typically:
1. `content.parts[0].functionCall` → `{"name":"get_weather","args":{"city":"London"}}` (Gemini asks for the tool)
2. `content.parts[0].functionResponse` → your function's return value
3. `content.parts[0].text` → the final answer

From Python (any app):
```python
import requests, google.auth.transport.requests, google.oauth2.id_token
token = google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), URL)  # works with a service account
requests.post(f"{URL}/run", headers={"Authorization": f"Bearer {token}"}, json={...})
```

---

## 9. Testing

| Level | How | What it proves |
|---|---|---|
| Tool unit test | `python -c "from agents.weather_agent.agent import get_weather; print(get_weather('Paris'))"` | Your Python logic works, no LLM involved |
| Interactive | `adk web agents` | The LLM calls the tool at the right moments |
| **Smoke test** | `./test.sh` (Cloud Run) or `URL=http://localhost:8080 ./test.sh` | Full path works: auth → server → session → Gemini → tool → answer. **Fails if the tool wasn't called** |
| Evaluation | `adk eval` with a `.test.json` of expected tool calls and answers | Quality doesn't regress when you change the prompt or model. Add this when the agent gets serious |

Run `./test.sh` after every deploy.

---

## 10. Monitoring

**Logs** (every request, plus Python `print`/`logging` output):
```bash
gcloud run services logs read weather-agent --region europe-west1 --limit 50
gcloud run services logs tail weather-agent --region europe-west1      # live
```
Console: *Cloud Run → weather-agent → Logs*, or *Logging → Logs Explorer* with
`resource.type="cloud_run_revision" resource.labels.service_name="weather-agent"`.

**Traces** (thanks to `otel_to_cloud`): *Console → Trace → Trace explorer*. Each request shows a waterfall:
`invoke_agent` → `call_llm` (how long Gemini took, tokens used) → `execute_tool get_weather`. This is **the** tool for
answering "why is my agent slow?"

**Metrics**: *Cloud Run → weather-agent → Metrics*: request count, latency (p50/p95/p99), 4xx/5xx, instance count,
CPU/memory. Create an alert: *Monitoring → Alerting → Create policy → Cloud Run Revision → Request count, filter
response_code_class = 5xx*.

**Revisions** (every deploy):
```bash
gcloud run revisions list --service weather-agent --region europe-west1
```

---

## 11. Change and redeploy

1. Edit `agent.py` (e.g. add `"madrid": "hot, 35°C"` or a new tool).
2. Test locally: `adk web agents`.
3. `cd terraform && terraform plan` → you'll see `terraform_data.image` **replaced** and the Cloud Run service
   **updated in place** (new image tag).
4. `terraform apply`, then `./test.sh`.

Rollback = redeploy the previous code (git revert + apply). Emergency rollback without Terraform:
`gcloud run services update-traffic weather-agent --to-revisions=PREVIOUS_REVISION=100 --region europe-west1`
(the next `terraform apply` will switch back to what the code says).

---

## 12. Sessions

Sessions live in the server's **memory**. Cloud Run may run several instances, and each one would have *different*
memory: message 1 lands on instance A, message 2 on instance B, and the agent has "forgotten" the conversation.
So we set `max_instance_count = 1` (marked `ponytail:` in the code).

To scale out, use a shared session store and then raise `max_instance_count`:
- **Agent Runtime sessions** (managed; easiest):
  `SESSION_SERVICE_URI=agentengine://projects/P/locations/europe-west1/reasoningEngines/ID` (a reasoning engine from project 02)
- **Cloud SQL / Postgres**: `SESSION_SERVICE_URI=postgresql+asyncpg://...` (credentials from Secret Manager)

---

## 13. Best practices

- **Private by default** (done). Expose to users through something that authenticates them: Gemini Enterprise,
  Google Chat (project 03), IAP, or API Gateway. Never `public = true` with no auth: anyone could spend your Gemini budget.
- **Least-privilege service account per agent** (done).
- **Pin dependency versions** (`requirements.txt`) (done). Update them on purpose, then retest.
- **Secrets** (API keys for your tools): Secret Manager + `env { value_source { secret_key_ref {...} } }` in Terraform,
  never in code or in `.env` files baked into the image (`.dockerignore` excludes `.env`).
- **Good tools** = clear names, typed args, precise docstrings, and they return `{"status": ...}`. Keep each tool
  doing one thing.
- **Instructions**: say when to call each tool and what to do on errors. Keep them short and testable.
- **Turn off the dev UI in production** (`serve_web_ui = false`).
- **Production**: remote state (GCS backend), build in CI, `terraform plan` in PRs, `deletion_protection = true`,
  `min_instance_count = 1` if cold starts hurt.
- **Next steps**: make it an **A2A** agent (`get_fast_api_app(a2a=True)` plus an `agent.json` Agent Card in the agent
  folder, served under `/a2a/weather_agent`) so other agents and Agent Registry can discover its skills
  (see project 02).

---

## 14. Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `could not find default credentials` | `gcloud auth application-default login` |
| `403 Forbidden` calling the URL | Missing or wrong token: use `gcloud auth print-identity-token` (identity token, not access token), or you lack `run.invoker` |
| `docker: permission denied` | Add yourself to the docker group: `sudo usermod -aG docker $USER`, then log out and back in |
| `denied: Permission "artifactregistry.repositories.uploadArtifacts"` | Run `gcloud auth configure-docker europe-west1-docker.pkg.dev` with an account that has access |
| Service fails to start ("container failed to listen on PORT") | Check `gcloud run services logs read ...`: usually an import error in `agent.py` |
| `404 model not found` / `Publisher model ... not found` | The model ID isn't available: set `model = "..."` in tfvars to a current one (Console → Agent Platform → Model Garden) |
| `429 RESOURCE_EXHAUSTED` | Gemini quota: retry later, or request a quota increase |
| Agent "forgets" the conversation | You're using a new `session_id`, or you raised `max_instance_count` with in-memory sessions (§12) |
| `Error 409: already exists` on apply | The resource was created outside Terraform: `terraform import` it or delete it |

---

## 15. Clean up

```bash
cd terraform && terraform destroy
```
Removes the service, the SA and its roles, and the repository (with its images). APIs stay enabled (harmless, free).
