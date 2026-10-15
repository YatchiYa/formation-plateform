"""Génère le PDF « Gemini Enterprise : conformité à la note de sécurité Acme » (projet 08)."""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Gemini-Enterprise-Note-securite-Acme.pdf")
F = "/home/yarab/.local/share/fonts/Inter/extras/ttf/"
for name, file in [("Inter", "Inter-Regular"), ("Inter-Md", "Inter-Medium"), ("Inter-SB", "Inter-SemiBold"),
                   ("Inter-B", "Inter-Bold"), ("Inter-I", "Inter-Italic"), ("Inter-L", "Inter-Light")]:
    pdfmetrics.registerFont(TTFont(name, F + file + ".ttf"))
pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Inter", normal="Inter", bold="Inter-SB", italic="Inter-I", boldItalic="Inter-SB")

NAVY = colors.HexColor("#14213D"); INK = colors.HexColor("#1C2333"); MUTED = colors.HexColor("#4A5568")
BLUE = colors.HexColor("#2F6FDE"); SOFT = colors.HexColor("#EEF2F9"); LINE = colors.HexColor("#D9DEE6")
WHITE = colors.white; ORANGE = colors.HexColor("#C75B12"); GREEN = colors.HexColor("#1E7A4C")
CODEBG = colors.HexColor("#F4F6FA"); ORANGE_BG = colors.HexColor("#FBF0E8"); GREEN_BG = colors.HexColor("#E8F3EC")
PHASE = [colors.HexColor("#2F6FDE"), colors.HexColor("#1F4FA8"), colors.HexColor("#1E7A4C"), colors.HexColor("#14213D")]

W, H = A4
M = 18 * mm
CW = W - 2 * M

st = {
    "h1": ParagraphStyle("h1", fontName="Inter-B", fontSize=20, leading=25, textColor=NAVY, spaceAfter=4),
    "kicker": ParagraphStyle("k", fontName="Inter-SB", fontSize=8.5, leading=11, textColor=BLUE, spaceAfter=3),
    "h2": ParagraphStyle("h2", fontName="Inter-SB", fontSize=12.5, leading=16, textColor=NAVY, spaceBefore=9, spaceAfter=4),
    "h3": ParagraphStyle("h3", fontName="Inter-SB", fontSize=10.5, leading=14, textColor=INK, spaceBefore=6, spaceAfter=2),
    "body": ParagraphStyle("b", fontName="Inter", fontSize=9.4, leading=13.6, textColor=INK, spaceAfter=5),
    "lead": ParagraphStyle("lead", fontName="Inter-L", fontSize=11.5, leading=16.5, textColor=INK, spaceAfter=8),
    "small": ParagraphStyle("s", fontName="Inter", fontSize=8, leading=11, textColor=MUTED, spaceAfter=4),
    "cell": ParagraphStyle("c", fontName="Inter", fontSize=8.2, leading=11, textColor=INK),
    "cellb": ParagraphStyle("cb", fontName="Inter-SB", fontSize=8.2, leading=11, textColor=INK),
    "th": ParagraphStyle("th", fontName="Inter-SB", fontSize=8.2, leading=11, textColor=WHITE),
    "bullet": ParagraphStyle("bl", fontName="Inter", fontSize=9.4, leading=13.6, textColor=INK, leftIndent=11, bulletIndent=0, spaceAfter=2.5),
    "quote": ParagraphStyle("q", fontName="Inter-Md", fontSize=10, leading=14.5, textColor=NAVY),
    "code": ParagraphStyle("code", fontName="Mono", fontSize=7.5, leading=9.8, textColor=INK),
    "banner": ParagraphStyle("bn", fontName="Inter", fontSize=9, leading=15, textColor=WHITE),
}


class Story(list):
    def __iadd__(self, other):
        (self.extend if isinstance(other, list) else self.append)(other)
        return self


def P(t, s="body"): return Paragraph(t, st[s])
def B(items): return [Paragraph(i, st["bullet"], bulletText="•") for i in items]


def table(header, rows, widths, first_bold=True, head=NAVY):
    data = [[Paragraph(h, st["th"]) for h in header]]
    for r in rows:
        data.append([Paragraph(c, st["cellb"] if (i == 0 and first_bold) else st["cell"]) for i, c in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    s = [("BACKGROUND", (0, 0), (-1, 0), head), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
         ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4), ("LEFTPADDING", (0, 0), (-1, -1), 5),
         ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    s += [("BACKGROUND", (0, i), (-1, i), SOFT) for i in range(2, len(data), 2)]
    t.setStyle(TableStyle(s))
    return KeepTogether([t, Spacer(1, 6)]) if len(rows) < 9 else [t, Spacer(1, 6)]


def code(text):
    t = Table([[Preformatted(text.strip("\n"), st["code"])]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([t, Spacer(1, 5)])


def callout(text, color=BLUE, bg=SOFT):
    t = Table([[Paragraph(text, st["quote"])]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return KeepTogether([t, Spacer(1, 6)])


def banner(n, title, subtitle, meta, color):
    left = Paragraph(f'<font name="Inter-B" size="28" color="#FFFFFF">{n}</font>', ParagraphStyle("lv", parent=st["body"], leading=32))
    mid = Paragraph(f'<font name="Inter-SB" size="8.5" color="#C9D3E6">PHASE {n}</font><br/>'
                    f'<font name="Inter-B" size="15" color="#FFFFFF">{title}</font><br/>'
                    f'<font name="Inter" size="9" color="#E3E8F2">{subtitle}</font>', st["banner"])
    right = Paragraph("<br/>".join(f'<font name="Inter" size="8" color="#E3E8F2">{m}</font>' for m in meta), st["banner"])
    t = Table([[left, mid, right]], colWidths=[15 * mm, 100 * mm, CW - 115 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return [t, Spacer(1, 8)]


def measure(num, title, demand, native, tf, proof, why, rest=None):
    head = Table([[Paragraph(f'<font name="Inter-B" size="13" color="#FFFFFF">{num}</font>', st["cell"]),
                   Paragraph(f'<font name="Inter-SB" size="10.5" color="#14213D">{title}</font>', st["cell"])]],
                 colWidths=[10 * mm, CW - 10 * mm])
    head.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, 0), BLUE), ("BACKGROUND", (1, 0), (1, 0), SOFT),
                              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, 0), "CENTER"),
                              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    rows = [["La note demande", demand], ["Natif (console)", native], ["Terraform / code", tf], ["Preuve", proof], ["Pourquoi", why]]
    if rest:
        rows.append(["Reste / limite", rest])
    body = Table([[Paragraph(a, st["cellb"]), Paragraph(b, st["cell"])] for a, b in rows], colWidths=[30 * mm, CW - 30 * mm])
    body.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, LINE),
                              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                              ("LEFTPADDING", (0, 0), (-1, -1), 5)]))
    return KeepTogether([head, body, Spacer(1, 9)])


