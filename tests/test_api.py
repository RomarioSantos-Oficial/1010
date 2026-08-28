from fastapi.testclient import TestClient

import api.server as server


def test_chat_and_health(tmp_path, monkeypatch):
    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    with TestClient(server.app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["llm_provider"] == "demo"
        response = client.post("/chat", json={"user_id": "teste", "text": "Quem é você?"})
        assert response.status_code == 200
        assert "personagem virtual" in response.json()["spoken_text"]


def test_rejects_invalid_user_id(tmp_path, monkeypatch):
    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    with TestClient(server.app) as client:
        response = client.post("/chat", json={"user_id": "../x", "text": "oi"})
        assert response.status_code == 422

