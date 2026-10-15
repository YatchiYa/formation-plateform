"""La fiche : TOUT ce qu'il faut saisir dans la console Gemini Enterprise, pour chaque modalité. Lancé par
« ./scripts/deployer.sh fiche » (lit la configuration chargée). N'appelle rien chez Google : il affiche.
"""
import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
from carte import NOM, DESCRIPTION, COMPETENCES, carte  # noqa: E402

p = argparse.ArgumentParser()
for o in ("--a2a", "--runtime", "--auth-a2a", "--auth-runtime"):
    p.add_argument(o, default="")
p.add_argument("--slides", action="store_true", help="le serveur MCP Slides est déployé")
p.add_argument("--sheets", action="store_true", help="le serveur MCP Sheets est déployé")
a = p.parse_args()
e = os.environ
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.metadata.readonly"]
SCOPE_SLIDES = "https://www.googleapis.com/auth/presentations"
SCOPES_AGENT = (SCOPES if a.sheets else SCOPES[:2] + SCOPES[3:]) + ([SCOPE_SLIDES] if a.slides else [])   # l'agent utilise aussi Slides si le serveur existe
clients = [c.strip() for c in e.get("OAUTH_CLIENT_IDS", "").split(",") if c.strip().endswith(".apps.googleusercontent.com")]
client = clients[0] if clients else "<ID du client OAuth (docs/10-5, étape 1)>"
domaine = e["ALLOWED_DOMAINS"].split(",")[0].strip()
mcp_host = urllib.parse.urlparse(e["MCP_URL"]).hostname


def url_auth(scopes):
    return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode({
        "client_id": client, "redirect_uri": "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html",
        "scope": " ".join(scopes), "hd": domaine, "include_granted_scopes": "true", "response_type": "code",
        "access_type": "offline", "prompt": "consent"}, quote_via=urllib.parse.quote)


def autorisation(nom, scopes):
    print(f"     Nom de l'autorisation : {nom}")
    print(f"     Client ID / secret    : {client} / (le secret, depuis Google Auth Platform → Clients)")
    print(f"     Authorization URL     : {url_auth(scopes)}")
    print("     Token URL             : https://oauth2.googleapis.com/token")
    print(f"     Scopes                : {' '.join(scopes)}")
    print("     PKCE / HTTP Basic     : décochés")


MODALITE_1 = f"""
================ Modalité 1 : connecteur natif « Custom MCP Server » (docs/10-5) ================
Console : Gemini Enterprise → l'app → section « MCP servers » → carte « Custom MCP Server » → Add MCP server
     (MCP Server URL : AVEC /mcp, même si l'aide de l'écran dit « base URL »)
     Authentication        : OAuth 2.0
     MCP Server URL        : {e['MCP_URL']}
     Authorization URL     : https://accounts.google.com/o/oauth2/v2/auth
     Auth URL parameters   : &access_type=offline&prompt=consent&hd={domaine}
     Token URL             : https://oauth2.googleapis.com/token
     Client ID / secret    : {client} / (le secret)
     Enable PKCE Support   : COCHER (décoché par défaut)
     Use HTTP Basic Auth.  : laisser coché (par défaut ; Google accepte les deux)
     Scopes                : {' '.join(SCOPES)}
     → Verify Auth → Continue → Multi-region : {e.get('GE_LOCATION', 'eu')} → nom : Google Sheets → Create
     → Actions → Reload custom actions → activer (lecture d'abord) → l'app → Connected data stores : ajouter
Politiques d'organisation (admin) : domaines de sortie autorisés = {mcp_host}, accounts.google.com, oauth2.googleapis.com
Droit ① : roles/run.invoker sur sheets-mcp pour {e.get('GE_SA') or 'service-<NUM_APP>@gcp-sa-discoveryengine.iam.gserviceaccount.com'}
"""
if a.sheets:
    print(MODALITE_1)
else:
    print("\n(sheets-mcp pas déployé : ./scripts/deployer.sh mcp sheets)\n")

if a.slides:
    hote = urllib.parse.urlparse(e["SLIDES_URL"]).hostname
    print(f"""================ Modalité 1 bis : connecteur natif Google SLIDES (docs/10-13) ================
Même écran que la modalité 1, un 2e connecteur « Custom MCP Server » :
     MCP Server URL        : {e['SLIDES_URL']}
     Authorization URL     : https://accounts.google.com/o/oauth2/v2/auth
     Auth URL parameters   : &access_type=offline&prompt=consent&hd={domaine}
     Token URL             : https://oauth2.googleapis.com/token
     Client ID / secret    : {client} / (le même client OAuth que pour Sheets)
     Enable PKCE Support   : COCHER ;  Use HTTP Basic Auth. : laisser coché
     Scopes                : openid https://www.googleapis.com/auth/userinfo.email {SCOPE_SLIDES} https://www.googleapis.com/auth/drive.metadata.readonly
     → nom du data connector : Google Slides
Domaine de sortie en plus : {hote}
Droit ① : roles/run.invoker sur slides-mcp pour le compte de l'app
""")
print("================ Modalité 2 : agent A2A sur Cloud Run (docs/10-6) ================")
if a.a2a:
    print("Console : Agents → + Add agent → Custom agent via A2A")
    print("  1. Carte, TOUTE la ligne :\n     " + json.dumps(carte(a.a2a), ensure_ascii=False))
    print(f"  2. Nom : {NOM} (A2A)")
    print("  3. Authentication (ne PAS cliquer Skip) :")
    autorisation(a.auth_a2a, SCOPES_AGENT)
    print("  Droit ① : roles/run.invoker sur sheets-agent pour le compte de l'app (./scripts/deployer.sh droits-app)")
else:
    print("  (pas encore déployé : ./scripts/deployer.sh agent)")
print("\n================ Modalité 3 : agent sur Agent Runtime (docs/10-6) ================")
if a.runtime:
    print("Console : Agents → + Add agent → Custom agent via Agent Runtime")
    print("  1. Authorizations → Add authorization (nom IDENTIQUE) :")
    autorisation(a.auth_runtime, SCOPES_AGENT + ["https://www.googleapis.com/auth/cloud-platform"])
    print(f"  2. Agent name : {NOM}\n  3. Description : {DESCRIPTION}\n  4. Agent Runtime resource path : {a.runtime}")
    print("  Droit ② : roles/discoveryengine.serviceAgent sur le projet pour le compte de l'app")
else:
    print("  (pas encore déployé : ./scripts/deployer.sh agent-runtime)")
print("\nQuestions proposées : " + " | ".join(x for c in COMPETENCES for x in c["examples"]))
