"""Lab Vertex AI Search : bucket GCS -> data store -> application -> recherche filtrée + réponse citée -> nettoyage.

Usage (identifiants ADC : `gcloud auth application-default login`) :
    python vais_lab.py setup        # bucket, data store (schéma + import), application de recherche
    python vais_lab.py wait         # attend que l'index réponde (quelques minutes)
    python vais_lab.py ask "Combien de jours de télétravail ?" ['annee >= 2026']
    python vais_lab.py cleanup      # supprime application, data store, bucket et vérifie
"""

import json
import os
import sys
import time
import warnings
from pathlib import Path

from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import NotFound
from google.cloud import discoveryengine_v1 as de

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("SEARCH_LOCATION", "eu")  # Vertex AI Search : global, eu ou us (pas de région seule)
BUCKET_LOCATION = os.environ.get("BUCKET_LOCATION", "europe-west1")
PREFIX = "lab-vais"
LABELS = {"formation-lab": "vertex-ai-search"}
BUCKET = os.environ.get("BUCKET") or f"{PREFIX}-{PROJECT}"
DATA_STORE_ID = f"{PREFIX}-docs"
ENGINE_ID = f"{PREFIX}-app"
DOCS = Path(__file__).with_name("docs")

# Métadonnées de chaque document : elles deviennent des champs filtrables.
METADATA = {
    "politique-teletravail": {"titre": "Politique de télétravail (v3)", "categorie": "rh", "annee": 2026},
    "politique-teletravail-2024": {"titre": "Politique de télétravail (v2, ancienne)", "categorie": "rh", "annee": 2024},
    "notes-de-frais": {"titre": "Procédure notes de frais", "categorie": "finance", "annee": 2026},
    "securite-informatique": {"titre": "Charte de sécurité informatique", "categorie": "securite", "annee": 2026},
    "onboarding": {"titre": "Guide d'accueil", "categorie": "rh", "annee": 2025},
}

# Schéma : « indexable » rend un champ filtrable, « retrievable » le renvoie dans les résultats,
# keyPropertyMapping=title en fait le titre affiché (champ clé : ni « searchable » ni « indexable », vérifié).
SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
    "properties": {
        "titre": {"type": "string", "retrievable": True, "keyPropertyMapping": "title"},
        "categorie": {"type": "string", "retrievable": True, "indexable": True, "dynamicFacetable": True},
        "annee": {"type": "number", "retrievable": True, "indexable": True},
    },
}

# quota_project_id : avec des identifiants ADC « utilisateur », cette API exige un projet de quota explicite (vérifié).
OPTS = ClientOptions(api_endpoint=f"{LOCATION}-discoveryengine.googleapis.com" if LOCATION != "global" else None,
                     quota_project_id=PROJECT)
COLLECTION = f"projects/{PROJECT}/locations/{LOCATION}/collections/default_collection"
DATA_STORE = f"{COLLECTION}/dataStores/{DATA_STORE_ID}"
ENGINE = f"{COLLECTION}/engines/{ENGINE_ID}"


def jsonl_lines(bucket: str, names: list[str]) -> str:
    """Un document par ligne : identifiant, métadonnées (structData) et lien vers le contenu dans GCS."""
    return "\n".join(json.dumps({
        "id": n, "structData": METADATA[n],
        "content": {"mimeType": "text/plain", "uri": f"gs://{bucket}/docs/{n}.txt"},
    }, ensure_ascii=False) for n in names)


def build_filter(categorie: str | None = None, annee_min: int | None = None) -> str:
    """Filtre Vertex AI Search à partir de valeurs contrôlées (jamais du texte libre de l'utilisateur)."""
    parts = []
    if categorie:
        if not categorie.isalnum():
            raise ValueError(f"catégorie invalide : {categorie!r}")
        parts.append(f'categorie: ANY("{categorie}")')
    if annee_min is not None:
        parts.append(f"annee >= {int(annee_min)}")
    return " AND ".join(parts)


def search_request(query: str, filtre: str = "") -> de.SearchRequest:
    """Recherche « classique » : documents classés + extraits, filtrés sur les métadonnées."""
    spec = de.SearchRequest.ContentSearchSpec
    return de.SearchRequest(
        serving_config=f"{ENGINE}/servingConfigs/default_search", query=query, page_size=5, filter=filtre,
        content_search_spec=spec(snippet_spec=spec.SnippetSpec(return_snippet=True)))


