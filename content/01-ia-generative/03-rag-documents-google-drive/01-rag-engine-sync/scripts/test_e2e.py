"""Test de bout en bout du kit déployé, à travers l'interface (même API que la page web).

  python3 scripts/test_e2e.py [http://localhost:8080] [question_drive attendu_drive]

Chaque étape est vérifiée par une assertion ; la moindre erreur arrête le test (code de sortie 1).
  1. l'API répond
  2. dépôt d'un fichier contenant un code unique -> synchro -> indexé -> l'agent donne le code et cite le fichier
  3. même fichier modifié -> synchro -> l'agent donne le NOUVEAU code
  4. suppression -> synchro -> absent de l'index -> l'agent ne trouve plus le code
On vérifie l'ÉTAT FINAL (index, réponses), pas les compteurs du dernier rapport : une passe planifiée peut
passer juste après la nôtre et écrire son propre rapport (vérifié).
  5. (facultatif) une question sur un de VOS documents (Drive, Gemini Enterprise…) -> texte attendu + lien cité
Bibliothèque standard uniquement (aucune installation).
"""

import json
import random
import string
import sys
import time
import urllib.request
import uuid

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8080"
APP = "assistant_documents"


def call(method, path, body=None, headers=None, raw=False, timeout=300):
    # Origin comme un navigateur : ADK refuse (403) une origine qu'il n'attend pas (vérifié derrière le proxy).
    headers = {"Origin": BASE, **(headers or {})}
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if raw else json.loads(data or b"{}")


def post_json(path, obj):
    return call("POST", path, json.dumps(obj).encode(), {"Content-Type": "application/json"})


def upload(name, text):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"{name}\"\r\n"
            f"Content-Type: text/plain\r\n\r\n{text}\r\n--{boundary}--\r\n").encode()
    return call("POST", "/api/upload", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})


def stamp(delta=0):
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(time.time() + delta))


def act_and_wait(action, timeout=600):
    """Fait l'action (qui déclenche une synchro), puis attend la fin d'une passe COMMENCÉE après elle."""
    since = stamp(-1)  # une passe partie AVANT l'action ne compte pas (elle a pu ne pas voir le changement)
    result = action()
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = call("GET", "/api/status")
        last = s["derniere_synchro"]
        if not s["synchro_en_cours"] and last and last["debut"] >= since:
            return result, last
        time.sleep(8)
    raise AssertionError("la synchro n'a pas fini à temps")


def ask(question):
    sid = post_json(f"/apps/{APP}/users/e2e/sessions", {})["id"]
    events = call("POST", "/run", json.dumps({"appName": APP, "userId": "e2e", "sessionId": sid,
                                              "newMessage": {"role": "user", "parts": [{"text": question}]}}).encode(),
                  {"Content-Type": "application/json"})
    texts = [p["text"] for e in events for p in (e.get("content") or {}).get("parts", []) if p.get("text")]
    return texts[-1] if texts else ""


def step(n, label):
    print(f"[{n}] {label}", flush=True)


def ok(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"    OK  {msg}", flush=True)


def main():
    code1 = "".join(random.choices(string.ascii_uppercase, k=4)) + "-" + str(random.randint(1000, 9999))
    code2 = "".join(random.choices(string.ascii_uppercase, k=4)) + "-" + str(random.randint(1000, 9999))
    name = f"e2e-{code1.lower()}.txt"
    question = "Quel est le code d'accès du local à vélos du bâtiment Héron ?"

    step(1, "l'API répond")
    s = call("GET", "/api/status")
    ok(s["corpus"].startswith("projects/"), f"corpus {s['corpus']}")

    step(2, f"dépôt de {name} (code {code1}) puis synchro")
    r, last = act_and_wait(lambda: upload(name, f"Consigne interne de test.\nLe code d'accès du local à vélos du "
                                                f"bâtiment Héron est {code1}.\n"))
    ok(r["deposes"] == [name], f"déposé : {r['deposes']} (synchro {r['synchro']})")
    ok(last["statut"] in ("ok", "avertissement"), f"synchro {last['statut']} en {last['duree_s']} s")
    docs = {d["nom"]: d for d in call("GET", "/api/documents")}
    ok(name in docs and docs[name]["origine"] == "depot", f"{name} indexé (origine dépôt)")
    a = ask(question)
    ok(code1 in a, f"l'agent répond {code1}  (réponse : {a[:200]!r})")
    ok(name in a, "et cite le fichier")

    step(3, f"modification : nouveau code {code2}")
    r, last = act_and_wait(lambda: upload(name, f"Consigne interne de test (mise à jour).\nLe code d'accès du local "
                                                f"à vélos du bâtiment Héron est désormais {code2}.\n"))
    # On vérifie l'état final (la réponse), pas les compteurs : une passe planifiée a pu passer juste après.
    print(f"    ..  dernière passe : {next((x for x in last['sources'] if x['source'] == 'Fichiers déposés'), {})}")
    a = ask(question)
    ok(code2 in a and code1 not in a, f"l'agent répond {code2} (plus {code1})  (réponse : {a[:200]!r})")

    step(4, "suppression")
    r, last = act_and_wait(lambda: call("DELETE", "/api/documents?cle=" + urllib.request.quote(docs[name]["cle"], safe="")))
    print(f"    ..  dernière passe : {last['supprimes']} retiré(s)")
    ok(name not in {d["nom"] for d in call("GET", "/api/documents")}, f"{name} absent de l'index")
    a = ask(question)
    ok(code2 not in a, "l'agent ne connaît plus le code")

    if len(sys.argv) > 3:
        q, expected = sys.argv[2], sys.argv[3]
        step(5, f"vos documents : « {q} »")
        a = ask(q)
        ok(expected.lower() in a.lower(), f"réponse contient « {expected} »  ({a[:200]!r})")
        ok("](http" in a, "avec un lien vers sa source")

    print("\nTOUT EST OK")


def cleanup():
    """En cas d'échec : retirer les fichiers de test restés dans les dépôts (sinon ils faussent les tests suivants)."""
    for d in call("GET", "/api/documents"):
        if d["origine"] == "depot" and d["nom"].startswith("e2e-"):
            call("DELETE", "/api/documents?cle=" + urllib.request.quote(d["cle"], safe=""))
            print(f"    (nettoyage : {d['nom']} supprimé)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"    ÉCHEC  {e}")
        cleanup()
        sys.exit(1)
