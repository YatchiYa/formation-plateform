"""Factures PDF -> JSON validé -> contrôles de cohérence -> écritures comptables CSV.

    python generer_factures.py      # crée factures/*.pdf (fictives)
    python factures.py              # traite factures/*.pdf, écrit sortie/
"""
import asyncio
import csv
import json
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field
from pypdf import PdfReader

load_dotenv()
ICI = Path(__file__).resolve().parent
TAUX_TVA_FR = {0.0, 2.1, 5.5, 10.0, 20.0}
TOLERANCE = 0.01  # euro : écarts d'arrondi acceptés


# 1. Le contrat de sortie : ce que le modèle DOIT renvoyer (validé par pydantic)
class Ligne(BaseModel):
    designation: str
    quantite: float
    prix_unitaire_ht: float
    montant_ht: float


class Facture(BaseModel):
    numero: str = Field(description="numéro de facture tel qu'imprimé")
    fournisseur: str
    date_facture: date = Field(description="format AAAA-MM-JJ")
    date_echeance: date | None = Field(description="null si absente du document")
    lignes: list[Ligne]
    total_ht: float = Field(description="total HT IMPRIMÉ sur la facture, sans le recalculer")
    taux_tva: float = Field(description="en pourcentage, ex. 20 pour 20 %")
    montant_tva: float = Field(description="montant de TVA IMPRIMÉ")
    total_ttc: float = Field(description="total TTC IMPRIMÉ")
    devise: str = "EUR"


extracteur = Agent(
    name="extracteur_factures",
    model=os.environ.get("MODEL", "gemini-3.5-flash"),
    instruction="Tu extrais les données d'une facture à partir de son texte. Recopie les montants "
                "EXACTEMENT comme ils sont imprimés, même s'ils te semblent faux : un contrôle "
                "automatique vérifiera la cohérence ensuite. N'invente aucune valeur.",
    output_schema=Facture,   # réponse JSON contrainte + validée
    output_key="facture",    # le JSON validé est rangé dans session.state["facture"]
)


# 2. Contrôles déterministes : du code, pas du LLM
def controler(f: Facture, aujourdhui: date) -> tuple[list[str], list[str]]:
    """Renvoie (anomalies bloquantes, alertes)."""
    bloquantes, alertes = [], []
    for l in f.lignes:
        if abs(l.quantite * l.prix_unitaire_ht - l.montant_ht) > TOLERANCE:
            bloquantes.append(f"ligne « {l.designation} » : {l.quantite} x {l.prix_unitaire_ht} != {l.montant_ht}")
    somme = round(sum(l.montant_ht for l in f.lignes), 2)
    if abs(somme - f.total_ht) > TOLERANCE:
        bloquantes.append(f"total HT imprimé {f.total_ht:.2f} != somme des lignes {somme:.2f}")
    if f.taux_tva not in TAUX_TVA_FR:
        bloquantes.append(f"taux de TVA inattendu : {f.taux_tva} %")
    tva_attendue = round(f.total_ht * f.taux_tva / 100, 2)
    if abs(tva_attendue - f.montant_tva) > TOLERANCE:
        bloquantes.append(f"TVA imprimée {f.montant_tva:.2f} != {f.taux_tva:g} % du HT ({tva_attendue:.2f})")
    if abs(f.total_ht + f.montant_tva - f.total_ttc) > TOLERANCE:
        bloquantes.append(f"TTC {f.total_ttc:.2f} != HT + TVA ({f.total_ht + f.montant_tva:.2f})")
    if f.date_echeance is None:
        alertes.append("date d'échéance absente")
    elif f.date_echeance < f.date_facture:
        bloquantes.append("échéance antérieure à la date de facture")
    elif f.date_echeance < aujourdhui:
        alertes.append(f"échéance dépassée depuis le {f.date_echeance.isoformat()}")
    return bloquantes, alertes


# 3. Écritures comptables (journal des achats, plan comptable général français)
def ecritures(f: Facture) -> list[dict]:
    base = {"journal": "HA", "date": f.date_facture.isoformat(), "piece": f.numero,
            "libelle": f"{f.fournisseur} {f.numero}"}
    return [{**base, "compte": "607000", "debit": f"{f.total_ht:.2f}", "credit": ""},      # achats HT
            {**base, "compte": "445660", "debit": f"{f.montant_tva:.2f}", "credit": ""},   # TVA déductible
            {**base, "compte": "401000", "debit": "", "credit": f"{f.total_ttc:.2f}"}]     # fournisseur TTC


def texte_pdf(chemin: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(chemin).pages)


async def extraire(runner: InMemoryRunner, texte: str) -> Facture:
    for essai in range(4):
        try:
            s = await runner.session_service.create_session(app_name="factures", user_id="compta")
            msg = types.Content(role="user", parts=[types.Part(text=texte)])
            async for _ in runner.run_async(user_id="compta", session_id=s.id, new_message=msg):
                pass
            s = await runner.session_service.get_session(app_name="factures", user_id="compta", session_id=s.id)
            return Facture.model_validate(s.state["facture"])
        except Exception as e:
            if essai == 3 or not any(c in str(e) for c in ("429", "503", "UNAVAILABLE")):
                raise
            await asyncio.sleep(10 * (essai + 1))


async def traiter(dossier: Path, sortie: Path, aujourdhui: date, runner: InMemoryRunner | None = None) -> list[dict]:
    runner = runner or InMemoryRunner(agent=extracteur, app_name="factures")
    sortie.mkdir(exist_ok=True)
    bilan, journal = [], []
    for pdf in sorted(dossier.glob("*.pdf")):
        f = await extraire(runner, texte_pdf(pdf))
        bloquantes, alertes = controler(f, aujourdhui)
        (sortie / f"{pdf.stem}.json").write_text(f.model_dump_json(indent=2), encoding="utf-8")
        if not bloquantes:
            journal += ecritures(f)  # seules les factures cohérentes partent en comptabilité
        bilan.append({"fichier": pdf.name, "numero": f.numero, "total_ttc": f.total_ttc,
                      "statut": "a_verifier" if bloquantes else "comptabilisee",
                      "anomalies": bloquantes, "alertes": alertes})
    with open(sortie / "ecritures.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["journal", "date", "piece", "compte", "libelle", "debit", "credit"],
                           delimiter=";")
        w.writeheader()
        w.writerows(journal)
    (sortie / "anomalies.json").write_text(json.dumps(bilan, ensure_ascii=False, indent=2), encoding="utf-8")
    return bilan


if __name__ == "__main__":
    for b in asyncio.run(traiter(ICI / "factures", ICI / "sortie", date.today())):
        print(f"{b['numero']:<12} {b['statut']:<14} {'; '.join(b['anomalies'] + b['alertes']) or 'OK'}")
