"""Génère un rapport PDF fictif dont une partie des informations n'existe QUE dans les figures.

Entreprise imaginaire : « Verdalis », exploitant de 4 entrepôts frigorifiques.
Les graphiques sont dessinés avec Pillow puis insérés dans le PDF avec reportlab.
Usage : python make_pdf.py  ->  rapport_verdalis_t3.pdf
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

HERE = Path(__file__).parent
W, H = 1000, 620
COLORS = ["#2a6fdb", "#e8833a", "#3aa76d", "#c94c4c", "#8e6cc9"]


def font(size):
    try:  # police avec accents si elle est installée (Linux : paquet fonts-dejavu)
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def blank(title):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((W // 2, 30), title, fill="black", font=font(30), anchor="mt")
    return img, d


def bar_chart(title, labels, values, unit):
    img, d = blank(title)
    x0, y0, y1 = 110, H - 80, 110
    vmax = max(values) * 1.15
    d.line((x0, y1, x0, y0), fill="black", width=2)
    d.line((x0, y0, W - 40, y0), fill="black", width=2)
    step = (W - 40 - x0) / len(values)
    for i, (lab, v) in enumerate(zip(labels, values)):
        top = y0 - (y0 - y1) * v / vmax
        xa = x0 + i * step + step * 0.2
        d.rectangle((xa, top, xa + step * 0.6, y0), fill=COLORS[i % 5])
        d.text((xa + step * 0.3, top - 8), f"{v} {unit}", fill="black", font=font(22), anchor="mb")
        d.text((xa + step * 0.3, y0 + 12), lab, fill="black", font=font(22), anchor="mt")
    return img


def line_chart(title, labels, values, ymin, ymax, unit, threshold=None):
    img, d = blank(title)
    x0, y0, y1 = 110, H - 80, 110
    d.line((x0, y1, x0, y0), fill="black", width=2)
    d.line((x0, y0, W - 40, y0), fill="black", width=2)
    ys = lambda v: y0 - (y0 - y1) * (v - ymin) / (ymax - ymin)
    for g in range(5):
        v = ymin + g * (ymax - ymin) / 4
        d.text((x0 - 10, ys(v)), f"{v:g}", fill="gray", font=font(18), anchor="rm")
    if threshold is not None:
        d.line((x0, ys(threshold), W - 40, ys(threshold)), fill="#c94c4c", width=2)
        d.text((W - 45, ys(threshold) - 6), f"objectif {threshold:g} {unit}", fill="#c94c4c", font=font(18), anchor="rb")
    step = (W - 40 - x0) / len(values)
    pts = [(x0 + step * (i + 0.5), ys(v)) for i, v in enumerate(values)]
    d.line(pts, fill=COLORS[0], width=4)
    for (x, y), lab, v in zip(pts, labels, values):
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=COLORS[0])
        d.text((x + 12, y - 12), f"{v:g} {unit}", fill="black", font=font(22), anchor="lb")
        d.text((x, y0 + 12), lab, fill="black", font=font(22), anchor="mt")
    return img


def table_image(title, header, rows):
    img, d = blank(title)
    colw = (W - 80) / len(header)
    for r, row in enumerate([header] + rows):
        y = 100 + r * 60
        if r == 0:
            d.rectangle((40, y, W - 40, y + 60), fill="#dde6f5")
        for c, cell in enumerate(row):
            d.text((40 + c * colw + 12, y + 30), str(cell), fill="black", font=font(22), anchor="lm")
        d.line((40, y + 60, W - 40, y + 60), fill="gray")
    return img


def flow_diagram(title, steps):
    img, d = blank(title)
    bw, gap, y = 160, 30, 280
    x = (W - (len(steps) * bw + (len(steps) - 1) * gap)) / 2
    for i, s in enumerate(steps):
        d.rounded_rectangle((x, y, x + bw, y + 110), radius=14, outline=COLORS[i % 5], width=4)
        for j, line in enumerate(s.split("\n")):
            d.text((x + bw / 2, y + 40 + j * 30), line, fill="black", font=font(20), anchor="mm")
        if i < len(steps) - 1:
            d.line((x + bw, y + 55, x + bw + gap, y + 55), fill="black", width=3)
            d.polygon([(x + bw + gap, y + 55), (x + bw + gap - 10, y + 48), (x + bw + gap - 10, y + 62)], fill="black")
        x += bw + gap
    return img


PAGES = [
    ("1. Synthèse du trimestre",
     ["Ce rapport présente l'activité des quatre entrepôts frigorifiques Verdalis au troisième trimestre 2026.",
      "Le chiffre d'affaires du trimestre atteint 18,4 millions d'euros, en hausse de 6 % sur un an.",
      "La direction des opérations pilote un plan de réduction de la consommation énergétique.",
      "Les sections suivantes détaillent l'énergie, la disponibilité, l'architecture de supervision et la maintenance."],
     None),
    ("2. Consommation énergétique",
     ["La figure 1 présente la consommation électrique de chaque entrepôt sur le trimestre.",
      "Le plan de réduction cible en priorité le site le plus consommateur, où l'isolation des quais sera refaite."],
     bar_chart("Figure 1 - Consommation électrique T3 2026 (MWh)", ["Lyon", "Nantes", "Lille", "Toulouse"], [412, 287, 355, 198], "MWh")),
    ("3. Disponibilité des chambres froides",
     ["La figure 2 montre le taux de disponibilité mensuel des chambres froides, comparé à l'objectif contractuel.",
      "Un incident sur un compresseur a affecté un des mois du trimestre."],
     line_chart("Figure 2 - Disponibilité mensuelle des chambres froides (%)", ["Juillet", "Août", "Septembre"],
                [99.2, 96.8, 99.5], 95, 100, "%", threshold=98.5)),
    ("4. Architecture de supervision",
     ["La chaîne de supervision des températures est décrite par la figure 3.",
      "Chaque composant est redondé, sauf le tableau de bord, accessible en lecture seule aux clients."],
     flow_diagram("Figure 3 - Chaîne de supervision des températures",
                  ["Sondes\nthermiques", "Passerelle\nLoRaWAN", "Broker\nMQTT", "Base\nTimescaleDB", "Tableau\nde bord"])),
    ("5. Maintenance",
     ["Le tableau 1 récapitule les coûts de maintenance par famille d'équipement sur le trimestre.",
      "Les contrats de maintenance sont renégociés chaque année en janvier."],
     table_image("Tableau 1 - Coûts de maintenance T3 2026", ["Équipement", "Interventions", "Coût (k€)"],
                 [["Compresseurs", 14, 86], ["Portes rapides", 31, 42], ["Groupes électrogènes", 3, 19], ["Sondes", 57, 11]])),
    ("6. Perspectives",
     ["Au quatrième trimestre, Verdalis ouvrira un cinquième entrepôt à Rennes, d'une capacité de 12 000 palettes.",
      "Le budget d'investissement prévu pour 2027 est de 4,2 millions d'euros, dont 40 % pour l'efficacité énergétique."],
     None),
]


def build(path=HERE / "rapport_verdalis_t3.pdf"):
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Rapport trimestriel Verdalis T3 2026 (fictif)")
    pw, ph = A4
    for title, paras, fig in PAGES:
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, ph - 60, title)
        c.setFont("Helvetica", 11)
        y = ph - 90
        for p in paras:
            c.drawString(50, y, p)
            y -= 18
        if fig is not None:
            w = pw - 100
            c.drawImage(ImageReader(fig), 50, y - 20 - w * H / W, width=w, height=w * H / W)
        c.setFont("Helvetica", 8)
        c.drawString(50, 30, "Document fictif généré pour un lab de formation - Verdalis n'existe pas.")
        c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    print("PDF écrit :", build())
