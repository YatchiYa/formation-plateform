"""GraphRAG léger : entités et relations extraites par Gemini -> graphe networkx -> communautés -> réponses.

Usage : python graphrag.py "Qui a formé le technicien qui a réparé le banc d'essai B2 ?"
"""
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import networkx as nx
import numpy as np
from dotenv import load_dotenv
from pydantic import BaseModel

HERE = Path(__file__).parent
CACHE = HERE / ".cache"
load_dotenv(HERE / ".env")
MODEL = os.environ.get("MODEL", "gemini-3.5-flash")
LIGHT_MODEL = os.environ.get("LIGHT_MODEL", "gemini-3.5-flash-lite")  # pour les tâches simples (repérer les entités)
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-2")
EMBED_DIM = int(os.environ.get("EMBED_DIM", "768"))


# ---------- Gemini ----------
def gemini():
    from google import genai
    return genai.Client()  # lit GOOGLE_API_KEY (ou GEMINI_API_KEY)


def with_retry(fn, tries=6):
    from google.genai import errors
    for i in range(tries):
        try:
            return fn()
        except errors.APIError as e:
            if e.code not in (429, 500, 503) or i == tries - 1:
                raise
            time.sleep(2 ** i)


def generate(client, prompt, schema=None, model=None):
    from google.genai import types
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=schema) if schema else None
    r = with_retry(lambda: client.models.generate_content(model=model or MODEL, contents=prompt, config=cfg))
    return r.parsed if schema else (r.text or "").strip()


