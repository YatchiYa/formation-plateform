"""Rédacteur et critique en boucle (Google ADK 2.10, mode « clé d'API »).

SequentialAgent(
    redacteur,                                   # premier brouillon
    LoopAgent(critique -> arbitre -> reviseur),  # jusqu'à validation ou max_iterations
)
L'arbitre est du code Python : il applique la grille et arrête la boucle (escalate=True).

Lancer :  python agent.py
"""
import asyncio
import os
import re
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.agents import Agent, BaseAgent, LoopAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import errors, types
from pydantic import BaseModel, Field

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
MODEL_REDACTEUR = os.environ.get("MODEL_REDACTEUR", "gemini-3.5-flash-lite")  # brouillons : modèle léger
MAX_TOURS = int(os.environ.get("MAX_TOURS", "4"))

# ---------- 1. La grille de qualité ----------
CRITERES = {
    "clarte": "Le lecteur comprend l'offre en une lecture ; phrases courtes, pas de jargon.",
    "concret": "Bénéfices chiffrés ou exemples précis tirés du brief, pas de promesses vagues.",
    "appel_action": "Une seule action claire et facile pour le lecteur à la fin.",
    "ton": "Professionnel et chaleureux, vouvoiement, pas de superlatifs creux.",
    "correction": "Orthographe, grammaire et accords irréprochables.",
}
SEUIL = 4                          # note minimale (sur 5) pour CHAQUE critère
MOYENNE_MIN = 4.8                  # et moyenne minimale sur l'ensemble des critères
MOTS_MIN, MOTS_MAX = 90, 150       # longueur attendue : lisible sur un écran de téléphone
MOTS_INTERDITS = ["révolutionnaire", "incroyable", "leader", "n°1", "meilleur du marché"]
MENTIONS_OBLIGATOIRES = ["89 EUR HT", "nimbus.example/audit"]  # prix exact et lien de réservation du brief


class Evaluation(BaseModel):
    clarte: int = Field(ge=1, le=5)
    concret: int = Field(ge=1, le=5)
    appel_action: int = Field(ge=1, le=5)
    ton: int = Field(ge=1, le=5)
    correction: int = Field(ge=1, le=5)
    remarques: list[str] = Field(description="Corrections précises et actionnables, une par problème")


def arbitrer(evaluation: dict, texte: str) -> tuple[bool, list[str]]:
    """Applique la grille. Les contrôles mesurables (longueur, mots interdits) sont faits en code."""
    consignes = [f"{c} : note {evaluation.get(c, 0)}/5 < {SEUIL}. {CRITERES[c]}"
                 for c in CRITERES if evaluation.get(c, 0) < SEUIL]
    moyenne = sum(evaluation.get(c, 0) for c in CRITERES) / len(CRITERES)
    if moyenne < MOYENNE_MIN:
        consignes.append(f"moyenne : {moyenne:.1f}/5 < {MOYENNE_MIN}. Traitez en priorité les remarques ci-dessous.")
    nb_mots = len(re.findall(r"\w+", texte))
    if not MOTS_MIN <= nb_mots <= MOTS_MAX:
        consignes.append(f"longueur : {nb_mots} mots, il en faut entre {MOTS_MIN} et {MOTS_MAX}.")
    consignes += [f"mot interdit : « {m} »" for m in MOTS_INTERDITS if m in texte.lower()]
    consignes += [f"mention obligatoire absente : « {m} »" for m in MENTIONS_OBLIGATOIRES if m not in texte]
    if consignes:  # les remarques du critique ne comptent que si la grille n'est pas satisfaite
        consignes += evaluation.get("remarques", [])
    return not consignes, consignes


