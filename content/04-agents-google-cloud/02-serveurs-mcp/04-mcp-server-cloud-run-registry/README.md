---
type: "course"
description: "Un serveur MCP de catalogue produits, privé sur Cloud Run et référencé dans Agent Registry, utilisable par ADK, Claude Code ou Gemini CLI."
tags: ["mcp", "fastmcp", "cloud-run", "agent-registry", "google-sheets"]
level: "intermediate"
duration: "3h"
usecases: ["analyse-donnees", "automatisation-processus"]
platforms: ["gemini-enterprise", "claude"]
date: "2026-10-04"
updated: "2026-10-14"
authors: ["Youcef"]
---
# Project 04: an MCP server on Cloud Run, registered in Agent Registry, used by an agent

**Goal:** build an **MCP server** (a "tool server" any AI agent can use), run it **privately on Cloud Run** with
Terraform, **register it in Agent Registry** with its list of tools, and use it from:
1. an **ADK agent that discovers it through the registry** (no hard-coded URL),
2. your own tools: Python, MCP Inspector, Gemini CLI, Claude Code.

> **Nouveau : [sheets-mcp/](sheets-mcp/README.md)**, un MCP Google Sheets complet (17 outils) avec **OAuth par utilisateur**, prêt à brancher dans Gemini Enterprise (Custom MCP Server).
>
> Read projects [01](../01-adk-cloud-run-terraform/README.md) (Cloud Run + Terraform basics) and
> [02](../02-agent-runtime-registry-terraform/README.md) (Agent Registry concepts) first.

---

## Contents

