from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    database_path: Path = ROOT / "data" / "app.db"
    catalog_path: Path = ROOT / "data" / "catalog.db"
    persona_path: Path = ROOT / "config" / "persona.yaml"
    llm_provider: str = "auto"
    llm_model_path: Path = ROOT / "models" / "llm" / "model.gguf"
    llm_context_size: int = 4096
    llm_gpu_layers: int = -1
    llama_server_port: int = 8081
    qdrant_path: Path = ROOT / "data" / "qdrant"
    embedding_model: str = str(ROOT / "models" / "embeddings" / "paraphrase-multilingual-MiniLM-L12-v2")
    semantic_memory_enabled: bool = True
    memory_similarity_threshold: float = 0.88
    stt_model_path: Path = ROOT / "models" / "stt" / "faster-whisper-small"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    tts_enabled: bool = True
    tts_provider: str = "kokoro"
    tts_kokoro_model_dir: Path = ROOT / "models" / "tts" / "kokoro-82m"
    tts_voice: str = "pf_dora"
    tts_language: str = "p"
    tts_device: str = "cpu"
    tts_speed: float = 1.0
    tts_model_path: Path = ROOT / "models" / "tts" / "pt_BR-faber-medium.onnx"
    tts_use_cuda: bool = False
    tts_length_scale: float = 1.0
    max_audio_bytes: int = 20 * 1024 * 1024
    avatar_sprite_url: str = "/assets/avatar/luna_sprite_v1_1.png"
    history_limit: int = 16
    memory_limit: int = 6
    obs_enabled: bool = False
    obs_host: str = "127.0.0.1"
    obs_port: int = 4455
    obs_password: str = ""
    live_queue_size: int = 200
    live_duplicate_window_seconds: float = 30.0
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
