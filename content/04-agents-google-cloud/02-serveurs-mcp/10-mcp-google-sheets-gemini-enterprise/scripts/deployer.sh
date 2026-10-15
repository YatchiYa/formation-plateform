#!/usr/bin/env bash
# Projet 10 : déployer le serveur MCP Google Sheets et l'agent qui l'utilise, puis les brancher sur Gemini Enterprise.
# Une action par étape. Tout vient de la configuration chargée : source scripts/config.sh config/10-mcp.env
#
# UTILISATION (dans le dossier du projet 10)
#   ./scripts/deployer.sh verifier          # LECTURE SEULE : facturation, API, vos droits, ce qui existe déjà
#   ./scripts/deployer.sh preparer          # une fois : API, 3 comptes de service (construction, MCP, agent) et leurs rôles
#   ./scripts/deployer.sh mcp [sheets|slides] # les serveurs MCP Sheets et Slides sur Cloud Run (privés), une image Cloud Build
#   ./scripts/deployer.sh agent             # l'agent A2A sur Cloud Run (+ droit d'appeler le serveur MCP)
#   ./scripts/deployer.sh agent-runtime     # l'agent sur Agent Runtime (+ droit d'appeler le serveur MCP)
#   ./scripts/deployer.sh registre          # déclarer le serveur MCP (et ses 17 outils) dans Agent Registry
#   ./scripts/deployer.sh fiche             # TOUT ce qu'il faut saisir dans Gemini Enterprise, modalité par modalité
#   ./scripts/deployer.sh droits-app        # droits du compte de l'app (plan, puis confirmation)            [NUM_APP]
#   ./scripts/deployer.sh autorisation client_secret.json [a2a|runtime]   # autorisation OAuth de l'agent  [app]
#   ./scripts/deployer.sh ajouter-app [a2a|runtime]                      # ajouter l'agent à l'app        [app]
#   ./scripts/deployer.sh tester            # tests réels (USER_TOKEN, SPREADSHEET_ID, et PRESENTATION_ID pour Slides : docs/10-8)
#   ./scripts/deployer.sh nettoyer          # inventaire, puis suppression après confirmation
#   --oui : pas de question (droits-app, nettoyer).
#
# Chaque commande lancée est affichée (▶). Relancer est sans danger : ce qui existe est gardé (« mcp » et « agent »
# redéploient une nouvelle révision, même adresse : c'est voulu). Guides : docs/10-2 (ce script pas à pas), docs/10-8.
set -euo pipefail
: "${PROJET:?Chargez la configuration : source scripts/config.sh config/10-mcp.env}"
cd "$(dirname "$0")/.."
ACTION=${1:-aide}; [ $# -gt 0 ] && shift
OUI=non; ARGS=()
for a in "$@"; do [ "$a" = --oui ] && OUI=oui || ARGS+=("$a"); done
set -- ${ARGS[@]+"${ARGS[@]}"}
PY=$( [ -x .venv/bin/python ] && echo .venv/bin/python || command -v python3 )
AUTH_ID_RUNTIME=$AUTH_ID-runtime   # Agent Runtime : autorisation à part, avec la portée cloud-platform en plus
SCOPES="openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.metadata.readonly"

lancer() { echo "▶ $*" >&2; "$@"; }
existe() { "$@" >/dev/null 2>&1; }
roles() {  # roles <compte> <rôle…> : rôles sur le projet ; réessaie si le compte est tout neuf (« does not exist »)
  local sa=$1 r essai; shift
  for r in "$@"; do
    for essai in 1 2 3 4 5 6; do
      gcloud projects add-iam-policy-binding "$PROJET" --condition=None --role="roles/$r" --member="serviceAccount:$sa" \
        >/dev/null 2>&1 && { echo "  ${sa%%@*} : roles/$r"; break; }
      [ $essai = 6 ] && { echo "ÉCHEC : roles/$r pour $sa (vos droits ? relancez)"; exit 1; }
      echo "  ${sa%%@*} : pas encore visible pour IAM, nouvel essai dans 10 s"; sleep 10
    done
  done
}
compte() {  # compte <nom> <description>
  existe gcloud iam service-accounts describe "$1@$PROJET.iam.gserviceaccount.com" --project="$PROJET" \
    && echo "  compte $1 : existe déjà" \
    || lancer gcloud iam service-accounts create "$1" --project="$PROJET" --display-name="$2"
}
invoker() {  # invoker <service Cloud Run> <membre> : droit d'appel (sans effet s'il existe)
  lancer gcloud run services add-iam-policy-binding "$1" --region="$REGION" --project="$PROJET" \
    --role=roles/run.invoker --member="$2" --condition=None >/dev/null 2>&1 && echo "  $2 : roles/run.invoker sur $1" \
    || { echo "ÉCHEC : run.invoker sur $1 pour $2 (le compte existe-t-il ? vos droits ?)"; exit 1; }
}
service_existe() { existe gcloud run services describe "$1" --region="$REGION" --project="$PROJET"; }
runtime() { "$PY" scripts/deployer_agent_runtime.py --projet "$PROJET" --region "$REGION" --trouver; }
confirmer() {  # confirmer <message> : demande de taper l'ID du projet (sauf --oui)
  [ "$OUI" = oui ] && return 0
  read -r -p "$1 Tapez l'ID du projet ($PROJET) pour confirmer : " R
  [ "$R" = "$PROJET" ] || { echo "Rien n'a été fait."; exit 0; }
}
construire() {  # construire <dossier> <nom> : image construite par Cloud Build ; affiche son nom (sortie standard)
  local dir=$1 image essai
  image=$REGION-docker.pkg.dev/$PROJET/sheets-mcp/$2:$(date +%Y%m%d-%H%M%S)
  existe gcloud artifacts repositories describe sheets-mcp --location="$REGION" --project="$PROJET" \
    || lancer gcloud artifacts repositories create sheets-mcp --repository-format=docker --location="$REGION" --project="$PROJET" >&2
  for essai in 1 2 3; do   # un compte de construction tout neuf peut être refusé 1 à 2 minutes
    lancer gcloud builds submit "$dir" --config=cloudbuild.yaml --substitutions="_IMAGE=$image" --region="$REGION" \
      --project="$PROJET" --service-account="projects/$PROJET/serviceAccounts/$BUILD_SA" >&2 && { echo "$image"; return 0; }
    [ $essai = 3 ] && { echo "ÉCHEC de la construction de $2 : 🔎 Cloud Build → Historique → la construction → journal" >&2; exit 1; }
    echo "  nouvel essai dans 40 s (droits de construction en cours d'activation)" >&2; sleep 40
  done
}
deployer_image() {  # deployer_image <service> <image> <compte> <fichier env> <options…> : le service Cloud Run, PRIVÉ
  local svc=$1 image=$2 sa=$3 env=$4; shift 4
  lancer gcloud run deploy "$svc" --image="$image" --region="$REGION" --project="$PROJET" --service-account="$sa" \
    --no-allow-unauthenticated --env-vars-file="$env" --quiet "$@"
}
env_agent() {  # env_agent <fichier> : variables de l'agent ; l'adresse de chaque serveur MCP DÉPLOYÉ (Sheets, Slides)
  printf 'AGENT_URL: "%s"\nAUTH_ID: "%s"\nMODEL: "%s"\nGOOGLE_CLOUD_PROJECT: "%s"\n' "$AGENT_URL" "$AUTH_ID" "$MODEL" "$PROJET" > "$1"
  service_existe "$MCP_SERVICE" && printf 'MCP_URL: "%s"\n' "$MCP_URL" >> "$1"
  service_existe "$SLIDES_SERVICE" && printf 'MCP_SLIDES_URL: "%s"\n' "$SLIDES_URL" >> "$1"
  true
}
un_mcp() {  # vrai si au moins un serveur MCP est déployé
  service_existe "$MCP_SERVICE" || service_existe "$SLIDES_SERVICE" \
    || { echo "Déployez d'abord un serveur MCP : ./scripts/deployer.sh mcp (ou mcp sheets, mcp slides)"; exit 1; }
}
invoker_mcp() {  # invoker_mcp <membre> : droit d'appel sur chaque serveur MCP déployé (Sheets, Slides)
  local s; for s in "$MCP_SERVICE" "$SLIDES_SERVICE"; do service_existe "$s" && invoker "$s" "$1"; done; true
}
app_requise() { : "${NUM_APP:?Renseignez NUM_APP (et PROJET_APP, APP_ID) : dans le fichier, ou devant la commande}"; }

case "$ACTION" in
  verifier)
    echo "== Compte gcloud : $(gcloud config get-value account 2>/dev/null)"
    F=$(gcloud billing projects describe "$PROJET" --format='value(billingEnabled)' 2>/dev/null || echo "?")
    echo "== Facturation de $PROJET : $( [ "$F" = True ] && echo active || echo "DÉSACTIVÉE ($F)")"; [ "$F" = True ] || echo "   !! Sans facturation : Cloud Run, Cloud Build, Vertex AI et Agent Runtime refusent."
    ACTIVES=$(gcloud services list --enabled --project="$PROJET" --format='value(config.name)' 2>/dev/null || true)
    echo "== API"
    for s in run cloudbuild artifactregistry iam logging sheets drive aiplatform agentregistry; do
      grep -qx "$s.googleapis.com" <<<"$ACTIVES" && echo "   OK       $s" || echo "   inactive $s   (./scripts/deployer.sh preparer)"
    done
    echo "== Vos droits sur $PROJET (groupes compris)"
    "$PY" - "$PROJET" "$(gcloud auth print-access-token)" <<'PY'
