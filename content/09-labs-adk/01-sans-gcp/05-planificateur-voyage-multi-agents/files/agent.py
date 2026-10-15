"""Planificateur de voyage multi-agents (Google ADK 2.10, mode « clé d'API »).

Pipeline : ParallelAgent(transport, hébergement, activités)
           -> assembleur (sortie structurée) -> contrôle du budget (code Python).

Lancer :  python agent.py
"""
import asyncio
import json
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.agents import Agent, BaseAgent, ParallelAgent, SequentialAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner
from google.genai import errors, types
from pydantic import BaseModel, Field

try:  # chargé comme package par `adk web` / `adk run`
    from .donnees import ACTIVITES, HEBERGEMENTS, TRANSPORTS
except ImportError:  # lancé directement : python agent.py
    from donnees import ACTIVITES, HEBERGEMENTS, TRANSPORTS

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")


# ---------- 1. Outils : des fonctions Python ordinaires (données fictives) ----------
def chercher_transports(origine: str, destination: str) -> dict:
    """Liste les transports aller-retour entre deux villes (prix par voyageur, en euros)."""
    res = [t for t in TRANSPORTS
           if t["origine"].lower() == origine.lower() and t["destination"].lower() == destination.lower()]
    return {"options": res} if res else {"erreur": f"Aucun transport {origine} -> {destination}"}


def chercher_hebergements(ville: str, prix_nuit_max: int) -> dict:
    """Liste les hébergements d'une ville dont le prix par nuit est <= prix_nuit_max (euros)."""
    res = [h for h in HEBERGEMENTS if h["ville"].lower() == ville.lower() and h["prix_nuit"] <= prix_nuit_max]
    return {"options": res} if res else {"erreur": f"Aucun hébergement à {ville} sous {prix_nuit_max} EUR/nuit"}


def chercher_activites(ville: str, centres_interet: list[str]) -> dict:
    """Liste les activités d'une ville. centres_interet : catégories parmi culture, gastronomie, musique, sport."""
    voulues = {c.lower() for c in centres_interet}
    res = [a for a in ACTIVITES if a["ville"].lower() == ville.lower() and (not voulues or a["categorie"] in voulues)]
    return {"options": res} if res else {"erreur": f"Aucune activité à {ville}"}


# ---------- 2. Sortie structurée de l'assembleur ----------
class Jour(BaseModel):
    jour: int
    programme: str = Field(description="Programme du jour en une ou deux phrases")
    activite_ids: list[str] = Field(default_factory=list, description="Identifiants A... prévus ce jour")


class Itineraire(BaseModel):
    titre: str
    transport_id: str = Field(description="Identifiant T... retenu")
    hebergement_id: str = Field(description="Identifiant H... retenu")
    jours: list[Jour]
    conseils: str


# ---------- 3. Contrôle du budget : agent déterministe, sans LLM ----------
def calculer_budget(itineraire: dict, voyageurs: int, nuits: int, budget_max: float) -> dict:
    """Recalcule le coût à partir du CATALOGUE (jamais à partir des prix écrits par le LLM)."""
    t = {x["id"]: x for x in TRANSPORTS}.get(itineraire.get("transport_id"))
    h = {x["id"]: x for x in HEBERGEMENTS}.get(itineraire.get("hebergement_id"))
    cat_a = {x["id"]: x for x in ACTIVITES}
    ids_a = [i for j in itineraire.get("jours", []) for i in j.get("activite_ids", [])]
    erreurs = [f"identifiant inconnu : {i}" for i in ids_a if i not in cat_a]
    if t is None:
        erreurs.append(f"transport inconnu : {itineraire.get('transport_id')}")
    if h is None:
        erreurs.append(f"hébergement inconnu : {itineraire.get('hebergement_id')}")
    if len(set(ids_a)) != len(ids_a):
        erreurs.append("activité réservée deux fois")
    postes = {
        "transport": (t["prix_eur"] * voyageurs) if t else 0,
        "hebergement": (h["prix_nuit"] * nuits) if h else 0,
        "activites": sum(cat_a[i]["prix_eur"] for i in set(ids_a) if i in cat_a) * voyageurs,
    }
    total = sum(postes.values())
    return {"postes": postes, "total": total, "budget_max": budget_max,
            "respecte": total <= budget_max and not erreurs, "erreurs": erreurs}


