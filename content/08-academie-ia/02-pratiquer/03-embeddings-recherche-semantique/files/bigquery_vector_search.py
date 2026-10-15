"""Pousser l'index local dans BigQuery et interroger avec VECTOR_SEARCH (mode « avec GCP »).

Usage :
  python bigquery_vector_search.py "chaussure pour courir dans la boue"   # crée, charge, cherche
  python bigquery_vector_search.py --nettoyer                             # supprime le dataset
Variables : GOOGLE_CLOUD_PROJECT (obligatoire), BQ_LOCATION (défaut europe-west1).
Coût : 60 lignes de 768 nombres, quelques centaines de Ko scannés (facturation minimale de 10 Mo).
"""
import os
import sys

from google.cloud import bigquery

import moteur

PROJET = os.environ["GOOGLE_CLOUD_PROJECT"]
LIEU = os.environ.get("BQ_LOCATION", "europe-west1")
DATASET = f"{PROJET}.lab_embeddings_recherche"
TABLE = f"{DATASET}.produits"
LABELS = {"formation-lab": "embeddings-recherche"}

SQL = f"""
SELECT base.id, base.nom, ROUND(1 - distance, 3) AS cosinus
FROM VECTOR_SEARCH(TABLE `{TABLE}`, 'embedding',
                   (SELECT @q AS embedding), top_k => 5, distance_type => 'COSINE')
ORDER BY distance
"""


def charger(bq):
    ds = bigquery.Dataset(DATASET)
    ds.location, ds.labels = LIEU, LABELS
    bq.create_dataset(ds, exists_ok=True)
    vecteurs, produits = moteur.charger_index()
    lignes = [{"id": p["id"], "nom": p["nom"], "categorie": p["categorie"],
               "embedding": [float(x) for x in v]} for p, v in zip(produits, vecteurs)]
    schema = [bigquery.SchemaField("id", "STRING"), bigquery.SchemaField("nom", "STRING"),
              bigquery.SchemaField("categorie", "STRING"),
              bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED")]
    job = bq.load_table_from_json(lignes, TABLE, job_config=bigquery.LoadJobConfig(
        schema=schema, write_disposition="WRITE_TRUNCATE", labels=LABELS))
    job.result()
    print(f"{len(lignes)} lignes chargées dans {TABLE}")


def chercher(bq, requete):
    q = moteur.embedder_gemini()([moteur.texte_requete(requete)])[0]
    config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("q", "FLOAT64", [float(x) for x in q])],
        maximum_bytes_billed=100 * 1024 ** 2, labels=LABELS)   # garde-fou : 100 Mo max
    job = bq.query(SQL, job_config=config, location=LIEU)
    for r in job.result():
        print(f"{r.cosinus:.3f}  {r.id}  {r.nom}")
    print(f"Octets traités : {job.total_bytes_processed}")


if __name__ == "__main__":
    bq = bigquery.Client(project=PROJET)
    if sys.argv[1:] == ["--nettoyer"]:
        bq.delete_dataset(DATASET, delete_contents=True, not_found_ok=True)
        print(f"Dataset {DATASET} supprimé")
    else:
        charger(bq)
        chercher(bq, sys.argv[1] if len(sys.argv) > 1 else "chaussure pour courir dans la boue")
