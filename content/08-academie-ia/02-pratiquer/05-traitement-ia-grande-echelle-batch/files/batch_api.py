"""Le même classement en mode « lot » asynchrone : environ moitié prix, résultat différé.

  python batch_api.py gemini --n 20                       # Batch API de l'API Gemini (clé d'API)
  python batch_api.py vertex --n 20 --bucket gs://mon-b   # Vertex AI batch prediction (ADC, GCS)

Les résultats sont écrits au même format que classer.py (resultats_batch.jsonl) :
rapport.py --resultats resultats_batch.jsonl fonctionne tel quel.
"""
import argparse
import json
import os
import re
import time

from dotenv import load_dotenv

from classer import SCHEMA, SYSTEM, ecrire_lot, lire_avis, prompt_lot, valider

load_dotenv()
FINAUX = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED",
          "JOB_STATE_EXPIRED", "JOB_STATE_PARTIALLY_SUCCEEDED"}


def requete(lot: list[dict]) -> dict:
    """Une GenerateContentRequest au format REST (JSON), une par ligne du fichier JSONL."""
    return {
        "contents": [{"role": "user", "parts": [{"text": prompt_lot(lot)}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json",
                             "responseJsonSchema": SCHEMA},
    }


def construire_jsonl(lots: list[list[dict]], chemin: str, avec_cle: bool) -> None:
    with open(chemin, "w", encoding="utf-8") as f:
        for i, lot in enumerate(lots):
            ligne = {"key": f"lot-{i}", "request": requete(lot)} if avec_cle else {"request": requete(lot)}
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")


def lire_reponse(lot: list[dict], reponse: dict) -> dict:
    u = reponse.get("usageMetadata", {})
    texte = reponse["candidates"][0]["content"]["parts"][0]["text"]
    return {"lot": [a["id"] for a in lot], "resultats": valider(lot, texte),
            "tokens_in": u.get("promptTokenCount", 0),
            "tokens_out": u.get("candidatesTokenCount", 0) + u.get("thoughtsTokenCount", 0)}


def attendre(client, nom: str, max_s: int) -> object:
    debut = time.time()
    while True:
        job = client.batches.get(name=nom)
        print(f"  {time.strftime('%H:%M:%S')} {job.state.name}")
        if job.state.name in FINAUX or time.time() - debut > max_s:
            return job
        time.sleep(30)


def via_gemini(lots, sortie, max_s):
    from google import genai
    from google.genai import types

    client = genai.Client()
    construire_jsonl(lots, "requetes_batch.jsonl", avec_cle=True)
    fichier = client.files.upload(file="requetes_batch.jsonl",
                                  config=types.UploadFileConfig(display_name="avis-lot", mime_type="jsonl"))
    job = client.batches.create(model=os.environ.get("MODEL", "gemini-3.5-flash-lite"), src=fichier.name,
                                config={"display_name": "lab-batch-ia-avis"})
    print("Job créé :", job.name)
    job = attendre(client, job.name, max_s)
    if job.state.name != "JOB_STATE_SUCCEEDED":
        print("Pas terminé (relancez plus tard avec batches.get) :", job.state.name)
        return
    contenu = client.files.download(file=job.dest.file_name).decode("utf-8")
    for ligne in contenu.splitlines():
        r = json.loads(ligne)
        lot = lots[int(r["key"].split("-")[1])]  # la clé relie chaque réponse à sa requête
        if "response" in r:
            ecrire_lot(sortie, lire_reponse(lot, r["response"]))
        else:
            print("  erreur sur", r["key"], r.get("error"))
    client.files.delete(name=fichier.name)  # ménage : le fichier d'entrée n'est plus utile


def via_vertex(lots, sortie, max_s, bucket):
    from google import genai
    from google.cloud import storage
    from google.genai import types

    projet, region = os.environ["GOOGLE_CLOUD_PROJECT"], os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
    client = genai.Client(vertexai=True, project=projet, location=region)
    construire_jsonl(lots, "requetes_batch.jsonl", avec_cle=False)
    nom_bucket = bucket.removeprefix("gs://")
    gcs = storage.Client(project=projet).bucket(nom_bucket)
    gcs.blob("entree/requetes.jsonl").upload_from_filename("requetes_batch.jsonl")
    job = client.batches.create(
        model=os.environ.get("MODEL", "gemini-2.5-flash"),
        src=f"{bucket}/entree/requetes.jsonl",
        config=types.CreateBatchJobConfig(dest=f"{bucket}/sortie", display_name="lab-batch-ia-avis"),
    )
    print("Job créé :", job.name)
    job = attendre(client, job.name, max_s)
    if job.state.name != "JOB_STATE_SUCCEEDED":
        print("Pas terminé :", job.state.name, getattr(job, "error", ""))
        return
    par_id = {a["id"]: a for lot in lots for a in lot}
    for blob in gcs.list_blobs(prefix="sortie/"):
        if not blob.name.endswith("predictions.jsonl"):
            continue
        for ligne in blob.download_as_text().splitlines():
            r = json.loads(ligne)
            # Vertex renvoie la requête avec la réponse : on y relit les ids du lot
            texte = r["request"]["contents"][0]["parts"][0]["text"]
            lot = [par_id[i] for i in re.findall(r"^\[(\w+)\]", texte, flags=re.M)]
            if r.get("response"):
                ecrire_lot(sortie, lire_reponse(lot, r["response"]))
            else:
                print("  erreur :", r.get("status"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["gemini", "vertex"])
    ap.add_argument("--n", type=int, default=20, help="nombre d'avis (petit lot pour tester)")
    ap.add_argument("--lot", type=int, default=10)
    ap.add_argument("--entree", default="avis.csv")
    ap.add_argument("--sortie", default="resultats_batch.jsonl")
    ap.add_argument("--bucket", help="gs://... (mode vertex)")
    ap.add_argument("--max-attente", type=int, default=1800, help="secondes avant d'arrêter d'attendre")
    a = ap.parse_args()
    avis = lire_avis(a.entree)[: a.n]
    lots = [avis[i:i + a.lot] for i in range(0, len(avis), a.lot)]
    if a.mode == "gemini":
        via_gemini(lots, a.sortie, a.max_attente)
    else:
        via_vertex(lots, a.sortie, a.max_attente, a.bucket)


if __name__ == "__main__":
    main()
