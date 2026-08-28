import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from memory.schemas import MemoryCandidate


class ValidatedResponse(BaseModel):
    spoken_text: str = Field(min_length=1, max_length=5000)
    emotion: Literal["neutral", "happy", "sad", "surprised", "thinking"] = "neutral"
    gesture: str | None = None
    action: str | None = Field(default=None, pattern=r"^[a-z_]+$")
    action_args: dict[str, Any] = Field(default_factory=dict)
    memory_candidates: list[MemoryCandidate] = Field(default_factory=list)


class ResponseValidator:
    def validate(self, answer: str) -> ValidatedResponse:
        cleaned = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL | re.IGNORECASE).strip()
        structured = self._parse_json(cleaned)
        if structured:
            return structured
        if not cleaned:
            cleaned = "Desculpe, não consegui formular uma resposta agora."
        return ValidatedResponse(spoken_text=cleaned)

    @staticmethod
    def _parse_json(text: str) -> ValidatedResponse | None:
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
        if not candidate.startswith("{"):
            return None
        try:
            return ValidatedResponse.model_validate(json.loads(candidate))
        except (json.JSONDecodeError, ValidationError):
            return None
