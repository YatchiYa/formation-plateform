"""Génère le PDF « Les agents dans Gemini Enterprise » pour les PM et l'équipe RH (projet 09).

À QUOI SERT CE SCRIPT
    Il fabrique le guide non technique destiné aux chefs de projet (PM) et à l'équipe RH :
    créer un agent soi-même, en réutiliser un, demander la connexion d'un agent développé, pourquoi un cadre.
    Fichier produit : Gemini-Enterprise-Agents-Guide-Equipes.pdf, à la RACINE du projet (14 pages A4).
    Le même contenu existe en présentation : scripts/build_pptx.js -> Gemini-Enterprise-Agents-Guide-Equipes.pptx.
    Pensez à modifier les deux si vous changez le message.

COMMENT LE LANCER (depuis la racine du projet 09-agents-multi-projets-gemini-enterprise)
    python3 scripts/build_pdf.py
    -> affiche « written .../scripts/../Gemini-Enterprise-Agents-Guide-Equipes.pdf »
    - Aucun argument : le chemin de sortie est fixé par OUT (dossier parent de scripts/). Le fichier
      existant est ÉCRASÉ. Pour produire ailleurs, copiez build_pdf.py ET pdf_style.py dans un dossier
      <x>/scripts/ et lancez-le là : le PDF sort dans <x>/.
    - Utilisez le Python SYSTÈME (python3, reportlab 3.6.8). Le .venv du projet n'a PAS reportlab.
    - Prérequis détaillés (reportlab, polices Inter et DejaVu Sans Mono) : voir l'en-tête de pdf_style.py.

CE QU'IL LIT / ÉCRIT
    Lit : pdf_style.py (style) et les polices. Tout le texte est écrit en dur dans ce fichier.
    Écrit : uniquement le PDF ci-dessus.

OÙ MODIFIER LE CONTENU
    - Couverture (page 1) : fonction on_cover (titres, sous-titre, version / date).
    - En-tête et pied des autres pages (« Octobre 2026 · v1.0 », numéro) : fonction on_page.
    - Métadonnées du PDF (titre, auteur, sujet) : appel BaseDocTemplate(...).
    - Corps : une section par bloc « # ===... N. Titre · page P », dans l'ordre des pages.
      Chaque section se termine par PageBreak() : 1 section = 1 page. Si vous ajoutez du texte,
      vérifiez qu'elle tient encore sur sa page (sinon le nombre de pages augmente).
    - Mise en forme (P, B, table, cards, steps, flow, callout, banner, code) : voir pdf_style.py.

VÉRIFIER APRÈS RÉGÉNÉRATION
    pdfinfo Gemini-Enterprise-Agents-Guide-Equipes.pdf | grep Pages     -> Pages: 14
    (sans pdfinfo : python3 -c "from pypdf import PdfReader; print(len(PdfReader('Gemini-Enterprise-Agents-Guide-Equipes.pdf').pages))")
    Puis ouvrez le PDF et parcourez-le : une section qui déborde crée une page presque vide.

ERREURS FRÉQUENTES
    - ModuleNotFoundError: No module named 'reportlab' -> lancé avec .venv/bin/python : utilisez python3.
    - TTFError: Can't open file ".../Inter-....ttf"     -> police manquante (voir pdf_style.py).
    - ModuleNotFoundError: No module named 'pdf_style'  -> ce fichier a été déplacé sans pdf_style.py.
    - Erreur « paraparser » / balise inattendue          -> mini-HTML mal fermé dans un texte (<b> sans </b>,
                                                           « & » seul : écrire « &amp; »).
"""
import os

from pdf_style import *  # noqa: F401,F403  (polices, couleurs, helpers communs)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Gemini-Enterprise-Agents-Guide-Equipes.pdf")


