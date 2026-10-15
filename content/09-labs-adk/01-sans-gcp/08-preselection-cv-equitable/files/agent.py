"""Présélection de CV FICTIFS avec contrôles d'équité (Google ADK 2.10, mode « clé d'API »).

1. anonymiser()       : on ne garde que les sections utiles au poste, on retire nom, contacts, genre grammatical
2. garde_anonymat()   : before_model_callback qui BLOQUE l'appel si un attribut sensible reste dans la requête
3. agent evaluateur   : sortie structurée (output_schema), une note et une justification par critère
4. scorer()           : score pondéré calculé en Python, preuves vérifiées, statut « en attente de revue humaine »

python agent.py           # évalue les 6 CV et écrit revue_humaine.csv
"""
import asyncio
import csv
import json
import os
import re
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import errors, types
from pydantic import BaseModel, Field

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
ICI = Path(__file__).parent
FICHE = json.loads((ICI / "fiche_poste.json").read_text(encoding="utf-8"))
CVS = json.loads((ICI / "cvs.json").read_text(encoding="utf-8"))

# ---------- 1. Anonymisation : liste BLANCHE de sections + nettoyage ----------
SECTIONS_UTILES = ["experience", "competences", "formation", "langues"]  # ni titre, ni loisirs, ni identité
# Limite connue : table de formes féminines/masculines limitée au vocabulaire des CV du lab ;
# en production, utiliser un outil de neutralisation (ou une relecture) adapté à vos CV.
FORME_UNIQUE = {"développeuse": "développeur", "ingénieure": "ingénieur", "diplômée": "diplômé",
                "certifiée": "certifié", "référente": "référent"}


def anonymiser(cv: dict) -> str:
    ident = cv["identite"]
    texte = "\n".join(f"{s.upper()} : {cv['sections'][s]}" for s in SECTIONS_UTILES)
    for mot in ident["nom"].split():                                   # prénom et nom, où qu'ils soient
        texte = re.sub(rf"\b{re.escape(mot)}\b", "[NOM]", texte, flags=re.I)
    texte = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[EMAIL]", texte)
    texte = re.sub(r"(?:\+33|0)\d(?:[ .]?\d{2}){4}", "[TEL]", texte)
    texte = re.sub(r"\b(Mme|Mlle|M\.|Madame|Monsieur)\s", "", texte)
    for f, m in FORME_UNIQUE.items():
        texte = re.sub(rf"\b{f}(s?)\b", rf"{m}\1", texte)
        texte = re.sub(rf"\b{f.capitalize()}(s?)\b", rf"{m.capitalize()}\1", texte)
    return texte


def termes_sensibles(cv: dict) -> list[str]:
    """Ce qui ne doit JAMAIS atteindre le modèle."""
    i = cv["identite"]
    return [*i["nom"].split(), i["email"], i["telephone"], i["date_naissance"][:4], i["nationalite"],
            i["adresse"].split(",")[-1].strip(), i["situation_familiale"]]