import json, sys, urllib.request
p, t = sys.argv[1], sys.argv[2]
B = [("serviceusage.services.enable", "activer les API", "serviceusage.serviceUsageAdmin"),
     ("iam.serviceAccounts.create", "créer les comptes de service", "iam.serviceAccountAdmin"),
     ("iam.serviceAccounts.actAs", "faire tourner un service avec un compte", "iam.serviceAccountUser"),
     ("resourcemanager.projects.setIamPolicy", "donner des rôles", "resourcemanager.projectIamAdmin"),
     ("cloudbuild.builds.create", "construire les images", "cloudbuild.builds.editor"),
     ("artifactregistry.repositories.create", "dépôt d'images (1re fois)", "artifactregistry.admin"),
     ("run.services.create", "services Cloud Run", "run.admin"),
     ("run.services.setIamPolicy", "droit d'appel run.invoker", "run.admin"),
     ("aiplatform.reasoningEngines.create", "Agent Runtime", "aiplatform.admin"),
     ("agentregistry.services.create", "Agent Registry (facultatif)", "agentregistry.editor")]
r = urllib.request.Request(f"https://cloudresourcemanager.googleapis.com/v3/projects/{p}:testIamPermissions",
                           json.dumps({"permissions": [b[0] for b in B]}).encode(), {"Authorization": "Bearer " + t, "Content-Type": "application/json"})
