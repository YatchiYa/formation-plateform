"""Agent de veille concurrentielle : recherche web -> signaux structurés -> synthèse Markdown sourcée.

    python veille.py                 # lit concurrents.json, écrit rapports/veille-AAAA-Snn.md
"""
import asyncio
import json
import os
from datetime import date
from pathlib import Path
from typing import Literal

import httpx
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool, ToolContext, google_search
from google.genai import types

load_dotenv()
ICI = Path(__file__).resolve().parent
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
CATEGORIES = ("prix", "lancement", "recrutement", "partenariat", "autre")

# 1. Sous-agent de recherche : SEUL outil = google_search (outil intégré au modèle).
chercheur = Agent(
    name="chercheur_web",
    model=MODEL,
    description="Recherche sur le web les actualités récentes d'une entreprise et renvoie des faits datés.",
    instruction="Tu fais une recherche Google sur la demande reçue. Réponds par 3 à 6 puces factuelles, "
                "chacune avec sa date (AAAA-MM-JJ si connue). Uniquement des faits trouvés, aucune opinion.",
    tools=[google_search],
)


# 2. Les sources viennent des métadonnées d'ancrage (grounding), pas du texte du modèle.
def url_finale(url: str) -> str:
    """Les URL d'ancrage sont des redirections Google : on garde la vraie page (repli : l'URL reçue)."""
    if "grounding-api-redirect" not in url:
        return url
    try:
        return httpx.head(url, follow_redirects=False, timeout=10).headers.get("location", url)
    except httpx.HTTPError:
        return url


def ajouter_sources(tool, args, tool_context: ToolContext, tool_response):
    """after_tool_callback : après chaque recherche, numérote les sources et relie chaque fait à ses sources."""
    if tool.name != chercheur.name:
        return None
    meta = tool_context.state.get("temp:_adk_grounding_metadata")
    tool_context.state["temp:_adk_grounding_metadata"] = None  # ne pas réattribuer à la recherche suivante
    sources = list(tool_context.state.get("sources", []))
    id_de = {}  # index du chunk dans cette recherche -> identifiant global de la source
    for i, chunk in enumerate(getattr(meta, "grounding_chunks", None) or []):
        if not (chunk.web and chunk.web.uri):
            continue
        url = url_finale(chunk.web.uri)
        existant = next((s for s in sources if s["url"] == url), None)
        if existant is None:
            existant = {"id": len(sources) + 1, "titre": chunk.web.title or chunk.web.domain or url, "url": url}
            sources.append(existant)
        id_de[i] = existant["id"]
    tool_context.state["sources"] = sources
    faits = [{"texte": s.segment.text, "sources": sorted({id_de[j] for j in s.grounding_chunk_indices or [] if j in id_de})}
             for s in (getattr(meta, "grounding_supports", None) or []) if s.segment and s.segment.text]
    return {"faits_sources": faits, "texte_complet": tool_response,
            "sources": [{"id": s["id"], "titre": s["titre"]} for s in sources if s["id"] in id_de.values()]}


def enregistrer_signal(concurrent: str, categorie: Literal["prix", "lancement", "recrutement", "partenariat", "autre"],
                       resume: str, date_signal: str, source_ids: list[int], tool_context: ToolContext) -> dict:
    """Enregistre un signal concurrentiel vérifiable.

    Args:
        concurrent: nom de l'entreprise concernée.
        categorie: prix, lancement, recrutement, partenariat ou autre.
        resume: le fait en une phrase.
        date_signal: date du fait, AAAA-MM-JJ (ou AAAA-MM si le jour est inconnu).
        source_ids: identifiants des sources (champ "sources" renvoyé par chercheur_web).
    """
    connues = {s["id"] for s in tool_context.state.get("sources", [])}
    if not source_ids or not set(source_ids) <= connues:
        return {"erreur": f"source_ids doit citer des sources existantes parmi {sorted(connues)}"}
    signaux = list(tool_context.state.get("signaux", []))
    signaux.append({"concurrent": concurrent, "categorie": categorie, "resume": resume,
                    "date": date_signal, "sources": sorted(set(source_ids))})
    tool_context.state["signaux"] = signaux
    return {"ok": True, "nb_signaux": len(signaux)}


