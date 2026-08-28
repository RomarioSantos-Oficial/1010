import asyncio
from dataclasses import dataclass
from threading import Event

from core.orchestrator import Orchestrator
from speech.audio_player import AudioPlayer
from speech.microphone import MicrophoneRecorder
from speech.stt import SpeechRecognizer
from speech.tts import TextToSpeech
from speech.vad import EnergyVoiceActivityDetector


@dataclass(frozen=True)
class VoiceTurn:
    transcript: str
    response: str


class VoiceLoop:
    """Ciclo local que mantém o microfone bloqueado durante a fala da Luna."""

    def __init__(
        self,
        microphone: MicrophoneRecorder,
        vad: EnergyVoiceActivityDetector,
        stt: SpeechRecognizer,
        orchestrator: Orchestrator,
        tts: TextToSpeech,
        player: AudioPlayer,
    ):
        self.microphone = microphone
        self.vad = vad
        self.stt = stt
        self.orchestrator = orchestrator
        self.tts = tts
        self.player = player
        self._speaking = Event()

    @property
    def speaking(self) -> bool:
        return self._speaking.is_set()

    async def run_once(self, user_id: str, record_seconds: float = 5.0) -> VoiceTurn | None:
        if self.speaking:
            return None
        samples = await asyncio.to_thread(self.microphone.record, record_seconds)
        if not self.vad.contains_speech(samples, self.microphone.sample_rate):
            return None
        wav_data = self.microphone.to_wav(samples)
        transcription = await asyncio.to_thread(self.stt.transcribe, wav_data, "pt")
        if not transcription.text:
            return None
        answer = await self.orchestrator.process(user_id, transcription.text)
        audio = await asyncio.to_thread(self.tts.synthesize, answer.spoken_text)
        self._speaking.set()
        try:
            await asyncio.to_thread(self.player.play, audio.data, True)
        finally:
            self._speaking.clear()
        return VoiceTurn(transcript=transcription.text, response=answer.spoken_text)
