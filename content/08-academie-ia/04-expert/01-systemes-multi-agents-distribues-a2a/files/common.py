"""Briques partagées par les 3 agents : modèle, jeton entre agents, serveur A2A protégé."""
import hmac
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a

load_dotenv(Path(__file__).with_name(".env"))  # .env du dossier du lab uniquement

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
HOST = os.environ.get("A2A_HOST", "localhost")
CARD_PATH = "/.well-known/agent-card.json"


def a2a_token() -> str:
    """Jeton partagé entre agents (en production : un jeton d'identité par appelant)."""
    token = os.environ.get("A2A_TOKEN", "")
    if len(token) < 16:
        raise RuntimeError("A2A_TOKEN absent ou trop court (16 caractères minimum).")
    return token


class BearerAuth:
    """Middleware ASGI : l'Agent Card reste publique, l'appel JSON-RPC exige le jeton."""

    def __init__(self, app, token: str):
        self.app, self.expected = app, f"Bearer {token}".encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and not scope["path"].endswith(CARD_PATH):
            got = dict(scope["headers"]).get(b"authorization", b"")
            if not hmac.compare_digest(got, self.expected):  # comparaison à temps constant
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})
                return
        await self.app(scope, receive, send)


def serve(agent, port: int, token: str | None = None):
    """Transforme un agent ADK en application A2A (Starlette) protégée par jeton."""
    # Derrière Cloud Run : A2A_HOST=<service>.run.app, A2A_PROTOCOL=https, A2A_PUBLIC_PORT=443
    app = to_a2a(agent, host=HOST, port=int(os.environ.get("A2A_PUBLIC_PORT", port)),
                 protocol=os.environ.get("A2A_PROTOCOL", "http"))
    app.add_middleware(BearerAuth, token=token or a2a_token())
    return app
