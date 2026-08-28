from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TypedDict


class Message(TypedDict):
    role: str
    content: str


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: Sequence[Message]) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

