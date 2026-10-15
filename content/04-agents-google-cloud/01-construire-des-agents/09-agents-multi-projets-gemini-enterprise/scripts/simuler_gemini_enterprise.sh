#!/usr/bin/env bash
# Simuler l'appel de Gemini Enterprise vers un agent, AVANT de l'ajouter à l'app.
#
# À QUOI SERT CE SCRIPT
# Gemini Enterprise appelle les agents avec le compte de service de SON projet
# (service-NUM@gcp-sa-discoveryengine…), qu'on ne peut pas emprunter. Le simulateur est un compte de service
# « ge-simulateur » créé dans le projet de l'app, à qui l'équipe de l'agent donne EXACTEMENT les mêmes droits.
# S'il passe, Gemini Enterprise passera ; s'il est refusé (403), le droit manque.
#
# QUAND L'UTILISER, ET QUI
#   docs/09, partie 3 : étape 1 (preparer, par l'admin Gemini Enterprise, une fois) et étape 4 (a2a / runtime, par
#   l'équipe de l'agent, pour prouver que son agent est joignable avant la demande d'ajout).
#
# PRÉREQUIS
#   - GE_PROJECT = ID du projet de l'app. « source scripts/config.sh … » le remplit (GE_PROJECT=PROJET_APP),
#     sinon : export GE_PROJECT=… . gcloud connecté, python3.
#   - preparer : pouvoir créer un compte de service dans le projet de l'app et modifier son IAM.
#   - a2a / runtime : avoir roles/iam.serviceAccountTokenCreator sur ge-simulateur (preparer le donne à l'admin ;
#     l'admin le donne aux équipes, docs/09 étape 1), et que l'équipe ait donné au simulateur les mêmes droits
#     qu'à Gemini Enterprise : roles/run.invoker sur le service Cloud Run, ou roles/discoveryengine.serviceAgent
#     sur le projet de l'agent Agent Runtime (docs/09 étape 4b).
#
# UTILISATION
#   export GE_PROJECT=acme-ge-demo                     # projet de l'app Gemini Enterprise
#   ./simuler_gemini_enterprise.sh preparer                 # admin GE, une fois : crée le simulateur
#   ./simuler_gemini_enterprise.sh a2a URL_SERVICE "question"            # agent Cloud Run (A2A v0.3)
#   ./simuler_gemini_enterprise.sh runtime projects/P/locations/R/reasoningEngines/ID "question"   # Agent Runtime
#   ex. ./scripts/simuler_gemini_enterprise.sh a2a https://meteo-a2a-shell-<NUM>.europe-west1.run.app "Bonjour"
#   La question est facultative (par défaut : « Bonjour, que sais-tu faire ? »).
#   Avec la configuration chargée (source scripts/config.sh …), pour TOUS les agents de AGENTS (docs/12-1-5) :
#   ./scripts/simuler_gemini_enterprise.sh droits         # donner au simulateur les droits de Gemini Enterprise
#   ./scripts/simuler_gemini_enterprise.sh tout           # appeler chaque agent (Cloud Run et Agent Runtime) : bilan
#   ./scripts/simuler_gemini_enterprise.sh retirer-droits # retirer ces droits au simulateur (fin de test)
#   ./scripts/simuler_gemini_enterprise.sh oauth identite [--sans-jeton]   # agent OAuth : avec / sans jeton utilisateur
#   … taille --methode console                             # un agent précis ; agents déployés par la console
#
# Droits à donner au simulateur (par l'équipe de l'agent, comme pour Gemini Enterprise) : docs/09, étape 4.
#
# CE QU'IL LIT / CE QU'IL CRÉE OU MODIFIE
#   preparer : crée le compte ge-simulateur@GE_PROJECT.iam.gserviceaccount.com s'il n'existe pas, et vous donne
#              (votre compte gcloud) roles/iam.serviceAccountTokenCreator dessus. Idempotent.
#   a2a      : envoie une question à l'agent ; ne crée rien.
#   runtime  : envoie une question ; crée une session de conversation dans l'agent (visible dans ses Sessions).
#   Ne pose AUCUN droit sur l'agent (c'est le test). Retirer les droits du simulateur après : docs/09 étape 4d.
#   droits / retirer-droits : PROJET DES AGENTS seulement : roles/discoveryengine.serviceAgent sur le projet et
#              roles/run.invoker sur chaque service Cloud Run, pour ge-simulateur (jamais pour le vrai compte de l'app).
#   tout     : comme a2a + runtime, pour chaque agent ; ne crée qu'une session de test par agent Agent Runtime.
#
# RÉSULTAT ATTENDU
#   preparer : « simulateur prêt : ge-simulateur@<projet>.iam.gserviceaccount.com »
#   sans droit (4a)   : « REFUSÉ (403) : le compte de Gemini Enterprise n'a pas … »   (normal : service privé)
#   avec droit (4c)   : « ACCEPTÉ (A2A v0.3) : <réponse> » ou « ACCEPTÉ (Agent Runtime) : <réponse> »
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « GE_PROJECT: export GE_PROJECT=… »  -> donner le projet de l'app.
#   Arrêt sans aucun message (a2a / runtime) -> le jeton du simulateur n'a pas pu être créé : rôle « Créateur de
#                                           jetons » manquant, ou simulateur créé il y a moins de 1 à 2 minutes.
#   « REFUSÉ (403) » juste après avoir donné le droit -> propagation IAM : attendre 2 à 3 minutes et relancer ;
#                                           sinon droit posé sur le mauvais projet / service.
#   « ERREUR <code> : … »                -> autre erreur HTTP (adresse ou nom de ressource faux…) : lire le message.
set -euo pipefail
: "${GE_PROJECT:?export GE_PROJECT=projet-de-votre-app-Gemini-Enterprise}"
SIMU="ge-simulateur@$GE_PROJECT.iam.gserviceaccount.com"

