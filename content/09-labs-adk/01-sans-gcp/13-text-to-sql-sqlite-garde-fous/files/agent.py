"""Agent text-to-SQL : questions en français -> SQL contrôlé -> réponse expliquée.

    python agent.py "Quel est le chiffre d'affaires livré par catégorie ?"
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.genai import types

import garde_fous
from creer_base import creer

load_dotenv()
BASE = Path(os.environ.get("BASE_SQLITE", Path(__file__).with_name("ventes.db")))
if not BASE.exists():
    creer(BASE)
CON = garde_fous.connecter(BASE)
SCHEMA = garde_fous.schema(BASE)


def executer_sql(requete: str, tool_context: ToolContext) -> dict:
    """Exécute UNE requête SQLite en lecture seule sur la base des ventes.

    Args:
        requete: une requête SELECT (ou WITH ... SELECT) sur les tables autorisées.
    Returns:
        les colonnes, les lignes (50 au maximum), 'tronque' si le résultat a été coupé,
        ou un champ 'erreur' expliquant pourquoi la requête a été refusée.
    """
    # Journal de toutes les requêtes proposées : utile pour l'évaluation et l'audit.
    tool_context.state["requetes"] = tool_context.state.get("requetes", []) + [requete]
    try:
        resultat = garde_fous.executer(CON, requete)
    except garde_fous.RequeteRefusee as e:
        tool_context.state["refus"] = tool_context.state.get("refus", 0) + 1
        return {"erreur": str(e), "conseil": "Corrige la requête et réessaie."}
    tool_context.state["dernier_resultat"] = resultat
    return resultat


INSTRUCTION = f"""Tu es un analyste de données. Tu réponds en français à des questions
sur la base SQLite des ventes d'une boutique fictive.

Schéma (seules ces tables existent pour toi) :
{SCHEMA}

Règles métier :
- chiffre d'affaires (CA) = SUM(lignes_commande.quantite * lignes_commande.prix_unitaire) ;
- sauf demande contraire, ne compte que les commandes au statut 'livree' pour le CA ;
- les dates sont des textes ISO 'AAAA-MM-JJ' : utilise strftime('%Y-%m', date_commande) ;
- statuts possibles : 'livree', 'annulee', 'en_cours'.

Méthode :
1. Écris UNE requête SQLite SELECT qui calcule directement le résultat final (moyenne,
   ratio, classement...) et appelle executer_sql. Ne calcule rien de tête, ne devine
   jamais un chiffre.
2. Si l'outil renvoie une erreur, corrige la requête (2 essais au maximum).
3. Réponds en trois parties courtes :
   **Réponse** : le résultat, chiffres arrondis à 2 décimales ;
   **Requête** : le SQL exécuté, dans un bloc ```sql ;
   **Explication** : comment le résultat est calculé (tables, filtres), et ses limites
   (par exemple « résultat tronqué à 50 lignes »).
Si la question sort du périmètre (autre table, modification des données, données
personnelles), refuse poliment et explique pourquoi."""

root_agent = Agent(
    name="analyste_sql",
    model=os.environ.get("MODEL", "gemini-3.5-flash"),
    description="Répond à des questions sur les ventes en écrivant du SQL contrôlé.",
    instruction=INSTRUCTION,
    tools=[executer_sql],
)


async def demander(question: str, agent=root_agent) -> tuple[str, dict]:
    """Pose une question dans une session neuve ; renvoie (réponse, état de session)."""
    runner = InMemoryRunner(agent=agent, app_name="text_to_sql")
    s = await runner.session_service.create_session(app_name="text_to_sql", user_id="u")
    reponse = ""
    async for ev in runner.run_async(
            user_id="u", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=question)])):
        if ev.is_final_response() and ev.content and ev.content.parts:
            reponse = "".join(p.text or "" for p in ev.content.parts)
    s = await runner.session_service.get_session(app_name="text_to_sql", user_id="u",
                                                 session_id=s.id)
    return reponse, s.state


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Combien de commandes ont été livrées en 2026 ?"
    print(asyncio.run(demander(q))[0])
