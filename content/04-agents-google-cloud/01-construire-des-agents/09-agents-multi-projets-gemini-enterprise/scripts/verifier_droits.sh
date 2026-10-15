#!/usr/bin/env bash
# Vérifier VOS droits sur le projet des agents (LECTURE SEULE), étape par étape des guides 12-1-1 à 12-1-5.
#
# Demande à Google, permission par permission, si votre compte peut le faire (testIamPermissions). Contrairement à
# « gcloud projects get-iam-policy … », cela compte AUSSI les rôles reçus par un groupe et les rôles personnalisés
# de l'organisation : c'est la vraie réponse.
#
#   source scripts/config.sh config/12-1-agents-dans-projet-exp.env
#   ./scripts/verifier_droits.sh                 # projet des agents ($PROJET_AGENTS)
#   ./scripts/verifier_droits.sh autre-projet    # un autre projet
#
# Résultat : une ligne par besoin, « OK » ou « MANQUANT », avec le rôle à demander. Rien n'est changé.
set -euo pipefail
P=${1:-${PROJET_AGENTS:?Chargez la configuration : source scripts/config.sh config/<fichier>.env}}
JETON=$(gcloud auth print-access-token)
python3 - "$P" "$JETON" <<'PY'
import json, sys, urllib.request
projet, jeton = sys.argv[1], sys.argv[2]
# (permission, à quoi elle sert dans les guides, rôle prédéfini qui la donne)
BESOINS = [
    ("serviceusage.services.enable", "Activer les API (12-1-1 partie 5)", "roles/serviceusage.serviceUsageAdmin"),
    ("iam.serviceAccounts.create", "Créer les comptes de service des agents", "roles/iam.serviceAccountAdmin"),
    ("iam.serviceAccounts.actAs", "Faire tourner un agent avec son compte", "roles/iam.serviceAccountUser"),
    ("resourcemanager.projects.setIamPolicy", "Donner des rôles aux comptes (agents, app, simulateur)", "roles/resourcemanager.projectIamAdmin"),
    ("modelarmor.templates.create", "Filtres Model Armor (12-1-1 partie 6)", "roles/modelarmor.admin"),
    ("artifactregistry.repositories.create", "Dépôt d'images (7.1)", "roles/artifactregistry.admin"),
    ("cloudbuild.builds.create", "Construire les images avec Cloud Build (7.2)", "roles/cloudbuild.builds.editor"),
    ("storage.buckets.create", "1re construction : le bucket <projet>_cloudbuild", "roles/storage.admin"),
    ("run.services.create", "Services Cloud Run (7.2)", "roles/run.admin"),
    ("run.services.setIamPolicy", "Droit run.invoker sur un service (12-1-4, 12-1-5)", "roles/run.admin"),
    ("aiplatform.reasoningEngines.create", "Agents Agent Runtime (partie 8)", "roles/aiplatform.admin"),
    ("agentregistry.services.create", "Déclarer les agents Cloud Run dans Agent Registry (partie 9)", "roles/agentregistry.admin"),
    ("dialogflow.agents.create", "Agent Dialogflow (partie 10, option)", "roles/dialogflow.admin"),
]
req = urllib.request.Request(f"https://cloudresourcemanager.googleapis.com/v3/projects/{projet}:testIamPermissions",
                             json.dumps({"permissions": [b[0] for b in BESOINS]}).encode(),
                             {"Authorization": "Bearer " + jeton, "Content-Type": "application/json"})
try:
    accordees = set(json.load(urllib.request.urlopen(req, timeout=30)).get("permissions", []))
except urllib.error.HTTPError as e:
    sys.exit(f"ERREUR {e.code} : projet introuvable ou pas même le droit de le lire ({projet}).")
print(f"== Vos droits sur {projet} (rôles directs, de groupe et personnalisés compris)")
manquants = []
for perm, usage, role in BESOINS:
    ok = perm in accordees
    print(f"  {'OK      ' if ok else 'MANQUANT'}  {usage:<62} {'' if ok else '→ demander ' + role}")
    if not ok:
        manquants.append(role)
print()
print("Tout est en place." if not manquants else
      "À demander à l'administrateur du projet : " + ", ".join(sorted(set(manquants))) +
      "\n(ou passer l'étape concernée si elle est optionnelle : Agent Registry, Dialogflow)")
PY
