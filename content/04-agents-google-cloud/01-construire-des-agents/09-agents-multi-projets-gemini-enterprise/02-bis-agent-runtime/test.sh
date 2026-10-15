#!/usr/bin/env bash
# Test des agents déployés sur Agent Runtime : une question chacun, outils appelés affichés.
#   ./test.sh            tous les agents (noms de ressource lus dans terraform output)
#   ./test.sh taille     un seul agent (sa clé du catalogue)
# Question : la 1re question d'exemple de l'agent dans agents/trio/catalogue.json.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PYTHON:-python3}

AGENTS=$(terraform -chdir=terraform output -json agents)
for k in ${1:-$($PY -c 'import json,sys; print(" ".join(json.loads(sys.argv[1])))' "$AGENTS")}; do
  NAME=$($PY -c 'import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$AGENTS" "$k")
  QUESTION=$($PY -c 'import json,sys; a=json.load(open("../agents/trio/catalogue.json"))[sys.argv[1]]
print(next((e for c in a["competences"] for e in c.get("examples", [])), "Que sais-tu faire ?"))' "$k")
  echo "== $k  ($NAME)"
  AGENT_NAME=$NAME $PY ../scripts/query.py - "$QUESTION"
  echo
done
