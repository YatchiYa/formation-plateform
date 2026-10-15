# Charger un fichier de configuration (config/*.env) dans le terminal. À lancer avec « source », pas « bash ».
#
# À QUOI SERT CE SCRIPT
#   Lit vos valeurs (projets, région, agents…) dans config/<fichier>.env, calcule celles qui en dépendent,
#   et les met dans le terminal pour gcloud, les autres scripts et Terraform (variables TF_VAR_…, donc
#   pas de terraform.tfvars à écrire). Puis il vérifie tout et affiche un résumé qui finit par « OK ».
#
# QUAND L'UTILISER, ET QUI
#   Toujours en premier, dans chaque nouveau terminal ET après chaque modification du fichier .env.
#   docs/12-1-1 partie 3, docs/12-1 et docs/12-2 §1.3, docs/12-3 §1.1. Tout le monde (équipe et admin).
#
# PRÉREQUIS
#   - Être dans le dossier du projet (cd …/09-agents-multi-projets-gemini-enterprise).
#   - Un fichier config/<fichier>.env rempli. Variables lues : PROJET_APP NUM_APP APP_ID GE_LOCATION
#     PROJET_AGENTS NUM_AGENTS REGION AGENTS PUBLIER AGENTS_OAUTH GROUPE_UTILISATEURS DOSSIER
#     (facultatives : PROMPT_TEMPLATE RESPONSE_TEMPLATE AGENT_GATEWAY).
#   - python3 (lecture de agents/trio/catalogue.json). Aucun appel à Google, aucun droit nécessaire.
#   - Marche avec bash et zsh (Mac).
#
# UTILISATION
#   source scripts/config.sh config/12-1-agents-dans-projet-exp.env   # agents dans un projet à part (12-1)
#   source scripts/config.sh config/12-2-agents-dans-projet-app.env   # agents dans le projet de l'app (12-2)
#   source scripts/config.sh                                          # sans fichier : affiche l'usage
#   Jamais « bash scripts/config.sh … » ni derrière un « | » : les variables disparaîtraient avec le script.
#
# CE QU'IL LIT / CE QU'IL MODIFIE
#   Lit le fichier .env et agents/trio/catalogue.json. Ne crée, ne modifie, ne supprime RIEN dans Google
#   Cloud ni sur le disque : il change seulement les variables de CE terminal. Sans danger à relancer.
#   Variables créées : toutes celles du fichier, plus CONFIG_FICHIER SCENARIO GE_SA MEME_PROJET AGENTS_LISTE
#   PROMPT_TEMPLATE RESPONSE_TEMPLATE CLOUDSDK_CORE_PROJECT (projet gcloud par défaut = PROJET_AGENTS,
#   dans ce terminal seulement) CLOUDSDK_API_ENDPOINT_OVERRIDES_MODELARMOR TF_VAR_… TF_WORKSPACE
#   GE_PROJECT GE_APP (pour add_agent_to_ge.sh et simuler_gemini_enterprise.sh).
#
# RÉSULTAT ATTENDU
#   == Configuration chargée : config/12-1-agents-dans-projet-exp.env
#      App Gemini Enterprise : (pas encore : agents seuls)   (projet -, numéro -, eu)
#      Projet des agents     : <PROJET_AGENTS> (numéro <NUM_AGENTS>), région europe-west1   [même projet que l'app : non]
#      Agents à déployer     : meteo
#      Compte de l'app       : (aucun : pas encore d'app, aucun droit donné)
#      Terraform             : espace « scenario-12-1 », publication dans l'app : non
#      Dossier               : <DOSSIER>
#      OK
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « Usage : source scripts/config.sh … »        -> fichier absent ou mal écrit : vérifier le chemin config/….env.
#   « MANQUANT : X dans … »                      -> X vide dans le fichier (PROJET_APP NUM_APP APP_ID si PUBLIER=oui).
#   « ATTENTION : agent « x » absent de … »      -> faute de frappe dans AGENTS (clés de agents/trio/catalogue.json).
#   « ATTENTION : NUM_APP et NUM_AGENTS … »      -> mettre les NUMÉROS de projet (chiffres), pas les ID.
#   « ATTENTION : région … incompatible … »      -> app eu => REGION europe-… ; app us => us-….
#   « À CORRIGER dans … » à la fin               -> les variables sont chargées QUAND MÊME : corriger, puis relancer.
#   Plus tard, une commande avec « --project= » vide -> configuration pas chargée dans CE terminal : relancer.

