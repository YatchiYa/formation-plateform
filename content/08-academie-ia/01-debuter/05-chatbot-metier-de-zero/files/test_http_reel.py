"""Test de bout en bout : vrai serveur uvicorn, vraies requêtes HTTP, vrai modèle.

Ignoré sans clé. Lancer :  pytest -s test_http_reel.py
"""
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv()
pytestmark = pytest.mark.skipif(
    not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE"),
    reason="pas de GOOGLE_API_KEY : test réel ignoré")


@pytest.fixture(scope="module")
def url(tmp_path_factory):
    with socket.socket() as s:  # un port libre
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    env = {**os.environ, "JOURNAL": str(tmp_path_factory.mktemp("j") / "journal.jsonl")}
    serveur = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--port", str(port), "--log-level", "warning"],
        cwd=Path(__file__).parent, env=env)
    base = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            if httpx.get(base + "/sante").status_code == 200:
                break
        except httpx.ConnectError:
            time.sleep(0.2)
    yield base
    serveur.terminate()
    serveur.wait()


def demander(url, session, message):
    """Envoie une question et lit la réponse en streaming, morceau par morceau."""
    debut, premier, morceaux = time.monotonic(), None, []
    with httpx.stream("POST", url + "/chat", json={"session": session, "message": message},
                      timeout=90) as r:
        assert r.status_code == 200
        for m in r.iter_text():
            premier = premier or time.monotonic() - debut
            morceaux.append(m)
        eid = r.headers["x-echange-id"]
    texte = "".join(morceaux)
    print(f"\n> {message}\n< {texte.strip()}\n  ({len(morceaux)} morceaux, "
          f"1er après {premier:.1f}s, total {time.monotonic() - debut:.1f}s)")
    return texte, eid


def test_conversation_complete(url):
    s = uuid.uuid4().hex
    assert "getReader" in httpx.get(url + "/").text

    texte, eid = demander(url, s, "Bonjour, à quelle heure ouvrez-vous le samedi ?")
    assert "8" in texte and "20" in texte                      # 8h à 20h dans la fiche

    texte, _ = demander(url, s, "Et le dimanche ?")             # demande la mémoire
    assert "9" in texte and "14" in texte

    texte, _ = demander(url, s, "Combien coûte la formule Premium et que contient-elle ?")
    assert "54" in texte

    texte, _ = demander(url, s, "J'ai mal au genou depuis ma dernière séance, quel exercice faire ?")
    assert any(m in texte.lower() for m in ("médecin", "kiné"))  # refus + orientation

    texte, _ = demander(url, s, "Comment s'appelle le professeur du yoga du lundi ?")  # absent de la fiche
    assert "accueil" in texte.lower()

    assert httpx.post(url + "/avis", json={"echange_id": eid, "note": 1}).status_code == 200
    stats = httpx.get(url + "/stats").json()
    print("\nstats :", stats)
    assert stats["echanges"] == 5 and stats["satisfaction"] == 1.0 and stats["erreurs"] == 0
