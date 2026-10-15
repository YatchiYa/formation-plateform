"""Registre de prompts versionnés : un fichier JSON relu en revue de code, des versions immuables.

Chaque version fige le modèle, ses paramètres, le prompt système et le gabarit.
Son empreinte (sha256) est recalculée au chargement : modifier une version publiée
au lieu d'en créer une nouvelle fait échouer le chargement (et donc la CI).
"""
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REGISTRY = Path(__file__).with_name("prompts.json")


@dataclass(frozen=True)
class PromptVersion:
    prompt_id: str
    version: str
    model: str
    config: dict
    system: str
    template: str
    sha256: str

    def render(self, **variables) -> str:
        return self.template.format(**variables)


def fingerprint(v: dict) -> str:
    payload = json.dumps({k: v[k] for k in ("model", "config", "system", "template")},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def load(prompt_id: str, version: str = "production", path: Path = REGISTRY) -> PromptVersion:
    entry = json.loads(path.read_text(encoding="utf-8"))[prompt_id]
    if version == "production":
        version = entry["production"]
    v = entry["versions"][version]
    if fingerprint(v) != v["sha256"]:
        raise ValueError(f"{prompt_id}@{version} a été modifié après publication : créez une nouvelle version")
    return PromptVersion(prompt_id, version, v["model"], v["config"], v["system"], v["template"], v["sha256"])


if __name__ == "__main__":
    # python prompt_registry.py : affiche l'empreinte à recopier quand on CRÉE une version
    for pid, entry in json.loads(REGISTRY.read_text(encoding="utf-8")).items():
        for ver, v in entry["versions"].items():
            ok = "ok" if fingerprint(v) == v["sha256"] else "À METTRE À JOUR"
            print(f"{pid}@{ver} sha256={fingerprint(v)} {ok}", file=sys.stderr)