# --------------------------------------------------------------------------- pages
def on_cover(c, d):
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(0, 0, 9 * mm, H, fill=1, stroke=0)
    labels = ["Console", "Terraform", "Tests", "Exploitation"]
    for i in range(4):
        x = W - 100 * mm + i * 22 * mm
        c.setFillColor(PHASE[i] if i < 3 else colors.HexColor("#3A4A6B"))
        c.rect(x, 40 * mm, 21 * mm, (16 + i * 15) * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#E3E8F2")); c.setFont("Inter-SB", 7.5)
        c.drawString(x + 2.5 * mm, 40 * mm + (16 + i * 15) * mm - 6 * mm, f"{i + 1} · {labels[i]}")
    c.setFillColor(colors.HexColor("#8FB3F5")); c.setFont("Inter-SB", 10)
    c.drawString(26 * mm, H - 45 * mm, "POUR L'ÉQUIPE PROJET ACME  ·  DEV · DEVOPS · PM · SÉCURITÉ · DPO")
    c.setFillColor(colors.HexColor("#F6F7F4")); c.setFont("Inter-B", 32)
    c.drawString(26 * mm, H - 70 * mm, "Gemini Enterprise")
    c.drawString(26 * mm, H - 83 * mm, "Note de sécurité Acme :")
    c.drawString(26 * mm, H - 96 * mm, "de la note à la preuve")
    c.setFont("Inter-L", 13.5); c.setFillColor(colors.HexColor("#C9D3E6"))
    for i, line in enumerate(["Les 10 mesures, activées d'abord en natif dans Google Cloud,",
                              "puis figées en Terraform, testées, et suivies chaque jour."]):
        c.drawString(26 * mm, H - 114 * mm - i * 7 * mm, line)
    c.setFont("Inter", 9.5)
    c.drawString(26 * mm, 30 * mm, "Version 1.0  ·  Octobre 2026  ·  Diffusion restreinte à l'équipe projet")
    c.drawString(26 * mm, 24 * mm, "Référence technique : projet 08-gemini-enterprise-securite-acme (Terraform, scripts, guides)")
    c.restoreState()


def on_page(c, d):
    c.saveState()
    c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(M, H - 12 * mm, W - M, H - 12 * mm)
    c.setFont("Inter-SB", 7.5); c.setFillColor(BLUE); c.drawString(M, H - 10 * mm, "GEMINI ENTERPRISE · NOTE DE SÉCURITÉ ACME")
    c.setFont("Inter", 7.5); c.setFillColor(MUTED); c.drawRightString(W - M, H - 10 * mm, "Diffusion restreinte")
    c.line(M, 12 * mm, W - M, 12 * mm)
    c.drawString(M, 8 * mm, "Octobre 2026 · v1.0")
    c.drawRightString(W - M, 8 * mm, f"{d.page}")
    c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, title="Gemini Enterprise - Note de sécurité Acme",
                      author="Équipe projet Gemini Enterprise", subject="Mise en conformité de Gemini Enterprise avec la note de sécurité",
                      leftMargin=M, rightMargin=M, topMargin=18 * mm, bottomMargin=18 * mm)
frame = Frame(M, 16 * mm, CW, H - 34 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=on_cover), PageTemplate(id="page", frames=[frame], onPage=on_page)])

S = Story([NextPageTemplate("page"), PageBreak()])

# ================================================================== 1. Synthèse
S += [P("SYNTHÈSE", "kicker"), P("En une page", "h1"),
      P("La note de sécurité Acme fixe <b>10 mesures</b> pour l'IA générative. Ce document explique, pour toute l'équipe, "
        "<b>comment</b> nous les appliquons à Gemini Enterprise, <b>dans quel ordre</b>, <b>pourquoi</b> chaque choix, "
        "et <b>comment nous le prouvons</b>.", "lead"),
      P("Le socle déjà construit (projet 06 : identité, chiffrement, connecteurs, Model Armor, journaux) couvrait le cœur de la note. "
        "Le projet 08 comble les écarts : protection des <b>agents personnalisés</b>, lutte contre le <b>Shadow AI</b>, export "
        "<b>SIEM</b>, <b>Access Approval</b>, analyse des documents <b>avant indexation</b>, <b>contrôle de sortie</b>, "
        "niveau d'accès <b>VPC-SC</b> et usage réel d'<b>Agent Registry</b>.")]
S += table(["Phase", "Ce qu'on fait", "Pourquoi", "Quand"], [
    ["1 · Console", "Activer ce que Google fournit nativement, en observation quand c'est possible", "Protection immédiate ; on mesure avant de bloquer", "Semaine 1"],
    ["2 · Terraform", "Reprendre chaque réglage en code relu, par paliers A → D", "Traçable, reproductible par domaine, sans dérive", "Semaines 2–3"],
    ["3 · Tests", "22 tests, chacun avec un résultat attendu et un journal de preuve", "Une mesure non prouvée n'existe pas", "Semaines 3–4"],
    ["4 · Exploitation", "Journal quotidien, revues hebdo et mensuelle, réponses aux alertes", "Détecter, réagir, prouver à l'audit", "En continu"],
], [26 * mm, 70 * mm, 55 * mm, CW - 151 * mm])
S += [P("Ce que l'équipe gagne", "h2")]
S += B(["<b>Une protection dès la première semaine</b>, sans attendre le code : journaux d'audit, Model Armor, plancher sur les agents.",
        "<b>Aucune coupure de service</b> : les contrôles risqués (blocage des agents, VPC-SC) passent d'abord deux semaines en observation.",
        "<b>Une conformité vérifiable en une commande</b> : <font name=\"Mono\" size=\"8.5\">verify_controls.sh</font> affiche chaque mesure OK / KO.",
        "<b>Une sécurité qu'on ne peut pas affaiblir par erreur</b> : plancher Model Armor, séparation des rôles, alerte à chaque changement.",
        "<b>Une note plus juste</b> : sept points techniques de la note sont corrigés, avec sources Google (page 16)."])
