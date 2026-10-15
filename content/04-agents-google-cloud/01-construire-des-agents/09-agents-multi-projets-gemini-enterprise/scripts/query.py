"""Interroger un agent Agent Runtime, comme le ferait un autre agent ou une application.

À quoi sert ce script
  Envoie une question à un agent déployé sur Agent Runtime et affiche sa réponse, ainsi que les outils
  (fonctions Python) qu'il a appelés. Sert à tester un agent après déploiement, et à prouver les droits.

Quand l'utiliser
  - docs/12-1-1, partie 8.2 (tester l'agent, 3 à 5 minutes après le déploiement) ;
  - docs/12-3, partie 3.7 (tester un nouvel agent Agent Runtime) ;
  - docs/06, partie 2.4 et docs/10 (agents stock et orchestrateur, déployés par terraform/).

Prérequis
  - Dans le dossier du projet, venv activé (source .venv/bin/activate) : il faut le paquet agentplatform.
  - Identifiants Python : gcloud auth application-default login (une fois).
  - Droit d'interroger l'agent : roles/aiplatform.user sur le projet, ou roles/aiplatform.viewer sur l'agent.
  - Mode « nom Terraform » seulement : terraform installé, et `terraform apply` déjà fait dans terraform/.
  - Aucune variable de configuration lue, sauf AGENT_NAME (ci-dessous).

Utilisation
  python scripts/query.py NOM_TERRAFORM "question"            ressource lue par `terraform output`
  AGENT_NAME=RESSOURCE python scripts/query.py - "question"   nom de ressource donné directement

    python scripts/query.py stock_agent "Stock de 8771234 à Lyon ?"
    python scripts/query.py orchestrator "Il reste des tentes 8771234 à Lyon ?"
    AGENT_NAME=projects/P/locations/R/reasoningEngines/ID python scripts/query.py - "question"
    AGENT_NAME=projects/$NUM_AGENTS/locations/$REGION/reasoningEngines/<ID> \\
      python scripts/query.py - "Je cours à Lille demain matin, quoi porter ?"

  NOM_TERRAFORM  une sortie de terraform/outputs.tf (stock_agent, orchestrator) ; ignoré si AGENT_NAME
                 est défini
                 (on met alors « - »). Le mode Terraform se lance depuis le dossier du projet.
  question       tous les mots suivants (les guillemets restent conseillés)
  AGENT_NAME     projects/<projet>/locations/<région>/reasoningEngines/<ID> : la ligne « déployé : » de
                 deployer_agent_runtime.py, ou la sortie `agents` de Terraform (02-bis)

Ce qu'il lit / ce qu'il crée
  Lit l'agent (Agent Runtime). Crée une SESSION de conversation dans l'agent (utilisateur test@acme.example),
  visible dans la console (Agent Runtime -> Sessions), et consomme des appels au modèle. Ne modifie ni ne
  supprime aucun agent. Aucun fichier local écrit.

Résultat attendu
    -> outil : pointure({'longueur_pied_cm': 27, 'activite': 'course'})
  agent : Pour la course à pied avec un pied de 27 cm, je vous conseille une pointure **42 EUR** …
  (« -> outil : » = un outil appelé par l'agent, avec ses arguments ; « agent : » = son texte.)

Prouve aussi les droits : avec un compte sans roles/aiplatform.viewer sur l'agent -> 403.

Erreurs fréquentes et que faire
  - 403 / PermissionDenied : votre compte n'a pas le droit d'interroger cet agent (voir Prérequis).
  - 404 / NotFound ou pas de réponse : mauvais AGENT_NAME, ou agent pas encore prêt -> attendre 3 à 5 minutes.
  - « Output "…" not found » (terraform) : nom de sortie inconnu, ou lancé hors du dossier du projet ;
    pour un agent déployé autrement, utiliser AGENT_NAME=… et « - ».
  - ValueError: not enough values to unpack : AGENT_NAME n'a pas la forme projects/…/locations/…/….
  - DefaultCredentialsError : gcloud auth application-default login.
  - IndexError : aucun argument -> donner au moins NOM_TERRAFORM (ou « - »).
  - « filtrée par Model Armor » juste après le déploiement : droits de l'agent pas encore actifs, attendre.
"""
import asyncio
import os
import subprocess
import sys

import agentplatform

which, question = sys.argv[1], " ".join(sys.argv[2:])
name = os.getenv("AGENT_NAME") or subprocess.check_output(
    ["terraform", "-chdir=terraform", "output", "-raw", which], text=True).strip()
# projects/<projet>/locations/<région>/reasoningEngines/<ID> : on en tire le projet et la région du client.
_, project, _, location, *_ = name.split("/")


async def main():
    """Ouvre une session, envoie la question, affiche les appels d'outils et le texte au fil de l'eau."""
    # Garder une référence au client : sinon il est détruit et ferme sa connexion avant l'appel asynchrone.
    client = agentplatform.Client(project=project, location=location)
    remote = client.runtimes.get(name=name)
    # Une session = une conversation ; l'agent garde l'historique par (user_id, session_id).
    session = await remote.async_create_session(user_id="test@acme.example")
    async for event in remote.async_stream_query(user_id="test@acme.example", session_id=session["id"], message=question):
        # Chaque événement contient des « parts » : soit un appel d'outil (function_call), soit du texte.
        for part in (event.get("content") or {}).get("parts", []):
            if "function_call" in part:
                print(f"  -> outil : {part['function_call']['name']}({part['function_call'].get('args')})")
            if part.get("text"):
                print(f"agent : {part['text']}")


asyncio.run(main())