class Arbitre(BaseAgent):
    """Lit l'évaluation, décide : on sort de la boucle (escalate) ou on donne des consignes au réviseur."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        s = ctx.session.state
        ok, consignes = arbitrer(s.get("evaluation") or {}, s.get("brouillon", ""))
        tours = s.get("tours", 0) + 1
        historique = s.get("historique", []) + [{"tour": tours, "evaluation": s.get("evaluation"), "valide": ok}]
        texte = f"Tour {tours} : {'VALIDÉ' if ok else f'{len(consignes)} consigne(s)'}"
        yield Event(author=self.name, invocation_id=ctx.invocation_id,
                    content=types.Content(role="model", parts=[types.Part(text=texte)]),
                    actions=EventActions(escalate=ok, state_delta={
                        "consignes": "\n".join(f"- {c}" for c in consignes),
                        "tours": tours, "historique": historique, "valide": ok}))


# ---------- 2. Les agents ----------
GRILLE = "\n".join(f"- {k} : {v}" for k, v in CRITERES.items())


def construire(model=None) -> SequentialAgent:
    """model : nom de modèle, ou fonction nom_agent -> modèle (utile pour les tests)."""
    m = model if callable(model) else (lambda nom: model or (MODEL_REDACTEUR if nom != "critique" else MODEL))
    redacteur = Agent(
        name="redacteur", model=m("redacteur"), output_key="brouillon", include_contents="none",
        instruction="Tu es rédacteur commercial. Écris une offre commerciale en français, en texte brut "
                    f"(sans titre Markdown), de {MOTS_MIN} à {MOTS_MAX} mots, à partir de ce brief :\n{{brief}}\n"
                    "N'invente aucun chiffre absent du brief.")
    critique = Agent(
        name="critique", model=m("critique"), output_schema=Evaluation, output_key="evaluation",
        include_contents="none",
        instruction=f"Tu es un relecteur exigeant. Note ce texte de 1 à 5 sur chaque critère :\n{GRILLE}\n"
                    "Sois sévère : 5 = rien à améliorer. Donne des remarques concrètes (quoi changer, où).\n"
                    "BRIEF :\n{brief}\n\nTEXTE À ÉVALUER :\n{brouillon}")
    reviseur = Agent(
        name="reviseur", model=m("reviseur"), output_key="brouillon", include_contents="none",
        instruction="Réécris le texte en appliquant TOUTES les consignes, sans rien inventer hors du brief. "
                    f"Réponds uniquement par le nouveau texte ({MOTS_MIN} à {MOTS_MAX} mots, texte brut).\n"
                    "BRIEF :\n{brief}\n\nCONSIGNES :\n{consignes}\n\nTEXTE ACTUEL :\n{brouillon}")
    boucle = LoopAgent(name="boucle_qualite", max_iterations=MAX_TOURS,
                       sub_agents=[critique, Arbitre(name="arbitre"), reviseur])
    return SequentialAgent(name="atelier_redaction", sub_agents=[redacteur, boucle])


root_agent = construire()


async def rediger(brief: str, agent=None, essais: int = 4) -> dict:
    """Exécute le pipeline et renvoie l'état final. Réessaie l'exécution sur 429/503."""
    agent = agent or root_agent
    for essai in range(essais):
        try:
            runner = InMemoryRunner(agent=agent, app_name="redaction")
            session = await runner.session_service.create_session(
                app_name="redaction", user_id="u1", state={"brief": brief})
            msg = types.Content(role="user", parts=[types.Part(text="Rédige l'offre décrite dans le brief.")])
            async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
                for p in (ev.content.parts if ev.content else []):
                    if p.text and ev.is_final_response():
                        print(f"  [{ev.author}] {p.text.strip()[:160]}")
            final = await runner.session_service.get_session(
                app_name="redaction", user_id="u1", session_id=session.id)
            return dict(final.state)
        except errors.APIError as e:
            if e.code not in (429, 503) or essai == essais - 1:
                raise
            await asyncio.sleep(15 * (essai + 1))


BRIEF_EXEMPLE = """Entreprise (fictive) : Atelier Nimbus, PME de maintenance informatique à Nantes.
Offre : contrat « Sérénité » pour cabinets de 5 à 20 postes : supervision des postes et sauvegardes,
intervention sur site sous 4 heures ouvrées, 89 EUR HT par poste et par mois, sans engagement au-delà de 12 mois.
Cible : gérants de cabinets comptables. Problème : pannes qui bloquent la saisie en période fiscale.
Action attendue : réserver un audit gratuit de 30 minutes sur nimbus.example/audit (adresse fictive)."""

if __name__ == "__main__":
    etat = asyncio.run(rediger(BRIEF_EXEMPLE))
    print("\n=== TEXTE FINAL ===\n" + etat["brouillon"])
    print(f"\nTours : {etat['tours']} | validé : {etat['valide']}")
    for h in etat["historique"]:
        print(h)
