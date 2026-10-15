#!/usr/bin/env bash
# Soigner un agent DÉJÀ AJOUTÉ à l'app Gemini Enterprise : nom, questions proposées, texte de la zone de saisie,
# langue, icône (docs/12-1-8, partie 12).
#
# À QUOI SERT CE SCRIPT
#   Modifie SEULEMENT ces champs de l'agent dans l'app (PATCH avec updateMask : rien d'autre ne bouge, ni la carte, ni
#   l'agent Agent Runtime, ni l'autorisation OAuth). Les valeurs viennent de agents/trio/catalogue.json :
#   nom = nom_affiche (+ « (A2A) » pour un agent A2A), questions = les « examples » des compétences.
#   Avant de modifier : affiche l'avant/après, enregistre l'avant dans avant-<ID>.json, demande de taper « oui ».
#
# PRÉREQUIS
#   - GE_PROJECT (ID du projet de l'app), GE_APP (ID de l'app), GE_LOCATION (eu par défaut) : remplis par
#     « source scripts/config.sh … », ou donnés devant la commande (sans toucher au fichier de config).
#   - Droit : roles/discoveryengine.admin (ou editor) sur le projet de l'app.
#
# UTILISATION
#   GE_PROJECT=acme-gemini-prod GE_APP=gemini-enterprise-app GE_LOCATION=eu \
#     ./scripts/personnaliser_agent.sh "test gmail remote agent with auth" courriels
#   … "Nom actuel" <clé> --nom "Rapport e-mails" --icone icone.png   # autre nom ; icône PNG carrée
#   … --annuler avant-<ID>.json                                       # remettre les valeurs d'avant
#   --oui : sans question (scripts, CI).
#
# RÉSULTAT ATTENDU
#   « AVANT : … », « APRÈS : … », puis « modifié : <nom> ». Dans le chat : nouveau nom, icône, questions proposées.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${GE_PROJECT:=${PROJET_APP:-}}" "${GE_APP:=${APP_ID:-}}" "${GE_LOCATION:=eu}"
[ -n "$GE_PROJECT" ] && [ -n "$GE_APP" ] || { sed -n '2,24p' "$0"; exit 2; }
HOST=$([ "$GE_LOCATION" = global ] && echo discoveryengine.googleapis.com || echo "$GE_LOCATION-discoveryengine.googleapis.com")
BASE="https://$HOST/v1alpha"
LISTE="$BASE/projects/$GE_PROJECT/locations/$GE_LOCATION/collections/default_collection/engines/$GE_APP/assistants/default_assistant/agents"
H=(-H "Authorization: Bearer $(gcloud auth print-access-token)" -H "Content-Type: application/json" -H "X-Goog-User-Project: $GE_PROJECT")
MASQUE=displayName,starterPrompts,customPlaceholderText,languageCode

if [ "${1:-}" = --annuler ]; then   # remettre l'avant enregistré (même masque, plus l'icône si elle y était)
  F=${2:?fichier avant-<ID>.json}
  NOM=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "$F")
  M=$(python3 -c 'import json,sys; print(sys.argv[2] + (",icon" if "icon" in json.load(open(sys.argv[1])) else ""))' "$F" "$MASQUE")
  curl -fsS -X PATCH "${H[@]}" "$BASE/$NOM?updateMask=$M" -d @"$F" >/dev/null && echo "remis comme avant : $NOM"; exit 0
fi

ACTUEL=${1:?nom actuel de l agent dans l app}; K=${2:?clé du catalogue}; shift 2
NOUVEAU=""; ICONE=""; OUI=non
while [ $# -gt 0 ]; do case "$1" in
  --nom) NOUVEAU=$2; shift 2;; --icone) ICONE=$2; shift 2;; --oui) OUI=oui; shift;; *) echo "option inconnue : $1"; exit 2;; esac; done

AGENT=$(curl -fsS "${H[@]}" "$LISTE" | python3 -c 'import json,sys
a=[x for x in json.load(sys.stdin).get("agents", []) if x.get("displayName") == sys.argv[1]]
print(json.dumps(a[0]) if a else "")' "$ACTUEL")
[ -z "$AGENT" ] && { echo "Aucun agent nommé « $ACTUEL » dans l'app. Les noms :"; curl -fsS "${H[@]}" "$LISTE" | python3 -c 'import json,sys; [print("  " + x.get("displayName", "")) for x in json.load(sys.stdin).get("agents", [])]'; exit 1; }

# python : l'avant (fichier), le corps (fichier), l'affichage avant/après ; imprime « <nom ressource> <id> ».
read -r NOM ID < <(AGENT=$AGENT python3 - "$K" "$NOUVEAU" "$ICONE" "$MASQUE" <<'PY'
import base64, json, os, sys
cle, nouveau, icone, masque = sys.argv[1:5]
ag = json.loads(os.environ["AGENT"])
cat = json.load(open("agents/trio/catalogue.json"))[cle]
champs = masque.split(",") + (["icon"] if icone else [])
avant = {"name": ag["name"], **{c: ag[c] for c in champs if c in ag}}
nom = nouveau or cat["nom_affiche"] + (" (A2A)" if "a2aAgentDefinition" in ag else "")
apres = {"displayName": nom,
         "starterPrompts": [{"text": e} for c in cat["competences"] for e in c.get("examples", [])][:4],
         "customPlaceholderText": cat.get("placeholder", f"Posez votre question à « {cat['nom_affiche']} »…"),
         "languageCode": "fr"}
if icone:
    apres["icon"] = {"content": base64.b64encode(open(icone, "rb").read()).decode()}
ident = ag["name"].rsplit("/", 1)[1]
json.dump(avant, open(f"avant-{ident}.json", "w"), ensure_ascii=False)
json.dump(apres, open(f"corps-{ident}.json", "w"), ensure_ascii=False)
court = lambda d: {k: ("<image>" if k == "icon" else v) for k, v in d.items() if k != "name"}
print("AVANT :", json.dumps(court(avant), ensure_ascii=False), file=sys.stderr)
print("APRÈS :", json.dumps(court(apres), ensure_ascii=False), file=sys.stderr)
print(ag["name"], ident)
PY
)
M=$MASQUE${ICONE:+,icon}
if [ "$OUI" != oui ]; then
  read -r -p "Modifier cet agent dans l'app $GE_APP (projet $GE_PROJECT) ? Tapez « oui » : " R
  [ "$R" = oui ] || { echo "rien modifié"; rm -f "corps-$ID.json"; exit 0; }
fi
curl -fsS -X PATCH "${H[@]}" "$BASE/$NOM?updateMask=$M" -d @"corps-$ID.json" >/dev/null
rm -f "corps-$ID.json"
echo "modifié : $NOM  (retour arrière : $0 --annuler avant-$ID.json)"