S += [Spacer(1, 4), P("Décisions attendues", "h2")]
S += table(["Décision", "Qui", "Pourquoi maintenant"], [
    ["Fournisseur d'identité : Google ou Entra ID / Okta", "Architecture + RSSI", "Avec un IdP tiers, pas de connecteurs Workspace ; changer plus tard efface l'historique"],
    ["Identité du connecteur SIEM", "SOC", "Nécessaire pour le palier B (export Pub/Sub)"],
    ["Access Transparency sur l'organisation", "Équipe Cloud centrale", "Prérequis d'Access Approval (support Enhanced / Premium)"],
    ["Exception « serveurs MCP sur Cloud Run »", "RSSI", "Recommandés par Google pour Gemini Enterprise ; à encadrer dans la mesure 1"],
], [58 * mm, 32 * mm, CW - 90 * mm])
S += [PageBreak()]

# ================================================================== 2. Qui fait quoi
S += [P("ORGANISATION", "kicker"), P("Qui fait quoi", "h1"),
      P("La sécurité de l'IA n'est pas l'affaire d'une seule équipe. Chacun a un rôle précis, et surtout : "
        "<b>personne ne peut désactiver sa propre sécurité</b>.", "lead")]
S += table(["Rôle", "Ce qu'il fait", "Ce qu'il ne peut pas faire"], [
    ["Chef de projet / PM", "Planifie les 4 phases, obtient les décisions, suit les indicateurs mensuels et le PV de recette", "—"],
    ["Sécurité (RSSI, SOC)", "Possède Model Armor, les clés, les journaux ; valide chaque PR sur les garde-fous ; traite les alertes", "Déployer seule : tout passe par la CI"],
    ["DevOps / plateforme", "Active la phase 1, écrit et applique la phase 2 via la CI, importe la console dans Terraform", "Modifier un garde-fou sans validation sécurité (CODEOWNERS)"],
    ["Développeurs d'agents", "Déploient sur Agent Runtime avec Model Armor et confirmation humaine ; enregistrent dans Agent Registry", "Exposer un service à Internet ; déployer hors CI (alerte)"],
    ["Admins Gemini Enterprise", "Gèrent l'app, les connecteurs, l'ouverture aux groupes", "Toucher aux filtres, aux clés, lire les journaux d'usage"],
    ["DPO", "Décide de la journalisation du contenu et des durées de conservation", "—"],
], [36 * mm, 82 * mm, CW - 118 * mm])
S += [P("Matrice RACI des activités clés", "h2")]
S += table(["Activité", "Sécu.", "DevOps", "Dév.", "PM", "DPO"], [
    ["Phase 1 : activations console", "A", "R", "I", "I", "I"],
    ["Phase 2 : PR Terraform des garde-fous", "A", "R", "C", "I", "—"],
    ["Agents : Model Armor + confirmation humaine", "A", "C", "R", "I", "—"],
    ["Phase 3 : recette, PV signé", "A", "C", "C", "R", "I"],
    ["Journal quotidien, alertes", "R / A", "C", "—", "I", "I (si données perso.)"],
    ["Conservation, journalisation du contenu", "C", "I", "—", "I", "A"],
], [70 * mm, 20 * mm, 20 * mm, 18 * mm, 18 * mm, CW - 146 * mm])
S += [P("R = réalise · A = approuve · C = consulté · I = informé", "small"),
      callout("Règle d'or pour tous : après la phase 2, <b>plus aucune modification de sécurité en console</b>. Toute exception "
              "déclenche l'alerte « garde-fou modifié » et doit correspondre à une PR."),
      PageBreak()]

# ================================================================== 3. Les 10 mesures
S += [P("VUE D'ENSEMBLE", "kicker"), P("Les 10 mesures et notre réponse", "h1"),
      P("Chaque mesure est couverte d'abord par un réglage <b>natif</b> de Google Cloud, puis par du <b>code</b>. "
        "Les scripts fournis automatisent l'inventaire, l'analyse des documents, le journal quotidien et le contrôle de conformité.", "lead")]
S += table(["#", "Mesure de la note", "Natif (phase 1)", "Terraform / script (phase 2)", "Statut"], [
    ["1", "Agents sur Agent Runtime", "Plancher Model Armor sur Agent Platform", "90_agents_registry.tf, 30_ai_guardrails.tf", "Couvert"],
    ["2", "Shadow AI", "Politiques d'org, Asset Inventory, SCC AI Protection", "75_shadow_ai.tf · shadow_ai_inventory.sh", "Couvert (Wiz : hors app)"],
    ["3", "Model Armor", "Templates, réglage de l'app, plancher", "30_ai_guardrails.tf (DLP France) · test_model_armor.sh", "Plus strict que la note"],
    ["4", "Journaux, AxT, Access Approval, SIEM", "Audit Logs, Access Transparency, Access Approval", "70, 80, 85_siem_access.tf · daily_report.sh", "Couvert (AxT : org)"],
    ["5", "Filtrage de sortie", "Agent Gateway, IP fixes des connecteurs", "60_advanced.tf, 95_secure_web_proxy.tf", "Couvert (voir correction)"],
    ["6", "RAG : droits, documents", "Connecteurs fédérés", "40_connectors.tf · scan_before_ingest.py", "Couvert"],
    ["7", "VPC Service Controls", "Périmètre en dry-run, niveau d'accès", "60_advanced.tf (+ aiplatform, agentregistry)", "Dry-run → appliqué"],
    ["8", "Identité, projet par domaine, rôles", "Fournisseur d'identité, groupes", "10_identity_access.tf, un tfvars par domaine", "Décision IdP"],
    ["9", "Validation humaine", "Confirmation des actions dans GE", "require_confirmation (agent), destructiveHint (MCP)", "Couvert"],
    ["10", "Agent Registry, partage", "Registre, partage d'agents désactivé", "90_agents_registry.tf, 50_app.tf", "Couvert"],
], [8 * mm, 38 * mm, 46 * mm, 58 * mm, CW - 150 * mm])
S += [Spacer(1, 2),
      P("Le détail de chaque mesure (ce que la note demande, ce que nous faisons, la preuve, la raison) est aux pages 9 à 13.", "small"),
      PageBreak()]

# ================================================================== 4. Méthode
S += [P("MÉTHODE", "kicker"), P("Pourquoi d'abord la console, puis Terraform ?", "h1"),
      P("C'est la question que l'on nous posera. Quatre arguments, tirés de la pratique des déploiements cloud en entreprise.", "lead")]
