"""Génère le PDF « Gemini Enterprise : feuille de route sécurité » (projet 06)."""
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Gemini-Enterprise-Feuille-de-route-securite.pdf")
F = "/home/yarab/.local/share/fonts/Inter/extras/ttf/"
for name, file in [("Inter", "Inter-Regular"), ("Inter-Md", "Inter-Medium"), ("Inter-SB", "Inter-SemiBold"),
                   ("Inter-B", "Inter-Bold"), ("Inter-I", "Inter-Italic"), ("Inter-L", "Inter-Light")]:
    pdfmetrics.registerFont(TTFont(name, F + file + ".ttf"))
pdfmetrics.registerFontFamily("Inter", normal="Inter", bold="Inter-SB", italic="Inter-I", boldItalic="Inter-SB")

NAVY = colors.HexColor("#14213D"); INK = colors.HexColor("#1C2333"); MUTED = colors.HexColor("#4A5568")
BLUE = colors.HexColor("#2F6FDE"); SOFT = colors.HexColor("#EEF2F9"); LINE = colors.HexColor("#D9DEE6")
PAPER = colors.HexColor("#FFFFFF"); ORANGE = colors.HexColor("#C75B12"); GREEN = colors.HexColor("#1E7A4C")
LEVEL = {0: colors.HexColor("#5B6B8C"), 1: colors.HexColor("#2F6FDE"), 2: colors.HexColor("#1F4FA8"), 3: colors.HexColor("#14213D")}

W, H = A4
M = 18 * mm

