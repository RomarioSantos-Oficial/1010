from core.state import SessionState
from persona.relationship_state import RelationshipState


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, SessionState] = {}
        self._relationships: dict[str, RelationshipState] = {}

    def session(self, user_id: str) -> SessionState:
        return self._sessions.setdefault(user_id, SessionState(user_id=user_id))

    def relationship(self, user_id: str) -> RelationshipState:
        return self._relationships.setdefault(user_id, RelationshipState())

    def observe(self, user_id: str, expression: str) -> None:
        session = self.session(user_id)
        session.expression = expression
        session.turn_count += 1
        self.relationship(user_id).observe_interaction()

    def clear(self, user_id: str) -> None:
        self._sessions.pop(user_id, None)
        self._relationships.pop(user_id, None)

