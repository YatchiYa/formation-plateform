#!/usr/bin/env bash
# Connecter à l'app Gemini Enterprise des agents DÉJÀ déployés dans le projet des agents (docs/12-1-4).
#
# À QUOI SERT CE SCRIPT
#   Étape après le déploiement (docs/12-1-1, 12-1-3). Il fait, dans l'ordre et en demandant confirmation :
#     1. vérifier (LECTURE SEULE) : l'app existe, vos droits, les agents déployés, les droits déjà donnés ;
#     2. droits : donner au compte de l'app le droit d'appeler les agents (dans le PROJET DES AGENTS seulement) ;
#     3. ajouter : ajouter chaque agent dans l'app (une entrée par agent, sans doublon).
#   L'accès des utilisateurs (rôle Agent User) se donne ensuite dans la console (docs/12-1-4, partie 6).
#
# PRÉREQUIS
#   Configuration chargée : source scripts/config.sh config/12-1-agents-dans-projet-exp.env, avec PROJET_APP,
#   NUM_APP, APP_ID, GE_LOCATION remplis (docs/12-1-4, partie 2). Les agents : la ligne AGENTS (vide = tous).
#   Vos droits : Gemini Enterprise Admin (roles/discoveryengine.admin) sur le projet de l'app ; sur le projet des
#   agents, de quoi donner des rôles (roles/resourcemanager.projectIamAdmin et roles/run.admin, ou Propriétaire).
#
# UTILISATION
#   ./scripts/connecter_app.sh apps                  # LECTURE SEULE : les apps du projet de l'app (pour APP_ID)
#   ./scripts/connecter_app.sh verifier              # LECTURE SEULE : tout vérifier, dire ce qui reste à faire
#   ./scripts/connecter_app.sh droits                # donner les droits (montre la liste, demande confirmation)
#   ./scripts/connecter_app.sh ajouter               # ajouter les agents dans l'app (liste, confirmation)
#   ./scripts/connecter_app.sh lister                # LECTURE SEULE : les agents présents dans l'app
#   ./scripts/connecter_app.sh retirer               # retour arrière : retirer de l'app + retirer run.invoker
#   … meteo taille                                   # seulement ces agents (sinon : ceux de AGENTS)
#   … --methode console                              # agents déployés par la console (noms en -console)
#   … --oui                                          # sans question (scripts) ; à éviter en production
#
# CE QU'IL CHANGE
#   apps, verifier, lister : rien.
#   droits  : projet des AGENTS seulement : roles/discoveryengine.serviceAgent sur le projet (agents Agent Runtime),
#             roles/run.invoker sur chaque service Cloud Run, pour le compte de l'app service-NUM_APP@gcp-sa-…
#   ajouter : projet de l'APP : une entrée par agent dans l'app (rien d'autre : ni IAM, ni API).
#   retirer : l'inverse des deux (le rôle sur le projet n'est retiré qu'avec --tout : d'autres agents peuvent s'en servir).
#   Relancer est sans danger : ce qui est déjà fait est sauté.
set -euo pipefail
: "${PROJET_AGENTS:?Chargez la configuration : source scripts/config.sh config/<fichier>.env}"
cd "$(dirname "$0")/.."

ACTION=${1:-aide}; [ $# -gt 0 ] && shift
METHODE=shell; OUI=non; TOUT=non; CLES=""
while [ $# -gt 0 ]; do
  case "$1" in
    --methode) METHODE=$2; shift 2;;
    --oui) OUI=oui; shift;;
    --tout) TOUT=oui; shift;;
    *) CLES="$CLES $1"; shift;;
  esac
done
CLES=${CLES:-$AGENTS_LISTE}
case "$METHODE" in shell|console) ;; *) echo "--methode : shell ou console (Terraform : docs/12-1-4, méthode Terraform)"; exit 2;; esac
PY=$(command -v python || command -v python3)

# Noms des ressources selon la méthode de déploiement (12-1-1 : -shell ; 12-1-3 : -console).
service_cr() { echo "$1-a2a-$METHODE"; }                    # service Cloud Run de l'agent
nom_rt() { echo "$1-$METHODE"; }                            # nom affiché de l'agent Agent Runtime
cle() { $PY -c "import json,sys; print(json.load(open('agents/trio/catalogue.json'))[sys.argv[1]][sys.argv[2]])" "$1" "$2"; }
# Noms dans l'app : comme Terraform (« Météo & équipement » pour Agent Runtime, « … (A2A) » pour Cloud Run).
nom_app_rt() { cle "$1" nom_affiche; }
nom_app_a2a() { echo "$(cle "$1" nom_affiche) (A2A)"; }