for n, (t, d) in enumerate([
    ("La protection n'attend pas le code.", "Activer les journaux d'audit ou Model Armor prend dix minutes en console. Attendre deux semaines de "
     "développement, c'est rester deux semaines sans protection, alors que des pilotes utilisent déjà l'outil."),
    ("Observer avant de bloquer.", "Le plancher Model Armor sur les agents en mode inspection et VPC-SC en dry-run montrent ce qui <i>serait</i> bloqué. "
     "On règle les seuils sur des cas réels, sans casser un service. Un contrôle trop strict pousse les équipes vers des IA non maîtrisées : "
     "c'est exactement le Shadow AI que la note veut éviter."),
    ("Le code ensuite, pour durer.", "Un réglage manuel se perd, se modifie sans trace et ne se reproduit pas dans le projet du domaine suivant. "
     "Terraform le rend relu (PR), traçable (Git), reproductible (un projet par domaine, mesure 8) et vérifiable : le plan montre toute dérive."),
    ("Rien n'est perdu entre les deux.", "Ce qui a été créé en console est importé dans Terraform par des blocs <font name=\"Mono\" size=\"8.5\">import</font> : "
     "Terraform adopte la ressource sans la recréer. Les écarts éventuels entre la console et le code apparaissent dans le plan, et se tranchent en revue."),
], 1):
    S += KeepTogether([P(f'<font color="#2F6FDE">{n}.</font>  {t}', "h3"), P(d)])
S += [Spacer(1, 4), P("Le calendrier", "h2")]
S += table(["Semaine", "Phase", "Livrable", "Critère de sortie"], [
    ["S1", "1 · Console", "Journal de bord des activations", "Audit actif ; Model Armor sur l'app ; plancher agents en inspection"],
    ["S2", "2 · Terraform A", "PR socle + palier A, import de la console", "Plan sans écart ; verify_controls.sh au vert"],
    ["S3", "2 · Terraform B, C", "SIEM branché ; politiques d'org ; VPC-SC dry-run", "Le SOC reçoit le flux ; pas de violation VPC-SC légitime"],
    ["S3–S4", "3 · Tests", "PV de recette des 22 tests", "Tests bloquants OK ; risques résiduels signés par le RSSI"],
    ["S5", "Bascule", "Plancher agents en blocage ; VPC-SC appliqué", "Deux semaines d'observation sans faux positif"],
    ["Ensuite", "4 · Exploitation", "Rapports quotidiens, mensuels archivés", "Indicateurs mensuels au comité"],
], [18 * mm, 30 * mm, 62 * mm, CW - 110 * mm])
S += [PageBreak()]

# ================================================================== 5. Phase 1
S += banner(1, "Activer le natif dans la console", "Effet immédiat, réversible, en observation quand c'est possible",
            ["Qui : DevOps + sécurité", "Durée : semaine 1", "Guide : docs/01-phase1-console.md"], PHASE[0])
S += [P("Astuce : le plus fiable pour trouver une page est la <b>barre de recherche</b> en haut de la console. La colonne « Rechercher » "
        "donne le terme à taper. Toujours vérifier le projet sélectionné en haut à gauche.")]
S += table(["#", "Action", "Rechercher", "Réglage clé", "§"], [
    ["1", "Journaux d'audit accès aux données", "Audit Logs", "Data Read + Data Write sur Discovery Engine, Agent Platform, Model Armor, Secret Manager, Agent Registry. Pas KMS en lecture.", "§4"],
    ["2", "Templates Model Armor", "Model Armor", "Région eu ; injection/jailbreak, URL, IA responsable « moyen et plus » ; données sensibles avancées (modèle DLP France) ; Inspect & Block", "§3"],
    ["3", "Model Armor dans l'app", "Gemini Enterprise", "App → Configurations : les deux templates ; mode fermé ; rôle Model Armor User au compte GE", "§3"],
    ["4", "Plancher + Agent Platform", "Model Armor", "Onglet Paramètres de plancher → Services → Agent Platform : Inspecter uniquement ; Cloud Logging activé", "§1"],
    ["5", "Agent Registry, partage", "Agent Registry", "Agents et MCP enregistrés ; partage d'agents désactivé dans l'app ; skills sur approbation", "§10"],
    ["6", "Inventaire Shadow AI", "Asset Inventory", "Ou script shadow_ai_inventory.sh sur l'organisation", "§2"],
    ["7", "Politiques d'organisation", "Règles d'administration", "run.allowedIngress, iam.allowedPolicyMemberDomains, gcp.resourceLocations", "§2"],
    ["8", "Accès de Google", "Access Transparency / Approval", "AxT sur l'org (support Enhanced/Premium) ; Access Approval : tous les services", "§4"],
    ["9", "Journaux et SIEM", "Routeur de journaux", "Buckets eu ge-security (365 j) et ge-usage (90 j) ; sink Pub/Sub. Peut être laissé à Terraform", "§4"],
    ["10", "VPC Service Controls", "VPC Service Controls", "Périmètre dry-run ; services dont aiplatform ; niveau d'accès IP Acme", "§7"],
    ["11", "AI Protection", "Security Command Center", "Si SCC Enterprise/Premium ; sinon Wiz si c'est le standard", "§2"],
], [11 * mm, 34 * mm, 30 * mm, CW - 89 * mm, 14 * mm])
S += [callout("Pourquoi les journaux d'audit en premier ? Par défaut, Google ne trace que l'administration : <b>qui interroge quoi n'est pas journalisé</b>. "
              "Sans cette étape, aucune enquête n'est possible. C'est dix minutes de travail, et la première chose à activer."),
      PageBreak()]

S += [P("PHASE 1 · ZOOM", "kicker"), P("Les deux réglages qui font la différence", "h1"),
      P("Plancher Model Armor étendu à Agent Platform (mesures 1 et 3)", "h2"),
      P("Dans Gemini Enterprise, Model Armor protège l'assistant, <b>pas les agents personnalisés</b> (ADK, A2A). Le plancher, avec le service "
        "<i>Agent Platform</i>, filtre <b>chaque appel Gemini fait dans le projet</b> : agents sur Agent Runtime, notebooks, scripts. C'est le filet "
        "de sécurité qui fonctionne même si un développeur oublie le plugin dans son agent."),
      P("Deux semaines en <b>Inspecter uniquement</b> : chaque verdict est journalisé, rien n'est bloqué. On regarde les faux positifs, puis on passe en "
        "<b>Inspecter et bloquer</b> (en Terraform : une ligne)."),
      code('''Logs Explorer : ce qui AURAIT été bloqué
jsonPayload.@type="type.googleapis.com/google.cloud.modelarmor.logging.v1.SanitizeOperationLogEntry"
jsonPayload.sanitizationResult.filterMatchState="MATCH_FOUND"'''),
      P("VPC Service Controls en dry-run (mesure 7)", "h2"),
      P("Le périmètre empêche l'exfiltration : même avec des identifiants volés, on ne copie pas les données hors du projet. Deux pièges connus, "
        "évités par la méthode :"),
      ]
