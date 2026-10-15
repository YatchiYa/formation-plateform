"""Client A2A minimal en JSON-RPC brut (httpx) : utile pour voir le protocole « à nu ».

python client.py "Devis pour 12 CHAISE-ERGO"            # SendMessage (réponse unique)
python client.py --stream "Devis pour 12 CHAISE-ERGO"   # SendStreamingMessage (SSE)
"""
import json
import os
from pathlib import Path
import sys
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))  # .env du dossier du lab uniquement
HEADERS = {"A2A-Version": "1.0", "Content-Type": "application/json"}


def _payload(method: str, text: str) -> dict:
    return {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method,
            "params": {"message": {"messageId": str(uuid.uuid4()), "role": "ROLE_USER",
                                   "parts": [{"text": text}]}}}


def _auth(token: str | None) -> dict:
    return {**HEADERS, "Authorization": f"Bearer {token or os.environ['A2A_TOKEN']}"}


def task_text(task: dict) -> str:
    """Texte des artefacts d'une tâche A2A terminée."""
    return "\n".join(p["text"] for a in task.get("artifacts", []) for p in a["parts"] if "text" in p)


def send(url: str, text: str, token: str | None = None, timeout: float = 120) -> dict:
    """SendMessage : renvoie la tâche finale (id, status.state, artifacts…)."""
    r = httpx.post(url, json=_payload("SendMessage", text), headers=_auth(token), timeout=timeout)
    r.raise_for_status()
    body = r.json()
    if "error" in body:
        raise RuntimeError(body["error"]["message"])
    return body["result"]["task"]


def stream(url: str, text: str, token: str | None = None, timeout: float = 120):
    """SendStreamingMessage : produit chaque événement SSE (task, statusUpdate, artifactUpdate)."""
    with httpx.stream("POST", url, json=_payload("SendStreamingMessage", text),
                      headers=_auth(token), timeout=timeout) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if line.startswith("data:"):
                yield json.loads(line[5:])["result"]


if __name__ == "__main__":
    args = sys.argv[1:]
    url = os.environ.get("ORCH_URL", "http://localhost:8100/")
    if args and args[0] == "--stream":
        for ev in stream(url, " ".join(args[1:])):
            kind = next(iter(ev))
            state = ev[kind].get("status", {}).get("state", "")
            print(f"[{kind}] {state}")
            if kind == "artifactUpdate":
                print(task_text({"artifacts": [ev[kind]["artifact"]]}))
    else:
        t = send(url, " ".join(args) or "Devis pour 12 CHAISE-ERGO")
        print(t["status"]["state"], "\n" + task_text(t))