def on_cover(c, d):
    """Dessine la couverture (page 1) : fond bleu nuit, 3 barres « niveaux », titre, version et date."""
    c.saveState()
    c.setFillColor(NAVY); c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(0, 0, 9 * mm, H, fill=1, stroke=0)
    labels = ["Vous créez", "Vous réutilisez", "On connecte"]
    for i in range(3):
        x = W - 92 * mm + i * 27 * mm
        c.setFillColor(LVL[i]); c.rect(x, 40 * mm, 25 * mm, (18 + i * 16) * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#E3E8F2")); c.setFont("Inter-SB", 7.5)
        c.drawString(x + 2.5 * mm, 40 * mm + (18 + i * 16) * mm - 6 * mm, f"{i + 1} · {labels[i]}")
    c.setFillColor(colors.HexColor("#8FB3F5")); c.setFont("Inter-SB", 10)
    c.drawString(26 * mm, H - 45 * mm, "POUR LES CHEFS DE PROJET ET L'ÉQUIPE RH  ·  ACME")
    c.setFillColor(colors.HexColor("#F6F7F4")); c.setFont("Inter-B", 32)
    c.drawString(26 * mm, H - 70 * mm, "Les agents dans")
    c.drawString(26 * mm, H - 83 * mm, "Gemini Enterprise")
    c.setFont("Inter-L", 13.5); c.setFillColor(colors.HexColor("#C9D3E6"))
    for i, line in enumerate(["Ce que vous pouvez faire vous-même, ce que vous pouvez demander,",
                              "comment ça marche, et pourquoi il y a un cadre."]):
        c.drawString(26 * mm, H - 100 * mm - i * 7 * mm, line)
    c.setFont("Inter", 9.5)
    c.drawString(26 * mm, 30 * mm, "Version 1.0  ·  Octobre 2026  ·  Diffusion interne")
    c.drawString(26 * mm, 24 * mm, "Référence technique : projet 09-agents-multi-projets-gemini-enterprise")
    c.restoreState()


def on_page(c, d):
    """En-tête et pied de page de toutes les pages après la couverture (filet, titre courant, numéro)."""
    c.saveState()
    c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(M, H - 12 * mm, W - M, H - 12 * mm)
    c.setFont("Inter-SB", 7.5); c.setFillColor(BLUE); c.drawString(M, H - 10 * mm, "GEMINI ENTERPRISE · LES AGENTS")
    c.setFont("Inter", 7.5); c.setFillColor(MUTED); c.drawRightString(W - M, H - 10 * mm, "Diffusion interne")
    c.line(M, 12 * mm, W - M, 12 * mm)
    c.drawString(M, 8 * mm, "Octobre 2026 · v1.0")
    c.drawRightString(W - M, 8 * mm, f"{d.page}")
    c.restoreState()


# Document : la page 1 utilise le modèle « cover », les suivantes le modèle « page ».
doc = BaseDocTemplate(OUT, pagesize=A4, title="Les agents dans Gemini Enterprise",
                      author="Équipe projet Gemini Enterprise", subject="Créer, réutiliser et connecter des agents : guide pour les équipes",
                      leftMargin=M, rightMargin=M, topMargin=18 * mm, bottomMargin=18 * mm)
frame = Frame(M, 16 * mm, CW, H - 34 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=on_cover), PageTemplate(id="page", frames=[frame], onPage=on_page)])

S = Story([NextPageTemplate("page"), PageBreak()])

# ================================================================== 1. En une page · page 2
S += [P("SYNTHÈSE", "kicker"), P("En une page", "h1"),
      P("Gemini Enterprise est l'assistant IA de Acme. En plus de répondre aux questions, il peut accueillir des "
        "<b>agents</b> : des assistants spécialisés dans une tâche précise. Ce document explique, sans jargon, "
        "<b>comment obtenir un agent</b>, <b>ce que vous pouvez faire vous-même</b>, et <b>pourquoi il y a un cadre</b>.", "lead"),
      P("Il y a trois façons d'avoir un agent", "h2")]
S += cards([("1 · Vous le créez", "Dans l'app Gemini Enterprise, <b>sans code</b> : vous décrivez ce que vous voulez, vous choisissez les sources "
             "(Drive, documents…), vous testez, vous partagez.<br/><br/><b>Délai :</b> quelques minutes.<br/><b>Qui :</b> vous."),
            ("2 · Vous en réutilisez un", "Un agent déjà publié par une autre équipe (ex. « Stock magasin ») peut devenir <b>une étape</b> "
             "de votre propre agent.<br/><br/><b>Délai :</b> immédiat.<br/><b>Qui :</b> vous."),
            ("3 · On connecte le vôtre", "Un agent <b>développé</b> par une équipe technique, hébergé ailleurs (autre projet Google Cloud), "
             "est <b>branché</b> dans l'app.<br/><br/><b>Délai :</b> quelques jours (vérifications).<br/><b>Qui :</b> admin ou équipe habilitée.")])
