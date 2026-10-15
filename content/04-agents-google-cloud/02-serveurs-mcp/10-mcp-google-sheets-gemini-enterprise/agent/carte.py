"""La carte A2A de l'agent, au format attendu par Gemini Enterprise (A2A 0.3, JSON-RPC).

  python agent/carte.py https://sheets-agent-<NUM>.<REGION>.run.app > carte-sheets-agent.json

C'est CETTE carte qu'on colle dans Gemini Enterprise (Custom agent via A2A), pas celle de /.well-known/agent-card.json,
qui a des champs en plus que la console refuse (vu au projet 09). main.py sert la même (variable AGENT_CARD).
"""
import json
import sys

NOM = "Assistant Google Sheets"
DESCRIPTION = ("Lit et modifie les Google Sheets (et les Google Slides) de l'utilisateur connecté : recherche, lecture, "
               "écriture, formules, mise en forme, onglets, diapositives, et toute l'API (serveurs MCP), avec ses propres droits.")
COMPETENCES = [
    {"id": "lire", "name": "Trouver et lire", "description": "Rechercher un classeur, lister ses onglets, lire et chercher des valeurs.",
     "tags": ["sheets", "lecture"], "examples": ["Trouve le classeur Ventes 2026 et résume l'onglet Ventes."]},
    {"id": "modifier", "name": "Modifier", "description": "Écrire, ajouter des lignes, formules, mise en forme, onglets, tri, batchUpdate.",
     "tags": ["sheets", "écriture"], "examples": ["Ajoute la ligne Sac à dos, 39 € dans l'onglet Ventes, puis trie par prix."]},
    {"id": "slides", "name": "Présentations Google Slides", "description": "Lire, créer et modifier des présentations (si le serveur Slides est branché).",
     "tags": ["slides", "présentation"], "examples": ["Fais une présentation de 3 diapositives à partir du classeur Ventes 2026."]},
]


def carte(url: str) -> dict:
    return {"protocolVersion": "0.3", "name": "sheets_agent", "description": DESCRIPTION, "url": url.rstrip("/"),
            "preferredTransport": "JSONRPC", "version": "1.0.0", "capabilities": {"streaming": True},
            "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain"], "skills": COMPETENCES}


if __name__ == "__main__":
    if sys.argv[1:] == ["--terraform"]:   # source « external » de Terraform : {"url": …} -> {"carte": "<JSON>"}
        print(json.dumps({"carte": json.dumps(carte(json.load(sys.stdin)["url"]), ensure_ascii=False)}))
    else:
        print(json.dumps(carte(sys.argv[1]), ensure_ascii=False))
