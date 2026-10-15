"""Lab Vertex AI RAG Engine : bucket GCS -> corpus -> recherche -> réponse ancrée -> nettoyage.

Usage (identifiants ADC : `gcloud auth application-default login`) :
    python rag_engine_lab.py setup            # bucket + corpus + import des documents de ./docs
    python rag_engine_lab.py ask "Combien de jours de télétravail ?"
    python rag_engine_lab.py cleanup          # supprime corpus + bucket et vérifie
    python rag_engine_lab.py all "question"   # les trois à la suite (ce que fait le test de bout en bout)
"""

import os
import sys
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

warnings.filterwarnings("ignore")  # « vertexai.rag est déprécié », « Python 3.10 non supporté »
load_dotenv()

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("RAG_LOCATION", "europe-west4")  # RAG Engine GA en Europe : europe-west3, europe-west4
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
PREFIX = "lab-rag-engine"  # préfixe de tout ce que le lab crée : le nettoyage s'appuie dessus
LABELS = {"formation-lab": "rag-engine"}
BUCKET = os.environ.get("BUCKET") or f"{PREFIX}-{PROJECT}"  # nom de bucket unique au monde
EMBEDDING_MODEL = "publishers/google/models/text-multilingual-embedding-002"
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "300"))  # en jetons
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "50"))
DOCS = Path(__file__).with_name("docs")


def chunking(size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Configuration de découpage. Le chevauchement doit rester plus petit que le morceau."""
    from vertexai import rag
    if not 0 <= overlap < size:
        raise ValueError(f"chunk_overlap ({overlap}) doit être >= 0 et < chunk_size ({size})")
    return rag.TransformationConfig(chunking_config=rag.ChunkingConfig(chunk_size=size, chunk_overlap=overlap))


def format_contexts(response) -> list[dict]:
    """Réponse de retrieval_query -> liste simple {source, score, texte} (score = distance : plus petit = plus proche)."""
    return [{"source": c.source_uri.rsplit("/", 1)[-1], "score": round(c.score, 3), "texte": c.text}
            for c in response.contexts.contexts]


def cited_sources(gm) -> list[str]:
    """Fichiers réellement cités par une réponse ancrée : les morceaux référencés par grounding_supports
    (pas ceux simplement récupérés puis ignorés), sans doublon, dans l'ordre."""
    chunks = (gm.grounding_chunks or []) if gm else []
    cited = sorted({i for s in (gm.grounding_supports or []) for i in (s.grounding_chunk_indices or [])}) if gm else []
    picked = [chunks[i] for i in cited if i < len(chunks)]
    uris = [ch.retrieved_context.uri for ch in picked if ch.retrieved_context and ch.retrieved_context.uri]
    return list(dict.fromkeys(u.rsplit("/", 1)[-1] for u in uris))


# --- Étape 1 : bucket temporaire ----------------------------------------------------

def upload_docs() -> str:
    from google.cloud import storage
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)
    if not bucket.exists():
        bucket.labels = LABELS
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket = client.create_bucket(bucket, location=LOCATION)
    for f in sorted(DOCS.glob("*.md")):
        bucket.blob(f"docs/{f.name}").upload_from_filename(str(f), content_type="text/markdown")
    # L'agent de service RAG Engine (créé par Google) doit pouvoir lire le bucket.
    number = _project_number()
    policy = bucket.get_iam_policy(requested_policy_version=3)
    policy.bindings.append({"role": "roles/storage.objectViewer",
                            "members": {f"serviceAccount:service-{number}@gcp-sa-vertex-rag.iam.gserviceaccount.com"}})
    bucket.set_iam_policy(policy)
    return f"gs://{BUCKET}/docs/"


def _project_number() -> str:
    from google.cloud import resourcemanager_v3
    return resourcemanager_v3.ProjectsClient().get_project(name=f"projects/{PROJECT}").name.split("/")[1]


# --- Étape 2 : base vectorielle, corpus, import ------------------------------------

def _engine_config_name() -> str:
    return f"projects/{PROJECT}/locations/{LOCATION}/ragEngineConfig"


def set_tier(tier: str) -> str:
    """Palier de la base RagManagedDb (Spanner) de la région : « basic » ou « unprovisioned ».
    Basic est facturé en continu tant qu'il n'est pas repassé en Unprovisioned (voir la leçon coûts)."""
    from vertexai import rag
    current = type(rag.get_rag_engine_config(name=_engine_config_name()).rag_managed_db_config.tier).__name__.lower()
    if current != tier:
        cls = {"basic": rag.Basic, "unprovisioned": rag.Unprovisioned}[tier]
        rag.update_rag_engine_config(rag.RagEngineConfig(
            name=_engine_config_name(), rag_managed_db_config=rag.RagManagedDbConfig(tier=cls())))
    return f"{current} -> {tier}"


