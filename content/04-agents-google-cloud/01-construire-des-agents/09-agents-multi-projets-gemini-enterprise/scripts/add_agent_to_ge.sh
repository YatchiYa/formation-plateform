#!/usr/bin/env bash
# Ajouter à l'app Gemini Enterprise un agent QUI EXISTE DÉJÀ, quel que soit son projet.
#
# À QUOI SERT CE SCRIPT
#   Ajoute (ou liste, ou supprime) un agent dans l'app Gemini Enterprise, comme « + Ajouter un agent » dans la
#   console : agent ADK sur Agent Runtime, ou agent A2A (Cloud Run…) décrit par sa carte. Il donne aussi au compte
#   de l'app le droit d'appeler l'agent, ou affiche la commande à transmettre à l'équipe propriétaire.
#
# QUAND L'UTILISER, ET QUI
#   L'admin Gemini Enterprise (rôle discoveryengine.admin sur le projet de l'app), une fois l'agent déployé :
#   docs/12-1 A6, docs/12-2 A3, docs/12-3 §3.6-3.8 et partie C4, docs/09 partie 2 (2.1, 2.2) et étape 6.
#
# PRÉREQUIS
#   - Variables : GE_PROJECT (ID du projet de l'app), GE_APP (ID de l'app), GE_LOCATION (eu par défaut).
#     « source scripts/config.sh config/<fichier>.env » les remplit (GE_PROJECT=PROJET_APP, GE_APP=APP_ID).
#   - gcloud connecté (gcloud auth login), curl, python3.
#   - API discoveryengine.googleapis.com active sur le projet de l'app.
#   - Pour poser le droit sur l'agent : pouvoir modifier l'IAM du projet de l'agent (Agent Runtime) ou du
#     service Cloud Run (A2A). Sinon le script affiche la commande à faire faire par l'équipe propriétaire.
#
# UTILISATION
#   export GE_PROJECT=acme-ge-recette GE_APP=acme-ge GE_LOCATION=eu   # (ou source scripts/config.sh …)
#   ./add_agent_to_ge.sh list                       # les agents de l'app : nom affiché, type, ID
#   ./add_agent_to_ge.sh adk  projects/AUTRE-PROJET/locations/europe-west1/reasoningEngines/123 "Nom" "Description"
#                                                   # agent Agent Runtime (description facultative : = Nom)
#   ./add_agent_to_ge.sh a2a  https://mon-agent-xyz.a.run.app/.well-known/agent-card.json "Nom"
#                                                   # agent A2A : carte lue sur le service (jeton d'identité envoyé)
#   ./add_agent_to_ge.sh a2a  carte-envoyee-par-l-equipe.json "Nom"      # carte reçue en fichier (service privé)
#   ./add_agent_to_ge.sh delete "Nom"               # retire l'agent de l'app (par son nom affiché exact)
#   AUTH_ID=acces-drive ./add_agent_to_ge.sh a2a …    # agent qui agit avec le compte de l'utilisateur (docs/12-3, partie C)
#     AUTH_ID : ID d'une autorisation déjà créée dans l'app (scripts/autorisation_oauth.sh list).
#
# CE QU'IL LIT / CE QU'IL CRÉE, MODIFIE OU SUPPRIME
#   list   : lecture seule.
#   adk    : crée une entrée d'agent dans l'app ; si l'agent est dans un AUTRE projet, donne au compte de l'app
#            (service-NUM_APP@gcp-sa-discoveryengine…) roles/discoveryengine.serviceAgent sur ce projet.
#   a2a    : crée une entrée d'agent dans l'app ; si l'URL de la carte est en *.run.app, donne à ce compte
#            roles/run.invoker sur le service Cloud Run trouvé.
#   delete : DESTRUCTIF, supprime l'entrée de l'app (l'agent lui-même, Cloud Run ou Agent Runtime, reste).
#   Sans doublon : adk / a2a relancés avec un nom déjà présent dans l'app ne recréent rien (« déjà dans l'app »).
#   Pour refaire une entrée (nouvelle carte, autre agent) : delete "Nom", puis adk / a2a. Les droits IAM, eux,
#   peuvent être redonnés sans effet de bord.
#   Aucun fichier local écrit.
#
# RÉSULTAT ATTENDU
#   adk / a2a : « droit accordé : --role=… --member=… » (autre projet / Cloud Run), puis
#               « ajouté : projects/…/engines/<app>/assistants/default_assistant/agents/<ID> ».
#   list      : une ligne par agent : nom affiché, adkAgentDefinition ou a2aAgentDefinition, ID.
#   adk / a2a déjà faits : « déjà dans l'app : Nom (<ID>) … ».
#   delete    : « supprimé : Nom », « introuvable : Nom », ou « ÉCHEC de la suppression : Nom ».
#   Ensuite, dans la console : donner le rôle Agent User au groupe d'utilisateurs, sur chaque agent.
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « GE_PROJECT: parameter null or not set »  -> configuration non chargée : source scripts/config.sh … (APP_ID rempli).
#   « Région … incompatible avec une app … »   -> agent à redéployer dans la bonne région (eu -> europe-*, us -> us-*).
#   « ⚠  Droit NON accordé … »                  -> pas d'accès IAM sur le projet de l'agent : envoyer la commande
#                                                 affichée à l'équipe propriétaire.
#   « curl: (22) … 403 » / PERMISSION_DENIED   -> pas Gemini Enterprise Admin (roles/discoveryengine.admin).
#   « introuvable : Nom »                      -> nom affiché différent (voir list).
#   « ÉCHEC de la suppression : Nom »          -> pas Gemini Enterprise Admin, ou erreur passagère : relancer.
#   Dans le chat « L'agent n'a pas pu répondre » -> droit run.invoker / discoveryengine.serviceAgent manquant,
#                                                 ou pas encore actif : attendre 2 à 3 minutes.
#   Agent absent du chat                       -> pas de rôle Agent User pour le groupe, ou pas de licence.
#
# Le script fait aussi le droit cross-project nécessaire (si vous avez le droit IAM sur l'autre projet),
# sinon il affiche la commande exacte à transmettre à l'équipe propriétaire de l'agent.
set -euo pipefail
: "${GE_PROJECT:?}" "${GE_APP:?}" "${GE_LOCATION:=eu}"

