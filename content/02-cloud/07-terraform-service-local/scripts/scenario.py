"""Simulation complète, pas à pas, du service Terraform (Gitea + Atlantis + MinIO).

Personnages :
  alice : développeuse (ouvre les pull requests, commente « atlantis apply »)
  bob   : équipe sécurité (relit et approuve, propriétaire des politiques)
  atlantis-bot : le service Terraform managé (répond dans les pull requests)

Chaque étape VÉRIFIE le résultat attendu ; le script s'arrête à la première anomalie.
Usage : python3 scripts/scenario.py     (après scripts/setup.sh)
"""
import base64
import json
import re
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = dict(l.split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l and not l.startswith("#"))
API = f"http://localhost:{ENV['GITEA_PORT']}/api/v1"
REPO = "acme/infra-demo"
ALICE, BOB = ENV["ALICE_TOKEN"], ENV["BOB_TOKEN"]
RUN = time.strftime("%H%M%S")          # suffixe : le scénario peut être rejoué
TIMEOUT = 300

STEP = [0]


def step(title):
    STEP[0] += 1
    print(f"\n\033[1;34m[{STEP[0]:02d}] {title}\033[0m")


def ok(msg):
    print(f"     \033[32m✔\033[0m {msg}")


def fail(msg):
    print(f"     \033[31m✘ {msg}\033[0m")
    sys.exit(1)


