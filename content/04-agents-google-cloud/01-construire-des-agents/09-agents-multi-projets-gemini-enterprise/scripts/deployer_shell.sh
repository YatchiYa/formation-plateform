#!/usr/bin/env bash
# Méthode shell (docs/12-1-1) : déployer les agents SANS rien taper à la main.
# Tout vient du fichier de configuration chargé (source scripts/config.sh config/<fichier>.env) ;
# les agents : la ligne AGENTS du fichier (vide = tous), ou les clés données après l'action.
#
# À QUOI SERT CE SCRIPT
#   Fait, une commande par étape, ce que docs/12-1-1 parties 6 à 9 font à la main : filtres Model Armor, dépôt
#   d'images, comptes de service et rôles, services Cloud Run (A2A), agents Agent Runtime, entrées Agent Registry,
#   puis les tests. Il n'ajoute PAS les agents à l'app Gemini Enterprise (voir add_agent_to_ge.sh).
#
# QUAND L'UTILISER, ET QUI
#   docs/12-1-1 « Deux façons de faire les parties 6 à 9 », façon 1 (aussi docs/12-1 et 12-2, méthode A).
#   Par l'équipe qui déploie les agents, dans le projet des agents (PROJET_AGENTS).
#
# PRÉREQUIS
#   - source scripts/config.sh config/<fichier>.env -> lit PROJET_AGENTS NUM_AGENTS REGION GE_LOCATION AGENTS_LISTE
#     PROMPT_TEMPLATE RESPONSE_TEMPLATE (et le point d'accès Model Armor régional).
#   - API actives (docs/12-1-1 partie 5, scripts/verifier_api.sh) ; vos rôles : docs/12-1-1 partie 4.
#   - gcloud connecté (gcloud auth login + gcloud auth application-default login), curl, python (environnement
#     Python du projet, pour deployer_agent_runtime.py et query.py).
#
# UTILISATION
#   ./scripts/deployer_shell.sh preparer               # une fois : filtres Model Armor, dépôt d'images, compte de construction
#   ./scripts/deployer_shell.sh cloudrun               # agents de AGENTS : image (Cloud Build), compte, service Cloud Run
#   ./scripts/deployer_shell.sh cloudrun taille        # seulement taille
#   ./scripts/deployer_shell.sh runtime  [clés…]       # Agent Runtime
#   ./scripts/deployer_shell.sh registre [clés…]       # déclarer les agents Cloud Run dans Agent Registry
#   ./scripts/deployer_shell.sh tester   [clés…]       # tester ce qui est déployé (Cloud Run et Agent Runtime)
#   ./scripts/deployer_shell.sh oauth    [clés…]       # agents OAuth : activer leurs API Google, afficher portées et étapes
#   ./scripts/deployer_shell.sh carte    [clés…]       # TOUT ce qu'il faut coller dans Gemini Enterprise (carte, chemin…)
#   CLIENT_ID=<ID client OAuth> ./scripts/deployer_shell.sh carte courriels   # + l'URL d'autorisation complète
#   ./scripts/deployer_shell.sh                        # sans action (ou « aide ») : affiche cette aide
#   Clés = celles de agents/trio/catalogue.json, ex. « runtime meteo taille ». Ordre conseillé : preparer,
#   cloudrun, runtime, registre, puis tester 3 à 5 minutes après.
#
# Chaque commande est affichée (▶) avant d'être lancée. Relancer est sans danger : ce qui existe déjà est gardé
# (sauf « cloudrun », qui reconstruit l'image et redéploie le service : c'est voulu).
# Supprimer : python scripts/nettoyer.py (--agent <clé>) --supprimer
#
# CE QU'IL CRÉE (tout dans PROJET_AGENTS)
#   preparer : templates Model Armor agents-prompt-shield et agents-response-shield (localisation GE_LOCATION),
#              dépôt Docker agents-shell (REGION), compte agents-build-sa + rôles storage.objectViewer,
#              artifactregistry.writer, logging.logWriter.
#   cloudrun : par agent K : image REGION-docker.pkg.dev/PROJET_AGENTS/agents-shell/K:v1 (Cloud Build), compte
#              K-a2a-shell-sa + rôles aiplatform.user, logging.logWriter, modelarmor.user, service Cloud Run PRIVÉ
#              K-a2a-shell. Fichier local : env-K.yaml. Relancé : l'image est reconstruite et le service
#              redéployé (nouvelle révision, même adresse) ; comptes et rôles déjà là sont gardés.
#   runtime  : par agent K : compte K-shell-sa + mêmes 3 rôles, agent Agent Runtime nommé K-shell (sauté s'il existe).
#   registre : par agent K : entrée Agent Registry K-a2a-shell (sautée si elle existe). Fichier local : carte-K.json.
#   oauth    : active les API Google de l'agent (catalogue, « oauth.apis ») dans PROJET_AGENTS (projet du client OAuth).
#   carte    : fichier local carte-K.json (agents Cloud Run) ; affiche la fiche (scripts/fiche_ge.py). Ne crée rien chez Google.
#   tester   : ne crée rien (envoie des questions aux agents ; Agent Runtime garde une session de test).
#   Ne supprime jamais rien. Pour supprimer : python scripts/nettoyer.py (voir plus haut).
#
# RÉSULTAT ATTENDU (extraits réels, docs/12-1-1)
#   == taille (Cloud Run)   image europe-west1-docker.pkg.dev/<PROJET>/agents-shell/taille:v1   adresse https://taille-a2a-shell-<NUM>.europe-west1.run.app
#   ▶ gcloud builds submit …            puis  … SUCCESS
#     taille-a2a-shell-sa : roles/aiplatform.user
#   Service URL: https://taille-a2a-shell-<NUM>.europe-west1.run.app
#   Relancé : « compte … : existe déjà », « déjà déployé », « déjà déclaré ».
#   tester : « OK : les agents répondent en A2A v0.3, avec mémoire de conversation » (Cloud Run), puis la réponse
#            de l'agent Agent Runtime.
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « PROJET_AGENTS: Chargez la configuration d abord … » -> source scripts/config.sh … dans ce terminal.
#   « AGENTS_LISTE: unbound variable »   -> idem (config.sh pas chargé).
#   PERMISSION_DENIED à gcloud builds submit -> droits tout neufs : le script réessaie 3 fois (40 s d'écart).
#   « ÉCHEC de la construction de K »    -> 🔎 « Cloud Build » → Historique → la construction → journal.
#   « does not have storage.objects.get access » -> « preparer » pas fait (compte agents-build-sa ou ses rôles).
#   « ÉCHEC : réponse bloquée par Model Armor » (tester) -> rôles des nouveaux comptes pas encore actifs : 2 à 5 min.
#   « ÉCHEC : 403 » (tester, Cloud Run)  -> votre compte n'a pas roles/run.invoker sur le service.
#   « Error code 13 » (Agent Runtime)    -> erreur interne de Google : relancer.
#   « déjà déployé : … » (runtime)       -> nouvelle version : supprimer d'abord (commande affichée), puis relancer.
set -euo pipefail
: "${PROJET_AGENTS:?Chargez la configuration d abord : source scripts/config.sh config/<fichier>.env}"
# Se placer à la racine du projet : les chemins (agents/, 01-bis-…, scripts/) sont relatifs à elle.
cd "$(dirname "$0")/.."
ACTION=${1:-aide}; [ $# -gt 0 ] && shift
# Les agents à traiter : les clés données après l'action, sinon AGENTS_LISTE (calculée par config.sh).
CLES=${*:-$AGENTS_LISTE}
BUILD_SA=agents-build-sa@$PROJET_AGENTS.iam.gserviceaccount.com
PY=$(command -v python || command -v python3)

# Petits outils :
#   lancer : affiche « ▶ commande » puis la lance (pour voir exactement ce qui est fait).
#   existe : vrai si la commande (souvent un « describe ») réussit ; sert à ne pas recréer ce qui existe.
#   roles  : add-iam-policy-binding est sans effet si le rôle est déjà là, donc relançable ;
#            --condition=None évite la question interactive de gcloud si le projet a des rôles avec condition.
lancer() { echo "▶ $*" >&2; "$@"; }   # affiche (sur stderr : jamais mélangé à une sortie redirigée), puis lance
existe() { "$@" >/dev/null 2>&1; }
roles() {  # roles <compte> <rôle…> : donne les rôles sur le projet (sans effet s'ils y sont déjà)
  # Un compte tout juste créé est refusé quelques secondes (« Service account … does not exist ») : on réessaie
  # chaque rôle jusqu'à 6 fois, 10 s d'écart, et on s'arrête net si le rôle n'a toujours pas pu être donné.
  local sa=$1 essai; shift
  for r in "$@"; do
    for essai in 1 2 3 4 5 6; do
      if gcloud projects add-iam-policy-binding "$PROJET_AGENTS" --condition=None --role="roles/$r" \
           --member="serviceAccount:$sa" >/dev/null 2>&1; then echo "  ${sa%%@*} : roles/$r"; break; fi
      [ $essai = 6 ] && { echo "ÉCHEC : impossible de donner roles/$r à $sa (droits ? relancez la même commande)"; exit 1; }
      echo "  ${sa%%@*} : compte pas encore visible pour IAM, nouvel essai dans 10 s…"; sleep 10
    done
  done
}
compte() {  # compte <nom> <description> : crée le compte de service s'il n'existe pas
  if existe gcloud iam service-accounts describe "$1@$PROJET_AGENTS.iam.gserviceaccount.com" --project="$PROJET_AGENTS"; then
    echo "  compte $1 : existe déjà"
  else
    lancer gcloud iam service-accounts create "$1" --project="$PROJET_AGENTS" --display-name="$2"
  fi
}
# cle <clé agent> <champ> : lit un champ (nom_affiche, description…) de l'agent dans agents/trio/catalogue.json.
# auth_id <clé> : l'ID d'autorisation OAuth de l'agent, lu dans AGENTS_OAUTH="clé=ID …" (vide si aucun) (docs/12-1-7).
auth_id() { local x; for x in ${AGENTS_OAUTH:-}; do [ "${x%%=*}" = "$1" ] && echo "${x#*=}"; done; return 0; }
cle() { $PY -c "import json,sys; print(json.load(open('agents/trio/catalogue.json'))[sys.argv[1]][sys.argv[2]])" "$1" "$2"; }
# moteur : liste les agents Agent Runtime de la région par l'API REST de Vertex AI (reasoningEngines) et renvoie
# celui dont le nom affiché correspond ; sert à savoir s'il est déjà déployé et à le tester.
moteur() {  # moteur <nom affiché> : nom de ressource de l'agent Agent Runtime, vide s'il n'existe pas
  curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    "https://$REGION-aiplatform.googleapis.com/v1/projects/$PROJET_AGENTS/locations/$REGION/reasoningEngines" \
    | $PY -c "import json,sys; print(next((e['name'] for e in json.load(sys.stdin).get('reasoningEngines',[]) if e['displayName']==sys.argv[1]), ''))" "$1"
}

case "$ACTION" in
  # preparer : ce qui est commun à tous les agents, créé une fois (chaque élément est sauté s'il existe déjà).
  # Model Armor : filtres injection de prompt / jailbreak, URL malveillantes, données sensibles (basic config) et
  # 4 catégories RAI au niveau « moyen et plus » ; deux templates, un pour les questions, un pour les réponses.
  # Compte de construction : Cloud Build construit avec CE compte (--service-account), qui a juste les droits utiles.
  preparer)
    for T in prompt response; do
      if existe gcloud model-armor templates describe "agents-$T-shield" --location="$GE_LOCATION" --project="$PROJET_AGENTS"; then
        echo "  filtre agents-$T-shield : existe déjà"
      else
        lancer gcloud model-armor templates create "agents-$T-shield" --location="$GE_LOCATION" --project="$PROJET_AGENTS" \
          --pi-and-jailbreak-filter-settings-enforcement=enabled --pi-and-jailbreak-filter-settings-confidence-level=medium-and-above \
          --malicious-uri-filter-settings-enforcement=enabled --basic-config-filter-enforcement=enabled \
          --rai-settings-filters='[{"filterType":"HATE_SPEECH","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"HARASSMENT","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"SEXUALLY_EXPLICIT","confidenceLevel":"MEDIUM_AND_ABOVE"},{"filterType":"DANGEROUS","confidenceLevel":"MEDIUM_AND_ABOVE"}]' \
          --template-metadata-log-operations
      fi
    done
    if existe gcloud artifacts repositories describe agents-shell --location="$REGION" --project="$PROJET_AGENTS"; then
      echo "  dépôt agents-shell : existe déjà"
    else
      lancer gcloud artifacts repositories create agents-shell --repository-format=docker --location="$REGION" --project="$PROJET_AGENTS"
    fi
    compte agents-build-sa "Construction des images des agents (Cloud Build)"
    roles "$BUILD_SA" storage.objectViewer artifactregistry.writer logging.logWriter
    echo "Prêt. Attendez 1 à 2 minutes (droits du compte de construction), puis : ./scripts/deployer_shell.sh cloudrun";;

  # cloudrun : pour chaque agent, 3 étapes. L'adresse du service se calcule d'avance (nom-NUMÉRO.REGION.run.app) :
  # elle est mise dans la carte de l'agent (env-K.yaml, écrit par carte_a2a.py) AVANT le déploiement.
  # Service privé (--no-allow-unauthenticated) : seuls les comptes avec roles/run.invoker peuvent l'appeler.
  cloudrun)
    for K in $CLES; do
      IMAGE=$REGION-docker.pkg.dev/$PROJET_AGENTS/agents-shell/$K:v1
      SA=$K-a2a-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
      URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app
      echo; echo "== $K (Cloud Run)   image $IMAGE   adresse $URL"
      echo "-- 1/3 l'image, construite par Cloud Build (environ 1 min 20 s)"
      for essai in 1 2 3; do   # un compte de construction tout neuf peut être refusé 1 à 2 minutes
        lancer gcloud builds submit --region="$REGION" --project="$PROJET_AGENTS" \
          --service-account="projects/$PROJET_AGENTS/serviceAccounts/$BUILD_SA" \
          --config=01-bis-cloud-run-a2a/cloudbuild.yaml --substitutions="_AGENT_DIR=${K}_agent,_IMAGE=$IMAGE" . && break
        [ $essai = 3 ] && { echo "ÉCHEC de la construction de $K : voir 🔎 « Cloud Build » → Historique"; exit 1; }
        echo "  nouvel essai dans 40 s (droits en cours d'activation)"; sleep 40
      done
      echo "-- 2/3 son compte de service et ses 3 rôles (Gemini, journaux, Model Armor)"
      compte "$K-a2a-shell-sa" "Agent $K (Cloud Run A2A, méthode shell)"
      roles "$SA" aiplatform.user logging.logWriter modelarmor.user
      echo "-- 3/3 le service Cloud Run (privé)"
      # Agent avec autorisation OAuth (AGENTS_OAUTH) : AUTH_ID et GE_ENGINE ajoutés à ses variables (carte_a2a.py).
      AUTH_ID=$(auth_id "$K") lancer "$PY" scripts/carte_a2a.py "$K" "$URL" --env-yaml > "env-$K.yaml"
      [ -n "$(auth_id "$K")" ] && echo "  autorisation OAuth : AUTH_ID=$(auth_id "$K")"
      lancer gcloud run deploy "$K-a2a-shell" --image="$IMAGE" --region="$REGION" --project="$PROJET_AGENTS" \
        --service-account="$SA" --no-allow-unauthenticated --env-vars-file="env-$K.yaml" \
        --memory=1Gi --cpu=1 --min-instances=0 --max-instances=1 --quiet
    done
    echo; echo "Attendez 3 à 5 minutes (droits des nouveaux comptes), puis : ./scripts/deployer_shell.sh tester $CLES";;

  # runtime : compte + rôles, puis déploiement par scripts/deployer_agent_runtime.py, avec les chemins des
  # templates Model Armor en variables d'environnement. Un agent déjà déployé n'est pas remplacé (pas de mise à jour).
  runtime)
    for K in $CLES; do
      SA=$K-shell-sa@$PROJET_AGENTS.iam.gserviceaccount.com
      echo; echo "== $K (Agent Runtime, nom $K-shell)"
      compte "$K-shell-sa" "Agent $K (Agent Runtime, méthode shell)"
      roles "$SA" aiplatform.user logging.logWriter modelarmor.user
      R=$(moteur "$K-shell")
      if [ -n "$R" ]; then
        echo "  déjà déployé : $R (nouvelle version : le supprimer d'abord, python scripts/nettoyer.py --agent $K --types runtime --supprimer)"
        continue
      fi
      A=$(auth_id "$K")   # autorisation OAuth de l'agent (AGENTS_OAUTH), vide sinon
      [ -n "$A" ] && echo "  autorisation OAuth : AUTH_ID=$A"
      lancer "$PY" scripts/deployer_agent_runtime.py --projet "$PROJET_AGENTS" --region "$REGION" --agent "${K}_agent" --nom "$K-shell" \
        --description "$(cle "$K" description)" --compte-service "$SA" \
        --env "PROMPT_TEMPLATE=$PROMPT_TEMPLATE" --env "RESPONSE_TEMPLATE=$RESPONSE_TEMPLATE" \
        ${A:+--env "AUTH_ID=$A" --env "GE_ENGINE=$TF_VAR_ge_engine"}
    done
    echo; echo "Attendez 3 à 5 minutes, puis : ./scripts/deployer_shell.sh tester $CLES";;

  # registre : déclare chaque service Cloud Run dans Agent Registry avec sa carte A2A (écrite dans carte-K.json),
  # puis affiche la liste des agents du registre.
  registre)
    for K in $CLES; do
      echo; echo "== $K (Agent Registry, entrée $K-a2a-shell)"
      if existe gcloud agent-registry services describe "$K-a2a-shell" --location="$REGION" --project="$PROJET_AGENTS"; then
        echo "  déjà déclaré"; continue
      fi
      "$PY" scripts/carte_a2a.py "$K" "https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app" > "carte-$K.json"
      lancer gcloud agent-registry services create "$K-a2a-shell" --location="$REGION" --project="$PROJET_AGENTS" \
        --display-name="$(cle "$K" nom_affiche)" --description="$(cle "$K" description)" \
        --agent-spec-type=A2A_AGENT_CARD --agent-spec-content="$(cat "carte-$K.json")"
    done
    echo; lancer gcloud agent-registry agents list --location="$REGION" --project="$PROJET_AGENTS" --format="table(displayName,agentId)";;

  # tester : teste seulement ce qui existe. Cloud Run : 01-bis-cloud-run-a2a/test.sh ; Agent Runtime :
  # scripts/query.py avec la 1re question d'exemple du catalogue. « || true » : un test raté n'arrête pas les autres.
  tester)
    for K in $CLES; do
      if existe gcloud run services describe "$K-a2a-shell" --region="$REGION" --project="$PROJET_AGENTS"; then
        echo; echo "== $K, Cloud Run"
        URL="https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app" lancer ./01-bis-cloud-run-a2a/test.sh "$K" || true
      fi
      R=$(moteur "$K-shell")
      if [ -n "$R" ]; then
        echo; echo "== $K, Agent Runtime ($R)"
        Q=$($PY -c "import json,sys; a=json.load(open('agents/trio/catalogue.json'))[sys.argv[1]]; print(next((e for c in a['competences'] for e in c.get('examples',[])), 'Que sais-tu faire ?'))" "$K")
        AGENT_NAME=$R lancer "$PY" scripts/query.py - "$Q" || true
      fi
    done;;

  # oauth : agents qui agissent avec le compte de l'utilisateur (docs/12-1-8). Le client OAuth lui-même ne se crée
  # PAS en ligne de commande (Google ne publie pas d'API pour cela) : console, lien affiché. Tout le reste est fait ici.
  oauth)
    for K in $CLES; do
      echo; echo "== $K"
      APIS=$($PY -c "import json,sys; print(' '.join(json.load(open('agents/trio/catalogue.json'))[sys.argv[1]].get('oauth',{}).get('apis',[])))" "$K")
      PORTEES=$($PY -c "import json,sys; print(' '.join(json.load(open('agents/trio/catalogue.json'))[sys.argv[1]].get('oauth',{}).get('portees',[])))" "$K")
      [ -z "$PORTEES" ] && { echo "  pas d'OAuth pour cet agent (pas de « oauth » dans le catalogue)"; continue; }
      [ -n "$APIS" ] && lancer gcloud services enable $APIS --project="$PROJET_AGENTS"
      echo "  portées (A2A)           : $PORTEES"
      echo "  portées (Agent Runtime) : $PORTEES https://www.googleapis.com/auth/cloud-platform"
      A=$(auth_id "$K")
      echo "  AGENTS_OAUTH            : ${A:-(aucune : mettre AGENTS_OAUTH=\"$K=acces-$K\" devant cloudrun / runtime / carte)}"
    done
    echo
    echo "Client OAuth (une fois, console, 2 min) : https://console.cloud.google.com/auth/clients?project=$PROJET_AGENTS"
    echo "  Audience Interne ; + Créer un client → Application Web ; URI de redirection autorisés :"
    echo "    https://vertexaisearch.cloud.google.com/oauth-redirect"
    echo "    https://vertexaisearch.cloud.google.com/static/oauth/oauth.html"
    echo "  → noter l'ID client et le secret (jamais dans le dépôt). Puis : CLIENT_ID=<ID> ./scripts/deployer_shell.sh carte $CLES";;

  # carte : la fiche de chaque agent pour la console Gemini Enterprise. Seulement ce qui est DÉPLOYÉ :
  # Cloud Run -> carte-K.json (scripts/carte_a2a.py, le format Google) ; Agent Runtime -> son chemin de ressource.
  carte)
    for K in $CLES; do
      URL=https://$K-a2a-shell-$NUM_AGENTS.$REGION.run.app; ARGS=()
      if existe gcloud run services describe "$K-a2a-shell" --region="$REGION" --project="$PROJET_AGENTS"; then
        "$PY" scripts/carte_a2a.py "$K" "$URL" > "carte-$K.json"; ARGS+=(--a2a "$URL" --carte "carte-$K.json")
      fi
      R=$(moteur "$K-shell"); [ -n "$R" ] && ARGS+=(--runtime "$R")
      "$PY" scripts/fiche_ge.py "$K" ${ARGS[@]+"${ARGS[@]}"} --auth "$(auth_id "$K")"
    done;;

  # Sans action reconnue : affiche l'en-tête, du titre jusqu'à la fin de « UTILISATION ».
  *) sed -n '2,38p' "$0"; exit 2;;
esac
