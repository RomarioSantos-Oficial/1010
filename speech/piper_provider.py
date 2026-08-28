import io
import wave
from pathlib import Path
from threading import RLock

from speech.tts import SynthesizedAudio, TextToSpeech


class PiperProvider(TextToSpeech):
    name = "piper"

    def __init__(self, model_path: Path, use_cuda: bool = False, length_scale: float = 1.0):
        self.model_path = Path(model_path)
        self.config_path = Path(f"{self.model_path}.json")
        self.use_cuda = use_cuda
        self.length_scale = length_scale
        self.enabled = True
        self.voice = self.model_path.stem
        self.voice_gender = "unspecified"
        self._voice = None
        self._lock = RLock()

    @property
    def ready(self) -> bool:
        return self.enabled and self.model_path.is_file() and self.config_path.is_file()

    def _load(self):
        if not self.enabled:
            raise FileNotFoundError("A voz opcional da Luna está desativada.")
        if not self.ready:
            raise FileNotFoundError(f"Modelo TTS não encontrado em {self.model_path}")
        if self._voice is None:
            with self._lock:
                if self._voice is None:
                    from piper import PiperVoice

                    self._voice = PiperVoice.load(
                        self.model_path,
                        config_path=self.config_path,
                        use_cuda=self.use_cuda,
                    )
        return self._voice

    def synthesize(self, text: str) -> SynthesizedAudio:
        clean_text = " ".join(text.split()).strip()
        if not clean_text:
            raise ValueError("O texto para síntese não pode estar vazio.")
        from piper import SynthesisConfig

        output = io.BytesIO()
        with self._lock:
            with wave.open(output, "wb") as wav_file:
                self._load().synthesize_wav(
                    clean_text,
                    wav_file,
                    syn_config=SynthesisConfig(length_scale=self.length_scale),
                )
        data = output.getvalue()
        with wave.open(io.BytesIO(data), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            duration = wav_file.getnframes() / max(1, sample_rate)
        return SynthesizedAudio(data=data, sample_rate=sample_rate, duration=duration)
