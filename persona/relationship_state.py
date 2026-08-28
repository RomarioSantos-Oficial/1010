from dataclasses import dataclass


@dataclass
class RelationshipState:
    familiarity: float = 0.0
    warmth: float = 0.5
    interaction_count: int = 0
    preferred_tone: str = "neutral"

    def observe_interaction(self) -> None:
        self.interaction_count += 1
        self.familiarity = min(1.0, self.interaction_count / 20)

