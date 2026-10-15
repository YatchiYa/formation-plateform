"""Moteur de recherche sémantique local : embeddings Gemini + numpy + sqlite.

Usage :
  python moteur.py indexer                       # calcule et sauvegarde l'index (index/)
  python moteur.py chercher "chaussure pour la boue"
  python moteur.py similaires P019
  python moteur.py doublons [seuil]
  python moteur.py clusters [k]
"""
import hashlib
import json
import os
import sqlite3
import sys
import time

import numpy as np
from dotenv import load_dotenv

load_dotenv()
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))
DOSSIER = os.environ.get("INDEX_DIR", "index")


# --- 1. Textes à vectoriser : préfixes de tâche de gemini-embedding-2 ---------
def texte_document(p: dict) -> str:
    return f"title: {p['nom']} | text: {p['categorie']}. {p['description']}"


def texte_requete(q: str) -> str:
    return f"task: search result | query: {q}"


def texte_symetrique(p: dict, tache: str) -> str:
    """Pour le clustering ou la similarité : même format des deux côtés."""
    return f"task: {tache} | query: {p['nom']}. {p['description']}"


# --- 2. Appel au modèle d'embeddings ------------------------------------------
def normaliser(m: np.ndarray) -> np.ndarray:
    return m / np.linalg.norm(m, axis=-1, keepdims=True)


def embedder_gemini(client=None, dim=EMBED_DIM, lot=20):
    """Renvoie une fonction textes -> matrice (n, dim) de vecteurs normalisés."""
    from google import genai
    from google.genai import errors, types
    client = client or genai.Client()
    if getattr(client, "vertexai", False):
        lot = 1  # sur Vertex AI, gemini-embedding-2 n'accepte qu'un contenu par requête

    def embed(textes):
        vecteurs = []
        for i in range(0, len(textes), lot):
            # Une Content par texte : une liste de str donnerait UN seul vecteur agrégé.
            contents = [types.Content(parts=[types.Part(text=t)]) for t in textes[i:i + lot]]
            for essai in range(4):
                try:
                    r = client.models.embed_content(
                        model=EMBED_MODEL, contents=contents,
                        config=types.EmbedContentConfig(output_dimensionality=dim))
                    break
                except errors.APIError as e:
                    if e.code not in (429, 500, 503) or essai == 3:
                        raise
                    time.sleep(2 ** essai * 2)
            vecteurs += [e.values for e in r.embeddings]
        return normaliser(np.array(vecteurs, dtype=np.float32))
    return embed


# --- 3. Index persistant : vecteurs.npy + produits.sqlite ---------------------
def empreinte(texte: str) -> str:
    return hashlib.sha256(f"{EMBED_MODEL}|{EMBED_DIM}|{texte}".encode()).hexdigest()[:16]


def charger_index(dossier=DOSSIER):
    vecteurs = np.load(os.path.join(dossier, "vecteurs.npy"))
    with sqlite3.connect(os.path.join(dossier, "produits.sqlite")) as db:
        db.row_factory = sqlite3.Row
        produits = [dict(r) for r in db.execute("SELECT * FROM produits ORDER BY ligne")]
    return vecteurs, produits


def indexer(produits, embed, dossier=DOSSIER) -> int:
    """(Re)construit l'index. Ne recalcule que les fiches nouvelles ou modifiées.
    Renvoie le nombre de textes envoyés au modèle."""
    os.makedirs(dossier, exist_ok=True)
    anciens = {}
    if os.path.exists(os.path.join(dossier, "vecteurs.npy")):
        v, ps = charger_index(dossier)
        anciens = {p["empreinte"]: v[p["ligne"]] for p in ps}
    textes = [texte_document(p) for p in produits]
    empreintes = [empreinte(t) for t in textes]
    a_calculer = [i for i, e in enumerate(empreintes) if e not in anciens]
    nouveaux = dict(zip(a_calculer, embed([textes[i] for i in a_calculer]))) if a_calculer else {}
    vecteurs = np.stack([nouveaux[i] if i in nouveaux else anciens[e]
                         for i, e in enumerate(empreintes)]).astype(np.float32)
    np.save(os.path.join(dossier, "vecteurs.npy"), vecteurs)
    with sqlite3.connect(os.path.join(dossier, "produits.sqlite")) as db:
        db.execute("DROP TABLE IF EXISTS produits")
        db.execute("CREATE TABLE produits (ligne INTEGER PRIMARY KEY, id TEXT UNIQUE, nom TEXT,"
                   " categorie TEXT, description TEXT, prix REAL, empreinte TEXT)")
        db.executemany("INSERT INTO produits VALUES (?,?,?,?,?,?,?)",
                       [(i, p["id"], p["nom"], p["categorie"], p["description"], p["prix"], e)
                        for i, (p, e) in enumerate(zip(produits, empreintes))])
    return len(a_calculer)


