"""Génère un long document fictif et déterministe (catalogue + conditions) pour les expériences
« contexte long vs RAG » et « mise en cache ». Aucune donnée réelle."""
import random

FAMILLES = ["lampe", "chaise", "bureau", "étagère", "fauteuil", "tapis", "miroir", "commode"]
MATIERES = ["chêne", "noyer", "métal brossé", "rotin", "lin", "verre fumé", "bambou", "laiton"]
COULEURS = ["sable", "anthracite", "vert sauge", "terracotta", "ivoire", "bleu nuit"]
ENTREPOTS = ["Lyon", "Nantes", "Lille", "Toulouse"]


def products(n=160, seed=7):
    rnd = random.Random(seed)
    out = []
    for i in range(1, n + 1):
        out.append({
            "ref": f"AT-{1000 + i}",
            "nom": f"{rnd.choice(FAMILLES).capitalize()} {rnd.choice(MATIERES)} {rnd.choice(COULEURS)}",
            "prix": rnd.randrange(19, 899),
            "delai": rnd.randrange(2, 21),
            "entrepot": rnd.choice(ENTREPOTS),
            "garantie": rnd.choice([1, 2, 3, 5]),
        })
    return out


def chunks(n=160, seed=7) -> list[str]:
    """Un passage par produit : l'unité de découpage pour le RAG."""
    return [f"Référence {p['ref']} : {p['nom']}. Prix {p['prix']} euros TTC. Expédié depuis l'entrepôt de "
            f"{p['entrepot']} sous {p['delai']} jours ouvrés. Garantie {p['garantie']} an(s)."
            for p in products(n, seed)]


def document(n=160, seed=7) -> str:
    head = ("# Catalogue et conditions de la boutique Atelier (document fictif)\n\n"
            "Retours acceptés sous 30 jours, produit non utilisé, dans son emballage d'origine. "
            "Livraison express disponible pour les produits expédiés depuis Lyon uniquement.\n\n## Produits\n")
    return head + "\n".join(f"- {c}" for c in chunks(n, seed))


if __name__ == "__main__":
    d = document()
    print(len(d), "caractères ;", d.splitlines()[5])
