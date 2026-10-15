"""Style commun des PDF du projet 09 (polices, couleurs, tableaux, blocs de code, encadrés, schémas).

À QUOI SERT CE FICHIER
    Ce n'est pas un script à lancer : c'est une « boîte à outils » partagée par les deux générateurs de PDF
        - scripts/build_pdf.py       -> Gemini-Enterprise-Agents-Guide-Equipes.pdf (PM / RH)
        - scripts/build_pdf_tuto.py  -> Gemini-Enterprise-Agents-Tutoriel-Pas-a-Pas.pdf (équipes techniques)
    Ils l'importent avec « from pdf_style import * » (ça marche parce que les trois fichiers sont dans
    le même dossier scripts/). Modifier ce fichier change donc l'apparence des DEUX PDF : régénérez les deux.

CE QU'IL CONTIENT
    - Enregistrement des polices (Inter + DejaVu Sans Mono), voir « Polices » ci-dessous.
    - Couleurs : NAVY, INK, MUTED, BLUE, SOFT, LINE, ORANGE, GREEN, *_BG, PHASE (4 couleurs), LVL (3 niveaux).
    - Mise en page A4 : W, H (taille de la page), M (marge 18 mm), CW (largeur utile du texte).
    - st : dictionnaire des styles de paragraphe (« h1 », « h2 », « body », « small », « code », ...).
    - Story : la liste des blocs du document, avec un « += » pratique.
    - Petits constructeurs de blocs : P, B, table, code, callout, banner, cards, steps, flow.
    - Ré-export des classes reportlab (BaseDocTemplate, Frame, PageBreak, Spacer, ...) utilisées par les builders.

PRÉREQUIS
    reportlab, installé pour le Python système : « python3 -c "import reportlab; print(reportlab.Version)" »
    affiche 3.6.8. ATTENTION : le .venv du projet n'a PAS reportlab (.venv/bin/python échoue avec
    ModuleNotFoundError). Utilisez donc « python3 », pas « .venv/bin/python ».
    Si reportlab manque : « sudo apt install python3-reportlab » ou « python3 -m pip install --user reportlab ».

POLICES (chemins en dur, à adapter si vous changez de machine)
    /home/yarab/.local/share/fonts/Inter/extras/ttf/  doit contenir Inter-Regular.ttf, Inter-Medium.ttf,
        Inter-SemiBold.ttf, Inter-Bold.ttf, Inter-Italic.ttf, Inter-Light.ttf
        (police Inter : https://rsms.me/inter/ , dossier « extras/ttf » de l'archive)
    /usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf  (paquet Debian/Ubuntu « fonts-dejavu-core »)
    Si un fichier manque, l'import échoue tout de suite avec une erreur du type
    « TTFError: Can't open file ".../Inter-Regular.ttf" » : installez la police ou corrigez la variable F.

ERREURS FRÉQUENTES
    - ModuleNotFoundError: No module named 'reportlab'  -> mauvais Python (le .venv) : lancez avec python3.
    - TTFError: Can't open file ...                      -> police absente, voir « Polices ».
    - ModuleNotFoundError: No module named 'pdf_style'   -> le builder a été déplacé hors de scripts/ :
                                                            il doit rester à côté de ce fichier.
"""
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)

# Polices : noms courts utilisés partout (« Inter-SB » = SemiBold, « Inter-B » = Bold, « Mono » = code).
F = "/home/yarab/.local/share/fonts/Inter/extras/ttf/"
for name, file in [("Inter", "Inter-Regular"), ("Inter-Md", "Inter-Medium"), ("Inter-SB", "Inter-SemiBold"),
                   ("Inter-B", "Inter-Bold"), ("Inter-I", "Inter-Italic"), ("Inter-L", "Inter-Light")]:
    pdfmetrics.registerFont(TTFont(name, F + file + ".ttf"))
pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Inter", normal="Inter", bold="Inter-SB", italic="Inter-I", boldItalic="Inter-SB")

# Couleurs de la charte (texte, accents, fonds des encadrés et des blocs de code).
NAVY = colors.HexColor("#14213D"); INK = colors.HexColor("#1C2333"); MUTED = colors.HexColor("#4A5568")
BLUE = colors.HexColor("#2F6FDE"); SOFT = colors.HexColor("#EEF2F9"); LINE = colors.HexColor("#D9DEE6")
WHITE = colors.white; ORANGE = colors.HexColor("#C75B12"); GREEN = colors.HexColor("#1E7A4C")
CODEBG = colors.HexColor("#F4F6FA"); ORANGE_BG = colors.HexColor("#FBF0E8"); GREEN_BG = colors.HexColor("#E8F3EC")
PHASE = [colors.HexColor("#2F6FDE"), colors.HexColor("#1F4FA8"), colors.HexColor("#1E7A4C"), colors.HexColor("#14213D")]

# Page A4 : marge M de chaque côté, CW = largeur utile pour les tableaux et encadrés.
W, H = A4
M = 18 * mm
CW = W - 2 * M

# Styles de paragraphe, appelés par leur clé : P("texte", "h2"), P("texte", "small"), ...
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
    """Liste des blocs du PDF, dans l'ordre d'affichage.

    « S += bloc » ajoute un bloc seul, « S += [b1, b2] » ajoute plusieurs blocs : les helpers peuvent
    donc renvoyer un bloc ou une liste sans que le builder ait à s'en soucier.
    """

    def __iadd__(self, other):
        (self.extend if isinstance(other, list) else self.append)(other)
        return self


