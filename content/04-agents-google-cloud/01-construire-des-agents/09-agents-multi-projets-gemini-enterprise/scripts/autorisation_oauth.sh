#!/usr/bin/env bash
# L'autorisation OAuth d'un agent dans l'app Gemini Enterprise (docs/12-3, partie C). Après « source scripts/config.sh … » :
#
# À QUOI SERT CE SCRIPT
#   Crée, liste ou supprime une « autorisation » dans l'app Gemini Enterprise : la fiche (client OAuth + portées)
#   qui permet à l'app de demander le consentement de l'utilisateur, puis d'envoyer SON jeton OAuth à l'agent.
#   Un agent s'en sert ensuite via AUTH_ID (add_agent_to_ge.sh) ou AGENTS_OAUTH (config, Terraform).
#
# QUAND L'UTILISER, ET QUI
#   docs/12-3, partie C, étape C2 (et C7 pour l'agent Identité), APRÈS avoir créé le client OAuth (C1) et AVANT
#   d'ajouter l'agent à l'app (C4). Par l'admin Gemini Enterprise (roles/discoveryengine.admin sur le projet de l'app).
#
# PRÉREQUIS
#   - source scripts/config.sh config/<fichier>.env  -> lit PROJET_APP, NUM_APP, GE_LOCATION (l'app doit exister).
#   - gcloud connecté, curl, python3 ; API discoveryengine.googleapis.com active sur le projet de l'app.
#   - Pour create : le JSON du client OAuth (type « Application Web »), avec les deux URI de redirection de
#     Gemini Enterprise : https://vertexaisearch.cloud.google.com/oauth-redirect
#                          https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
#
# UTILISATION
#   ./scripts/autorisation_oauth.sh create acces-drive client_secret.json "https://www.googleapis.com/auth/cloud-platform"
#   ./scripts/autorisation_oauth.sh create acces-identite client_secret.json "openid email https://www.googleapis.com/auth/cloud-platform"
#   ./scripts/autorisation_oauth.sh create acces-gmail client_secret.json "https://www.googleapis.com/auth/gmail.readonly" "Gmail (lecture seule)"
#   ./scripts/autorisation_oauth.sh renommer acces-gmail "Gmail (lecture seule)"   # nom affiché seulement (docs/12-1-8)
#   ./scripts/autorisation_oauth.sh list
#   ./scripts/autorisation_oauth.sh delete acces-drive
#   create <ID> <fichier client_secret.json> "<portées>" : l'ID est définitif ; c'est la valeur à mettre dans AUTH_ID
#   ou AGENTS_OAUTH (docs/12-3 C4).
#
# client_secret.json : le fichier téléchargé à la création du client OAuth (type « Application Web »), avec les deux
# URI de redirection de Gemini Enterprise. Le secret part directement chez Google : il n'est écrit nulle part ailleurs
# (ni dans Terraform, ni dans le dépôt). Plusieurs portées : séparées par des espaces, dans les mêmes guillemets.
#
# CE QU'IL LIT / CE QU'IL CRÉE, MODIFIE OU SUPPRIME
#   create : lit client_secret.json (rien n'est écrit sur le disque) ; crée l'autorisation
#            projects/NUM_APP/locations/GE_LOCATION/authorizations/<ID> dans l'app. Pas idempotent : un ID déjà
#            pris est refusé par Google (supprimer d'abord, ou choisir un autre ID).
#   list   : lecture seule.
#   delete : DESTRUCTIF ; les agents qui l'utilisent n'auront plus de bouton « Autoriser » qui marche.
#
# RÉSULTAT ATTENDU
#   create : « autorisation créée : projects/<NUM_APP>/locations/eu/authorizations/acces-drive »
#   list   : un nom complet par ligne (projects/…/authorizations/<ID>)
#   delete : « supprimée : acces-drive »
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « PROJET_APP: source scripts/config.sh d abord » -> charger la configuration (PROJET_APP, NUM_APP remplis).
#   « ÉCHEC : TenantProject with location eu … does not exist » -> pas d'app dans ce projet / cette localisation :
#                                                     vérifier PROJET_APP, NUM_APP, GE_LOCATION.
#   « ÉCHEC : … » (autre message de Google)         -> lire le message : ID déjà pris, droits (discoveryengine.admin)…
#   Agent sans bouton « Autoriser » dans le chat     -> l'ID donné à AUTH_ID / AGENTS_OAUTH doit être IDENTIQUE à
#                                                     celui de « list ».
set -euo pipefail
: "${PROJET_APP:?source scripts/config.sh d abord}" "${NUM_APP:?}" "${GE_LOCATION:?}"