def answer_request(query: str, filtre: str = "") -> de.AnswerQueryRequest:
    """Réponse générée (résumé) avec citations, sur les documents qui passent le filtre."""
    R = de.AnswerQueryRequest
    return R(
        serving_config=f"{ENGINE}/servingConfigs/default_search", query=de.Query(text=query),
        search_spec=R.SearchSpec(search_params=R.SearchSpec.SearchParams(max_return_results=3, filter=filtre)),
        answer_generation_spec=R.AnswerGenerationSpec(
            include_citations=True, answer_language_code="fr",
            ignore_non_answer_seeking_query=True, ignore_adversarial_query=True, ignore_low_relevant_content=True))


def parse_search(resp) -> list[dict]:
    return [{"id": r.document.id, "titre": r.document.struct_data.get("titre"),
             "annee": int(r.document.struct_data.get("annee", 0))} for r in resp.results]


def ref_title(ref) -> str:
    """Titre d'une référence : morceau (chunk_info, le cas observé ici) ou document entier."""
    if ref.chunk_info.content:
        meta = ref.chunk_info.document_metadata
        return meta.title or meta.uri.rsplit("/", 1)[-1]
    info = ref.unstructured_document_info
    return info.title or info.uri.rsplit("/", 1)[-1]


def parse_answer(ans) -> dict:
    """Texte de la réponse, puis chaque passage cité avec le(s) document(s) source(s)."""
    titres = [ref_title(r) for r in ans.references]
    citations = [{"passage": ans.answer_text[c.start_index:c.end_index].strip()[:80],
                  "sources": sorted({titres[int(x.reference_id)] for x in c.sources if int(x.reference_id) < len(titres)})}
                 for c in ans.citations]
    return {"reponse": ans.answer_text, "citations": citations, "sources": list(dict.fromkeys(t for c in citations for t in c["sources"])),  # cités, pas seulement lus
            "ignoree": [de.Answer.AnswerSkippedReason(x).name for x in ans.answer_skipped_reasons]}


# --- setup ---------------------------------------------------------------------------

def upload_docs() -> str:
    from google.cloud import storage
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)
    if not bucket.exists():
        bucket.labels = LABELS
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket = client.create_bucket(bucket, location=BUCKET_LOCATION)
    names = sorted(METADATA)
    for n in names:
        bucket.blob(f"docs/{n}.txt").upload_from_filename(str(DOCS / f"{n}.txt"), content_type="text/plain")
    bucket.blob("metadata.jsonl").upload_from_string(jsonl_lines(BUCKET, names), content_type="application/json")
    # L'agent de service de Vertex AI Search (créé par Google) doit lire le bucket et y écrire le rapport
    # d'erreurs d'import (vérifié : 403 sinon, il tente de créer son propre bucket de travail).
    from google.cloud import resourcemanager_v3
    number = resourcemanager_v3.ProjectsClient().get_project(name=f"projects/{PROJECT}").name.split("/")[1]
    policy = bucket.get_iam_policy(requested_policy_version=3)
    agent = f"serviceAccount:service-{number}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
    for role in ("roles/storage.objectAdmin", "roles/storage.legacyBucketReader"):  # objets + storage.buckets.get
        policy.bindings.append({"role": role, "members": {agent}})
    bucket.set_iam_policy(policy)
    return f"gs://{BUCKET}/metadata.jsonl"