class ControleBudget(BaseAgent):
    """Lit l'itinéraire dans l'état de session et écrit le verdict budgétaire."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        s = ctx.session.state
        verdict = calculer_budget(s.get("itineraire") or {}, s["voyageurs"], s["nuits"], s["budget_max"])
        etat = "OK" if verdict["respecte"] else "À REVOIR"
        texte = f"Budget {etat} : {verdict['total']} EUR pour {verdict['budget_max']} EUR max. Détail : {verdict['postes']}"
        if verdict["erreurs"]:
            texte += f" Erreurs : {verdict['erreurs']}"
        yield Event(author=self.name, invocation_id=ctx.invocation_id,
                    content=types.Content(role="model", parts=[types.Part(text=texte)]),
                    actions=EventActions(state_delta={"controle_budget": verdict}))


# ---------- 4. Assemblage des agents ----------
def construire(model=None) -> SequentialAgent:
    """model : nom de modèle, ou fonction nom_agent -> modèle (utile pour les tests)."""
    m = model if callable(model) else (lambda _nom: model or MODEL)
    transport = Agent(
        name="transport", model=m("transport"), tools=[chercher_transports], output_key="transport",
        instruction="Tu es l'expert transport. Demande : {demande}. Appelle chercher_transports, puis "
                    "recommande 1 option principale et 1 alternative moins chère, avec leur identifiant T..., "
                    "leur durée et leur prix par voyageur. Réponds en 3 lignes maximum.")
    hebergement = Agent(
        name="hebergement", model=m("hebergement"), tools=[chercher_hebergements], output_key="hebergement",
        instruction="Tu es l'expert hébergement. Demande : {demande}. Budget total : {budget_max} EUR pour "
                    "{nuits} nuits. Appelle chercher_hebergements avec un prix_nuit_max raisonnable (au plus 40 % "
                    "du budget divisé par le nombre de nuits), puis recommande 2 options avec identifiant H..., "
                    "quartier, prix par nuit et note. 3 lignes maximum.")
    activites = Agent(
        name="activites", model=m("activites"), tools=[chercher_activites], output_key="activites",
        instruction="Tu es l'expert activités. Demande : {demande}. Appelle chercher_activites avec les centres "
                    "d'intérêt de la demande, puis propose 3 à 4 activités avec identifiant A..., durée et prix "
                    "par voyageur. 4 lignes maximum.")
    assembleur = Agent(
        name="assembleur", model=m("assembleur"), output_schema=Itineraire, output_key="itineraire",
        instruction="Tu assembles un itinéraire de {nuits} nuits pour {voyageurs} voyageur(s), budget total "
                    "{budget_max} EUR. Propositions reçues :\nTRANSPORT : {transport}\nHÉBERGEMENT : {hebergement}\n"
                    "ACTIVITÉS : {activites}\nChoisis UNIQUEMENT des identifiants présents ci-dessus. Calcule "
                    "mentalement le total (transport x voyageurs + nuit x nuits + activités x voyageurs) et "
                    "choisis des options qui tiennent dans le budget. N'invente aucun prix.")
    return SequentialAgent(name="planificateur_voyage", sub_agents=[
        ParallelAgent(name="recherches", sub_agents=[transport, hebergement, activites]),
        assembleur,
        ControleBudget(name="controle_budget"),
    ])


root_agent = construire()  # point d'entrée attendu par `adk web` / `adk run`


async def planifier(demande: dict, agent=None, essais: int = 4) -> dict:
    """Exécute le pipeline et renvoie l'état final (itinéraire + verdict). Réessaie sur 429/503."""
    agent = agent or root_agent
    for essai in range(essais):
        try:
            runner = InMemoryRunner(agent=agent, app_name="voyage")
            session = await runner.session_service.create_session(
                app_name="voyage", user_id="u1",
                state={"demande": demande["texte"], "voyageurs": demande["voyageurs"],
                       "nuits": demande["nuits"], "budget_max": demande["budget_max"]})
            msg = types.Content(role="user", parts=[types.Part(text=demande["texte"])])
            async for ev in runner.run_async(user_id="u1", session_id=session.id, new_message=msg):
                for p in (ev.content.parts if ev.content else []):
                    if p.function_call:
                        print(f"  [{ev.author}] outil {p.function_call.name}({dict(p.function_call.args)})")
                    elif p.text and ev.is_final_response():
                        print(f"  [{ev.author}] {p.text.strip()[:300]}")
            final = await runner.session_service.get_session(app_name="voyage", user_id="u1", session_id=session.id)
            return dict(final.state)
        except errors.APIError as e:
            if e.code not in (429, 503) or essai == essais - 1:
                raise
            await asyncio.sleep(15 * (essai + 1))


DEMANDE_EXEMPLE = {
    "texte": "Nous partons à 2 de Lyon à Lisbonne pour 3 nuits. Nous aimons la culture et la gastronomie. "
             "Budget total 900 euros tout compris.",
    "voyageurs": 2, "nuits": 3, "budget_max": 900,
}

if __name__ == "__main__":
    etat = asyncio.run(planifier(DEMANDE_EXEMPLE))
    print(json.dumps({"itineraire": etat.get("itineraire"), "controle_budget": etat.get("controle_budget")},
                     ensure_ascii=False, indent=2))