S += [P("Ce qu'il faut retenir", "h2")]
S += B(["<b>Vous êtes autonomes</b> pour créer et composer des agents avec ce qui est déjà en place.",
        "<b>Faire entrer quelque chose de nouveau</b> (un agent développé, un nouvel outil, une nouvelle source) passe par une "
        "demande : c'est volontaire, pour protéger les données.",
        "<b>Un agent ne voit jamais plus que vous</b> : il respecte les droits d'accès des documents de chaque utilisateur.",
        "<b>Le partage d'un agent</b> à des collègues est validé par l'administrateur, pour éviter la diffusion d'un agent non vérifié.",
        "<b>Pour l'équipe RH</b> : les données personnelles des salariés demandent un avis du DPO avant tout agent qui y accède (page 6)."])
S += [Spacer(1, 4), callout("La règle simple : <b>composer, c'est libre ; connecter, c'est encadré.</b>"), PageBreak()]

# ================================================================== 2. C'est quoi un agent · page 3
S += [P("COMPRENDRE", "kicker"), P("Qu'est-ce qu'un agent ?", "h1"),
      P("L'assistant Gemini Enterprise répond à des questions générales en cherchant dans les outils de l'entreprise. Un "
        "<b>agent</b> est un assistant <b>spécialisé</b> : il a une mission précise, des consignes, des sources choisies, "
        "et parfois des actions (envoyer un résumé, remplir un tableau).", "lead")]
S += table(["", "L'assistant", "Un agent"], [
    ["Mission", "Tout sujet", "Une tâche précise (ex. répondre sur la politique de télétravail)"],
    ["Sources", "Tout ce à quoi vous avez accès", "Seulement les sources choisies pour la mission"],
    ["Consignes", "Générales", "Ton, format, étapes, limites définies une fois pour toutes"],
    ["Régularité", "À la demande", "À la demande, ou planifié (ex. chaque lundi)"],
    ["Partage", "—", "Peut être partagé à une équipe : tout le monde a les mêmes réponses"],
], [28 * mm, 55 * mm, CW - 83 * mm])
S += [P("Deux familles d'agents", "h2")]
S += cards([("Agents sans code", "Créés dans l'app web par n'importe quel utilisateur autorisé. Ils s'appuient sur les sources et outils "
             "déjà connectés. Idéal pour les besoins métier : FAQ, résumés, rédaction, suivi."),
            ("Agents développés", "Écrits par une équipe technique (ex. l'agent « Stock magasin » de l'équipe Supply). Ils accèdent à des "
             "systèmes internes, font des calculs, suivent une logique précise. Ils sont <b>connectés</b> à l'app par l'équipe "
             "habilitée.")], color=colors.HexColor("#1F4FA8"))
S += [callout("Un agent n'a pas d'accès « en propre » aux documents : il cherche <b>avec les droits de la personne qui l'utilise</b>. "
              "Un collègue qui n'a pas accès à un dossier RH n'y aura pas accès en passant par un agent.", GREEN, GREEN_BG),
      PageBreak()]

# ================================================================== 3. Les 3 niveaux · page 4
S += [P("QUI PEUT FAIRE QUOI", "kicker"), P("Trois niveaux d'autonomie", "h1"),
      P("Chacun a le niveau qui correspond à son besoin. La grande majorité des utilisateurs n'a besoin que du niveau 1.", "lead")]
S += table(["", "1 · Utilisateur", "2 · Équipe habilitée (« builder »)", "3 · Administrateur"], [
    ["Qui", "Tout collaborateur ayant accès à l'app", "2-3 équipes techniques certifiées", "Équipe plateforme Gemini Enterprise"],
    ["Où", "App web Gemini Enterprise", "App web + console Google Cloud", "Console Google Cloud"],
    ["Peut", "Créer des agents sans code ; réutiliser les agents publiés ; partager (avec validation)",
     "Connecter <b>ses</b> agents développés, y compris depuis un autre projet ; choisir qui les utilise",
     "Tout : sources, outils, sécurité, validation des partages"],
    ["Ne peut pas", "Brancher un agent ou un outil externe", "Toucher aux réglages de sécurité de l'app", "—"],
    ["Délai type", "Minutes", "Heures", "Jours (selon la file)"],
], [24 * mm, 48 * mm, 52 * mm, CW - 124 * mm])
S += [Spacer(1, 4), P("Pourquoi un niveau « builder » ?", "h2"),
      P("Sans lui, chaque nouvelle version d'un agent technique demande un ticket à l'équipe plateforme. Avec lui, une équipe "
        "technique habilitée publie ses agents elle-même, <b>sans pouvoir modifier la sécurité</b> de l'app : son rôle "
        "Google Cloud est limité aux agents. Les ajouts restent tracés et signalés à la sécurité."),
      callout("Pour le PM : le niveau 2 réduit les délais pour les équipes qui livrent souvent ; il se décide équipe par équipe, "
              "après une charte et une courte formation."),
      PageBreak()]

