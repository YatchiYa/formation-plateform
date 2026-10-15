'''Écrit le petit projet Python FICTIF « facturo » (16 fichiers, facturation) dans projet_demo/.

Usage : python make_project.py [dossier]   (défaut : projet_demo)
'''
import sys
from pathlib import Path

FICHIERS = {
"facturo/__init__.py": '''"""facturo : petite application de facturation (projet fictif pour le lab RAG sur code)."""
__version__ = "0.4.0"
''',
"facturo/config.py": '''"""Chargement de la configuration depuis les variables d'environnement."""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    devise: str = "EUR"
    taux_tva_defaut: float = 0.20
    delai_paiement_jours: int = 30
    smtp_host: str = "localhost"
    base_path: str = "facturo.db"


def load_settings() -> Settings:
    """Lit FACTURO_DEVISE, FACTURO_DELAI, FACTURO_SMTP et FACTURO_DB ; valeurs par défaut sinon."""
    return Settings(
        devise=os.environ.get("FACTURO_DEVISE", "EUR"),
        delai_paiement_jours=int(os.environ.get("FACTURO_DELAI", "30")),
        smtp_host=os.environ.get("FACTURO_SMTP", "localhost"),
        base_path=os.environ.get("FACTURO_DB", "facturo.db"),
    )
''',
"facturo/models.py": '''"""Modèles de données : client, facture, ligne de facture."""
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Client:
    id: int
    nom: str
    email: str
    pays: str = "FR"


@dataclass
class LigneFacture:
    designation: str
    quantite: int
    prix_unitaire_ht: float
    categorie_tva: str = "normal"

    def montant_ht(self) -> float:
        return round(self.quantite * self.prix_unitaire_ht, 2)


@dataclass
class Facture:
    numero: str
    client: Client
    date_emission: date
    lignes: list = field(default_factory=list)
    remise_pct: float = 0.0
    payee: bool = False
    montant_paye: float = 0.0

    def total_ht(self) -> float:
        """Somme des lignes, remise déduite."""
        brut = sum(l.montant_ht() for l in self.lignes)
        return round(brut * (1 - self.remise_pct / 100), 2)

    def total_ttc(self) -> float:
        """Total toutes taxes comprises : la TVA est calculée ligne par ligne."""
        from .tva import calcul_tva, taux_tva
        tva = sum(calcul_tva(l.montant_ht(), taux_tva(l.categorie_tva)) for l in self.lignes)
        return round(self.total_ht() + tva * (1 - self.remise_pct / 100), 2)
''',
"facturo/tva.py": '''"""Taux et calcul de la TVA."""

TAUX_TVA = {"normal": 0.20, "intermediaire": 0.10, "reduit": 0.055, "super_reduit": 0.021}


def taux_tva(categorie: str) -> float:
    """Renvoie le taux de TVA d'une catégorie ; lève ValueError si la catégorie est inconnue."""
    if categorie not in TAUX_TVA:
        raise ValueError(f"Catégorie de TVA inconnue : {categorie}")
    return TAUX_TVA[categorie]


def calcul_tva(montant_ht: float, taux: float) -> float:
    """Montant de TVA arrondi au centime."""
    return round(montant_ht * taux, 2)


def autoliquidation(client_pays: str) -> bool:
    """Vrai pour un client professionnel hors de France dans l'UE : la TVA est due par le client."""
    return client_pays in {"BE", "DE", "ES", "IT", "LU", "NL"}
''',
"facturo/numerotation.py": '''"""Numérotation continue des factures : FAC-AAAA-NNNN."""
import re

MOTIF = re.compile(r"^FAC-(\\d{4})-(\\d{4})$")


def prochain_numero(annee: int, dernier: str | None) -> str:
    """Numéro suivant ; la séquence repart à 0001 au changement d'année."""
    if dernier:
        m = MOTIF.match(dernier)
        if not m:
            raise ValueError(f"Numéro invalide : {dernier}")
        if int(m.group(1)) == annee:
            return f"FAC-{annee}-{int(m.group(2)) + 1:04d}"
    return f"FAC-{annee}-0001"
''',
"facturo/remises.py": '''"""Codes promotionnels et remise de fidélité."""

CODES_PROMO = {"BIENVENUE10": 10.0, "PRINTEMPS15": 15.0}
REMISE_MAX_PCT = 25.0


def appliquer_code_promo(facture, code: str) -> float:
    """Applique un code promo à la facture et renvoie la remise totale en pourcentage."""
    if code not in CODES_PROMO:
        raise ValueError("Code promo inconnu")
    facture.remise_pct = min(facture.remise_pct + CODES_PROMO[code], REMISE_MAX_PCT)
    return facture.remise_pct


def remise_fidelite(nb_factures_payees: int) -> float:
    """5 % à partir de 10 factures payées, 8 % à partir de 25."""
    if nb_factures_payees >= 25:
        return 8.0
    if nb_factures_payees >= 10:
        return 5.0
    return 0.0
''',
"facturo/pdf_export.py": '''"""Export des factures (format texte simplifié qui tient lieu de PDF dans ce projet fictif)."""
from pathlib import Path


def rendu_texte(facture) -> str:
    lignes = [f"Facture {facture.numero} - {facture.client.nom}"]
    lignes += [f"  {l.designation} x{l.quantite} : {l.montant_ht():.2f} HT" for l in facture.lignes]
    lignes.append(f"Total TTC : {facture.total_ttc():.2f}")
    return "\\n".join(lignes)


def exporter_pdf(facture, dossier: str) -> Path:
    """Écrit la facture dans <dossier>/<numero>.pdf et renvoie le chemin."""
    chemin = Path(dossier) / f"{facture.numero}.pdf"
    chemin.write_text(rendu_texte(facture), encoding="utf-8")
    return chemin
''',
"facturo/email_sender.py": '''"""Envoi des factures par e-mail, avec nouvelles tentatives."""
import smtplib
import time
from email.message import EmailMessage

MAX_TENTATIVES = 3


def construire_message(facture, destinataire: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = f"Votre facture {facture.numero}"
    msg["To"] = destinataire
    msg.set_content(f"Bonjour {facture.client.nom}, veuillez trouver votre facture ci-jointe.")
    return msg


def envoyer_facture(facture, destinataire: str, smtp_host: str = "localhost") -> bool:
    """Envoie la facture ; réessaie jusqu'à MAX_TENTATIVES fois avec une attente croissante."""
    for tentative in range(1, MAX_TENTATIVES + 1):
        try:
            with smtplib.SMTP(smtp_host) as smtp:
                smtp.send_message(construire_message(facture, destinataire))
            return True
        except OSError:
            time.sleep(2 ** tentative)
    return False
''',
"facturo/relances.py": '''"""Relances des factures impayées."""
from datetime import date, timedelta

PALIERS_RELANCE = [7, 15, 30]  # jours de retard déclenchant une relance


def factures_en_retard(factures, aujourd_hui: date, delai_jours: int = 30) -> list:
    """Factures non payées dont l'échéance (émission + délai) est dépassée."""
    return [f for f in factures
            if not f.payee and f.date_emission + timedelta(days=delai_jours) < aujourd_hui]


def niveau_relance(jours_retard: int) -> int:
    """0 = pas de relance, 1 = rappel aimable, 2 = relance ferme, 3 = mise en demeure."""
    return sum(jours_retard >= p for p in PALIERS_RELANCE)


def planifier_relances(factures, aujourd_hui: date, delai_jours: int = 30) -> list:
    """Liste de (numéro, niveau) à envoyer aujourd'hui."""
    plan = []
    for f in factures_en_retard(factures, aujourd_hui, delai_jours):
        retard = (aujourd_hui - f.date_emission).days - delai_jours
        if niveau_relance(retard):
            plan.append((f.numero, niveau_relance(retard)))
    return plan
''',
"facturo/paiements.py": '''"""Enregistrement des paiements et rapprochement bancaire."""


class PaiementRefuse(Exception):
    pass


def enregistrer_paiement(facture, montant: float) -> None:
    """Ajoute un paiement ; la facture passe à payée quand le total TTC est atteint."""
    if montant <= 0:
        raise PaiementRefuse("Le montant doit être positif")
    facture.montant_paye = round(facture.montant_paye + montant, 2)
    if facture.montant_paye >= facture.total_ttc():
        facture.payee = True


def rapprocher(releve: list, factures: list) -> dict:
    """Associe chaque ligne du relevé bancaire (libellé, montant) à la facture dont le numéro apparaît."""
    par_numero = {f.numero: f for f in factures}
    resultat = {}
    for libelle, montant in releve:
        for numero, f in par_numero.items():
            if numero in libelle:
                resultat[numero] = montant
    return resultat
''',
"facturo/devises.py": '''"""Conversion de devises à partir d'une table de taux fournie."""


def convertir(montant: float, de: str, vers: str, taux: dict) -> float:
    """taux est un dict {"USD": 1.08, ...} exprimé pour 1 EUR."""
    if de == vers:
        return montant
    en_eur = montant if de == "EUR" else montant / taux[de]
    return round(en_eur if vers == "EUR" else en_eur * taux[vers], 2)
''',
"facturo/stockage.py": '''"""Persistance des factures dans SQLite."""
import json
import sqlite3


class DepotFactures:
    def __init__(self, chemin: str = "facturo.db"):
        self.db = sqlite3.connect(chemin)
        self.db.execute("CREATE TABLE IF NOT EXISTS factures (numero TEXT PRIMARY KEY, donnees TEXT)")

    def sauvegarder(self, numero: str, donnees: dict) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO factures VALUES (?, ?)", (numero, json.dumps(donnees)))

    def charger(self, numero: str) -> dict | None:
        row = self.db.execute("SELECT donnees FROM factures WHERE numero = ?", (numero,)).fetchone()
        return json.loads(row[0]) if row else None

    def dernier_numero(self, annee: int) -> str | None:
        """Plus grand numéro de l'année, utilisé par la numérotation."""
        row = self.db.execute("SELECT MAX(numero) FROM factures WHERE numero LIKE ?", (f"FAC-{annee}-%",)).fetchone()
        return row[0]
''',
"facturo/auth.py": '''"""Authentification des utilisateurs de l'interface d'administration."""
import hashlib
import hmac
import secrets

ITERATIONS = 200_000


def hacher_mot_de_passe(mot_de_passe: str, sel: bytes | None = None) -> tuple:
    sel = sel or secrets.token_bytes(16)
    return sel, hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode(), sel, ITERATIONS)


def verifier_mot_de_passe(mot_de_passe: str, sel: bytes, attendu: bytes) -> bool:
    """Comparaison en temps constant pour éviter les attaques temporelles."""
    return hmac.compare_digest(hacher_mot_de_passe(mot_de_passe, sel)[1], attendu)


def generer_jeton_session() -> str:
    return secrets.token_urlsafe(32)
''',
"facturo/journal.py": '''"""Configuration des journaux (logs)."""
import logging


def configurer_logs(niveau: str = "INFO") -> logging.Logger:
    logging.basicConfig(level=niveau, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    return logging.getLogger("facturo")
''',
"facturo/api.py": '''"""Points d'entrée applicatifs appelés par l'interface web."""
from datetime import date

from .models import Facture
from .numerotation import prochain_numero
from .stockage import DepotFactures


def creer_facture(depot: DepotFactures, client, lignes: list, aujourd_hui: date | None = None) -> Facture:
    """Crée une facture avec le prochain numéro libre de l'année et la sauvegarde."""
    aujourd_hui = aujourd_hui or date.today()
    numero = prochain_numero(aujourd_hui.year, depot.dernier_numero(aujourd_hui.year))
    facture = Facture(numero=numero, client=client, date_emission=aujourd_hui, lignes=lignes)
    depot.sauvegarder(numero, {"client": client.nom, "total_ttc": facture.total_ttc()})
    return facture


def annuler_facture(depot: DepotFactures, numero: str) -> None:
    """Une facture émise ne se supprime pas : on enregistre un avoir du même montant."""
    donnees = depot.charger(numero)
    if donnees is None:
        raise KeyError(numero)
    depot.sauvegarder(f"AV-{numero}", {**donnees, "total_ttc": -donnees["total_ttc"]})
''',
"facturo/cli.py": '''"""Interface en ligne de commande : python -m facturo.cli relances"""
import argparse
from datetime import date

from .config import load_settings
from .journal import configurer_logs


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="facturo")
    parser.add_argument("commande", choices=["relances", "export", "version"])
    args = parser.parse_args(argv)
    log = configurer_logs()
    settings = load_settings()
    log.info("commande %s (délai %s jours)", args.commande, settings.delai_paiement_jours)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''',
}


def build(out_dir: Path) -> list[Path]:
    paths = []
    for rel, src in FICHIERS.items():
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(src, encoding="utf-8")
        paths.append(p)
    return paths


if __name__ == "__main__":
    for p in build(Path(sys.argv[1] if len(sys.argv) > 1 else "projet_demo")):
        print("écrit", p)