besoin_app() {  # l'app doit être renseignée pour tout sauf « apps »
  for v in PROJET_APP NUM_APP APP_ID GE_LOCATION; do
    eval "[ -n \"\${$v:-}\" ]" || { echo "MANQUANT dans le fichier de configuration : $v (docs/12-1-4, partie 2)"; exit 2; }
  done
}
jeton() { gcloud auth print-access-token; }
hote() { [ "$1" = global ] && echo discoveryengine.googleapis.com || echo "$1-discoveryengine.googleapis.com"; }
api() {  # api GET|DELETE <url> : appel REST à l'API de l'app, facturé au projet de l'app
  curl -sS -X "$1" -H "Authorization: Bearer $(jeton)" -H "X-Goog-User-Project: $PROJET_APP" "$2"
}
moteur() {  # nom de ressource de l'agent Agent Runtime $1 (nom affiché), vide s'il n'existe pas
  curl -s -H "Authorization: Bearer $(jeton)" \
    "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
    | $PY -c "import json,sys; print(next((e['name'] for e in json.load(sys.stdin).get('reasoningEngines',[]) if e['displayName']==sys.argv[1]), ''))" "$1"
}
existe_cr() { gcloud run services describe "$(service_cr "$1")" --region="$REGION" --project="$PROJET_AGENTS" >/dev/null 2>&1; }
a_invoker() {  # le compte de l'app a-t-il run.invoker sur le service de l'agent $1 ?
  gcloud run services get-iam-policy "$(service_cr "$1")" --region="$REGION" --project="$PROJET_AGENTS" \
    --flatten=bindings --filter="bindings.role=roles/run.invoker AND bindings.members:$GE_SA" --format="value(bindings.role)" 2>/dev/null | grep -q .
}
a_service_agent() {  # le compte de l'app a-t-il discoveryengine.serviceAgent sur le projet des agents ?
  gcloud projects get-iam-policy "$PROJET_AGENTS" --flatten=bindings \
    --filter="bindings.role=roles/discoveryengine.serviceAgent AND bindings.members:$GE_SA" --format="value(bindings.role)" | grep -q .
}
agents_app() {  # noms affichés des agents déjà dans l'app, un par ligne
  api GET "https://$(hote "$GE_LOCATION")/v1alpha/projects/$PROJET_APP/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID/assistants/default_assistant/agents" \
    | $PY -c 'import json,sys; [print(a.get("displayName","")) for a in json.load(sys.stdin).get("agents",[])]'
}
confirmer() {  # confirmer "<texte>" <valeur à taper>
  [ "$OUI" = oui ] && return 0
  read -r -p "$1 Tapez « $2 » pour confirmer : " r
  [ "$r" = "$2" ] || { echo "Annulé : rien n'a été changé."; exit 1; }
}

case "$ACTION" in
  apps)
    : "${PROJET_APP:?PROJET_APP vide dans la configuration}"
    echo "== Apps Gemini Enterprise du projet $PROJET_APP (APP_ID = 1re colonne, GE_LOCATION = 2e)"
    for loc in eu us global; do
      api GET "https://$(hote $loc)/v1alpha/projects/$PROJET_APP/locations/$loc/collections/default_collection/engines" \
        | $PY -c 'import json,sys
