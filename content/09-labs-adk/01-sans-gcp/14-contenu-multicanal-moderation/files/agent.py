"""Déclinaisons multicanal d'un brief produit, avec modération par callbacks.

    python agent.py brief_produit.md
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent, ParallelAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types

from moderation import masquer_donnees_personnelles, promesses_interdites

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

CANAUX = {
    "linkedin": (1300, "Post LinkedIn professionnel : une accroche forte en 1re ligne, "
                       "3 paragraphes courts, un appel à l'action, 3 hashtags maximum."),
    "instagram": (800, "Légende Instagram : ton chaleureux, 2 ou 3 emojis, phrases courtes, "
                       "5 hashtags en fin de texte."),
    "newsletter": (1500, "Bloc de newsletter : un objet d'e-mail (ligne 'Objet : ...'), "
                         "un titre, 2 paragraphes, un bouton d'action entre crochets."),
    "whatsapp": (350, "Message WhatsApp de diffusion : 2 à 3 phrases, vouvoiement, "
                      "1 emoji au plus, un lien factice https://exemple.fr/produit."),
}

REGLES = """Règles de conformité (obligatoires) :
- n'invente aucun chiffre, aucune caractéristique, aucun prix absent du brief ;
- aucune promesse absolue : pas de « garanti à vie », « 100 % », « sans risque »,
  « le meilleur du marché », « miracle », ni d'allégation de santé ;
- n'écris aucune donnée personnelle (e-mail, téléphone, nom d'un particulier) ;
- si le brief contient [EMAIL], [TELEPHONE]... ignore ces marqueurs."""

BLOQUE = "[BLOQUÉ PAR LA MODÉRATION]"


def _journal(ctx: CallbackContext, etape: str, motif: list[str]) -> None:
    # Une clé PAR canal : les 4 agents tournent en parallèle ; avec une liste
    # commune, une lecture périmée suivie d'une écriture ferait perdre des entrées.
    cle = f"moderation_{ctx.agent_name}"
    ctx.state[cle] = ctx.state.get(cle, []) + [{"etape": etape, "motif": motif}]


def moderer_entree(callback_context: CallbackContext,
                   llm_request: LlmRequest) -> LlmResponse | None:
    """AVANT le modèle : masque les données personnelles, refuse un brief non conforme."""
    for content in llm_request.contents:
        for part in content.parts or []:
            if part.text:
                part.text, trouves = masquer_donnees_personnelles(part.text)
                if trouves:
                    _journal(callback_context, "entrée : masquage", trouves)
    brief = " ".join(p.text or "" for c in llm_request.contents if c.role == "user"
                     for p in c.parts or [])
    interdites = promesses_interdites(brief)
    if interdites:  # Le modèle n'est PAS appelé : 0 token consommé.
        _journal(callback_context, "entrée : brief refusé", interdites)
        return LlmResponse(content=types.Content(role="model", parts=[types.Part(
            text=f"{BLOQUE} Brief non conforme : {', '.join(interdites)}.")]))
    return None


def moderer_sortie(callback_context: CallbackContext,
                   llm_response: LlmResponse) -> LlmResponse | None:
    """APRÈS le modèle : bloque une promesse interdite ou une donnée personnelle."""
    if not llm_response.content or not llm_response.content.parts:
        return None
    texte = "".join(p.text or "" for p in llm_response.content.parts)
    motifs = promesses_interdites(texte) + masquer_donnees_personnelles(texte)[1]
    if not motifs:
        return None
    _journal(callback_context, "sortie : texte bloqué", motifs)
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(
        text=f"{BLOQUE} Le texte généré contenait : {', '.join(motifs)}.")]))


def agent_canal(canal: str, max_car: int, consigne: str, model=MODEL) -> Agent:
    return Agent(
        name=canal,
        model=model,
        description=f"Rédige la déclinaison {canal} du brief.",
        instruction=f"Tu es rédacteur marketing. À partir du brief produit de l'utilisateur, "
                    f"écris UNIQUEMENT le texte final pour ce canal, en français.\n{consigne}\n"
                    f"Longueur maximale : {max_car} caractères.\n{REGLES}",
        output_key=f"texte_{canal}",
        before_model_callback=moderer_entree,
        after_model_callback=moderer_sortie,
    )


def creer_agent(model=MODEL) -> ParallelAgent:
    return ParallelAgent(
        name="declinaisons",
        description="Produit en parallèle les 4 déclinaisons d'un brief.",
        sub_agents=[agent_canal(c, m, txt, model) for c, (m, txt) in CANAUX.items()],
    )


root_agent = creer_agent()


async def decliner(brief: str, agent=root_agent) -> dict:
    """Lance les 4 rédacteurs en parallèle ; renvoie l'état final de la session."""
    runner = InMemoryRunner(agent=agent, app_name="multicanal")
    s = await runner.session_service.create_session(app_name="multicanal", user_id="u")
    async for _ in runner.run_async(
            user_id="u", session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=brief)])):
        pass
    s = await runner.session_service.get_session(app_name="multicanal", user_id="u",
                                                 session_id=s.id)
    return s.state


def rapport(etat: dict) -> str:
    lignes = []
    for canal, (max_car, _) in CANAUX.items():
        texte = etat.get(f"texte_{canal}", "")
        statut = "BLOQUÉ" if texte.startswith(BLOQUE) else (
            "TROP LONG" if len(texte) > max_car else "ok")
        lignes += [f"## {canal} ({len(texte)}/{max_car} car., {statut})", texte, ""]
    lignes.append("## Journal de modération")
    lignes += [f"- {canal} | {e['etape']} | {', '.join(e['motif'])}"
               for canal in CANAUX for e in etat.get(f"moderation_{canal}", [])
               ] or ["- rien à signaler"]
    return "\n".join(lignes)


if __name__ == "__main__":
    chemin = Path(sys.argv[1] if len(sys.argv) > 1 else "brief_produit.md")
    print(rapport(asyncio.run(decliner(chemin.read_text(encoding="utf-8")))))
