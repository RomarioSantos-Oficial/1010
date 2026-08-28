import asyncio
from types import SimpleNamespace

import numpy as np

from speech.faster_whisper_provider import FasterWhisperProvider
from speech.kokoro_provider import KokoroProvider
from speech.stt import TranscriptionResult
from speech.tts import SynthesizedAudio
from speech.vad import EnergyVoiceActivityDetector
from speech.voice_loop import VoiceLoop


def test_vad_rejects_silence_and_accepts_voice_like_signal():
    vad = EnergyVoiceActivityDetector()
    silence = np.zeros(16000, dtype=np.float32)
    time = np.arange(16000, dtype=np.float32) / 16000
    voice_like = 0.08 * np.sin(2 * np.pi * 180 * time)
    assert not vad.contains_speech(silence, 16000)
    assert vad.contains_speech(voice_like, 16000)


def test_faster_whisper_empty_audio_does_not_load_model(tmp_path):
    stt = FasterWhisperProvider(tmp_path / "missing")
    assert not stt.ready
    assert stt.transcribe(b"").text == ""


def test_kokoro_voice_is_female_primary_and_can_be_disabled(tmp_path):
    tts = KokoroProvider(tmp_path, voice="pf_dora", enabled=False)
    assert tts.voice == "pf_dora"
    assert tts.voice_gender == "female"
    assert not tts.ready


def test_voice_loop_blocks_microphone_feedback():
    samples = np.full(16000, 0.08, dtype=np.float32)

    class Microphone:
        sample_rate = 16000

        def record(self, _seconds):
            return samples

        def to_wav(self, _samples):
            return b"wav"

    class STT:
        def transcribe(self, _audio, _language):
            return TranscriptionResult(text="Olá Luna")

    class Brain:
        async def process(self, _user_id, _text):
            return SimpleNamespace(spoken_text="Olá! Como posso ajudar?")

    class TTS:
        def synthesize(self, _text):
            return SynthesizedAudio(b"audio", 22050, 1.0)

    observed = []

    class Player:
        def play(self, _audio, _blocking):
            observed.append(loop.speaking)

    loop = VoiceLoop(Microphone(), EnergyVoiceActivityDetector(), STT(), Brain(), TTS(), Player())
    result = asyncio.run(loop.run_once("teste", 1.0))
    assert result.transcript == "Olá Luna"
    assert observed == [True]
    assert not loop.speaking
