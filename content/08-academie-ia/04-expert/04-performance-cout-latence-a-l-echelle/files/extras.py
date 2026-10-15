"""Trois mesures complémentaires au banc (quelques appels chacune).

  python extras.py tokens   # compression du prompt : count_tokens avant / après
  python extras.py cache    # cache de contexte explicite : créer, utiliser, supprimer
  python extras.py batch    # API Batch : 2 requêtes à -50 %, résultat différé
"""
import re
import sys
import time

from dotenv import load_dotenv

import router as R


def sections(kb: str) -> dict:
    """Découpe la FAQ en {titre: texte} sur les lignes '## '."""
    parts = re.split(r"^## ", kb, flags=re.M)[1:]
    return {p.split("\n", 1)[0].strip(): p.split("\n", 1)[1] for p in parts}


def compact(kb: str) -> str:
    """Compression sans perte d'information utile : puces, titres et espaces en trop."""
    kb = re.sub(r"^# .*\n", "", kb, flags=re.M)
    kb = re.sub(r"^- ", "", kb, flags=re.M)
    return re.sub(r"\n{2,}", "\n", kb).strip()


def tokens(client):
    base = R.SYSTEM.split("\n\n")[0]
    variants = {
        "FAQ complète (markdown)": R.SYSTEM,
        "FAQ complète compactée": base + "\n" + compact(R.KB),
        "Section « Livraison » seule": base + "\n" + sections(R.KB)["Livraison"],
    }
    for name, text in variants.items():
        n = client.models.count_tokens(model=R.SMALL_MODEL, contents=text).total_tokens
        print(f"{name:30} {n:6d} tokens")


def cache(client, repeat: int = 2):
    from google.genai import types

    # Notre FAQ (~1 000 tokens) est sous le minimum du cache explicite (1 024 tokens pour ce modèle
    # le 2026-10-15) : pour la démo, on la répète. En vrai, on cache un gros contexte (> 10 000 tokens).
    try:
        c = client.caches.create(model=R.SMALL_MODEL, config=types.CreateCachedContentConfig(
            system_instruction="\n\n".join([R.SYSTEM] * repeat), ttl="300s", display_name="lab-perf-faq"))
    except Exception as e:  # trop peu de tokens pour le minimum du modèle, modèle non éligible...
        print("Création du cache refusée :", str(e)[:200])
        return
    try:
        r = client.models.generate_content(
            model=R.SMALL_MODEL, contents="Combien coûte la livraison express ?",
            config=types.GenerateContentConfig(cached_content=c.name))
        u = r.usage_metadata
        print(f"cache={c.name.split('/')[-1][:6]}... prompt={u.prompt_token_count} "
              f"dont en cache={u.cached_content_token_count}\n-> {r.text.strip()[:120]}")
    finally:
        client.caches.delete(name=c.name)  # le stockage du cache est facturé à l'heure
        print("cache supprimé")


def batch(client):
    reqs = [{"contents": [{"role": "user", "parts": [{"text": R.SYSTEM + "\n\nQuestion : " + q}]}]}
            for q in ["Livrez-vous en Belgique ?", "Quelle garantie pour une ampoule LED ?"]]
    job = client.batches.create(model=R.SMALL_MODEL, src=reqs, config={"display_name": "lab-perf-batch"})
    t0 = time.time()
    while job.state.name not in ("JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED",
                                 "JOB_STATE_EXPIRED") and time.time() - t0 < 900:
        time.sleep(20)
        job = client.batches.get(name=job.name)
    print(f"état={job.state.name} après {time.time() - t0:.0f} s")
    if job.state.name == "JOB_STATE_SUCCEEDED":
        for r in job.dest.inlined_responses:
            print("->", r.response.text.strip()[:120])
    elif job.state.name not in ("JOB_STATE_FAILED", "JOB_STATE_CANCELLED"):
        client.batches.cancel(name=job.name)
        print("job annulé (trop long pour une démo)")


if __name__ == "__main__":
    load_dotenv()
    from google import genai

    {"tokens": tokens, "cache": cache, "batch": batch}[sys.argv[1]](genai.Client())
