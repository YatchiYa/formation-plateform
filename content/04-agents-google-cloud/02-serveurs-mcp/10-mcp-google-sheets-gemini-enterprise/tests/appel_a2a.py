"""Appeler l'agent A2A EXACTEMENT comme Gemini Enterprise (agent ajouté avec une autorisation OAuth).

  X-Serverless-Authorization : jeton d'identité du « compte de l'app » (Cloud Run vérifie run.invoker)
  Authorization              : jeton OAuth de l'utilisateur (rangé par l'agent dans temp:AUTH_ID)

Variables : AGENT_URL, USER_TOKEN (facultatif : sans lui, comme avant « Autoriser »), ID_TOKEN (Cloud Run ; en local,
une valeur quelconque suffit), QUESTION, CONTEXTE (facultatif : continuer la même conversation, valeur affichée
par l'appel précédent).

  python tests/appel_a2a.py
"""
import json
import os
import urllib.request
import uuid

h = {"Content-Type": "application/json", "A2A-Version": "0.3",
     "X-Serverless-Authorization": f"Bearer {os.getenv('ID_TOKEN', 'local')}"}
if os.getenv("USER_TOKEN"):
    h["Authorization"] = f"Bearer {os.environ['USER_TOKEN']}"
msg = {"kind": "message", "role": "user", "messageId": str(uuid.uuid4()),
       "parts": [{"kind": "text", "text": os.environ["QUESTION"], "metadata": {"source": "appel_a2a.py"}}]}
if os.getenv("CONTEXTE"):
    msg["contextId"] = os.environ["CONTEXTE"]
corps = {"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"message": msg}}
req = urllib.request.Request(os.environ["AGENT_URL"].rstrip("/") + "/", json.dumps(corps).encode(), h)
r = json.load(urllib.request.urlopen(req, timeout=300))
r = r.get("result", r)
texte = " ".join(p.get("text", "") for a in r.get("artifacts", []) for p in a.get("parts", []))
print(f"état : {r.get('status', {}).get('state')}   CONTEXTE={r.get('contextId')}\n{texte or json.dumps(r, ensure_ascii=False)[:1500]}")
