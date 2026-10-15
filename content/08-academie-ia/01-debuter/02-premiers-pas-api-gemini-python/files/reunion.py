"""Assistant de réunion : résumé + actions à partir d'une transcription, avec l'API Gemini.

    python reunion.py resume  reunion_exemple.txt          # résumé structuré + actions
    python reunion.py resume  reunion_exemple.txt --stream # résumé affiché au fil de l'eau
    python reunion.py tokens  reunion_exemple.txt          # tokens + coût estimé, sans générer
    python reunion.py chat    reunion_exemple.txt          # questions/réponses multi-tours

Mode « clé d'API » (par défaut) : GEMINI_API_KEY (ou GOOGLE_API_KEY).
Mode « Vertex AI » : GOOGLE_GENAI_USE_VERTEXAI=TRUE et GOOGLE_CLOUD_PROJECT=<projet>.
"""
import argparse
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
# Prix en dollars par million de tokens. Valeurs d'EXEMPLE : recopiez celles de la page
# https://ai.google.dev/gemini-api/docs/pricing pour votre modèle.
PRIX_ENTREE_1M = float(os.environ.get("PRIX_ENTREE_1M", "0.30"))
PRIX_SORTIE_1M = float(os.environ.get("PRIX_SORTIE_1M", "2.50"))

SYSTEM_INSTRUCTION = """Tu es l'assistant de réunion d'une équipe.
On te donne la transcription d'une réunion. Tu réponds en français, de façon factuelle.
Tu n'inventes ni décision, ni responsable, ni date : si l'information n'est pas dans
la transcription, écris « non précisé »."""


class Action(BaseModel):
    tache: str
    responsable: str
    echeance: str


class CompteRendu(BaseModel):
    resume: str
    decisions: list[str]
    actions: list[Action]


def make_client() -> genai.Client:
    """Le même code sert les deux modes : le SDK lit les variables d'environnement.
    Le délai (en millisecondes) évite qu'une requête bloquée fige le programme."""
    return genai.Client(http_options=types.HttpOptions(timeout=90_000))


def mode() -> str:
    vertex = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() in ("true", "1")
    return "Vertex AI" if vertex else "clé d'API"


def config(**extra) -> types.GenerateContentConfig:
    # TEMPERATURE facultative : Gemini 3.6+ l'ignore et, pour Gemini 3 / 3.5, la doc
    # conseille la valeur par défaut. Utile avec gemini-2.5-flash (ex. TEMPERATURE=0.2).
    if os.environ.get("TEMPERATURE"):
        extra["temperature"] = float(os.environ["TEMPERATURE"])
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        max_output_tokens=4096,   # plafond de la réponse (pensée comprise)
        **extra,
    )


def avec_reessais(appel, essais=4, attente=5):
    """Réessaie sur 429 (quota) et 5xx (serveur), avec attente exponentielle."""
    for essai in range(essais):
        try:
            return appel()
        except errors.APIError as e:
            if e.code not in (429, 500, 502, 503, 504) or essai == essais - 1:
                raise
            pause = attente * 2 ** essai
            print(f"[erreur {e.code}, nouvel essai dans {pause} s]", file=sys.stderr)
            time.sleep(pause)


def cout(usage) -> float:
    """Coût estimé d'un appel à partir de usage_metadata (la pensée est facturée en sortie)."""
    entree = usage.prompt_token_count or 0
    sortie = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return (entree * PRIX_ENTREE_1M + sortie * PRIX_SORTIE_1M) / 1_000_000


def compte_rendu(client, transcription: str) -> tuple[CompteRendu, float]:
    response = avec_reessais(lambda: client.models.generate_content(
        model=MODEL,
        contents=f"Transcription :\n{transcription}\n\nFais le compte rendu.",
        config=config(response_mime_type="application/json", response_schema=CompteRendu),
    ))
    return CompteRendu.model_validate_json(response.text), cout(response.usage_metadata)


def en_markdown(cr: CompteRendu) -> str:
    lignes = ["## Résumé", cr.resume, "", "## Décisions"]
    lignes += [f"- {d}" for d in cr.decisions] or ["- aucune"]
    lignes += ["", "## Actions", "| Tâche | Responsable | Échéance |", "| --- | --- | --- |"]
    lignes += [f"| {a.tache} | {a.responsable} | {a.echeance} |" for a in cr.actions]
    return "\n".join(lignes)


def resume_stream(client, transcription: str) -> str:
    """Affiche le résumé morceau par morceau ; renvoie le texte complet."""
    def lancer():
        # La requête part à la première itération : on réessaie donc toute la boucle.
        # Limite connue : une coupure en plein flux réaffiche le début ; reprendre au morceau près si gênant.
        texte = ""
        for chunk in client.models.generate_content_stream(
                model=MODEL, contents=f"Transcription :\n{transcription}\n\nRésume en 5 lignes.",
                config=config()):
            print(chunk.text or "", end="", flush=True)
            texte += chunk.text or ""
        return texte

    texte = avec_reessais(lancer)
    print()
    return texte


def tokens(client, transcription: str) -> int:
    r = avec_reessais(lambda: client.models.count_tokens(model=MODEL, contents=transcription))
    return r.total_tokens


def chat(client, transcription: str, entrees=sys.stdin) -> None:
    session = client.chats.create(model=MODEL, config=config(), history=[
        types.Content(role="user", parts=[types.Part(text=f"Transcription :\n{transcription}")]),
        types.Content(role="model", parts=[types.Part(text="Transcription reçue. Posez vos questions.")]),
    ])
    print("Posez vos questions (ligne vide pour quitter).")
    for question in entrees:
        if not question.strip():
            break
        r = avec_reessais(lambda: session.send_message(question.strip()))
        print(f"> {question.strip()}\n{r.text.strip()}\n")


def main(argv=None) -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Assistant de réunion (Gemini)")
    p.add_argument("commande", choices=["resume", "tokens", "chat"])
    p.add_argument("fichier", help="transcription de la réunion (.txt)")
    p.add_argument("--stream", action="store_true", help="résumé en streaming")
    args = p.parse_args(argv)
    with open(args.fichier, encoding="utf-8") as f:
        transcription = f.read()

    client = make_client()
    print(f"[mode : {mode()} | modèle : {MODEL}]", file=sys.stderr)
    if args.commande == "tokens":
        n = tokens(client, transcription)
        print(f"{n} tokens en entrée, soit environ {n * PRIX_ENTREE_1M / 1e6:.6f} $ avant la réponse")
    elif args.commande == "chat":
        chat(client, transcription)
    elif args.stream:
        resume_stream(client, transcription)
    else:
        cr, dollars = compte_rendu(client, transcription)
        print(en_markdown(cr))
        print(f"\n[coût estimé : {dollars:.6f} $]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