# P : un paragraphe ; t accepte le mini-HTML reportlab (<b>, <i>, <br/>, <font ...>) ; s = clé de st.
def P(t, s="body"): return Paragraph(t, st[s])
# B : liste à puces, un paragraphe « • » par élément de items.
def B(items): return [Paragraph(i, st["bullet"], bulletText="•") for i in items]


def table(header, rows, widths, first_bold=True, head=NAVY):
    """Tableau à en-tête coloré et lignes alternées.

    header : titres des colonnes ; rows : liste de lignes (listes de textes) ; widths : largeur de chaque
    colonne (en mm, total = CW) ; first_bold : 1re colonne en gras ; head : couleur de l'en-tête.
    Moins de 9 lignes : le tableau reste sur une seule page ; sinon il peut se couper (en-tête répété).
    """
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
    """Bloc de code (police Mono, fond gris clair) ; text est affiché tel quel, sans retour à la ligne auto."""
    t = Table([[Preformatted(text.strip("\n"), st["code"])]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([t, Spacer(1, 5)])


def callout(text, color=BLUE, bg=SOFT):
    """Encadré mis en avant : barre verticale de couleur color à gauche, fond bg."""
    t = Table([[Paragraph(text, st["quote"])]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return KeepTogether([t, Spacer(1, 6)])


def banner(n, title, subtitle, meta, color, label="NIVEAU", kicker=None):
    """Bandeau pleine largeur : grand numéro n, titre + sous-titre au centre, lignes meta à droite.

    Le petit texte au-dessus du titre vaut kicker s'il est donné, sinon « label n » (ex. « NIVEAU 1 »).
    """
    left = Paragraph(f'<font name="Inter-B" size="28" color="#FFFFFF">{n}</font>', ParagraphStyle("lv", parent=st["body"], leading=32))
    mid = Paragraph(f'<font name="Inter-SB" size="8.5" color="#C9D3E6">{kicker or f"{label} {n}"}</font><br/>'
                    f'<font name="Inter-B" size="15" color="#FFFFFF">{title}</font><br/>'
                    f'<font name="Inter" size="9" color="#E3E8F2">{subtitle}</font>', st["banner"])
    right = Paragraph("<br/>".join(f'<font name="Inter" size="8" color="#E3E8F2">{m}</font>' for m in meta), st["banner"])
    t = Table([[left, mid, right]], colWidths=[15 * mm, 100 * mm, CW - 115 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), color), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return [t, Spacer(1, 8)]



# Couleurs des 3 niveaux d'autonomie (couverture du guide PM / RH).
LVL = [colors.HexColor("#2F6FDE"), colors.HexColor("#1F4FA8"), colors.HexColor("#1E7A4C")]


def cards(items, color=BLUE):
    """Cartes côte à côte : [(titre, texte), ...]."""
    w = (CW - 4 * mm * (len(items) - 1)) / len(items)
    cells = [[Paragraph(f'<font name="Inter-SB" size="10.5" color="#14213D">{t}</font><br/><br/>{d}', st["cell"]) for t, d in items]]
    t = Table(cells, colWidths=[w] * len(items))
    s = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
         ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]
    for i in range(len(items)):
        s += [("BACKGROUND", (i, 0), (i, 0), SOFT), ("LINEABOVE", (i, 0), (i, 0), 3, color)]
    t.setStyle(TableStyle(s))
    return KeepTogether([t, Spacer(1, 8)])


def steps(items):
    """Liste numérotée : une pastille bleue 1, 2, 3... devant chaque texte de items."""
    rows = [[Paragraph(f'<font name="Inter-B" size="12" color="#FFFFFF">{i}</font>', st["cell"]), Paragraph(x, st["body"])]
            for i, x in enumerate(items, 1)]
    t = Table(rows, colWidths=[9 * mm, CW - 9 * mm])
    s = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 3),
         ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LINEBELOW", (1, 0), (1, -1), 0.3, LINE)]
    s += [("BACKGROUND", (0, i), (0, i), BLUE) for i in range(len(items))]
    t.setStyle(TableStyle(s))
    return KeepTogether([t, Spacer(1, 8)])


def flow(boxes):
    """Schéma horizontal : boîtes reliées par des flèches ; boxes = [(titre, description), ...]."""
    cells, widths = [], []
    bw = (CW - 8 * mm * (len(boxes) - 1)) / len(boxes)
    for i, (t, d) in enumerate(boxes):
        if i:
            cells.append(Paragraph('<font name="Inter-B" size="16" color="#2F6FDE">→</font>', st["cell"])); widths.append(8 * mm)
        cells.append(Paragraph(f'<font name="Inter-SB" color="#FFFFFF">{t}</font><br/><font color="#E3E8F2" size="7.8">{d}</font>', st["cell"]))
        widths.append(bw)
    t = Table([cells], colWidths=widths)
    s = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
         ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
    s += [("BACKGROUND", (i, 0), (i, 0), NAVY) for i in range(0, len(cells), 2)]
    t.setStyle(TableStyle(s))
    return KeepTogether([t, Spacer(1, 8)])


