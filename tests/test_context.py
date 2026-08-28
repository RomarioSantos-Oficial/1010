from brain.context_manager import ContextManager


def test_context_caps_large_history():
    history = [{"role": "user", "content": f"mensagem {index}"} for index in range(1000)]
    selected = ContextManager(history_limit=20, max_chars=1000).select_history(history)
    assert len(selected) == 20
    assert selected[-1]["content"] == "mensagem 999"

