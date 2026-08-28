from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TranscriptionSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str = "pt"
    duration: float = 0.0
    segments: list[TranscriptionSegment] = field(default_factory=list)


class SpeechRecognizer(ABC):
    name = "stt"

    @property
    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def transcribe(self, audio: bytes, language: str = "pt") -> TranscriptionResult:
        raise NotImplementedError
