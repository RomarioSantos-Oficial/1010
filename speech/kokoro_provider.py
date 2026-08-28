import io
from pathlib import Path
from threading import RLock

import numpy as np
import soundfile as sf

from speech.tts import SynthesizedAudio, TextToSpeech


class KokoroProvider(TextToSpeech):
    """Kokoro TTS using only model and voice files stored on this computer."""

    name = "kokoro"

    def __init__(
        self,
        model_dir: Path,
        voice: str = "pf_dora",
        language: str = "p",
        device: str = "cpu",
        speed: float = 1.0,
        enabled: bool = True,
    ):
        self.model_dir = Path(model_dir)
        self.model_path = self.model_dir / "kokoro-v1_0.pth"
        self.config_path = self.model_dir / "config.json"
        self.voice = voice
        self.voice_gender = "female"
        self.voice_path = self.model_dir / "voices" / f"{voice}.pt"
        self.language = language
        self.device = device
        self.speed = speed
        self.enabled = enabled
        self.repo_id = "hexgrad/Kokoro-82M"
        self._pipeline = None
        self._voice_pack = None
        self._lock = RLock()

    @property
    def ready(self) -> bool:
        return self.enabled and all(
            path.is_file() for path in (self.model_path, self.config_path, self.voice_path)
        )

    def _load(self):
        if not self.enabled:
            raise FileNotFoundError("A voz opcional da Luna está desativada.")
        if not self.ready:
            raise FileNotFoundError(f"Modelo Kokoro não encontrado em {self.model_dir}")
        if self._pipeline is None:
            with self._lock:
                if self._pipeline is None:
                    from kokoro import KModel, KPipeline

                    model = KModel(
                        repo_id=self.repo_id,
                        config=str(self.config_path),
                        model=str(self.model_path),
                    ).to(self.device).eval()
                    pipeline = KPipeline(
                        lang_code=self.language,
                        repo_id=self.repo_id,
                        model=model,
                        device=self.device,
                    )
                    self._voice_pack = pipeline.load_voice(str(self.voice_path))
                    self._pipeline = pipeline
        return self._pipeline, self._voice_pack

    def synthesize(self, text: str) -> SynthesizedAudio:
        clean_text = " ".join(text.split()).strip()
        if not clean_text:
            raise ValueError("O texto para síntese não pode estar vazio.")

        with self._lock:
            pipeline, voice_pack = self._load()
            chunks = []
            for _graphemes, _phonemes, audio in pipeline(
                clean_text,
                voice=voice_pack,
                speed=self.speed,
                split_pattern=r"(?<=[.!?])\s+|\n+",
            ):
                if hasattr(audio, "detach"):
                    audio = audio.detach().cpu().numpy()
                samples = np.asarray(audio, dtype=np.float32).reshape(-1)
                if samples.size:
                    chunks.append(samples)

        if not chunks:
            raise RuntimeError("O Kokoro não produziu áudio para o texto informado.")
        samples = np.concatenate(chunks)
        sample_rate = 24000
        output = io.BytesIO()
        sf.write(output, samples, sample_rate, format="WAV", subtype="PCM_16")
        data = output.getvalue()
        return SynthesizedAudio(
            data=data,
            sample_rate=sample_rate,
            duration=len(samples) / sample_rate,
        )
