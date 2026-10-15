"""Assistant de rédaction de fiches produit : le prototype Google AI Studio, en Python.

Usage :
    python fiche_produit.py "Gourde isotherme 500 ml, inox, garde le froid 24 h"
    python fiche_produit.py --fichier produits.txt      # une description par ligne

La clé est lue dans GEMINI_API_KEY (ou GOOGLE_API_KEY), depuis l'environnement ou un .env.
"""
import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

MODEL = os.environ.get("MODEL", "gemini-3.5-flash")

# 1. Le prompt système, copié depuis le champ « System instructions » d'AI Studio.
SYSTEM_INSTRUCTION = """Tu es rédacteur e-commerce pour une boutique en ligne française.
À partir d'une description brute, tu rédiges une fiche produit :
- un titre de 70 caractères maximum, sans majuscules partout ;
- une accroche d'une phrase ;
- une description de 2 à 3 phrases, ton chaleureux et précis ;
- 3 à 5 points forts courts ;
- 3 à 6 mots-clés en minuscules pour le référencement.
N'invente AUCUNE caractéristique absente de la description (dimensions, matière, garantie...).
Si une information manque, n'en parle pas."""

# 2. Les exemples (« few-shot ») : une entrée et la sortie idéale attendue.
EXEMPLES = [
    (
        "Tasse céramique 350 ml, émail mat vert sauge, passe au lave-vaisselle",
        {
            "titre": "Tasse en céramique 350 ml, émail mat vert sauge",
            "accroche": "Votre boisson chaude préférée mérite une jolie tasse.",
            "description": "Cette tasse en céramique de 350 ml arbore un émail mat vert sauge "
                           "doux au toucher. Elle passe au lave-vaisselle pour un entretien sans effort.",
            "points_forts": ["Contenance 350 ml", "Émail mat vert sauge", "Compatible lave-vaisselle"],
            "mots_cles": ["tasse", "céramique", "vert sauge", "mug"],
        },
    ),
]


# 3. Le schéma de sortie, équivalent du « Structured output » d'AI Studio.
class FicheProduit(BaseModel):
    titre: str = Field(description="70 caractères maximum")
    accroche: str
    description: str
    points_forts: list[str]
    mots_cles: list[str]


# 4. Les paramètres du panneau « Run settings ».
def reglages_echantillonnage() -> dict:
    """Température et top-p, seulement si TEMPERATURE / TOP_P sont définies.
    Gemini 3.6+ les ignore ; pour Gemini 3 et 3.5, la doc conseille les valeurs par défaut."""
    noms = {"temperature": "TEMPERATURE", "top_p": "TOP_P"}
    return {cle: float(os.environ[var]) for cle, var in noms.items() if os.environ.get(var)}


def build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        max_output_tokens=4096,  # plafond de la réponse, pensée comprise
        **reglages_echantillonnage(),
        response_mime_type="application/json",
        response_schema=FicheProduit,
    )


def build_contents(description: str) -> list[types.Content]:
    """Les exemples deviennent des tours user/model, puis vient la vraie demande."""
    contents = []
    for entree, sortie in EXEMPLES:
        contents.append(types.Content(role="user", parts=[types.Part(text=entree)]))
        contents.append(types.Content(role="model", parts=[
            types.Part(text=json.dumps(sortie, ensure_ascii=False))]))
    contents.append(types.Content(role="user", parts=[types.Part(text=description)]))
    return contents


def rediger_fiche(client, description: str, essais: int = 4) -> FicheProduit:
    """Appelle Gemini et renvoie une fiche validée. Réessaie sur 429 / 5xx."""
    description = description.strip()
    if not description:
        raise ValueError("Description vide")
    for essai in range(essais):
        try:
            response = client.models.generate_content(
                model=MODEL, contents=build_contents(description), config=build_config())
            return FicheProduit.model_validate_json(response.text)
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or essai == essais - 1:
                raise
            time.sleep(2 ** essai * 5)  # 5 s, 10 s, 20 s


def main(argv=None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Rédige des fiches produit avec Gemini")
    parser.add_argument("description", nargs="?", help="description brute du produit")
    parser.add_argument("--fichier", help="fichier texte : une description par ligne")
    args = parser.parse_args(argv)
    if args.fichier:
        with open(args.fichier, encoding="utf-8") as f:
            descriptions = [ligne for ligne in f if ligne.strip()]
    elif args.description:
        descriptions = [args.description]
    else:
        parser.error("donnez une description ou --fichier")

    client = genai.Client()  # lit GEMINI_API_KEY ou GOOGLE_API_KEY
    fiches = [rediger_fiche(client, d).model_dump() for d in descriptions]
    json.dump(fiches, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
