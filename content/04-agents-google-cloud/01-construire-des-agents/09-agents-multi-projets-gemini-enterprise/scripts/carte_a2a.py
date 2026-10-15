"""Carte A2A v0.3 d'un agent du trio, et fichier d'environnement de son service Cloud Run (méthode « shell »).

À quoi sert ce script
  Fabrique la « carte » A2A d'un agent : un JSON qui donne son nom, sa description, son adresse
  et ses compétences.
  C'est ce qu'on colle dans Gemini Enterprise (agent via A2A) et ce qu'on déclare dans Agent Registry.
  Avec --env-yaml, il écrit plutôt les variables d'environnement du service Cloud Run (dont cette carte).
  Même contenu que Terraform (01-bis) : noms, descriptions et compétences lus dans agents/trio/catalogue.json.

Quand l'utiliser
  - docs/12-1-1, partie 7.2 c) (--env-yaml, avant `gcloud run deploy`) et 7.4 (plusieurs agents) ;
  - docs/12-1-1, partie 7.6 (la carte pour Gemini Enterprise) et partie 9 (déclaration dans Agent Registry) ;
  - docs/12-3, parties 3.3 et 3.6 (un nouvel agent), partie C4 (agent avec OAuth, AUTH_ID).

Prérequis
  - Lancer depuis n'importe où : le catalogue est trouvé à partir de l'emplacement du script.
  - Python 3.9 ou plus (python3 du système suffit : bibliothèque standard seulement).
  - Pour --env-yaml seulement : configuration chargée dans ce terminal,
      source scripts/config.sh config/12-1-agents-dans-projet-exp.env
    qui définit PROJET_AGENTS, PROMPT_TEMPLATE, RESPONSE_TEMPLATE (et TF_VAR_ge_engine, utile avec AUTH_ID).
  - Aucun droit Google Cloud : le script n'appelle aucune API.

Utilisation
  python3 scripts/carte_a2a.py CLE URL [--env-yaml]
    CLE         clé de l'agent dans agents/trio/catalogue.json (meteo, taille, traduction…)
    URL         adresse du service Cloud Run (la « Service URL ») ; le « / » final est retiré
    --env-yaml  écrire les variables du service Cloud Run au lieu de la carte

  Exemples :
    python3 scripts/carte_a2a.py meteo https://meteo-a2a-shell-NUM.europe-west1.run.app > carte-meteo.json
    python3 scripts/carte_a2a.py meteo https://meteo-a2a-shell-NUM.europe-west1.run.app --env-yaml \\
      > env-meteo.yaml
    K=meteo; URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app
    python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml
    AUTH_ID=acces-drive python3 scripts/carte_a2a.py $K $URL --env-yaml > env-$K.yaml    # agent avec OAuth

  Variables d'environnement lues (avec --env-yaml) :
    PROJET_AGENTS                       -> GOOGLE_CLOUD_PROJECT (projet où l'agent appelle Gemini)
    PROMPT_TEMPLATE, RESPONSE_TEMPLATE  -> filtres Model Armor (docs/12-1-1, partie 6)
    MODEL                               facultatif, défaut gemini-3.5-flash
    AUTH_ID                             facultatif : ID de l'autorisation OAuth de l'app (docs/12-3, C) ;
                                        ajoute alors AUTH_ID et GE_ENGINE (lu dans TF_VAR_ge_engine)

Ce qu'il lit / ce qu'il crée
  Lit agents/trio/catalogue.json. Écrit seulement sur la sortie standard (rediriger avec > fichier).
  Ne crée, ne modifie et ne supprime rien dans Google Cloud. Sans danger, relançable à volonté.

Résultat attendu
  Sans option : la carte sur UNE ligne, par exemple
    {"protocolVersion": "0.3", "name": "meteo_agent", "description": "Météo réelle…", "url": "https://…", …}
  (python3 -m json.tool --no-ensure-ascii carte-meteo.json pour la lire.)
  Avec --env-yaml : une ligne par variable, AGENT, AGENT_CARD, GOOGLE_CLOUD_PROJECT, MODEL, PROMPT_TEMPLATE,
  RESPONSE_TEMPLATE (+ AUTH_ID, GE_ENGINE), par exemple
    AGENT: "meteo_agent"

Erreurs fréquentes et que faire
  - IndexError (list index out of range) : CLE ou URL manquant -> donner les deux arguments.
  - KeyError: 'metoe' : clé absente du catalogue -> vérifier l'orthographe (agents/trio/catalogue.json).
  - KeyError: 'PROJET_AGENTS' (ou 'PROMPT_TEMPLATE'…) avec --env-yaml : configuration pas chargée dans ce
    terminal -> source scripts/config.sh config/<fichier>.env.
  - KeyError: 'TF_VAR_ge_engine' avec AUTH_ID : idem ; et remplir PROJET_APP, NUM_APP, APP_ID dans le fichier.
  - Gemini Enterprise refuse la carte, ou l'agent ne répond pas : URL différente de la « Service URL » de
    `gcloud run deploy` (souvent NUM_AGENTS faux) -> corriger, recharger, régénérer la carte.
"""
import json
import os
import sys
from pathlib import Path

cle, url = sys.argv[1], sys.argv[2].rstrip("/")
a = json.loads((Path(__file__).resolve().parent.parent / "agents" / "trio" / "catalogue.json").read_text())[cle]
# Format de carte attendu par Gemini Enterprise : A2A 0.3, transport JSON-RPC, texte en entrée et en sortie.
carte = {"protocolVersion": "0.3", "name": a["dossier"], "description": a["description"], "url": url,
         "preferredTransport": "JSONRPC", "version": "1.0.0", "capabilities": {"streaming": True},
         "defaultInputModes": ["text/plain"], "defaultOutputModes": ["text/plain"], "skills": a["competences"]}
if "--env-yaml" in sys.argv:
    # Variables lues par 01-bis-cloud-run-a2a/main.py au démarrage (AGENT_CARD : la carte qu'il sert).
    env = {"AGENT": a["dossier"], "AGENT_CARD": json.dumps(carte, ensure_ascii=False),
           "GOOGLE_CLOUD_PROJECT": os.environ["PROJET_AGENTS"], "MODEL": os.getenv("MODEL", "gemini-3.5-flash"),
           "PROMPT_TEMPLATE": os.environ["PROMPT_TEMPLATE"], "RESPONSE_TEMPLATE": os.environ["RESPONSE_TEMPLATE"]}
    if os.getenv("AUTH_ID"):
        # Agent qui agit avec le compte de l'utilisateur : l'ID d'autorisation et l'app qui fournit le jeton.
        env |= {"AUTH_ID": os.environ["AUTH_ID"], "GE_ENGINE": os.environ["TF_VAR_ge_engine"]}
    # Chaque valeur est écrite en JSON (guillemets, échappements) : `gcloud run deploy --env-vars-file` la lit
    # comme du YAML, et JSON est un YAML valide. Évite tout souci avec les « : » et accents de la carte.
    print("\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in env.items()))   # JSON est un YAML valide
else:
    print(json.dumps(carte, ensure_ascii=False))
