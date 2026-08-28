from core.session_manager import SessionManager


def test_session_and_relationship_are_isolated():
    sessions = SessionManager()
    sessions.observe("a", "happy")
    assert sessions.session("a").expression == "happy"
    assert sessions.relationship("a").interaction_count == 1
    assert sessions.session("b").expression == "neutral"
    assert sessions.relationship("b").interaction_count == 0

