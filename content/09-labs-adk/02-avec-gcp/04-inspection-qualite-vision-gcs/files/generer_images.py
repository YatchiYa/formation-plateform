"""Génère des photos FICTIVES de rondelles métalliques, conformes ou défectueuses.

Usage : python generer_images.py [dossier]   (par défaut ./images)
Écrit aussi verite_terrain.json (la bonne réponse, qui ne part PAS dans le bucket).
"""
import json
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

TAILLE = 512
# nom de fichier neutre -> défaut réel (le nom ne doit pas trahir la réponse)
PIECES = {
    "piece-01.png": "aucun",
    "piece-02.png": "rayure",
    "piece-03.png": "aucun",
    "piece-04.png": "fissure",
    "piece-05.png": "tache",
    "piece-06.png": "manque",
}


def dessiner_piece(defaut: str, graine: int) -> Image.Image:
    rnd = random.Random(graine)
    img = Image.new("RGB", (TAILLE, TAILLE), (235, 235, 230))  # fond du convoyeur
    d = ImageDraw.Draw(img)
    c, r_ext, r_int = TAILLE // 2, 190, 70
    d.ellipse([c - r_ext, c - r_ext, c + r_ext, c + r_ext], fill=(150, 155, 160), outline=(90, 90, 95), width=4)
    d.ellipse([c - r_int, c - r_int, c + r_int, c + r_int], fill=(235, 235, 230), outline=(90, 90, 95), width=4)
    for _ in range(400):  # grain du métal
        x, y = rnd.randint(c - r_ext, c + r_ext), rnd.randint(c - r_ext, c + r_ext)
        if r_int + 4 < ((x - c) ** 2 + (y - c) ** 2) ** 0.5 < r_ext - 4:
            g = rnd.randint(140, 170)
            d.point((x, y), fill=(g, g + 3, g + 6))
    if defaut == "rayure":
        d.line([(c - 160, c - 60), (c - 40, c - 150)], fill=(225, 225, 230), width=5)
    elif defaut == "fissure":
        x, y, pts = c + 75, c - 20, []
        for _ in range(7):
            pts.append((x, y))
            x, y = x + rnd.randint(10, 18), y + rnd.randint(-14, 14)
        d.line(pts, fill=(20, 20, 20), width=4)
    elif defaut == "tache":
        d.ellipse([c + 60, c + 70, c + 130, c + 125], fill=(120, 75, 35))  # rouille
    elif defaut == "manque":
        d.pieslice([c - r_ext, c - r_ext, c + r_ext, c + r_ext], 300, 330, fill=(235, 235, 230))
    return img.filter(ImageFilter.GaussianBlur(0.6))


def generer(dossier: Path) -> dict:
    dossier.mkdir(parents=True, exist_ok=True)
    for i, (nom, defaut) in enumerate(PIECES.items()):
        dessiner_piece(defaut, graine=i).save(dossier / nom)
    (dossier.parent / "verite_terrain.json").write_text(json.dumps(PIECES, indent=2), encoding="utf-8")
    return PIECES


if __name__ == "__main__":
    cible = Path(sys.argv[1] if len(sys.argv) > 1 else "images")
    print(f"{len(generer(cible))} images écrites dans {cible}/")
