"""Génère produits.json : 60 fiches produit FICTIVES (marques et produits inventés).

Les 3 dernières fiches sont des quasi-doublons volontaires (même produit, autre rédaction)
pour l'exercice de dédoublonnage. Usage :  python generer_produits.py
"""
import json

FICHES = [
    # (catégorie, nom, description, prix en euros)
    ("Chaussures", "Trailrun Gecko", "Chaussure de trail à crampons de 5 mm pour terrains boueux et rocailleux, membrane respirante.", 129),
    ("Chaussures", "Asphalte Flow", "Chaussure de running route très amortie pour les longues sorties sur bitume, drop 8 mm.", 115),
    ("Chaussures", "Randonnée Cimes Mid", "Chaussure de randonnée tige mi-haute, imperméable, semelle adhérente pour la montagne.", 149),
    ("Chaussures", "Sandale Rivière", "Sandale de marche à séchage rapide, idéale pour traverser les cours d'eau en été.", 49),
    ("Chaussures", "Indoor Court", "Chaussure de salle pour badminton et squash, semelle gomme qui ne marque pas le sol.", 69),
    ("Chaussures", "Pantoufle Nuage", "Chausson d'intérieur en laine bouillie, semelle souple antidérapante, très chaud.", 35),
    ("Cuisine", "Bouilloire Thermia 1,7 L", "Bouilloire électrique en inox avec réglage de température de 40 à 100 °C pour le thé.", 59),
    ("Cuisine", "Friteuse à air Croustia", "Friteuse sans huile de 5 litres : frites et légumes croustillants avec une cuillère d'huile.", 99),
    ("Cuisine", "Blender Vortex", "Blender haute vitesse 1200 W pour smoothies, soupes et glace pilée, bol en verre.", 89),
    ("Cuisine", "Machine à pain Mie d'Or", "Machine à pain programmable, 12 programmes dont sans gluten, départ différé 13 h.", 79),
    ("Cuisine", "Cafetière à piston Bistro", "Cafetière à piston en verre borosilicate de 1 litre, filtre inox, sans électricité.", 29),
    ("Cuisine", "Balance culinaire Précise", "Balance de cuisine numérique, précision au gramme jusqu'à 5 kg, fonction tare.", 19),
    ("Bureau", "Fauteuil Ergo Dos+", "Fauteuil de bureau ergonomique avec soutien lombaire réglable et accoudoirs 4D.", 289),
    ("Bureau", "Bureau assis-debout Élévo", "Bureau à hauteur réglable électriquement, deux moteurs, mémoire de 3 positions.", 399),
    ("Bureau", "Repose-pieds Pivot", "Repose-pieds inclinable qui soulage le bas du dos et les jambes en position assise.", 39),
    ("Bureau", "Lampe de bureau Halo", "Lampe LED à intensité et température de couleur réglables, port USB de recharge.", 45),
    ("Bureau", "Support écran double Duo", "Bras articulé pour deux moniteurs jusqu'à 32 pouces, fixation par pince.", 79),
    ("Bureau", "Tapis de souris XXL Plaine", "Grand sous-main en tissu 90 x 40 cm, bords cousus, base caoutchouc.", 22),
    ("Audio", "Casque Silence Pro", "Casque sans fil à réduction active de bruit, 40 heures d'autonomie, idéal en avion.", 249),
    ("Audio", "Écouteurs Sport Fil-Libre", "Écouteurs sans fil résistants à la sueur avec crochets d'oreille pour courir.", 79),
    ("Audio", "Enceinte Galet", "Petite enceinte Bluetooth étanche IP67 qui flotte, pour la plage ou la piscine.", 59),
    ("Audio", "Barre de son Cinéma 2.1", "Barre de son avec caisson de basses sans fil pour améliorer le son de la télévision.", 199),
    ("Audio", "Platine vinyle Sillon", "Tourne-disque à entraînement par courroie avec préampli intégré et sortie USB.", 179),
    ("Audio", "Micro USB Podcast", "Microphone USB cardioïde pour podcast et visioconférence, prise casque intégrée.", 89),
    ("Jardin", "Tondeuse sans fil Herbo 40", "Tondeuse à batterie 40 V, coupe 42 cm, pour jardins jusqu'à 500 m².", 329),
    ("Jardin", "Tuyau extensible Flexi 30 m", "Tuyau d'arrosage extensible léger avec pistolet 7 jets, se rétracte après usage.", 39),
    ("Jardin", "Composteur Humus 400 L", "Composteur en plastique recyclé avec trappe de récolte, pour déchets de cuisine et de jardin.", 69),
    ("Jardin", "Sécateur Coupe-Net", "Sécateur à lames franches en acier forgé pour branches jusqu'à 22 mm.", 34),
    ("Jardin", "Récupérateur d'eau 300 L", "Cuve de récupération d'eau de pluie avec robinet et kit de raccordement à la gouttière.", 89),
    ("Jardin", "Hôtel à insectes Ruche", "Abri en bois pour abeilles solitaires et coccinelles, favorise la pollinisation.", 25),
    ("Bébé", "Poussette Citadine Plume", "Poussette compacte de 6 kg qui se plie d'une main, acceptée en cabine d'avion.", 259),
    ("Bébé", "Babyphone Vidéo Veille", "Écoute-bébé avec caméra, vision nocturne et capteur de température de la chambre.", 119),
    ("Bébé", "Porte-bébé Kangou", "Porte-bébé physiologique ventral et dorsal, de la naissance à 15 kg.", 99),
    ("Bébé", "Chaise haute Évolutive", "Chaise haute en bois réglable qui se transforme en chaise pour enfant jusqu'à 10 ans.", 149),
    ("Bébé", "Tapis d'éveil Jungle", "Tapis de jeu matelassé avec arche et jouets suspendus pour stimuler bébé.", 55),
    ("Bébé", "Gigoteuse Douillette TOG 2.5", "Turbulette en coton bio pour dormir au chaud sans couverture, de 6 à 18 mois.", 39),
    ("Camping", "Tente Dôme 3 places", "Tente de camping 3 places montage en 5 minutes, double toit imperméable 3000 mm.", 159),
    ("Camping", "Sac de couchage Grand Froid", "Duvet sarcophage confort -5 °C, garnissage synthétique, compressible.", 89),
    ("Camping", "Réchaud gaz Mini-Flamme", "Réchaud de randonnée ultraléger 80 g à visser sur cartouche de gaz.", 29),
    ("Camping", "Lampe frontale Lumen 400", "Frontale rechargeable 400 lumens avec faisceau rouge, étanche à la pluie.", 39),
    ("Camping", "Matelas autogonflant Repos", "Matelas de sol autogonflant de 5 cm, isolant, se roule dans un sac compact.", 69),
    ("Camping", "Gourde filtrante Source", "Bouteille avec filtre intégré qui rend potable l'eau des ruisseaux et des lacs.", 45),
    ("Bagagerie", "Valise cabine Escale 55", "Valise rigide 4 roues aux dimensions cabine, serrure TSA, 38 litres.", 129),
    ("Bagagerie", "Sac à dos urbain Navette", "Sac à dos 20 L avec compartiment ordinateur 15 pouces et poche anti-vol au dos.", 69),
    ("Bagagerie", "Sac de voyage Weekend", "Sac polochon en toile cirée de 45 L, idéal pour deux ou trois jours.", 79),
    ("Bagagerie", "Cubes de rangement Ordre", "Set de 6 pochettes de compression pour organiser les vêtements dans la valise.", 25),
    ("Bagagerie", "Pèse-bagage Envol", "Balance numérique à crochet pour vérifier le poids des bagages avant l'aéroport.", 12),
    ("Bagagerie", "Sac à dos randonnée Crête 45", "Sac de trek 45 litres avec dos ventilé, ceinture rembourrée et housse de pluie.", 119),
    ("Informatique", "Clavier mécanique Frappe", "Clavier mécanique compact rétroéclairé, switchs silencieux, connexion Bluetooth et USB-C.", 99),
    ("Informatique", "Souris verticale Poignet", "Souris ergonomique verticale qui réduit les tensions du poignet et du canal carpien.", 45),
    ("Informatique", "Webcam Full HD Visio", "Webcam 1080p avec micro stéréo et cache de confidentialité pour les réunions en ligne.", 59),
    ("Informatique", "Hub USB-C 7 en 1", "Adaptateur USB-C avec HDMI 4K, lecteur de cartes SD, 3 ports USB et charge 100 W.", 49),
    ("Informatique", "Disque SSD externe Rapide 1 To", "SSD portable 1 To jusqu'à 1000 Mo/s, résistant aux chutes, pour sauvegardes.", 109),
    ("Informatique", "Support PC portable Alu", "Support en aluminium qui surélève l'ordinateur portable à hauteur des yeux.", 35),
    ("Maison", "Aspirateur robot Furet", "Robot aspirateur laveur avec cartographie laser, programmable depuis le smartphone.", 299),
    ("Maison", "Purificateur d'air Brise", "Purificateur avec filtre HEPA pour pièces de 40 m², réduit pollens et poussières.", 149),
    ("Maison", "Ampoule connectée Teinte", "Ampoule LED Wi-Fi à couleurs variables, pilotable à la voix ou par application.", 19),
    # Quasi-doublons volontaires (même produit, rédaction différente)
    ("Chaussures", "Trail Gecko (coloris forêt)", "Chaussure de trail running avec crampons de 5 mm, pensée pour la boue et les rochers, tige respirante.", 129),
    ("Audio", "Casque Silence Pro - édition noire", "Casque Bluetooth à annulation active du bruit, autonomie 40 h, parfait pour les voyages en avion.", 249),
    ("Camping", "Tente Dôme 3 personnes", "Tente 3 personnes qui se monte en cinq minutes, double toit étanche 3000 mm.", 159),
]


def main():
    produits = [{"id": f"P{i:03d}", "categorie": c, "nom": n, "description": d, "prix": p}
                for i, (c, n, d, p) in enumerate(FICHES, 1)]
    assert len(produits) == 60
    with open("produits.json", "w", encoding="utf-8") as f:
        json.dump(produits, f, ensure_ascii=False, indent=1)
    print(f"{len(produits)} fiches écrites dans produits.json")


if __name__ == "__main__":
    main()
