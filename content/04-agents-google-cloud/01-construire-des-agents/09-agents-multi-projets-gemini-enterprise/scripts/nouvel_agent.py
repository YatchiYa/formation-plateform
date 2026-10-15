"""Créer le squelette d'un nouvel agent dans agents/trio : dossier, agent.py, entrée du catalogue.

À quoi sert ce script
  Prépare un nouvel agent prêt à compléter : un dossier agents/trio/<clé>_agent/ (avec un outil d'exemple)
  et une entrée <clé> dans agents/trio/catalogue.json. Ensuite, tous les modes de déploiement le connaissent
  (Terraform, shell, console) : c'est le catalogue qui décide.

Quand l'utiliser
  docs/12-3, partie 1.2 (le squelette), avant 1.3 (écrire les vrais outils) et 1.4 (tester).
  Aussi cité par docs/12-1-1, partie 12 et docs/12-1-2, partie 9 (« créer un tout nouvel agent »).

Prérequis
  - Lancer depuis le dossier du projet, venv activé (source .venv/bin/activate). Aucune configuration ni
    connexion Google : le script ne touche qu'à des fichiers locaux.

Utilisation
  python scripts/nouvel_agent.py CLE "NOM AFFICHÉ" "DESCRIPTION"

    python scripts/nouvel_agent.py taille "Conseil taille" \\
        "Conseille la bonne taille de vêtement à partir des mesures."
    python scripts/nouvel_agent.py velo "Atelier vélo" \\
        "Diagnostique une panne de vélo simple et dit si l'atelier est nécessaire."

  CLE          minuscules et chiffres, commence par une lettre, 2 à 15 caractères
               (elle forme les noms Google : service « <clé>-a2a », compte « <clé>-a2a-shell-sa »,
               30 caractères max)
  NOM AFFICHÉ  unique dans le catalogue : c'est par ce nom que Gemini Enterprise reconnaît l'agent
  DESCRIPTION  une phrase claire, montrée aux utilisateurs
  Exactement 3 arguments (mettre le nom et la description entre guillemets) ; sinon ce texte s'affiche.

Ce qu'il crée / modifie
  Crée agents/trio/<clé>_agent/__init__.py et agents/trio/<clé>_agent/agent.py (outil exemple_outil).
  Modifie agents/trio/catalogue.json (ajoute l'entrée <clé> à la fin, réécrit le fichier indenté).
  Rien dans Google Cloud. Refuse plutôt que d'écraser : clé, nom affiché ou dossier déjà pris => rien
  n'est créé.
  Pour annuler : supprimer le dossier et retirer l'entrée du catalogue.

Résultat attendu
  créé : agents/trio/velo_agent/agent.py et l'entrée « velo » du catalogue
  à faire : écrire les outils dans velo_agent/agent.py, mettre de vrais exemples dans le catalogue, tester.

Ensuite : écrire les vrais outils dans agents/trio/<clé>_agent/agent.py, tester en local (adk web),
puis déployer
(Terraform 01-bis : un nouveau service Cloud Run ; 02-bis : un nouvel agent Agent Runtime). Voir docs/12-3.

Erreurs fréquentes et que faire
  - Ce texte s'affiche : pas exactement 3 arguments -> guillemets autour du nom et de la description.
  - « Clé invalide : … » : majuscule, tiret, accent ou longueur -> autre clé (ex. velo, taille2).
  - « La clé « … » existe déjà dans le catalogue. » / « Le dossier … existe déjà. » : choisir une autre clé.
  - « Le nom « … » est déjà pris par un autre agent … » : choisir un nom affiché unique.
  - JSONDecodeError : catalogue.json cassé (virgule) -> python3 -m json.tool agents/trio/catalogue.json
"""
import json
import re
import sys
from pathlib import Path

TRIO = Path(__file__).resolve().parent.parent / "agents" / "trio"

# Modèle du fichier agent.py. Les {{ }} donnent des accolades littérales après .format().
# Les 3 dernières lignes (root_agent, app, agent_runtime_app) sont les points d'entrée attendus par Cloud Run
# (01-bis, `app`) et Agent Runtime (`agent_runtime_app`) : ne pas les changer.
MODELE = '''"""Agent {NOM} : {DESCRIPTION}"""
from agentplatform.frameworks.adk import AdkApp
from google.adk.agents import Agent

import commun


def exemple_outil(question: str) -> dict:
    """À remplacer : ce que fait l'outil, en une phrase (le modèle lit ce texte).

    Args:
        question: La demande de l'utilisateur.
    """
    return {{"status": "success", "reponse": "à remplacer par le vrai traitement"}}


root_agent = Agent(
    name="{DOSSIER}",
    model=commun.modele(),
    description="{DESCRIPTION}",
    instruction="Appelle toujours exemple_outil avant de répondre. Réponds en français, en 5 lignes maximum.",
    tools=[exemple_outil],
)

app = commun.app_securisee(root_agent)
agent_runtime_app = AdkApp(app=app)
'''


def main():
    """Vérifie les 3 arguments, puis crée le dossier de l'agent et son entrée dans le catalogue."""
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    cle, nom, description = sys.argv[1], sys.argv[2], sys.argv[3]
    # La clé devient : service Cloud Run « <clé>-a2a », comptes « <clé>-a2a-shell-sa » (30 caractères max chez Google).
    if not re.fullmatch(r"[a-z][a-z0-9]{1,14}", cle):
        sys.exit("Clé invalide : minuscules et chiffres, commence par une lettre, 2 à 15 caractères (ex. taille).")
    catalogue_path = TRIO / "catalogue.json"
    catalogue = json.loads(catalogue_path.read_text())
    # Toutes les vérifications AVANT de créer quoi que ce soit : un refus ne laisse aucun reste.
    if cle in catalogue:
        sys.exit(f"La clé « {cle} » existe déjà dans le catalogue.")
    if any(a["nom_affiche"] == nom for a in catalogue.values()):   # même nom = même agent pour Gemini Enterprise
        sys.exit(f"Le nom « {nom} » est déjà pris par un autre agent : choisir un nom affiché unique.")
    dossier = TRIO / f"{cle}_agent"
    if dossier.exists():
        sys.exit(f"Le dossier {dossier} existe déjà.")
    dossier.mkdir()
    (dossier / "__init__.py").write_text("from . import agent\n")
    # Guillemets doubles remplacés par des simples : la description est insérée entre "…" dans le code Python.
    (dossier / "agent.py").write_text(MODELE.format(NOM=nom, DESCRIPTION=description.replace('"', "'"), DOSSIER=f"{cle}_agent"))
    # Une compétence par défaut, montrée dans la carte A2A : remplacer l'exemple par de vraies questions.
    catalogue[cle] = {"dossier": f"{cle}_agent", "nom_affiche": nom, "description": description,
                      "competences": [{"id": cle, "name": nom, "description": description, "tags": [cle],
                                       "examples": ["Que sais-tu faire ?"]}]}
    catalogue_path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n")
    print(f"créé : {dossier.relative_to(TRIO.parent.parent)}/agent.py et l'entrée « {cle} » du catalogue")
    print(f"à faire : écrire les outils dans {dossier.name}/agent.py, mettre de vrais exemples dans le catalogue, tester.")


if __name__ == "__main__":
    main()
