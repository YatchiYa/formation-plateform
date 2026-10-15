---
type: "article"
description: "Héberger un agent sur Agent Runtime, le rendre découvrable dans Agent Registry et l'ajouter à Gemini Enterprise."
tags: ["agent-runtime", "agent-registry", "gemini-enterprise", "terraform"]
level: "beginner"
duration: "2h"
usecases: ["assistant-interne"]
platforms: ["gemini-enterprise", "vertex-ai"]
date: "2026-09-29"
updated: "2026-10-14"
authors: ["Youcef"]
references:
  - title: "official guide"
    url: https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent
---
# Project 02: Agent Runtime + Agent Registry (+ Gemini Enterprise), with Terraform

**Goal:** deploy an ADK agent to **Agent Runtime**, Google's *managed* agent hosting (formerly "Agent Engine"),
using only Terraform: no Docker, no web server code. Then see it appear automatically in **Agent Registry**,
register the Cloud Run agent from project 01 there too, call the agent from Python and REST, and make it available to
employees in **Gemini Enterprise**.

> Do [project 01](../01-adk-cloud-run-terraform/README.md) first; this one assumes you know what an agent,
> a tool, a session, and a Terraform resource are.

---

## Contents

1. [Concepts: Agent Runtime, Agent Registry, Gemini Enterprise](#1-concepts)
2. [The files](#2-the-files)
3. [The agent code explained](#3-the-agent-code-explained)
4. [How the code gets to Google: `pack.py`](#4-how-the-code-gets-to-google-packpy)
5. [The Terraform explained](#5-the-terraform-explained)
6. [Step by step](#6-step-by-step)
7. [Calling the agent (Python, REST, console)](#7-calling-the-agent)
8. [Agent Registry: see, search, discover](#8-agent-registry)
9. [Add the agent to Gemini Enterprise](#9-add-the-agent-to-gemini-enterprise)
10. [Testing](#10-testing)
11. [Monitoring](#11-monitoring)
12. [Change and redeploy](#12-change-and-redeploy)
13. [Best practices and next steps](#13-best-practices)
14. [Troubleshooting](#14-troubleshooting)
15. [Clean up](#15-clean-up)

---

## 1. Concepts

### Agent Runtime: "just give me your Python, I'll host it"

In project 01 **you** built the container, wrote the web server, chose where sessions live, and so on.
With Agent Runtime you upload **source code + requirements.txt**, and Google:

- builds and runs the container, scales it (0 → N), and gives it an HTTPS API,
- provides **managed sessions** (conversation history stored by Google, shared by all instances, so there's no
  "max 1 instance" problem) and **Memory Bank** (long-term memory across sessions),
- plugs in tracing, logging, and a playground in the console,
- **registers the agent in Agent Registry automatically**,
- is the native way to plug a custom agent into **Gemini Enterprise**.

In APIs and Terraform it's still called **ReasoningEngine**: the resource name looks like
`projects/123/locations/europe-west1/reasoningEngines/456`, and the Terraform resource is `google_vertex_ai_reasoning_engine`.

### `AdkApp`: the adapter

Agent Runtime doesn't call your `Agent` directly. It calls **methods** on a Python object: `async_create_session`,
`async_stream_query`, and so on. `AdkApp(agent=root_agent)` is the wrapper that provides those methods for an ADK agent.

```
client ──HTTPS──▶ Agent Runtime ──calls──▶ app.async_stream_query(user_id, session_id, message)
                                               │   (AdkApp)
                                               └─▶ runs root_agent (Gemini + tools), stores events in the managed session
```

### Agent Registry: the company's "agent catalog"

When a company has dozens of agents and MCP servers (tool servers) spread over Cloud Run, GKE, and Agent Runtime,
nobody knows what exists. **Agent Registry** (`agentregistry.googleapis.com`) is the central inventory:

- **Agents**, **MCP servers**, **Endpoints** (plain APIs), and **Skills** each get an entry with name,
  description, protocols/URLs, and skills (from an **A2A Agent Card**).
- **Automatic registration**: agents on **Agent Runtime** (this project), on **GKE** (with a label), and on
  **Cloud Run** (deployed with `gcloud alpha run deploy --functional-type=agent --identity-type=agent-identity`).
- **Manual registration**: anything else, including our project 01 agent, as a **Service** resource (Terraform
  `google_agent_registry_service`).
- **Consumers**: humans (console, `gcloud agent-registry agents search`), **other agents** (ADK's `AgentRegistry`
  class turns an entry into a sub-agent or toolset), Agent Studio, and Gemini Enterprise.

Read-only vs writable: you **write** a `Service`; the registry **projects** it as a read-only `Agent` (or `McpServer`, or
`Endpoint`) that consumers read.

### A2A (Agent2Agent protocol), in one paragraph

An open standard for agents to talk to each other. An A2A agent publishes an **Agent Card** (JSON: name, description,
URL, **skills**) and accepts messages at a standard endpoint. If an agent speaks A2A, the registry knows its *skills*,
so an orchestrator agent can pick it automatically. Our agents are plain REST for now, which is fine to start with.

### Gemini Enterprise

The **app employees use** (a chat interface at `vertexaisearch.cloud.google.com/...`, formerly Agentspace).
Admins can add custom agents to it. An Agent Runtime agent is added via **Agents → Add agent → Custom agent via
Agent Runtime**. Then users see it in the agent list and chat with it, with SSO and their own identity.

```
          you (Terraform)                           Google manages                       people
┌───────────────────────────────┐   ┌──────────────────────────────────┐   ┌──────────────────────────┐
│ agent/ source  ──pack.py──▶   │   │ Agent Runtime: build, run, scale │   │ Gemini Enterprise app    │
│ google_vertex_ai_reasoning_   │──▶│  sessions, memory, traces        │──▶│ Google Chat (project 03) │
│ engine                        │   │         │ auto-register           │   │ other agents via registry│
│ google_agent_registry_service │──▶│ Agent Registry (catalog)         │   └──────────────────────────┘
└───────────────────────────────┘   └──────────────────────────────────┘
```

---

## 2. The files

```
02-agent-runtime-registry-terraform/
├── agent/                           ← EXACTLY what gets uploaded to Agent Runtime
│   ├── requirements.txt             ← installed by Agent Runtime when it builds
│   └── currency_agent/
│       ├── __init__.py
│       ├── agent.py                 ← tool + root_agent + `app = AdkApp(...)`
│       └── .env.example             ← for local runs only (never uploaded)
├── scripts/
│   ├── pack.py                      ← makes agent/ into a base64 tar.gz for Terraform
│   ├── query.py                     ← call the deployed agent from Python
│   ├── discover.py                  ← list agents from Agent Registry (like an orchestrator would)
│   └── test.sh                      ← REST smoke test (fails if the tool wasn't called)
└── terraform/
    ├── versions.tf / variables.tf / outputs.tf / terraform.tfvars.example
    ├── main.tf                      ← APIs, source packaging, the Agent Runtime agent
    ├── registry.tf                  ← manual registration of the Cloud Run agent (optional)
    └── class_methods.json           ← the agent's API "contract" (which methods clients can call)
```

---

## 3. The agent code explained

File: [agent/currency_agent/agent.py](agent/currency_agent/agent.py)

```python
RATES_TO_EUR = {"EUR": 1.0, "USD": 0.86, ...}

def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Converts an amount of money from one currency to another. ..."""
```
A tool with **three typed arguments**. Gemini reads the types and docstring and fills in
`amount=250, from_currency="USD", to_currency="MAD"` from a sentence like "how much is 250 dollars in dirhams?".
Unknown currencies → `{"status": "error", ...}` so the model can explain instead of making something up.

```python
root_agent = Agent(name="currency_agent", model=Gemini(...), description=..., instruction=..., tools=[convert_currency])
```
Same as project 01. The `description` matters even more here: **Agent Registry and Gemini Enterprise show it**
to people and to other agents.

```python
app = AdkApp(agent=root_agent)
```
**The only new line.** Agent Runtime imports the module `currency_agent.agent` and uses the object `app`
(Terraform: `entrypoint_module` / `entrypoint_object`). `AdkApp` comes from `agentplatform.frameworks.adk`
(the new package name; the old `vertexai.agent_engines.AdkApp` still works). Inside Agent Runtime, `AdkApp`
automatically uses the **managed session service** and **Memory Bank**. Locally it uses in-memory ones.

```python
if __name__ == "__main__": assert ...
```
A self-check of the tool logic: `cd agent && python -m currency_agent.agent` → `convert_currency OK`.

---

## 4. How the code gets to Google: `pack.py`

Terraform resource `google_vertex_ai_reasoning_engine` accepts the code **inline**, as a
**base64-encoded `.tar.gz`** of the source folder (`source_code_spec.inline_source.source_archive`).

[scripts/pack.py](scripts/pack.py) builds that archive and prints `{"archive": "<base64>"}`. That's the JSON
format Terraform's `external` data source expects.

**Why is it "deterministic"?** A normal `tar czf` records file timestamps and the gzip creation time, so the bytes
change on every run. Terraform would then see a "change" on every `plan` and redeploy every time (≈ 5 minutes
each). `pack.py` sorts files, sets every timestamp and owner to 0, and uses `gzip mtime=0`. Result:
**same code ⇒ identical bytes ⇒ `plan` says "No changes"**. The idea is the same as the image-tag hash in project 01.

It skips `__pycache__`, `.env` (secrets must never be uploaded), `.adk`, and `.venv`.

Archive contents (the paths Terraform refers to):
```
requirements.txt
currency_agent/__init__.py
currency_agent/agent.py
```

---

## 5. The Terraform explained

### `versions.tf`
Same as project 01, plus the **`external`** provider (runs `pack.py`).

### `variables.tf`
`project_id`, `region` (where the agent runs, `europe-west1`), `display_name`, `model`,
`cloud_run_agent_url` (optional, from project 01), `registry_location` (for manual entries, `global`).

### `main.tf`

**① APIs.** `aiplatform` (Agent Runtime + Gemini), `agentregistry`, `cloudresourcemanager` (required by Agent
Runtime deployments), plus logging, monitoring, trace, and telemetry.

**② `data "external" "agent_source"`**
```hcl
data "external" "agent_source" {
  program = ["python3", "${path.module}/../scripts/pack.py"]
  query   = { src = abspath("${path.module}/../agent") }
}
```
A **data source** (it reads and creates nothing): on every `plan`, Terraform runs `pack.py`, sends it
`{"src": ".../agent"}` on stdin, and reads the JSON it prints. The result is available as
`data.external.agent_source.result.archive`.

**③ `google_vertex_ai_reasoning_engine.agent`: the agent itself**

```hcl
resource "google_vertex_ai_reasoning_engine" "agent" {
  display_name = var.display_name        # shown in console, registry, Gemini Enterprise
  description  = "..."
  region       = var.region

  spec {
    agent_framework = "google-adk"       # tells Google it's ADK → enables ADK-specific features (UI, sessions)
    class_methods   = file("${path.module}/class_methods.json")
```
- **`class_methods`**: the list of methods clients may call on `app` (`async_create_session`, `async_stream_query`,
  …), each with an `api_mode`:
  - `""` → normal call through `:query`
  - `"async"` → async call through `:query`
  - `"stream"` / `"async_stream"` → streamed response through `:streamQuery`

  When you deploy with the Python SDK it inspects `AdkApp` and generates this list for you. **Terraform can't run your
  Python**, so the list is written by hand in [class_methods.json](terraform/class_methods.json) (the 11 standard
  ADK methods, as documented by the provider). If it's missing, clients get "method not found".

```hcl
    source_code_spec {
      inline_source { source_archive = data.external.agent_source.result.archive }
      python_spec {
        version           = "3.12"
        entrypoint_module = "currency_agent.agent"   # → currency_agent/agent.py inside the archive
        entrypoint_object = "app"                    # → the AdkApp object
        requirements_file = "requirements.txt"       # → pip install -r requirements.txt
      }
    }
```
- This is **source deployment**: Google builds the container for you. The alternatives are `container_spec`
  (your own image) or `package_spec` (old style: a pickled object in GCS, avoid it).

```hcl
    deployment_spec {
      min_instances = 0            # scale to zero
      max_instances = 2            # OK to scale: sessions are managed (shared), not in memory
      env { name = "MODEL"  value = var.model }
    }
  }
  timeouts { create = "30m" update = "30m" }  # building takes a few minutes
  depends_on = [google_project_service.apis]
}
```
- No `service_account` → the agent runs as the project's **Reasoning Engine Service Agent**
  (`service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com`), which Google creates and which can
  already call Gemini. See [Best practices](#13-best-practices) for a dedicated identity.

### `registry.tf`

```hcl
resource "google_agent_registry_service" "cloud_run_agent" {
  count        = var.cloud_run_agent_url == "" ? 0 : 1     # only if you gave the URL
  location     = var.registry_location                    # "global"
  service_id   = "weather-agent-cloud-run"
  display_name = "weather-agent (Cloud Run)"
  description  = "Answers questions about the current weather in a city. ..."
  agent_spec { type = "NO_SPEC" }                          # plain REST agent (no A2A card)
  interfaces { protocol_binding = "HTTP_JSON"  url = var.cloud_run_agent_url }
}
```
- There is **nothing in Terraform for the Agent Runtime agent**: it's registered automatically.
- The project 01 agent runs on plain Cloud Run, so we register it **manually** as a `Service`.
  With `NO_SPEC`, the registry knows its name, description, and URL, but not its skills. Once it speaks A2A,
  switch to `type = "A2A_AGENT_CARD"` with `content = jsonencode(<agent card>)` (and no `interfaces`).

### `outputs.tf`
`agent_resource_name` (you'll need it everywhere), `agent_id`, `query_url`, `console_url`,
`registered_cloud_run_agent`.

---

## 6. Step by step

### 6.1 Try it locally first

```bash
cd ~/Bureau/trash && source .venv/bin/activate
cd 02-agent-runtime-registry-terraform/agent
python -m currency_agent.agent                           # tool self-check → "convert_currency OK"
cp currency_agent/.env.example currency_agent/.env       # set your project ID
adk web .                                                # http://localhost:8000 → currency_agent
#   try: "How much is 250 USD in MAD?", "and in yen?", "convert 10 BTC to EUR" (→ polite error)
```

### 6.2 Deploy

```bash
cd ../terraform
cp terraform.tfvars.example terraform.tfvars              # set project_id
# optional: register project 01's agent too
echo "cloud_run_agent_url = \"$(terraform -chdir=../../01-adk-cloud-run-terraform/terraform output -raw url)\"" >> terraform.tfvars

terraform init
terraform plan
terraform apply            # 5-10 min the first time: Google builds the image and installs requirements
terraform output agent_resource_name
```

### 6.3 Check it in the console

`terraform output console_url` → **Agent Platform → Agent Runtime (Deployments)** → `currency-agent`:
- **Playground** tab: chat with it right away,
- **Sessions**, **Traces**, **Logs**, **Metrics** tabs,
- **Deployment details**: build status (if the build fails, the error is here).

---

## 7. Calling the agent

### Python ([scripts/query.py](scripts/query.py))

```bash
cd ~/Bureau/trash/02-agent-runtime-registry-terraform
python scripts/query.py "How much is 250 USD in MAD?"
# session: 1234567890
#   -> tool call: convert_currency({'amount': 250, 'from_currency': 'USD', 'to_currency': 'MAD'})
# agent: 250 USD is 2336.96 MAD.
```
What it does:
```python
remote = agentplatform.Client(project=..., location=...).runtimes.get(name=AGENT_NAME)  # a proxy object
session = await remote.async_create_session(user_id="demo-user")                        # → class_methods!
async for event in remote.async_stream_query(user_id=..., session_id=session["id"], message=question): ...
```
`remote.async_create_session` exists because of `class_methods.json`: the SDK generates one Python method per
declared method.

### REST (any language)

```bash
NAME=$(terraform -chdir=terraform output -raw agent_resource_name)
BASE="https://europe-west1-aiplatform.googleapis.com/v1/$NAME"
TOKEN=$(gcloud auth print-access-token)       # ← ACCESS token here (Google API), not identity token

# create a session → {"output": {"id": "...", ...}}
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "$BASE:query" \
  -d '{"class_method": "async_create_session", "input": {"user_id": "u1"}}'

# ask (streamed, Server-Sent Events)
curl -N -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "$BASE:streamQuery?alt=sse" \
  -d '{"class_method": "async_stream_query",
       "input": {"user_id": "u1", "session_id": "SESSION_ID", "message": "100 GBP in EUR?"}}'

# list a user's sessions
curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" "$BASE:query" \
  -d '{"class_method": "async_list_sessions", "input": {"user_id": "u1"}}'
```

> **Access token vs identity token.** Cloud Run (project 01) checks an **identity token**
> (`print-identity-token`: "who you are"). Google APIs such as Agent Runtime take an **access token**
> (`print-access-token`: "what you may do"). Mixing them up gives 401/403.

**Who can call it?** Anyone with `roles/aiplatform.user` on the project. To allow one app or user on this agent only:
`google_vertex_ai_reasoning_engine_iam_member` (Terraform).

---

## 8. Agent Registry

```bash
# the Agent Runtime agent, auto-registered in its region
gcloud agent-registry agents list --location=europe-west1
# the manually registered Cloud Run agent
gcloud agent-registry agents list --location=global
gcloud agent-registry services list --location=global      # the writable "Service" you created

# search (keyword / semantic)
gcloud agent-registry agents search --location=europe-west1 --search-string="currency conversion"

# details
gcloud agent-registry agents describe AGENT_ID --location=europe-west1
```
Console: **Agent Registry → Agents** (filter by location or runtime).

### Discovery from code (how an orchestrator agent finds others)

```bash
python scripts/discover.py europe-west1
python scripts/discover.py global
```
[scripts/discover.py](scripts/discover.py) uses ADK's `AgentRegistry` class. In a real orchestrator you'd go further:

```python
from google.adk.integrations.agent_registry import AgentRegistry
registry = AgentRegistry(project_id="...", location="global")
fx = registry.get_remote_a2a_agent("projects/.../agents/...")   # A2A agents → usable as a sub-agent
tools = registry.get_mcp_toolset("projects/.../mcpServers/...") # MCP servers → usable as tools
boss = Agent(name="assistant", model=..., sub_agents=[fx], tools=[tools], instruction="Delegate...")
```
(This needs `pip install "google-adk[a2a,agent-identity]" mcp`. `get_remote_a2a_agent` only works for agents that
speak **A2A**; see next steps.)

Manual registration with gcloud (same as `registry.tf`):
```bash
gcloud agent-registry services create my-agent --location=global \
  --display-name="My Agent" --agent-spec-type=no-spec \
  --interfaces="url=https://my-agent.example.com,protocolBinding=http-json"
```

---

## 9. Add the agent to Gemini Enterprise

Prerequisites: a **Gemini Enterprise** subscription/app in your org (Console → *Gemini Enterprise*) and the
**Gemini Enterprise Admin** role. Location compatibility: an app in `global` or `eu` works with an agent in
`europe-west1`.

### Option A: console (easiest)
*Gemini Enterprise → your app → Agents → **Add agent** → **Custom agent via Agent Runtime***, then paste
`terraform output -raw agent_resource_name`, set a display name, a description, and an icon.

### Option B: REST (scriptable)
```bash
PROJECT_ID=$(gcloud config get project)
APP_ID=your-gemini-enterprise-app-id          # Console → Gemini Enterprise → Apps → ID column
LOC=global                                    # "global", "us" or "eu": the app's location
AGENT=$(terraform -chdir=terraform output -raw agent_resource_name)
HOST=$([ "$LOC" = global ] && echo discoveryengine.googleapis.com || echo $LOC-discoveryengine.googleapis.com)

curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJECT_ID" \
  "https://$HOST/v1alpha/projects/$PROJECT_ID/locations/$LOC/collections/default_collection/engines/$APP_ID/assistants/default_assistant/agents" \
  -d "{
    \"displayName\": \"Currency converter\",
    \"description\": \"Converts amounts between EUR, USD, GBP, JPY and MAD.\",
    \"adkAgentDefinition\": {\"provisionedReasoningEngine\": {\"reasoningEngine\": \"$AGENT\"}}
  }"
```
Then *Agents → your agent → Sharing*: choose who can use it. Users open the Gemini Enterprise web app →
**Agents** → *Currency converter*.

If your tools need to act **as the user** (read *their* Drive, BigQuery, …), you add an OAuth `authorizationConfig`
to the registration; see the [official guide](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-adk-agent).

---

## 10. Testing

| Level | Command |
|---|---|
| Tool logic | `cd agent && python -m currency_agent.agent` |
| Local, interactive | `adk web agent` (from the project folder) |
| Deployed, Python | `python scripts/query.py "100 USD to EUR"` |
| **Deployed, REST smoke test** | `./scripts/test.sh`: creates a session, streams a query, **fails if `convert_currency` wasn't called** |
| Console | Agent Runtime → currency-agent → Playground |

---

## 11. Monitoring

Agent Runtime → *currency-agent*:
- **Traces**: every query as a waterfall (`invoke_agent` → `call_llm` → `execute_tool convert_currency`), with timings
  and token counts. Also in *Cloud Trace → Trace explorer*.
- **Logs**: in the tab, or in Logs Explorer:
  `resource.type="aiplatform.googleapis.com/ReasoningEngine" resource.labels.reasoning_engine_id="AGENT_ID"`
- **Metrics**: request count, latency, errors, instances, CPU/memory. Alert on them in Cloud Monitoring.
- **Sessions**: browse real conversations (great for debugging "why did it answer that?").

---

## 12. Change and redeploy

Edit anything in `agent/` → `terraform plan` shows `spec.source_code_spec.inline_source.source_archive` changing →
`terraform apply` → Google rebuilds (a few minutes) and switches over. The resource name and ID **stay the same**,
so Gemini Enterprise, the registry, and the Chat bridge keep working with no changes.

Changing `requirements.txt` or `MODEL` works the same way.

---

## 13. Best practices

- **Stable ID, changing code.** Anything that points at the agent (Gemini Enterprise, the Chat bridge, other agents)
  uses the resource name. Never destroy and recreate it just to update the code; `apply` updates in place.
- **Dedicated identity** (production): either set `spec.service_account` to a service account with only
  `roles/aiplatform.user` (+ what your tools need), or use **Agent Identity** (`spec.identity_type = "AGENT_IDENTITY"`),
  a per-agent identity governed by the Agent Platform. Grant it only what the tools need.
- **Secrets**: `deployment_spec.secret_env { name = "API_KEY" secret_ref { secret = "my-secret" version = "latest" } }`
  (the secret must already exist in Secret Manager). Never commit a `.env`; `pack.py` refuses to upload them.
- **Pin requirements** (done), and keep `class_methods.json` in sync if you upgrade to a very different ADK.
  Deploy once with `adk deploy agent_engine` and compare if in doubt.
- **Descriptions are product**: the registry, Gemini Enterprise, and orchestrator agents choose agents from their
  `description` and skills. Write them for a reader who has never seen your code.
- **Make it A2A** (next step): serve an Agent Card so skills are discoverable. This is what lets the registry, Agent
  Studio, and other agents use it as a sub-agent. In `class_methods.json`, add
  `"a2a_agent_card": "<agent card JSON string>"` to `async_create_session` (see the provider docs for
  `google_vertex_ai_reasoning_engine`).
- **Memory Bank**: to remember users *across* sessions, add `PreloadMemoryTool` to the agent and configure
  `context_spec.memory_bank_config` in Terraform.
- **Evaluate** before changing the model or instructions (`adk eval`, or Agent Platform evaluation).

---

## 14. Troubleshooting

| Symptom | Fix |
|---|---|
| `apply` fails with a build error | Console → Agent Runtime → the agent → deployment/build logs. Usually a missing package in `requirements.txt` or an import error |
| `apply` shows changes every time | Something non-deterministic is in `agent/` (e.g. a generated file): delete it, or add it to `skip` in `pack.py` |
| `method not found: async_stream_query` | `class_methods.json` doesn't match `AdkApp`. Compare with `AdkApp(...).register_operations()` |
| `401/403` on REST | Use `gcloud auth print-access-token`, and check you have `roles/aiplatform.user` |
| Agent not in the registry | Check the right location (`--location=europe-west1`). Auto-registration only covers the **same project**. Wait a minute after deploy |
| `404 Publisher model not found` | Change `model` in tfvars |
| Gemini Enterprise: "location not compatible" | App in `us` → deploy the agent to a US region (`region = "us-central1"`); `eu` → an EU region; `global` → any |

---

## 15. Clean up

```bash
cd terraform && terraform destroy
```
Remove the agent from Gemini Enterprise first (console: Agents → ⋮ → Delete), or the registration will point at a
deleted agent.
