import io
from pathlib import Path
from threading import Lock

from speech.stt import SpeechRecognizer, TranscriptionResult, TranscriptionSegment


class FasterWhisperProvider(SpeechRecognizer):
    name = "faster-whisper"

    def __init__(self, model_path: Path, device: str = "cpu", compute_type: str = "int8"):
        self.model_path = Path(model_path)
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._lock = Lock()

    @property
    def ready(self) -> bool:
        return (self.model_path / "model.bin").is_file() and (self.model_path / "config.json").is_file()

    def _load(self):
        if not self.ready:
            raise FileNotFoundError(f"Modelo STT não encontrado em {self.model_path}")
        if self._model is None:
            with self._lock:
                if self._model is None:
                    from faster_whisper import WhisperModel

                    self._model = WhisperModel(
                        str(self.model_path),
                        device=self.device,
                        compute_type=self.compute_type,
                        local_files_only=True,
                    )
        return self._model

    def transcribe(self, audio: bytes, language: str = "pt") -> TranscriptionResult:
        if not audio:
            return TranscriptionResult(text="", language=language)
        segments, info = self._load().transcribe(
            io.BytesIO(audio),
            language=language,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        parsed = [
            TranscriptionSegment(start=float(segment.start), end=float(segment.end), text=segment.text.strip())
            for segment in segments
            if segment.text.strip()
        ]
        text = " ".join(segment.text for segment in parsed).strip()
        duration = float(getattr(info, "duration", parsed[-1].end if parsed else 0.0))
        detected_language = str(getattr(info, "language", language) or language)
        return TranscriptionResult(text=text, language=detected_language, duration=duration, segments=parsed)
