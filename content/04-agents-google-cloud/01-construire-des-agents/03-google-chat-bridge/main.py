"""Google Chat (Workspace add-on, HTTP) -> agent on Agent Runtime.

Chat POSTs an event here; we forward the text to the agent and reply
synchronously with the agent's answer.
Auth: this Cloud Run service is private; only the Workspace add-ons service
account has roles/run.invoker, so Cloud Run itself rejects anyone else.
"""
import os

import agentplatform
from fastapi import FastAPI, Request

AGENT_NAME = os.environ["AGENT_NAME"]  # projects/.../locations/.../reasoningEngines/ID
_, PROJECT, _, LOCATION, *_ = AGENT_NAME.split("/")

agent = agentplatform.Client(project=PROJECT, location=LOCATION).runtimes.get(name=AGENT_NAME)
app = FastAPI()


def reply(text: str) -> dict:
    return {"hostAppDataAction": {"chatDataAction": {"createMessageAction": {"message": {"text": text}}}}}


async def session_for(user_id: str) -> str:
    # Stateless: reuse the user's most recent Agent Runtime session, else create one.
    # ponytail: one conversation per user across all spaces; key on space+user if you need separation.
    sessions = (await agent.async_list_sessions(user_id=user_id)).get("sessions", [])
    if sessions:
        return max(sessions, key=lambda s: s.get("lastUpdateTime", s.get("last_update_time", 0)))["id"]
    return (await agent.async_create_session(user_id=user_id))["id"]


@app.post("/")
async def chat_event(request: Request) -> dict:
    chat = (await request.json()).get("chat", {})

    if "addedToSpacePayload" in chat:
        return reply("Hi! Ask me to convert currencies, e.g. *100 USD to EUR*.")

    message = chat.get("messagePayload", {}).get("message")
    if not message:
        return {}  # other events (removed from space, etc.): nothing to say

    text = (message.get("argumentText") or message.get("text") or "").strip()  # argumentText drops the @mention
    user_id = message["sender"]["name"]  # "users/123..." — stable per person
    session_id = await session_for(user_id)

    answer = []
    async for event in agent.async_stream_query(user_id=user_id, session_id=session_id, message=text):
        answer += [p["text"] for p in (event.get("content") or {}).get("parts", []) if p.get("text")]
    return reply(answer[-1] if answer else "Sorry, I have no answer for that.")
