"""Génère 3 PDF fictifs (entreprise imaginaire « Atelier Nova ») dans docs/.

Usage : python make_pdfs.py [dossier]   (défaut : docs)
"""
import sys
from pathlib import Path

from reportlab import rl_config
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

rl_config.invariant = 1  # PDF identiques octet pour octet d'une génération à l'autre (pas de date)

# Chaque document = liste de pages ; chaque page = (titre, [paragraphes]).
DOCS = {
    "guide-accueil.pdf": [
        ("Bienvenue chez Atelier Nova", [
            "Atelier Nova est une entreprise fictive de 40 personnes qui conçoit du mobilier de bureau. "
            "Ce guide présente l'organisation et les règles pratiques pour les nouveaux arrivants.",
            "Les bureaux sont ouverts de 7 h 30 à 20 h du lundi au vendredi. Le badge d'accès est remis "
            "le premier jour par l'équipe des services généraux, au 2e étage.",
        ]),
        ("Outils informatiques", [
            "Votre ordinateur portable est préparé par le support informatique. Le mot de passe initial "
            "doit être changé dès la première connexion et comporter au moins 14 caractères.",
            "Pour toute panne, ouvrez un ticket sur le portail interne « Aide Nova ». Le délai de prise "
            "en charge visé est de 4 heures ouvrées pour une panne bloquante.",
        ]),
        ("Vie pratique", [
            "La cantine est ouverte de 11 h 45 à 14 h. Le repas est subventionné à hauteur de 60 % par l'entreprise.",
            "Les places de parking sont attribuées par tirage au sort chaque trimestre. Un local à vélos "
            "sécurisé de 30 places est disponible au sous-sol.",
        ]),
    ],
    "politique-teletravail.pdf": [
        ("Politique de télétravail", [
            "Tout salarié en CDI ayant terminé sa période d'essai peut demander à télétravailler. "
            "La demande se fait auprès du manager via le formulaire RH-12.",
            "Le télétravail est limité à 2 jours par semaine. Le mardi est un jour de présence obligatoire "
            "pour toutes les équipes.",
        ]),
        ("Équipement et indemnité", [
            "L'entreprise fournit un écran et un casque pour le domicile. Une indemnité forfaitaire de "
            "30 euros par mois couvre les frais de connexion et d'électricité.",
            "Le salarié atteste disposer d'une assurance habitation couvrant l'activité professionnelle.",
        ]),
    ],
    "notes-de-frais.pdf": [
        ("Procédure des notes de frais", [
            "Les notes de frais sont saisies dans l'application Dépenses avant le 5 du mois suivant. "
            "Chaque dépense doit être accompagnée d'un justificatif photographié.",
            "Le remboursement intervient sur la paie du mois suivant la validation par le manager.",
        ]),
        ("Plafonds de remboursement", [
            "Le plafond d'un repas d'affaires est de 25 euros par personne. L'hôtel est remboursé jusqu'à "
            "120 euros la nuit à Paris et 90 euros en province.",
            "Les trajets en train se font en seconde classe, sauf trajet de plus de 3 heures où la "
            "première classe est autorisée.",
        ]),
        ("Kilométrage", [
            "L'usage d'un véhicule personnel est remboursé selon le barème kilométrique en vigueur, "
            "sur présentation d'un ordre de mission signé.",
        ]),
    ],
}


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    paths = []
    for name, pages in DOCS.items():
        story = []
        for i, (title, paragraphs) in enumerate(pages):
            if i:
                story.append(PageBreak())
            story += [Paragraph(title, styles["Heading1"]), Spacer(1, 12)]
            story += [Paragraph(p, styles["BodyText"]) for p in paragraphs]
        path = out_dir / name
        SimpleDocTemplate(str(path), pagesize=A4).build(story)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for p in build(Path(sys.argv[1] if len(sys.argv) > 1 else "docs")):
        print("écrit", p)
