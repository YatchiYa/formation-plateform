#!/usr/bin/env bash
# Test de bout en bout des agents A2A sur Cloud Run (un service par agent), avec LE MÊME protocole que Gemini Enterprise
# (A2A v0.3, message/send puis 2e tour dans la même conversation).
#
#   ./test.sh                         URL lues dans terraform output
#   URL=http://localhost:8080 ./test.sh meteo   un seul agent, en local (docker run, voir README)
#   URL=https://meteo-a2a-NUM.europe-west1.run.app ./test.sh meteo   un seul agent déployé (votre jeton)
set -euo pipefail
cd "$(dirname "$0")"

if [ -n "${URL:-}" ]; then URLS="{\"${1:-meteo}\": \"$URL\"}"
  case "$URL" in https://*) TOKEN=$(gcloud auth print-identity-token);; *) TOKEN="";; esac   # service déployé : jeton ; local : rien
else URLS=$(terraform -chdir=terraform output -json urls); TOKEN=$(gcloud auth print-identity-token); fi

URLS="$URLS" TOKEN="$TOKEN" python3 - <<'PY'
import json, os, sys, time, urllib.error, urllib.request, uuid

QUESTIONS = {
    "meteo": ("Quel temps fait-il à Chamonix ?", "Et pour y randonner, quoi porter ?"),
    "redaction": ("Reformule pour un email client : 'ton velo est pret passe avant samedi'", "Plus court, en 2 phrases."),
    "traduction": ("Traduis en espagnol : 'Votre tente Quechua est disponible en retrait en magasin.'", "Et en italien ?"),
}
CATALOGUE = json.load(open(os.path.join("..", "agents", "trio", "catalogue.json")))
for cle, agent in CATALOGUE.items():   # nouveaux agents : la 1re question d'exemple du catalogue
    if cle not in QUESTIONS:
        exemple = next((e for c in agent["competences"] for e in c.get("examples", [])), "Que sais-tu faire ?")
        QUESTIONS[cle] = (exemple, "Peux-tu résumer ta réponse en une phrase ?")
H = {"Content-Type": "application/json", "A2A-Version": "0.3"}
if os.environ["TOKEN"]:
    H["Authorization"] = "Bearer " + os.environ["TOKEN"]

def call(url, path="", body=None):
    req = urllib.request.Request(url.rstrip("/") + path, json.dumps(body).encode() if body else None, H)
    for attempt in range(3):   # erreurs passagères de Google (404 hors conteneur, 429, 5xx) : on réessaie
        try:
            return json.load(urllib.request.urlopen(req, timeout=180))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                sys.exit(f"ÉCHEC : {e.code} sur {req.full_url} : votre compte n'a pas le droit d'appeler ce service (roles/run.invoker).")
            if attempt == 2 or e.code not in (404, 429, 500, 502, 503, 504):
                raise
            time.sleep(5)

def send(url, text, ctx=None):
    # Métadonnées sur le morceau de texte, comme Gemini Enterprise (sans elles, un défaut de l'agent passait inaperçu).
    msg = {"kind": "message", "role": "user", "messageId": str(uuid.uuid4()),
           "parts": [{"kind": "text", "text": text, "metadata": {"source": "test.sh"}}]}
    if ctx:
        msg["contextId"] = ctx
    r = call(url, body={"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"message": msg}})
    assert "result" in r, r.get("error")
    r = r["result"]
    text = " ".join(p.get("text", "") for a in r.get("artifacts", []) for p in a["parts"])
    assert r["status"]["state"] == "completed" and text, r["status"]
    if "Model Armor" in text:   # question normale bloquée = droit modelarmor.user pas encore actif, ou template injoignable
        sys.exit("ÉCHEC : réponse bloquée par Model Armor. Juste après le premier apply, attendre 2 à 5 minutes "
                 "(propagation des droits) et relancer ; sinon, voir les journaux Cloud Run (403 modelarmor).")
    return r["contextId"], text

for name, url in json.loads(os.environ["URLS"]).items():
    card = call(url, "/.well-known/agent-card.json")
    print(f"== {name}  carte : {card['name']} (A2A {card.get('protocolVersion') or card['supportedInterfaces'][0]['protocolVersion']})")
    q1, q2 = QUESTIONS[name]
    ctx, t1 = send(url, q1)
    print(f"   Q1 > {q1}\n   R1 < {t1[:220]}")
    ctx2, t2 = send(url, q2, ctx)
    assert ctx2 == ctx
    print(f"   Q2 > {q2}\n   R2 < {t2[:220]}\n")
print("OK : les agents répondent en A2A v0.3, avec mémoire de conversation")
PY
