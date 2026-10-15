#!/usr/bin/env bash
# Inscrire / désinscrire un agent dans une app Gemini Enterprise.
# Appelé par Terraform (terraform_data.publish) avec ces variables d'environnement :
#   PROJECT_ID HOST PARENT DISPLAY_NAME DESCRIPTION, et soit
#   AGENT  (ressource Agent Runtime : projects/P/locations/R/reasoningEngines/ID)  soit
#   CARD   (carte d'agent A2A en JSON, v0.3, ex. un agent sur Cloud Run)
# Facultatif : AUTHORIZATION (projects/NUM/locations/LOC/authorizations/AUTH_ID) : Gemini Enterprise demande le
#   consentement de l'utilisateur et envoie son jeton OAuth à l'agent (docs/12-3, partie C).
# Usage : register_agent.sh create|delete
#
# À QUOI SERT CE SCRIPT
#   Ajoute un agent à l'app Gemini Enterprise (create) ou l'en retire (delete). Terraform n'a pas de ressource pour
#   ça : il appelle ce script (local-exec) dans terraform/30_gemini_enterprise.tf, 01-bis-cloud-run-a2a/terraform/main.tf
#   et 02-bis-agent-runtime/terraform/main.tf. C'est l'équivalent « Terraform » de add_agent_to_ge.sh.
#
# QUAND L'UTILISER, ET QUI
#   On ne le lance pas soi-même : « terraform apply » avec PUBLIER=oui (docs/12-1 B5, docs/12-2 B3, docs/12-3 §2.3
#   et C4) l'appelle pour chaque agent ; « terraform destroy » (ou un agent retiré de AGENTS) appelle delete.
#   Celui qui lance Terraform doit être admin Gemini Enterprise (roles/discoveryengine.admin) sur le projet de l'app.
#
# PRÉREQUIS
#   - Les variables ci-dessus (Terraform les donne, en MAJUSCULES, depuis le bloc « input » de terraform_data.publish).
#     PROJECT_ID = ID du projet de l'app ; HOST = eu-discoveryengine.googleapis.com (ou us-…, ou sans préfixe
#     pour global) ; PARENT = projects/<app>/locations/<loc>/collections/default_collection/engines/<APP_ID>/assistants/default_assistant.
#   - Pour Terraform lui-même : source scripts/config.sh config/<fichier>.env (variables TF_VAR_…).
#   - gcloud connecté, curl, python3.
#
# UTILISATION
#   ./scripts/register_agent.sh create     # inscrit l'agent (remplace une inscription du même nom affiché)
#   ./scripts/register_agent.sh delete     # le désinscrit (rien à faire s'il n'existe pas)
#   À la main (dépannage), exemple A2A :
#     PROJECT_ID=$PROJET_APP HOST=eu-discoveryengine.googleapis.com \
#     PARENT=projects/$PROJET_APP/locations/eu/collections/default_collection/engines/$APP_ID/assistants/default_assistant \
#     DISPLAY_NAME="Météo & équipement (A2A)" DESCRIPTION="…" CARD="$(cat carte-meteo.json)" ./scripts/register_agent.sh create
#   Agent Runtime : AGENT=projects/P/locations/R/reasoningEngines/ID à la place de CARD.
#
# CE QU'IL LIT / CE QU'IL CRÉE, MODIFIE OU SUPPRIME
#   Lit la liste des agents de l'app. create : supprime l'entrée de même nom affiché si elle existe, puis en crée
#   une nouvelle (idempotent : jamais de doublon, mais la nouvelle entrée a un nouvel ID : redonner l'accès
#   Agent User). delete : DESTRUCTIF, supprime l'entrée de l'app (l'agent déployé, lui, reste). Ne pose aucun droit
#   IAM (Terraform le fait à part). Aucun fichier local.
#
# RÉSULTAT ATTENDU
#   create : le JSON de l'agent créé renvoyé par l'API, puis « registered <DISPLAY_NAME> »
#   delete : « unregistered <DISPLAY_NAME> » (même si l'agent n'existait pas)
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « PROJECT_ID: unbound variable » (ou autre variable) -> lancé sans les variables : passer par Terraform.
#   « curl: (22) … 403 » (Terraform : erreur du provisioner local-exec) -> pas admin Gemini Enterprise
#                                     (roles/discoveryengine.admin), ou mauvais PROJECT_ID / app.
#   « usage: … create|delete »        -> action manquante ou mal écrite.
set -euo pipefail

# En-têtes de chaque appel : jeton de votre compte gcloud, et X-Goog-User-Project = le projet de l'app, à qui
# Google compte l'appel (quota) : exigé par l'API Discovery Engine avec un jeton d'utilisateur.
H=(-H "Authorization: Bearer $(gcloud auth print-access-token)"
   -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJECT_ID")
# API REST v1alpha (pas de commande gcloud ni de ressource Terraform pour les agents d'une app).
BASE="https://$HOST/v1alpha"

# Chercher une inscription existante avec le même nom affiché (rend le script idempotent).
EXISTING=$(curl -fsS "${H[@]}" "$BASE/$PARENT/agents" | python3 -c '
import json, os, sys
agents = json.load(sys.stdin).get("agents", [])
print(next((a["name"] for a in agents if a.get("displayName") == os.environ["DISPLAY_NAME"]), ""))')

case "${1:-}" in
  # create : supprimer l'ancienne entrée (s'il y en a une), puis Python construit le corps JSON à partir des
  # variables d'environnement (A2A si CARD est rempli, sinon Agent Runtime avec AGENT) et curl l'envoie (POST).
  create)
    [ -n "$EXISTING" ] && curl -fsS -X DELETE "${H[@]}" "$BASE/$EXISTING" >/dev/null   # remplacer, jamais dupliquer
    python3 -c '
import json, os, sys
e = os.environ
body = {"displayName": e["DISPLAY_NAME"], "description": e["DESCRIPTION"]}
if e.get("CARD"):
    body["a2aAgentDefinition"] = {"jsonAgentCard": e["CARD"]}
else:
    body["adkAgentDefinition"] = {"provisionedReasoningEngine": {"reasoningEngine": e["AGENT"]}}
if e.get("AUTHORIZATION"):   # A2A : une autorisation pour cet agent ; Agent Runtime : une liste, pour ses outils
    a = e["AUTHORIZATION"].split(",")   # plusieurs fournisseurs : Agent Runtime seulement (docs/12-1-8)
    if len(a) > 1 and e.get("CARD"):
        sys.exit("A2A : UNE seule autorisation par agent ; plusieurs = Agent Runtime (docs/12-1-8).")
    body["authorizationConfig"] = {"agentAuthorization": a[0]} if e.get("CARD") else {"toolAuthorizations": a}
print(json.dumps(body))' | curl -fsS -X POST "${H[@]}" "$BASE/$PARENT/agents" -d @-
    echo; echo "registered $DISPLAY_NAME";;
  # delete : supprimer l'entrée trouvée plus haut, s'il y en a une.
  delete)
    [ -n "$EXISTING" ] && curl -fsS -X DELETE "${H[@]}" "$BASE/$EXISTING" >/dev/null
    echo "unregistered $DISPLAY_NAME";;
  *) echo "usage: $0 create|delete" >&2; exit 2;;
esac
