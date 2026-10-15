"""RAG sur BigQuery : morceaux + embeddings dans une table, recherche par VECTOR_SEARCH avec filtres SQL.

Usage (identifiants ADC : `gcloud auth application-default login`) :
    python bq_rag.py load                                 # dataset lab_rag_bq + table chunks
    python bq_rag.py search "jours de télétravail" rh 2026  # requête [catégorie] [année minimale]
    python bq_rag.py cleanup                              # supprime le dataset et vérifie
"""

import functools
import os
import re
import sys
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")  # dataset ET modèles Vertex AI
DATASET = os.environ.get("BQ_DATASET", "lab_rag_bq")
TABLE = f"{PROJECT}.{DATASET}.chunks"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "gemini-embedding-001")
DIMS = 768  # gemini-embedding-001 sort 3072 valeurs ; on réduit (output_dimensionality) pour stocker moins
MAX_BYTES = 10**8  # garde-fou : une requête qui lirait plus de 100 Mo est refusée au lieu d'être facturée
CATEGORIES = ("rh", "finance", "securite")
DOCS = Path(__file__).with_name("docs")

# Métadonnées des documents : deviennent des colonnes filtrables en SQL.
METADATA = {
    "politique-teletravail": ("Politique de télétravail (v3)", "rh", 2026),
    "politique-teletravail-2024": ("Politique de télétravail (v2, ancienne)", "rh", 2024),
    "notes-de-frais": ("Procédure notes de frais", "finance", 2026),
    "securite-informatique": ("Charte de sécurité informatique", "securite", 2026),
    "onboarding": ("Guide d'accueil", "rh", 2025),
}


def split_sections(markdown: str) -> list[str]:
    """Découpe un document Markdown en sections « ## » ; l'en-tête (titre + version) est recopié dans
    chaque morceau pour qu'il garde son contexte (« quelle version ? quelle société ? »)."""
    parts = re.split(r"\n(?=## )", markdown.strip())
    head, sections = parts[0], parts[1:]
    return [f"{head}\n\n{s}" for s in sections] or [head]


def build_query(categorie: str | None = None, annee_min: int | None = None, top_k: int = 4) -> tuple[str, dict]:
    """SQL VECTOR_SEARCH + paramètres. Les filtres passent par des paramètres (@categorie…), jamais
    par concaténation de texte : pas d'injection SQL possible, même si le modèle invente une valeur."""
    where, params = [], {}
    if categorie:
        if categorie not in CATEGORIES:
            raise ValueError(f"catégorie inconnue : {categorie!r} (attendu : {', '.join(CATEGORIES)})")
        where.append("categorie = @categorie")
        params["categorie"] = categorie
    if annee_min:
        where.append("annee >= @annee_min")
        params["annee_min"] = int(annee_min)
    base = f"(SELECT * FROM `{TABLE}`" + (f" WHERE {' AND '.join(where)})" if where else ")")
    sql = f"""
SELECT base.doc, base.titre, base.annee, base.texte, distance
FROM VECTOR_SEARCH(
  {base}, 'embedding',
  (SELECT @query_embedding AS embedding),
  top_k => {int(top_k)}, distance_type => 'COSINE')
ORDER BY distance"""
    return sql, params


@functools.cache  # un seul client : un client temporaire est fermé avant la requête (vérifié)
def _genai():
    from google import genai
    from google.genai import types
    return genai.Client(vertexai=True, project=PROJECT, location=LOCATION, http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5, initial_delay=2)))


def embed(texts: list[str], task: str) -> list[list[float]]:
    """task = RETRIEVAL_DOCUMENT pour les morceaux, RETRIEVAL_QUERY pour la question."""
    from google.genai import types
    r = _genai().models.embed_content(model=EMBEDDING_MODEL, contents=texts, config=types.EmbedContentConfig(
        task_type=task, output_dimensionality=DIMS))  # Limite connue : un seul appel, découper en lots au-delà de ~100 textes
    return [e.values for e in r.embeddings]