ok = set(json.load(urllib.request.urlopen(r, timeout=30)).get("permissions", []))
for perm, usage, role in B:
    print(f"   {'OK      ' if perm in ok else 'MANQUANT'} {usage:<42} {'' if perm in ok else '-> demander roles/' + role}")
PY
    echo "== Déjà là"
    for s in "$MCP_SERVICE" "$SLIDES_SERVICE" "$AGENT_SERVICE"; do service_existe "$s" && echo "   Cloud Run $s" || echo "   (pas de service $s)"; done
    R=$(runtime 2>/dev/null || true); echo "   Agent Runtime : ${R:-(aucun)}"
    [ -z "$OAUTH_CLIENT_IDS" ] && echo "!! OAUTH_CLIENT_IDS vide : créez le client OAuth (docs/10-5, étape 1) avant « mcp »."
    true;;

  preparer)
    lancer gcloud services enable cloudresourcemanager.googleapis.com serviceusage.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
      iam.googleapis.com logging.googleapis.com sheets.googleapis.com slides.googleapis.com drive.googleapis.com aiplatform.googleapis.com --project="$PROJET"
    lancer gcloud services enable agentregistry.googleapis.com --project="$PROJET" \
      || echo "  (Agent Registry indisponible ou bloqué par l'organisation : facultatif, l'action « registre » le dira)"
    compte sheets-build-sa "Construction des images du projet 10 (Cloud Build)"
    roles "$BUILD_SA" storage.objectViewer artifactregistry.writer logging.logWriter
    compte sheets-mcp-sa "Serveur MCP Google Sheets : AUCUN rôle (agit avec le jeton de l'utilisateur)"
    compte sheets-agent-sa "Agent Assistant Google Sheets (Cloud Run et Agent Runtime)"
    roles "$AGENT_SA" aiplatform.user logging.logWriter
    echo "Prêt. Attendez 1 à 2 minutes (droits des nouveaux comptes), puis : ./scripts/deployer.sh mcp";;

  mcp)
    [ -n "$OAUTH_CLIENT_IDS" ] || { echo "OAUTH_CLIENT_IDS est vide : le serveur refuserait de démarrer (sécurité). Créez le client OAuth (docs/10-5, étape 1), mettez son ID dans le fichier, rechargez."; exit 1; }
    PRODUITS=${*:-sheets slides}   # ./scripts/deployer.sh mcp sheets : seulement Sheets
    IMAGE=$(construire mcp_server mcp-google)   # UNE image ; PRODUIT choisit les outils au démarrage
    for P in $PRODUITS; do
      E=$(mktemp); printf 'PRODUIT: "%s"\nOAUTH_CLIENT_IDS: "%s"\nALLOWED_DOMAINS: "%s"\n' "$P" "$OAUTH_CLIENT_IDS" "$ALLOWED_DOMAINS" > "$E"
      deployer_image "$P-mcp" "$IMAGE" "$MCP_SA" "$E" --memory=512Mi --cpu=1 --min-instances=0 --max-instances=5 --timeout=120
      rm -f "$E"
      echo "Serveur MCP $P : https://$P-mcp-$NUM_PROJET.$REGION.run.app/mcp (privé : sans droit run.invoker, Cloud Run répond 403)."
    done
    service_existe "$AGENT_SERVICE" && invoker_mcp "serviceAccount:$AGENT_SA"   # l'agent garde l'accès aux serveurs
    echo "Ensuite : ./scripts/deployer.sh agent (ou agent-runtime), registre, fiche.";;

  agent)
    un_mcp
    E=$(mktemp); env_agent "$E"
    deployer_image "$AGENT_SERVICE" "$(construire agent sheets-agent)" "$AGENT_SA" "$E" --memory=1Gi --cpu=1 --min-instances=0 --max-instances=1 --timeout=300
    rm -f "$E"
    invoker_mcp "serviceAccount:$AGENT_SA"
    echo; echo "Agent A2A : $AGENT_URL   carte : ./scripts/deployer.sh fiche";;

  agent-runtime)
    un_mcp
    invoker_mcp "serviceAccount:$AGENT_SA"
    R=$(runtime)
    if [ -n "$R" ]; then echo "déjà déployé : $R (nouvelle version : ./scripts/deployer.sh nettoyer, puis relancer)"; exit 0; fi
    lancer "$PY" scripts/deployer_agent_runtime.py --projet "$PROJET" --region "$REGION" --compte-service "$AGENT_SA" \
      --env "AUTH_ID=$AUTH_ID_RUNTIME" --env "MODEL=$MODEL" \
      $(service_existe "$MCP_SERVICE" && echo "--env MCP_URL=$MCP_URL") \
      $(service_existe "$SLIDES_SERVICE" && echo "--env MCP_SLIDES_URL=$SLIDES_URL");;

  registre)
    lancer "$PY" scripts/gen_toolspec.py
    for P in sheets slides; do
      service_existe "$P-mcp" || { echo "  ($P-mcp pas déployé : pas déclaré)"; continue; }
      if existe gcloud agent-registry services describe "$P-mcp" --location="$REGISTRE_LOCATION" --project="$PROJET"; then
        echo "  déjà déclaré : $P-mcp ($REGISTRE_LOCATION)"; continue
      fi
      NOM=$([ $P = sheets ] && echo "Google Sheets (MCP)" || echo "Google Slides (MCP)")
      lancer gcloud agent-registry services create "$P-mcp" --location="$REGISTRE_LOCATION" --project="$PROJET" \
        --display-name="$NOM" \
        --description="Lecture et modification de $NOM au nom de l'utilisateur (OAuth Google, domaine restreint)." \
        --mcp-server-spec-type=tool-spec --mcp-server-spec-content="$(cat terraform/toolspec-$P.json)" \
        --interfaces="url=https://$P-mcp-$NUM_PROJET.$REGION.run.app/mcp,protocolBinding=jsonrpc"
    done
    lancer gcloud agent-registry mcp-servers list --location="$REGISTRE_LOCATION" --project="$PROJET" \
      --format="table(displayName,name.basename())" || true;;

  fiche)
    A2A=""; service_existe "$AGENT_SERVICE" && A2A=$AGENT_URL
    "$PY" scripts/fiche.py --a2a "$A2A" --runtime "$(runtime 2>/dev/null || true)" --auth-a2a "$AUTH_ID" --auth-runtime "$AUTH_ID_RUNTIME" \
      $(service_existe "$MCP_SERVICE" && echo --sheets) $(service_existe "$SLIDES_SERVICE" && echo --slides);;

  droits-app)
    app_requise
    echo "Plan, pour le compte de l'app $GE_SA :"
    service_existe "$MCP_SERVICE" && echo "  ① roles/run.invoker sur $MCP_SERVICE        (connecteur « Custom MCP Server » Sheets)"
    service_existe "$SLIDES_SERVICE" && echo "  ① roles/run.invoker sur $SLIDES_SERVICE        (connecteur « Custom MCP Server » Slides)"
    service_existe "$AGENT_SERVICE" && echo "  ① roles/run.invoker sur $AGENT_SERVICE      (agent A2A)"
    R=$(runtime 2>/dev/null || true); [ -n "$R" ] && echo "  ② roles/discoveryengine.serviceAgent sur le projet $PROJET (agent Agent Runtime)"
    confirmer "Donner ces droits ?"
    invoker_mcp "serviceAccount:$GE_SA"
    service_existe "$AGENT_SERVICE" && invoker "$AGENT_SERVICE" "serviceAccount:$GE_SA"
    [ -n "$R" ] && roles "$GE_SA" discoveryengine.serviceAgent
    echo "Attendez 2 à 3 minutes avant de tester dans l'app.";;

  autorisation)
    app_requise; : "${PROJET_APP:?}"
    CLIENT=${1:?Usage : ./scripts/deployer.sh autorisation client_secret.json [a2a|runtime]}; MODE=${2:-a2a}
    ID=$AUTH_ID; S=$SCOPES
    service_existe "$SLIDES_SERVICE" && S="$S https://www.googleapis.com/auth/presentations"   # l'agent utilise aussi Slides
    [ "$MODE" = runtime ] && { ID=$AUTH_ID_RUNTIME; S="$S https://www.googleapis.com/auth/cloud-platform"; }
    BASE="https://$GE_HOST/v1alpha/projects/$NUM_APP/locations/$GE_LOCATION/authorizations"
    "$PY" - "$BASE/$ID" "$CLIENT" "$S" "$(cut -d, -f1 <<<"$ALLOWED_DOMAINS")" <<'PY' |