# Pas de commande gcloud (ni de ressource Terraform) pour les agents d'une app : on appelle l'API REST v1alpha.
# Point d'accès : régional (eu-discoveryengine…, us-…) sauf pour une app « global ».
HOST=$([ "$GE_LOCATION" = global ] && echo discoveryengine.googleapis.com || echo "$GE_LOCATION-discoveryengine.googleapis.com")
BASE="https://$HOST/v1alpha/projects/$GE_PROJECT/locations/$GE_LOCATION/collections/default_collection/engines/$GE_APP/assistants/default_assistant/agents"
# En-têtes de chaque appel : votre jeton gcloud, et X-Goog-User-Project = le projet de l'app, à qui Google
# compte l'appel (quota, facturation) : avec un jeton d'utilisateur, l'API Discovery Engine l'exige.
H=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: $GE_PROJECT")
# Le compte de service de l'app (celui qui appellera l'agent) se déduit du NUMÉRO du projet de l'app.
GE_NUMBER=$(gcloud projects describe "$GE_PROJECT" --format='value(projectNumber)')
GE_SA="serviceAccount:service-$GE_NUMBER@gcp-sa-discoveryengine.iam.gserviceaccount.com"

# grant : tente la commande gcloud ; en cas d'échec (pas le droit IAM), n'arrête pas le script mais affiche la
# commande exacte, prête à copier (printf %q met les guillemets), pour l'équipe propriétaire de l'agent.
grant() {  # grant <commande gcloud complète> : l'exécute, ou l'affiche si on n'a pas le droit
  if "$@" --quiet >/dev/null 2>&1; then echo "droit accordé : ${*: -2}"
  else echo "⚠  Droit NON accordé (pas d'accès IAM). À faire par l'équipe propriétaire :"; printf '   %q' "$@"; echo; fi
}

