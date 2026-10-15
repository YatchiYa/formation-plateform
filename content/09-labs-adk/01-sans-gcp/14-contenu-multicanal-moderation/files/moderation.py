"""Règles de modération, en Python pur (testables sans modèle).

- données personnelles : e-mail, téléphone français, IBAN, numéro de carte -> masquées ;
- promesses interdites : allégations absolues ou trompeuses -> bloquées.
"""
import re

DONNEES_PERSONNELLES = {
    "email": re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"),
    "telephone": re.compile(r"(?<!\d)(?:\+33\s?|0)[1-9](?:[\s.-]?\d{2}){4}(?!\d)"),
    "iban": re.compile(r"\bFR\d{2}(?:\s?[\dA-Z]{4}){5}\s?[\dA-Z]{3}\b", re.I),
    "carte": re.compile(r"(?<!\d)(?:\d{4}[\s-]?){3}\d{4}(?!\d)"),
}

# Limite connue : liste de motifs, pas un classifieur ; à enrichir avec votre service juridique.
PROMESSES_INTERDITES = {
    "garantie absolue": r"garanti(e|s|es)? (à vie|à 100|sans condition)|résultats? garantis?",
    "100 %": r"100 ?% (efficace|garanti|sûr|sans risque|satisfait)",
    "sans risque": r"(sans|zéro|aucun) (aucun )?risque",
    "allégation santé": r"\bguéri[rt]\b|\bsoigne(nt)?\b|prévient (le|la|les) (cancer|maladie)",
    "superlatif invérifiable": r"\bmeilleur(e|s|es)?\b[^.!?\n]{0,30}\b(du|au) (marché|monde)|n°\s?1 mondial",
    "miracle": r"\bmiracle\b",
}
_PROMESSES = {k: re.compile(v, re.I) for k, v in PROMESSES_INTERDITES.items()}


def masquer_donnees_personnelles(texte: str) -> tuple[str, list[str]]:
    """Remplace chaque donnée personnelle par [EMAIL], [TELEPHONE]... ; renvoie aussi les types trouvés."""
    trouves = []
    for nom, motif in DONNEES_PERSONNELLES.items():
        texte, n = motif.subn(f"[{nom.upper()}]", texte)
        if n:
            trouves.append(nom)
    return texte, trouves


def promesses_interdites(texte: str) -> list[str]:
    """Les catégories de promesses interdites présentes dans le texte."""
    return [nom for nom, motif in _PROMESSES.items() if motif.search(texte)]


if __name__ == "__main__":
    t, d = masquer_donnees_personnelles("Contact : lea.dupont@exemple.fr, 06 12 34 56 78")
    assert t == "Contact : [EMAIL], [TELEPHONE]" and d == ["email", "telephone"], (t, d)
    assert promesses_interdites("Résultat garanti à vie, zéro risque !") == [
        "garantie absolue", "sans risque"]
    assert promesses_interdites("Garde l'eau fraîche 12 h (tests internes).") == []
    print("ok")