S += B(["<b>L'interface de Gemini Enterprise passe par l'API discoveryengine</b> : sans niveau d'accès (IP de sortie Acme), un périmètre appliqué "
        "bloque aussi les utilisateurs légitimes.",
        "<b>Les connecteurs se créent avant</b> l'application du périmètre.",
        "Notre périmètre ajoute <b>aiplatform</b> et <b>agentregistry</b>, absents de la configuration initiale alors que la note les exige."])
S += [code('''Logs Explorer : violations VPC-SC (observation)
protoPayload.metadata.@type="type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata"
protoPayload.metadata.dryRun=true'''),
      P("Journal de bord de la phase 1", "h2"),
      P("Chaque activation est notée : date, qui, action exacte, identifiant créé, preuve. Ce journal sert deux fois : pour l'import "
        "Terraform de la phase 2, et comme preuve d'audit."),
      PageBreak()]

# ================================================================== 6. Phase 2
S += banner(2, "Figer la sécurité en Terraform", "Code relu, déployé par la CI, reproductible pour chaque domaine",
            ["Qui : DevOps (exécution), sécurité (revue)", "Durée : semaines 2–3", "Guide : docs/phase2-terraform/"], PHASE[1])
S += [P("Quatre paliers, chacun dans sa propre PR", "h2")]
S += table(["Palier", "Contenu", "Prérequis", "Variables"], [
    ["A · Projet", "Socle 06 ; audit aiplatform + agentregistry ; plancher Agent Platform ; droits Agent Registry ; alerte Shadow AI", "Droits sur le projet",
     "armor_agent_platform_mode, agent_developer_groups"],
    ["B · SOC", "Export Pub/Sub vers le SIEM (même filtre que le bucket sécurité)", "Identité du connecteur SIEM", "enable_siem_export, siem_subscriber"],
    ["C · Organisation", "Politiques d'org ; VPC-SC + niveau d'accès ; Access Approval", "Rôles org ; Access Transparency ; ID client Workspace",
     "enforce_org_policies, vpc_sc_access_policy, corporate_ip_ranges, access_approval_emails"],
    ["D · Réseau", "Secure Web Proxy, liste blanche de domaines", "VPC, sous-réseaux, liste validée", "swp"],
], [24 * mm, 66 * mm, 38 * mm, CW - 128 * mm])
S += [P("Ce qui change par rapport au socle 06", "h2")]
S += table(["Fichier", "Ajout", "Mesure"], [
    ["30_ai_guardrails.tf", "Plancher étendu : integrated_services = AI_PLATFORM, mode inspect ou block", "§1 §3"],
    ["60_advanced.tf", "aiplatform et agentregistry dans le périmètre ; niveau d'accès IP Acme", "§7"],
    ["70_detection.tf", "Journaux d'accès aux données pour aiplatform et agentregistry", "§4"],
    ["75_shadow_ai.tf (nouveau)", "3 politiques d'organisation ; alerte service public / agent créé hors circuit", "§2"],
    ["85_siem_access.tf (nouveau)", "Topic + abonnement Pub/Sub, sink, droit du writer ; Access Approval", "§4"],
    ["90_agents_registry.tf (nouveau)", "Droits du registre ; agent exemple sur Agent Runtime, identité dédiée, sortie Agent Gateway", "§1 §9 §10"],
    ["95_secure_web_proxy.tf (nouveau)", "Proxy, politique, liste blanche, sous-réseau dédié", "§5"],
    ["imports.tf.example (nouveau)", "Blocs import pour adopter les ressources créées en console", "—"],
], [52 * mm, CW - 70 * mm, 18 * mm])
S += [P("Reprendre la console sans rien recréer", "h2"),
      code('''import {
  to = google_model_armor_template.shield["ge-prompt-shield"]          # adresse dans le code
  id = "projects/PROJECT_ID/locations/eu/templates/ge-prompt-shield"    # ressource existante
}
# terraform plan  ->  "1 to import" ; tout "~ update" = un écart console / code à trancher en revue'''),
      PageBreak()]

S += [P("PHASE 2 · CODE", "kicker"), P("Les extraits qui portent la note", "h1"),
      P("Plancher Model Armor : de l'observation au blocage en une ligne", "h3"),
      code('''integrated_services = var.armor_agent_platform_mode == "off" ? [] : ["AI_PLATFORM"]
dynamic "ai_platform_floor_setting" {
  for_each = var.armor_agent_platform_mode == "off" ? [] : [1]
  content {
    inspect_only         = var.armor_agent_platform_mode == "inspect"
    inspect_and_block    = var.armor_agent_platform_mode == "block"
    enable_cloud_logging = true
  }
}'''),
      P("Shadow AI : empêcher plutôt que constater", "h3"),
      code('''org_policies = {
  "run.allowedIngress"             = ["internal-and-cloud-load-balancing"]  # pas de Cloud Run public
  "gcp.resourceLocations"          = ["in:eu-locations"]                   # rien hors UE
  "iam.allowedPolicyMemberDomains" = [var.workspace_customer_id]           # pas de allUsers
}'''),
      P("SIEM : le même filtre que le bucket sécurité, en temps réel", "h3"),
      code('''resource "google_logging_project_sink" "siem" {
  destination            = "pubsub.googleapis.com/${google_pubsub_topic.siem[0].id}"
  filter                 = local.security_log_filter
  unique_writer_identity = true
}'''),
      P("Circuit CI/CD", "h2")]
S += B(["PR → <font name=\"Mono\" size=\"8.5\">terraform plan</font> publié dans la PR → <b>validation obligatoire de la sécurité</b> sur les fichiers garde-fous (CODEOWNERS) → apply par la CI.",
        "L'alerte « garde-fou modifié » arrive : elle doit correspondre à la PR.",
        "<font name=\"Mono\" size=\"8.5\">verify_controls.sh</font> en fin de pipeline : un KO fait échouer le déploiement.",
        "Un projet par domaine (mesure 8) : même code, un fichier tfvars et un état par domaine."])
S += [PageBreak()]

