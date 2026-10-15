# Charger la configuration du projet 10 dans le terminal :   source scripts/config.sh config/10-mcp.env
#
# Lit le fichier, vérifie les champs obligatoires, puis calcule et exporte tout ce dont les scripts et Terraform ont
# besoin (noms des services et comptes, adresses, variables TF_VAR_*). Ne crée rien dans Google Cloud.
# Les valeurs de l'app peuvent être données devant la commande sans toucher au fichier :
#   PROJET_APP=… NUM_APP=… APP_ID=… source scripts/config.sh config/10-mcp.env
[ -f "${1:-}" ] || { echo "Usage : source scripts/config.sh config/10-mcp.env"; return 1 2>/dev/null || exit 1; }
_garde() { local v; for v in PROJET_APP NUM_APP APP_ID OAUTH_CLIENT_IDS; do eval "_${v}=\${$v:-}"; done; }
_garde
set -a
# shellcheck disable=SC1090
. "$1"
set +a
for _v in PROJET_APP NUM_APP APP_ID OAUTH_CLIENT_IDS; do   # une valeur donnée devant la commande l'emporte sur le fichier
  eval "[ -n \"\$_${_v}\" ] && export ${_v}=\"\$_${_v}\""
done
_ok=1
for _v in PROJET NUM_PROJET REGION ALLOWED_DOMAINS AUTH_ID; do
  eval "[ -n \"\${$_v:-}\" ]" || { echo "MANQUANT : $_v dans $1"; _ok=0; }
done
case "$NUM_PROJET" in *[!0-9]*|"") echo "ATTENTION : NUM_PROJET doit être le NUMÉRO du projet (chiffres)"; _ok=0;; esac

export CONFIG_FICHIER=$1
export MCP_SERVICE=sheets-mcp AGENT_SERVICE=sheets-agent RUNTIME_NOM=sheets-agent
export MCP_SA=sheets-mcp-sa@$PROJET.iam.gserviceaccount.com          # identité du serveur MCP : AUCUN rôle
export AGENT_SA=sheets-agent-sa@$PROJET.iam.gserviceaccount.com      # identité de l'agent (Cloud Run et Agent Runtime)
export BUILD_SA=sheets-build-sa@$PROJET.iam.gserviceaccount.com      # construit les images (Cloud Build)
export MCP_BASE=https://$MCP_SERVICE-$NUM_PROJET.$REGION.run.app
export MCP_URL=$MCP_BASE/mcp
export SLIDES_SERVICE=slides-mcp                                       # même image, PRODUIT=slides
export SLIDES_BASE=https://$SLIDES_SERVICE-$NUM_PROJET.$REGION.run.app
export SLIDES_URL=$SLIDES_BASE/mcp
export AGENT_URL=https://$AGENT_SERVICE-$NUM_PROJET.$REGION.run.app
export GE_SA=${NUM_APP:+service-$NUM_APP@gcp-sa-discoveryengine.iam.gserviceaccount.com}
export GE_HOST=$([ "$GE_LOCATION" = global ] && echo discoveryengine.googleapis.com || echo "$GE_LOCATION-discoveryengine.googleapis.com")
# Terraform (terraform/) lit les mêmes valeurs.
export TF_VAR_project_id=$PROJET TF_VAR_project_number=$NUM_PROJET TF_VAR_region=$REGION TF_VAR_auth_id=$AUTH_ID TF_VAR_model=$MODEL
export TF_VAR_registry_location=$REGISTRE_LOCATION TF_VAR_ge_project_number=${NUM_APP:-}
export TF_VAR_oauth_client_ids="[$(printf '%s' "$OAUTH_CLIENT_IDS" | tr ',' '\n' | sed '/^ *$/d; s/ //g; s/.*/"&"/' | paste -sd, -)]"
export TF_VAR_allowed_domains="[$(printf '%s' "$ALLOWED_DOMAINS" | tr ',' '\n' | sed '/^ *$/d; s/ //g; s/.*/"&"/' | paste -sd, -)]"

cat <<EOF
== Configuration chargée : $1
   Projet (MCP + agent)  : $PROJET (n° $NUM_PROJET), région $REGION
   Serveur MCP Sheets    : $MCP_URL
   Serveur MCP Slides    : $SLIDES_URL
   Agent A2A             : $AGENT_URL
   App Gemini Enterprise : ${PROJET_APP:-(pas encore)} ${APP_ID:+/ $APP_ID} ${GE_SA:+(compte $GE_SA)}
   Clients OAuth acceptés: ${OAUTH_CLIENT_IDS:-(AUCUN : le serveur MCP refusera de démarrer ; docs/10-5, étape 1)}
   Domaines acceptés     : $ALLOWED_DOMAINS
EOF
[ "$_ok" = 1 ] || echo "!! Corrigez le fichier, puis rechargez-le."
unset _ok _v _garde