def create_corpus():
    from vertexai import rag
    return rag.create_corpus(
        display_name=f"{PREFIX}-corpus",
        description="Corpus du lab RAG Engine (documents fictifs). formation-lab=rag-engine",
        backend_config=rag.RagVectorDbConfig(rag_embedding_model_config=rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(publisher_model=EMBEDDING_MODEL))))


def import_docs(corpus_name: str, gcs_uri: str):
    from vertexai import rag
    return rag.import_files(corpus_name, [gcs_uri], transformation_config=chunking(),
                            max_embedding_requests_per_min=300, timeout=900)


def find_corpus():
    from vertexai import rag
    return next((c for c in rag.list_corpora() if c.display_name.startswith(PREFIX)), None)


# --- Étape 3 : recherche seule, puis génération ancrée ----------------------------

def retrieve(corpus_name: str, question: str, top_k: int = 3) -> list[dict]:
    from vertexai import rag
    resp = rag.retrieval_query(
        text=question, rag_resources=[rag.RagResource(rag_corpus=corpus_name)],
        rag_retrieval_config=rag.RagRetrievalConfig(top_k=top_k, filter=rag.Filter(vector_distance_threshold=0.6)))
    return format_contexts(resp)


def answer(corpus_name: str, question: str) -> tuple[str, list[str]]:
    """Gemini appelle lui-même RAG Engine (outil « retrieval ») et renvoie les sources utilisées."""
    from google import genai
    from google.genai import types
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION,
                          http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=5)))
    rag_tool = types.Tool(retrieval=types.Retrieval(vertex_rag_store=types.VertexRagStore(
        rag_resources=[types.VertexRagStoreRagResource(rag_corpus=corpus_name)],
        rag_retrieval_config=types.RagRetrievalConfig(top_k=4))))
    resp = client.models.generate_content(
        model=MODEL, contents=question,
        config=types.GenerateContentConfig(
            tools=[rag_tool], temperature=0,
            system_instruction="Réponds en français, uniquement à partir des documents. "
                               "Si l'information n'y est pas, dis-le."))
    return resp.text.strip(), cited_sources(resp.candidates[0].grounding_metadata)


# --- Étape 4 : nettoyage -------------------------------------------------------------

def cleanup() -> None:
    from google.cloud import storage
    from vertexai import rag
    for c in rag.list_corpora():
        if c.display_name.startswith(PREFIX):
            rag.delete_corpus(name=c.name)
            print("corpus supprimé :", c.name)
    bucket = storage.Client(project=PROJECT).bucket(BUCKET)
    if bucket.exists():
        bucket.delete(force=True)  # force : supprime d'abord les objets (moins de 256)
        print("bucket supprimé :", BUCKET)
    for _ in range(12):  # la suppression met quelques secondes à apparaître dans la liste (vu : < 1 min)
        restants = [c.display_name for c in rag.list_corpora()]
        if not any(n.startswith(PREFIX) for n in restants):
            break
        time.sleep(10)
    if not restants:  # plus aucun corpus dans la région : on coupe la base Spanner (et sa facture)
        print("palier RagManagedDb :", set_tier("unprovisioned"))
    else:
        print("ATTENTION : d'autres corpus existent, la base RagManagedDb reste active :", restants)
    print("vérification : corpus du lab restants =", [n for n in restants if n.startswith(PREFIX)],
          "| bucket existe =", bucket.exists())


def main(argv: list[str]) -> None:
    import vertexai
    if not PROJECT:
        sys.exit("Définissez GOOGLE_CLOUD_PROJECT (voir .env.example).")
    vertexai.init(project=PROJECT, location=LOCATION)
    cmd, question = argv[0], " ".join(argv[1:]) or "Combien de jours de télétravail par semaine ?"
    try:
        run(cmd, question)
    finally:
        if cmd == "all":  # même en cas d'erreur : rien ne doit rester facturé
            cleanup()


def run(cmd: str, question: str) -> None:
    if cmd in ("setup", "all"):
        t = time.time()
        uri = upload_docs()
        print("palier RagManagedDb :", set_tier("basic"))
        corpus = create_corpus()
        print("corpus créé :", corpus.name)
        res = import_docs(corpus.name, uri)
        print(f"import : {res.imported_rag_files_count} fichiers, {res.failed_rag_files_count} échecs, "
              f"{time.time() - t:.0f} s")
    if cmd in ("ask", "all"):
        corpus = find_corpus()
        print("\nQUESTION :", question)
        for c in retrieve(corpus.name, question):
            print(f"  [{c['score']}] {c['source']} : {c['texte'][:90]!r}")
        text, sources = answer(corpus.name, question)
        print("RÉPONSE :", text, "\nSOURCES :", sources)
    if cmd == "cleanup":
        cleanup()


if __name__ == "__main__":
    main(sys.argv[1:] or ["all"])