# ================================================================== 4. Niveau 1 pas à pas · page 5
S += banner(1, "Créer votre agent, vous-même", "Dans l'app web Gemini Enterprise, sans code, sans accès technique",
            ["Qui : tout utilisateur autorisé", "Durée : 10 à 30 minutes", "Outil : Workflow Builder"], LVL[0])
S += steps(["Ouvrez l'app Gemini Enterprise → menu <b>Agents</b> → <b>Créer un agent</b>.",
            "Décrivez en français ce que vous voulez : <i>« Un agent qui répond aux questions des managers sur la politique de "
            "télétravail, à partir du guide RH 2026, en citant le paragraphe. »</i> L'outil propose les consignes et les étapes.",
            "Choisissez les <b>sources</b> : uniquement celles déjà connectées (dossier Drive « Politiques RH », SharePoint…).",
            "Si besoin, ajoutez une <b>étape « agent existant »</b> : un agent déjà publié par une autre équipe.",
            "<b>Testez</b> avec de vraies questions. Ajustez les consignes (ton, longueur, ce qu'il doit refuser).",
            "<b>Publiez</b>, puis <b>partagez</b> avec un groupe (ex. « Managers Lille ») : la demande part en validation."])
S += [P("Ce que vous pouvez utiliser dans votre agent", "h2")]
S += table(["Disponible", "Exemples", "Si ce n'est pas là"], [
    ["Sources déjà connectées", "Google Drive, SharePoint, Gmail, Agenda, Jira…", "Demande à l'admin (nouvelle source)"],
    ["Outils déjà connectés", "Lire / écrire dans un tableau Google Sheets (outil MCP), créer un ticket", "Demande à l'admin (nouvel outil)"],
    ["Agents déjà publiés", "« Stock magasin (Supply) », « Prix et promotions »", "Demande de connexion (niveau 2 ou 3)"],
    ["Planification", "Tous les lundis à 8 h, résumé envoyé", "Disponible si la fonctionnalité est activée"],
], [42 * mm, 78 * mm, CW - 120 * mm])
S += [callout("Bon réflexe : écrire dans les consignes ce que l'agent <b>doit refuser</b> (« Ne réponds pas aux questions sur des cas "
              "individuels de salariés ; renvoie vers ton RRH »)."), PageBreak()]

# ================================================================== 5. Exemples RH · page 6
S += [P("POUR L'ÉQUIPE RH", "kicker"), P("Idées d'agents, et limites à respecter", "h1")]
S += table(["Agent", "Mission", "Sources", "Niveau", "Avis DPO"], [
    ["FAQ politiques RH", "Répondre aux managers sur télétravail, congés, mobilité, en citant le texte", "Dossier « Politiques RH » (documents publics internes)", "1", "Non"],
    ["Accueil nouvel arrivant", "Guider la première semaine : démarches, contacts, formations", "Livret d'accueil, planning type", "1", "Non"],
    ["Préparation d'entretien annuel", "Proposer une trame et des questions selon le poste", "Référentiel de compétences", "1", "Non"],
    ["Synthèse des offres internes", "Résumer chaque lundi les nouvelles offres de mobilité", "Dossier des offres publiées", "1 (planifié)", "Non"],
    ["Questions paie individuelles", "Répondre sur SA fiche de paie", "Système de paie", "3 (développé)", "<b>Oui</b>"],
    ["Analyse de dossiers salariés", "Résumer des dossiers individuels", "Dossiers du personnel", "3 (développé)", "<b>Oui, préalable</b>"],
], [36 * mm, 50 * mm, 44 * mm, 18 * mm, CW - 148 * mm])
S += [P("Les données personnelles des salariés", "h2"),
      P("Les agents qui touchent à des <b>données personnelles</b> (paie, santé, évaluations, dossiers disciplinaires) relèvent "
        "du RGPD. Avant d'en créer un :")]
