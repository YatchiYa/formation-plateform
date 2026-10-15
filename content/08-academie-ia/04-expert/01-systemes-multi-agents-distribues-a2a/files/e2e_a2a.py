"""Test de bout en bout AVEC le vrai modèle : 3 serveurs A2A sur 3 ports.

python e2e_a2a.py      (lit la clé et A2A_TOKEN depuis l'environnement ou .env)
Une quinzaine d'appels au modèle au total.
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import httpx

from client import send, stream, task_text
from orchestrator import discover

HERE = Path(__file__).parent
PORTS = {"stock_agent": 8101, "pricing_agent": 8102, "orchestrator": 8100}
ORCH = "http://localhost:8100/"


def start(name: str, **env) -> subprocess.Popen:
    p = subprocess.Popen([sys.executable, "-m", "uvicorn", f"{name}:app", "--port", str(PORTS[name])],
                         cwd=HERE, env={**os.environ, **env},
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    card = f"http://localhost:{PORTS[name]}/.well-known/agent-card.json"
    for _ in range(60):  # attend que l'Agent Card réponde
        try:
            httpx.get(card, timeout=1).raise_for_status()
            return p
        except httpx.HTTPError:
            time.sleep(0.5)
    p.kill()
    raise RuntimeError(f"{name} n'a pas démarré")


def digits(s: str) -> str:
    return re.sub(r"[^\d]", "", s)


def main():
    procs = {n: start(n) for n in ("stock_agent", "pricing_agent")}
    procs["orchestrator"] = start("orchestrator")
    try:
        print("1) Devis complet en streaming")
        states, answer = [], ""
        for ev in stream(ORCH, "Je voudrais un devis pour 12 CHAISE-ERGO"):
            kind = next(iter(ev))
            states.append(ev[kind].get("status", {}).get("state", kind))
            if kind == "artifactUpdate":
                answer += task_text({"artifacts": [ev[kind]["artifact"]]})
        print("   états :", " > ".join(dict.fromkeys(states)))
        print("   réponse :", answer.replace("\n", " ")[:300])
        assert states[-1] == "TASK_STATE_COMPLETED" and "204120" in digits(answer)  # 12*189*0,90

        print("2) Appel sans jeton")
        r = httpx.post(ORCH, json={}, timeout=5)
        print("   HTTP", r.status_code)
        assert r.status_code == 401

        print("3) Panne de l'agent tarification pendant le service")
        procs.pop("pricing_agent").kill()
        t = send(ORCH, "Devis pour 6 BUREAU-120")
        print("   réponse :", task_text(t).replace("\n", " ")[:300])
        assert t["status"]["state"] == "TASK_STATE_COMPLETED"
        assert "18753" not in digits(task_text(t))  # le prix (6*329*0,95) ne peut pas être connu

        print("4) Découverte avec un agent absent du réseau")
        found, missing = discover()
        print("   disponibles :", [a["name"] for a in found], "| absents :", missing)
        assert missing == ["pricing_agent"]

        print("5) Délai dépassé (A2A_TIMEOUT=1 s)")
        procs["pricing_agent"] = start("pricing_agent")
        procs.pop("orchestrator").kill()
        procs["orchestrator"] = start("orchestrator", A2A_TIMEOUT="1")
        t = send(ORCH, "Devis pour 3 BUREAU-120")
        print("   réponse :", task_text(t).replace("\n", " ")[:300])
        assert "987" not in digits(task_text(t))  # 3*329 = 987 : ne doit pas apparaître
        print("OK : 5 scénarios passés")
    finally:
        for p in procs.values():
            p.kill()


if __name__ == "__main__":
    main()