def embed(client, texts):
    from google.genai import types
    contents = [types.Content(parts=[types.Part(text=t)]) for t in texts]  # un Content par texte = un vecteur par texte
    r = with_retry(lambda: client.models.embed_content(
        model=EMBED_MODEL, contents=contents, config=types.EmbedContentConfig(output_dimensionality=EMBED_DIM)))
    v = np.array([e.values for e in r.embeddings], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def cached(name: str, key_data, compute):
    """Relit .cache/<name>-<empreinte>.json si les entrées n'ont pas changé, sinon calcule et enregistre."""
    key = hashlib.sha256(json.dumps(key_data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = CACHE / f"{name}-{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    value = compute()
    CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    return value


# ---------- 1. Extraction structurée ----------
class Entity(BaseModel):
    name: str
    type: str          # personne, projet, organisation, site, equipement, composant, incident
    description: str


class Relation(BaseModel):
    source: str
    relation: str
    target: str
    doc_id: str


class Extraction(BaseModel):
    entities: list[Entity]
    relations: list[Relation]


EXTRACT_PROMPT = """Extrais un graphe de connaissances des documents ci-dessous.
- Entités : personnes, projets, organisations, sites, équipements, composants, incidents.
- Utilise toujours le nom canonique le plus court et complet : « Héron » (pas « le projet Héron »), « Sofia Brenet », « Grenoble ».
- Relations : uniquement celles écrites explicitement, avec un verbe court (dirige, fournit, filiale de, rend compte à,
  partage avec, intègre, situé à, audite, a formé, a réparé, a travaillé avec, transporte entre…).
- doc_id : l'identifiant du document d'où vient la relation.

"""


def extract(client, docs: list[dict], batch: int = 6) -> dict:
    def compute():
        out = {"entities": [], "relations": []}
        for i in range(0, len(docs), batch):
            text = "\n".join(f"[{d['id']}] {d['text']}" for d in docs[i:i + batch])
            r = generate(client, EXTRACT_PROMPT + text, Extraction)
            out["entities"] += [e.model_dump() for e in r.entities]
            out["relations"] += [x.model_dump() for x in r.relations]
        return out
    return cached("extraction", [MODEL, EXTRACT_PROMPT, docs, batch], compute)


# ---------- 2. Graphe (sans réseau) ----------
GENERIC = {"le", "la", "les", "l", "projet", "societe", "groupe", "cabinet", "site", "de", "du", "d"}


def node_key(name: str) -> str:
    """Résolution d'entités minimale : « le projet Héron », « Projet Heron » et « Héron » donnent la même clé « heron »."""
    s = unicodedata.normalize("NFKD", name.lower()).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", s)
    while len(words) > 1 and words[0] in GENERIC:
        words = words[1:]
    return " ".join(words)


def build_graph(data: dict) -> nx.Graph:
    G = nx.Graph()
    for e in data["entities"]:
        k = node_key(e["name"])
        if k not in G:
            G.add_node(k, name=e["name"], type=e["type"], descriptions=[])
        G.nodes[k]["descriptions"].append(e["description"])
    for r in data["relations"]:
        a, b = node_key(r["source"]), node_key(r["target"])
        if a == b:
            continue
        for k, n in ((a, r["source"]), (b, r["target"])):
            if k not in G:
                G.add_node(k, name=n, type="inconnu", descriptions=[])
        if not G.has_edge(a, b):
            G.add_edge(a, b, facts=[])
        G.edges[a, b]["facts"].append(f"{G.nodes[a]['name']} --{r['relation']}--> {G.nodes[b]['name']} [{r['doc_id']}]")
    return G


def communities(G: nx.Graph) -> list[list[str]]:
    """Louvain : regroupe les nœuds très connectés entre eux. seed fixe = résultat reproductible."""
    return [sorted(c) for c in nx.community.louvain_communities(G, seed=42)]


def neighborhood_facts(G: nx.Graph, seeds: list[str], radius: int = 2, max_facts: int = 40) -> list[str]:
    """Faits (arêtes) à au plus `radius` sauts des entités de la question, les plus proches d'abord."""
    dist = {}
    for s in seeds:
        for n, d in nx.single_source_shortest_path_length(G, s, cutoff=radius).items():
            dist[n] = min(d, dist.get(n, d))
    edges = [(max(dist[a], dist[b]), a, b) for a, b in G.edges if a in dist and b in dist]
    facts = []
    for _, a, b in sorted(edges):
        facts += G.edges[a, b]["facts"]
    return list(dict.fromkeys(facts))[:max_facts]


# ---------- 3. Résumés de communautés ----------
class Summaries(BaseModel):
    summaries: list[str]


def summarize_communities(client, G: nx.Graph, comms: list[list[str]]) -> list[str]:
    blocks = []
    for i, c in enumerate(comms):
        # on parcourt G.edges (ordre d'insertion, stable) et non G.subgraph(c).edges (ordre variable d'un processus à l'autre)
        facts = [f for a, b in G.edges if a in c and b in c for f in G.edges[a, b]["facts"]]
        blocks.append(f"Communauté {i} : {', '.join(G.nodes[n]['name'] for n in c)}\n" + "\n".join(facts))
    prompt = ("Pour chaque communauté ci-dessous, écris un résumé de 2 phrases qui nomme ses membres principaux et "
              f"leurs liens. Renvoie exactement {len(comms)} résumés, dans l'ordre.\n\n" + "\n\n".join(blocks))
    return cached("communautes", [MODEL, blocks], lambda: list(generate(client, prompt, Summaries).summaries))


# ---------- 4. Répondre ----------
class Mentions(BaseModel):
    names: list[str]


def link_entities(client, G: nx.Graph, question: str) -> list[str]:
    """Repère les nœuds du graphe cités dans la question (le LLM choisit dans la liste des noms connus)."""
    names = sorted(G.nodes[n]["name"] for n in G)
    prompt = (f"Liste des entités connues : {names}\n\nQuestion : {question}\n\n"
              "Renvoie les noms de la liste qui sont cités ou désignés directement dans la question, recopiés à l'identique.")
    r = generate(client, prompt, Mentions, model=LIGHT_MODEL)
    found = [node_key(n) for n in (r.names if r else [])]  # r vaut None si le JSON est invalide
    return [k for k in dict.fromkeys(literal_mentions(G, question) + found) if k in G]


def literal_mentions(G: nx.Graph, question: str) -> list[str]:
    """Filet de sécurité sans LLM : les nœuds dont la clé apparaît telle quelle (mots entiers) dans la question."""
    q = " " + " ".join(re.findall(r"[a-z0-9]+", unicodedata.normalize("NFKD", question.lower()).encode("ascii", "ignore").decode())) + " "
    return [k for k in G if f" {k} " in q]


class GraphRAG:
    def __init__(self, G, comms, summaries, client=None):
        self.G, self.comms, self.summaries, self.client = G, comms, summaries, client
        self.community_of = {n: i for i, c in enumerate(comms) for n in c}

    @classmethod
    def build(cls, client, docs):
        G = build_graph(extract(client, docs))
        comms = communities(G)
        return cls(G, comms, summarize_communities(client, G, comms), client)

    def context(self, seeds: list[str]) -> str:
        if not seeds:  # aucune entité reconnue : « recherche globale » sur tous les résumés de communautés
            return "Résumés de communautés :\n" + "\n".join(self.summaries)
        entities = [f"{self.G.nodes[s]['name']} : {' '.join(self.G.nodes[s]['descriptions'])}" for s in seeds]
        facts = neighborhood_facts(self.G, seeds)
        comm_ids = sorted({self.community_of[s] for s in seeds})
        summ = [self.summaries[i] for i in comm_ids if i < len(self.summaries)]
        return ("Entités de la question :\n" + "\n".join(entities) + "\n\nRelations du graphe :\n" + "\n".join(facts)
                + "\n\nRésumés de communautés :\n" + "\n".join(summ))

    def answer(self, question: str) -> tuple[str, list[str]]:
        seeds = link_entities(self.client, self.G, question)
        prompt = (f"{self.context(seeds)}\n\nQuestion : {question}\n"
                  "Réponds en français en 2 phrases maximum, uniquement à partir des relations ci-dessus. "
                  "Suis les relations de proche en proche si nécessaire et cite les [doc_id] utilisés. "
                  "Si l'information manque, dis-le.")
        return generate(self.client, prompt), seeds


class VectorRAG:
    """La référence : RAG vectoriel classique, top k documents."""
    def __init__(self, docs, vecs, client=None):
        self.docs, self.vecs, self.client = docs, vecs, client

    @classmethod
    def build(cls, client, docs):
        vecs = np.array(cached("embeddings", [EMBED_MODEL, EMBED_DIM, docs],
                               lambda: embed(client, [d["text"] for d in docs]).tolist()), dtype=np.float32)
        return cls(docs, vecs, client)

    def answer(self, question: str, q_vec=None, k: int = 4) -> tuple[str, list[str]]:
        q_vec = embed(self.client, [question])[0] if q_vec is None else q_vec
        hits = [self.docs[i] for i in np.argsort(-(self.vecs @ q_vec))[:k]]
        prompt = ("Documents :\n" + "\n".join(f"[{d['id']}] {d['text']}" for d in hits) +
                  f"\n\nQuestion : {question}\nRéponds en français en 2 phrases maximum, uniquement à partir "
                  "des documents ci-dessus, et cite les [id] utilisés. Si l'information manque, dis-le.")
        return generate(self.client, prompt), [d["id"] for d in hits]


def load_corpus():
    return [json.loads(line) for line in open(HERE / "corpus.jsonl", encoding="utf-8")]


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Qui a formé le technicien qui a réparé le banc d'essai B2 ?"
    client, docs = gemini(), load_corpus()
    g = GraphRAG.build(client, docs)
    print(f"Graphe : {g.G.number_of_nodes()} nœuds, {g.G.number_of_edges()} arêtes, {len(g.comms)} communautés")
    text, seeds = g.answer(q)
    print(f"[graphe] entités={seeds}\n  {text}")
    text, ids = VectorRAG.build(client, docs).answer(q)
    print(f"[vecteurs] documents={ids}\n  {text}")