S += B(["<b>Avis du DPO</b> : finalité, minimisation, durée de conservation, information des salariés (et du CSE si nécessaire).",
        "<b>Pas de copie</b> de ces données dans un dossier partagé « pour que l'agent les trouve » : l'agent doit lire la source "
        "d'origine, avec ses droits d'accès.",
        "<b>Partage restreint</b> au groupe RH concerné, jamais à toute l'entreprise.",
        "Les questions et réponses sont journalisées pour la sécurité, avec un accès limité et une durée de conservation bornée."])
S += [callout("Protection automatique : si une question ou une réponse contient un numéro de sécurité sociale, un IBAN ou un "
              "numéro de carte d'identité, Gemini Enterprise <b>bloque</b> l'échange (filtre de sécurité Model Armor).", GREEN, GREEN_BG),
      PageBreak()]

# ================================================================== 6. Partager · page 7
S += [P("PARTAGER", "kicker"), P("Partager un agent avec vos collègues", "h1"),
      P("Un agent utile à une personne l'est souvent à toute une équipe. Le partage est simple, mais <b>validé</b> : "
        "c'est ce qui garantit qu'un agent diffusé largement a été vérifié.", "lead")]
S += flow([("Vous", "publiez et partagez votre agent avec un groupe"), ("Demande", "envoyée automatiquement à l'administrateur"),
           ("Validation", "l'admin vérifie sources, consignes et destinataires"), ("Équipe", "l'agent apparaît dans sa galerie d'agents")])
S += table(["Réglage de l'app", "Choix recommandé", "Pourquoi"], [
    ["Création d'agents par les utilisateurs", "Activée, d'abord pour un groupe pilote", "Apprendre, mesurer les usages"],
    ["Partage d'agents", "Activé", "Mutualiser les bons agents"],
    ["Partage sans validation de l'admin", "Désactivé", "Pas de diffusion d'un agent non vérifié"],
    ["Partage à des groupes entiers", "Avec validation", "Un groupe peut compter des milliers de personnes"],
    ["Galerie d'agents", "Activée", "Vitrine des agents disponibles"],
], [55 * mm, 55 * mm, CW - 110 * mm])
S += [P("Ce que l'administrateur vérifie en quelques minutes : les sources utilisées, les consignes (ce que l'agent refuse), "
        "et que les destinataires ont bien le droit de voir ces sources.", "small"), PageBreak()]

# ================================================================== 7. Connecter un agent développé · page 8
S += banner(2, "Connecter un agent développé par une équipe", "Quand l'agent est écrit en code et tourne dans un autre projet Google Cloud",
            ["Qui : équipe habilitée ou admin", "Délai : quelques jours", "Guides : docs/02, 03 et 07"], LVL[1], kicker="NIVEAUX 2 ET 3")
S += [P("Comment ça marche, en une image", "h2")]
S += flow([("Projet de l'équipe Supply", "l'agent « Stock magasin » y est développé et hébergé"),
           ("Autorisation", "l'équipe Supply autorise notre app à appeler son agent"),
           ("App Gemini Enterprise", "l'agent est ajouté et décrit"),
           ("Utilisateurs", "le groupe autorisé le trouve dans la galerie")])
S += B(["<b>Les utilisateurs n'ont besoin d'aucun accès</b> au projet de l'équipe Supply : c'est l'app qui appelle l'agent.",
        "<b>L'équipe propriétaire garde la main</b> : c'est elle qui autorise l'app à utiliser son agent, et elle peut retirer cette autorisation.",
        "<b>Un agent peut en appeler un autre</b> : l'« Assistant magasin » demande le stock à l'agent de l'équipe Supply, au lieu de "
        "réinventer la fonction. Chaque équipe reste responsable de son agent.",
        "<b>Trois techniques possibles</b> (hébergement Google géré, conteneur Cloud Run, catalogue central) : choix de l'équipe "
        "technique, sans effet pour l'utilisateur.",
        "<b>Si l'agent est dans le même projet que l'app</b>, c'est encore plus simple : aucune autorisation à donner, l'agent est "
        "ajouté en quelques minutes (tutoriel pas à pas : docs/02)."])
S += [P("Exemple concret, déjà réalisé dans le projet de référence", "h2")]
S += table(["Élément", "Où il vit", "Ce qu'il fait"], [
    ["Agent « Stock magasin »", "Projet de l'équipe Supply", "Donne le stock d'un article par magasin"],
    ["Agent « Assistant magasin »", "Projet de l'app Gemini Enterprise", "Conseille les vendeurs ; demande le stock à l'agent Supply"],
    ["App Gemini Enterprise", "Projet de l'app", "Propose les deux agents aux vendeurs autorisés"],
], [52 * mm, 55 * mm, CW - 107 * mm])
S += [PageBreak()]

