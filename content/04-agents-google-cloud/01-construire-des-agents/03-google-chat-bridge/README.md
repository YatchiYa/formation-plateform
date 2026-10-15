---
type: "article"
description: "Faire répondre votre agent dans Google Chat pour les personnes de votre entreprise, avec une authentification service à service."
tags: ["google-chat", "workspace", "cloud-run"]
level: "intermediate"
duration: "1h30"
usecases: ["assistant-interne"]
platforms: ["gemini-enterprise"]
date: "2026-09-29"
updated: "2026-10-14"
authors: ["Youcef"]
references:
  - title: "Chat app with an ADK agent via Apps Script"
    url: https://developers.google.com/workspace/add-ons/chat/quickstart-adk-agent
  - title: "Chat app with an A2A agent"
    url: https://developers.google.com/workspace/add-ons/chat/quickstart-a2a-agent
---
# Project 03: your agent in Google Chat (company Workspace)

**Goal:** people in your Google Workspace domain open Google Chat, message **Currency Agent** (direct message, or
@mention in a space), and get answers from the Agent Runtime agent from
[project 02](../02-agent-runtime-registry-terraform/README.md).

**How:** a tiny **bridge** service on Cloud Run (≈ 50 lines of Python, deployed with Terraform) receives Chat events,
calls the agent, and returns the answer. Only Google Chat can call it: no public endpoint, no API keys.

