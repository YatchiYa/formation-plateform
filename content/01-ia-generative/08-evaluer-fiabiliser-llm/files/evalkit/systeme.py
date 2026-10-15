FAUX = {"Combien de jours de congés ?": {"reponse": "Vous avez 25 jours ouvrés.", "sources": ["conges-2026"]},
        "Quelle est la politique vélo ?": {"reponse": "Je ne trouve pas cette information.", "sources": []},
        "Combien de jours de télétravail ?": {"reponse": "2 jours par semaine.", "sources": ["teletravail-2024"]}}
def repondre(q):
    return FAUX[q]