# ================================================================== 8. Comment demander · page 9
S += [P("DEMANDER", "kicker"), P("Comment demander la connexion d'un agent", "h1")]
S += steps(["<b>Le PM ou l'équipe métier</b> décrit le besoin : mission, utilisateurs visés, sources ou systèmes concernés, données personnelles ou non.",
            "<b>L'équipe technique</b> développe l'agent (ou il existe déjà) et l'héberge dans son projet, en Europe.",
            "<b>La sécurité</b> vérifie la checklist ci-dessous (et le DPO si données personnelles).",
            "<b>L'équipe habilitée ou l'admin</b> connecte l'agent à l'app et l'autorise pour le groupe visé.",
            "<b>Les utilisateurs</b> le trouvent dans la galerie d'agents. Le PM suit l'adoption et les retours."])
S += [P("La checklist avant connexion", "h2")]
S += table(["Point vérifié", "Pourquoi"], [
    ["Hébergé en Europe", "Les données de Acme restent dans l'UE"],
    ["Filtre de sécurité (Model Armor) intégré à l'agent", "Le filtre de l'app ne s'applique pas automatiquement aux agents développés"],
    ["Identité technique propre à l'agent, droits minimum", "Un problème sur un agent ne touche pas les autres"],
    ["Confirmation humaine avant toute action qui modifie", "L'agent propose, l'humain valide"],
    ["Description claire", "C'est elle qui fait choisir le bon agent"],
    ["Groupe d'utilisateurs précis", "Pas d'ouverture à toute l'entreprise par défaut"],
    ["Propriétaire et contact identifiés", "Savoir qui appeler en cas de problème"],
    ["Avis DPO si données personnelles", "Obligation RGPD"],
], [80 * mm, CW - 80 * mm])
S += [callout("Délai indicatif : agent sans données personnelles, 2 à 5 jours ouvrés ; avec données personnelles, selon l'avis du DPO."),
      PageBreak()]

# ================================================================== 8 bis. Agent déjà dans un registre · page 10
S += [P("CAS FRÉQUENT", "kicker"), P("Une équipe a déjà un agent dans son catalogue ?", "h1"),
      P("Beaucoup d'équipes techniques ont déjà des agents, rangés dans <b>leur</b> catalogue d'agents (Agent Registry, dans "
        "<b>leur</b> projet Google Cloud). Bonne nouvelle : <b>pas besoin de les refaire</b>. Le catalogue sert à les retrouver "
        "et à savoir comment les brancher ; ensuite, trois voies.", "lead")]
S += table(["", "Voie 1 · Agent hébergé chez Google", "Voie 2 · Agent hébergé ailleurs", "Voie 3 · Par notre catalogue"], [
    ["Pour quel agent", "Agent développé et hébergé sur la plateforme Google (Agent Runtime)", "Agent hébergé sur Cloud Run ou ailleurs, au standard A2A", "Les deux"],
    ["Ce que l'équipe fait", "Une autorisation dans son projet", "Une autorisation sur son service", "Fournit la « carte » de son agent"],
    ["Ce que nous faisons", "Ajout dans l'app", "Ajout dans l'app", "Inscription dans notre catalogue, contrôle de passage, ajout"],
    ["Délai", "Le jour même", "Le jour même", "Quelques jours (mise en place)"],
    ["Contrôle", "Standard", "L'agent doit se protéger lui-même", "Le plus fort : tout passe par un point de contrôle"],
], [28 * mm, 50 * mm, 48 * mm, CW - 126 * mm])
S += [P("Ce que l'équipe nous envoie (une seule fois)", "h2")]
S += table(["Information", "Exemple"], [
    ["Projet et nom de l'agent dans son catalogue", "acme-agents-pricing · « pricing »"],
    ["Type : hébergé chez Google, ou ailleurs (A2A)", "Hébergé chez Google"],
    ["Nom et description pour les utilisateurs", "« Prix et promotions » : prix et promotions d'un article"],
    ["Groupe d'utilisateurs visé", "Vendeurs Lille"],
    ["Données utilisées, données personnelles ?", "Prix publics, non"],
    ["Protection intégrée, confirmation avant action", "Oui, oui"],
    ["Propriétaire et contact", "equipe-pricing@acme.example"],
], [80 * mm, CW - 80 * mm])
S += [callout("Pour le PM : avec ces informations, la plupart des agents déjà existants sont disponibles dans l'app <b>le jour même</b>. "
              "Mode d'emploi technique complet : <font name=\"Mono\" size=\"8.5\">docs/04-agents-deja-dans-un-registry.md</font>."),
      PageBreak()]