d=json.load(sys.stdin)
for e in d.get("engines",[]): print("  " + e["name"].split("/")[-1].ljust(40), sys.argv[1].ljust(7), e.get("displayName",""), "(" + e.get("solutionType","") + ")")' "$loc" 2>/dev/null || true
    done
    echo "(aucune ligne : pas d'app dans ce projet, ou pas le droit de les lire : roles/discoveryengine.viewer)";;

  verifier)
    besoin_app
    echo "== 1. Configuration"
    n=$(gcloud projects describe "$PROJET_APP" --format='value(projectNumber)' 2>/dev/null || true)
    [ "$n" = "$NUM_APP" ] && echo "  OK   numéro du projet de l'app : $NUM_APP" || { echo "  KO   NUM_APP=$NUM_APP mais $PROJET_APP a le numéro « $n »"; exit 1; }
    echo "== 2. L'app"
    app=$(api GET "https://$(hote "$GE_LOCATION")/v1alpha/projects/$PROJET_APP/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID")
    if echo "$app" | grep -q '"displayName"'; then
      echo "  OK   $APP_ID existe : « $(echo "$app" | $PY -c 'import json,sys; print(json.load(sys.stdin)["displayName"])') » ($GE_LOCATION)"
    else
      echo "  KO   app $APP_ID introuvable en $GE_LOCATION : $(echo "$app" | $PY -c 'import json,sys; print(json.load(sys.stdin).get("error",{}).get("message","?"))' 2>/dev/null)"
      echo "       → pas encore d'app ? Les droits se vérifient quand même ci-dessous ; l'ajout attendra l'app."
      echo "       → pour prouver l'appel sans app : docs/12-1-5 (simulation). Liste des apps : ./scripts/connecter_app.sh apps"
      APP_ABSENTE=oui
    fi
    case "$GE_LOCATION:$REGION" in eu:europe-*|us:us-*|global:*) echo "  OK   région des agents $REGION compatible avec l'app $GE_LOCATION";;
      *) echo "  KO   région $REGION incompatible avec une app $GE_LOCATION"; exit 1;; esac
    echo "== 3. Vos rôles (directs ; ceux reçus par un groupe ne s'affichent pas : vérifier dans la console)"
    moi=$(gcloud config get-value account 2>/dev/null)
    for p in "$PROJET_APP" "$PROJET_AGENTS"; do
      echo "  $p : $(gcloud projects get-iam-policy "$p" --flatten=bindings --filter="bindings.members:user:$moi" --format='value(bindings.role)' 2>/dev/null | tr '\n' ' ')"
    done
    echo "== 4. Les agents (méthode $METHODE) et les droits du compte de l'app $GE_SA"
    if [ "$MEME_PROJET" = oui ]; then echo "  OK   même projet que l'app : rien à donner pour Agent Runtime"
    elif a_service_agent; then echo "  OK   discoveryengine.serviceAgent sur $PROJET_AGENTS (agents Agent Runtime)"
    else echo "  À FAIRE  discoveryengine.serviceAgent sur $PROJET_AGENTS (si vous ajoutez des agents Agent Runtime)"; fi
    dans_app=$(agents_app 2>/dev/null || true)
    deploye=non
    for K in $CLES; do
      if existe_cr "$K"; then deploye=oui
        a_invoker "$K" && d="droit OK" || d="À FAIRE : run.invoker"
        grep -qxF "$(nom_app_a2a "$K")" <<<"$dans_app" && a="dans l'app" || a="À AJOUTER"
        [ "${APP_ABSENTE:-non}" = oui ] && a="(app absente)"
        echo "  $K  Cloud Run $(service_cr "$K") : $d ; « $(nom_app_a2a "$K") » : $a"
      else echo "  $K  Cloud Run $(service_cr "$K") : non déployé"; fi
      if [ -n "$(moteur "$(nom_rt "$K")")" ]; then deploye=oui
        grep -qxF "$(nom_app_rt "$K")" <<<"$dans_app" && a="dans l'app" || a="À AJOUTER"
        [ "${APP_ABSENTE:-non}" = oui ] && a="(app absente)"
        echo "  $K  Agent Runtime $(nom_rt "$K") : « $(nom_app_rt "$K") » : $a"
      else echo "  $K  Agent Runtime $(nom_rt "$K") : non déployé"; fi
    done
    [ $deploye = non ] && echo "  → aucun de ces agents n'est déployé (méthode $METHODE) : déployez d'abord (docs/12-1-1, ./scripts/deployer_shell.sh)."
    echo "Rien n'a été changé. Suite : ./scripts/connecter_app.sh droits$([ "${APP_ABSENTE:-non}" = oui ] && echo " (l'ajout attendra l'app)" || echo ", puis ajouter")."
    [ "${APP_ABSENTE:-non}" = oui ] && exit 1 || exit 0;;

  droits)
    besoin_app
    plan=()
    rt=non; cr=non
    for K in $CLES; do [ -n "$(moteur "$(nom_rt "$K")")" ] && rt=oui; existe_cr "$K" && cr=oui; done
    [ $rt = non ] && [ $cr = non ] && { echo "Aucun agent déployé (méthode $METHODE) parmi : $CLES. Déployez d'abord (docs/12-1-1)."; exit 1; }
    [ "$MEME_PROJET" = non ] && [ $rt = oui ] && ! a_service_agent && plan+=("projet $PROJET_AGENTS : roles/discoveryengine.serviceAgent")
    for K in $CLES; do existe_cr "$K" && ! a_invoker "$K" && plan+=("service $(service_cr "$K") : roles/run.invoker"); done
    [ ${#plan[@]} = 0 ] && { echo "Rien à faire : les droits sont déjà en place."; exit 0; }
    echo "== Droits à donner à $GE_SA, dans le projet des agents $PROJET_AGENTS :"; printf '   - %s\n' "${plan[@]}"
    confirmer "Ces droits permettent à l'app d'APPELER ces agents." "$PROJET_AGENTS"
    gcloud beta services identity create --service=discoveryengine.googleapis.com --project="$PROJET_APP" >/dev/null 2>&1 || true
    for ligne in "${plan[@]}"; do
      case "$ligne" in
        projet*) echo "▶ gcloud projects add-iam-policy-binding $PROJET_AGENTS --condition=None --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$GE_SA"
                 gcloud projects add-iam-policy-binding "$PROJET_AGENTS" --condition=None --role=roles/discoveryengine.serviceAgent \
                   --member="serviceAccount:$GE_SA" >/dev/null && echo "  fait";;
        service*) S=$(echo "$ligne" | cut -d' ' -f2)
                 echo "▶ gcloud run services add-iam-policy-binding $S --region=$REGION --project=$PROJET_AGENTS --role=roles/run.invoker --member=serviceAccount:$GE_SA"
                 gcloud run services add-iam-policy-binding "$S" --region="$REGION" --project="$PROJET_AGENTS" \
                   --role=roles/run.invoker --member="serviceAccount:$GE_SA" >/dev/null && echo "  fait";;
      esac
    done
    echo "Droits donnés. Ils s'appliquent en 2 à 3 minutes. Suite : ./scripts/connecter_app.sh ajouter";;

  ajouter)
    besoin_app
    dans_app=$(agents_app); plan=()
    for K in $CLES; do
      R=$(moteur "$(nom_rt "$K")")
      [ -n "$R" ] && ! grep -qxF "$(nom_app_rt "$K")" <<<"$dans_app" && plan+=("adk|$K|$R")
      existe_cr "$K" && ! grep -qxF "$(nom_app_a2a "$K")" <<<"$dans_app" && plan+=("a2a|$K|")
    done
    [ ${#plan[@]} = 0 ] && { echo "Rien à ajouter : les agents déployés sont déjà dans l'app."; exit 0; }
    echo "== À ajouter dans l'app $APP_ID (projet $PROJET_APP) :"
    for p in "${plan[@]}"; do IFS='|' read -r t K R <<<"$p"
      [ $t = adk ] && echo "   - « $(nom_app_rt "$K") »  (Agent Runtime $R)" || echo "   - « $(nom_app_a2a "$K") »  (A2A, service $(service_cr "$K"))"; done
    confirmer "Ces agents apparaîtront dans l'app (visibles seulement après l'étape Agent User)." "$APP_ID"
    for p in "${plan[@]}"; do IFS='|' read -r t K R <<<"$p"
      if [ $t = adk ]; then
        echo "▶ ./scripts/add_agent_to_ge.sh adk $R \"$(nom_app_rt "$K")\""
        ./scripts/add_agent_to_ge.sh adk "$R" "$(nom_app_rt "$K")" "$(cle "$K" description)"
      else
        "$PY" scripts/carte_a2a.py "$K" "https://$(service_cr "$K")-$NUM_AGENTS.$REGION.run.app" > "carte-$K.json"
        echo "▶ ./scripts/add_agent_to_ge.sh a2a carte-$K.json \"$(nom_app_a2a "$K")\""
        ./scripts/add_agent_to_ge.sh a2a "carte-$K.json" "$(nom_app_a2a "$K")" | grep -v "Donner roles/run.invoker" || true
      fi
    done
    echo "Ajoutés. Suite : l'accès Agent User pour $GROUPE_UTILISATEURS, dans la console (docs/12-1-4, partie 6).";;

  lister)
    besoin_app; ./scripts/add_agent_to_ge.sh list;;

  retirer)
    besoin_app
    dans_app=$(agents_app); plan=()
    for K in $CLES; do
      for n in "$(nom_app_rt "$K")" "$(nom_app_a2a "$K")"; do grep -qxF "$n" <<<"$dans_app" && plan+=("app|$n"); done
      existe_cr "$K" && a_invoker "$K" && plan+=("invoker|$(service_cr "$K")")
    done
    [ "$TOUT" = oui ] && [ "$MEME_PROJET" = non ] && a_service_agent && plan+=("projet|$PROJET_AGENTS")
    [ ${#plan[@]} = 0 ] && { echo "Rien à retirer."; exit 0; }
    echo "== Retour arrière :"
    for p in "${plan[@]}"; do IFS='|' read -r t v <<<"$p"; case $t in
      app) echo "   - retirer « $v » de l'app";; invoker) echo "   - retirer run.invoker de l'app sur $v";;
      projet) echo "   - retirer discoveryengine.serviceAgent de l'app sur le projet $v (TOUS ses agents Agent Runtime)";; esac; done
    confirmer "Les utilisateurs ne verront plus ces agents." "$APP_ID"
    for p in "${plan[@]}"; do IFS='|' read -r t v <<<"$p"; case $t in
      app) ./scripts/add_agent_to_ge.sh delete "$v";;
      invoker) gcloud run services remove-iam-policy-binding "$v" --region="$REGION" --project="$PROJET_AGENTS" \
                 --role=roles/run.invoker --member="serviceAccount:$GE_SA" >/dev/null && echo "retiré : run.invoker sur $v";;
      projet) gcloud projects remove-iam-policy-binding "$v" --condition=None --role=roles/discoveryengine.serviceAgent \
                --member="serviceAccount:$GE_SA" >/dev/null && echo "retiré : discoveryengine.serviceAgent sur $v";;
    esac; done;;

  *) sed -n '2,32p' "$0"; exit 2;;
esac
