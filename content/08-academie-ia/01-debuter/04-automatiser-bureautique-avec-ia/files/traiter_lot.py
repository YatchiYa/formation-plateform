"""Trie un lot d'e-mails (CSV ou Excel) avec Gemini, sans jamais rien envoyer.

    python traiter_lot.py emails.csv                 # -> emails_traite.csv
    python traiter_lot.py emails.xlsx --limite 5     # Excel accepté (openpyxl)
    python traiter_lot.py emails_traite.csv          # reprend : seules les lignes sans statut sont traitées

Ajoute les colonnes resume, categorie, priorite, brouillon_reponse, statut.
statut = « à valider » (ou « à relire en priorité ») : un humain relit avant toute action.
"""
import argparse
import os
import time
from pathlib import Path
from typing import Literal

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
MODEL = os.environ.get("MODEL", "gemini-3.5-flash-lite")  # modèle « volume » : moins cher par ligne
COLONNES_IA = ["resume", "categorie", "priorite", "brouillon_reponse", "statut"]


class Analyse(BaseModel):
    resume: str
    categorie: Literal["commande", "facturation", "reclamation", "rendez-vous", "information",
                       "fournisseur", "spam", "autre"]
    priorite: Literal["haute", "normale", "basse"]
    brouillon_reponse: str


PROMPT = """Tu tries la boîte de réception d'un atelier de mobilier.
Pour l'e-mail ci-dessous :
- resume : une phrase de 20 mots maximum ;
- categorie et priorite (haute = client mécontent, menace d'avis/remboursement, ou échéance sous 48 h) ;
- brouillon_reponse : 2 à 3 phrases polies, sans promettre de remboursement ni de date.
N'invente aucune information absente de l'e-mail.

Objet : {objet}
Texte : {texte}"""


def statut_pour(a: Analyse) -> str:
    """Règle déterministe : les cas sensibles passent en tête de la file de relecture."""
    if a.priorite == "haute" or a.categorie in ("reclamation", "autre"):
        return "à relire en priorité"
    return "à valider"


def lire(chemin: Path) -> pd.DataFrame:
    df = pd.read_excel(chemin) if chemin.suffix in (".xlsx", ".xls") else pd.read_csv(chemin)
    for c in COLONNES_IA:
        if c not in df.columns:
            df[c] = ""
    return df.fillna("").astype({c: str for c in COLONNES_IA})


def ecrire(df: pd.DataFrame, chemin: Path):
    df.to_excel(chemin, index=False) if chemin.suffix in (".xlsx", ".xls") else df.to_csv(chemin, index=False)


def analyser(client, objet, texte, essais=4) -> Analyse:
    from google.genai import errors, types
    config = types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json",
                                         response_schema=Analyse)
    for i in range(essais):
        try:
            r = client.models.generate_content(model=MODEL, contents=PROMPT.format(objet=objet, texte=texte),
                                               config=config)
            return Analyse.model_validate_json(r.text)
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == essais - 1:
                raise
            time.sleep(5 * 2 ** i)


def traiter(df: pd.DataFrame, client, limite=None, sauvegarder=None) -> int:
    """Traite les lignes sans statut. sauvegarder(df) est appelé après chaque ligne : rien n'est perdu en cas d'arrêt."""
    a_faire = df.index[df["statut"] == ""][:limite]
    for n, i in enumerate(a_faire, 1):
        try:
            a = analyser(client, df.at[i, "objet"], df.at[i, "texte"])
            df.loc[i, COLONNES_IA] = [a.resume, a.categorie, a.priorite, a.brouillon_reponse, statut_pour(a)]
        except Exception as e:  # une ligne en échec ne bloque pas le lot
            df.at[i, "statut"] = f"erreur : {type(e).__name__}"
        print(f"[{n}/{len(a_faire)}] ligne {df.at[i, 'id']} -> {df.at[i, 'categorie']} / {df.at[i, 'statut']}")
        if sauvegarder:
            sauvegarder(df)
    return len(a_faire)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("fichier", type=Path)
    p.add_argument("--limite", type=int, help="nombre maximum de lignes à traiter (pour tester)")
    args = p.parse_args()
    from google import genai
    client = genai.Client()  # lit GOOGLE_API_KEY / GEMINI_API_KEY
    entree = args.fichier
    sortie = entree if entree.stem.endswith("_traite") else entree.with_name(f"{entree.stem}_traite{entree.suffix}")
    df = lire(entree)
    nb = traiter(df, client, args.limite, sauvegarder=lambda d: ecrire(d, sortie))
    ecrire(df, sortie)
    print(f"{nb} ligne(s) traitée(s) -> {sortie}")
    print(df["statut"].value_counts().to_string())