# ================================================================== 9. Pourquoi ce cadre · page 11
S += [P("POURQUOI", "kicker"), P("Pourquoi ce cadre, et pas « tout ouvert » ?", "h1"),
      P("Le cadre n'est pas là pour freiner : il permet d'ouvrir largement la création d'agents <b>parce que</b> les points "
        "sensibles sont maîtrisés.", "lead")]
S += table(["Risque", "Ce qui pourrait arriver", "Ce qui l'empêche"], [
    ["Fuite de données", "Un agent diffusé à tous montre des informations à des personnes non autorisées",
     "L'agent respecte les droits de chaque utilisateur ; le partage est validé"],
    ["Agent non maîtrisé (« Shadow AI »)", "Une équipe branche un agent externe sans contrôle",
     "Seuls l'admin et les équipes habilitées peuvent connecter ; chaque ajout est tracé et signalé"],
    ["Manipulation de l'IA", "Un document piégé fait dire ou faire n'importe quoi à l'agent",
     "Filtre Model Armor ; confirmation humaine avant toute action"],
    ["Données personnelles", "Un agent RH traite des données sans base légale",
     "Avis DPO, partage restreint, journalisation encadrée"],
    ["Dépendance à une personne", "Un agent critique n'a plus de propriétaire",
     "Propriétaire identifié, revue trimestrielle"],
], [36 * mm, 66 * mm, CW - 102 * mm])
S += [P("Les bénéfices", "h2")]
S += B(["<b>Autonomie</b> pour les métiers : créer un agent prend des minutes, sans ticket.",
        "<b>Réutilisation</b> : un bon agent développé une fois sert à toutes les équipes, sans copier le code.",
        "<b>Confiance</b> : la sécurité et le DPO savent ce qui est connecté, par qui, pour qui.",
        "<b>Rapidité</b> pour les équipes techniques habilitées, qui publient sans attendre."])
S += [PageBreak()]

# ================================================================== 10. Qui fait quoi + feuille de route · page 12
S += [P("ORGANISATION", "kicker"), P("Qui fait quoi", "h1")]
S += table(["Activité", "Utilisateur / RH", "PM", "Équipe technique", "Admin GE", "Sécurité", "DPO"], [
    ["Créer un agent sans code", "R", "I", "—", "—", "—", "—"],
    ["Valider un partage", "C", "I", "—", "R / A", "I", "C (si données perso.)"],
    ["Exprimer un besoin d'agent développé", "C", "R", "C", "I", "I", "C"],
    ["Développer et héberger l'agent", "—", "I", "R", "—", "C", "—"],
    ["Vérifier la checklist", "—", "I", "C", "C", "R / A", "A (si données perso.)"],
    ["Connecter l'agent à l'app", "—", "I", "R (si habilitée)", "R / A", "I", "—"],
    ["Suivre l'adoption", "C", "R", "I", "C", "—", "—"],
], [52 * mm, 22 * mm, 12 * mm, 25 * mm, 18 * mm, 18 * mm, CW - 147 * mm])
S += [P("R = réalise · A = approuve · C = consulté · I = informé", "small"), P("Feuille de route proposée", "h2")]
S += table(["Phase", "Création d'agents (niveau 1)", "Connexion d'agents développés", "Pour l'équipe RH"], [
    ["Pilote (maintenant)", "Groupe pilote, partage validé", "Admin uniquement", "FAQ politiques RH, accueil nouvel arrivant"],
    ["Généralisation", "Tous les utilisateurs, partage validé", "Admin + 2-3 équipes habilitées", "Agents planifiés (veille, synthèses)"],
    ["Cible", "Tous", "Équipes habilitées + catalogue central contrôlé", "Agents développés sur données RH, après avis DPO"],
], [30 * mm, 45 * mm, 50 * mm, CW - 125 * mm])
S += [PageBreak()]

