import re

from pydantic import BaseModel


class ValidatedResponse(BaseModel):
    spoken_text: str
    emotion: str = "neutral"
    action: str | None = None
    action_args: dict = {}


class ResponseValidator:
    def validate(self, answer: str) -> ValidatedResponse:
        cleaned = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL | re.IGNORECASE).strip()
        if not cleaned:
            cleaned = "Desculpe, não consegui formular uma resposta agora."
        lowered = cleaned.lower()
        emotion = "happy" if any(word in lowered for word in ("claro", "ótimo", "feliz")) else "neutral"
        return ValidatedResponse(spoken_text=cleaned, emotion=emotion)
