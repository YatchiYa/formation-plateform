"""Test de bout en bout : lance l'API RH locale, puis joue 6 scénarios avec le VRAI modèle.

Usage :  python e2e.py          (clé GEMINI_API_KEY / GOOGLE_API_KEY, ou Vertex AI via .env)
Environ 15 à 25 appels au modèle.
"""
import json
import os
import subprocess
import sys
import time

import httpx
from dotenv import load_dotenv
from google import genai

load_dotenv()
os.environ.setdefault("AUDIT_PATH", "audit_e2e.jsonl")
import assistant  # noqa: E402  (après AUDIT_PATH)

PORT = "8077"
SCENARIOS = [
    # (utilisateur, question, mode, réponse aux confirmations)
    ("E001", "Combien de jours de congés me reste-t-il ?", "AUTO", True),
    ("E004", "Compare les soldes de RTT de Camille Martin et de Karim Benali.", "AUTO", True),
    ("E001", "Pose-moi des RTT du 2026-11-04 au 2026-11-06.", "AUTO", True),
    ("E001", "Finalement, annule cette demande.", "AUTO", False),
    ("E004", "Quel est le solde de Lucie Moreau ?", "AUTO", True),
    ("E001", "Explique-moi en une phrase ce qu'est un RTT.", "NONE", True),
]


def main():
    if os.path.exists(assistant.AUDIT_PATH):
        os.remove(assistant.AUDIT_PATH)
    api = subprocess.Popen([sys.executable, "-m", "uvicorn", "api_rh:app", "--port", PORT,
                            "--log-level", "warning"])
    try:
        for _ in range(50):
            try:
                if httpx.get(f"http://127.0.0.1:{PORT}/sante").status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.2)
        client = genai.Client()
        print(f"Modèle : {assistant.MODEL} | Vertex AI : {os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', 'FALSE')}")
        historiques = {}
        for utilisateur, question, mode, oui in SCENARIOS:
            print(f"\n[{utilisateur}] {question}   (mode {mode})")
            reponse = assistant.repondre(
                client, historiques.setdefault(utilisateur, []), question, utilisateur,
                confirmer=lambda nom, args, oui=oui: print(f"  ⚠ confirmation {nom} -> {'oui' if oui else 'non'}") or oui,
                mode=mode)
            print("  →", reponse.strip().replace("\n", " ")[:300])
    finally:
        api.terminate()
    print("\nJournal d'audit :")
    with open(assistant.AUDIT_PATH, encoding="utf-8") as f:
        for ligne in f:
            e = json.loads(ligne)
            print(f"  {e['utilisateur']} {e['outil']:<21} {e['statut']:<19} {json.dumps(e['args'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
