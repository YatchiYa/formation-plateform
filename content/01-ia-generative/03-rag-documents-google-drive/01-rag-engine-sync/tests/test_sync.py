"""Logique pure de la synchro (sans réseau). Lancer : ../.venv/bin/pytest -q tests/"""
import os
import sys
from types import SimpleNamespace as NS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
os.environ.setdefault("PROJECT_ID", "test")  # kit.py s'initialise sans appel réseau quand BUCKET est vide
import kit  # noqa: E402


def drive_file(file_id):
    return NS(name=f"rf-{file_id}", gcs_source=None,
              google_drive_source=NS(resource_ids=[NS(resource_id=file_id)]))


def gcs_file(uri):
    return NS(name=f"rf-{uri}", google_drive_source=None, gcs_source=NS(uris=[uri]))


def test_corpus_key():
    assert kit.corpus_key(drive_file("abc123")) == "abc123"
    assert kit.corpus_key(gcs_file("gs://b/uploads/x.pdf")) == "gs://b/uploads/x.pdf"
    assert kit.corpus_key(NS(name="rf-9", google_drive_source=None, gcs_source=None)) == "rf-9"


def test_to_delete():
    present = {"keep": "rf-keep", "gone": "rf-gone", "gs://b/uploads/a": "rf-a", "gs://b/uploads/b": "rf-b"}
    desired = {"keep", "gs://b/uploads/a", "new-not-yet-indexed"}
    assert kit.to_delete(present, desired) == ["rf-b", "rf-gone"]
    assert kit.to_delete(present, set(present)) == []          # rien ne change -> rien à supprimer
    assert kit.to_delete({}, desired) == []                    # corpus vide


def test_drive_to_import():
    from datetime import datetime, timezone
    t = lambda h: datetime(2026, 10, 14, h, tzinfo=timezone.utc)
    files = {"new": {"name": "n", "modified": t(9)}, "same": {"name": "s", "modified": t(9)},
             "edited": {"name": "e", "modified": t(12)}}
    indexed_at = {"same": t(10), "edited": t(10), "gone": t(10)}
    assert kit.drive_to_import(files, indexed_at) == ["edited", "new"]   # l'inchangé n'est pas réimporté
    assert kit.drive_to_import({}, indexed_at) == []


def test_parse_folder_id():
    fid = "1gYDE23jVl5GLPAe5Z8QbRVaMa0dtaKYM"
    assert kit.parse_folder_id(f"https://drive.google.com/drive/folders/{fid}?usp=sharing") == fid
    assert kit.parse_folder_id(f"https://drive.google.com/drive/u/0/folders/{fid}") == fid
    assert kit.parse_folder_id(f"https://drive.google.com/open?id={fid}") == fid
    assert kit.parse_folder_id(f"  {fid} ") == fid
    for bad in ["", "hello world", "https://exemple.com/"]:
        try:
            kit.parse_folder_id(bad)
            assert False, bad
        except ValueError:
            pass


def test_public_link():
    assert kit.public_link("gs://b/uploads/x.pdf") == "https://storage.cloud.google.com/b/uploads/x.pdf"
    assert kit.public_link("https://docs.google.com/d/1") == "https://docs.google.com/d/1"
