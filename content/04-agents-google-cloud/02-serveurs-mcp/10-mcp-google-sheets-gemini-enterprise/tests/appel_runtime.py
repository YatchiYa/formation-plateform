"""Appeler l'agent Agent Runtime EXACTEMENT comme Gemini Enterprise : méthode streaming_agent_run_with_events, avec le
jeton de l'utilisateur dans « authorizations » (clé = ID de l'autorisation). Repris du simulateur du projet 09.

  USER_TOKEN=… python tests/appel_runtime.py <projects/…/reasoningEngines/ID> <ID autorisation> "<question>"
Jeton d'appel : le vôtre (gcloud) ; Gemini Enterprise utilise le sien (droit ② discoveryengine.serviceAgent).
"""
import json
import os
import subprocess
import sys
import urllib.request

moteur, auth_id, question = sys.argv[1:4]
region = moteur.split("/")[3]
req_json = {"message": {"role": "user", "parts": [{"text": question}]}, "user_id": "test-projet-10",
            "authorizations": {auth_id: {"access_token": os.environ["USER_TOKEN"]}}}
corps = {"class_method": "streaming_agent_run_with_events", "input": {"request_json": json.dumps(req_json)}}
jeton = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
req = urllib.request.Request(f"https://{region}-aiplatform.googleapis.com/v1/{moteur}:streamQuery?alt=sse",
                             json.dumps(corps).encode(), {"Content-Type": "application/json", "Authorization": f"Bearer {jeton}"})
textes = []
for ligne in urllib.request.urlopen(req, timeout=300).read().decode().splitlines():
    ligne = ligne.strip().removeprefix("data: ")
    if ligne:
        for ev in json.loads(ligne).get("events", [json.loads(ligne)]):
            textes += [p["text"] for p in (ev.get("content") or {}).get("parts", []) if p.get("text")]
print(" ".join(textes) or "(aucun texte : voir les journaux de l'agent)")
