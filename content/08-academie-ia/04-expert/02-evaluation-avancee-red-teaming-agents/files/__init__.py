# Point d'entrée de `adk eval .` : ADK importe ce fichier et y cherche `root_agent`.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bank_agent import root_agent  # noqa: E402,F401
