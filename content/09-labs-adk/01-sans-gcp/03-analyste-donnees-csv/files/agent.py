"""Analyste de données qui exécute du Python (Google ADK 2.10, clé d'API Gemini).

BuiltInCodeExecutor active l'outil « exécution de code » de Gemini : le modèle écrit
du Python, Google l'exécute dans un bac à sable (pandas, matplotlib disponibles),
le modèle lit le résultat et continue. Rien ne s'exécute sur votre machine.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
MAX_LIGNES = 2000  # Limite connue : les données voyagent dans le prompt ; au-delà, pré-agréger ou exécuteur local

INSTRUCTION = """Tu es analyste de données. Tu réponds en français.
Règles :
- Tout chiffre que tu donnes doit venir d'un code Python que tu as exécuté. Jamais de calcul de tête.
- Commence par charger les données reçues dans un DataFrame pandas (io.StringIO), en recopiant le CSV EN ENTIER,
  puis vérifie le nombre de lignes avec len(df).
- Trace UN graphique matplotlib lisible (titre, axes, légende) : chiffre d'affaires mensuel par catégorie.
Rapport final en Markdown avec ces sections :
## Chiffres clés (CA total, CA par région, CA par catégorie)
## Tendances (évolution mensuelle, saisonnalité, catégorie qui progresse le plus)
## Recommandations (3 actions concrètes, chacune justifiée par un chiffre)
## Limites de l'analyse"""

root_agent = Agent(
    name="analyste_donnees",
    model=MODEL,
    description="Analyse un CSV de ventes en exécutant du code Python et produit un rapport avec graphique.",
    instruction=INSTRUCTION,
    code_executor=BuiltInCodeExecutor(),  # pas d'autres outils dans cet agent
)


def construire_message(question: str, chemin_csv: str) -> types.Content:
    """Fonction pure : la question + le contenu du CSV, dans un seul message utilisateur."""
    csv = Path(chemin_csv).read_text(encoding="utf-8").strip()
    n = csv.count("\n")
    if n > MAX_LIGNES:
        raise ValueError(f"{n} lignes : trop pour le prompt (max {MAX_LIGNES}). Pré-agrégez d'abord.")
    return types.Content(role="user", parts=[types.Part(
        text=f"{question}\n\nDonnées ({n} lignes, fichier {Path(chemin_csv).name}) :\n```csv\n{csv}\n```")])
