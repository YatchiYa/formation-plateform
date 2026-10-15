"""Test de la chaîne complète de l'agent, SANS Gemini (pas besoin de Vertex AI ni de facturation) :

  appel A2A comme Gemini Enterprise (2 en-têtes) -> agent/main.py (range le jeton) -> agent ADK -> McpToolset
  -> serveur MCP (local) -> VRAIE API Google Sheets avec le jeton de l'utilisateur

Seul le modèle est remplacé par un « faux Gemini » qui demande l'outil read_range, puis répond avec son résultat.
Vérifie aussi : sans jeton utilisateur, l'agent ne voit qu'un outil (autorisation_requise) au lieu d'une erreur.

Variables : USER_TOKEN (portées spreadsheets + presentations + userinfo.email), SPREADSHEET_ID, OAUTH_CLIENT_IDS, ALLOWED_DOMAINS
(les valeurs qui acceptent ce jeton : voir docs/10-8).
  python tests/test_agent_chaine.py
"""
import json
import os
import socket
import sys
import threading
import time
import urllib.request
import uuid
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent


def port_libre() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


P_MCP, P_SLIDES, P_AGENT = port_libre(), port_libre(), port_libre()
os.environ["MCP_URL"] = f"http://127.0.0.1:{P_MCP}/mcp"
os.environ["MCP_SLIDES_URL"] = f"http://127.0.0.1:{P_SLIDES}/mcp"   # les deux serveurs : Sheets et Slides
sys.path[:0] = [str(ICI / "agent"), str(ICI / "mcp_server")]   # carte.py, sheets_agent ; noyau, outils_*

import uvicorn  # noqa: E402
from google.adk.models.base_llm import BaseLlm  # noqa: E402
from google.adk.models.llm_response import LlmResponse  # noqa: E402
from google.genai import types  # noqa: E402

import importlib.util  # noqa: E402


def charger(nom: str, fichier: Path):
    """Les deux serveurs s'appellent main.py : on les charge par leur chemin."""
    spec = importlib.util.spec_from_file_location(nom, fichier)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


os.environ["PRODUIT"] = "sheets"
serveur_mcp = charger("serveur_mcp", ICI / "mcp_server" / "main.py")
os.environ["PRODUIT"] = "slides"
serveur_slides = charger("serveur_slides", ICI / "mcp_server" / "main.py")
serveur_a2a = charger("serveur_a2a", ICI / "agent" / "main.py")
from sheets_agent import agent  # noqa: E402

SID = os.environ["SPREADSHEET_ID"]
VUS: list[list[str]] = []


class FauxGemini(BaseLlm):
    """Appelle read_range si l'outil est proposé (sinon autorisation_requise), puis renvoie le résultat de l'outil."""
    model: str = "faux-gemini"

    async def generate_content_async(self, llm_request, stream=False):
        VUS.append(sorted(llm_request.tools_dict))
        reponses = [p.function_response for p in llm_request.contents[-1].parts or [] if p.function_response]
        if reponses:
            texte = "RÉSULTAT " + json.dumps(reponses[0].response, ensure_ascii=False)
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text=texte)]))
        elif "read_range" in llm_request.tools_dict:
            appel = types.FunctionCall(name="read_range", args={"spreadsheet_id": SID, "range_a1": "A1:C4"})
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=appel)]))
        else:
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(function_call=types.FunctionCall(name="autorisation_requise", args={}))]))


agent.root_agent.model = FauxGemini()


def demarrer(app, port):
    s = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=s.run, daemon=True).start()
    while not s.started:
        time.sleep(0.05)


def appel(jeton_utilisateur: str | None) -> str:
    h = {"Content-Type": "application/json", "A2A-Version": "0.3", "X-Serverless-Authorization": "Bearer jeton-de-l-app"}
    if jeton_utilisateur:
        h["Authorization"] = f"Bearer {jeton_utilisateur}"
    msg = {"kind": "message", "role": "user", "messageId": str(uuid.uuid4()),
           "parts": [{"kind": "text", "text": "Lis A1:C4", "metadata": {"source": "test"}}]}
    req = urllib.request.Request(f"http://127.0.0.1:{P_AGENT}/", json.dumps(
        {"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"message": msg}}).encode(), h)
    r = json.load(urllib.request.urlopen(req, timeout=120))["result"]
    assert r["status"]["state"] == "completed", r
    return " ".join(p.get("text", "") for a in r.get("artifacts", []) for p in a["parts"])


demarrer(serveur_mcp.app, P_MCP)
demarrer(serveur_slides.app, P_SLIDES)
demarrer(serveur_a2a.app, P_AGENT)

texte = appel(os.environ["USER_TOKEN"])
print(f"outils vus par le modèle : {len(VUS[0])} ({', '.join(VUS[0][:4])}…)")
assert len(VUS[0]) == 37 and "slides_add_slide" in VUS[0] and "slides_batch_update" in VUS[0] and "batch_update" in VUS[0], VUS[0]   # 17 Sheets + 20 Slides, sans collision
print(f"réponse de l'agent        : {texte[:160]}")
assert "Tente" in texte and "149" in texte, texte

VUS.clear()
texte = appel(None)
print(f"sans jeton utilisateur    : outils {VUS[0]} -> {texte[:120]}")
assert VUS[0] == ["autorisation_requise"] and "Autoriser" in texte, (VUS, texte)
print("\nOK : A2A -> agent -> MCP -> Google Sheets, avec le jeton de l'utilisateur ; sans jeton, message clair.")