# ================================================================== 11. FAQ · page 13
S += [P("QUESTIONS FRÉQUENTES", "kicker"), P("FAQ", "h1")]
S += table(["Question", "Réponse"], [
    ["Puis-je connecter moi-même un agent trouvé ailleurs, en collant son adresse ?",
     "Non. Il n'existe pas de bouton « connecter un agent externe » pour les utilisateurs. Faites une demande (page 9)."],
    ["Puis-je utiliser l'agent d'une autre équipe dans mon propre agent ?",
     "Oui, s'il est déjà publié dans l'app et partagé avec vous : ajoutez une étape « agent existant »."],
    ["Mon agent verra-t-il des documents que je ne vois pas ?", "Non. Il cherche avec vos droits d'accès."],
    ["Mes collègues verront-ils mes conversations avec l'agent ?", "Non. Le partage d'un agent ne partage pas les conversations."],
    ["Pourquoi mon partage est « en attente » ?", "L'administrateur valide les partages. Comptez un à deux jours ouvrés."],
    ["Un agent peut-il agir à ma place (envoyer, modifier) ?", "Seulement s'il en a l'outil, et toujours après votre confirmation."],
    ["Faut-il un accès à Google Cloud ?", "Non pour les niveaux 1 et pour utiliser les agents. Oui seulement pour les équipes techniques."],
    ["L'agent est dans le même projet que l'app : est-ce plus simple ?",
     "Oui : aucune autorisation supplémentaire. Il est ajouté et testé en moins d'une heure."],
    ["Une équipe a déjà un agent dans son catalogue (Agent Registry) : faut-il le refaire ?",
     "Non. Elle nous envoie quelques informations et l'agent est branché, souvent le jour même (page 10)."],
    ["Puis-je créer un agent sur des données de paie ?", "Pas en libre-service : c'est un agent développé, après avis du DPO."],
], [70 * mm, CW - 70 * mm])
S += [Spacer(1, 6), callout("Prochaine étape proposée : un atelier d'une heure avec l'équipe RH pour choisir deux agents pilotes "
                            "(FAQ politiques RH, accueil nouvel arrivant), les créer ensemble, et définir le groupe de partage."),
      PageBreak()]

# ================================================================== Annexe technique · page 14
S += [P("ANNEXE", "kicker"), P("Pour transmettre aux équipes techniques", "h1"),
      P("Cette page résume la mise en œuvre. Le détail est dans le dossier <font name=\"Mono\" size=\"8.5\">09-agents-multi-projets-gemini-enterprise/docs</font>.")]
S += table(["Sujet", "En bref", "Document"], [
    ["Comprendre et choisir", "6 façons d'ajouter un agent ; comment choisir ; même projet ou autre projet", "docs/01"],
    ["Tutoriel même projet", "Agent simple dans le projet de l'app : écrire, tester, déployer, ajouter, donner l'accès, plan de test. Aucun droit à ajouter", "docs/02"],
    ["Tutoriel autre projet", "Agent dans un autre projet : Agent Runtime, Cloud Run + A2A, Agent Registry + Agent Gateway", "docs/03"],
    ["Agent déjà dans un Agent Registry", "Lire l'entrée (scripts/registry.py), puis 3 voies : nom de ressource, carte A2A, ou déclaration dans notre registre + Agent Gateway", "docs/04"],
    ["Droits et régions", "Matrice unique : le projet de l'agent donne le droit au compte de Gemini Enterprise (discoveryengine.serviceAgent ou run.invoker)", "docs/05"],
    ["Agent qui appelle un agent", "Découverte dans Agent Registry, appel Agent Runtime avec un droit sur l'agent appelé seulement (aiplatform.viewer)", "docs/06"],
    ["Autonomie et délégation", "Rôles : Gemini Enterprise User (niveau 1), Agent Admin (niveau 2), Gemini Enterprise Admin (niveau 3)", "docs/07"],
    ["En code", "Terraform : deux projets, droits, publication ; une PR par agent d'une autre équipe", "README, terraform/"],
], [40 * mm, CW - 62 * mm, 22 * mm])
S += [P("Points à confirmer au premier déploiement réel", "h2")]
S += B(["Affichage des agents d'un autre projet dans l'étape « agent existant » de Workflow Builder (d'après la documentation Google : non, tant qu'ils ne sont pas publiés dans l'app).",
        "Accès à la page Agents de la console avec le seul rôle « builder ».",
        "Libellés exacts des menus de la console (ils évoluent souvent)."])
S += [P("Sources Google : Workflow Builder, partage d'agents, fonctionnalités de l'app web, ajout d'agents ADK et A2A, accès "
        "cross-project, import depuis Agent Registry (docs.cloud.google.com/gemini/enterprise, octobre 2026).", "small")]

# Assemble toutes les sections et écrit le PDF.
doc.build(S)
print("written", OUT)
