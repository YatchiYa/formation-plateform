"""Tuteur pédagogique ADK : évalue le niveau, pose des questions, adapte la difficulté
et garde la progression dans l'état « user: » (persisté entre sessions par main.py)."""
import os

from google.adk.agents import Agent
from google.adk.tools import ToolContext

APP_NAME = "tuteur"
NIVEAUX = {1: "débutant", 2: "élémentaire", 3: "intermédiaire", 4: "avancé", 5: "expert"}


def ajuster_niveau(niveau: int, serie: list[bool]) -> tuple[int, list[bool]]:
    """Règle déterministe : 2 bonnes réponses d'affilée -> +1, 2 erreurs d'affilée -> -1.

    Renvoie (nouveau niveau, nouvelle série). La série repart de zéro à chaque changement.
    """
    if serie[-2:] == [True, True] and niveau < 5:
        return niveau + 1, []
    if serie[-2:] == [False, False] and niveau > 1:
        return niveau - 1, []
    return niveau, serie[-2:]


def definir_niveau(theme: str, niveau: int, tool_context: ToolContext) -> dict:
    """Enregistre le niveau de départ d'un thème après le test de positionnement.

    Args:
        theme: le thème travaillé, en minuscules (ex. "python", "sql").
        niveau: de 1 (débutant) à 5 (expert).
    """
    niveau = max(1, min(5, int(niveau)))
    progression = dict(tool_context.state.get("user:progression", {}))
    progression[theme.lower()] = {"niveau": niveau, "serie": [], "bonnes": 0, "total": 0, "a_revoir": []}
    tool_context.state["user:progression"] = progression  # réaffecter = écrire un state_delta
    return {"theme": theme.lower(), "niveau": niveau, "libelle": NIVEAUX[niveau]}


def enregistrer_reponse(theme: str, notion: str, correcte: bool, tool_context: ToolContext) -> dict:
    """Enregistre la réponse de l'élève et recalcule le niveau du thème.

    Args:
        theme: le thème de la question (ex. "python").
        notion: la notion testée, en 2 à 4 mots (ex. "compréhension de liste").
        correcte: True si la réponse de l'élève est juste.
    """
    progression = dict(tool_context.state.get("user:progression", {}))
    fiche = dict(progression.get(theme.lower()) or {"niveau": 2, "serie": [], "bonnes": 0, "total": 0, "a_revoir": []})
    ancien = fiche["niveau"]
    fiche["total"] += 1
    fiche["bonnes"] += int(correcte)
    a_revoir = [n for n in fiche["a_revoir"] if n != notion]
    fiche["a_revoir"] = a_revoir if correcte else (a_revoir + [notion])[-5:]
    fiche["niveau"], fiche["serie"] = ajuster_niveau(ancien, fiche["serie"] + [correcte])
    progression[theme.lower()] = fiche
    tool_context.state["user:progression"] = progression
    return {"niveau": fiche["niveau"], "libelle": NIVEAUX[fiche["niveau"]],
            "changement": fiche["niveau"] - ancien, "score": f"{fiche['bonnes']}/{fiche['total']}"}


INSTRUCTION = f"""Tu es un tuteur patient qui parle français et tutoie l'élève.
Niveaux : {NIVEAUX}.
Progression mémorisée de l'élève (vide = nouvel élève) : {{user:progression?}}

Déroulé :
1. Si le thème demandé n'est pas dans la progression : pose 2 questions de positionnement
   (une facile, une plus difficile), UNE à la fois, puis appelle definir_niveau.
   Si le thème est connu : salue l'élève, rappelle son niveau et ses notions à revoir.
2. Pose UNE question à la fois, adaptée au niveau du thème. Privilégie les notions à revoir.
3. Quand l'élève répond : juge la réponse, appelle enregistrer_reponse, puis donne un retour
   court (pourquoi c'est juste ou faux) et enchaîne avec la question suivante au niveau renvoyé.
   Si "changement" vaut 1 ou -1, annonce le changement de niveau.
Ne donne jamais la réponse avant que l'élève ait essayé. Reste concis (moins de 120 mots)."""

root_agent = Agent(
    name="tuteur",
    model=os.environ.get("MODEL", "gemini-3.5-flash"),
    description="Tuteur adaptatif qui mémorise la progression de l'élève.",
    instruction=INSTRUCTION,
    tools=[definir_niveau, enregistrer_reponse],
)