# --- 4. Recherche, similaires, doublons, clusters -----------------------------
def top_k(vecteurs, requete, k=5, exclure=()):
    """Similarité cosinus = produit scalaire, car tous les vecteurs sont normalisés."""
    scores = vecteurs @ requete
    for i in exclure:
        scores[i] = -np.inf
    meilleurs = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in meilleurs]


def chercher(vecteurs, produits, embed, requete, k=5):
    q = embed([texte_requete(requete)])[0]
    return [(produits[i], s) for i, s in top_k(vecteurs, q, k)]


def similaires(vecteurs, produits, produit_id, k=4):
    ligne = next(p["ligne"] for p in produits if p["id"] == produit_id)
    return [(produits[i], s) for i, s in top_k(vecteurs, vecteurs[ligne], k, exclure=[ligne])]


def doublons(vecteurs, seuil=0.9):
    """Paires (i, j, score) au-dessus du seuil. Limite : O(n²), passer à un index ANN au-delà de ~100 000 fiches."""
    sim = vecteurs @ vecteurs.T
    i, j = np.where(np.triu(sim, k=1) >= seuil)
    return sorted(((int(a), int(b), float(sim[a, b])) for a, b in zip(i, j)), key=lambda x: -x[2])


def kmeans(vecteurs, k, iterations=50, graine=0, essais=5):
    """K-means sphérique minimal (cosinus), relancé `essais` fois ; garde le plus compact."""
    rng = np.random.default_rng(graine)
    meilleur, meilleure_cohesion = None, -np.inf
    for _ in range(essais):
        centres = vecteurs[rng.choice(len(vecteurs), k, replace=False)]
        for _ in range(iterations):
            etiquettes = np.argmax(vecteurs @ centres.T, axis=1)
            nouveaux = normaliser(np.stack([vecteurs[etiquettes == c].mean(0) if np.any(etiquettes == c)
                                            else centres[c] for c in range(k)]))
            if np.allclose(nouveaux, centres):
                break
            centres = nouveaux
        cohesion = float(np.sum(vecteurs * centres[etiquettes]))  # somme des cosinus au centre
        if cohesion > meilleure_cohesion:
            meilleur, meilleure_cohesion = etiquettes, cohesion
    return meilleur


def purete(etiquettes, categories) -> float:
    """Part des fiches dont le groupe a pour catégorie majoritaire la leur (1.0 = parfait)."""
    total = 0
    for c in set(etiquettes.tolist()):
        membres = [categories[i] for i in np.where(etiquettes == c)[0]]
        total += max(membres.count(x) for x in set(membres))
    return total / len(categories)


# --- 5. Ligne de commande ------------------------------------------------------
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "aide"
    if cmd == "indexer":
        with open("produits.json", encoding="utf-8") as f:
            n = indexer(json.load(f), embedder_gemini())
        print(f"Index à jour dans {DOSSIER}/ ({n} fiche(s) recalculée(s), modèle {EMBED_MODEL}, {EMBED_DIM} dims)")
    elif cmd == "chercher":
        v, ps = charger_index()
        for p, s in chercher(v, ps, embedder_gemini(), sys.argv[2]):
            print(f"{s:.3f}  {p['id']}  {p['nom']}  ({p['categorie']})")
    elif cmd == "similaires":
        v, ps = charger_index()
        for p, s in similaires(v, ps, sys.argv[2]):
            print(f"{s:.3f}  {p['id']}  {p['nom']}")
    elif cmd == "doublons":
        v, ps = charger_index()
        for i, j, s in doublons(v, float(sys.argv[2]) if len(sys.argv) > 2 else 0.9):
            print(f"{s:.3f}  {ps[i]['id']} {ps[i]['nom']}  <->  {ps[j]['id']} {ps[j]['nom']}")
    elif cmd == "clusters":
        v, ps = charger_index()
        k = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        # Tâche symétrique « clustering » : nouveaux vecteurs (3 appels pour 60 fiches)
        vc = embedder_gemini()([texte_symetrique(p, "clustering") for p in ps])
        categories = [p["categorie"] for p in ps]
        for nom, m in (("vecteurs de recherche", v), ("vecteurs « clustering »", vc)):
            print(f"Pureté avec les {nom} : {purete(kmeans(m, k), categories):.2f}")
        etiquettes = kmeans(vc, k)
        for c in range(k):
            print(f"Groupe {c}: " + ", ".join(ps[i]["nom"] for i in np.where(etiquettes == c)[0]))
    else:
        print(__doc__)
