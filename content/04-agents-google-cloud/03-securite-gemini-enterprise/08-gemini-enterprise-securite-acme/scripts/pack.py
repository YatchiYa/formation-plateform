"""Terraform `external` data source: tar.gz + base64 the agent source.

Deterministic on purpose (sorted files, zeroed mtimes/owners, gzip mtime=0):
same code => same bytes => Terraform sees no change => no redeploy.
"""
import base64
import gzip
import io
import json
import sys
import tarfile
from pathlib import Path

src = Path(json.load(sys.stdin)["src"])
skip = {"__pycache__", ".adk", ".env", ".venv"}

raw = io.BytesIO()
with tarfile.open(fileobj=raw, mode="w") as tar:
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if not path.is_file() or skip & set(rel.parts):
            continue
        info = tar.gettarinfo(str(path), arcname=str(rel))
        info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
        with path.open("rb") as f:
            tar.addfile(info, f)

archive = gzip.compress(raw.getvalue(), mtime=0)
json.dump({"archive": base64.b64encode(archive).decode()}, sys.stdout)
