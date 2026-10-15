"""Lab « compte rendu d'appel » : faux appel en TTS -> transcription + diarisation -> compte rendu -> réponse vocale.

Usage : python compte_rendu.py [appel_fictif.json] [dossier_sortie]
"""
import json
import os
import sys
import time

import voix


def main(script_path="appel_fictif.json", out="sortie"):
    os.makedirs(out, exist_ok=True)
    script = json.load(open(script_path, encoding="utf-8"))
    c = voix.client()
    timings = {}

    t = time.time()
    dur = voix.tts_dialogue(c, script["lines"], script["voices"], f"{out}/appel.wav")
    timings["1_tts_appel"] = time.time() - t
    print(f"[1] appel.wav : {dur:.1f} s d'audio ({voix.TTS_MODEL})")

    t = time.time()
    segments = voix.transcribe(c, f"{out}/appel.wav")
    timings["2_transcription"] = time.time() - t
    voix.dump(segments, f"{out}/transcription.json")
    print(f"[2] transcription ({voix.STT_MODEL}) : {len(segments)} tours de parole")
    print(voix.as_text(segments))

    reference = " ".join(l["text"] for l in script["lines"])
    hypothesis = " ".join(s["text"] for s in segments)
    score = voix.wer(reference, hypothesis)
    print(f"    WER (taux d'erreur sur les mots) : {score:.1%}")

    t = time.time()
    cr = voix.summarize(c, segments)
    timings["3_compte_rendu"] = time.time() - t
    voix.dump(cr.model_dump(), f"{out}/compte_rendu.json")
    print(f"[3] compte rendu ({voix.MODEL}) :")
    print(json.dumps(cr.model_dump(), ensure_ascii=False, indent=2))
    # Garde-fou : un chiffre mal entendu est l'erreur la plus coûteuse. On vérifie dans le SI
    # (ici une simple liste) avant d'agir ; sinon on fait confirmer par un humain.
    known = script.get("commandes_connues", [])
    to_confirm = cr.numero_commande not in known
    if to_confirm:
        print(f"    ATTENTION : commande {cr.numero_commande!r} inconnue du SI -> à confirmer par un conseiller")

    t = time.time()
    dur = voix.tts(c, cr.reponse_vocale, f"{out}/reponse.wav", voice="Kore", style="chaleureuse, posée")
    timings["4_tts_reponse"] = time.time() - t
    print(f"[4] reponse.wav : {dur:.1f} s d'audio")

    print("Durées (s) :", {k: round(v, 1) for k, v in timings.items()})
    return {"segments": segments, "wer": score, "compte_rendu": cr, "a_confirmer": to_confirm}


if __name__ == "__main__":
    main(*sys.argv[1:])
