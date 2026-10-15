"""Lance un réglage supervisé (supervised fine-tuning) de Gemini sur Vertex AI.

Par défaut : DRY-RUN. Valide les fichiers, estime les tokens facturés, affiche la configuration
exacte qui serait envoyée. Aucun appel réseau, aucun coût.

  python launch_tuning.py                      # dry-run
  python launch_tuning.py --run                # PAYANT : envoie les fichiers sur GCS et crée le job

Variables : GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, TUNING_BASE_MODEL, TUNING_BUCKET
"""
import argparse
import json
import sys
import time

from common import env
from validate_jsonl import validate_file

SLUG = "adapter-modele"
ADAPTER_SIZES = {1: "ADAPTER_SIZE_ONE", 2: "ADAPTER_SIZE_TWO", 4: "ADAPTER_SIZE_FOUR",
                 8: "ADAPTER_SIZE_EIGHT", 16: "ADAPTER_SIZE_SIXTEEN"}


def sdk_objects(plan: dict):
    """Construit les objets du SDK google-genai : une faute de nom de paramètre échoue ICI, sans réseau."""
    from google.genai import types

    return types.TuningDataset(**plan["training_dataset"]), types.CreateTuningJobConfig(**plan["config"])


def build_plan(train_path="train.jsonl", val_path="validation.jsonl", epochs=None, adapter_size=None,
               lr_multiplier=None) -> dict:
    project = env("GOOGLE_CLOUD_PROJECT", "mon-projet")
    errors, train_stats, _ = validate_file(train_path)
    v_errors, val_stats, _ = validate_file(val_path)
    if errors or v_errors:
        raise SystemExit("Jeu de données invalide :\n" + "\n".join(errors + v_errors))
    bucket = env("TUNING_BUCKET", f"lab-{SLUG}-{project}")
    config = {"tuned_model_display_name": f"lab-{SLUG}-tickets",
              "validation_dataset": {"gcs_uri": f"gs://{bucket}/validation.jsonl"},
              "labels": {"formation-lab": SLUG}}
    # None = laisser Vertex AI choisir (recommandé pour un premier essai)
    if epochs:
        config["epoch_count"] = epochs
    if adapter_size:
        config["adapter_size"] = ADAPTER_SIZES[adapter_size]
    if lr_multiplier:
        config["learning_rate_multiplier"] = lr_multiplier
    n_epochs = epochs or 3   # hypothèse pour l'estimation si Vertex choisit lui-même
    return {"project": project, "location": env("GOOGLE_CLOUD_LOCATION", "europe-west1"),
            "base_model": env("TUNING_BASE_MODEL", "gemini-2.5-flash-lite"),
            "training_dataset": {"gcs_uri": f"gs://{bucket}/train.jsonl"},
            "config": config,
            "estimation": {"exemples_train": train_stats["exemples"], "exemples_validation": val_stats["exemples"],
                           "tokens_train": train_stats["tokens_estimes"], "epochs_supposes": n_epochs,
                           "tokens_factures_estimes": train_stats["tokens_estimes"] * n_epochs}}


def run(plan: dict, train_path: str, val_path: str):
    from google import genai
    from google.cloud import storage
    from google.genai import types

    bucket_name = plan["training_dataset"]["gcs_uri"].split("/")[2]
    gcs = storage.Client(project=plan["project"])
    bucket = gcs.bucket(bucket_name)
    if not bucket.exists():
        bucket = gcs.create_bucket(bucket_name, location=plan["location"])
        bucket.labels = {"formation-lab": SLUG}
        bucket.patch()
    bucket.blob("train.jsonl").upload_from_filename(train_path)
    bucket.blob("validation.jsonl").upload_from_filename(val_path)

    client = genai.Client(vertexai=True, project=plan["project"], location=plan["location"])
    training_dataset, config = sdk_objects(plan)
    job = client.tunings.tune(base_model=plan["base_model"], training_dataset=training_dataset, config=config)
    print("job :", job.name)
    while job.state in (types.JobState.JOB_STATE_PENDING, types.JobState.JOB_STATE_RUNNING):
        time.sleep(60)
        job = client.tunings.get(name=job.name)
        print(time.strftime("%H:%M"), job.state)
    print("état final :", job.state)
    if job.tuned_model:
        print("endpoint à utiliser comme MODEL :", job.tuned_model.endpoint)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="train.jsonl")
    ap.add_argument("--validation", default="validation.jsonl")
    ap.add_argument("--epochs", type=int)
    ap.add_argument("--adapter-size", type=int, choices=[1, 2, 4, 8, 16])
    ap.add_argument("--lr-multiplier", type=float)
    ap.add_argument("--run", action="store_true", help="lance VRAIMENT le job (payant)")
    a = ap.parse_args()
    plan = build_plan(a.train, a.validation, a.epochs, a.adapter_size, a.lr_multiplier)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    sdk_objects(plan)   # vérifie les paramètres contre le SDK installé
    if not a.run:
        print("\nDRY-RUN : rien n'a été envoyé. Ajoutez --run pour lancer le job (payant).", file=sys.stderr)
        return
    run(plan, a.train, a.validation)


if __name__ == "__main__":
    main()
