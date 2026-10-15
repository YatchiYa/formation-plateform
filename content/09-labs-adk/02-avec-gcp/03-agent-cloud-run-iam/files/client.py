"""Appelle l'agent déployé sur Cloud Run (service privé) avec un jeton d'identité.

Usage :
    export SERVICE_URL=$(gcloud run services describe lab-agent-cloud-run-iam \
        --region europe-west1 --project "$PROJECT_ID" --format 'value(status.url)')
    export ID_TOKEN=$(gcloud auth print-identity-token)
    python client.py "Combien de jours de télétravail ai-je droit ?"
"""
import os
import sys
import uuid

import httpx

APP_NAME = os.environ.get("APP_NAME", "assistant_interne")


def demander(question: str, url: str, jeton: str, transport: httpx.BaseTransport | None = None) -> dict:
    """Crée une session puis envoie la question à l'API ADK (/run). Renvoie réponse et outils appelés."""
    entetes = {"Authorization": f"Bearer {jeton}"}
    user, session = "employe-demo", str(uuid.uuid4())
    with httpx.Client(base_url=url, headers=entetes, timeout=120, transport=transport) as http:
        r = http.post(f"/apps/{APP_NAME}/users/{user}/sessions/{session}", json={})
        r.raise_for_status()
        r = http.post("/run", json={
            "app_name": APP_NAME, "user_id": user, "session_id": session,
            "new_message": {"role": "user", "parts": [{"text": question}]},
        })
        r.raise_for_status()
    outils, texte = [], ""
    for ev in r.json():  # /run renvoie la liste des événements de l'invocation
        for part in (ev.get("content") or {}).get("parts", []):
            if part.get("functionCall"):
                outils.append(part["functionCall"]["name"])
            if part.get("text"):
                texte = part["text"]  # le dernier texte est la réponse finale
    return {"reponse": texte.strip(), "outils": outils}


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "Combien de jours de télétravail par semaine ?"
    resultat = demander(question, os.environ["SERVICE_URL"], os.environ["ID_TOKEN"])
    print("OUTILS  :", ", ".join(resultat["outils"]) or "aucun")
    print("REPONSE :", resultat["reponse"])
