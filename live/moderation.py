import re
from dataclasses import dataclass

from safety.content_policy import ContentSafetyPolicy


@dataclass(frozen=True)
class ModerationDecision:
    allowed: bool
    code: str | None = None
    message: str | None = None


class LiveModeration:
    hard_block_codes = frozenset({"minor", "deceased", "coercion", "mutilation", "homicide_instruction"})

    def __init__(self, safety: ContentSafetyPolicy, max_length: int = 500):
        self.safety = safety
        self.max_length = max_length

    def evaluate(self, user_id: str, text: str) -> ModerationDecision:
        clean = text.strip()
        if not clean:
            return ModerationDecision(False, "empty", "Comentário vazio.")
        if len(clean) > self.max_length:
            return ModerationDecision(False, "too_long", "Comentário acima do limite da live.")
        if len(re.findall(r"https?://|www\.", clean.casefold())) > 1:
            return ModerationDecision(False, "spam", "Comentário identificado como spam.")
        if re.search(r"(.)\1{11,}", clean.casefold()):
            return ModerationDecision(False, "spam", "Comentário identificado como spam.")
        safety = self.safety.evaluate(user_id, clean)
        if not safety.allowed and safety.code in self.hard_block_codes:
            return ModerationDecision(False, safety.code, safety.message)
        return ModerationDecision(True)