# Pas de fichier valide : on affiche l'usage. « return » arrête un script lancé avec source ; si quelqu'un l'a lancé
# avec bash, « return » échoue et c'est « exit » qui sert.
if [ -z "${1:-}" ] || [ ! -f "$1" ]; then
  echo "Usage : source scripts/config.sh config/<fichier>.env   (fichiers : $(ls config/*.env 2>/dev/null | tr '\n' ' '))"
  return 1 2>/dev/null || exit 1
fi

# « set -a » : toute variable lue dans le fichier est automatiquement exportée (visible par gcloud, Terraform, Python).
set -a
# shellcheck disable=SC1090
. "$1"
set +a
CONFIG_FICHIER=$1
SCENARIO=$(basename "$1" .env | cut -d- -f1-2)           # 12-1 ou 12-2

# Valeurs calculées
GE_SA=${NUM_APP:+service-$NUM_APP@gcp-sa-discoveryengine.iam.gserviceaccount.com}   # compte de Gemini Enterprise (vide : pas encore d'app)
MEME_PROJET=$([ "$PROJET_AGENTS" = "$PROJET_APP" ] && echo oui || echo non)
# Les agents à déployer : AGENTS du fichier, ou tous ceux du catalogue si AGENTS est vide.
AGENTS_LISTE=${AGENTS:-$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))))' "$(dirname "$1")/../agents/trio/catalogue.json" 2>/dev/null)}
export GE_SA MEME_PROJET SCENARIO CONFIG_FICHIER AGENTS_LISTE

# Templates Model Armor de la méthode shell (fichier : PROMPT_TEMPLATE / RESPONSE_TEMPLATE pour des templates centraux)
export PROMPT_TEMPLATE=${PROMPT_TEMPLATE:-projects/$PROJET_AGENTS/locations/$GE_LOCATION/templates/agents-prompt-shield}
export RESPONSE_TEMPLATE=${RESPONSE_TEMPLATE:-projects/$PROJET_AGENTS/locations/$GE_LOCATION/templates/agents-response-shield}

# gcloud : projet par défaut, et point d'accès européen de Model Armor (templates en « eu »)
# (sans ce point d'accès régional, « gcloud model-armor templates … » ne trouve pas les templates « eu »)
export CLOUDSDK_CORE_PROJECT=$PROJET_AGENTS
export CLOUDSDK_API_ENDPOINT_OVERRIDES_MODELARMOR=https://modelarmor.$GE_LOCATION.rep.googleapis.com/

