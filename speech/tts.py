from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SynthesizedAudio:
    data: bytes
    sample_rate: int
    duration: float
    media_type: str = "audio/wav"


class TextToSpeech(ABC):
    name = "tts"

    @property
    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, text: str) -> SynthesizedAudio:
        raise NotImplementedError
