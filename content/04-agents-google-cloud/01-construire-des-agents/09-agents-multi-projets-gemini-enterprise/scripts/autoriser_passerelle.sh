#!/usr/bin/env bash
# Mode « Agents depuis Agent Registry » : autoriser le compte de Gemini Enterprise à passer l'Agent Gateway
# vers une entrée du registre (rôle roles/iap.egressor sur l'entrée). Valeurs : source scripts/config.sh …
#
# À QUOI SERT CE SCRIPT
#   Quand l'app passe par une Agent Gateway, son compte de service (GE_SA) a besoin du « droit de passage »
#   roles/iap.egressor sur CHAQUE entrée d'Agent Registry qu'il appelle. Ce script ajoute ce droit, ou le retire.
#
# QUAND L'UTILISER, ET QUI
#   docs/12-2, A5 « Mode Agent Registry », étape 2 (après avoir créé la passerelle ge-egress, avant de la relier à
#   l'app) ; et « Revenir en arrière » avec « retirer ». Agents et app dans le MÊME projet (scénario 12-2).
#   Par qui peut modifier l'IAM des entrées du registre de ce projet (ex. propriétaire du projet).
#
# PRÉREQUIS
#   - source scripts/config.sh config/12-2-agents-dans-projet-app.env  -> lit PROJET_AGENTS, GE_SA (donc NUM_APP
#     rempli), REGION.
#   - L'entrée existe dans Agent Registry (scripts/deployer_shell.sh registre : <clé>-a2a-shell).
#   - gcloud avec la commande « agent-registry », python3.
#
# UTILISATION
#   ./scripts/autoriser_passerelle.sh meteo-a2a-shell            # ajouter le droit pour le compte de l'app
#   ./scripts/autoriser_passerelle.sh meteo-a2a-shell retirer    # le retirer (tout autre 2e mot = ajouter)
#   for K in $(echo $AGENTS_LISTE); do ./scripts/autoriser_passerelle.sh $K-a2a-shell; done   # tous les agents
#
# CE QU'IL LIT / CE QU'IL MODIFIE
#   Lit l'entrée du registre et la politique IAM de son agent (côté IAP) ; MODIFIE seulement le rôle
#   roles/iap.egressor de cette politique (les autres rôles sont gardés). Idempotent : relancer donne le même
#   résultat. Ne crée ni ne supprime aucune ressource ; aucun fichier local.
#
# RÉSULTAT ATTENDU
#   ajouter : roles/iap.egressor pour serviceAccount:service-<NUM_APP>@gcp-sa-discoveryengine.iam.gserviceaccount.com sur projects/<PROJET>/locations/europe-west1/iap_web/agentRegistry/agents/agentregistry-…
#   (« retirer : … » avec « retirer »)
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « PROJET_AGENTS: charger la configuration … » -> source scripts/config.sh … dans ce terminal.
#   « GE_SA: parameter null or not set »         -> NUM_APP vide dans le fichier de configuration.
#   Erreur gcloud (entrée introuvable) puis trace Python « HTTPError » -> mauvais ID d'entrée ou mauvaise REGION :
#                                                  vérifier avec deployer_shell.sh registre.
#   Trace Python « HTTPError: HTTP Error 403 »   -> pas le droit de modifier l'IAM de cette entrée.
#   Tout le chat bloqué après la liaison de la passerelle -> droit iap.egressor manquant : relancer ce script.
set -euo pipefail
: "${PROJET_AGENTS:?charger la configuration : source scripts/config.sh config/<fichier>.env}" "${GE_SA:?}" "${REGION:?}"
SERVICE=${1:?id du service dans le registre, ex. meteo-a2a-shell}
# L'entrée « service » du registre pointe vers un « agent » (registryResource) : c'est sur cet agent, vu comme une
# ressource IAP, que se pose le droit de passage. On garde son ID (dernier morceau du chemin).
AGENT=$(basename "$(gcloud agent-registry services describe "$SERVICE" --location="$REGION" --project="$PROJET_AGENTS" --format='value(registryResource)')")
RES="projects/$PROJET_AGENTS/locations/$REGION/iap_web/agentRegistry/agents/$AGENT"
# Appel direct de l'API IAP (v1) en Python : lire la politique IAM (getIamPolicy), la modifier, la renvoyer
# (setIamPolicy). setIamPolicy REMPLACE toute la politique : on repart donc de celle lue (avec son etag, qui fait
# refuser l'écriture si quelqu'un l'a changée entre-temps) et on ne touche qu'au rôle roles/iap.egressor.
RES=$RES TOK=$(gcloud auth print-access-token) MEMBRE="serviceAccount:$GE_SA" ACTION=${2:-ajouter} python3 - <<'PY'
import json, os, urllib.request
res = os.environ["RES"]
def call(verb, body):
    r = urllib.request.Request(f"https://iap.googleapis.com/v1/{res}:{verb}", json.dumps(body).encode(),
                               {"Authorization": "Bearer " + os.environ["TOK"], "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r))
pol = call("getIamPolicy", {})
# Garder tous les autres rôles tels quels ; rassembler les membres actuels de roles/iap.egressor.
liens = [b for b in pol.get("bindings", []) if b["role"] != "roles/iap.egressor"]
membres = {m for b in pol.get("bindings", []) if b["role"] == "roles/iap.egressor" for m in b["members"]}
# Ensemble (set) : ajouter un membre déjà présent ou retirer un absent ne change rien (idempotent).
membres = membres - {os.environ["MEMBRE"]} if os.environ["ACTION"] == "retirer" else membres | {os.environ["MEMBRE"]}
# Plus aucun membre : on n'écrit pas de rôle vide.
if membres:
    liens.append({"role": "roles/iap.egressor", "members": sorted(membres)})
pol["bindings"] = liens
call("setIamPolicy", {"policy": pol})
print(f"{os.environ['ACTION']} : roles/iap.egressor pour {os.environ['MEMBRE']} sur {res}")
PY
