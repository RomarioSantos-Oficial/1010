from dataclasses import dataclass

from safety.content_policy import ContentSafetyPolicy, PolicyDecision


@dataclass(frozen=True)
class VisualSubject:
    subject_id: str
    age: int
    alive: bool = True
    ai_generated: bool = True


class VisualContentPolicy:
    """Limita o provador ao avatar adulto e fictício autorizado da Luna."""

    def __init__(self, content_policy: ContentSafetyPolicy):
        self.content_policy = content_policy

    def validate(
        self, user_id: str, prompt: str, subject: VisualSubject,
        adults_only_product: bool = False,
    ) -> PolicyDecision:
        decision = self.content_policy.evaluate(user_id, prompt, modality="try_on")
        if not decision.allowed:
            return decision
        if subject.subject_id != "luna" or not subject.ai_generated:
            return PolicyDecision(False, "unauthorized_identity", "O provador deste projeto só pode usar a personagem Luna.")
        if subject.age < 18:
            return PolicyDecision(False, "minor", "O provador não aceita pessoas menores de 18 anos.")
        if not subject.alive:
            return PolicyDecision(False, "deceased", "O provador não aceita pessoas mortas.")
        if adults_only_product and not self.content_policy.age_gate.is_verified(user_id):
            return PolicyDecision(False, "age_verification", "A demonstração de produtos adultos exige confirmação 18+.")
        return PolicyDecision(True)
