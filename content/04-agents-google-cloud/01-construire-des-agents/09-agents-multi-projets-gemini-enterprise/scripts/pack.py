"""Source de données Terraform `external` : met le code d'un agent en tar.gz, encodé en base64.

À quoi sert ce script
  Terraform ne sait pas fabriquer lui-même l'archive de code qu'attend Agent Runtime. Ce script la fabrique :
  il lit un dossier, en fait un tar.gz, l'encode en base64 et le rend à Terraform, qui l'envoie à Google.

Quand l'utiliser
  Jamais à la main : appelé AUTOMATIQUEMENT par Terraform, à chaque `terraform plan` / `apply`, depuis
  terraform/modules/adk_agent/main.tf (data "external" "source"). Dans le plan, c'est la ligne
    module.agent["meteo"].data.external.source will be read during apply
  Utilisé par 02-bis-agent-runtime (docs/12-1-2, partie 6) et terraform/ (agents stock et orchestrateur).

Prérequis
  - `python3` du système (pas besoin du venv) : bibliothèque standard seulement.
  - Aucune configuration, aucun droit Google Cloud : rien n'est appelé sur le réseau.

Utilisation
  Entrée : un objet JSON sur l'entrée standard (protocole de la source `external` de Terraform) :
    src   dossier du code (ex. agents/trio)
    only  facultatif : éléments de 1er niveau à garder, séparés par des virgules
          (ex. "commun.py,requirements.txt,taille_agent") ; vide ou absent = tout le dossier.
          Ainsi, modifier ou ajouter UN AUTRE agent ne change pas l'archive de celui-ci
          (pas de redéploiement).
  Toujours exclus : __pycache__, .adk, .env, .venv.

  Essai à la main, depuis le dossier du projet (affiche la longueur de l'archive) :
    echo '{"src":"agents/trio","only":"commun.py,requirements.txt,meteo_agent"}' | python3 scripts/pack.py \\
      | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["archive"]))'

Ce qu'il lit / ce qu'il crée
  Lit les fichiers de `src`. N'écrit aucun fichier, ne touche à rien dans Google Cloud : LECTURE SEULE.
  Déterministe exprès (fichiers triés, dates et propriétaires mis à zéro, gzip mtime=0) :
  même code => mêmes octets => Terraform ne voit aucun changement => pas de redéploiement.

Résultat attendu
  Exactement UN objet JSON sur la sortie standard, et rien d'autre (Terraform l'exige) :
    {"archive": "H4sI…"}
  Terraform le lit dans data.external.source.result.archive (source_archive de l'agent).

Erreurs fréquentes et que faire
  - Terraform : « Unexpected External Program Results » ou JSONDecodeError : l'entrée n'est pas un JSON
    valide, ou quelque chose d'autre a été écrit sur la sortie standard -> ne jamais ajouter de print ici.
  - KeyError: 'src' : la clé src manque dans l'entrée.
  - Archive vide ou agent qui ne démarre pas (module introuvable) : mauvais `src`, ou `only` ne contient pas
    le dossier de l'agent / commun.py / requirements.txt (voir source_include dans 02-bis-agent-runtime).
  - Terraform redéploie un agent sans changement de code : un fichier parasite est apparu dans le dossier
    de l'agent (fichier d'éditeur, sortie de test…) -> le supprimer.
"""
import base64
import gzip
import io
import json
import sys
import tarfile
from pathlib import Path

query = json.load(sys.stdin)
src = Path(query["src"])
only = set(filter(None, query.get("only", "").split(",")))   # "" -> ensemble vide = tout garder
skip = {"__pycache__", ".adk", ".env", ".venv"}   # caches, état local d'adk, secrets locaux, environnement

raw = io.BytesIO()
with tarfile.open(fileobj=raw, mode="w") as tar:
    # sorted() : l'ordre des fichiers dans l'archive ne dépend pas du système de fichiers.
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if not path.is_file() or skip & set(rel.parts) or (only and rel.parts[0] not in only):
            continue
        info = tar.gettarinfo(str(path), arcname=str(rel))
        # Date de modification et propriétaire changent d'un poste à l'autre (ou après un git clone) :
        # les mettre à zéro rend l'archive identique tant que le CONTENU des fichiers ne change pas.
        info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
        with path.open("rb") as f:
            tar.addfile(info, f)

# mtime=0 : sinon gzip inscrit l'heure courante dans l'en-tête et l'archive changerait à chaque plan.
archive = gzip.compress(raw.getvalue(), mtime=0)
# Seule sortie autorisée : l'objet JSON que Terraform attend (valeurs de type chaîne uniquement).
json.dump({"archive": base64.b64encode(archive).decode()}, sys.stdout)
