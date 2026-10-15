"""Agent Identité utilisateur : l'utilisateur est-il authentifié (OAuth via Gemini Enterprise), avec quel compte ?

Un outil : qui_suis_je. Il lit le jeton OAuth que Gemini Enterprise transmet (commun.jeton_utilisateur) et demande à
Google à qui il appartient (tokeninfo) : compte, domaine (ex. acme.example), portées accordées, durée restante.
Le jeton lui-même n'est jamais affiché ni renvoyé au modèle.

Sert à vérifier la chaîne OAuth de bout en bout avant de brancher de vrais outils (docs/12-3, partie C).
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun


def qui_suis_je(tool_context) -> dict:
    """Dit si l'utilisateur est authentifié auprès de Gemini Enterprise, avec quel compte et quels droits."""
    jeton = commun.jeton_utilisateur(tool_context)
    if not os.getenv("AUTH_ID"):
        return {"status": "success", "authentifie": False,
                "raison": "agent déployé sans autorisation OAuth (AUTH_ID absent) : voir docs/12-3, partie C"}
    if not jeton:
        return {"status": "success", "authentifie": False,
                "raison": "aucun jeton reçu : l'utilisateur n'a pas encore cliqué sur « Autoriser », ou l'agent "
                          "n'est pas appelé depuis Gemini Enterprise"}
    try:
        url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"access_token": jeton})
        info = json.load(urllib.request.urlopen(url, timeout=10))
    except urllib.error.HTTPError:
        # Jeton expiré, révoqué, ou émis par un autre fournisseur (Jira, Salesforce…) : Google ne peut pas le lire.
        return {"status": "success", "authentifie": True, "verifie_par_google": False,
                "raison": "jeton reçu, mais Google ne le reconnaît pas (expiré, ou d'un autre fournisseur OAuth)"}
    email = info.get("email", "")
    return {"status": "success", "authentifie": True, "verifie_par_google": True,
            "compte": email or "(portée « email » non accordée)",
            "domaine": email.split("@")[-1] if email else "",
            "portees": info.get("scope", "").split(),
            "expire_dans_secondes": int(info.get("expires_in", 0)),
            "autorisation": os.environ["AUTH_ID"]}


root_agent = Agent(
    name="identite_agent",
    model=commun.modele(),
    description="Dit si l'utilisateur est authentifié auprès de Gemini Enterprise, avec quel compte et quels droits.",
    instruction=(
        "Appelle toujours qui_suis_je. Réponds en français, en 5 lignes maximum : authentifié ou non ; si oui, le "
        "compte, le domaine, les portées en clair (ex. « email », « cloud-platform »), et la durée restante en minutes ; "
        "si non, la raison et quoi faire. N'invente jamais un compte."
    ),
    tools=[qui_suis_je],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