# appel_a2a : envoie un message A2A v0.3 (JSON-RPC « message/send ») au service Cloud Run, exactement comme
# Gemini Enterprise : le jeton va dans X-Serverless-Authorization (Cloud Run y vérifie l'IAM, ce qui laisse
# « Authorization » libre pour le jeton OAuth de l'utilisateur). 401/403 = run.invoker manquant.
appel_a2a() {  # URL TOKEN Q dans l'environnement
python3 - <<'PY'
import json, os, sys, urllib.error, urllib.request, uuid
body = {"jsonrpc": "2.0", "id": "1", "method": "message/send", "params": {"message": {
    "kind": "message", "role": "user", "messageId": str(uuid.uuid4()), "parts": [{"kind": "text", "text": os.environ["Q"]}]}}}
req = urllib.request.Request(os.environ["URL"].rstrip("/") + "/", json.dumps(body).encode(), {
    "Content-Type": "application/json", "A2A-Version": "0.3", "X-Serverless-Authorization": "Bearer " + os.environ["TOKEN"],
    # Agent avec autorisation OAuth : Gemini Enterprise ajoute le jeton DE L'UTILISATEUR dans Authorization.
    **({"Authorization": "Bearer " + os.environ["USER_TOKEN"]} if os.environ.get("USER_TOKEN") else {})})
try:
    r = json.load(urllib.request.urlopen(req, timeout=180))["result"]
except urllib.error.HTTPError as e:
    sys.exit(f"REFUSÉ ({e.code}) : le compte de Gemini Enterprise n'a pas roles/run.invoker sur ce service." if e.code in (401, 403)
             else f"ERREUR {e.code} : {e.read()[:300]!r}")
# La réponse de l'agent : les textes de tous les « artifacts » renvoyés.
print("ACCEPTÉ (A2A v0.3) :", " ".join(p.get("text", "") for a in r.get("artifacts", []) for p in a["parts"]))
PY
}

# appel_runtime : comme Gemini Enterprise, passe par l'API Agent Runtime (Vertex AI, point d'accès de la région
# lue dans le nom de ressource) : 1) « query » create_session pour ouvrir une session ; 2) « streamQuery »
# stream_query avec la question ; la réponse arrive en plusieurs lignes JSON, dont on garde les textes.
appel_runtime() {  # NAME TOKEN Q GE_PROJECT dans l'environnement
python3 - <<'PY'
import json, os, sys, urllib.error, urllib.request
name, region = os.environ["NAME"], os.environ["NAME"].split("/")[3]
base = f"https://{region}-aiplatform.googleapis.com/v1/{name}"
H = {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]}
def post(verb, body):
    req = urllib.request.Request(f"{base}:{verb}", json.dumps(body).encode(), H)
    try:
        return urllib.request.urlopen(req, timeout=180).read().decode()
    except urllib.error.HTTPError as e:
        sys.exit(f"REFUSÉ ({e.code}) : le compte de Gemini Enterprise n'a pas roles/discoveryengine.serviceAgent sur le projet de l'agent."
                 if e.code in (401, 403) else f"ERREUR {e.code} : {e.read()[:300]!r}")