1. [Concepts: MCP, why Cloud Run, why the registry](#1-concepts)
2. [The files](#2-the-files)
3. [The MCP server code explained](#3-the-mcp-server-code-explained)
4. [The Terraform explained](#4-the-terraform-explained)
5. [The registry-driven agent explained](#5-the-registry-driven-agent-explained)
6. [Step by step](#6-step-by-step)
7. [Use the MCP server from other clients](#7-use-the-mcp-server-from-other-clients)
8. [Let a deployed agent use it (Agent Runtime / Cloud Run)](#8-let-a-deployed-agent-use-it)
9. [Testing](#9-testing)
10. [Monitoring](#10-monitoring)
11. [Change the tools](#11-change-the-tools)
12. [Best practices and next steps](#12-best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Clean up](#14-clean-up)

---

## 1. Concepts

### MCP (Model Context Protocol)

In projects 01 and 02, the tools (`get_weather`, `convert_currency`) were Python functions **inside** the agent.
That's fine for one agent. But when 10 agents (and Claude Code, Gemini CLI, Gemini Enterprise…) all need "read the
product catalog", you don't want to copy the function 10 times.

**MCP** is an open standard that puts tools in a **separate server**. Any MCP-compatible client can:
- `tools/list` → "what tools do you have?" (name, description, JSON schema of the arguments)
- `tools/call` → "run `get_stock` with `{"sku": "SKU-001"}`"

```
  ADK agent ─┐
  Claude Code├──MCP (JSON-RPC over HTTP)──▶  MCP server "product-catalog"  ──▶ your DB / API
  Gemini CLI ┘                                 tools: search_products, get_stock
```

Words you'll see:
- **Tool**: a function the model may call (what we use here). MCP also has *resources* (readable data) and
  *prompts* (templates).
- **Transport**: how messages travel. `stdio` = the client starts the server as a local process (local-only).
  **Streamable HTTP** = the server is a web service at a URL like `https://…/mcp`. That's what makes a **remote**,
  shared server possible, so it's what we use.
- **JSON-RPC 2.0**: the message format (`{"jsonrpc":"2.0","method":"tools/list","id":1}`).

### Why Cloud Run

An MCP server over HTTP is just a web service, so Cloud Run is a natural fit: HTTPS, scale to zero, autoscaling, and
**IAM authentication built in**. Our server is **private**: only identities with `roles/run.invoker` can call it.
That matters, because a tool server often reaches internal data.

### Why Agent Registry

Without a registry, every agent hard-codes `https://product-catalog-xyz.run.app/mcp`. With the registry:
- the MCP server is **listed** with its description and **its tools** (console → *Agent Registry → MCP Servers*),
- admins see *which tools exist in the company* (governance),
- agents **look it up by name** at startup: `registry.get_mcp_toolset(...)`. If the URL changes, you update the
  registry, not 10 agents.

**Manual vs automatic registration.** Cloud Run can register an MCP server automatically (`gcloud run deploy
--functional-type=mcp-server`, which only sets the annotation `apphub.cloud.google.com/functional-type: mcp-server`).
Here we register **manually with Terraform** (`google_agent_registry_service`) because:
it's explicit and reviewable, we control the exact URL (`…/mcp`) and protocol, and we publish the **tool list**
(`toolspec.json`) even though the server is private. Google's automatic *tool import* only works for public endpoints.

---

## 2. The files

```
04-mcp-server-cloud-run-registry/
├── server/                     ← the MCP server (what runs on Cloud Run)
│   ├── main.py                 ← FastMCP server: 2 tools, served at /mcp
│   ├── requirements.txt        ← fastmcp 4.0.10 + uvicorn
│   └── Dockerfile / .dockerignore
├── agent/                      ← an ADK agent that USES the server, found via the registry
│   └── shop_agent/
│       ├── __init__.py
│       ├── agent.py
│       └── .env.example
├── scripts/
│   └── test_mcp.py             ← smoke test: auth, tools/list == toolspec.json, calls each tool
└── terraform/
    ├── versions.tf / variables.tf / outputs.tf / terraform.tfvars.example
    ├── main.tf                 ← APIs, image build, SA (no roles), private Cloud Run, invokers
    ├── registry.tf             ← the MCP server entry in Agent Registry
    └── toolspec.json           ← the tool list published in the registry
```

---

## 3. The MCP server code explained

File: [server/main.py](server/main.py)

```python
from fastmcp import FastMCP
mcp = FastMCP("product-catalog", instructions="Company product catalog: ...")
```
**FastMCP** is the most popular Python library for writing MCP servers (Google's Cloud Run tutorial uses it too).
`instructions` is sent to clients when they connect: a hint for the model about what this server is for.

```python
@mcp.tool(annotations={"title": "Search products", "readOnlyHint": True})
def search_products(query: str) -> list[dict]:
    """Searches the product catalog by name or category (case-insensitive).
    Args:
        query: Words to look for, e.g. "laptop" or "accessories".
    """
```
- `@mcp.tool` turns a normal function into an MCP tool. FastMCP reads the **name**, the **type hints** (to build the
  JSON schema of the arguments), and the **docstring** (description plus per-argument descriptions). This is the same
  idea as ADK tools: whatever you write here is exactly what the LLM sees.
- `annotations` are standard MCP hints: `readOnlyHint: True` tells clients "this tool changes nothing", so some
  clients won't ask the user for confirmation. Use `destructiveHint: True` for tools that delete or modify data.
- The data is a dict (marked `ponytail:`). Replace it with a database or API call; nothing else changes.

```python
app = mcp.http_app(path="/mcp", stateless_http=True)
```
- Builds an ASGI web app (served by uvicorn) exposing the MCP **Streamable HTTP** transport at `/mcp`.
- **`stateless_http=True` matters on Cloud Run.** By default an MCP server keeps a *session* in memory per client.
  Cloud Run may send request 1 to instance A and request 2 to instance B, and B would answer "unknown session".
  Stateless mode treats each request independently, so we can safely run up to 5 instances (`max_instance_count = 5`).

The Dockerfile is the same pattern as project 01 (slim Python, dependencies first, non-root user, `uvicorn main:app`).

---

## 4. The Terraform explained

### `main.tf`

| Block | What / why |
|---|---|
| `google_project_service.apis` | Cloud Run, Artifact Registry, Agent Registry |
| `google_artifact_registry_repository.mcp` + `terraform_data.image` | Image store + build/push. Tag = hash of `server/` files (project 01 §6 explains this pattern) |
| `google_service_account.mcp` | The server's identity, with **no roles at all**: it calls no Google API. Least privilege at its simplest. If a tool later reads BigQuery, grant only `roles/bigquery.dataViewer` here |
| `google_cloud_run_v2_service.mcp` | Private service, scale 0→5, 512 MiB. **No `allUsers` invoker**: unauthenticated calls get 403 |
| `google_cloud_run_v2_service_iam_member.invokers` | `for_each` over `var.invokers`: extra identities allowed to call the server (e.g. a deployed agent's service account). Project owners (you) can already call it |

### `registry.tf`

```hcl
resource "google_agent_registry_service" "mcp" {
  location     = var.registry_location            # "global" (manual registration isn't allowed in "us"/"eu")
  service_id   = var.service_name                 # "product-catalog"
  display_name = var.service_name                 # ← the name agents search for
  description  = "Company product catalog: ..."   # ← shown in the registry; write it for humans and LLMs

  mcp_server_spec {
    type    = "TOOL_SPEC"
    content = file("${path.module}/toolspec.json")  # the tools, published in the registry
  }
  interfaces {
    protocol_binding = "JSONRPC"                       # MCP = JSON-RPC
    url              = "${google_cloud_run_v2_service.mcp.uri}/mcp"   # built from the Cloud Run resource
  }
}
```
- Note the **reference** `google_cloud_run_v2_service.mcp.uri`. Terraform knows it must create the service first,
  then register its real URL. No copy-pasting of URLs.
- You write a **Service**; the registry exposes it as a read-only **MCP Server** resource
  (`output registry_mcp_server` = `projects/…/locations/global/mcpServers/…`). That's what agents read.
- [toolspec.json](terraform/toolspec.json) format (max 10 KB):
  ```json
  {"tools": [{"name": "get_stock", "description": "...", "annotations": {"title": "...", "readOnlyHint": true}}]}
  ```
  It **duplicates** the tool list from `main.py`, so `scripts/test_mcp.py` fails if the two drift apart.

### `variables.tf` / `outputs.tf`
Inputs: `project_id`, `region`, `service_name`, `registry_location`, `invokers`.
Outputs: `url`, `mcp_endpoint`, `registry_mcp_server`.

---

## 5. The registry-driven agent explained

File: [agent/shop_agent/agent.py](agent/shop_agent/agent.py). It's an ADK agent whose tools come **from the
MCP server**, which it finds **through the registry**.

```python
def identity_token_header(_context) -> dict:
    try:
        token = google.oauth2.id_token.fetch_id_token(Request(), audience)
    except Exception:
        token = subprocess.check_output(["gcloud", "auth", "print-identity-token"], text=True).strip()
    return {"Authorization": f"Bearer {token}"}
```
**Authentication to the private Cloud Run service.** ADK calls this function before connecting to the MCP server and
adds the returned headers. Cloud Run wants a Google **identity token**:
- when the agent runs **as a service account** (on Cloud Run or Agent Runtime), `fetch_id_token` gets one from the
  metadata server, with `audience` = the service URL;
- when you run it **locally** as yourself, that call fails (user accounts can't mint tokens that way), so we fall back
  to `gcloud auth print-identity-token`.

```python
registry = AgentRegistry(project_id=PROJECT, location="global", header_provider=identity_token_header)
servers = registry.list_mcp_servers().get("mcpServers", [])
server = next(s for s in servers if s.get("displayName") == "product-catalog")
```
**Discovery.** It lists the registry's MCP servers and picks the one named `product-catalog`. The agent knows only a
*name*, never a URL. (The registry calls use your normal ADC credentials.)

```python
endpoint = next(i["url"] for p in [server, *server.get("protocols", [])] for i in p.get("interfaces", []))
audience = endpoint.removesuffix("/mcp")
```
Reads the URL from the registry entry. The identity-token audience is the service's **base** URL, without `/mcp`.

```python
catalog_tools = registry.get_mcp_toolset(server["name"])
root_agent = Agent(..., tools=[catalog_tools])
```
`get_mcp_toolset` returns an ADK **`McpToolset`**. When the agent starts, it connects to the server, calls
`tools/list`, and exposes `search_products` and `get_stock` to Gemini as if they were local functions. When Gemini
calls one, ADK sends `tools/call` to Cloud Run.

```
adk web ─▶ shop_agent ─(1) list_mcp_servers──▶ Agent Registry
                      ─(2) tools/list + tools/call, Bearer <identity token>──▶ Cloud Run /mcp
                      ─(3) Gemini decides which tool to call, with which args
```

---

## 6. Step by step

### 6.1 Run the server locally and poke it

```bash
cd ~/Bureau/trash && source .venv/bin/activate
uv pip install fastmcp==4.0.10                 # once
cd 04-mcp-server-cloud-run-registry/server
python main.py                                 # → http://localhost:8080/mcp

# other terminal: the smoke test against the local server
cd ~/Bureau/trash/04-mcp-server-cloud-run-registry
URL=http://localhost:8080 python scripts/test_mcp.py

# or raw JSON-RPC, to see the protocol itself
curl -s -X POST localhost:8080/mcp -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_stock","arguments":{"sku":"SKU-001"}}}'
```

Visual exploration: `npx @modelcontextprotocol/inspector` → Transport *Streamable HTTP*, URL `http://localhost:8080/mcp`
→ *List tools* → run them.

### 6.2 Deploy + register

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars        # set project_id
terraform init
terraform plan                                      # ~9 resources
terraform apply
terraform output mcp_endpoint
terraform output registry_mcp_server
```

### 6.3 Check the registry

```bash
gcloud agent-registry mcp-servers list --location=global
gcloud agent-registry mcp-servers describe <ID from the list> --location=global
gcloud agent-registry services describe product-catalog --location=global   # the writable entry
```
Console: **Agent Registry → MCP Servers → product-catalog**: description, URL, and the 2 tools.

### 6.4 Test the deployed server

```bash
cd .. && python scripts/test_mcp.py          # uses terraform output url + your identity token
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$(terraform -chdir=terraform output -raw mcp_endpoint)"   # no token → 403
```

### 6.5 Use it from the ADK agent (via the registry)

```bash
cd agent
cp shop_agent/.env.example shop_agent/.env         # set GOOGLE_CLOUD_PROJECT
adk web .                                           # http://localhost:8000 → shop_agent
```
Try: *"Do we have laptops in stock?"* → the agent calls `search_products("laptop")`, sees that SKU-002 has 0 in
stock, and answers with SKUs and prices. Click the events to see the MCP `functionCall` / `functionResponse`.

---

## 7. Use the MCP server from other clients

Every client needs an identity token for the private service. The simplest approach for local tools is the
**Cloud Run proxy**: it listens on localhost and adds your token to every request.

```bash
gcloud run services proxy product-catalog --region europe-west1 --port 8080
# → http://localhost:8080/mcp, authenticated as you
```

| Client | How |
|---|---|
| **Claude Code** | `claude mcp add --transport http product-catalog http://localhost:8080/mcp` |
| **Gemini CLI** | in `~/.gemini/settings.json`: `{"mcpServers": {"product-catalog": {"httpUrl": "http://localhost:8080/mcp"}}}` |
| **MCP Inspector** | `npx @modelcontextprotocol/inspector` → `http://localhost:8080/mcp` |
| **Python (fastmcp)** | see [scripts/test_mcp.py](scripts/test_mcp.py): `StreamableHttpTransport(url, headers={"Authorization": f"Bearer {token}"})` |
| **ADK, without the registry** | `McpToolset(connection_params=StreamableHTTPConnectionParams(url=".../mcp"), header_provider=...)` |

To give a **colleague** access: add `"user:colleague@novagen.tech"` to `invokers` in `terraform.tfvars`, then apply.
They use the same proxy command.

---

## 8. Let a deployed agent use it

A deployed agent runs as a **service account**, which must be (a) allowed to call the MCP server and
(b) allowed to read the registry.

**Agent Runtime (reuse project 02):**
1. Copy `agent/shop_agent/` into `02-agent-runtime-registry-terraform/agent/` and add, at the end of `agent.py`:
   ```python
   from agentplatform.frameworks.adk import AdkApp
   app = AdkApp(agent=root_agent)
   ```
2. In project 02, set `entrypoint_module = "shop_agent.agent"`, add `mcp` to `agent/requirements.txt`, and
   change `google-adk==2.10.0` to `google-adk[a2a,agent-identity]==2.10.0`.
   Add `env { name = "GOOGLE_CLOUD_PROJECT" ... }` only if it isn't set automatically.
3. Allow the agent's identity (the Reasoning Engine service agent, or your custom SA) here in project 04:
   ```hcl
   invokers = ["serviceAccount:service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com"]
   ```
   and grant it `roles/agentregistry.viewer` on the project, so it can list MCP servers.
4. Apply both projects. You can now add that agent to Gemini Enterprise (project 02 §9) or Google Chat (project 03).
   Employees then use the MCP tools through the agent.

**Cloud Run agent (project 01 style):** same idea. Add its SA (`weather-agent-sa@…`) to `invokers` and grant it
`roles/agentregistry.viewer`. In both cases `fetch_id_token` works automatically.

---

## 9. Testing

| Level | Command | Proves |
|---|---|---|
| Server, local | `URL=http://localhost:8080 python scripts/test_mcp.py` | Tools work, and the `toolspec.json` names match |
| Server, deployed | `python scripts/test_mcp.py` | Deploy + IAM + transport work |
| Security | `curl -X POST <mcp_endpoint>` without a token → `403` | The server isn't public |
| Registry | `gcloud agent-registry mcp-servers list --location=global` | The entry exists, with tools |
| End to end | `adk web agent` → ask about stock | Registry discovery + auth + Gemini choosing the tools |

---

## 10. Monitoring

- Logs: `gcloud run services logs tail product-catalog --region europe-west1`. Each MCP call is a `POST /mcp`.
  FastMCP logs tool errors.
- Metrics: *Cloud Run → product-catalog → Metrics* (requests, latency, 4xx = auth problems, 5xx = bugs).
- From the agent side: traces in ADK (`adk web` events), or Cloud Trace when the agent is deployed with telemetry
  on (`execute_tool search_products` spans).
- Audit who can call it: `gcloud run services get-iam-policy product-catalog --region europe-west1`.

---

## 11. Change the tools

1. Add or modify a `@mcp.tool` in `server/main.py`.
2. Update `terraform/toolspec.json` (name, description, annotations).
3. `URL=http://localhost:8080 python scripts/test_mcp.py` locally. It fails if you forgot step 2.
4. `terraform apply` → new image + updated registry entry. Then `python scripts/test_mcp.py`.

Agents pick up new tools at their next start (`tools/list`). No agent code changes.

---

## 12. Best practices

- **Private by default** (done): `run.invoker` only for the identities that need it. Never `allUsers` for a tool
  server that reaches internal data.
- **Server SA with minimal roles** (done: none).
- **Read-only tools first**, and mark them with `readOnlyHint`. For write tools, use `destructiveHint`, validate every
  argument server-side, and log who called what.
- **Validate inputs at the server**: the arguments come from an LLM, so treat them like user input
  (types are enforced by the schema; also check values and ranges).
- **Good descriptions** (tool docstrings + registry description): they're how LLMs and humans decide to use your tool.
- **Stateless HTTP** (done) on Cloud Run.
- **Keep the registry in sync** with the code (done via the test). To go further, generate `toolspec.json` from
  `tools/list` in CI.
- **User-level auth** (next step): when tools must act *as the end user* (their data, their permissions), use Agent
  Registry **bindings** + **Agent Identity auth providers** (`google_agent_registry_binding`,
  `google_agent_identity_auth_provider`). `get_mcp_toolset` then resolves the auth scheme automatically.
- **Agent Gateway** (enterprise): put agent↔tool traffic behind a gateway for central policies (`deployment_spec.agent_gateway_config`).

---

## 13. Troubleshooting

| Symptom | Fix |
|---|---|
| `403` from Cloud Run | Missing or wrong token. Locally use `print-identity-token` (not access token), or the proxy. For a deployed agent, its SA isn't in `invokers` |
| `401` with a token | The audience is wrong: it must be the base URL **without** `/mcp` |
| `406 Not Acceptable` with curl | Add `-H 'Accept: application/json, text/event-stream'` (required by Streamable HTTP) |
| `Bad Request: Missing session ID` / `unknown session` | The server isn't stateless: keep `stateless_http=True` |
| Agent: `MCP server 'product-catalog' not found` | Wrong project or location (`REGISTRY_LOCATION`, default `global`), missing `roles/agentregistry.viewer`, or Terraform not applied |
| `test_mcp.py`: `toolspec.json out of sync` | Update `terraform/toolspec.json` to match `server/main.py`, then apply |
| Registry `apply` error on location | Manual registration isn't allowed in `us`/`eu` multi-regions: use `global` or a region |

---

## 14. Clean up

```bash
cd terraform && terraform destroy
```
This deletes the registry entry, the Cloud Run service, the SA, and the image repository. Remove the MCP server from
any Claude Code or Gemini CLI configs (`claude mcp remove product-catalog`).