import json, sys, urllib.parse
nom, client, scopes, hd = sys.argv[1].split("/v1alpha/")[1], sys.argv[2], sys.argv[3], sys.argv[4]
c = json.load(open(client)); c = c.get("web") or c.get("installed") or c
url = c["auth_uri"] + "?" + urllib.parse.urlencode({"client_id": c["client_id"], "scope": scopes, "hd": hd,
      "redirect_uri": "https://vertexaisearch.cloud.google.com/static/oauth/oauth.html", "include_granted_scopes": "true",
      "response_type": "code", "access_type": "offline", "prompt": "consent"})
print(json.dumps({"name": nom, "displayName": "Google Sheets", "serverSideOauth2": {
    "clientId": c["client_id"], "clientSecret": c["client_secret"], "authorizationUri": url, "tokenUri": c["token_uri"]}}))
PY
    curl -sS -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" \
      -H "X-Goog-User-Project: $PROJET_APP" "$BASE?authorizationId=$ID" -d @- \
      | "$PY" -c 'import json,sys; r=json.load(sys.stdin); sys.exit("ÉCHEC : " + r["error"]["message"]) if "error" in r else print("autorisation créée :", r.get("name", ""))'
    echo "Ajoutez l'ID client à OAUTH_CLIENT_IDS (fichier), rechargez, puis ./scripts/deployer.sh mcp (le serveur doit accepter ces jetons).";;

  ajouter-app)
    app_requise; : "${PROJET_APP:?}" "${APP_ID:?}"; MODE=${1:-a2a}
    BASE="https://$GE_HOST/v1alpha/projects/$PROJET_APP/locations/$GE_LOCATION/collections/default_collection/engines/$APP_ID/assistants/default_assistant/agents"
    H=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: $PROJET_APP")
    if [ "$MODE" = runtime ]; then NOM="Assistant Google Sheets"; R=$(runtime); : "${R:?Pas d agent Agent Runtime : ./scripts/deployer.sh agent-runtime}"; ID=$AUTH_ID_RUNTIME
    else NOM="Assistant Google Sheets (A2A)"; service_existe "$AGENT_SERVICE" || { echo "Pas d'agent A2A : ./scripts/deployer.sh agent"; exit 1; }; R=""; ID=$AUTH_ID; fi
    DEJA=$(curl -fsS "${H[@]}" "$BASE" | "$PY" -c 'import json,sys; print(next((a["name"] for a in json.load(sys.stdin).get("agents",[]) if a.get("displayName")==sys.argv[1]), ""))' "$NOM")
    [ -n "$DEJA" ] && { echo "déjà dans l'app : $NOM ($DEJA)"; exit 0; }
    "$PY" - "$NOM" "$MODE" "$R" "$AGENT_URL" "projects/$NUM_APP/locations/$GE_LOCATION/authorizations/$ID" <<'PY' |
