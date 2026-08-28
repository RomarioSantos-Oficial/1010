from tests.helpers import make_memory


def test_memory_survives_new_sqlite_store(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("ana", "Prefiro respostas curtas.")
    semantic.close()
    from memory.sqlite_store import SQLiteStore
    assert any("respostas curtas" in item["content"] for item in SQLiteStore(store.path).memories("ana"))


def test_semantic_memory_survives_restart(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("ana", "Prefiro produtos discretos")
    semantic.close()
    store, semantic, memory = make_memory(tmp_path)
    assert "discreto" in memory.retrieve("ana", "Qual estilo combina comigo?")[0]
    semantic.close()


def test_history_is_isolated_by_user(tmp_path):
    store, semantic, _ = make_memory(tmp_path)
    store.add_message("a", "user", "segredo A")
    store.add_message("b", "user", "mensagem B")
    assert store.history("a") == [{"role": "user", "content": "segredo A"}]
    semantic.close()


def test_sensitive_data_and_name_are_not_stored(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("ana", "Meu CPF é 123.456.789-00")
    memory.observe("ana", "Meu nome é Ana")
    assert store.memories("ana") == []
    semantic.close()


def test_shopping_style_is_normalized(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("ana", "Prefiro produtos mais discretos.")
    item = store.memories("ana")[0]
    assert item["memory_type"] == "shopping_style"
    assert item["canonical_key"] == "shopping_style"
    assert "discreto" in item["content"]
    semantic.close()


def test_changed_preference_updates_instead_of_growing(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("ana", "Gosto de vermelho.")
    memory.observe("ana", "Ultimamente prefiro preto.")
    items = store.memories("ana")
    assert len(items) == 1
    assert "preto" in items[0]["content"]
    assert items[0]["updated_at"] >= items[0]["created_at"]
    semantic.close()


def test_duplicate_preferences_do_not_accumulate(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("ana", "Gosto de vestidos pretos")
    memory.observe("ana", "Prefiro vestidos pretos")
    memory.observe("ana", "Adoro vestido preto")
    assert len(store.memories("ana")) == 1
    semantic.close()


def test_delete_and_user_isolation(tmp_path):
    store, semantic, memory = make_memory(tmp_path)
    memory.observe("a", "Prefiro produtos discretos")
    memory.observe("b", "Prefiro produtos marcantes")
    assert "discreto" in memory.retrieve("a", "Que estilo eu gosto?")[0]
    memory.clear_user("a")
    assert store.memories("a") == []
    assert len(store.memories("b")) == 1
    semantic.close()