# ================================================================== 7. Mesures détaillées
S += [P("MESURE PAR MESURE", "kicker"), P("Ce que la note demande, ce que nous faisons", "h1")]
S += measure("1", "Agents sur Agent Runtime (ex-Agent Engine)",
             "Héberger les agents sur la plateforme gérée de Google plutôt que sur des serveurs « maison ».",
             "Agent Runtime ; plancher Model Armor appliqué à Agent Platform.",
             "Agent sur Agent Runtime avec identité dédiée, ModelArmorPlugin en mode fermé, refus de démarrer sans Model Armor, sortie via Agent Gateway.",
             "T08 (jailbreak bloqué par l'agent), T09–T10 (plancher), verify_controls.sh.",
             "Héberger sur Agent Runtime ne filtre rien en soi. Plugin (par conception) + plancher (filet de sécurité) : deux protections indépendantes.",
             "Exception encadrée pour les serveurs MCP sur Cloud Run, recommandés par Google pour Gemini Enterprise : privés, enregistrés, déployés par la CI.")
S += measure("2", "Shadow AI",
             "Repérer et mettre en quarantaine les IA non gouvernées ; posture de sécurité IA.",
             "Cloud Asset Inventory ; politiques d'organisation ; Security Command Center AI Protection.",
             "75_shadow_ai.tf : Cloud Run non public, partage limité au domaine, UE ; alerte « service public / agent créé ». Script d'inventaire mensuel.",
             "T18 (allUsers refusé ou alerte), T19 (agent hors CI détecté), inventaire archivé.",
             "Empêcher coûte moins cher que détecter ; détecter rattrape ce qui passe ; l'inventaire prouve l'état au comité.",
             "Quarantaine réseau et Wiz : décisions d'organisation, hors périmètre de l'app.")
S += measure("3", "Model Armor (Inspect & Block, URL, données sensibles)",
             "Filtrer prompts et réponses, bloquer, détecter les données sensibles.",
             "Templates, réglage Model Armor de l'app, plancher.",
             "Deux templates Inspect & Block ; détecteurs DLP France (NIR, CNI, passeport, IBAN…) ; multilingue ; mode fermé dans l'app.",
             "T01–T07 ; test_model_armor.sh.",
             "Plus strict que la note : sortie filtrée aussi, mode fermé, détecteurs français. Le filtre « de base » ne voit ni IBAN ni NIR.")
S += [PageBreak()]
S += measure("4", "Journaux, Access Transparency, Access Approval, SIEM",
             "Journaux d'accès aux données (dont Vertex AI), AxT, Access Approval, envoi au SIEM.",
             "Audit Logs ; Access Transparency (organisation) ; Access Approval ; routeur de journaux.",
             "Audit étendu à aiplatform et agentregistry ; buckets UE (365 j sécurité, 90 j usage, accès restreint) ; Pub/Sub vers le SIEM ; Access Approval sur tous les services éligibles.",
             "T21 (changement visible côté SIEM) ; journal quotidien ; verify_controls.sh.",
             "Access Approval couvre Gemini Enterprise, Agent Runtime, Model Armor et Cloud KMS (GA) : aucun ingénieur Google n'accède aux données sans accord.",
             "Access Transparency : activation par l'équipe Cloud centrale (support Enhanced / Premium).")
S += measure("5", "Filtrage de sortie",
             "Contrôler les destinations Internet appelées par l'IA (Secure Web Proxy).",
             "Agent Gateway (sortie gouvernée, refus par défaut) ; IP fixes des connecteurs ; politiques d'org sur les destinations.",
             "Agent Gateway ; agent relié à la passerelle ; Secure Web Proxy optionnel avec liste blanche.",
             "T13 (lien externe inconnu) ; journaux de la passerelle et du proxy.",
             "Gemini Enterprise est un SaaS : il ne sort pas par le VPC Acme. Le SWP filtre nos charges ; Agent Gateway filtre GE et les agents.")
S += measure("6", "RAG : droits et contenu indexé",
             "Respecter les droits des sources ; éviter l'empoisonnement des documents.",
             "Connecteurs fédérés : les droits de la source s'appliquent à chaque requête.",
             "scan_before_ingest.py : Model Armor analyse PDF, Word, Excel, PowerPoint, CSV, texte ; quarantaine ; fail closed.",
             "T14 (A ne voit pas le fichier de B), T15 (PDF piégé en quarantaine).",
             "Model Armor filtre la question et la réponse, pas les documents récupérés : l'analyse en amont ferme cette porte pour les dépôts que l'on alimente.",
             "Sources fédérées (Drive, SharePoint) : protection par les droits, le filtre de sortie et la confirmation humaine.")
S += [PageBreak()]
S += measure("7", "VPC Service Controls",
             "Périmètre anti-exfiltration autour des services IA.",
             "Périmètre en dry-run ; niveaux d'accès.",
             "discoveryengine, aiplatform, agentregistry, modelarmor, dlp, cloudkms, secretmanager ; niveau d'accès IP Acme.",
             "T22 (accès hors réseau Acme journalisé, puis refusé).",
             "Le dry-run évite la coupure ; le niveau d'accès évite de bloquer les utilisateurs.",
             "Passage en appliqué après deux semaines ; niveau « appareil géré » si Endpoint Verification est déployé.")
S += measure("8", "Identité, un projet par domaine, séparation des rôles",
             "Fédération d'identité, isolation par domaine, rôles séparés.",
             "Fournisseur d'identité de l'app ; groupes.",
             "Rôles par groupes ; sécurité seule maître des filtres, clés et journaux ; un tfvars et un état par domaine.",
             "T16 (hors groupe refusé), T17 (admin GE ne touche pas aux filtres) ; contrôle « aucun utilisateur individuel ».",
             "Un domaine compromis n'expose pas les autres ; un administrateur ne peut pas désactiver sa propre sécurité.",
             "Décision IdP : avec Entra / Okta, pas de connecteurs Workspace ; changer plus tard efface l'historique.")
S += measure("9", "Validation humaine des actions",
             "Un humain confirme toute action qui modifie des données.",
             "Gemini Enterprise demande confirmation pour les actions et les outils MCP marqués destructifs.",
             "Agent : require_confirmation sur les outils d'écriture ; MCP : annotations destructiveHint.",
             "T11 (remboursement confirmé ou refusé), T12 (outil MCP destructif).",
             "Dernier rempart contre l'injection indirecte : même manipulé, l'agent ne peut rien modifier sans accord.")
S += measure("10", "Agent Registry et partage",
             "Catalogue central des agents ; partage encadré.",
             "Agent Registry ; partage d'agents désactivé ; skills sur approbation.",
             "Lecture pour les utilisateurs, publication pour les développeurs ; fonctionnalités de l'app.",
             "verify_controls.sh ; T19.",
             "Ce qui n'est pas au registre n'est pas gouverné ; avec Agent Gateway, il n'est même pas joignable.")
S += [PageBreak()]

