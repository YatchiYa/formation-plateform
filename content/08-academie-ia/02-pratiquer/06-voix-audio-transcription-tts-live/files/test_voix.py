"""Tests sans clé ni réseau : python -m pytest -q"""
import io
import json
import wave
from types import SimpleNamespace as NS

import compte_rendu
import live_demo
import voix


def pcm(seconds, rate=24000):
    return b"\x01\x00" * int(seconds * rate)


def test_save_wav_wraps_raw_pcm(tmp_path):
    dur = voix.save_wav(pcm(1.5), tmp_path / "a.wav")
    with wave.open(str(tmp_path / "a.wav")) as w:
        assert (w.getnchannels(), w.getsampwidth(), w.getframerate()) == (1, 2, 24000)
    assert abs(dur - 1.5) < 1e-6


def test_save_wav_keeps_existing_wav(tmp_path):
    voix.save_wav(pcm(1), tmp_path / "a.wav")
    data = (tmp_path / "a.wav").read_bytes()
    voix.save_wav(data, tmp_path / "b.wav")  # déjà un WAV : pas de double en-tête
    assert (tmp_path / "b.wav").read_bytes() == data


def test_segments_merge_same_speaker():
    part = lambda spk, txt: NS(audio_transcription=NS(speaker_label=spk, text=txt))
    parts = [part("spk:0", "Bonjour."), part("spk:0", "Léa à l'appareil."), part("spk:1", "Bonjour"),
             NS(audio_transcription=None)]
    assert voix.segments_from_parts(parts) == [
        {"speaker": "spk:0", "text": "Bonjour. Léa à l'appareil."}, {"speaker": "spk:1", "text": "Bonjour"}]


def test_wer():
    assert voix.wer("ça fait dix jours", "Ça fait dix jours !") == 0
    assert voix.wer("ça fait dix jours", "ça fait 10 jours") == 0.25   # une substitution sur 4 mots
    assert voix.wer("a b c", "a c") == 1 / 3                            # une suppression


def test_resample_and_chunks(tmp_path):
    voix.save_wav(pcm(1), tmp_path / "q.wav")
    out = live_demo.to_pcm16k(str(tmp_path / "q.wav"))
    assert len(out) == 16000 * 2
    assert [len(c) for c in live_demo.chunks(out)] == [3200] * 10


class FakeModels:
    """Faux client : renvoie de l'audio pour le TTS, des segments pour le STT, du JSON pour le résumé."""
    def __init__(self):
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        if model == voix.TTS_MODEL:
            return NS(candidates=[NS(content=NS(parts=[NS(inline_data=NS(data=pcm(0.5)))]))])
        if model == voix.STT_MODEL:
            seg = lambda s, t: NS(audio_transcription=NS(speaker_label=s, text=t))
            return NS(candidates=[NS(content=NS(parts=[seg("spk:0", "Bonjour, service client."),
                                                      seg("spk:1", "Ma commande 4521 n'est pas arrivée.")]))])
        return NS(text=json.dumps({
            "role_agent": "spk:0", "motif": "retard de livraison", "numero_commande": "4521",
            "sentiment_client": "mécontent", "actions": ["renvoi express"], "resume": "Colis bloqué.",
            "reponse_vocale": "Bonjour, votre nouvelle lampe part aujourd'hui."}))


def test_pipeline_with_fake_client(tmp_path, monkeypatch):
    fake = NS(models=FakeModels())
    monkeypatch.setattr(voix, "client", lambda: fake)
    script = tmp_path / "appel.json"
    script.write_text(json.dumps({"voices": {"Agent": "Kore", "Client": "Puck"},
                                  "lines": [{"speaker": "Agent", "text": "Bonjour, service client."}]}))
    res = compte_rendu.main(str(script), str(tmp_path / "out"))
    assert res["compte_rendu"].numero_commande == "4521"
    assert res["a_confirmer"]  # aucune commande connue dans ce script de test
    assert fake.models.calls == [voix.TTS_MODEL, voix.STT_MODEL, voix.MODEL, voix.TTS_MODEL]
    for f in ["appel.wav", "reponse.wav", "transcription.json", "compte_rendu.json"]:
        assert (tmp_path / "out" / f).exists()


def test_retry_on_429(monkeypatch):
    monkeypatch.setattr(voix.time, "sleep", lambda s: None)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise type("E", (Exception,), {"code": 429})()
        return "ok"
    assert voix.with_retry(flaky) == "ok" and len(calls) == 3