# Autorisation OAuth (optionnelle), ajoutée au corps JSON : A2A = une pour l'agent, Agent Runtime = une liste pour ses outils.
# avec_auth lit le corps JSON sur l'entrée standard et le réécrit, avec « authorizationConfig » si AUTH_ID est donné.
# Plusieurs fournisseurs (Agent Runtime seulement, docs/12-1-8) : AUTH_ID="acces-google,acces-atlassian".
avec_auth() { python3 -c 'import json,sys; b=json.load(sys.stdin); ids=[i for i in sys.argv[2].split(",") if i]
a=[sys.argv[1] + i for i in ids]
if len(a) > 1 and "a2aAgentDefinition" in b: sys.exit("A2A : UNE seule autorisation par agent (docs/12-1-8) ; plusieurs = Agent Runtime.")
if a: b["authorizationConfig"] = {"agentAuthorization": a[0]} if "a2aAgentDefinition" in b else {"toolAuthorizations": a}
print(json.dumps(b))' "projects/$GE_NUMBER/locations/$GE_LOCATION/authorizations/" "${AUTH_ID:-}"; }

# id_par_nom "Nom" -> nom de ressource de l'agent de l'app qui porte exactement ce nom affiché (vide sinon).
id_par_nom() { curl -fsS "${H[@]}" "$BASE" | python3 -c 'import json,sys; print(next((a["name"] for a in json.load(sys.stdin).get("agents",[]) if a.get("displayName")==sys.argv[1]), ""))' "$1"; }
# deja "Nom" : si l'app a déjà un agent de ce nom, le dit et arrête (pas de doublon).
deja() { local id; id=$(id_par_nom "$1"); [ -z "$id" ] && return 0
  echo "déjà dans l'app : $1 (${id##*/}). Pour le refaire : $0 delete \"$1\", puis relancer."; exit 0; }

case "${1:-}" in
  # list : GET sur la liste des agents ; Python affiche nom, type (…AgentDefinition) et ID (fin du nom de ressource).
  list)
    curl -fsS "${H[@]}" "$BASE" | python3 -c '