import json, sys
sys.path.insert(0, "agent")
from carte import carte, DESCRIPTION, COMPETENCES
nom, mode, runtime, url, auth = sys.argv[1:6]
corps = {"displayName": nom, "description": DESCRIPTION, "languageCode": "fr",
         "starterPrompts": [{"text": e} for c in COMPETENCES for e in c["examples"]]}
if mode == "runtime":
    corps |= {"adkAgentDefinition": {"provisionedReasoningEngine": {"reasoningEngine": runtime}},
              "authorizationConfig": {"toolAuthorizations": [auth]}}
else:
    corps |= {"a2aAgentDefinition": {"jsonAgentCard": json.dumps(carte(url), ensure_ascii=False)},
              "authorizationConfig": {"agentAuthorization": auth}}
print(json.dumps(corps, ensure_ascii=False))
PY
    curl -fsS -X POST "${H[@]}" "$BASE" -d @- | "$PY" -c 'import json,sys; print("ajouté :", json.load(sys.stdin)["name"])'
    echo "Puis : l'agent → User permissions → Agent User pour votre groupe (console, docs/10-6).";;

  tester)
    : "${USER_TOKEN:?Il faut un jeton utilisateur (portée spreadsheets et/ou presentations) : docs/10-8, partie 2}"
    [ -n "${SPREADSHEET_ID:-}${PRESENTATION_ID:-}" ] || { echo "Donnez SPREADSHEET_ID (test Sheets) et/ou PRESENTATION_ID (test Slides)"; exit 1; }
    echo "== 1. Sans aucun jeton : Cloud Run doit refuser (403)"
    for U in $(service_existe "$MCP_SERVICE" && echo "$MCP_URL") $(service_existe "$SLIDES_SERVICE" && echo "$SLIDES_URL"); do
      C=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$U" -H 'Content-Type: application/json' -d '{}'); echo "   $C  $U"; [ "$C" = 403 ] || echo "   !! attendu 403"
    done
    ID_TOKEN=$(gcloud auth print-identity-token)
    echo "== 2. Le serveur MCP Sheets, comme le connecteur de Gemini Enterprise (2 en-têtes), les 17 outils sur le vrai classeur"
    if [ -n "${SPREADSHEET_ID:-}" ] && service_existe "$MCP_SERVICE"; then
      MCP_URL=$MCP_URL ID_TOKEN=$ID_TOKEN lancer "$PY" tests/test_reel.py
    else echo "   (sauté : SPREADSHEET_ID vide, ou sheets-mcp pas déployé)"; fi
    if [ -n "${PRESENTATION_ID:-}" ] && service_existe "$SLIDES_SERVICE"; then
      echo "== 2 bis. Le serveur MCP Slides, comme le connecteur, les 20 outils sur la vraie présentation"
      MCP_URL=$SLIDES_URL ID_TOKEN=$ID_TOKEN lancer "$PY" tests/test_reel_slides.py
    fi
    if service_existe "$AGENT_SERVICE" && [ -n "${SPREADSHEET_ID:-}" ]; then
      echo "== 3. L'agent A2A, comme Gemini Enterprise (jeton de l'utilisateur dans Authorization)"
      AGENT_URL=$AGENT_URL ID_TOKEN=$ID_TOKEN QUESTION="Dans le classeur $SPREADSHEET_ID, liste les onglets puis donne les 3 premières lignes du premier." lancer "$PY" tests/appel_a2a.py
    fi
    R=$(runtime 2>/dev/null || true)
    if [ -n "$R" ] && [ -n "${SPREADSHEET_ID:-}" ]; then
      echo "== 4. L'agent Agent Runtime, comme Gemini Enterprise (jeton dans « authorizations »)"
      lancer "$PY" tests/appel_runtime.py "$R" "$AUTH_ID_RUNTIME" "Dans le classeur $SPREADSHEET_ID, donne les 3 premières lignes du premier onglet."
    fi;;

  nettoyer)
    R=$(runtime 2>/dev/null || true)
    echo "Inventaire (projet $PROJET) :"
    for s in "$MCP_SERVICE" "$SLIDES_SERVICE" "$AGENT_SERVICE"; do service_existe "$s" && echo "  Cloud Run      $s"; done
    [ -n "$R" ] && echo "  Agent Runtime  $R"
    for s in "$MCP_SERVICE" "$SLIDES_SERVICE"; do existe gcloud agent-registry services describe "$s" --location="$REGISTRE_LOCATION" --project="$PROJET" && echo "  Agent Registry $s"; done
    for c in sheets-mcp-sa sheets-agent-sa sheets-build-sa; do existe gcloud iam service-accounts describe "$c@$PROJET.iam.gserviceaccount.com" --project="$PROJET" && echo "  Compte         $c"; done
    existe gcloud artifacts repositories describe sheets-mcp --location="$REGION" --project="$PROJET" && echo "  Images         dépôt Artifact Registry sheets-mcp"
    echo "(Les agents ajoutés dans l'app et le connecteur MCP se retirent dans la console de l'app : docs/10-9.)"
    confirmer "Tout supprimer ?"
    for s in "$MCP_SERVICE" "$SLIDES_SERVICE" "$AGENT_SERVICE"; do service_existe "$s" && lancer gcloud run services delete "$s" --region="$REGION" --project="$PROJET" --quiet; done
    [ -n "$R" ] && lancer "$PY" scripts/deployer_agent_runtime.py --projet "$PROJET" --region "$REGION" --supprimer "$R"
    for s in "$MCP_SERVICE" "$SLIDES_SERVICE"; do
      existe gcloud agent-registry services describe "$s" --location="$REGISTRE_LOCATION" --project="$PROJET" \
        && lancer gcloud agent-registry services delete "$s" --location="$REGISTRE_LOCATION" --project="$PROJET" --quiet
    done
    for sa_roles in "$AGENT_SA:aiplatform.user logging.logWriter" "$BUILD_SA:storage.objectViewer artifactregistry.writer logging.logWriter"; do
      for r in ${sa_roles#*:}; do gcloud projects remove-iam-policy-binding "$PROJET" --member="serviceAccount:${sa_roles%%:*}" \
        --role="roles/$r" --condition=None >/dev/null 2>&1 && echo "  retiré : roles/$r de ${sa_roles%%:*}"; done
    done
    [ -n "$GE_SA" ] && gcloud projects remove-iam-policy-binding "$PROJET" --member="serviceAccount:$GE_SA" \
      --role=roles/discoveryengine.serviceAgent --condition=None >/dev/null 2>&1 && echo "  retiré : droit ② du compte de l'app"
    for c in sheets-mcp-sa sheets-agent-sa sheets-build-sa; do
      existe gcloud iam service-accounts describe "$c@$PROJET.iam.gserviceaccount.com" --project="$PROJET" \
        && lancer gcloud iam service-accounts delete "$c@$PROJET.iam.gserviceaccount.com" --project="$PROJET" --quiet
    done
    existe gcloud artifacts repositories describe sheets-mcp --location="$REGION" --project="$PROJET" \
      && lancer gcloud artifacts repositories delete sheets-mcp --location="$REGION" --project="$PROJET" --quiet
    echo "Terminé.";;

  *) sed -n '2,22p' "$0"; exit 2;;
esac
