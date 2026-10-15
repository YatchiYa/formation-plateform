"""Client A2A minimal (JSON-RPC, protocole A2A 1.0) : lit la carte de l'agent puis lui envoie un message.

Local :     python client_a2a.py http://localhost:8002 "Devis pour 500 VIS-M6"
Cloud Run : ID_TOKEN=$(gcloud auth print-identity-token) python client_a2a.py https://... "..."
"""
import os
import sys
import uuid

import httpx


def appeler(url: str, texte: str, jeton: str | None = None, transport: httpx.BaseTransport | None = None) -> dict:
    entetes = {"A2A-Version": "1.0"}
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    with httpx.Client(headers=entetes, timeout=180, transport=transport) as http:
        carte = http.get(f"{url.rstrip('/')}/.well-known/agent-card.json").raise_for_status().json()
        point = carte["supportedInterfaces"][0]["url"]  # l'URL RPC annoncée par la carte
        r = http.post(point, json={
            "jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "SendMessage",
            "params": {"message": {"messageId": str(uuid.uuid4()), "role": "ROLE_USER", "parts": [{"text": texte}]}},
        }).raise_for_status().json()
    if "error" in r:
        raise RuntimeError(r["error"])
    tache = r["result"]["task"]
    reponse = " ".join(p.get("text", "") for a in tache.get("artifacts", []) for p in a["parts"]).strip()
    appels = [p["data"]["name"] for m in tache.get("history", []) for p in m["parts"]
              if p.get("metadata", {}).get("adk_type") == "function_call"]
    return {"agent": carte["name"], "etat": tache["status"]["state"], "outils": appels, "reponse": reponse}


if __name__ == "__main__":
    res = appeler(sys.argv[1], sys.argv[2], os.environ.get("ID_TOKEN"))
    for cle, val in res.items():
        print(f"{cle.upper():8}: {val}")
