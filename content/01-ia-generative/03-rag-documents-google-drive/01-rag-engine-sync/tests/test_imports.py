"""Chaque module de l'image s'importe (une faute à l'import ferait échouer le démarrage sur Cloud Run, vu en vrai)."""
import importlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
os.environ.setdefault("PROJECT_ID", "test")


def test_modules_importables():
    for name in ["kit", "gdrive", "hook", "main", "sync_job", "agents.assistant_documents.agent"]:
        importlib.import_module(name)
