"""Serveur A2A de l'agent « Assistant Google Sheets », pour Cloud Run, appelable par Gemini Enterprise.

  - GET  /.well-known/agent-card.json   carte de l'agent
  - POST /                              appels A2A JSON-RPC (message/send, message/stream)

Gemini Enterprise (agent ajouté AVEC une autorisation OAuth) envoie :
  X-Serverless-Authorization : son propre jeton, consommé par Cloud Run (run.invoker) ;
  Authorization              : le jeton OAuth de l'utilisateur -> rangé dans l'état « temp:AUTH_ID », jamais enregistré.
L'agent le relit (sheets_agent.agent.jeton_utilisateur) et le transmet au serveur MCP.

Variables : AGENT_URL (adresse publique du service, pour la carte), MCP_URL, AUTH_ID, PORT.
"""
import json
import os
import tempfile

from google.adk.a2a.converters.request_converter import convert_a2a_request_to_agent_run_request
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.executor.config import A2aAgentExecutorConfig
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from carte import carte
from sheets_agent import agent

# ponytail: sessions en mémoire => 1 instance Cloud Run max ; une base de sessions avant d'en mettre plus.
runner = Runner(app=agent.app, session_service=InMemorySessionService(), artifact_service=InMemoryArtifactService(),
                memory_service=InMemoryMemoryService())

fichier_carte = os.path.join(tempfile.mkdtemp(), "agent-card.json")
with open(fichier_carte, "w", encoding="utf-8") as f:
    json.dump(carte(os.getenv("AGENT_URL", f"http://localhost:{os.getenv('PORT', '8080')}")), f)


def avec_jeton_utilisateur(request, part_converter):
    """Requête A2A -> exécution ADK, plus le jeton OAuth de l'utilisateur dans « temp:AUTH_ID »."""
    run = convert_a2a_request_to_agent_run_request(request, part_converter)
    headers = request.call_context.state.get("headers", {}) if request.call_context else {}
    auth = headers.get("authorization", "")
    # Sans X-Serverless-Authorization, « Authorization » est le jeton d'appel Cloud Run, pas celui de l'utilisateur.
    if "x-serverless-authorization" in headers and auth.lower().startswith("bearer "):
        run.state_delta = {**(run.state_delta or {}), f"temp:{agent.AUTH_ID}": auth[7:]}
    return run


app = to_a2a(agent.root_agent, runner=runner, agent_card=fichier_carte, port=int(os.getenv("PORT", "8080")),
             agent_executor_factory=lambda r: A2aAgentExecutor(
                 runner=r, config=A2aAgentExecutorConfig(request_converter=avec_jeton_utilisateur)))