# ================================================================== 8. Agents
S += [P("DÉVELOPPEURS", "kicker"), P("Le modèle d'agent sécurisé", "h1"),
      P("Chaque agent personnalisé suit le modèle fourni (<font name=\"Mono\" size=\"9\">agent/secure_agent</font>). Le code applique trois mesures de la note.", "lead"),
      code('''# §9 : toute action qui modifie passe par un humain
tools=[get_order, FunctionTool(refund_order, require_confirmation=needs_human)]

# §3 : Model Armor sur chaque question et chaque réponse, mode fermé
ModelArmorPlugin(config=ModelArmorConfig(
    prompt_template_name=os.environ["PROMPT_TEMPLATE"],
    response_template_name=os.environ["RESPONSE_TEMPLATE"],
    block_on_screening_failure=True))

# Fail closed : jamais d'agent déployé sans Model Armor
elif os.getenv("LOCAL_DEV") != "1":
    raise RuntimeError("PROMPT_TEMPLATE/RESPONSE_TEMPLATE manquants")''')]
S += table(["Règle", "Pourquoi"], [
    ["Déployé sur Agent Runtime, par la CI", "Hébergement géré, journaux, enregistrement automatique dans Agent Registry"],
    ["Identité dédiée par agent", "Un droit donné au compte partagé vaudrait pour tous les agents du projet"],
    ["ModelArmorPlugin, mode fermé", "Gemini Enterprise ne filtre pas les agents personnalisés"],
    ["Refus de démarrer sans Model Armor", "Une variable oubliée ne doit jamais produire un agent non filtré"],
    ["require_confirmation sur les écritures", "Mesure 9 : un humain valide avant l'exécution"],
    ["Outils MCP : readOnlyHint / destructiveHint", "Gemini Enterprise demande confirmation pour les outils destructifs"],
    ["Sortie via Agent Gateway", "Seuls les outils enregistrés sont joignables"],
], [65 * mm, CW - 65 * mm])
S += [P("Essayer en local", "h3"),
      code('''cd agent
LOCAL_DEV=1 python secure_agent/agent.py    # autotest des outils
LOCAL_DEV=1 adk web .                        # « Rembourse 10 € sur CMD-1002, colis abîmé »
                                             # -> l'interface demande une CONFIRMATION'''),
      PageBreak()]

# ================================================================== 9. Phase 3
S += banner(3, "Prouver : le plan de tests", "Une mesure n'est en place que si un test la prouve et qu'un journal en garde la trace",
            ["Qui : sécurité (exécution), PM (suivi)", "Durée : semaines 3–4", "Guide : docs/03-plan-de-tests.md"], PHASE[2])
S += [code('''./scripts/test_model_armor.sh                             # T01-T05 : filtrage
PROJECT_ID=... APP_ID=... ./scripts/verify_controls.sh   # T20 : conformité, une ligne OK / KO par mesure''')]
S += table(["#", "Test", "Attendu", "Preuve"], [
    ["T01–T05", "Question normale ; jailbreak FR ; IBAN ; carte ; URL de test", "Normale acceptée, le reste bloqué", "Sortie du script"],
    ["T06", "NIR de test dans l'app", "Bloqué (DLP France)", "ge-usage : CUSTOMER_POLICY_VIOLATION"],
    ["T07", "Désactiver le filtre jailbreak d'un template", "Refusé par le plancher", "Audit UpdateTemplate en échec"],
    ["T08", "Jailbreak envoyé à l'agent", "Bloqué par le plugin", "Journaux de l'agent"],
    ["T09–T10", "Appel Gemini direct avec jailbreak, plancher inspect puis block", "Journalisé, puis bloqué", "SanitizeOperationLogEntry"],
    ["T11–T12", "Remboursement par l'agent ; outil MCP destructif", "Confirmation demandée", "Interface, traces"],
    ["T13", "Document avec image markdown vers un domaine inconnu", "L'image externe n'est pas chargée", "Onglet Réseau du navigateur"],
    ["T14–T15", "Fichier partagé avec B seulement ; PDF piégé", "Invisible pour A ; PDF en quarantaine", "Interface ; CSV du scanner"],
    ["T16–T17", "Compte hors groupe ; admin GE sur un filtre", "Refusés", "Audit PERMISSION_DENIED"],
    ["T18–T19", "allUsers sur Cloud Run ; agent créé hors CI", "Refusé ou alerte", "E-mail, inventaire"],
    ["T20–T21", "verify_controls.sh ; PR qui modifie un template", "Tout OK ; alerte + SIEM", "Sortie archivée ; SIEM"],
    ["T22", "Appel de l'API depuis un réseau hors Acme", "Violation journalisée, puis refus", "Requête VPC-SC"],
], [17 * mm, 62 * mm, 45 * mm, CW - 124 * mm])
S += [callout("Critère de passage en production : T01–T12, T14, T16, T17, T20 et T21 OK. Les autres tests sont OK, ou le risque est "
              "accepté par écrit par le RSSI.", GREEN, GREEN_BG),
      PageBreak()]

# ================================================================== 10. Phase 4
S += banner(4, "Exploiter : le journal quotidien", "Savoir chaque matin, en dix minutes, si quelque chose d'anormal s'est passé",
            ["Qui : sécurité / SOC", "Durée : 10 min par jour", "Guide : docs/04-exploitation-journaliere.md"], PHASE[3])
S += table(["Fréquence", "Quoi", "Outil"], [
    ["Chaque jour", "Journal quotidien : changements, blocages, Shadow AI, accès refusés, VPC-SC ; traiter les alertes", "daily_report.sh, Alerting"],
    ["Chaque semaine", "Faux positifs Model Armor ; nouveaux agents au registre", "Log Analytics, Agent Registry"],
    ["Chaque mois", "Conformité et inventaire Shadow AI, archivés (preuve d'audit)", "verify_controls.sh, shadow_ai_inventory.sh"],
    ["Chaque trimestre", "Groupes, liste blanche de sortie, durées de conservation, exceptions", "IAM, terraform.tfvars"],
], [28 * mm, 95 * mm, CW - 123 * mm])
S += [P("Où trouver chaque journal", "h2")]
S += table(["Journal", "Contenu", "Où", "Durée"], [
    ["Audit admin", "Création, modification, droits", "Bucket ge-security", "365 j"],
    ["Audit accès aux données", "Qui a interrogé quoi (GE, Agent Platform, Model Armor, registre)", "ge-security", "365 j"],
    ["Verdicts Model Armor", "Filtre déclenché (et contenu si activé)", "ge-security", "365 j"],
    ["Usage Gemini Enterprise", "Questions, sources, motif de blocage", "ge-usage (sécurité seule)", "90 j"],
    ["Access Transparency", "Accès d'un ingénieur Google", "_Required / ge-security", "400 j"],
    ["VPC-SC", "Requêtes bloquées ou qui le seraient", "ge-security", "365 j"],
    ["SIEM", "Copie temps réel de ge-security", "Pub/Sub → outil du SOC", "Selon SOC"],
], [38 * mm, 70 * mm, 45 * mm, CW - 153 * mm])
S += [P("Dans la console : <b>Logs Explorer</b> → Affiner la portée → Stockage → <b>ge-security</b>. Pour du SQL et des tableaux de bord : <b>Log Analytics</b>.", "small"),
      P("Quand une alerte sonne", "h2")]
