#!/usr/bin/env bash
# Vérifier des API sur un projet et activer SEULEMENT celles qui manquent.
#   ./scripts/verifier_api.sh PROJET api1.googleapis.com api2.googleapis.com …
#
# À QUOI SERT CE SCRIPT
#   Une API Google doit être activée dans un projet avant qu'on s'en serve. Ce script regarde lesquelles sont déjà
#   actives, affiche OK / MANQUANTE pour chacune de votre liste, et active d'un coup seulement les manquantes.
#
# QUAND L'UTILISER, ET QUI
#   Au début de chaque guide, après la connexion : docs/12-1-1 partie 5 (et 10.1 pour Dialogflow), docs/12-1 §1.6,
#   docs/12-2 §1.6. Par la personne qui déploie, sur le projet des agents ; par l'admin sur le projet de l'app.
#
# PRÉREQUIS
#   - source scripts/config.sh config/<fichier>.env, pour avoir $PROJET_AGENTS / $PROJET_APP (le script lui-même ne
#     lit que ses arguments).
#   - gcloud connecté. Pour activer : roles/serviceusage.serviceUsageAdmin (ou propriétaire) sur le projet.
#
# UTILISATION
#   ./scripts/verifier_api.sh <PROJET> <api> [<api> …]     (nom complet : xxx.googleapis.com)
#   ./scripts/verifier_api.sh $PROJET_AGENTS run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
#   ./scripts/verifier_api.sh $PROJET_APP cloudresourcemanager.googleapis.com serviceusage.googleapis.com discoveryengine.googleapis.com
#   ./scripts/verifier_api.sh $PROJET_AGENTS dialogflow.googleapis.com
#
# CE QU'IL LIT / CE QU'IL MODIFIE
#   Lit la liste des API actives du projet. Active les API manquantes (rien d'autre ; il n'en désactive jamais).
#   Idempotent : relancé, il répond « rien à activer ». Aucun fichier local.
#
# RÉSULTAT ATTENDU
#   OK        cloudresourcemanager.googleapis.com
#   MANQUANTE cloudbuild.googleapis.com
#   activées : cloudbuild.googleapis.com          (ou « rien à activer » si tout est OK)
#   Activation : 1 à 2 minutes.
#
# ERREURS FRÉQUENTES ET QUE FAIRE
#   « 1: projet »                       -> aucun argument : donner le projet puis les API.
#   Toutes « MANQUANTE » + erreur gcloud -> le projet est vide ou faux. Si $PROJET_… est vide (configuration pas
#                                          chargée), la 1re API est prise pour le projet : source scripts/config.sh ….
#   PERMISSION_DENIED à l'activation     -> rôle serviceusage.serviceUsageAdmin manquant.
#   PERMISSION_DENIED juste APRÈS        -> API tout juste activée : attendre 1 minute, relancer la commande suivante.
# Pas de « set -e » : on veut afficher tout le bilan même si une commande échoue.
set -uo pipefail
P=${1:?projet}; shift
# Une seule lecture de la liste des API actives (plus rapide que d'interroger API par API).
actives=$(gcloud services list --enabled --project="$P" --format="value(config.name)")
manquantes=()
# grep -qx : la ligne doit être EXACTEMENT le nom de l'API (pas seulement le contenir).
for API in "$@"; do
  if grep -qx "$API" <<<"$actives"; then echo "OK        $API"; else echo "MANQUANTE $API"; manquantes+=("$API"); fi
done
# Une seule commande d'activation pour toutes les manquantes.
if [ ${#manquantes[@]} -gt 0 ]; then
  gcloud services enable "${manquantes[@]}" --project="$P" && echo "activées : ${manquantes[*]}"
else
  echo "rien à activer"
fi
