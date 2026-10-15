"""Source de données Terraform `external` : met le code de l'agent (dossier agent/) en tar.gz, encodé en base64.

Agent Runtime n'accepte pas d'image : il veut le code en archive. Terraform appelle ce script tout seul
(terraform/main.tf, data "external" "agent_source") : ne pas le lancer à la main.

Entrée (JSON sur l'entrée standard) : {"src": "<dossier>", "only": "<éléments de 1er niveau à garder, séparés par des virgules>"}.
Sortie : exactement {"archive": "H4sI…"} et rien d'autre (Terraform l'exige ; ne jamais ajouter de print ici).
Déterministe (fichiers triés, dates et propriétaires à zéro) : même code => même archive => pas de redéploiement.
Toujours exclus : __pycache__, .adk, .env, .venv. Repris du projet 09 (scripts/pack.py).
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
