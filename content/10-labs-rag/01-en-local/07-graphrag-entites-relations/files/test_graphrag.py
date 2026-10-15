"""Tests sans clé d'API : résolution d'entités, graphe, voisinage, communautés, repérage littéral, score. pytest -q"""
from evaluate import coverage
from graphrag import GraphRAG, build_graph, communities, literal_mentions, neighborhood_facts, node_key

DATA = {
    "entities": [
        {"name": "Sofia Brenet", "type": "personne", "description": "dirige Héron"},
        {"name": "Héron", "type": "projet", "description": "projet de Grenoble"},
        {"name": "Ilex Capteurs", "type": "organisation", "description": "fournisseur"},
        {"name": "Pyralis Énergie", "type": "organisation", "description": "groupe"},
        {"name": "Orvale Conseil", "type": "organisation", "description": "cabinet d'audit"},
    ],
    "relations": [
        {"source": "Sofia Brenet", "relation": "dirige", "target": "le projet Héron", "doc_id": "d01"},
        {"source": "Projet Heron", "relation": "utilise les capteurs de", "target": "Ilex Capteurs", "doc_id": "d02"},
        {"source": "Ilex Capteurs", "relation": "filiale de", "target": "Pyralis Énergie", "doc_id": "d03"},
        {"source": "Orvale Conseil", "relation": "audite", "target": "Tessera Logistique", "doc_id": "d18"},
    ],
}


def test_node_key_fusionne_les_variantes():
    assert node_key("le projet Héron") == node_key("Projet Heron") == node_key("Héron") == "heron"
    assert node_key("Pyralis Énergie") == "pyralis energie"
    assert node_key("Site") == "site"  # on ne vide jamais complètement un nom


def test_graphe_sans_doublon_et_avec_provenance():
    G = build_graph(DATA)
    assert "heron" in G and "projet heron" not in G
    assert G.number_of_nodes() == 6  # Tessera Logistique créée depuis une relation
    assert G.edges["heron", "ilex capteurs"]["facts"] == ["Héron --utilise les capteurs de--> Ilex Capteurs [d02]"]


def test_voisinage_a_deux_sauts():
    G = build_graph(DATA)
    facts = neighborhood_facts(G, ["sofia brenet"], radius=2)
    assert any("[d02]" in f for f in facts) and not any("[d03]" in f for f in facts)  # Pyralis est à 3 sauts
    assert neighborhood_facts(G, ["sofia brenet"], radius=3)[0].endswith("[d01]")  # les plus proches d'abord


def test_communautes_reproductibles():
    G = build_graph(DATA)
    assert communities(G) == communities(G)
    assert sorted(n for c in communities(G) for n in c) == sorted(G)


def test_reperage_litteral():
    G = build_graph(DATA)
    assert literal_mentions(G, "Qui dirige le projet Héron ?") == ["heron"]
    assert literal_mentions(G, "Quel lien entre Sofia Brenet et Pyralis Énergie ?") == ["sofia brenet", "pyralis energie"]


def test_recherche_globale_sans_entite():
    G = build_graph(DATA)
    g = GraphRAG(G, communities(G), ["Résumé A", "Résumé B"])
    assert g.context([]) == "Résumés de communautés :\nRésumé A\nRésumé B"
    assert "Entités de la question :\nSofia Brenet : dirige Héron" in g.context(["sofia brenet"])


def test_score_par_couverture():
    assert coverage("Lina Ferraz dirige Lynx", ["Lina Ferraz", "Maëlle Ostin"]) == 0.5
    assert coverage("maelle ostin et LINA FERRAZ", ["Lina Ferraz", "Maëlle Ostin"]) == 1.0
