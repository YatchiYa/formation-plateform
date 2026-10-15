"""Agent du tutoriel « même projet » (docs/02) : FAQ congés, sans donnée personnelle.

Volontairement minimal : un outil en lecture seule, des règles en dur.
Pour la production : ajouter Model Armor (voir agents/specialist/stock_agent).
"""
from google.adk.agents import Agent
from google.adk.models import Gemini

# ponytail: règles en dur pour le tutoriel ; en vrai, lire le guide RH (source connectée).
REGLES = {
    "conges payes": "25 jours ouvrés par an, acquis à raison de 2,08 jours par mois travaillé.",
    "rtt": "Selon l'accord d'entreprise : 10 jours par an pour un forfait jours.",
    "mariage": "4 jours ouvrés pour le mariage ou le PACS du salarié.",
    "naissance": "3 jours ouvrés, plus le congé de paternité de 25 jours calendaires.",
}


def regle_conges(type_conge: str) -> dict:
    """Règle Acme pour un type de congé.

    Args:
        type_conge: "conges payes", "rtt", "mariage" ou "naissance".
    """
    regle = REGLES.get(type_conge.strip().lower().replace("é", "e"))
    if regle is None:
        return {"status": "error", "error_message": f"Type inconnu. Connus : {', '.join(REGLES)}."}
    return {"status": "success", "type": type_conge, "regle": regle}


root_agent = Agent(
    name="conges_agent",
    model=Gemini(model="gemini-3.5-flash", client_kwargs={"enterprise": True, "location": "global"}),
    description="Répond aux questions générales sur les règles de congés Acme (congés payés, RTT, événements familiaux).",
    instruction=(
        "Tu réponds aux questions générales sur les congés. Appelle toujours regle_conges et cite la règle. "
        "Tu ne réponds jamais sur la situation individuelle d'un salarié (solde, demande en cours) : "
        "renvoie alors vers le RRH."
    ),
    tools=[regle_conges],
)

if __name__ == "__main__":
    assert regle_conges("RTT")["status"] == "success"
    assert regle_conges("Congés payés")["regle"].startswith("25 jours")
    assert regle_conges("sabbatique")["status"] == "error"
    print("conges_agent OK")
