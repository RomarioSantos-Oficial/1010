from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from brain.demo_provider import DemoProvider
from brain.llama_cpp_provider import LlamaCppProvider
from brain.llama_server_provider import LlamaServerProvider
from brain.prompt_builder import PromptBuilder
from brain.response_validator import ResponseValidator
from config.settings import ROOT, settings
from core.orchestrator import Orchestrator
from memory.service import MemoryService
from memory.sqlite_store import SQLiteStore
from persona.identity import load_persona


class ChatRequest(BaseModel):
    user_id: str = Field(default="local_user", min_length=1, max_length=80, pattern=r"^[\w.-]+$")
    text: str = Field(min_length=1, max_length=4000)


def make_provider():
    if settings.llm_provider == "demo":
        return DemoProvider()
    if settings.llm_provider == "llama_server":
        return LlamaServerProvider(
            settings.llm_model_path, settings.llm_context_size,
            settings.llm_gpu_layers, settings.llama_server_port,
        )
    if settings.llm_provider in {"auto", "llama_cpp"}:
        try:
            return LlamaCppProvider(
                settings.llm_model_path,
                settings.llm_context_size,
                settings.llm_gpu_layers,
            )
        except (RuntimeError, FileNotFoundError):
            if settings.llm_provider == "llama_cpp":
                raise
    return DemoProvider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    persona = load_persona(settings.persona_path)
    store = SQLiteStore(settings.database_path)
    provider = make_provider()
    app.state.persona = persona
    app.state.store = store
    app.state.provider = provider
    app.state.orchestrator = Orchestrator(
        provider, store, MemoryService(store), PromptBuilder(persona), ResponseValidator()
    )
    yield
    close = getattr(provider, "close", None)
    if close:
        close()


app = FastAPI(title="Luna IA Local", version="0.1.0", lifespan=lifespan)
WEB = ROOT / "ui" / "web"
app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "persona": app.state.persona.name,
        "llm_provider": app.state.provider.name,
        "model_ready": app.state.provider.name != "demo",
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = await app.state.orchestrator.process(request.user_id, request.text)
        return {**result.model_dump(), "provider": app.state.provider.name}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Falha ao gerar resposta local.") from exc


@app.get("/memory/{user_id}")
def get_memory(user_id: str):
    return {"user_id": user_id, "memories": app.state.store.memories(user_id)}


@app.delete("/memory/{user_id}", status_code=204)
def delete_memory(user_id: str):
    app.state.store.clear_user(user_id)