st = {
    "h1": ParagraphStyle("h1", fontName="Inter-B", fontSize=21, leading=26, textColor=NAVY, spaceAfter=4),
    "kicker": ParagraphStyle("k", fontName="Inter-SB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h2": ParagraphStyle("h2", fontName="Inter-SB", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Inter-SB", fontSize=10.5, leading=14, textColor=INK, spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("b", fontName="Inter", fontSize=9.4, leading=13.6, textColor=INK, spaceAfter=5),
    "lead": ParagraphStyle("lead", fontName="Inter-L", fontSize=12, leading=17, textColor=INK, spaceAfter=8),
    "small": ParagraphStyle("s", fontName="Inter", fontSize=8, leading=11, textColor=MUTED),
    "cell": ParagraphStyle("c", fontName="Inter", fontSize=8.3, leading=11.2, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName="Inter-SB", fontSize=8.3, leading=11.2, textColor=INK),
    "th": ParagraphStyle("th", fontName="Inter-SB", fontSize=8.3, leading=11, textColor=PAPER),
    "bullet": ParagraphStyle("bl", fontName="Inter", fontSize=9.4, leading=13.6, textColor=INK, leftIndent=11, bulletIndent=0, spaceAfter=2.5),
    "banner": ParagraphStyle("bn", fontName="Inter", fontSize=9, leading=16.5, textColor=PAPER),
    "bannermeta": ParagraphStyle("bm", fontName="Inter", fontSize=8, leading=12.5, textColor=PAPER),
    "quote": ParagraphStyle("q", fontName="Inter-Md", fontSize=10.5, leading=15, textColor=NAVY),
}


def P(t, s="body"): return Paragraph(t, st[s])
def B(items): return [Paragraph(i, st["bullet"], bulletText="•") for i in items]


def table(header, rows, widths, first_bold=True, zebra=True, head_color=NAVY):
    data = [[Paragraph(h, st["th"]) for h in header]]
    for r in rows:
        data.append([Paragraph(c, st["cellb"] if (i == 0 and first_bold) else st["cell"]) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), head_color), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 4.5),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0: style.append(("BACKGROUND", (0, i), (-1, i), SOFT))
    t.setStyle(TableStyle(style))
    return t


def callout(text, color=BLUE, bg=SOFT):
    t = Table([[Paragraph(text, st["quote"])]], colWidths=[W - 2 * M])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def level_banner(n, title, subtitle, meta):
    left = Paragraph(f'<font name="Inter-B" size="30" color="#FFFFFF">{n}</font>', ParagraphStyle("lv", parent=st["body"], leading=34))
    mid = Paragraph(f'<font name="Inter-SB" size="8.5" color="#C9D3E6">NIVEAU {n}</font><br/>'
                    f'<font name="Inter-B" size="15" color="#FFFFFF">{title}</font><br/>'
                    f'<font name="Inter" size="9" color="#E3E8F2">{subtitle}</font>', st["banner"])
    right = Paragraph("<br/>".join(f'<font name="Inter" size="8" color="#E3E8F2">{m}</font>' for m in meta), st["bannermeta"])
    t = Table([[left, mid, right]], colWidths=[16 * mm, 100 * mm, W - 2 * M - 116 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), LEVEL[n]), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return t


def gate(items, title="Critères de passage au niveau suivant"):
    box = Table([[""]], colWidths=[3.2 * mm], rowHeights=[3.2 * mm])
    box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, GREEN)]))
    rows = [[Paragraph(f'<font name="Inter-SB" color="#1E7A4C">{title}</font>', st["cell"]), ""]]
    rows += [[box, Paragraph(i, st["cell"])] for i in items]
    t = Table(rows, colWidths=[8 * mm, W - 2 * M - 8 * mm])
    t.setStyle(TableStyle([("SPAN", (0, 0), (1, 0)), ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F3EC")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


# --------------------------------------------------------------------------- pages
def on_cover(c, d):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(0, 0, 9 * mm, H, fill=1, stroke=0)
    # escalier des niveaux (motif)
    for i in range(4):
        c.setFillColor(LEVEL[i] if i else colors.HexColor("#3A4A6B"))
        c.rect(W - 92 * mm + i * 20 * mm, 40 * mm, 20 * mm, (14 + i * 16) * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#C9D3E6")); c.setFont("Inter-SB", 9)
        c.drawString(W - 92 * mm + i * 20 * mm + 3 * mm, 40 * mm + (14 + i * 16) * mm - 6 * mm, f"N{i}")
    c.setFillColor(colors.HexColor("#8FB3F5")); c.setFont("Inter-SB", 10)
    c.drawString(26 * mm, H - 45 * mm, "PRÉPARÉ POUR LES ÉQUIPES ACME  ·  SÉCURITÉ · ARCHITECTURE · DATA")
    c.setFillColor(colors.HexColor("#F6F7F4")); c.setFont("Inter-B", 34)
    c.drawString(26 * mm, H - 70 * mm, "Gemini Enterprise")
    c.drawString(26 * mm, H - 84 * mm, "Feuille de route sécurité")
    c.setFont("Inter-L", 14); c.setFillColor(colors.HexColor("#C9D3E6"))
    for i, line in enumerate(["De la découverte dans la console Google Cloud",
                              "à une production industrialisée en Terraform,",
                              "niveau par niveau."]):
        c.drawString(26 * mm, H - 102 * mm - i * 7 * mm, line)
    c.setFont("Inter", 9.5)
    c.drawString(26 * mm, 30 * mm, "Version 1.0  ·  Octobre 2026  ·  Document de travail, diffusion interne")
    c.drawString(26 * mm, 24 * mm, "Socle technique de référence : projet 06-gemini-enterprise-security-baseline (Terraform)")
    c.restoreState()


def on_page(c, d):
    c.saveState()
    c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(M, H - 12 * mm, W - M, H - 12 * mm)
    c.setFont("Inter-SB", 7.5); c.setFillColor(BLUE); c.drawString(M, H - 10 * mm, "GEMINI ENTERPRISE · FEUILLE DE ROUTE SÉCURITÉ")
    c.setFont("Inter", 7.5); c.setFillColor(MUTED); c.drawRightString(W - M, H - 10 * mm, "Acme · Diffusion interne")
    c.line(M, 12 * mm, W - M, 12 * mm)
    c.drawString(M, 8 * mm, "Octobre 2026 · v1.0")
    c.drawRightString(W - M, 8 * mm, f"{d.page}")
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, title="Gemini Enterprise - Feuille de route sécurité",
                      author="Équipe projet Gemini Enterprise", subject="Sécurité Gemini Enterprise par niveaux",
                      leftMargin=M, rightMargin=M, topMargin=18 * mm, bottomMargin=18 * mm)
frame = Frame(M, 16 * mm, W - 2 * M, H - 34 * mm, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=on_cover),
                      PageTemplate(id="page", frames=[frame], onPage=on_page)])
CW = W - 2 * M
S = []
S += [NextPageTemplate("page"), PageBreak()]

# ---------------------------------------------------------------- 1. Synthèse
S += [P("SYNTHÈSE", "kicker"), P("En une page", "h1"),
      P("Gemini Enterprise donne à chaque collaborateur un assistant IA qui <b>répond à partir des outils de l'entreprise</b> : "
        "Google Workspace, Microsoft 365, GitHub, Jira, BigQuery… Sa valeur est directement liée à ce qu'il peut voir. "
        "Son risque aussi : <b>un assistant qui voit tout peut tout divulguer</b>.", "lead"),
      P("Nous proposons de déployer la sécurité <b>par niveaux</b>, comme on monte un escalier : chaque marche apporte une "
        "protection mesurable, débloque un périmètre d'usage plus large, et ne commence que lorsque la précédente est validée."),
      Spacer(1, 4),
      table(["Niveau", "Objectif", "Où", "Utilisateurs · données", "Durée indicative"], [
          ["0 · Découverte", "Comprendre la plateforme et tester les garde-fous natifs", "Console Google Cloud", "10 à 20 testeurs · données non sensibles", "1 à 2 semaines"],
          ["1 · Socle", "Poser les 6 couches de sécurité en code, sur un pilote métier", "Terraform", "Un pilote (50 à 200) · données internes", "3 à 4 semaines"],
          ["2 · Production", "Chiffrement par les clés Acme, preuves d'audit, exploitation", "Terraform + CI/CD", "Ouverture par groupes · données internes", "4 à 6 semaines"],
          ["3 · Avancé", "Agents maison, MCP, Databricks, périmètre anti-exfiltration", "Terraform + organisation", "Tous · sources étendues", "Selon besoins"],
      ], [26 * mm, 52 * mm, 30 * mm, 38 * mm, CW - 146 * mm]),
      Spacer(1, 8),
      P("Ce que cette approche apporte", "h2")]
S += B(["<b>Aller vite sans prendre de risque</b> : on teste en quelques jours dans la console, sur des données sans enjeu, "
        "pendant que le socle de production est construit en code.",
        "<b>Une sécurité démontrable</b> : chaque mesure répond à un risque nommé, se teste en recette, et laisse une trace d'audit.",
        "<b>Une sécurité qu'on ne peut pas affaiblir par erreur</b> : plancher Model Armor, séparation des rôles, alerte dès qu'un garde-fou change.",
        "<b>Conformité RGPD by design</b> : données en UE, sources interrogées sans copie, conservation minimisée, journaux réservés à la sécurité.",
        "<b>Industrialisation</b> : la même configuration Terraform, relue et versionnée, pour la recette et la production."])
S += [Spacer(1, 6), P("Décisions attendues de Acme", "h2"),
      table(["Décision", "Pourquoi maintenant", "Quand"], [
          ["Fournisseur d'identité (Google ou Entra ID)", "Choix structurant : en changer plus tard efface l'historique des conversations", "Avant le niveau 1"],
          ["Localisation (UE recommandée)", "Immuable après création ; conditionne le chiffrement CMEK", "Avant le niveau 1"],
          ["Sources du pilote", "Définit les connecteurs, les secrets et les autorisations à préparer", "Pendant le niveau 0"],
          ["Durée de conservation et journalisation du contenu", "Données personnelles de salariés : DPO, et CSE si besoin", "Avant le niveau 2"],
      ], [55 * mm, 85 * mm, CW - 140 * mm]),
      PageBreak()]

# ---------------------------------------------------------------- 2. Principes
S += [P("PRINCIPES", "kicker"), P("Six principes qui guident tous les choix", "h1"),
      P("Ces principes viennent de la pratique des déploiements cloud en entreprise. Ils évitent les deux échecs classiques : "
        "le projet bloqué par une sécurité « tout ou rien », et le pilote ouvert trop vite qu'on ne sait plus refermer.", "lead")]
for n, (t, d) in enumerate([
    ("Tester dans la console, industrialiser en code.", "La console Google Cloud permet d'activer et de comprendre les garde-fous en quelques minutes. "
     "Mais une configuration faite à la main ne se relit pas, ne se reproduit pas et dérive. Tout ce qui est validé en console "
     "est repris en Terraform avant d'atteindre des données réelles."),
    ("Mesurer avant de bloquer, puis bloquer.", "Les filtres trop stricts poussent les collaborateurs vers des IA grand public non maîtrisées, ce qui est le pire scénario. "
     "On observe (journaux, faux positifs), on règle, puis on applique. Exception : les contrôles d'identité et de données sont bloquants dès le premier jour."),
    ("Les droits de la source font foi.", "Par défaut, l'assistant interroge les sources en direct avec l'identité de l'utilisateur (mode fédéré). "
     "Chacun ne voit que ce qu'il voit déjà, et aucune copie n'existe hors de la source. Toute copie (ingestion) est une exception justifiée."),
    ("Défense en profondeur.", "Aucune mesure n'est suffisante seule. L'identité limite qui entre, les connecteurs limitent ce qui est visible, Model Armor "
     "filtre ce qui est échangé, la journalisation détecte ce qui a échappé."),
    ("Personne ne peut désactiver sa propre sécurité.", "Les administrateurs de l'assistant ne gèrent ni les filtres, ni les clés, ni les journaux sensibles. "
     "Un plancher technique interdit d'affaiblir les filtres, et toute modification déclenche une alerte."),
    ("Chaque décision est tracée et réversible.", "Les choix (seuils, conservation, journalisation) sont des variables documentées, relues en revue de code, "
     "et validées par la bonne personne : sécurité, DPO ou métier."),
], 1):
    S.append(KeepTogether([P(f'<font color="#2F6FDE">{n}.</font>  {t}', "h3"), P(d)]))
S += [Spacer(1, 6), callout("« La bonne question n'est pas : est-ce que l'IA est sûre ? C'est : qu'est-ce que l'IA peut voir, "
                            "qu'est-ce qu'on lui envoie, et comment le sait-on ? » Le reste du document répond à ces trois questions, niveau par niveau."),
      PageBreak()]

# ---------------------------------------------------------------- 3. Escalier
S += [P("VUE D'ENSEMBLE", "kicker"), P("L'escalier de sécurité", "h1"),
      P("Chaque niveau s'appuie sur le précédent. Les mesures sont cumulatives : le niveau 2 contient tout le niveau 1.", "lead")]
stairs = [
    (0, "Découverte", "Console", ["App de test en UE", "SSO Workspace", "Model Armor natif", "Recherche web coupée", "Données non sensibles"]),
    (1, "Socle", "Terraform", ["Groupes et séparation des rôles", "Model Armor + DLP France", "Connecteurs fédérés", "Secrets en coffre", "Journaux dédiés et alertes"]),
    (2, "Production", "Terraform + CI/CD", ["Clés de chiffrement Acme (CMEK)", "Preuves d'audit verrouillées", "Politiques d'organisation UE", "Revue de code obligatoire", "Exploitation et revues d'accès"]),
    (3, "Avancé", "Terraform + organisation", ["VPC Service Controls", "Agent Gateway", "Agents maison filtrés", "Databricks via MCP", "SIEM / SOC"]),
]
cols = []
for n, name, where, items in stairs:
    inner = [Paragraph(f'<font name="Inter-B" size="20" color="#FFFFFF">N{n}</font>', st["body"]),
             Paragraph(f'<font name="Inter-SB" size="11" color="#FFFFFF">{name}</font><br/><font size="8" color="#C9D3E6">{where}</font>', st["body"]),
             Spacer(1, 3)] + [Paragraph(f'<font size="8" color="#E9EEF7">• {i}</font>', st["cell"]) for i in items]
    cols.append(inner)
t = Table([cols], colWidths=[CW / 4] * 4)
t.setStyle(TableStyle([("BACKGROUND", (i, 0), (i, 0), LEVEL[i]) for i in range(4)] +
                      [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                       ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                       ("LINEAFTER", (0, 0), (2, 0), 2, PAPER)]))
S += [t, Spacer(1, 10), P("Les six couches de protection", "h2"),
      table(["Couche", "Question à laquelle elle répond", "N0", "N1", "N2", "N3"], [
          ["1 · Identité et accès", "Qui peut entrer, et qui peut changer les règles ?", "SSO", "Complet", "Revues", "Entra ID si besoin"],
          ["2 · Protection des données", "Qui contrôle le chiffrement et les secrets ?", "Google", "Secrets", "CMEK", "Org. policies"],
          ["3 · Connecteurs", "Que peut voir l'assistant, et avec quels droits ?", "1 source test", "Fédéré", "IP fixes", "MCP, Databricks"],
          ["4 · Filtrage IA", "Qu'est-ce qui entre et sort du modèle ?", "Natif", "DLP France", "Red team", "Agents maison"],
          ["5 · Exposition", "Où vont les données, que partage-t-on ?", "UE, web off", "Partages fermés", "Ouverture gouvernée", "VPC-SC"],
          ["6 · Audit et détection", "Comment le sait-on ?", "Audit", "Alertes", "Logs verrouillés", "SIEM"],
      ], [34 * mm, 52 * mm, 18 * mm, 21 * mm, 22 * mm, CW - 147 * mm]),
      Spacer(1, 8),
      callout("Pourquoi des niveaux plutôt qu'un « big bang » ? Parce que trois décisions sont <b>irréversibles</b> : la localisation de l'app, "
              "le fournisseur d'identité et l'activation du chiffrement CMEK. On les prend à froid, après avoir appris en niveau 0, "
              "et non dans l'urgence d'un lancement.", ORANGE, colors.HexColor("#FBF1EA")),
      PageBreak()]

# ---------------------------------------------------------------- 4. Niveau 0
S += [level_banner(0, "Découverte : tester directement dans la console Google Cloud",
                   "Comprendre la plateforme, éprouver les garde-fous natifs, sans enjeu de données.",
                   ["Où : console Google Cloud", "Qui : 10 à 20 testeurs", "Données : non sensibles", "Durée : 1 à 2 semaines"]),
      Spacer(1, 8), P("Pourquoi commencer par la console", "h2"),
      P("Gemini Enterprise est un service managé : l'essentiel des garde-fous s'active en quelques clics. Commencer par la console "
        "permet aux équipes sécurité et métier de <b>voir</b> concrètement ce que fait chaque réglage avant de le figer en code. "
        "C'est aussi le moyen le plus rapide d'obtenir des retours d'usage réels pour cadrer le pilote."),
      P("Ce que l'on active, et où", "h2"),
      table(["Mesure", "Pourquoi", "Où dans la console"], [
          ["Projet de découverte dédié", "Isoler les essais ; il sera supprimé ensuite", "Resource Manager → Nouveau projet (dans l'organisation)"],
          ["App Gemini Enterprise en <b>UE</b>", "Habituer tout le monde au choix de résidence européenne", "Gemini Enterprise → Créer une app → Localisation : EU"],
          ["Identité Google Workspace (SSO)", "Aucun compte local, double authentification de l'annuaire", "Gemini Enterprise → Paramètres → Identité"],
          ["Licences d'essai, groupe de testeurs", "Périmètre maîtrisé et nominatif", "Gemini Enterprise → Abonnements ; IAM → groupe"],
          ["Un connecteur Google Drive <b>fédéré</b> sur un dossier de test", "Vérifier que les droits Drive sont respectés", "App → Data stores → Google Drive"],
          ["Model Armor sur l'assistant", "Voir les blocages (injection, données sensibles)", "Security → Model Armor → Templates (région EU), puis App → Configurations"],
          ["Recherche web publique désactivée", "Aucune question ne part vers un moteur public", "App → Configurations → Assistant"],
          ["Journaux d'accès aux données", "Premières traces d'audit", "IAM → Journaux d'audit → Discovery Engine, Model Armor"],
      ], [50 * mm, 55 * mm, CW - 105 * mm]),
      Spacer(1, 6), P("Ce que l'on teste ensemble", "h2")]
S += B(["Un testeur ne retrouve pas un document Drive qui ne lui est pas partagé.",
        "« Ignore tes instructions… », un numéro de carte de test ou un lien malveillant sont bloqués.",
        "Les réponses citent leurs sources ; la qualité est jugée sur des cas d'usage réels du métier.",
        "On observe les faux positifs de Model Armor sur le vocabulaire Acme (produits, sports, références)."])
S += [Spacer(1, 4),
      callout("Règle d'or du niveau 0 : <b>aucune donnée personnelle ou confidentielle</b>. L'app de découverte est jetable : "
              "elle n'a pas le chiffrement CMEK, qui doit être activé <b>avant</b> la création de l'app de production.", ORANGE, colors.HexColor("#FBF1EA")),
      Spacer(1, 6),
      gate(["Les 4 décisions structurantes sont prises (identité, localisation, sources du pilote, conservation).",
            "Les tests ci-dessus sont passés et les faux positifs sont documentés.",
            "L'inventaire des réglages faits en console est établi, pour être repris en Terraform."]),
      PageBreak()]

# ---------------------------------------------------------------- 5. Niveau 1
S += [level_banner(1, "Socle : les six couches en code, sur un pilote métier",
                   "Rejouer en Terraform ce qui a été validé, et ajouter ce que la console ne fait pas bien.",
                   ["Où : Terraform (projet 06)", "Qui : un pilote de 50 à 200", "Données : internes", "Durée : 3 à 4 semaines"]),
      Spacer(1, 8), P("Pourquoi passer au code maintenant", "h2"),
      P("Dès que de vraies données entrent en jeu, la configuration doit être <b>relue, reproductible et traçable</b>. Terraform "
        "décrit l'état attendu ; toute modification passe par une revue de code ; l'historique Git devient la preuve d'audit. "
        "Le socle livré (projet 06) couvre les six couches et a été conçu pour ce pilote."),
      P("Les mesures du socle", "h2"),
      table(["Couche", "Mesure", "Pourquoi", "Fichier"], [
          ["1 Identité", "4 groupes : utilisateurs, admins, pilotage, sécurité", "Revue d'accès simple ; un départ coupe l'accès", "10_identity_access.tf"],
          ["1 Identité", "Séparation des rôles", "Les admins de l'app ne touchent ni filtres, ni clés, ni journaux", "10_identity_access.tf"],
          ["2 Données", "Secrets des connecteurs dans Secret Manager", "Aucun mot de passe dans le code ; rotation sans redéploiement", "20_data_protection.tf"],
          ["2 Données", "Conversations conservées 30 jours (60 par défaut)", "Minimisation RGPD", "50_app.tf"],
          ["3 Connecteurs", "Modèle générique, <b>fédéré</b> par défaut", "Droits natifs de la source, aucune copie", "40_connectors.tf"],
          ["3 Connecteurs", "IP sortantes fixes autorisées côté SaaS", "Seul Gemini Enterprise peut appeler la source", "40_connectors.tf"],
          ["4 Filtrage", "Model Armor entrée + sortie, <b>FAIL_CLOSED</b>", "Jamais de réponse non filtrée", "30_ai_guardrails.tf"],
          ["4 Filtrage", "Détecteurs français : NIR, CNI, passeport, IBAN, carte, secrets", "Le filtre par défaut de Google est orienté États-Unis", "30_ai_guardrails.tf"],
          ["4 Filtrage", "Plancher Model Armor", "Aucun filtre ne peut être affaibli, même par un admin", "30_ai_guardrails.tf"],
          ["5 Exposition", "UE, recherche web coupée, partages fermés", "Pas de fuite vers Internet ni entre collègues", "50_app.tf"],
          ["6 Détection", "Journaux dédiés en UE, lisibles par la sécurité seule", "Les questions des salariés ne traînent pas dans les journaux", "80_logging.tf"],
          ["6 Détection", "Alertes : garde-fou modifié, pic de blocages", "Détecter un affaiblissement ou une attaque", "70_detection.tf, 80_logging.tf"],
      ], [24 * mm, 56 * mm, 58 * mm, CW - 138 * mm]),
      Spacer(1, 6),
      gate(["La recette de sécurité est passée (13 tests du guide, dont droits Drive/SharePoint et blocages Model Armor).",
            "Les points « à valider » du guide (§16) sont levés sur le projet réel.",
            "Le DPO a validé la conservation et la journalisation ; les collaborateurs du pilote sont informés.",
            "Les retours du pilote confirment la valeur métier (taux d'usage, qualité perçue)."]),
      PageBreak()]

# ---------------------------------------------------------------- 6. Niveau 2
S += [level_banner(2, "Production : maîtrise du chiffrement, preuves et exploitation",
                   "Ouvrir à grande échelle avec des garanties opposables.",
                   ["Où : Terraform + CI/CD", "Qui : ouverture par groupes", "Données : internes", "Durée : 4 à 6 semaines"]),
      Spacer(1, 8), P("Pourquoi ce niveau", "h2"),
      P("À grande échelle, la question n'est plus seulement « est-ce sûr ? » mais « pouvons-nous le <b>prouver</b>, le <b>maîtriser</b> "
        "et le <b>maintenir</b> dans le temps ? ». Ce niveau apporte le contrôle du chiffrement, l'intégrité des preuves et une exploitation outillée."),
      table(["Mesure", "Pourquoi", "Comment"], [
          ["<b>CMEK</b> : données chiffrées avec une clé Acme (Cloud KMS, multi-région Europe)",
           "Contrôle : désactiver la clé rend les données illisibles en 15 minutes (interrupteur d'urgence). Exigence fréquente des politiques de sécurité.",
           "Clé enregistrée <b>avant</b> la création de l'app de production ; rotation manuelle ; protection contre la suppression."],
          ["Journaux de sécurité <b>verrouillés</b>", "Intégrité des preuves : personne ne peut réduire la rétention ni supprimer le bucket.", "<i>lock_security_logs</i> (irréversible)"],
          ["Politiques d'organisation : ressources en UE, CMEK obligatoire", "Empêcher toute dérive future, même dans un nouveau projet.", "Organisation Google Cloud"],
          ["Chaîne CI/CD Terraform", "Aucune modification manuelle en production ; plan relu, validation sécurité sur les garde-fous.", "État distant chiffré, plan en revue, apply par la CI"],
          ["Access Transparency", "Journal des accès éventuels du personnel Google aux données.", "Organisation (apps UE ou US)"],
          ["Exploitation", "Revue d'accès trimestrielle, rotation des secrets, exercices de red team sur l'assistant.", "Procédures du guide (§14)"],
          ["Ouverture progressive", "Par groupes métier, avec les partages d'agents ouverts une fois la gouvernance définie.", "Groupes et paramètres de l'app"],
      ], [55 * mm, 62 * mm, CW - 117 * mm]),
      Spacer(1, 6),
      callout("Pourquoi CMEK au niveau 2 et pas plus tôt ? Parce qu'il doit être enregistré <b>avant</b> la création de l'app qu'il protège "
              "(ce qui est créé avant reste chiffré par Google), et qu'il engage l'exploitation : rotation, procédure de révocation, astreinte. "
              "On l'active sur l'app de production, de façon préparée."),
      Spacer(1, 6),
      gate(["Le test de révocation de clé est réalisé en recette (indisponibilité en moins de 15 minutes, puis rétablissement).",
            "La chaîne CI/CD est en place ; plus aucun droit d'écriture humain en production.",
            "Les tableaux de bord d'usage et de sécurité sont suivis par les équipes désignées."]),
      PageBreak()]

# ---------------------------------------------------------------- 7. Niveau 3
S += [level_banner(3, "Avancé : agents maison, nouvelles sources, périmètre",
                   "Étendre la valeur sans étendre la surface d'attaque.",
                   ["Où : Terraform + organisation", "Qui : tous", "Données : sources étendues", "Durée : selon besoins"]),
      Spacer(1, 8), P("Pourquoi un niveau dédié", "h2"),
      P("Les agents personnalisés (ADK, A2A) et les serveurs MCP font passer l'assistant de « répondre » à « <b>agir</b> » : interroger Databricks, "
        "appeler une API métier, créer un ticket. Point clé : <b>le filtrage Model Armor de Gemini Enterprise ne s'applique pas aux agents "
        "personnalisés</b>. Ils exigent des contrôles propres."),
      table(["Mesure", "Pourquoi", "Quand l'activer"], [
          ["<b>Agent Gateway</b> (sortie)", "Pare-feu des agents : refus par défaut, règles par outil (lecture seule…), traçabilité de chaque appel.", "Dès le premier agent maison ou serveur MCP"],
          ["Agents maison avec leur propre Model Armor", "Combler l'angle mort du filtrage de l'app.", "Pour chaque agent"],
          ["Identité d'agent (Agent Identity)", "Une identité par agent, sans clé, révocable ; droits au plus juste.", "Avec Agent Gateway"],
          ["Databricks via son serveur MCP managé", "Pas de connecteur natif ; le serveur MCP conserve les droits Unity Catalog.", "Selon les cas d'usage data"],
          ["<b>VPC Service Controls</b>", "Périmètre autour des API : bloque l'exfiltration même avec des identifiants volés.", "D'abord en observation, puis activé ; idéalement avant les connecteurs de production"],
          ["Export SIEM / SOC, Security Command Center", "Intégrer l'IA à la supervision de sécurité existante.", "Selon l'outillage de Acme"],
          ["Entra ID (Workforce Identity Federation)", "Si l'annuaire de référence est Microsoft et que l'ingestion Microsoft 365 est requise.", "Décision du niveau 0"],
      ], [55 * mm, 70 * mm, CW - 125 * mm]),
      Spacer(1, 6),
      callout("Agent Gateway n'apporte presque rien sans agent maison : nous ne l'imposons pas trop tôt. Le socle le prévoit "
              "(une variable suffit), pour qu'il soit en place <b>le jour où</b> le premier agent qui agit est mis en service."),
      PageBreak()]

# ---------------------------------------------------------------- 8. Console vs Terraform
S += [P("MÉTHODE", "kicker"), P("Console ou Terraform : qui fait quoi", "h1"),
      P("La console sert à <b>apprendre et vérifier</b> ; Terraform sert à <b>garantir</b>. Quelques réglages n'existent pas encore "
        "dans Terraform : le socle les applique par l'API, ou ils restent des gestes d'administration documentés.", "lead"),
      table(["Élément", "Console (niveau 0)", "Terraform (niveaux 1 à 3)", "Reste manuel"], [
          ["App, assistant, recherche web, langue", "Oui", "Oui", "—"],
          ["Identité, rôles et groupes", "Oui", "Oui", "Appartenance aux groupes (annuaire)"],
          ["Templates Model Armor, plancher, DLP France", "Oui", "Oui", "—"],
          ["Connecteurs (Workspace, Microsoft, GitHub, Jira…)", "Oui", "Oui (modèle générique)", "Autorisation OAuth initiale, IP à autoriser côté SaaS"],
          ["Secrets des connecteurs", "—", "Référencés (jamais leur valeur)", "Création des valeurs par la sécurité"],
          ["CMEK (clés et enregistrement)", "Possible", "Oui, avec protection contre la suppression", "Révocation d'urgence (procédure)"],
          ["Conservation des conversations, observabilité", "Oui", "Par l'API, depuis Terraform", "—"],
          ["Journaux dédiés, exclusions, alertes", "Oui", "Oui", "—"],
          ["Licences", "Oui", "Possible (facturé)", "Attribution recommandée en console"],
          ["Partage d'un agent maison aux utilisateurs", "Oui", "Partiel", "Validation par un admin"],
          ["Agent Gateway, VPC-SC", "Possible", "Oui (options)", "Règles d'entrée VPC-SC à concevoir"],
      ], [50 * mm, 26 * mm, 46 * mm, CW - 122 * mm]),
      Spacer(1, 8), P("Le passage console → Terraform, sans perte", "h2")]
S += B(["Pendant le niveau 0, chaque réglage fait en console est noté dans un inventaire (quoi, pourquoi, valeur).",
        "Au niveau 1, chaque ligne de l'inventaire devient une variable ou une ressource Terraform, relue en revue de code.",
        "L'app de découverte est supprimée : la production repart d'un état décrit à 100 % par le code, avec CMEK dès la création.",
        "Une alerte signale ensuite toute modification manuelle des garde-fous : le code reste la seule référence."])
S += [PageBreak()]

# ---------------------------------------------------------------- 9. Model Armor
S += [P("ZOOM", "kicker"), P("Model Armor : le pare-feu des échanges avec l'IA", "h1"),
      P("Model Armor analyse <b>chaque question</b> avant le modèle et <b>chaque réponse</b> avant l'utilisateur. C'est un classifieur "
        "indépendant du modèle : on ne peut pas le « convaincre » comme on contourne une consigne.", "lead"),
      table(["Filtre", "Ce qu'il détecte", "Réglage du socle", "Pourquoi"], [
          ["Injection et jailbreak", "« Ignore tes instructions… », consignes cachées dans un document", "Activé · seuil moyen", "Risque n°1 des applications d'IA (OWASP)"],
          ["Liens malveillants", "Phishing et malware connus", "Activé", "L'assistant ne relaie jamais un lien piégé"],
          ["IA responsable", "Haine, harcèlement, sexuel explicite, dangereux", "Activé · seuil moyen", "Responsabilité de l'employeur"],
          ["Données sensibles", "NIR, CNI, passeport, n° fiscal, IBAN, carte, clés et jetons", "Modèle DLP France", "Le filtre de base de Google ne voit ni le NIR ni l'IBAN"],
      ], [32 * mm, 52 * mm, 34 * mm, CW - 118 * mm]),
      Spacer(1, 8), P("Trois garanties", "h2"),
      table(["Garantie", "Effet", "Pourquoi"], [
          ["FAIL_CLOSED", "Si Model Armor est indisponible, l'assistant refuse", "La sécurité passe avant la disponibilité"],
          ["Plancher (floor setting)", "Aucun filtre ne peut être moins strict que le minimum du projet", "Une garantie mécanique, pas une promesse"],
          ["Séparation des rôles + alerte", "Seule la sécurité modifie les filtres ; toute modification est signalée", "Personne ne désactive sa propre sécurité"],
      ], [38 * mm, 70 * mm, CW - 108 * mm]),
      Spacer(1, 8), P("Choix assumés", "h2")]
S += B(["<b>Seuil moyen</b> plutôt que strict : un outil qui bloque à tort est contourné. Le plancher et la détection couvrent le reste.",
        "<b>E-mails et téléphones non bloqués</b> : omniprésents dans le travail normal ; ils restent protégés par les droits d'accès.",
        "<b>Contenu filtré non journalisé</b> (recommandation Google) : les blocages sont tout de même comptés et alertés via les journaux d'usage.",
        "<b>Angle mort connu</b> : les agents maison ne sont pas filtrés par l'app. Ils sont traités au niveau 3."])
S += [PageBreak()]

# ---------------------------------------------------------------- 10. Journaux & RGPD
S += [P("ZOOM", "kicker"), P("Journalisation : tout tracer, sans tout exposer", "h1"),
      table(["Journal", "Contenu", "Données personnelles", "Socle (stockage UE)"], [
          ["Audit d'administration", "Qui a modifié les filtres, clés, droits, connecteurs", "Identité des admins", "Bucket sécurité · 365 j"],
          ["Audit d'accès aux données", "Appels à Gemini Enterprise, Model Armor, lectures de secrets", "Identité des utilisateurs", "Bucket sécurité · 365 j"],
          ["Usage Gemini Enterprise", "Qui a demandé quoi, sources, réponses bloquées", "Oui (questions)", "Bucket usage · 90 j"],
          ["Texte intégral questions et réponses", "Contenu exact", "Oui, intégralement", "Désactivé · décision DPO"],
          ["Contenu filtré par Model Armor", "Texte bloqué et filtre déclenché", "Oui", "Désactivé · recommandation Google"],
          ["Statistiques d'usage", "Utilisateurs actifs, requêtes, retours", "Agrégées", "Console Analytics"],
      ], [42 * mm, 58 * mm, 32 * mm, CW - 132 * mm]),
      Spacer(1, 8), P("Pourquoi ce dispositif", "h2")]
S += B(["<b>Séparer les finalités</b> : la preuve d'audit (1 an) et le suivi d'usage (90 jours) n'ont ni la même durée ni les mêmes lecteurs.",
        "<b>Sortir les questions du journal par défaut</b>, lisible par de nombreux rôles techniques, pour les réserver à l'équipe sécurité.",
        "<b>Enquêter en SQL sans copie</b> : les journaux restent dans leur bucket européen (Log Analytics).",
        "<b>Détecter sans surveiller</b> : l'alerte compte les blocages, elle n'expose pas les questions."])
S += [Spacer(1, 6),
      callout("Cadre RGPD et droit du travail : journaliser l'usage d'un outil par les salariés est un traitement de données personnelles. "
              "Il faut une finalité écrite, l'information des collaborateurs, l'inscription au registre des traitements, des durées proportionnées "
              "et, si l'outil permet un contrôle de l'activité, la consultation du CSE. Le socle démarre au plus sobre ; toute extension se décide avec le DPO."),
      PageBreak()]

# ---------------------------------------------------------------- 11. Risques
S += [P("COUVERTURE", "kicker"), P("Les risques, et le niveau qui les traite", "h1"),
      table(["#", "Risque", "Exemple", "Mesures", "Niveau"], [
          ["R1", "Accès non autorisé", "Ex-collaborateur, compte partagé", "SSO, groupes", "0 → 1"],
          ["R2", "Divulgation de données", "Un stagiaire retrouve des salaires", "Connecteurs fédérés, DLP en sortie", "1"],
          ["R3", "Injection de prompt", "Consigne cachée dans un document", "Model Armor", "0 → 1"],
          ["R4", "Données personnelles échangées", "Un IBAN client collé dans une question", "DLP France", "1"],
          ["R5", "Contenus dangereux ou malveillants", "Lien de phishing relayé", "Model Armor", "0 → 1"],
          ["R6", "Affaiblissement de la sécurité", "Un filtre coupé « pour une démo »", "Séparation des rôles, plancher, alerte", "1"],
          ["R7", "Perte de maîtrise des données", "Données hors UE, non révocables", "UE, CMEK", "0 → 2"],
          ["R8", "Secrets exposés", "Mot de passe dans un dépôt Git", "Secret Manager", "1"],
          ["R9", "Exfiltration", "Export massif avec identifiants volés", "IP fixes, VPC-SC", "1 → 3"],
          ["R10", "Abus non détecté", "200 tentatives de jailbreak ignorées", "Journaux dédiés, alertes", "1 → 2"],
          ["R11", "Agent qui agit sans contrôle", "Un agent maison appelle une API sensible", "Agent Gateway, Model Armor par agent", "3"],
      ], [10 * mm, 40 * mm, 50 * mm, 52 * mm, CW - 152 * mm]),
      Spacer(1, 6), P("Les risques résiduels assumés", "h2")]
S += B(["Une attaque très subtile peut passer le seuil moyen de Model Armor : le plancher, les droits d'accès et la détection limitent l'impact.",
        "En mode fédéré, la question est transmise à l'éditeur de la source (Microsoft, GitHub…) et relève de ses conditions contractuelles.",
        "En cas de panne de Model Armor, l'assistant est indisponible (choix FAIL_CLOSED)."])
S += [PageBreak()]

# ---------------------------------------------------------------- 12. Gouvernance & planning
S += [P("ORGANISATION", "kicker"), P("Gouvernance, rôles et planning", "h1"),
      P("Qui fait quoi (RACI simplifié)", "h2"),
      table(["Activité", "Sécurité", "Admin Gemini Ent.", "Plateforme / DevOps", "DPO", "Métier"], [
          ["Filtres Model Armor, plancher, clés", "R / A", "I", "C", "I", "—"],
          ["Connecteurs et sources", "C", "R", "C", "C", "A"],
          ["Code Terraform, CI/CD", "C (revue)", "C", "R / A", "—", "—"],
          ["Conservation, journalisation du contenu", "C", "I", "I", "A", "C"],
          ["Ouverture à de nouveaux groupes", "C", "R", "I", "I", "A"],
          ["Enquête après alerte", "R / A", "C", "C", "I (si données perso.)", "—"],
      ], [52 * mm, 20 * mm, 26 * mm, 28 * mm, 26 * mm, CW - 152 * mm]),
      P("R = réalise · A = approuve · C = consulté · I = informé", "small"),
      Spacer(1, 6), P("Planning indicatif", "h2"),
      table(["Semaines", "Étape", "Livrable"], [
          ["S1 – S2", "Niveau 0 : découverte en console, décisions structurantes", "Inventaire des réglages, 4 décisions actées"],
          ["S3 – S6", "Niveau 1 : déploiement du socle Terraform, recette, pilote", "Recette de sécurité signée, retours du pilote"],
          ["S7 – S12", "Niveau 2 : production (CMEK, CI/CD, verrouillages), ouverture par groupes", "Mise en production, tableaux de bord"],
          ["Ensuite", "Niveau 3 : agents maison, Databricks, VPC-SC, Agent Gateway", "Selon la feuille de route métier"],
      ], [24 * mm, 90 * mm, CW - 114 * mm]),
      P("Durées indicatives, à ajuster selon la disponibilité des équipes et les délais d'autorisation des sources (Microsoft, GitHub, Atlassian).", "small"),
      PageBreak()]

# ---------------------------------------------------------------- 13. Validation & conclusion
S += [P("TRANSPARENCE", "kicker"), P("Ce qui reste à valider sur le projet réel", "h1"),
      P("Le socle Terraform est validé syntaxiquement et construit sur la documentation Google d'octobre 2026. Il n'a pas encore été "
        "déployé dans l'environnement Acme. Les points ci-dessous seront confirmés lors de la recette du niveau 1 ; chacun a une solution de repli.", "lead"),
      table(["Point", "Repli si besoin"], [
          ["Localisation du modèle DLP associé aux filtres Model Armor en UE", "Autre localisation DLP, ou filtre de base en attendant"],
          ["Noms exacts des paramètres de certains connecteurs (Teams, GitHub)", "Création une fois en console, puis reprise en code"],
          ["Présence du motif de blocage dans les journaux d'usage", "Activation temporaire de la journalisation Model Armor en recette"],
          ["Noms des opérations surveillées par l'alerte « garde-fou modifié »", "Ajustement du filtre après le premier changement observé"],
          ["Exclusion effective des questions du journal par défaut", "Vérification dans l'explorateur de journaux"],
      ], [100 * mm, CW - 100 * mm]),
      Spacer(1, 10), P("Pourquoi cette approche est la bonne", "h1")]
S += B(["<b>Elle permet de démarrer demain</b>, en console, sans exposer une seule donnée sensible.",
        "<b>Elle prend les décisions irréversibles au bon moment</b> : après avoir appris, pas pendant le lancement.",
        "<b>Elle rend la sécurité visible et vérifiable</b> : chaque mesure a un risque, un test et une trace.",
        "<b>Elle protège l'adoption</b> : des réglages mesurés évitent que les collaborateurs contournent l'outil.",
        "<b>Elle prépare la suite</b> : agents, Databricks et périmètre réseau s'ajoutent sans refaire le socle."])
S += [Spacer(1, 10),
      callout("Proposition de prochaine étape : un atelier de deux heures avec les équipes sécurité, architecture et DPO pour acter les quatre "
              "décisions structurantes, puis le lancement du niveau 0 dans un projet de découverte dédié."),
      PageBreak()]

# ---------------------------------------------------------------- Annexe
S += [P("ANNEXE", "kicker"), P("Correspondance avec le socle Terraform", "h1"),
      table(["Fichier", "Contenu", "Niveau"], [
          ["versions.tf · variables.tf", "Versions, configuration du fournisseur, toutes les entrées (validées)", "1"],
          ["00_foundation.tf", "API activées, comptes de service Google", "1"],
          ["10_identity_access.tf", "Identité de l'app, rôles par groupes, séparation des rôles", "1"],
          ["20_data_protection.tf", "CMEK (clés Europe et régionales), secrets des connecteurs", "1 (secrets) · 2 (CMEK)"],
          ["30_ai_guardrails.tf", "Modèle DLP France, filtres Model Armor, plancher", "1"],
          ["40_connectors.tf", "Connecteurs génériques fédérés, IP fixes", "1"],
          ["50_app.tf", "App, assistant, fonctionnalités, conservation, observabilité", "1"],
          ["60_advanced.tf", "Agent Gateway, VPC Service Controls (options)", "3"],
          ["70_detection.tf", "Journaux d'audit, alerte « garde-fou modifié »", "1"],
          ["80_logging.tf", "Buckets de journaux UE, exclusions, accès, alerte de blocages", "1 · 2 (verrouillage)"],
          ["docs/ (13 fiches)", "Explication pédagogique de chaque fichier, ligne par ligne", "—"],
      ], [45 * mm, 100 * mm, CW - 145 * mm]),
      Spacer(1, 8), P("Références Google Cloud", "h2")]
S += B(["Gemini Enterprise : CMEK, Model Armor, fournisseur d'identité, connecteurs, VPC Service Controls, journaux d'audit et d'usage "
        "(docs.cloud.google.com/gemini/enterprise).",
        "Model Armor : présentation, modèles, plancher (docs.cloud.google.com/model-armor).",
        "Agent Gateway (docs.cloud.google.com/gemini-enterprise-agent-platform).",
        "Fournisseur Terraform Google (registry.terraform.io/providers/hashicorp/google)."])

doc.build(S)
print("written", OUT)