def creer_veilleur(model=MODEL, chercheur_agent: Agent = chercheur) -> Agent:
    return Agent(
        name="veilleur",
        model=model,
        instruction="""Tu es analyste de veille concurrentielle. Pour CHAQUE concurrent de la demande :
1. Appelle chercheur_web avec une requête précise (nom + actualités + période demandée).
2. Pour chaque fait sur les prix, un lancement, des recrutements ou un partenariat, appelle
   enregistrer_signal en citant les sources de CE fait (champ faits_sources). Ignore les faits sans source.
Quand tout est enregistré, réponds par une synthèse de 3 à 5 phrases : tendances communes
et ce qu'il faudrait surveiller. Pas de liste de liens : le rapport les ajoute.""",
        tools=[AgentTool(chercheur_agent, propagate_grounding_metadata=True), enregistrer_signal],
        after_tool_callback=ajouter_sources,
    )


# 3. Le rapport est mis en forme par du code : sources et structure garanties.
def rediger_rapport(synthese: str, signaux: list[dict], sources: list[dict], jour: date) -> str:
    annee, semaine, _ = jour.isocalendar()
    lignes = [f"# Veille concurrentielle - semaine {semaine} ({annee})", "",
              f"_Généré le {jour.isoformat()} par un agent : à relire avant diffusion._", "",
              "## Synthèse", "", synthese.strip(), ""]
    for cat in CATEGORIES:
        du_type = sorted((s for s in signaux if s["categorie"] == cat), key=lambda s: s["date"], reverse=True)
        if du_type:
            lignes += [f"## {cat.capitalize()}", "", "| Date | Concurrent | Signal | Sources |", "|---|---|---|---|"]
            lignes += [f"| {s['date']} | {s['concurrent']} | {s['resume']} | "
                       f"{' '.join(f'[{i}]' for i in s['sources'])} |" for s in du_type]
            lignes.append("")
    cites = sorted({i for s in signaux for i in s["sources"]})
    lignes += ["## Sources", ""] + [f"{s['id']}. [{s['titre']}]({s['url']})" for s in sources if s["id"] in cites]
    return "\n".join(lignes) + "\n"


async def lancer_veille(config: dict, jour: date, agent: Agent | None = None) -> tuple[str, dict]:
    runner = InMemoryRunner(agent=agent or creer_veilleur(), app_name="veille")
    demande = (f"Secteur : {config['secteur']}. Concurrents : {', '.join(config['concurrents'])}. "
               f"Période : les {config.get('jours', 7)} jours précédant le {jour.isoformat()}.")
    for essai in range(4):
        try:
            s = await runner.session_service.create_session(app_name="veille", user_id="veille")
            synthese = ""
            async for ev in runner.run_async(user_id="veille", session_id=s.id,
                                             new_message=types.Content(role="user", parts=[types.Part(text=demande)])):
                for p in (ev.content.parts if ev.content else []):
                    if p.function_call:
                        print(f"   [outil] {p.function_call.name} {json.dumps(dict(p.function_call.args), ensure_ascii=False)[:150]}")
                    if p.text and ev.is_final_response():
                        synthese += p.text
            etat = (await runner.session_service.get_session(app_name="veille", user_id="veille", session_id=s.id)).state
            return rediger_rapport(synthese, etat.get("signaux", []), etat.get("sources", []), jour), etat
        except Exception as e:
            if essai == 3 or not any(c in str(e) for c in ("429", "503", "UNAVAILABLE")):
                raise
            await asyncio.sleep(15 * (essai + 1))


if __name__ == "__main__":
    jour = date.today()
    config = json.loads((ICI / "concurrents.json").read_text(encoding="utf-8"))
    rapport, _ = asyncio.run(lancer_veille(config, jour))
    sortie = ICI / "rapports" / f"veille-{jour.isocalendar()[0]}-S{jour.isocalendar()[1]:02d}.md"
    sortie.parent.mkdir(exist_ok=True)
    sortie.write_text(rapport, encoding="utf-8")
    print(f"Rapport écrit : {sortie}")
