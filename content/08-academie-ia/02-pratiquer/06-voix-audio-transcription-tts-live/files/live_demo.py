"""Conversation en temps réel avec la Live API (WebSocket) : on « parle » à l'agent avec un WAV,
il répond en voix. Mesure la latence entre la fin de la phrase et le premier morceau d'audio.

Usage : python live_demo.py sortie/question.wav sortie/live_reponse.wav
"""
import asyncio
import os
import sys
import time
import wave

import numpy as np

import voix

LIVE_MODEL = os.getenv("LIVE_MODEL", "gemini-3.8-live")
IN_RATE = 16000   # la Live API attend du PCM 16 bits mono à 16 kHz en entrée
CHUNK_MS = 100    # on envoie l'audio par morceaux de 100 ms, comme un micro

SYSTEM = ("Tu es Léa, agente du service client de la boutique Atelier. Réponds en une ou deux phrases, "
          "en français. Tu n'as accès à aucun système : n'invente jamais un statut de commande, "
          "propose plutôt de vérifier et de rappeler.")

QUESTION = "Bonjour, ma commande 4521 n'est toujours pas arrivée. Vous pouvez me dire où elle en est ?"


def to_pcm16k(path: str) -> bytes:
    """Lit un WAV mono 16 bits et le rééchantillonne à 16 kHz (interpolation linéaire)."""
    with wave.open(path) as w:
        rate, pcm = w.getframerate(), np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    if rate != IN_RATE:
        x = np.linspace(0, len(pcm) - 1, int(len(pcm) * IN_RATE / rate))
        pcm = np.interp(x, np.arange(len(pcm)), pcm).astype(np.int16)
    return pcm.tobytes()


def chunks(pcm: bytes, ms: int = CHUNK_MS):
    step = IN_RATE * 2 * ms // 1000  # 2 octets par échantillon
    return [pcm[i:i + step] for i in range(0, len(pcm), step)]


async def converse(question_wav: str, out_wav: str):
    from google.genai import types
    c = voix.client()
    if not os.path.exists(question_wav):  # pas de micro ? on fabrique la question du client en TTS
        os.makedirs(os.path.dirname(question_wav) or ".", exist_ok=True)
        voix.tts(c, QUESTION, question_wav, voice="Puck", style="inquiet")
    cfg = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction=SYSTEM,
        input_audio_transcription=types.AudioTranscriptionConfig(),   # ce que l'API a entendu
        output_audio_transcription=types.AudioTranscriptionConfig(),  # ce qu'elle dit
    )
    speech = chunks(to_pcm16k(question_wav))
    silence = chunks(b"\x00\x00" * IN_RATE)  # 1 s de silence : la détection de fin de parole conclut le tour
    t0 = time.time()
    async with c.aio.live.connect(model=LIVE_MODEL, config=cfg) as session:
        print(f"WebSocket ouvert en {time.time() - t0:.2f} s ({LIVE_MODEL})")
        speech_end = {}

        async def micro():  # simule un micro : envoi en temps réel
            for i, ch in enumerate(speech + silence):
                if i == len(speech):
                    speech_end["t"] = time.time()  # fin de la parole, début du silence
                await session.send_realtime_input(audio=types.Blob(data=ch, mime_type=f"audio/pcm;rate={IN_RATE}"))
                await asyncio.sleep(CHUNK_MS / 1000)

        sender = asyncio.create_task(micro())
        audio, heard, said, first = b"", "", "", None
        async for msg in session.receive():
            sc = msg.server_content
            if msg.data:
                first = first or time.time()
                audio += msg.data
            if sc and sc.input_transcription and sc.input_transcription.text:
                heard += sc.input_transcription.text
            if sc and sc.output_transcription and sc.output_transcription.text:
                said += sc.output_transcription.text
            if sc and sc.turn_complete:
                break
        sender.cancel()

    dur = voix.save_wav(audio, out_wav)
    latency = first - speech_end.get("t", first) if first else None
    print(f"Entendu : {heard.strip()}")
    print(f"Répondu : {said.strip()}")
    print(f"Latence fin de parole -> 1er audio : {latency:.2f} s ; réponse de {dur:.1f} s -> {out_wav}")
    return {"heard": heard, "said": said, "latency": latency}


if __name__ == "__main__":
    asyncio.run(converse(*(sys.argv[1:] or ["sortie/question.wav", "sortie/live_reponse.wav"])))
