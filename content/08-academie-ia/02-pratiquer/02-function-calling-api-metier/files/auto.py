"""Le même assistant en mode AUTOMATIQUE : le SDK exécute lui-même les fonctions Python.

Pratique pour prototyper, mais pas de point d'arrêt pour confirmer, valider ou auditer.
Usage :  python auto.py "Combien de RTT reste-t-il à E001 ?"
"""
import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import types

import outils_rh

load_dotenv()
UTILISATEUR = "E004"  # en vrai : l'identité de la session, jamais un argument du modèle


def chercher_employe(nom: str) -> dict:
    """Cherche un employé par nom dans l'annuaire et renvoie son identifiant (ex. E002)."""
    return outils_rh.chercher_employe(UTILISATEUR, nom)


def consulter_solde(employe_id: str) -> dict:
    """Donne le solde de congés payés et de RTT (en jours) d'un employé, ex. E001."""
    return outils_rh.consulter_solde(UTILISATEUR, employe_id)


if __name__ == "__main__":
    client = genai.Client()
    chat = client.chats.create(
        model=os.environ.get("MODEL", "gemini-3.5-flash"),
        config=types.GenerateContentConfig(
            tools=[chercher_employe, consulter_solde],  # le SDK déduit les schémas
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=5)))
    reponse = chat.send_message(sys.argv[1] if len(sys.argv) > 1 else
                                "Combien de RTT reste-t-il à Karim Benali ?")
    for c in chat.get_history():
        for part in c.parts:
            if part.function_call:
                print("  appel :", part.function_call.name, dict(part.function_call.args))
    print(reponse.text)
