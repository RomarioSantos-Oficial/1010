from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    database_path: Path = ROOT / "data" / "app.db"
    persona_path: Path = ROOT / "config" / "persona.yaml"
    llm_provider: str = "auto"
    llm_model_path: Path = ROOT / "models" / "llm" / "model.gguf"
    llm_context_size: int = 4096
    llm_gpu_layers: int = -1
    llama_server_port: int = 8081
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=ROOT / ".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