# Pas de commande gcloud ni de ressource Terraform pour les autorisations : API REST v1alpha de Discovery Engine.
# Le chemin utilise le NUMÉRO du projet ; X-Goog-User-Project = projet à qui Google compte l'appel (quota),
# exigé avec un jeton d'utilisateur.
HOST=$([ "$GE_LOCATION" = global ] && echo discoveryengine.googleapis.com || echo "$GE_LOCATION-discoveryengine.googleapis.com")
BASE="https://$HOST/v1alpha/projects/$NUM_APP/locations/$GE_LOCATION/authorizations"
H=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJET_APP")

case "${1:-}" in
  # create : Python (heredoc) lit le client OAuth et écrit le corps JSON sur sa sortie, envoyé directement à curl
  # par le « | » (le secret ne passe par aucun fichier). curl sans -f : on veut lire le message d'erreur de Google ;
  # le dernier Python l'affiche (« ÉCHEC : … ») et arrête le script (pipefail), sinon on affiche le succès.
  create)
    ID=${2:?ID de l autorisation, ex. acces-drive}; CLIENT=${3:?fichier client_secret.json}; SCOPES=${4:?portées OAuth}
    NOM=${5:-$ID}   # nom affiché (displayName, exigé par l'API) : facultatif, l'ID par défaut
    python3 - "$BASE/$ID" "$CLIENT" "$SCOPES" "$NOM" <<'PY' | curl -sS -X POST "${H[@]}" "$BASE?authorizationId=$ID" -d @- | python3 -c 'import json,sys; r=json.load(sys.stdin); sys.exit("ÉCHEC : " + r["error"]["message"]) if "error" in r else None'
import json, sys, urllib.parse
# nom = la partie après « /v1alpha/ » : projects/NUM/locations/LOC/authorizations/ID
nom, client, scopes, affiche = sys.argv[1].split("/v1alpha/")[1], sys.argv[2], sys.argv[3], sys.argv[4]
c = json.load(open(client))
# Le JSON téléchargé range ses valeurs sous « web » (Application Web) ou « installed » ; sinon on le prend tel quel.
c = c.get("web") or c.get("installed") or c
# Paramètres exigés par Gemini Enterprise : code d'autorisation, jeton de rafraîchissement (offline), consentement affiché.
# (sans access_type=offline, Google refuse : « The authorization URI must contain 'access_type=offline' … »)
auth_uri = c["auth_uri"] + "?" + urllib.parse.urlencode({
    "client_id": c["client_id"], "redirect_uri": "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html",
    "scope": scopes, "include_granted_scopes": "true", "response_type": "code", "access_type": "offline", "prompt": "consent"})
print(json.dumps({"name": nom, "displayName": affiche, "serverSideOauth2": {"clientId": c["client_id"], "clientSecret": c["client_secret"],
                                                     "authorizationUri": auth_uri, "tokenUri": c["token_uri"]}}))
PY
    echo "autorisation créée : projects/$NUM_APP/locations/$GE_LOCATION/authorizations/$ID";;
  # renommer : PATCH du seul nom affiché (updateMask=displayName) ; le client, le secret et les portées ne bougent pas.
  renommer)
    curl -fsS -X PATCH "${H[@]}" "$BASE/${2:?ID}?updateMask=displayName" \
      -d "$(python3 -c 'import json,sys; print(json.dumps({"displayName": sys.argv[1]}))' "${3:?nom affiché}")" >/dev/null \
      && echo "renommée : $2 → « $3 »";;
  list)
    curl -fsS "${H[@]}" "$BASE" | python3 -c 'import json,sys; [print(a["name"], "|", a.get("displayName", "")) for a in json.load(sys.stdin).get("authorizations", [])]';;
  delete)
    curl -fsS -X DELETE "${H[@]}" "$BASE/${2:?ID}" >/dev/null && echo "supprimée : $2";;
  # Sans action reconnue : affiche l'en-tête, de « À QUOI SERT » jusqu'à la fin de « UTILISATION ».
  *) sed -n '2,32p' "$0"; exit 2;;
esac
