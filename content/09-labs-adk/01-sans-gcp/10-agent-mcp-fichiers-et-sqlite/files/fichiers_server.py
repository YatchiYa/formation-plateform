"""Serveur MCP (stdio) de fichiers en LECTURE SEULE, limité à un dossier (DOCS_ROOT)."""
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

RACINE = Path(os.environ.get("DOCS_ROOT", Path(__file__).with_name("docs"))).resolve()
TAILLE_MAX = 20_000  # caractères renvoyés au modèle, au plus
EXTENSIONS = {".md", ".txt", ".csv"}

mcp = MCPServer("fichiers", instructions=f"Documents internes en lecture seule ({RACINE.name}/).")


def _chemin_sur(nom: str) -> Path:
    """Résout `nom` sous RACINE et refuse toute sortie du dossier (../, chemin absolu, lien)."""
    chemin = (RACINE / nom).resolve()
    if not chemin.is_relative_to(RACINE):
        raise ValueError(f"Accès refusé hors de {RACINE.name}/ : {nom}")
    if chemin.suffix not in EXTENSIONS:
        raise ValueError(f"Extension non autorisée : {chemin.suffix or '(aucune)'}")
    return chemin


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def lister_documents() -> list[str]:
    """Liste les documents disponibles (chemins relatifs au dossier partagé)."""
    return sorted(str(p.relative_to(RACINE)) for p in RACINE.rglob("*") if p.suffix in EXTENSIONS)


@mcp.tool(annotations=ToolAnnotations(read_only_hint=True))
def lire_document(nom: str) -> str:
    """Renvoie le contenu texte d'un document du dossier partagé.

    Args:
        nom: chemin relatif tel que renvoyé par lister_documents (ex. "politique-retours.md").
    """
    return _chemin_sur(nom).read_text(encoding="utf-8")[:TAILLE_MAX]


if __name__ == "__main__":
    mcp.run()