> Prerequisites: project 02 deployed (you need `agent_resource_name`), and a **Google Workspace** account in your
> company (a personal @gmail.com can't create Chat apps). Project and Workspace should belong to the same
> organization (`novagen.tech`).

---

## Contents

1. [How it works](#1-how-it-works)
2. [The files](#2-the-files)
3. [The bridge code explained](#3-the-bridge-code-explained)
4. [The Terraform explained](#4-the-terraform-explained)
5. [Step by step](#5-step-by-step)
6. [Make it available to the whole company](#6-make-it-available-to-the-whole-company)
7. [Testing](#7-testing)
8. [Monitoring](#8-monitoring)
9. [Limits, best practices, next steps](#9-limits-best-practices-next-steps)
10. [Other ways to get an agent into Chat](#10-other-ways)
11. [Troubleshooting](#11-troubleshooting)
12. [Clean up](#12-clean-up)

---

## 1. How it works

A **Google Chat app** is a bot that Chat talks to over HTTP. Since 2025, Chat apps are built as
**Google Workspace add-ons**: when a user writes to the app, Google POSTs a JSON **event** to an **HTTP endpoint
URL** you configure, and the JSON you return becomes the app's reply.

```
 user in Google Chat: "@Currency Agent 100 USD in EUR?"
        │
        ▼
 Google Chat ──POST event (JSON) + Google-signed token──▶ Cloud Run "chat-bridge" (private)
   identity: service-PROJECT_NUMBER@gcp-sa-gsuiteaddons...        │  Cloud Run checks: does this identity
                                                                   │  have roles/run.invoker? yes → let in
                                                                   ▼
                                           main.py: text + user → Agent Runtime (project 02)
                                              async_list/create_session, async_stream_query
                                                                   │ runs as chat-bridge-sa (roles/aiplatform.user)
                                                                   ▼
 Google Chat ◀──── {"hostAppDataAction": ... "message": {"text": "100 USD = 86.00 EUR"}} ──┘
```

**Security, step by step:**
1. The Cloud Run service is **private**: every request needs a Google-signed identity token, and Cloud Run itself
   rejects anything else before our code runs.
2. Only **two** identities can call it: the Workspace add-ons service account (Google Chat) and project
   owners (you, for testing).
3. The bridge runs as its own service account, whose only permission is to call the agent.
4. Which **people** can talk to the app is controlled in the Chat configuration (visibility), and later by your
   Workspace admin.

**Conversation memory:** each Chat user (`users/1234…`) gets their own Agent Runtime **session**. The bridge
reuses the user's latest session, so follow-ups like "and in yen?" work. The bridge itself stores nothing
(it's stateless), so it can scale freely.

---

## 2. The files

```
03-google-chat-bridge/
├── main.py               ← the bridge (FastAPI): Chat event → agent → Chat reply
├── requirements.txt      ← agentplatform SDK (google-cloud-aiplatform), fastapi, uvicorn
├── Dockerfile / .dockerignore
├── test.sh               ← sends a fake Chat event to the deployed bridge
└── terraform/
    ├── versions.tf / variables.tf / outputs.tf / terraform.tfvars.example
    └── main.tf           ← APIs, image build, bridge SA, Cloud Run, invoker permission for Chat
```

---

## 3. The bridge code explained

File: [main.py](main.py)

```python
AGENT_NAME = os.environ["AGENT_NAME"]          # set by Terraform: projects/.../reasoningEngines/ID
_, PROJECT, _, LOCATION, *_ = AGENT_NAME.split("/")
agent = agentplatform.Client(project=PROJECT, location=LOCATION).runtimes.get(name=AGENT_NAME)
```
Runs **once at startup**: builds a client proxy for the deployed agent (the same thing `scripts/query.py` does in
project 02). `os.environ["AGENT_NAME"]` (not `.get`) makes the container crash at startup if it's missing, so a
config mistake shows up immediately.

```python
def reply(text):
    return {"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": text}}}}}
```
The exact JSON shape Google Chat (add-on style) expects in order to post a message. Chat supports basic formatting
in `text`: `*bold*`, `_italic_`, `` `code` ``, links.

```python
async def session_for(user_id):
    sessions = (await agent.async_list_sessions(user_id=user_id)).get("sessions", [])
    if sessions: return <most recently updated>["id"]
    return (await agent.async_create_session(user_id=user_id))["id"]
```
Finds the user's latest conversation, or starts one. Sessions live in Agent Runtime, so every bridge instance sees
the same ones.

```python
@app.post("/")
async def chat_event(request):
    chat = (await request.json()).get("chat", {})
    if "addedToSpacePayload" in chat:  return reply("Hi! ...")      # app added to a space / DM opened
    message = chat.get("messagePayload", {}).get("message")
    if not message:                    return {}                    # other events: say nothing
    text = message.get("argumentText") or message.get("text")        # argumentText = text WITHOUT "@Currency Agent"
    user_id = message["sender"]["name"]                              # "users/123…": stable per person
```
An incoming event looks like this (trimmed):
```json
{"chat": {"messagePayload": {
   "space":   {"name": "spaces/AAAA", "spaceType": "DIRECT_MESSAGE"},
   "message": {"text": "@Currency Agent 100 USD in EUR?", "argumentText": " 100 USD in EUR?",
               "sender": {"name": "users/1234567890", "displayName": "Yarab", "email": "yarab@novagen.tech"}}}}}
```

```python
    answer = []
    async for event in agent.async_stream_query(user_id=user_id, session_id=session_id, message=text):
        answer += [p["text"] for p in event.get("content", {}).get("parts", []) if p.get("text")]
    return reply(answer[-1] if answer else "Sorry, ...")
```
Streams the agent's events (tool call, tool result, answer) and keeps the **last text**, which is the final answer.

---

## 4. The Terraform explained

File: [terraform/main.tf](terraform/main.tf). It follows the same patterns as project 01 (read that one first);
only the new parts are explained here.

| Block | What / why |
|---|---|
| `local.addons_sa` | `service-<PROJECT_NUMBER>@gcp-sa-gsuiteaddons.iam.gserviceaccount.com`: the identity Google Chat uses to call your endpoint. Built from the **project number**, read with `data "google_project" "this"` |
| `google_project_service.apis` | Adds `chat.googleapis.com` (Chat apps) and `gsuiteaddons.googleapis.com` (Workspace add-ons) |
| `google_artifact_registry_repository.repo` + `terraform_data.image` | Build and push the bridge image; the tag is the hash of the source files (same as project 01) |
| `google_service_account.bridge` + `roles/aiplatform.user` | The bridge's identity: it may call Agent Runtime, nothing else |
| `google_cloud_run_v2_service.bridge` | Private service. `AGENT_NAME` env var. `timeout = 60s` |
| `google_cloud_run_v2_service_iam_member.chat_invoker` | **The key line**: `roles/run.invoker` for the add-ons service account → Chat may call the bridge. Nobody else (except owners) can |

What Terraform **can't** do: the **Chat app configuration** (name, avatar, endpoint URL, visibility). That's
done once in the console (step 5.3). It's a Workspace setting, not a Cloud resource.

---

## 5. Step by step

### 5.1 Deploy the bridge

```bash
cd ~/Bureau/trash/03-google-chat-bridge/terraform
cp terraform.tfvars.example terraform.tfvars
# set project_id and agent_resource_name:
terraform -chdir=../../02-agent-runtime-registry-terraform/terraform output -raw agent_resource_name

terraform init && terraform apply
terraform output url
```

> If `apply` fails on `chat_invoker` with *"service account ... does not exist"*: Google creates the add-ons
> service account lazily. Open the Chat API configuration page once (step 5.3, `terraform output chat_config_console`),
> then run `terraform apply` again.

### 5.2 Test the bridge before touching Chat

```bash
cd .. && ./test.sh
# { "hostAppDataAction": { ... "message": { "text": "100 USD is 86.00 EUR." } } }
```

### 5.3 Configure the Chat app (console, once)

Open `terraform output -raw chat_config_console` (*APIs & Services → Google Chat API → Configuration*):

| Field | Value |
|---|---|
| App name | `Currency Agent` |
| Avatar URL | any public HTTPS image, e.g. `https://developers.google.com/chat/images/quickstart-app-avatar.png` |
| Description | `Converts currencies (powered by Gemini)` |
| Interactive features | **On** |
| Functionality | ✅ *Join spaces and group conversations* (plus 1:1 messages, which are always on) |
| Connection settings | **HTTP endpoint URL** → `terraform output -raw url` |
| Triggers | *Use a common HTTP endpoint URL for all triggers* |
| Authentication audience | *HTTP endpoint URL* |
| Visibility | ✅ *Make this Chat app available to specific people and groups in `novagen.tech`* → your email (+ testers) |
| Logs | ✅ *Log errors to Logging* |

**Save.** The page also shows the **service account email** Chat uses. Check it matches `local.addons_sa`.

### 5.4 Use it

Google Chat → **+ New chat** → search **Currency Agent** → *Start chat* → "How much is 250 USD in MAD?"
→ then "and in yen?" (it remembers). In a space: *Apps & integrations → Add apps → Currency Agent*,
then `@Currency Agent 50 GBP in EUR`.

---

## 6. Make it available to the whole company

1. **Small group**: add people or Google Groups in *Visibility* (step 5.3). Max 5 individuals, or use a group.
2. **Whole domain**: publish it as a **private** app in the Google Workspace Marketplace:
   - enable the **Google Workspace Marketplace SDK** in the same project → *App configuration*: select
     *Chat app*, set visibility to **Private** (only your domain) → fill in the *Store listing* → **Publish**.
     Private apps aren't reviewed by Google.
   - a **Workspace admin** can then *install it for the whole domain or chosen OUs* (Admin console → Apps →
     Google Workspace Marketplace apps → your app → Install), so everyone sees it without searching.
3. Admins can also allow or block Chat apps per OU: *Admin console → Apps → Google Workspace → Google Chat → Chat apps*.

---

## 7. Testing

| What | How |
|---|---|
| Bridge logic without cloud | The offline check used while building this: a fake agent + FastAPI `TestClient` (see §3 for the event shapes) |
| Bridge deployed | `./test.sh` (fake Chat event, your identity) |
| End to end | A DM to the app in Google Chat |
| Security | `curl -X POST $(terraform -chdir=terraform output -raw url)` **without** a token → must return **403** |

---

## 8. Monitoring

- Bridge: `gcloud run services logs tail chat-bridge --region europe-west1`, Cloud Run metrics (latency, 5xx).
- Chat-side errors (e.g. "app not responding"): Logs Explorer → `resource.type="chat.googleapis.com/Project"`
  (only if you ticked *Log errors to Logging*).
- Agent: traces and sessions in Agent Runtime (project 02, §11). Each Chat user shows up as `user_id = users/…`.

---

## 9. Limits, best practices, next steps

- **Reply time:** Chat waits about **30 s** for a synchronous reply. Our agent answers in 2–5 s. For slow agents
  (long tool chains), return `{}` immediately and post the answer later with the **Chat API**
  (`spaces.messages.create` as the app, via the `chat.bot` scope). That's the upgrade path, marked in the code comments.
- **One conversation per user across all spaces** (marked `ponytail:` in the code). To separate them, use
  `f"{space}:{user}"` as the `user_id` for sessions.
- **User identity:** the agent currently acts as the *bridge* (service account). If tools must act **as the
  user** (their Drive, Calendar…), you need user OAuth (Chat app authorization with user scopes); that's advanced.
- **Rich replies:** return `cardsV2` instead of `text` for buttons, tables, and images.
- **Don't log message contents** in production unless your data policy allows it.
- Least privilege is already done: private service, one invoker, and a bridge SA with one role.

---

## 10. Other ways

| Option | When |
|---|---|
| **This bridge (HTTP + Cloud Run + Terraform)** | You want everything as code, no keys, and full control |
| Google's quickstart, [Chat app with an ADK agent via Apps Script](https://developers.google.com/workspace/add-ons/chat/quickstart-adk-agent) | Fast demo, no Cloud Run. But it stores a **service-account key** in script properties, which Google itself says isn't recommended for production |
| [Chat app with an A2A agent](https://developers.google.com/workspace/add-ons/chat/quickstart-a2a-agent) | Your agent speaks A2A |
| **Gemini Enterprise** (project 02 §9) | Users chat with agents in the Gemini Enterprise app rather than in Chat. No code at all; requires a Gemini Enterprise licence |

---

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| Chat says *"Currency Agent is not responding"* | `gcloud run services logs read chat-bridge ...`: a 403 means `chat_invoker` is missing or the wrong SA (compare with the SA shown on the Chat config page); a 500 means a Python error, and the traceback is in the logs |
| Can't find the app in Chat | Your email isn't in *Visibility*, or your admin blocks Chat apps for your OU |
| `Google Chat API is only available to Google Workspace users` | You're logged in with a personal Gmail account: use your company account |
| Answers but forgets context | Check session reuse in the agent's *Sessions* tab: `user_id` must stay the same |
| `apply` error on `chat_invoker` | See the note in 5.1 |

---

## 12. Clean up

1. Chat API → Configuration: delete or disable the app (and unpublish it from the Marketplace SDK if published).
2. `cd terraform && terraform destroy`