user = "simulateur@" + os.environ["GE_PROJECT"]
session = json.loads(post("query", {"classMethod": "create_session", "input": {"user_id": user}}))["output"]["id"]
texts = []
for line in post("streamQuery", {"classMethod": "stream_query", "input": {"user_id": user, "session_id": session, "message": os.environ["Q"]}}).splitlines():
    if line.strip():
        texts += [p["text"] for p in (json.loads(line).get("content") or {}).get("parts", []) if p.get("text")]
print("ACCEPTÉ (Agent Runtime) :", " ".join(texts))
PY
}

# appel_runtime_oauth : l'appel que fait Gemini Enterprise à un agent Agent Runtime qui a une autorisation OAuth :
# méthode streaming_agent_run_with_events, avec le jeton de l'utilisateur dans « authorizations » (clé = AUTH_ID).
appel_runtime_oauth() {  # NAME TOKEN Q AUTH_ID USER_TOKEN (vide = utilisateur pas encore autorisé)
python3 - <<'PY'
import json, os, sys, urllib.error, urllib.request
name = os.environ["NAME"]; region = name.split("/")[3]
req_json = {"message": {"role": "user", "parts": [{"text": os.environ["Q"]}]}, "user_id": "simulateur"}
if os.environ.get("USER_TOKEN"):
    # Plusieurs autorisations (docs/12-1-8) : le même jeton Google pour chacune (un jeton Atlassian ne se simule pas).
    req_json["authorizations"] = {i: {"access_token": os.environ["USER_TOKEN"]} for i in os.environ["AUTH_ID"].split(",")}
body = {"class_method": "streaming_agent_run_with_events", "input": {"request_json": json.dumps(req_json)}}
req = urllib.request.Request(f"https://{region}-aiplatform.googleapis.com/v1/{name}:streamQuery?alt=sse", json.dumps(body).encode(),
                             {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    lignes = urllib.request.urlopen(req, timeout=300).read().decode().splitlines()
except urllib.error.HTTPError as e:
    sys.exit(f"REFUSÉ ({e.code}) : droit discoveryengine.serviceAgent manquant ?" if e.code in (401, 403) else f"ERREUR {e.code} : {e.read()[:300]!r}")
texts = []
for l in lignes:
    l = l.strip().removeprefix("data: ")
    if not l:
        continue
    for ev in json.loads(l).get("events", [json.loads(l)]):
        texts += [p["text"] for p in (ev.get("content") or {}).get("parts", []) if p.get("text")]
print("ACCEPTÉ (Agent Runtime, OAuth) :", " ".join(texts))
PY
}

# --- Mode « configuration » (docs/12-1-5) : agents lus dans AGENTS, noms selon la méthode de déploiement. ---
ACTION=${1:-}
METHODE=shell; CLES=""
SANS_JETON=non
case "$ACTION" in droits|retirer-droits|tout|oauth)   # a2a / runtime gardent leurs arguments ($2, $3) tels quels
  : "${PROJET_AGENTS:?Chargez la configuration : source scripts/config.sh config/<fichier>.env}"
  shift
  while [ $# -gt 0 ]; do case "$1" in --methode) METHODE=$2; shift 2;; --sans-jeton) SANS_JETON=oui; shift;; *) CLES="$CLES $1"; shift;; esac; done
  CLES=${CLES:-$AGENTS_LISTE}
  cd "$(dirname "$0")/..";;
esac
service_cr() { echo "$1-a2a-$METHODE"; }                    # service Cloud Run de l'agent (12-1-1 : -shell)
url_cr() { echo "https://$(service_cr "$1")-$NUM_AGENTS.$REGION.run.app"; }
moteur() {  # nom de ressource de l'agent Agent Runtime « <clé>-<méthode> », vide s'il n'existe pas
  curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
    | python3 -c "import json,sys; print(next((e['name'] for e in json.load(sys.stdin).get('reasoningEngines',[]) if e['displayName']==sys.argv[1]), ''))" "$1-$METHODE"
}
existe_cr() { gcloud run services describe "$(service_cr "$1")" --region="$REGION" --project="$PROJET_AGENTS" >/dev/null 2>&1; }

case "$ACTION" in
  # droits / retirer-droits : les MÊMES droits que ceux du compte de l'app (docs/12-1-4), pour le simulateur.
  droits|retirer-droits)
    verbe=$([ "$ACTION" = droits ] && echo add || echo remove)
    rt=non; for K in $CLES; do [ -n "$(moteur "$K")" ] && rt=oui; done
    if [ $rt = oui ] && [ "${MEME_PROJET:-non}" = non ]; then
      echo "▶ gcloud projects $verbe-iam-policy-binding $PROJET_AGENTS --role=roles/discoveryengine.serviceAgent --member=serviceAccount:$SIMU"
      gcloud projects "$verbe-iam-policy-binding" "$PROJET_AGENTS" --condition=None --role=roles/discoveryengine.serviceAgent \
        --member="serviceAccount:$SIMU" >/dev/null 2>&1 && echo "  fait" || echo "  (rien à faire, ou refusé)"
    fi
    for K in $CLES; do existe_cr "$K" || continue
      echo "▶ gcloud run services $verbe-iam-policy-binding $(service_cr "$K") --role=roles/run.invoker --member=serviceAccount:$SIMU"
      gcloud run services "$verbe-iam-policy-binding" "$(service_cr "$K")" --region="$REGION" --project="$PROJET_AGENTS" \
        --role=roles/run.invoker --member="serviceAccount:$SIMU" >/dev/null 2>&1 && echo "  fait" || echo "  (rien à faire, ou refusé)"
    done
    [ "$ACTION" = droits ] && echo "Attendez 2 à 3 minutes (les droits s'appliquent), puis : ./scripts/simuler_gemini_enterprise.sh tout"
    exit 0;;

  # oauth : comme « tout », mais pour un agent qui a une autorisation OAuth (AGENTS_OAUTH) : envoie, en plus, le jeton
  # de l'utilisateur (ici : VOTRE jeton gcloud, comme si vous aviez cliqué « Autoriser » dans Gemini Enterprise).
  # --sans-jeton : comme un utilisateur qui n'a pas encore autorisé (l'agent doit le dire). docs/12-1-7.
  oauth)
    for K in $CLES; do
      A=""; for x in ${AGENTS_OAUTH:-}; do [ "${x%%=*}" = "$K" ] && A=${x#*=}; done
      [ -z "$A" ] && { echo "$K : pas d'autorisation dans AGENTS_OAUTH (ex. AGENTS_OAUTH=\"$K=acces-$K\"), ignoré"; continue; }
      U=$([ "$SANS_JETON" = oui ] && echo "" || gcloud auth print-access-token)
      Q="Suis-je authentifié ? Avec quel compte ?"
      if existe_cr "$K"; then
        echo; echo "== $K, Cloud Run, AUTH_ID=$A, jeton utilisateur : $([ -n "$U" ] && echo oui || echo non)"
        TOKEN=$(gcloud auth print-identity-token --impersonate-service-account="$SIMU" --audiences="$(url_cr "$K")" --include-email 2>/dev/null) \
          && URL=$(url_cr "$K") TOKEN=$TOKEN USER_TOKEN=$U Q=$Q appel_a2a || true
      fi
      R=$(moteur "$K")
      if [ -n "$R" ]; then
        echo; echo "== $K, Agent Runtime, AUTH_ID=$A, jeton utilisateur : $([ -n "$U" ] && echo oui || echo non)"
        TOKEN=$(gcloud auth print-access-token --impersonate-service-account="$SIMU" 2>/dev/null) \
          && NAME=$R TOKEN=$TOKEN Q=$Q AUTH_ID=$A USER_TOKEN=$U appel_runtime_oauth || true
      fi
    done
    exit 0;;

  # tout : appelle chaque agent déployé, comme Gemini Enterprise, et fait le bilan.
  tout)
    bilan=()
    for K in $CLES; do
      Q=$(python3 -c "import json,sys; a=json.load(open('agents/trio/catalogue.json'))[sys.argv[1]]; print(next((e for c in a['competences'] for e in c.get('examples',[])), 'Bonjour'))" "$K")
      if existe_cr "$K"; then
        echo; echo "== $K, Cloud Run $(service_cr "$K") : « $Q »"
        if TOKEN=$(gcloud auth print-identity-token --impersonate-service-account="$SIMU" --audiences="$(url_cr "$K")" --include-email 2>/dev/null) \
           && URL=$(url_cr "$K") TOKEN=$TOKEN Q=$Q appel_a2a; then bilan+=("ACCEPTÉ  $K  Cloud Run (A2A)"); else bilan+=("REFUSÉ   $K  Cloud Run (A2A)"); fi
      fi
      R=$(moteur "$K")
      if [ -n "$R" ]; then
        echo; echo "== $K, Agent Runtime $K-$METHODE : « $Q »"
        if TOKEN=$(gcloud auth print-access-token --impersonate-service-account="$SIMU" 2>/dev/null) \
           && NAME=$R TOKEN=$TOKEN Q=$Q appel_runtime; then bilan+=("ACCEPTÉ  $K  Agent Runtime"); else bilan+=("REFUSÉ   $K  Agent Runtime"); fi
      fi
    done
    [ ${#bilan[@]} = 0 ] && { echo "Aucun agent déployé (méthode $METHODE) parmi :$CLES"; exit 1; }
    echo; echo "== Bilan (compte simulateur $SIMU)"; printf '   %s\n' "${bilan[@]}"
    exit 0;;
esac


case "$ACTION" in
  # preparer : crée le compte seulement s'il n'existe pas (describe || create), puis donne à VOTRE compte gcloud le
  # droit de créer des jetons pour lui (nécessaire pour l'« emprunter » dans a2a / runtime).
  # --condition=None : évite la question interactive de gcloud si la politique a des conditions.
  preparer)
    gcloud iam service-accounts describe "$SIMU" --project="$GE_PROJECT" >/dev/null 2>&1 ||
      gcloud iam service-accounts create ge-simulateur --project="$GE_PROJECT" \
        --display-name="Simulateur Gemini Enterprise - tests d'acces aux agents"
    gcloud iam service-accounts add-iam-policy-binding "$SIMU" --project="$GE_PROJECT" --condition=None \
      --role=roles/iam.serviceAccountTokenCreator --member="user:$(gcloud config get-value account 2>/dev/null)" >/dev/null
    echo "simulateur prêt : $SIMU"
    echo "Les jetons peuvent mettre 1 à 2 minutes à fonctionner après la création.";;

  # a2a : jeton d'IDENTITÉ (OIDC) du simulateur, pour l'audience = l'adresse du service (ce que Cloud Run vérifie).
  # Si sa création échoue, le script s'arrête (set -e) sans message, l'erreur gcloud étant masquée (2>/dev/null).
  a2a)  # Comme Gemini Enterprise : jeton OIDC de son compte dans l'en-tête X-Serverless-Authorization
    URL=${2:?URL du service Cloud Run}; Q=${3:-"Bonjour, que sais-tu faire ?"}
    TOKEN=$(gcloud auth print-identity-token --impersonate-service-account="$SIMU" --audiences="$URL" --include-email 2>/dev/null)
    URL=$URL TOKEN=$TOKEN Q=$Q appel_a2a;;

  # runtime : jeton d'ACCÈS (OAuth) du simulateur, pour l'API Vertex AI. Même remarque si sa création échoue.
  runtime)  # Comme Gemini Enterprise : API Agent Runtime, jeton d'accès de son compte
    NAME=${2:?nom de ressource projects/P/locations/R/reasoningEngines/ID}; Q=${3:-"Bonjour, que sais-tu faire ?"}
    TOKEN=$(gcloud auth print-access-token --impersonate-service-account="$SIMU" 2>/dev/null)
    NAME=$NAME TOKEN=$TOKEN Q=$Q appel_runtime;;

  # Sans action reconnue : affiche l'en-tête, du titre jusqu'à la fin de « UTILISATION ».
  *) sed -n '2,37p' "$0"; exit 2;;
esac