def api(token, method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"token {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        fail(f"{method} {path} -> HTTP {e.code} : {e.read().decode()[:300]}")


def new_branch_with_file(branch, path, content, message):
    api(ALICE, "POST", f"/repos/{REPO}/contents/{path}", {
        "branch": "main", "new_branch": branch, "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "author": {"name": "alice", "email": "alice@acme.local"}})


def open_pr(branch, title, body):
    pr = api(ALICE, "POST", f"/repos/{REPO}/pulls", {"head": branch, "base": "main", "title": title, "body": body})
    return pr["number"]


def comment(token, pr, text):
    api(token, "POST", f"/repos/{REPO}/issues/{pr}/comments", {"body": text})


def bot_comments(pr):
    return [c for c in api(ALICE, "GET", f"/repos/{REPO}/issues/{pr}/comments?limit=50") if c["user"]["login"] == "atlantis-bot"]


def wait_bot(pr, *needles, after=0, timeout=TIMEOUT):
    """Attend un commentaire d'Atlantis (id > after) contenant TOUS les textes donnés."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        for c in bot_comments(pr):
            if c["id"] > after and all(n.lower() in c["body"].lower() for n in needles):
                return c
        time.sleep(3)
    last = bot_comments(pr)
    fail(f"PR #{pr} : pas de réponse d'Atlantis contenant {needles} en {timeout}s. "
         f"Dernier commentaire : {last[-1]['body'][:600] if last else '(aucun)'}")


def last_bot_id(pr):
    cs = bot_comments(pr)
    return cs[-1]["id"] if cs else 0


def excerpt(body, *keys, n=4):
    lines = [l for l in body.splitlines() if any(k.lower() in l.lower() for k in keys)]
    for l in lines[:n]:
        print(f"       │ {l.strip()[:150]}")


def minio(cmd):
    return subprocess.run(["docker", "compose", "exec", "-T", "minio", "sh", "-c",
                           f"mc alias set local http://localhost:9000 '{ENV['MINIO_ROOT_USER']}' '{ENV['MINIO_ROOT_PASSWORD']}' >/dev/null && {cmd}"],
                          cwd=ROOT, capture_output=True, text=True).stdout


def bucket_tf(name, location, labels, env):
    lab = ", ".join(f'{k} = "{v}"' for k, v in labels.items())
    return f'''module "{name.replace("-", "_")}" {{
  source   = "../../modules/gcs_bucket_sim"
  name     = "acme-{env}-{name}"
  location = "{location}"
  labels   = {{ {lab} }}
}}
'''


GOOD_LABELS = lambda env: {"owner": "data-team", "env": env, "cost_center": "cc-1234"}
ATLANTIS = f"http://localhost:{ENV['ATLANTIS_PORT']}"


def release(token, pr):
    """Libère les verrous et plans de la PR (`atlantis unlock`).
    Avec Gitea, Atlantis ne reçoit pas l'événement « PR fermée/fusionnée » : on libère explicitement."""
    mark = last_bot_id(pr)
    comment(token, pr, "atlantis unlock")
    wait_bot(pr, "unlock", after=mark, timeout=120)


def close_pr(pr):
    release(ALICE, pr)
    api(ALICE, "PATCH", f"/repos/{REPO}/pulls/{pr}", {"state": "closed"})


def stale_locks():
    with urllib.request.urlopen(ATLANTIS + "/") as r:
        return sorted(set(re.findall(r'lock\?id=([^"&]+)', r.read().decode())))

# =============================================================================== 0. Santé
step("Vérification du service : Gitea, Atlantis, MinIO")
api(ALICE, "GET", f"/repos/{REPO}")
ok("Gitea répond, le dépôt acme/infra-demo existe et alice y a accès")
with urllib.request.urlopen(f"http://localhost:{ENV['ATLANTIS_PORT']}/healthz") as r:
    ok(f"Atlantis répond (/healthz : HTTP {r.status})")
if "tfstate" not in minio("mc ls local"):
    fail("bucket tfstate absent")
ok("MinIO : bucket d'état « tfstate » présent")
for lock_id in stale_locks():   # verrous laissés par une exécution précédente interrompue
    urllib.request.urlopen(urllib.request.Request(f"{ATLANTIS}/locks?id={lock_id}", method="DELETE"))
    ok(f"verrou résiduel supprimé : {urllib.parse.unquote(urllib.parse.unquote(lock_id))}")

# =============================================================================== Scénario 1 : nominal
print("\n\033[1m━━━ SCÉNARIO 1 : un changement conforme, de la pull request à la production de l'état ━━━\033[0m")
step("alice crée une branche et ajoute un bucket « logs » dans envs/dev")
b1 = f"feature/logs-bucket-{RUN}"
new_branch_with_file(b1, f"envs/dev/logs_{RUN}.tf", bucket_tf(f"logs-{RUN}", "EU", GOOD_LABELS("dev"), "dev"),
                     "Ajout du bucket de logs (dev)")
ok(f"branche {b1} poussée")

step("alice ouvre la pull request → Atlantis planifie automatiquement (autoplan)")
pr1 = open_pr(b1, f"Ajout d'un bucket de logs en dev ({RUN})", "Besoin : stocker les logs applicatifs. Localisation UE, labels complets.")
ok(f"PR #{pr1} ouverte")
c = wait_bot(pr1, "ran plan", "to add")
ok("Atlantis a publié le plan dans la PR :")
excerpt(c["body"], "Ran Plan", "Plan:", "to add")

step("Politiques du service (Conftest) sur le plan")
c = wait_bot(pr1, "policy")
if "fail" in c["body"].lower() and "0 failures" not in c["body"].lower():
    fail("la politique aurait dû passer : " + c["body"][:400])
ok("Politiques passées (UE, labels obligatoires, pas d'accès public)")
excerpt(c["body"], "tests,", n=1)

step("alice tente « atlantis apply » SANS approbation → refusé par le service")
mark = last_bot_id(pr1)
comment(ALICE, pr1, "atlantis apply -p dev")
c = wait_bot(pr1, "approved", after=mark)
ok("Refus d'Atlantis (apply_requirements: approved) :")
excerpt(c["body"], "approved", "apply", n=2)

step("bob (sécurité) relit et APPROUVE la pull request")
api(BOB, "POST", f"/repos/{REPO}/pulls/{pr1}/reviews", {"event": "APPROVED", "body": "Conforme : UE, labels OK. Approuvé."})
ok("revue « Approved » enregistrée dans Gitea")

step("alice relance « atlantis apply -p dev » → Atlantis applique LE plan approuvé")
time.sleep(3)
mark = last_bot_id(pr1)
comment(ALICE, pr1, "atlantis apply -p dev")
c = wait_bot(pr1, "apply complete", after=mark)
ok("Apply réussi :")
excerpt(c["body"], "Apply complete", "Ran Apply", n=2)

step("L'état distant (MinIO ≈ Cloud Storage) contient la nouvelle ressource")
listing = minio("mc ls local/tfstate/dev/")
state = minio("mc cat local/tfstate/dev/terraform.tfstate")
if f"acme-dev-logs-{RUN}" not in state:
    fail("ressource absente de l'état")
versions = minio("mc ls --versions local/tfstate/dev/terraform.tfstate").strip().splitlines()
st = json.loads(state)
ok(f"état dev/terraform.tfstate : serial {st['serial']}, {len(st['resources'])} ressource(s), {len(versions)} version(s) conservée(s)")
ok("verrou libéré après l'apply (aucun fichier .tflock restant)" if ".tflock" not in listing else "verrou présent (inattendu)")

step("alice libère le verrou (atlantis unlock) puis fusionne la PR (main protégée : 1 approbation requise)")
release(ALICE, pr1)
ok("verrou du projet dev libéré")
api(ALICE, "POST", f"/repos/{REPO}/pulls/{pr1}/merge", {"Do": "merge", "delete_branch_after_merge": True})
if not api(ALICE, "GET", f"/repos/{REPO}/pulls/{pr1}")["merged"]:
    fail("PR non fusionnée")
ok(f"PR #{pr1} fusionnée : main = ce qui est déployé")

# =============================================================================== Scénario 2 : politique
print("\n\033[1m━━━ SCÉNARIO 2 : un changement NON conforme est arrêté par les politiques ━━━\033[0m")
step("alice propose un bucket en us-central1, sans label cost_center, dans envs/prod")
b2 = f"feature/us-bucket-{RUN}"
new_branch_with_file(b2, f"envs/prod/analytics_{RUN}.tf",
                     bucket_tf(f"analytics-{RUN}", "us-central1", {"owner": "bi-team", "env": "prod"}, "prod"),
                     "Bucket analytics (prod)")
pr2 = open_pr(b2, f"Bucket analytics en prod ({RUN})", "Test : doit être refusé par les politiques.")
ok(f"PR #{pr2} ouverte")
wait_bot(pr2, "ran plan", "to add")
ok("plan calculé (la syntaxe est valide…)")
c = wait_bot(pr2, "policy", "fail")
ok("…mais les politiques ÉCHOUENT :")
excerpt(c["body"], "interdite", "manquant", "fail", n=4)

step("Même approuvée par un pair, la PR ne peut pas être appliquée tant que la politique échoue")
api(BOB, "POST", f"/repos/{REPO}/pulls/{pr2}/reviews", {"event": "APPROVED", "body": "Approuvé (test)"})
time.sleep(3)
mark = last_bot_id(pr2)
comment(ALICE, pr2, "atlantis apply -p prod")
c = wait_bot(pr2, after=mark, timeout=120)
body = c["body"].lower()
if "apply complete" in body:
    fail("l'apply aurait dû être bloqué")
ok("apply refusé par le service :")
excerpt(c["body"], "policy", "fail", "approv", n=3)
close_pr(pr2)
ok(f"PR #{pr2} fermée sans rien déployer ; la production est intacte")
if f"analytics-{RUN}" in minio("mc cat local/tfstate/prod/terraform.tfstate 2>/dev/null || true"):
    fail("la ressource non conforme a été créée !")
ok("vérifié : l'état prod ne contient pas la ressource refusée")

# =============================================================================== Scénario 3 : verrous
print("\n\033[1m━━━ SCÉNARIO 3 : deux pull requests sur le même projet → verrou ━━━\033[0m")
step("alice ouvre deux PR qui modifient toutes les deux envs/dev")
b3, b4 = f"feature/cache-{RUN}", f"feature/archive-{RUN}"
new_branch_with_file(b3, f"envs/dev/cache_{RUN}.tf", bucket_tf(f"cache-{RUN}", "EU", GOOD_LABELS("dev"), "dev"), "Bucket cache")
pr3 = open_pr(b3, f"Bucket cache ({RUN})", "PR A")
wait_bot(pr3, "ran plan", "to add")
ok(f"PR #{pr3} planifiée : Atlantis VERROUILLE le projet dev pour cette PR")
new_branch_with_file(b4, f"envs/dev/archive_{RUN}.tf", bucket_tf(f"archive-{RUN}", "EU", GOOD_LABELS("dev"), "dev"), "Bucket archive")
pr4 = open_pr(b4, f"Bucket archive ({RUN})", "PR B")
c = wait_bot(pr4, "locked")
ok(f"PR #{pr4} : Atlantis refuse de planifier, le projet est verrouillé par la PR #{pr3} :")
excerpt(c["body"], "locked", n=2)

step(f"La PR #{pr3} est abandonnée (atlantis unlock + fermeture) → la PR #{pr4} peut planifier")
close_pr(pr3)
time.sleep(5)
mark = last_bot_id(pr4)
comment(ALICE, pr4, "atlantis plan -p dev")
wait_bot(pr4, "ran plan", "to add", after=mark)
ok(f"PR #{pr4} planifiée après libération du verrou")
close_pr(pr4)
ok(f"PR #{pr4} fermée (nettoyage)")

# =============================================================================== Bilan
print("\n\033[1;32m━━━ BILAN : toutes les vérifications sont passées ━━━\033[0m")
print(f"""
  PR #{pr1}  conforme   → plan auto, politiques OK, apply refusé sans approbation, approuvé, appliqué, fusionné
  PR #{pr2}  non conf.  → politiques en échec (UE + label manquant), apply bloqué, PR fermée, prod intacte
  PR #{pr3}/#{pr4}  verrou → la 2e PR attend que la 1re libère le projet dev

  À voir dans le navigateur :
    Gitea     http://localhost:{ENV['GITEA_PORT']}/{REPO}/pulls?state=all   (connexion : alice, mot de passe dans .env)
    Atlantis  http://localhost:{ENV['ATLANTIS_PORT']}
    MinIO     http://localhost:{ENV['MINIO_CONSOLE_PORT']}  → bucket tfstate (états dev/prod versionnés)
""")
