"""Écrit 5 contrats FICTIFS (texte brut structuré en articles et clauses) dans contrats/.

Usage : python make_contracts.py [dossier]   (défaut : contrats)
Toutes les sociétés et personnes sont imaginaires.
"""
import sys
from pathlib import Path

CONTRATS = [
    {"fichier": "CT-2024-031-location-entrepot.txt", "titre": "CONTRAT DE LOCATION D'ENTREPÔT",
     "ref": "CT-2024-031", "type": "location", "date": "2024-06-03",
     "parties": ["Atelier Nova", "SCI Les Tilleuls"],
     "articles": [
         ("Objet", ["Le bailleur, SCI Les Tilleuls, loue au preneur, Atelier Nova, un entrepôt de 850 m² situé zone des Pins, lot 12."]),
         ("Durée", ["Le contrat est conclu pour une durée de neuf (9) ans à compter du 1er juillet 2024."]),
         ("Loyer", ["Le loyer est fixé à 3 200 euros hors taxes par mois, payable d'avance le 1er de chaque mois.",
                    "Le loyer est révisé chaque année selon l'indice des loyers des activités tertiaires."]),
         ("Résiliation", ["Le preneur peut donner congé à l'expiration de chaque période triennale, avec un préavis de six (6) mois.",
                          "Le congé est notifié par lettre recommandée avec accusé de réception."]),
         ("Assurance", ["Le preneur assure les locaux contre l'incendie, le dégât des eaux et le vol, et en justifie chaque année."]),
         ("Loi applicable et juridiction", ["Le contrat est soumis au droit français. Tout litige relève du tribunal judiciaire de Nantes."]),
     ]},
    {"fichier": "CT-2025-014-maintenance-logiciel.txt", "titre": "CONTRAT DE PRESTATION DE SERVICES",
     "ref": "CT-2025-014", "type": "prestation", "date": "2025-03-12",
     "parties": ["Atelier Nova", "DataPlume SAS"],
     "articles": [
         ("Objet", ["DataPlume SAS assure la maintenance corrective et évolutive du logiciel de gestion de production d'Atelier Nova."]),
         ("Durée", ["Le contrat prend effet le 1er avril 2025 pour une durée de vingt-quatre (24) mois, sans reconduction tacite."]),
         ("Prix et paiement", ["La prestation est facturée 4 800 euros hors taxes par mois.",
                               "Les factures sont payables à trente (30) jours fin de mois. Tout retard entraîne des pénalités au taux de trois fois le taux d'intérêt légal."]),
         ("Niveaux de service", [
             "Une anomalie bloquante est prise en charge en moins de quatre (4) heures ouvrées et corrigée en moins de deux (2) jours ouvrés.",
             "Une anomalie mineure est corrigée dans la version suivante, au plus tard sous trente (30) jours.",
             "Si le délai de prise en charge d'une anomalie bloquante est dépassé plus de deux fois dans un mois, une pénalité de 5 % de la redevance mensuelle est appliquée.",
             "Un rapport mensuel présente le nombre d'anomalies ouvertes, corrigées et en attente, ainsi que les délais constatés.",
             "Les pénalités sont plafonnées à 15 % de la redevance mensuelle et constituent une indemnité forfaitaire.",
         ]),
         ("Résiliation", ["Chaque partie peut résilier le contrat par lettre recommandée avec un préavis de trois (3) mois.",
                          "En cas de manquement grave non corrigé dans les quinze (15) jours suivant une mise en demeure, la résiliation est immédiate."]),
         ("Responsabilité", ["La responsabilité de DataPlume SAS est limitée au montant des sommes perçues au cours des douze (12) derniers mois."]),
         ("Confidentialité", ["Les parties gardent confidentielles les informations échangées pendant le contrat et trois (3) ans après sa fin."]),
         ("Loi applicable et juridiction", ["Le contrat est soumis au droit français. Tout litige relève du tribunal de commerce de Lyon."]),
     ]},
    {"fichier": "CT-2025-022-nettoyage-locaux.txt", "titre": "CONTRAT DE PRESTATION DE SERVICES",
     "ref": "CT-2025-022", "type": "prestation", "date": "2025-05-20",
     "parties": ["Atelier Nova", "Clairéclat Services"],
     "articles": [
         ("Objet", ["Clairéclat Services assure le nettoyage des bureaux et de l'atelier d'Atelier Nova, cinq jours par semaine."]),
         ("Durée", ["Le contrat est conclu pour douze (12) mois à compter du 1er juin 2025 et se renouvelle par tacite reconduction pour des périodes de douze mois."]),
         ("Prix et paiement", ["Le forfait mensuel est de 1 150 euros hors taxes. Les factures sont payables à quarante-cinq (45) jours."]),
         ("Résiliation", ["Chaque partie peut résilier le contrat avec un préavis d'un (1) mois, par lettre recommandée ou par courriel avec accusé de lecture."]),
         ("Responsabilité", ["Clairéclat Services est responsable des dommages causés par son personnel et justifie d'une assurance de responsabilité civile professionnelle."]),
         ("Loi applicable et juridiction", ["Le contrat est soumis au droit français. Tout litige relève du tribunal de commerce de Lyon."]),
     ]},
    {"fichier": "CT-2025-040-licence-logiciel.txt", "titre": "CONTRAT DE LICENCE DE LOGICIEL",
     "ref": "CT-2025-040", "type": "licence", "date": "2025-09-01",
     "parties": ["Atelier Nova", "Kerlogic"],
     "articles": [
         ("Objet", ["Kerlogic concède à Atelier Nova une licence d'utilisation non exclusive du logiciel de conception KerCAD pour 25 postes."]),
         ("Durée", ["La licence est concédée pour un (1) an à compter du 1er septembre 2025, renouvelable par tacite reconduction."]),
         ("Redevance", ["La redevance annuelle est de 15 000 euros hors taxes, payable à la signature puis à chaque date anniversaire."]),
         ("Résiliation", ["Chaque partie peut s'opposer au renouvellement en respectant un préavis de soixante (60) jours avant la date anniversaire."]),
         ("Responsabilité", ["La responsabilité de Kerlogic est plafonnée au montant de la redevance annuelle. Kerlogic ne répond pas des pertes de données."]),
         ("Loi applicable et juridiction", ["Le contrat est soumis au droit français. Tout litige relève du tribunal de commerce de Rennes."]),
     ]},
    {"fichier": "CT-2025-041-accord-confidentialite.txt", "titre": "ACCORD DE CONFIDENTIALITÉ",
     "ref": "CT-2025-041", "type": "confidentialite", "date": "2025-02-10",
     "parties": ["Atelier Nova", "DataPlume SAS"],
     "articles": [
         ("Objet", ["Le présent accord encadre l'échange d'informations confidentielles préalable au contrat de maintenance."]),
         ("Informations confidentielles", ["Sont confidentiels les plans, codes sources, données de production et conditions commerciales échangés entre les parties."]),
         ("Durée", ["Les obligations de confidentialité s'appliquent pendant cinq (5) ans à compter de la signature."]),
         ("Restitution", ["À la fin de l'accord, chaque partie restitue ou détruit les informations reçues dans un délai de quinze (15) jours."]),
         ("Loi applicable et juridiction", ["Le présent accord est soumis au droit français. Tout litige relève du tribunal de commerce de Lyon."]),
     ]},
]


def render(c: dict) -> str:
    lines = [c["titre"], f"Référence : {c['ref']}", f"Type : {c['type']}",
             f"Parties : {' ; '.join(c['parties'])}", f"Date de signature : {c['date']}", ""]
    for n, (titre, clauses) in enumerate(c["articles"], start=1):
        lines.append(f"Article {n} – {titre}")
        lines += [f"{n}.{i} {clause}" for i, clause in enumerate(clauses, start=1)]
        lines.append("")
    return "\n".join(lines)


def build(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for c in CONTRATS:
        p = out_dir / c["fichier"]
        p.write_text(render(c), encoding="utf-8")
        paths.append(p)
    return paths


if __name__ == "__main__":
    for p in build(Path(sys.argv[1] if len(sys.argv) > 1 else "contrats")):
        print("écrit", p)