# Terraform : les variables viennent d'ici ; un « espace de travail » par scénario (états séparés)
export TF_VAR_agents_project_id=$PROJET_AGENTS
export TF_VAR_ge_project_number=$NUM_APP
export TF_VAR_ge_project_id=$PROJET_APP
export TF_VAR_region=$REGION
export TF_VAR_ge_location=$GE_LOCATION
# ge_app_id vide quand PUBLIER n'est pas « oui » : Terraform déploie les agents sans les ajouter à l'app.
export TF_VAR_ge_app_id=$([ "$PUBLIER" = "oui" ] && echo "$APP_ID" || echo "")
export TF_VAR_agent_gateway=$([ "${AGENT_GATEWAY:-non}" = "oui" ] && echo true || echo false)
# Agents qui agissent avec le compte de l'utilisateur (OAuth, docs/12-3 partie C) : AGENTS_OAUTH="cle=ID_autorisation …"
# Les deux lignes suivantes traduisent le texte du fichier en syntaxe Terraform :
#   AGENTS_OAUTH="velo=acces-drive"  ->  TF_VAR_oauth_agents={"velo"="acces-drive",}
#   AGENTS="meteo taille"            ->  TF_VAR_agents=["meteo","taille",]
# (les morceaux mal écrits sont ignorés par sed : seules les clés en minuscules/chiffres sont gardées).
export TF_VAR_oauth_agents="{$(printf '%s' "${AGENTS_OAUTH:-}" | tr ' ' '\n' | sed -n 's/^\([a-z0-9]*\)=\(.*\)$/"\1"="\2",/p' | tr -d '\n')}"
export TF_VAR_agents="[$(printf '%s' "${AGENTS:-}" | tr ' ' '\n' | sed -n 's/^\([a-z0-9]*\)$/"\1",/p' | tr -d '\n')]"   # vide = tous
export TF_VAR_ge_engine=projects/$NUM_APP/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID
export TF_WORKSPACE=scenario-$SCENARIO

# Scripts d'ajout à l'app (add_agent_to_ge.sh)
export GE_PROJECT=$PROJET_APP GE_APP=$APP_ID

# Vérifications (on note les problèmes dans _ok sans s'arrêter, pour tous les afficher d'un coup)
_ok=1
# Toujours obligatoires : le projet des agents. L'app (PROJET_APP, NUM_APP, APP_ID) peut attendre : vide = agents seuls.
_requis="GE_LOCATION PROJET_AGENTS NUM_AGENTS REGION DOSSIER"
[ "${PUBLIER:-non}" = "oui" ] && _requis="$_requis PROJET_APP NUM_APP APP_ID"
# « $(echo $_requis) » : découpe la liste en mots aussi sous zsh (qui, sinon, ne découpe pas une variable).
for _v in $(echo $_requis); do
  eval "_val=\${$_v:-}"                                    # compatible bash et zsh (Mac)
  [ -n "$_val" ] || { echo "MANQUANT : $_v dans $1"; _ok=0; }
done
for _k in $(echo $AGENTS_LISTE); do                     # chaque agent demandé doit exister dans le catalogue
  python3 -c 'import json,sys; sys.exit(sys.argv[2] not in json.load(open(sys.argv[1])))' "$(dirname "$1")/../agents/trio/catalogue.json" "$_k" \
    || { echo "ATTENTION : agent « $_k » absent de agents/trio/catalogue.json"; _ok=0; }
done
case "$NUM_APP$NUM_AGENTS" in *[!0-9]*) echo "ATTENTION : NUM_APP et NUM_AGENTS doivent être des nombres"; _ok=0;; esac
# Une app « eu » n'accepte que des agents en europe-…, une app « us » en us-… ; « global » accepte tout.
case "$GE_LOCATION:$REGION" in eu:europe-*|us:us-*|global:*) ;; *) echo "ATTENTION : région $REGION incompatible avec une app $GE_LOCATION"; _ok=0;; esac

# Le résumé affiché (les variables _… sont temporaires, effacées à la fin)
_app=${APP_ID:-"(pas encore : agents seuls)"}; _sa=${GE_SA:-"(aucun : pas encore d'app, aucun droit donné)"}
cat <<RESUME
== Configuration chargée : $1
   App Gemini Enterprise : $_app   (projet ${PROJET_APP:--}, numéro ${NUM_APP:--}, $GE_LOCATION)
   Projet des agents     : $PROJET_AGENTS (numéro $NUM_AGENTS), région $REGION   [même projet que l'app : $MEME_PROJET]
   Agents à déployer     : $AGENTS_LISTE
   Compte de l'app       : $_sa
   Terraform             : espace « $TF_WORKSPACE », publication dans l'app : $PUBLIER
   Dossier               : $DOSSIER
RESUME
[ $_ok = 1 ] && echo "   OK" || echo "   À CORRIGER dans $1, puis relancer cette commande."
unset _ok _v _val _k _requis _app _sa