import json,sys
for a in json.load(sys.stdin).get("agents", []):
    kind = next((k for k in a if k.endswith("AgentDefinition")), "?")
    print(a.get("displayName", "").ljust(35), kind.ljust(22), a["name"].split("/")[-1])';;

  # adk : on lit projet et région dans le nom de ressource, on vérifie la région, on donne le droit si l'agent
  # est dans un autre projet (comparé à l'ID ET au numéro du projet de l'app : le nom peut contenir l'un ou l'autre),
  # puis POST du corps JSON (Python construit le JSON pour échapper correctement accents et guillemets).
  # --condition=None : évite la question interactive de gcloud quand la politique IAM du projet a des conditions.
  adk)  # Agent ADK hébergé sur Agent Runtime (ex-Agent Engine), dans n'importe quel projet
    ENGINE=${2:?resource projects/P/locations/R/reasoningEngines/ID}; NAME=${3:?nom}; DESC=${4:-$NAME}
    deja "$NAME"
    AGENT_PROJECT=$(cut -d/ -f2 <<<"$ENGINE"); REGION=$(cut -d/ -f4 <<<"$ENGINE")
    case "$GE_LOCATION:$REGION" in eu:europe-*|us:us-*|global:*) ;; *)
      echo "Région $REGION incompatible avec une app '$GE_LOCATION' (eu -> europe-*, us -> us-*)." >&2; exit 2;; esac
    if [ "$AGENT_PROJECT" != "$GE_PROJECT" ] && [ "$AGENT_PROJECT" != "$GE_NUMBER" ]; then
      grant gcloud projects add-iam-policy-binding "$AGENT_PROJECT" --condition=None \
        --role=roles/discoveryengine.serviceAgent --member="$GE_SA"
    fi
    python3 -c 'import json,sys; print(json.dumps({"displayName": sys.argv[1], "description": sys.argv[2],
      "adkAgentDefinition": {"provisionedReasoningEngine": {"reasoningEngine": sys.argv[3]}}}))' "$NAME" "$DESC" "$ENGINE" | avec_auth |
      curl -fsS -X POST "${H[@]}" "$BASE" -d @- | python3 -c 'import json,sys; print("ajouté :", json.load(sys.stdin)["name"])';;

  # a2a : 1) la carte (fichier local, ou téléchargée avec un jeton d'identité, nécessaire pour un Cloud Run privé) ;
  # 2) son champ « url » : si c'est un service Cloud Run (*.run.app), on le cherche parmi les services visibles
  #    (projet gcloud par défaut : PROJET_AGENTS si config.sh est chargé) pour donner roles/run.invoker au compte de
  #    l'app ; introuvable -> simple rappel à l'écran ; 3) POST de la carte entière (jsonAgentCard, en texte).
  a2a)  # Agent A2A (Cloud Run, GKE, autre cloud…) : on lit sa carte d'agent
    CARD_SRC=${2:?URL ou fichier de la carte d agent}; NAME=${3:?nom}
    deja "$NAME"
    if [ -f "$CARD_SRC" ]; then CARD=$(cat "$CARD_SRC")   # carte envoyée par l'équipe : rien à lire sur son service
    else
      TOKEN=$(gcloud auth print-identity-token 2>/dev/null || true)   # Cloud Run privé : jeton d'identité
      CARD=$(curl -fsS ${TOKEN:+-H "Authorization: Bearer $TOKEN"} "$CARD_SRC")
    fi
    SERVICE_URL=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["url"])' "$CARD")
    if [[ "$SERVICE_URL" == *.run.app* ]]; then
      SVC=$(gcloud run services list --filter="status.url:${SERVICE_URL%%/}" --format='value(metadata.name,region,project)' 2>/dev/null | head -1 || true)
      if [ -n "$SVC" ]; then read -r S R _ <<<"$SVC"
        grant gcloud run services add-iam-policy-binding "$S" --region="$R" --role=roles/run.invoker --member="$GE_SA"
      else echo "⚠  Donner roles/run.invoker à $GE_SA sur le service Cloud Run de $SERVICE_URL (projet de l'agent)."; fi
    fi
    python3 -c 'import json,sys; print(json.dumps({"displayName": sys.argv[1], "description": json.loads(sys.argv[2]).get("description", sys.argv[1]),
      "a2aAgentDefinition": {"jsonAgentCard": sys.argv[2]}}))' "$NAME" "$CARD" | avec_auth |
      curl -fsS -X POST "${H[@]}" "$BASE" -d @- | python3 -c 'import json,sys; print("ajouté :", json.load(sys.stdin)["name"])';;

  # delete : l'API supprime par ID, pas par nom : on cherche d'abord le 1er agent dont le nom affiché est exactement
  # celui donné, puis DELETE. Rien trouvé -> « introuvable » ; suppression refusée -> « ÉCHEC » (code de sortie 1).
  delete)
    NAME=${2:?nom affiché}
    ID=$(id_par_nom "$NAME")
    if [ -z "$ID" ]; then echo "introuvable : $NAME"
    elif curl -fsS -X DELETE "${H[@]}" "https://$HOST/v1alpha/$ID" >/dev/null; then echo "supprimé : $NAME"
    else echo "ÉCHEC de la suppression : $NAME"; exit 1; fi;;

  # Sans action reconnue : affiche la partie « À QUOI SERT » … « UTILISATION » de l'en-tête ci-dessus.
  *) sed -n '2,31p' "$0"; exit 2;;
esac
