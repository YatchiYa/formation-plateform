#!/usr/bin/env python3
"""Note §6 - Filtrer les documents AVANT de les rendre visibles à Gemini Enterprise.

Model Armor vérifie chaque fichier (injection de prompt cachée, liens malveillants,
données sensibles FR). Un fichier « propre » est copié dans --clean (dossier/bucket
que le connecteur indexe) ; un fichier suspect part en --quarantine avec la raison.

    python3 scan_before_ingest.py --template projects/P/locations/eu/templates/ge-prompt-shield \
        --src ./a_publier --clean ./publie --quarantine ./quarantaine

Pour un bucket : gcloud storage rsync gs://depot ./a_publier, puis l'inverse sur --clean.
Sortie : rapport CSV (stdout) ; code retour 1 si au moins un fichier est mis en quarantaine.
"""
import argparse
import base64
import csv
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

TYPES = {".pdf": "PDF", ".docx": "WORD_DOCUMENT", ".xlsx": "EXCEL_DOCUMENT", ".pptx": "POWERPOINT_DOCUMENT",
         ".txt": "TXT", ".md": "TXT", ".csv": "CSV"}
MAX_BYTES = 4 * 1024 * 1024  # ponytail: au-delà, revue manuelle ; découper les gros fichiers si fréquent.


def matched_filters(result: dict) -> list[str]:
    """Noms des filtres en MATCH_FOUND dans une réponse sanitizeUserPrompt."""
    def hit(node) -> bool:  # matchState peut être imbriqué (sdp -> inspectResult)
        if isinstance(node, dict):
            return node.get("matchState") == "MATCH_FOUND" or any(hit(v) for v in node.values())
        return False
    return [name for name, res in result.get("sanitizationResult", {}).get("filterResults", {}).items() if hit(res)]


def scan(template: str, path: Path, token: str) -> list[str]:
    location = template.split("/")[3]
    body = {"userPromptData": {"byteItem": {"byteDataType": TYPES[path.suffix.lower()],
                                            "byteData": base64.b64encode(path.read_bytes()).decode()}}}
    req = urllib.request.Request(
        f"https://modelarmor.{location}.rep.googleapis.com/v1/{template}:sanitizeUserPrompt",
        data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return matched_filters(json.load(r))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--clean", type=Path, required=True)
    ap.add_argument("--quarantine", type=Path, required=True)
    a = ap.parse_args()
    token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
    out = csv.writer(sys.stdout)
    out.writerow(["fichier", "verdict", "raison"])
    quarantined = 0
    for f in sorted(p for p in a.src.rglob("*") if p.is_file()):
        rel = f.relative_to(a.src)
        if f.suffix.lower() not in TYPES:
            verdict, reason = "QUARANTAINE", "format non analysable"
        elif f.stat().st_size > MAX_BYTES:
            verdict, reason = "QUARANTAINE", "trop volumineux : revue manuelle"
        else:
            try:
                hits = scan(a.template, f, token)
                verdict, reason = ("QUARANTAINE", "+".join(hits)) if hits else ("OK", "")
            except Exception as e:  # fail closed : une erreur d'analyse n'ouvre jamais la porte
                verdict, reason = "QUARANTAINE", f"erreur d'analyse : {e}"
        dest = (a.clean if verdict == "OK" else a.quarantine) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        quarantined += verdict != "OK"
        out.writerow([rel, verdict, reason])
    return 1 if quarantined else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        sample = {"sanitizationResult": {"filterResults": {
            "pi_and_jailbreak": {"piAndJailbreakFilterResult": {"matchState": "MATCH_FOUND"}},
            "malicious_uris": {"maliciousUriFilterResult": {"matchState": "NO_MATCH_FOUND"}},
            "sdp": {"sdpFilterResult": {"inspectResult": {"matchState": "MATCH_FOUND"}}}}}}
        assert matched_filters(sample) == ["pi_and_jailbreak", "sdp"], matched_filters(sample)
        print("self-test OK")
        sys.exit(0)
    sys.exit(main())
