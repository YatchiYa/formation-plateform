"""Vérifie, en LECTURE SEULE, la posture d'un projet qui héberge une plateforme IA.

Contrôles : API attendues activées, rôles primitifs (owner/editor), accès publics,
compte Compute par défaut trop puissant, clés de comptes de service téléchargées,
journaux d'audit « accès aux données » sur Vertex AI.

Usage :
    gcloud auth application-default login
    python check_posture.py --project mon-projet [--json]

Permissions nécessaires (lecture) : roles/iam.securityReviewer + roles/serviceusage.serviceUsageViewer.
"""
import argparse
import json
import os
import sys

EXPECTED_APIS = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "cloudkms.googleapis.com",
    "logging.googleapis.com",
    "iap.googleapis.com",
    "modelarmor.googleapis.com",
    "accesscontextmanager.googleapis.com",
]
PRIMITIVE = {"roles/owner", "roles/editor"}
PUBLIC = {"allUsers", "allAuthenticatedUsers"}


def mask(member: str) -> str:
    """user:alice@exemple.fr -> user:al***@exemple.fr (les rapports circulent)."""
    kind, _, email = member.partition(":")
    if "@" not in email:
        return member
    local, _, domain = email.partition("@")
    return f"{kind}:{local[:2]}***@{domain}"


def evaluate(project_number: str, enabled: set, policy: dict, keys: dict) -> list:
    """Fonction pure : renvoie une liste (niveau, contrôle, détail). Niveaux : OK, WARN, FAIL."""
    out = []
    missing = [a for a in EXPECTED_APIS if a not in enabled]
    out.append(("OK" if not missing else "WARN", "API attendues",
                "toutes activées" if not missing else "manquantes : " + ", ".join(missing)))

    bindings = policy.get("bindings", [])
    default_sa = f"serviceAccount:{project_number}-compute@developer.gserviceaccount.com"
    public, sa_primitive, humans_primitive, default_sa_roles = [], [], [], []
    for b in bindings:
        for m in b.get("members", []):
            if m in PUBLIC:
                public.append(f"{m} -> {b['role']}")
            if m == default_sa:
                default_sa_roles.append(b["role"])
            if b["role"] in PRIMITIVE:
                (sa_primitive if m.startswith("serviceAccount:") else humans_primitive).append(m)

    out.append(("FAIL" if public else "OK", "Accès public (allUsers)",
                "; ".join(public) or "aucun"))
    bad_default = sorted(set(default_sa_roles) & PRIMITIVE)
    out.append(("FAIL" if bad_default else "OK", "Compte Compute par défaut",
                "a " + ", ".join(bad_default) if bad_default else "pas de rôle primitif"))
    others = [m for m in sa_primitive if m != default_sa]
    out.append(("WARN" if others else "OK", "Comptes de service owner/editor",
                f"{len(others)} : " + ", ".join(mask(m) for m in sorted(set(others))) if others else "aucun"))
    humans = sorted(set(humans_primitive))
    out.append(("WARN" if len(humans) > 3 else "OK", "Humains owner/editor",
                f"{len(humans)} (cible : 3 au plus, idéalement via un groupe)"))

    with_keys = {sa: n for sa, n in keys.items() if n}
    out.append(("WARN" if with_keys else "OK", "Clés de comptes de service",
                ", ".join(f"{mask('sa:' + sa)} ({n})" for sa, n in sorted(with_keys.items())) or "aucune clé utilisateur"))

    audit = {c.get("service"): {x.get("logType") for x in c.get("auditLogConfigs", [])}
             for c in policy.get("auditConfigs", [])}
    covered = audit.get("aiplatform.googleapis.com", set()) | audit.get("allServices", set())
    need = {"DATA_READ", "DATA_WRITE"}
    out.append(("OK" if need <= covered else "WARN", "Audit accès aux données Vertex AI",
                "actif" if need <= covered else "manque " + ", ".join(sorted(need - covered))))
    return out


def fetch(project: str):
    """Appels REST en lecture seule (aucune méthode d'écriture n'est utilisée)."""
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    s = AuthorizedSession(creds)

    def get(url, **params):
        r = s.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    number = get(f"https://cloudresourcemanager.googleapis.com/v1/projects/{project}")["projectNumber"]

    enabled, token = set(), None
    while True:
        page = get(f"https://serviceusage.googleapis.com/v1/projects/{project}/services",
                   filter="state:ENABLED", pageSize=200, **({"pageToken": token} if token else {}))
        enabled |= {x["config"]["name"] for x in page.get("services", [])}
        token = page.get("nextPageToken")
        if not token:
            break

    # getIamPolicy est un POST, mais c'est une lecture (permission resourcemanager.projects.getIamPolicy).
    r = s.post(f"https://cloudresourcemanager.googleapis.com/v3/projects/{project}:getIamPolicy",
               json={"options": {"requestedPolicyVersion": 3}}, timeout=30)
    r.raise_for_status()
    policy = r.json()

    keys = {}
    for sa in get(f"https://iam.googleapis.com/v1/projects/{project}/serviceAccounts",
                  pageSize=100).get("accounts", []):
        k = get(f"https://iam.googleapis.com/v1/{sa['name']}/keys", keyTypes="USER_MANAGED")
        keys[sa["email"]] = len(k.get("keys", []))
    return number, enabled, policy, keys


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    if not a.project:
        sys.exit("Indiquez --project ou GOOGLE_CLOUD_PROJECT.")

    results = evaluate(*fetch(a.project))
    if a.json:
        print(json.dumps([dict(zip(("niveau", "controle", "detail"), r)) for r in results],
                         ensure_ascii=False, indent=2))
    else:
        for level, name, detail in results:
            print(f"[{level:4}] {name:36} {detail}")
    fails = sum(r[0] == "FAIL" for r in results)
    warns = sum(r[0] == "WARN" for r in results)
    print(f"\n{len(results)} contrôles : {fails} FAIL, {warns} WARN")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
