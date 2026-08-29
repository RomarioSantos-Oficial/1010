from fastapi.testclient import TestClient

import api.server as server
from speech.stt import TranscriptionResult, TranscriptionSegment
from speech.tts import SynthesizedAudio
from tests.helpers import TestEmbeddings


def test_chat_and_health(tmp_path, monkeypatch):
    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(server.settings, "catalog_path", tmp_path / "catalog.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    monkeypatch.setattr(server, "SentenceTransformerEmbeddings", lambda _: TestEmbeddings())
    with TestClient(server.app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["llm_provider"] == "demo"
        response = client.post("/chat", json={"user_id": "teste", "text": "Quem é você?"})
        assert response.status_code == 200
        assert "personagem virtual" in response.json()["spoken_text"]


def test_rejects_invalid_user_id(tmp_path, monkeypatch):
    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(server.settings, "catalog_path", tmp_path / "catalog.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    monkeypatch.setattr(server, "SentenceTransformerEmbeddings", lambda _: TestEmbeddings())
    with TestClient(server.app) as client:
        response = client.post("/chat", json={"user_id": "../x", "text": "oi"})
        assert response.status_code == 422


def test_invalid_automatic_tool_arguments_preserve_conversation(tmp_path, monkeypatch):
    class InvalidArgsProvider:
        name = "demo"

        def chat(self, _messages):
            return (
                '{"spoken_text":"Vou lembrar que você prefere roupas azuis.",'
                '"emotion":"happy","action":"recommend_products",'
                '"action_args":{"color":"azul"},"memory_candidates":[]}'
            )

    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(server.settings, "catalog_path", tmp_path / "catalog.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    monkeypatch.setattr(server, "DemoProvider", InvalidArgsProvider)
    monkeypatch.setattr(server, "SentenceTransformerEmbeddings", lambda _: TestEmbeddings())
    with TestClient(server.app) as client:
        response = client.post(
            "/chat",
            json={"user_id": "teste", "text": "Eu prefiro roupas azuis."},
        )
        payload = response.json()
        assert response.status_code == 200
        assert payload["spoken_text"] == "Vou lembrar que você prefere roupas azuis."
        assert payload["action"] is None
        assert payload["action_args"] == {}


def test_speech_and_avatar_endpoints(tmp_path, monkeypatch):
    class FakeSTT:
        name = "fake-stt"
        ready = True

        def __init__(self, *_args, **_kwargs):
            pass

        def transcribe(self, _audio, language="pt"):
            return TranscriptionResult(
                text="Olá Luna", language=language, duration=1.2,
                segments=[TranscriptionSegment(0.0, 1.2, "Olá Luna")],
            )

    class FakeTTS:
        name = "fake-tts"
        ready = True

        def __init__(self, *_args, **_kwargs):
            pass

        def synthesize(self, _text):
            return SynthesizedAudio(b"RIFF-test", 22050, 0.4)

    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(server.settings, "catalog_path", tmp_path / "catalog.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    monkeypatch.setattr(server, "SentenceTransformerEmbeddings", lambda _: TestEmbeddings())
    monkeypatch.setattr(server, "FasterWhisperProvider", FakeSTT)
    monkeypatch.setattr(server, "KokoroProvider", FakeTTS)
    with TestClient(server.app) as client:
        health = client.get("/health").json()
        assert health["stt"] == "ok" and health["tts"] == "ok" and health["avatar"] == "ok"
        transcript = client.post("/speech/transcribe", files={"audio": ("test.wav", b"audio", "audio/wav")})
        assert transcript.status_code == 200
        assert transcript.json()["text"] == "Olá Luna"
        audio = client.post("/speech/synthesize", json={"text": "Olá!"})
        assert audio.status_code == 200 and audio.headers["content-type"] == "audio/wav"
        manifest = client.get("/avatar/manifest").json()
        assert manifest["ai_generated"] is True


def test_local_live_queue_and_response(tmp_path, monkeypatch):
    monkeypatch.setattr(server.settings, "database_path", tmp_path / "test.db")
    monkeypatch.setattr(server.settings, "qdrant_path", tmp_path / "qdrant")
    monkeypatch.setattr(server.settings, "catalog_path", tmp_path / "catalog.db")
    monkeypatch.setattr(server.settings, "llm_provider", "demo")
    monkeypatch.setattr(server.settings, "obs_enabled", False)
    monkeypatch.setattr(server, "SentenceTransformerEmbeddings", lambda _: TestEmbeddings())
    with TestClient(server.app) as client:
        started = client.post("/live/start", json={"connect_obs": False})
        assert started.status_code == 200
        assert started.json()["running"] is True

        queued = client.post(
            "/live/comments",
            json={"platform": "local", "user_id": "ana", "text": "Olá, Luna?"},
        )
        assert queued.status_code == 200
        assert queued.json()["accepted"] is True

        processed = client.post("/live/process-next")
        payload = processed.json()
        assert payload["processed"] is True
        assert payload["message"]["user_id"] == "ana"
        assert payload["response"]["spoken_text"]

        stopped = client.post("/live/stop")
        assert stopped.json()["running"] is False