S += table(["Alerte", "Première question", "Si la réponse est non"], [
    ["Garde-fou modifié", "Une PR Terraform correspond ?", "Incident : terraform apply remet la configuration validée ; retirer les droits ; prévenir le RSSI"],
    ["Pic de blocages", "Un seul utilisateur, ou beaucoup ?", "Un seul : tentative d'abus (charte). Beaucoup : faux positif, ajuster par PR"],
    ["Service public / agent créé", "PR et inscription au registre ?", "Contacter l'auteur ; retirer allUsers, arrêter ou régulariser"],
    ["Demande Access Approval", "Le ticket support est-il connu ?", "Refuser ; sinon approuver pour la durée minimale"],
], [36 * mm, 50 * mm, CW - 86 * mm])
S += [PageBreak()]

# ================================================================== 11. Corrections
S += [P("TRANSPARENCE", "kicker"), P("Sept points de la note à corriger", "h1"),
      P("La note est solide sur le fond. Sept points sont inexacts techniquement ; les corriger évite qu'un auditeur, ou une équipe, "
        "s'appuie sur une protection qui n'existe pas.", "lead")]
S += table(["#", "La note dit", "La réalité", "Ce que nous faisons"], [
    ["1", "Exemple JSON Model Armor", "Noms de champs invalides : l'API refuse le JSON tel quel", "Syntaxe correcte dans le code et dans docs/05"],
    ["2", "La configuration de base détecte les données Acme", "Détecteurs orientés US : ni IBAN, ni NIR, ni CNI", "Configuration avancée, modèle DLP France"],
    ["3", "« Detect and redact »", "Dans Gemini Enterprise, une détection bloque : pas de masquage", "Formulation « détecter et bloquer »"],
    ["4", "Le filtre d'URL couvre Echo Leak", "Il ne bloque que les URL connues comme malveillantes", "Test T13, contrôle de sortie, confirmation humaine"],
    ["5", "Model Armor protège tous les modèles", "Dans GE, il ne filtre pas les agents personnalisés", "Plugin dans l'agent + plancher Agent Platform"],
    ["6", "Le SWP filtre la sortie de l'IA", "GE est un SaaS : il ne sort pas par le VPC Acme", "Agent Gateway pour GE ; SWP pour nos charges"],
    ["7", "WIF Entra / Okta", "Pas de connecteurs Workspace avec un IdP tiers ; changer efface l'historique", "Décision à prendre avant la production"],
], [8 * mm, 42 * mm, 62 * mm, CW - 112 * mm])
S += [callout("Point d'attention transverse : <b>l'injection indirecte</b> (document piégé). Model Armor filtre la question et la réponse, "
              "pas le contenu des documents récupérés. D'où trois défenses complémentaires : analyse avant indexation, filtre de sortie, "
              "confirmation humaine. Aucune ne suffit seule.", ORANGE, ORANGE_BG),
      PageBreak()]

# ================================================================== 12. À valider + conclusion
S += [P("TRANSPARENCE", "kicker"), P("Ce qui reste à valider sur le projet réel", "h1"),
      P("Le code est validé (<font name=\"Mono\" size=\"10\">terraform validate</font>, schéma du provider vérifié pour chaque ressource), "
        "les autotests de l'agent, du scanner et du contrôle de conformité passent. Il n'a pas encore été déployé chez Acme. "
        "Chaque point ci-dessous a une solution de repli.", "lead")]
S += table(["Point", "Repli"], [
    ["Le Secure Web Proxy exige-t-il un certificat sans inspection TLS ?", "Ajouter un certificat Certificate Manager"],
    ["Affichage de la confirmation d'un agent ADK dans l'interface GE", "Confirmation par message explicite dans l'agent"],
    ["Taille maximale d'un document analysé par Model Armor", "Quarantaine au-delà de 4 Mo, revue manuelle"],
    ["Noms exacts des méthodes surveillées par l'alerte Shadow AI", "Ajuster le filtre après le premier événement"],
    ["Champs exacts des journaux d'usage pour les tableaux de bord", "Ajuster les requêtes sur les premiers journaux réels"],
], [100 * mm, CW - 100 * mm])
S += [Spacer(1, 6), P("Pourquoi cette approche est la bonne", "h1")]
S += B(["<b>Elle protège dès la première semaine</b>, avec ce que Google fournit, sans attendre le code.",
        "<b>Elle ne casse rien</b> : ce qui peut bloquer passe d'abord par l'observation.",
        "<b>Elle dure</b> : tout finit en code relu, reproductible pour chaque domaine.",
        "<b>Elle se prouve</b> : 22 tests, une commande de conformité, un journal quotidien.",
        "<b>Elle corrige la note</b> là où elle promettait une protection qui n'existe pas."])
S += [Spacer(1, 8),
      callout("Prochaine étape proposée : un atelier de deux heures (sécurité, plateforme, PM, DPO) pour acter les quatre décisions de la page 2, "
              "puis le lancement de la phase 1 dans le projet de recette."),
      CondPageBreak(90 * mm), P("ANNEXE", "kicker"), P("Les livrables du projet 08", "h2")]
S += table(["Livrable", "Contenu"], [
    ["README.md", "Guide principal : mesures, phases, rôles, corrections"],
    ["docs/01 à 05", "Console pas à pas · Terraform par paliers · plan de tests · exploitation journalière · correspondance avec la note"],
    ["terraform/ + terraform/docs/", "Code et une fiche explicative par fichier pour les débutants"],
    ["agent/secure_agent", "Agent modèle : Model Armor, confirmation humaine, fail closed"],
    ["scripts/", "test_model_armor, verify_controls, daily_report, shadow_ai_inventory, scan_before_ingest"],
], [50 * mm, CW - 50 * mm])

doc.build(S)
print("written", OUT)
