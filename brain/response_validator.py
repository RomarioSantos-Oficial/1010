import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

from memory.schemas import MemoryCandidate

ALLOWED_ACTIONS = frozenset({
    "get_product",
    "get_stock",
    "get_product_guide",
    "search_products",
    "recommend_products",
})
ALLOWED_EMOTIONS = frozenset({"neutral", "happy", "sad", "surprised", "thinking"})
NO_ACTION_VALUES = frozenset({"", "none", "null", "no_action", "nenhuma"})


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
        if cleaned.startswith("{"):
            return ValidatedResponse(
                spoken_text="Desculpe, não consegui estruturar uma resposta válida agora.",
            )
        if not cleaned:
            cleaned = "Desculpe, não consegui formular uma resposta agora."
        return ValidatedResponse(spoken_text=cleaned)

    @staticmethod
    def _parse_json(text: str) -> ValidatedResponse | None:
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
        if not candidate.startswith("{"):
            return None
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        spoken_text = payload.get("spoken_text")
        if not isinstance(spoken_text, str) or not spoken_text.strip():
            return None

        emotion = payload.get("emotion", "neutral")
        if emotion not in ALLOWED_EMOTIONS:
            emotion = "neutral"

        gesture = payload.get("gesture")
        if not isinstance(gesture, str):
            gesture = None

        raw_action = payload.get("action")
        action = raw_action.strip().casefold() if isinstance(raw_action, str) else None
        if action in NO_ACTION_VALUES or action not in ALLOWED_ACTIONS:
            action = None
        action_args = payload.get("action_args") if action else {}
        if not isinstance(action_args, dict):
            action_args = {}

        memories: list[MemoryCandidate] = []
        candidates = payload.get("memory_candidates", [])
        if isinstance(candidates, list):
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                try:
                    memories.append(MemoryCandidate.model_validate(item))
                except ValidationError:
                    continue

        return ValidatedResponse(
            spoken_text=spoken_text.strip()[:5000],
            emotion=emotion,
            gesture=gesture,
            action=action,
            action_args=action_args,
            memory_candidates=memories,
        )
