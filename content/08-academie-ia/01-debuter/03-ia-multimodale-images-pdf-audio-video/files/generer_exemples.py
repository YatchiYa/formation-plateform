"""Génère les fichiers d'exemple FICTIFS du lab (aucune donnée réelle).

    python generer_exemples.py            # ticket.png, facture.png, rapport.pdf, tuto.mp4, memo.wav

- memo.wav : voix synthétique via un modèle TTS Gemini si une clé est disponible,
  sinon un simple bip (la transcription n'aura alors rien à transcrire).
- tuto.mp4 : nécessite ffmpeg (sinon l'étape est sautée).
"""
import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ICI = Path(__file__).parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def police(taille):
    try:
        return ImageFont.truetype(FONT, taille)
    except OSError:  # autre système : police par défaut de Pillow
        return ImageFont.load_default(taille)


def image_texte(lignes, largeur, hauteur, taille=22, fond="white"):
    img = Image.new("RGB", (largeur, hauteur), fond)
    d = ImageDraw.Draw(img)
    f = police(taille)
    y = 30
    for ligne in lignes:
        d.text((30, y), ligne, fill="black", font=f)
        y += int(taille * 1.5)
    return img


def ticket():
    lignes = [
        "   BOULANGERIE DU CANAL",
        "   (commerce fictif)",
        "   12 quai des Exemples, Lyon",
        "",
        "Date : 14/10/2026  08:42",
        "Ticket n° 004521",
        "--------------------------------",
        "2 x Croissant          2,60 EUR",
        "1 x Baguette tradition 1,30 EUR",
        "1 x Café allongé       2,10 EUR",
        "1 x Jus d'orange       3,50 EUR",
        "--------------------------------",
        "TOTAL TTC              9,50 EUR",
        "dont TVA 10 %          0,86 EUR",
        "Payé par carte",
        "",
        "   Merci de votre visite !",
    ]
    img = image_texte(lignes, 520, 720, fond=(250, 248, 240))
    # Effet « photo » : légère rotation, flou et grain
    img = img.rotate(3, expand=True, fillcolor=(120, 110, 100)).filter(ImageFilter.GaussianBlur(0.8))
    random.seed(1)
    px = img.load()
    for _ in range(6000):
        x, y = random.randrange(img.width), random.randrange(img.height)
        g = random.randint(150, 230)
        px[x, y] = (g, g, g)
    img.save(ICI / "ticket.png")


def facture():
    lignes = [
        "PAPETERIE MARTIN & FILS (société fictive)",
        "SIRET : 000 000 000 00000 (fictif)",
        "",
        "FACTURE N° F-2026-0193      Date : 02/10/2026",
        "Client : Atelier Nord (fictif)",
        "",
        "Désignation               Qté   PU HT   Total HT",
        "Ramette papier A4          10    4,50     45,00",
        "Stylos bille (boîte)        2    6,00     12,00",
        "Classeurs                   5    3,20     16,00",
        "",
        "                         Total HT        73,00 EUR",
        "                         TVA 20 %        14,60 EUR",
        "                         Total TTC       87,60 EUR",
        "",
        "Échéance : 01/11/2026 - Virement",
    ]
    image_texte(lignes, 820, 620, taille=20).save(ICI / "facture.png")


def rapport():
    c = canvas.Canvas(str(ICI / "rapport.pdf"), pagesize=A4)
    pages = [
        ("Rapport d'activité T3 2026 - Atelier Nord (entreprise fictive)", [
            "Résumé : le chiffre d'affaires du trimestre atteint 412 000 EUR,",
            "en hausse de 8 % par rapport au T2. La marge brute est de 31 %.",
            "Trois faits marquants : ouverture d'un second atelier à Villeurbanne,",
            "lancement de la gamme de mobilier en bois recyclé, et recrutement",
            "de 4 personnes (effectif total : 27).",
        ]),
        ("Ventes par canal", [
            "Boutique : 198 000 EUR (48 %)",
            "Site web : 151 000 EUR (37 %), +22 % sur le trimestre",
            "Professionnels : 63 000 EUR (15 %), en baisse de 5 %",
            "Le panier moyen en ligne passe de 184 EUR à 201 EUR.",
        ]),
        ("Risques et prochaines étapes", [
            "Risque principal : hausse du prix du bois de 12 % depuis juillet.",
            "Le délai de livraison moyen est remonté à 9 jours (objectif : 6).",
            "Décisions pour le T4 : renégocier deux contrats fournisseurs,",
            "automatiser le suivi des commandes, viser 450 000 EUR de CA.",
        ]),
    ]
    for i, (titre, lignes) in enumerate(pages, 1):
        c.setFont("Helvetica-Bold", 15)
        c.drawString(60, 780, titre)
        c.setFont("Helvetica", 12)
        for j, ligne in enumerate(lignes):
            c.drawString(60, 740 - 22 * j, ligne)
        c.setFont("Helvetica", 9)
        c.drawString(60, 40, f"Document fictif généré pour une formation - page {i}/3")
        c.showPage()
    c.save()


def video():
    if not shutil.which("ffmpeg"):
        print("ffmpeg absent : tuto.mp4 non généré")
        return
    etapes = ["1. Débranchez l'imprimante", "2. Ouvrez le capot avant",
              "3. Retirez la feuille coincée", "4. Refermez et rebranchez"]
    with tempfile.TemporaryDirectory() as tmp:
        for i, e in enumerate(etapes, 1):
            img = image_texte(["Tutoriel (fictif) : bourrage papier", "", e], 640, 360, taille=26,
                              fond=(225, 238, 250))
            img.save(f"{tmp}/f{i}.png")
        # 1 image toutes les 3 s -> vidéo de 12 s
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "1/3", "-i", f"{tmp}/f%d.png",
                        "-r", "10", "-pix_fmt", "yuv420p", str(ICI / "tuto.mp4")], check=True)


def ecrire_wav(chemin, pcm, taux=24000):
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taux)
        w.writeframes(pcm)


def audio():
    texte = ("Bonjour, c'est Camille du service achats. Petit rappel pour la réunion de jeudi : "
             "il faut valider le devis de quatre cent vingt euros pour les chaises, "
             "et envoyer le bon de commande avant vendredi midi. Merci !")
    try:
        from dotenv import load_dotenv
        from google import genai
        from google.genai import types
        load_dotenv()
        client = genai.Client()
        r = client.models.generate_content(
            model=os.environ.get("TTS_MODEL", "gemini-2.5-flash-preview-tts"),
            contents=f"Dis d'un ton naturel : {texte}",
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
        ecrire_wav(ICI / "memo.wav", r.candidates[0].content.parts[0].inline_data.data)
    except Exception as e:  # pas de clé, quota… : un bip de 2 s à 440 Hz
        print("TTS indisponible, bip de remplacement :", type(e).__name__)
        pcm = b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * t / 16000)))
                       for t in range(32000))
        ecrire_wav(ICI / "memo.wav", pcm, 16000)


if __name__ == "__main__":
    ticket(); facture(); rapport(); video(); audio()
    print("OK :", ", ".join(p.name for p in sorted(ICI.glob("*")) if p.suffix in {".png", ".pdf", ".mp4", ".wav"}))
