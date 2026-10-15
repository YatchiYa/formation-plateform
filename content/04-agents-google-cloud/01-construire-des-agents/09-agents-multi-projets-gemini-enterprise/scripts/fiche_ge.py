"""Fiche d'un agent : TOUT ce qu'il faut saisir dans la console Gemini Enterprise pour l'ajouter (docs/12-1-8).

À QUOI SERT CE SCRIPT
  Lancé par « ./scripts/deployer_shell.sh carte <clé> » (pas à la main, en général). Affiche, pour un agent déployé :
  le nom, la description, la carte A2A (Cloud Run) ou le chemin Agent Runtime, l'étape Authentification (OAuth),
  les questions proposées, et les droits de l'app. Ne crée et n'appelle RIEN chez Google : il affiche.

UTILISATION
  python3 scripts/fiche_ge.py CLE [--a2a URL --carte carte-CLE.json] [--runtime RESSOURCE] [--auth IDS]
  Variables lues (facultatives) : CLIENT_ID (ID du client OAuth : l'URL d'autorisation est alors complète),
  GE_SA (compte de l'app, calculé par config.sh quand NUM_APP est rempli), PROJET_AGENTS.
"""
import argparse
import json
import os
import urllib.parse
from pathlib import Path

REDIRECT = "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html"
CLOUD = "https://www.googleapis.com/auth/cloud-platform"

p = argparse.ArgumentParser()
p.add_argument("cle")
p.add_argument("--a2a", default="")
p.add_argument("--carte", default="")
p.add_argument("--runtime", default="")
p.add_argument("--auth", default="")
o = p.parse_args()
a = json.loads((Path(__file__).resolve().parent.parent / "agents" / "trio" / "catalogue.json").read_text())[o.cle]
portees = a.get("oauth", {}).get("portees", [])
ids = [i for i in o.auth.split(",") if i]
client = os.getenv("CLIENT_ID", "")


def url_google(scopes: list[str]) -> str:
    if not client:
        return "(relancer avec CLIENT_ID=<ID du client OAuth> devant la commande : l'URL complète s'affiche ici)"
    return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode({
        "client_id": client, "redirect_uri": REDIRECT, "scope": " ".join(scopes), "include_granted_scopes": "true",
        "response_type": "code", "access_type": "offline", "prompt": "consent"}, quote_via=urllib.parse.quote)


def autorisation(auth_id: str, scopes: list[str]) -> None:
    if "atlassian" in auth_id:
        print(f"      [{auth_id}] Atlassian : champs de docs/12-1-8, partie 6.1 (Client ID/secret Atlassian, "
              "URL https://auth.atlassian.com/authorize?…, Token URL https://auth.atlassian.com/oauth/token)")
        return
    print(f"      Nom de l'autorisation  : {auth_id}")
    print("      Client ID / secret     : ceux du client OAuth (Google Auth Platform → Clients)")
    print(f"      Authorization URL      : {url_google(scopes)}")
    print("      Token URL              : https://oauth2.googleapis.com/token")
    print(f"      Scopes                 : {' '.join(scopes)}")
    print("      PKCE / HTTP Basic      : décochés")


print(f"\n================ {o.cle} : {a['nom_affiche']} ================")
print(f"Description (à coller) : {a['description']}")
if o.a2a:
    print(f"\n[A2A sur Cloud Run]  {o.a2a}")
    print("  Console : Gemini Enterprise → l'app → Agents → + Add agent → Custom agent via A2A")
    print(f"  1. Carte (fichier {o.carte}), TOUTE la ligne ci-dessous, du 1er {{ au dernier }} :")
    print("     " + Path(o.carte).read_text().strip())
    print(f"  2. Nom : {a['nom_affiche']} (A2A)")
    if not ids:
        print("  3. Authentication : Skip & Finish (agent sans OAuth)")
    else:
        if len(ids) > 1:
            print(f"  ⚠ A2A = UNE autorisation : seule « {ids[0]} » sera utilisée (plusieurs : Agent Runtime, docs/12-1-8)")
        print("  3. Authentication (ne PAS cliquer Skip) :")
        autorisation(ids[0], portees)
if o.runtime:
    print(f"\n[Agent Runtime]  {o.runtime}")
    print("  Console : Gemini Enterprise → l'app → Agents → + Add agent → Custom agent via Agent Runtime")
    if not ids:
        print("  1. Authorizations : rien → Next")
    else:
        print("  1. Authorizations → Add authorization (une par ID ; le nom doit être IDENTIQUE) :")
        for i in ids:
            autorisation(i, portees + [CLOUD])
    print(f"  2. Agent name : {a['nom_affiche']}")
    print("  3. Description : celle du haut")
    print(f"  4. Agent Runtime resource path : {o.runtime}")
if not (o.a2a or o.runtime):
    print("\nPas encore déployé : ./scripts/deployer_shell.sh cloudrun|runtime " + o.cle)
exemples = [e for c in a["competences"] for e in c.get("examples", [])]
print("\nQuestions proposées (starter prompts) : " + " | ".join(exemples))
print("  (en un clic : scripts/personnaliser_agent.sh, docs/12-1-8 partie 12)")
if (o.a2a or o.runtime) and os.getenv("GE_SA"):
    sa, projet = os.environ["GE_SA"], os.getenv("PROJET_AGENTS", "<projet des agents>")
    print(f"\nDroits de l'app (compte {sa}) :")
    if o.a2a:
        print(f"  ① roles/run.invoker sur le service {o.cle}-a2a-shell (Cloud Run → service → Sécurité)")
    if o.runtime:
        print(f"  ② roles/discoveryengine.serviceAgent sur le projet {projet} (IAM), une fois pour tous")
    print("  Script : ./scripts/connecter_app.sh droits " + o.cle)
elif o.a2a or o.runtime:
    print("\nDroits de l'app : ① run.invoker (Cloud Run), ② discoveryengine.serviceAgent (projet) → docs/12-1-4 partie 3")
