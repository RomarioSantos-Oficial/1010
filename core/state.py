from dataclasses import dataclass


@dataclass
class PersonaState:
    warmth: float = 0.8
    energy: float = 0.7
    humor: float = 0.5
    confidence: float = 0.7
    expression: str = "neutral"


@dataclass
class GlobalPersonaState(PersonaState):
    mode: str = "conversation"


@dataclass
class SessionState:
    user_id: str
    expression: str = "neutral"
    turn_count: int = 0
