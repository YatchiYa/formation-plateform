"""Assistant RH : boucle de function calling MANUELLE avec google-genai.

Usage :  python assistant.py --utilisateur E004
(l'API RH doit tourner : uvicorn api_rh:app --port 8077)
"""
import argparse
import json
import os
import time
from datetime import date, datetime, timezone

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import outils_rh

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
AUDIT_PATH = os.environ.get("AUDIT_PATH", "audit.jsonl")
MAX_TOURS = 6

SYSTEME = """Tu es l'assistant RH interne. Tu réponds en français, brièvement.
L'utilisateur connecté a l'identifiant {utilisateur}. Nous sommes le {aujourdhui}.
Règles :
- Pour tout solde, demande ou employé, appelle un outil : n'invente jamais un chiffre.
- Si l'utilisateur donne un nom, appelle d'abord chercher_employe.
- Lance en parallèle les appels indépendants.
- Si un outil renvoie "erreur", explique-la simplement sans réessayer à l'aveugle."""


# --- Journal d'audit : une ligne JSON par appel d'outil ----------------------
def journaliser(**evenement):
    evenement = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), **evenement}
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(evenement, ensure_ascii=False) + "\n")


# --- Appel au modèle avec réessais sur 429 / 503 ------------------------------
def generer(client, contents, config, essais=4):
    for i in range(essais):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=config)
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == essais - 1:
                raise
            time.sleep(2 ** i * 2)  # 2 s, 4 s, 8 s


# --- Exécution d'UN appel demandé par le modèle --------------------------------
def executer(fc, utilisateur, confirmer) -> dict:
    base = {"utilisateur": utilisateur, "outil": fc.name, "args": dict(fc.args or {})}
    try:
        args = outils_rh.valider(fc.name, fc.args)
    except ValueError as e:
        journaliser(**base, statut="refuse_validation", detail=str(e))
        return {"erreur": f"Arguments invalides : {e}"}
    if fc.name in outils_rh.SENSIBLES and not confirmer(fc.name, args):
        journaliser(**base, statut="refuse_utilisateur")
        return {"erreur": "Action annulée : l'utilisateur n'a pas confirmé."}
    t0 = time.perf_counter()
    resultat = outils_rh.OUTILS[fc.name](utilisateur, **args)
    journaliser(**base, statut="erreur" if "erreur" in resultat else "ok",
                duree_ms=round((time.perf_counter() - t0) * 1000), resultat=resultat)
    return resultat


def repondre(client, historique, question, utilisateur, confirmer, mode="AUTO",
             afficher=print) -> str:
    """Ajoute la question à l'historique, fait tourner la boucle, renvoie la réponse."""
    historique.append(types.Content(role="user", parts=[types.Part(text=question)]))
    for tour in range(MAX_TOURS):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEME.format(utilisateur=utilisateur,
                                              aujourdhui=date.today().isoformat()),
            tools=[types.Tool(function_declarations=outils_rh.DECLARATIONS)],
            # ANY seulement au 1er tour : sinon le modèle ne pourrait jamais conclure.
            tool_config=types.ToolConfig(function_calling_config=types.FunctionCallingConfig(
                mode=mode if tour == 0 else "AUTO")),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        reponse = generer(client, historique, config)
        historique.append(reponse.candidates[0].content)  # garde les thought signatures
        appels = reponse.function_calls or []
        if not appels:
            return reponse.text or ""
        afficher(f"  [tour {tour + 1}] {len(appels)} appel(s) : "
                 + ", ".join(f"{fc.name}({json.dumps(dict(fc.args or {}), ensure_ascii=False)})"
                             for fc in appels))
        parts = [types.Part(function_response=types.FunctionResponse(
                     id=fc.id, name=fc.name, response=executer(fc, utilisateur, confirmer)))
                 for fc in appels]
        historique.append(types.Content(role="user", parts=parts))
    return "Je n'ai pas pu terminer en un nombre raisonnable d'étapes. Un humain RH va reprendre."


def confirmer_console(nom, args):
    return input(f"  ⚠ Confirmer {nom} {args} ? (oui/non) ").strip().lower() == "oui"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--utilisateur", default="E004", help="identifiant de la session (ex. E004)")
    a = p.parse_args()
    client, historique = genai.Client(), []
    print(f"Assistant RH ({MODEL}) - connecté en tant que {a.utilisateur}. Ctrl+C pour quitter.")
    while True:
        print("Assistant :", repondre(client, historique, input("Vous : "), a.utilisateur,
                                      confirmer_console))
