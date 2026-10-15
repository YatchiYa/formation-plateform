"""Serveur A2A d'UN agent du trio, pour Cloud Run, appelable par Gemini Enterprise.

Chaque agent a son image (Dockerfile, construite par Cloud Build) ; la variable AGENT dit lequel servir (ex. meteo_agent).
Un service Cloud Run par agent = une URL, une identité et un droit d'appel par agent.

  - GET  /.well-known/agent-card.json   carte de l'agent (A2A)
  - POST /                              appels A2A JSON-RPC (message/send, message/stream ; v0.3 et v1.0)

AGENT_CARD : la carte A2A v0.3 (JSON) écrite par Terraform, avec l'URL publique du service. C'est la même que celle
collée dans Gemini Enterprise et déclarée dans Agent Registry. Absente en local : carte générée depuis l'agent.

AUTH_ID (optionnel) : agent enregistré avec une autorisation OAuth (docs/12-3, partie C). Gemini Enterprise envoie alors
le jeton de l'utilisateur dans l'en-tête Authorization (son propre jeton d'appel est dans X-Serverless-Authorization,
consommé par Cloud Run). On le range dans l'état « temp:AUTH_ID », comme Agent Runtime : commun.jeton_utilisateur()
le lit de la même façon aux deux endroits.
"""
import importlib
import json
import os
import tempfile

from google.adk.a2a.converters.request_converter import convert_a2a_request_to_agent_run_request
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.artifacts import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

module = importlib.import_module(f"{os.environ['AGENT']}.agent")

# Runner construit sur `app` (et non sur root_agent seul) : c'est lui qui porte le plugin Model Armor.
# ponytail: sessions en mémoire => max 1 instance Cloud Run ; base de données de sessions avant d'en mettre plus.
runner = Runner(app=module.app, session_service=InMemorySessionService(), artifact_service=InMemoryArtifactService(),
                memory_service=InMemoryMemoryService(), credential_service=InMemoryCredentialService())

card = None
if os.getenv("AGENT_CARD"):
    card = os.path.join(tempfile.mkdtemp(), "agent-card.json")
    with open(card, "w", encoding="utf-8") as f:
        json.dump(json.loads(os.environ["AGENT_CARD"]), f)



def avec_jeton_utilisateur(request, part_converter):
    """Requête A2A -> exécution ADK, plus le jeton OAuth de l'utilisateur (si AUTH_ID) dans « temp:AUTH_ID »."""
    run = convert_a2a_request_to_agent_run_request(request, part_converter)
    headers = request.call_context.state.get("headers", {}) if request.call_context else {}
    auth = headers.get("authorization", "")
    # Sans X-Serverless-Authorization, l'en-tête Authorization est le jeton d'appel Cloud Run, pas celui de l'utilisateur.
    if os.getenv("AUTH_ID") and "x-serverless-authorization" in headers and auth.lower().startswith("bearer "):
        # A2A = UNE autorisation par agent : la 1re de AUTH_ID (docs/12-1-8).
        run.state_delta = {**(run.state_delta or {}), f"temp:{os.environ['AUTH_ID'].split(',')[0]}": auth[7:]}
    return run


app = to_a2a(module.root_agent, runner=runner, agent_card=card, port=int(os.getenv("PORT", "8080")),
             agent_executor_factory=lambda r: A2aAgentExecutor(
                 runner=r, config=A2aAgentExecutorConfig(request_converter=avec_jeton_utilisateur)))
