from memory.service import MemoryService
from memory.sqlite_store import SQLiteStore


def test_memory_survives_new_store(tmp_path):
    path = tmp_path / "app.db"
    first = SQLiteStore(path)
    MemoryService(first).observe("ana", "Eu gosto de respostas curtas.")
    second = SQLiteStore(path)
    assert any("respostas curtas" in item["content"] for item in second.memories("ana"))


def test_history_is_isolated_by_user(tmp_path):
    store = SQLiteStore(tmp_path / "app.db")
    store.add_message("a", "user", "segredo A")
    store.add_message("b", "user", "mensagem B")
    assert store.history("a") == [{"role": "user", "content": "segredo A"}]