def garde_anonymat(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    """before_model_callback : exécuté avant CHAQUE appel au modèle. Lever une exception arrête tout."""
    texte = str(llm_request.config.system_instruction or "") + " ".join(
        p.text or "" for c in llm_request.contents for p in c.parts or [])
    fuites = [t for t in callback_context.state.get("termes_sensibles", []) if t.lower() in texte.lower()]
    if fuites:
        raise PermissionError(f"appel bloqué, attributs sensibles présents : {fuites}")
    return None  # None = l'appel au modèle peut avoir lieu


# ---------- 2. Sortie structurée ----------
class NoteCritere(BaseModel):
    critere: Literal["python_backend", "bases_donnees", "cloud_devops", "qualite", "communication"]
    note: int = Field(ge=0, le=3, description="0 absent, 1 faible, 2 conforme, 3 au-delà de l'attendu")
    justification: str = Field(description="Une phrase factuelle")
    preuve: str = Field(description="Citation EXACTE et courte du CV, ou chaîne vide si rien")


class EvaluationCV(BaseModel):
    notes: list[NoteCritere]
    points_a_verifier: list[str] = Field(description="Questions à poser en entretien")


GRILLE = "\n".join(f"- {c['id']} (poids {c['poids']}) : {c['attendu']}" for c in FICHE["criteres"])
INSTRUCTION = f"""Tu aides un recruteur à PRÉSÉLECTIONNER des CV pour le poste : {FICHE['intitule']}.
Note chaque critère de 0 à 3 UNIQUEMENT à partir des compétences et expériences décrites :
{GRILLE}
Règles : une note par critère, une justification factuelle, une preuve citée mot pour mot du CV.
N'infère jamais l'âge, le genre, l'origine ou la situation familiale, et ne les utilise pas.
Tu ne décides pas : un humain relit chaque dossier."""


def construire(model=None) -> Agent:
    return Agent(name="evaluateur", model=model or MODEL, instruction=INSTRUCTION, output_schema=EvaluationCV,
                 output_key="evaluation", include_contents="default", before_model_callback=garde_anonymat,
                 generate_content_config=types.GenerateContentConfig(temperature=0))


root_agent = construire()


# ---------- 3. Score et décision : en code, jamais par le modèle ----------
def scorer(evaluation: dict, texte_anonyme: str) -> dict:
    poids = {c["id"]: c["poids"] for c in FICHE["criteres"]}
    notes = {n["critere"]: n for n in evaluation["notes"]}
    manquants = [c for c in poids if c not in notes]
    sans_preuve = [c for c, n in notes.items()
                   if n["note"] > 0 and (not n["preuve"] or n["preuve"].lower() not in texte_anonyme.lower())]
    score = round(100 * sum(poids[c] * notes[c]["note"] for c in poids if c in notes) / (3 * sum(poids.values())))
    tranche = "fort" if score >= 65 else "moyen" if score >= 40 else "faible"
    return {"score": score, "tranche": tranche, "criteres_manquants": manquants, "preuves_introuvables": sans_preuve,
            "statut": "en_attente_revue_humaine"}  # aucune décision automatique, jamais


async def evaluer_texte(texte: str, sensibles: list[str], agent=None, essais: int = 4) -> dict:
    agent = agent or root_agent
    for essai in range(essais):
        try:
            runner = InMemoryRunner(agent=agent, app_name="cv")
            session = await runner.session_service.create_session(
                app_name="cv", user_id="recruteur", state={"termes_sensibles": sensibles})
            msg = types.Content(role="user", parts=[types.Part(text="CV ANONYMISÉ :\n" + texte)])
            async for _ in runner.run_async(user_id="recruteur", session_id=session.id, new_message=msg):
                pass
            etat = (await runner.session_service.get_session(
                app_name="cv", user_id="recruteur", session_id=session.id)).state
            return etat["evaluation"]
        except errors.APIError as e:
            if e.code not in (429, 503) or essai == essais - 1:
                raise
            await asyncio.sleep(15 * (essai + 1))


async def evaluer_cv(cv: dict, agent=None) -> dict:
    texte = anonymiser(cv)
    evaluation = await evaluer_texte(texte, termes_sensibles(cv), agent)
    return {"id": cv["id"], **scorer(evaluation, texte), "evaluation": evaluation}


def ecrire_revue_humaine(resultats: list[dict], chemin: str = "revue_humaine.csv") -> None:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "score", "tranche_suggeree", "preuves_introuvables", "statut",
                    "decision_recruteur", "commentaire_recruteur"])
        for r in sorted(resultats, key=lambda r: -r["score"]):
            w.writerow([r["id"], r["score"], r["tranche"], ";".join(r["preuves_introuvables"]), r["statut"], "", ""])


if __name__ == "__main__":
    async def main():
        resultats = [await evaluer_cv(cv) for cv in CVS]
        for r in resultats:
            print(r["id"], r["score"], r["tranche"], {n["critere"]: n["note"] for n in r["evaluation"]["notes"]},
                  "preuves introuvables :", r["preuves_introuvables"])
        ecrire_revue_humaine(resultats)
        print("-> revue_humaine.csv : à compléter par un recruteur (colonne decision_recruteur).")
    asyncio.run(main())
