"""Discuter avec Alti dans le terminal, avant même d'avoir une interface web.

Lancer :  python console.py      (Ctrl+D pour quitter)
"""
import sys
import uuid

import chatbot

session = uuid.uuid4().hex
print("Alti : Bonjour, que puis-je faire pour vous ?")
for ligne in sys.stdin:
    if ligne.strip():
        print("Vous :", ligne.strip())
        print("Alti : ", end="")
        for morceau in chatbot.repondre(session, ligne.strip(), uuid.uuid4().hex[:12]):
            print(morceau, end="", flush=True)
        print()