def rows_from_docs() -> list[dict]:
    rows = []
    for name, (titre, categorie, annee) in METADATA.items():
        for i, texte in enumerate(split_sections((DOCS / f"{name}.md").read_text(encoding="utf-8"))):
            rows.append({"id": f"{name}#{i}", "doc": name, "titre": titre, "categorie": categorie,
                         "annee": annee, "texte": texte})
    return rows


def load() -> None:
    from google.cloud import bigquery
    bq = bigquery.Client(project=PROJECT, location=LOCATION)
    ds = bigquery.Dataset(f"{PROJECT}.{DATASET}")
    ds.location, ds.labels = LOCATION, {"formation-lab": "rag-bigquery"}
    ds.default_table_expiration_ms = 24 * 3600 * 1000  # filet de sécurité : les tables expirent après 24 h
    bq.create_dataset(ds, exists_ok=True)
    rows = rows_from_docs()
    for r, v in zip(rows, embed([r["texte"] for r in rows], "RETRIEVAL_DOCUMENT")):
        r["embedding"] = v
    schema = [bigquery.SchemaField(n, t, mode=m) for n, t, m in [
        ("id", "STRING", "REQUIRED"), ("doc", "STRING", "REQUIRED"), ("titre", "STRING", "NULLABLE"),
        ("categorie", "STRING", "NULLABLE"), ("annee", "INT64", "NULLABLE"), ("texte", "STRING", "NULLABLE"),
        ("embedding", "FLOAT64", "REPEATED")]]
    job = bq.load_table_from_json(rows, TABLE, job_config=bigquery.LoadJobConfig(
        schema=schema, write_disposition="WRITE_TRUNCATE"))
    job.result()
    print(f"table {TABLE} : {bq.get_table(TABLE).num_rows} morceaux de {DIMS} dimensions")


def search(requete: str, categorie: str | None = None, annee_min: int | None = None, top_k: int = 4) -> list[dict]:
    from google.cloud import bigquery
    sql, params = build_query(categorie, annee_min, top_k)
    qp = [bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", embed([requete], "RETRIEVAL_QUERY")[0])]
    qp += [bigquery.ScalarQueryParameter(k, "INT64" if isinstance(v, int) else "STRING", v) for k, v in params.items()]
    job = bigquery.Client(project=PROJECT, location=LOCATION).query(sql, job_config=bigquery.QueryJobConfig(
        query_parameters=qp, maximum_bytes_billed=MAX_BYTES))
    rows = [{"doc": r.doc, "titre": r.titre, "annee": r.annee, "distance": round(r.distance, 3), "texte": r.texte}
            for r in job.result()]
    print(f"  [BigQuery] {job.total_bytes_processed} octets lus, filtre={params or 'aucun'}", file=sys.stderr)
    return rows


def cleanup() -> None:
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery
    bq = bigquery.Client(project=PROJECT, location=LOCATION)
    bq.delete_dataset(f"{PROJECT}.{DATASET}", delete_contents=True, not_found_ok=True)
    try:
        bq.get_dataset(f"{PROJECT}.{DATASET}")
        print("ATTENTION : le dataset existe encore")
    except NotFound:
        print(f"dataset {DATASET} supprimé (vérifié : get_dataset -> NotFound)")


if __name__ == "__main__":
    if not PROJECT:
        sys.exit("Définissez GOOGLE_CLOUD_PROJECT (voir .env.example).")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "load"
    t = time.time()
    if cmd == "load":
        load()
    elif cmd == "search":
        a = sys.argv[2:] + [None, None]
        for r in search(a[0], a[1] or None, int(a[2]) if a[2] else None):
            print(f"  {r['distance']}  {r['titre']} ({r['annee']}) : {r['texte'].splitlines()[-1][:80]}")
    elif cmd == "cleanup":
        cleanup()
    print(f"({time.time() - t:.1f} s)", file=sys.stderr)
