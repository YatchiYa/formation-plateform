"""Pipeline d'extraction : sortie structurée -> validation -> réparation -> revue humaine.

Extraire tout le jeu annoté :  python extraction.py jeu_annote.jsonl resultats.jsonl
"""
import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from schemas import CATALOGUE, SCHEMAS

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
SEUIL_CONFIANCE = 0.8
MAX_REPARATIONS = 1

CONSIGNES = {
    "cv": "Extrais les informations de ce CV.",
    "commande": ("Extrais la commande de cet e-mail. Références valides : "
                 f"{', '.join(sorted(CATALOGUE))}. Si le client corrige sa commande, garde la version finale."),
    "compte_rendu": "Extrais les informations de ce compte rendu de réunion.",
}
REGLES = ("Règles : n'invente rien ; un champ absent du texte vaut null (ou une liste vide) ; "
          "un champ que tu as dû deviner ou qui est ambigu va dans champs_incertains ; "
          "dates au format AAAA-MM-JJ.")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client()  # GOOGLE_API_KEY, ou Vertex AI si GOOGLE_GENAI_USE_VERTEXAI=TRUE
    return _client


def appeler(prompt: str, schema) -> str:
    """Un appel Gemini en mode JSON contraint, avec réessai sur 429/503."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=schema, temperature=0)
    for essai in range(4):
        try:
            return get_client().models.generate_content(model=MODEL, contents=prompt, config=config).text
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or essai == 3:
                raise
            time.sleep(5 * 2 ** essai)


def extraire(type_doc: str, texte: str) -> dict:
    schema = SCHEMAS[type_doc]
    prompt = f"{CONSIGNES[type_doc]}\n{REGLES}\n\n<document>\n{texte}\n</document>"
    brut = appeler(prompt, schema)
    reparations = 0
    while True:
        try:
            objet = schema.model_validate_json(brut)
            break
        except ValidationError as e:
            if reparations >= MAX_REPARATIONS:
                return {"donnees": None, "reparations": reparations, "a_revoir": True,
                        "raisons": [f"invalide après réparation : {e.errors()[0]['msg']}"]}
            reparations += 1
            # Réparation : on renvoie le JSON fautif et les erreurs exactes au modèle.
            brut = appeler(f"{prompt}\n\nTa réponse précédente :\n{brut}\n\n"
                           f"Elle viole ces règles de validation :\n{e}\n"
                           "Corrige-la en t'appuyant uniquement sur le document.", schema)
    donnees = objet.model_dump(mode="json")
    raisons = []
    if reparations:  # une réparation peut rendre valide en supprimant de l'information
        raisons.append(f"réparé {reparations} fois")
    if objet.confiance < SEUIL_CONFIANCE:
        raisons.append(f"confiance {objet.confiance} < {SEUIL_CONFIANCE}")
    if objet.champs_incertains:
        raisons.append("champs incertains : " + ", ".join(objet.champs_incertains))
    return {"donnees": donnees, "reparations": reparations, "a_revoir": bool(raisons), "raisons": raisons}


def extraire_lot(chemin_entree: str, chemin_sortie: str) -> None:
    """Traite un fichier JSONL ({id, type, texte}) et écrit un résultat par ligne."""
    with open(chemin_entree, encoding="utf-8") as f:
        docs = [json.loads(l) for l in f if l.strip()]
    with open(chemin_sortie, "w", encoding="utf-8") as sortie:
        for doc in docs:
            debut = time.monotonic()
            try:
                res = extraire(doc["type"], doc["texte"])
            except Exception as e:  # un document en échec ne bloque pas le lot
                res = {"donnees": None, "reparations": 0, "a_revoir": True, "raisons": [f"erreur : {e}"]}
            res = {"id": doc["id"], "type": doc["type"], **res,
                   "duree_s": round(time.monotonic() - debut, 1), "modele": MODEL}
            sortie.write(json.dumps(res, ensure_ascii=False) + "\n")
            print(f"{doc['id']:6} {doc['type']:13} réparations={res['reparations']} "
                  f"revue={'OUI' if res['a_revoir'] else 'non'} {'; '.join(res['raisons'])}")
    # Limite connue : séquentiel ; pour des milliers de documents, passer à l'API Batch de Gemini.


if __name__ == "__main__":
    extraire_lot(sys.argv[1] if len(sys.argv) > 1 else "jeu_annote.jsonl",
                 sys.argv[2] if len(sys.argv) > 2 else "resultats.jsonl")