def setup() -> None:
    t = time.time()
    uri = upload_docs()
    print("bucket :", uri)
    ds_client = de.DataStoreServiceClient(client_options=OPTS)
    try:
        ds = ds_client.get_data_store(name=DATA_STORE)  # relance de setup : on garde l'existant
    except NotFound:
        ds = ds_client.create_data_store(
            parent=COLLECTION, data_store_id=DATA_STORE_ID,
            data_store=de.DataStore(
                display_name=DATA_STORE_ID, industry_vertical=de.IndustryVertical.GENERIC,
                solution_types=[de.SolutionType.SOLUTION_TYPE_SEARCH],
                content_config=de.DataStore.ContentConfig.CONTENT_REQUIRED,
                starting_schema=de.Schema(json_schema=json.dumps(SCHEMA)))).result(timeout=600)
    print("data store :", ds.name)
    op = de.DocumentServiceClient(client_options=OPTS).import_documents(de.ImportDocumentsRequest(
        parent=f"{DATA_STORE}/branches/default_branch",
        gcs_source=de.GcsSource(input_uris=[uri], data_schema="document"),
        error_config=de.ImportErrorConfig(gcs_prefix=f"gs://{BUCKET}/import-errors/"),
        reconciliation_mode=de.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL))
    res = op.result(timeout=1800)
    print(f"import : {op.metadata.success_count} réussis, {op.metadata.failure_count} échecs",
          [e.message for e in res.error_samples][:2])
    eng_client = de.EngineServiceClient(client_options=OPTS)
    try:
        eng = eng_client.get_engine(name=ENGINE)
    except NotFound:
        eng = eng_client.create_engine(
            parent=COLLECTION, engine_id=ENGINE_ID,
            engine=de.Engine(
                display_name=ENGINE_ID, solution_type=de.SolutionType.SOLUTION_TYPE_SEARCH,
                industry_vertical=de.IndustryVertical.GENERIC, data_store_ids=[DATA_STORE_ID],
                search_engine_config=de.Engine.SearchEngineConfig(
                    search_tier=de.SearchTier.SEARCH_TIER_ENTERPRISE,       # requis pour les réponses générées
                    search_add_ons=[de.SearchAddOn.SEARCH_ADD_ON_LLM]))).result(timeout=600)
    print(f"application : {eng.name} ({time.time() - t:.0f} s)")


def ask(query: str, filtre: str = "") -> dict:
    docs = parse_search(de.SearchServiceClient(client_options=OPTS).search(search_request(query, filtre)))
    ans = de.ConversationalSearchServiceClient(client_options=OPTS).answer_query(answer_request(query, filtre)).answer
    return {"documents": docs, **parse_answer(ans)}


def wait(max_minutes: int = 20) -> None:
    """Interroge jusqu'à ce que les 5 documents soient trouvables (l'indexation suit l'import)."""
    t = time.time()
    while time.time() - t < max_minutes * 60:
        n = len(parse_search(de.SearchServiceClient(client_options=OPTS).search(search_request("Nimbus Conseil"))))
        print(f"{time.time() - t:4.0f} s : {n} documents trouvés")
        if n >= len(METADATA):
            return
        time.sleep(30)
    print("index incomplet après", max_minutes, "min")


def cleanup() -> None:
    from google.cloud import storage
    engines, stores = de.EngineServiceClient(client_options=OPTS), de.DataStoreServiceClient(client_options=OPTS)
    # L'application d'abord : un data store rattaché à une application ne peut pas être supprimé.
    for label, delete, get, name in [("application", engines.delete_engine, engines.get_engine, ENGINE),
                                     ("data store", stores.delete_data_store, stores.get_data_store, DATA_STORE)]:
        try:
            delete(name=name)  # opération longue : on ne lit pas son résultat (vide, le SDK le refuse — vérifié)
        except NotFound:
            print(label, "déjà absent(e)")
            continue
        for _ in range(90):  # on attend que la ressource ait vraiment disparu (max 15 min)
            try:
                get(name=name)
                time.sleep(10)
            except NotFound:
                print(label, "supprimé(e)")
                break
    bucket = storage.Client(project=PROJECT).bucket(BUCKET)
    if bucket.exists():
        bucket.delete(force=True)
        print("bucket supprimé :", BUCKET)
    print("vérification : applications =", [e.name for e in engines.list_engines(parent=COLLECTION) if PREFIX in e.name],
          "| data stores =", [d.name for d in stores.list_data_stores(parent=COLLECTION) if PREFIX in d.name],
          "| bucket existe =", bucket.exists())


if __name__ == "__main__":
    if not PROJECT:
        sys.exit("Définissez GOOGLE_CLOUD_PROJECT (voir .env.example).")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "setup"
    if cmd == "setup":
        setup()
    elif cmd == "wait":
        wait()
    elif cmd == "ask":
        out = ask(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif cmd == "cleanup":
        cleanup()
