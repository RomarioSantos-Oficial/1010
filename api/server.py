import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from adult_commerce.age_gate import AgeGate
from avatar.avatar_2d import avatar_manifest
from avatar.avatar_3d import full_body_3d_manifest
from avatar.controller import AvatarController
from brain.context_manager import ContextManager
from brain.demo_provider import DemoProvider
from brain.llama_cpp_provider import LlamaCppProvider
from brain.llama_server_provider import LlamaServerProvider
from brain.prompt_builder import PromptBuilder
from brain.response_validator import ResponseValidator
from brain.tool_router import CommerceIntentRouter, CommerceToolRouter
from commerce.catalog import CatalogService
from config.settings import ROOT, settings
from core.logging import configure_logging
from core.orchestrator import Orchestrator
from live.chat_queue import LiveMessageQueue
from live.live_agent import LiveAgent
from live.obs_controller import OBSController, OBSUnavailable
from memory.embeddings import SentenceTransformerEmbeddings
from memory.memory_candidate import MemoryCandidateExtractor
from memory.qdrant_store import QdrantMemoryStore
from memory.semantic_memory import SemanticMemory
from memory.service import MemoryService
from memory.sqlite_store import SQLiteStore
from persona.identity import load_persona
from safety.content_policy import ContentSafetyPolicy
from speech.faster_whisper_provider import FasterWhisperProvider
from speech.kokoro_provider import KokoroProvider
from speech.microphone import MicrophoneRecorder
from speech.piper_provider import PiperProvider

logger = logging.getLogger("luna.api")


class ChatRequest(BaseModel):
    user_id: str = Field(default="local_user", min_length=1, max_length=80, pattern=r"^[\w.-]+$")
    text: str = Field(min_length=1, max_length=4000)


class AgeVerificationRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80, pattern=r"^[\w.-]+$")
    confirmed_adult: bool


class SpeechSynthesisRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1200)


class LiveStartRequest(BaseModel):
    connect_obs: bool = False


class LiveCommentRequest(BaseModel):
    platform: str = Field(default="local", min_length=1, max_length=40, pattern=r"^[\w.-]+$")
    user_id: str = Field(min_length=1, max_length=80, pattern=r"^[\w.-]+$")
    text: str = Field(min_length=1, max_length=500)


def make_provider():
    if settings.llm_provider == "demo":
        return DemoProvider()
    if settings.llm_provider == "llama_server":
        return LlamaServerProvider(settings.llm_model_path, settings.llm_context_size, settings.llm_gpu_layers, settings.llama_server_port)
    if settings.llm_provider in {"auto", "llama_cpp"}:
        try:
            return LlamaCppProvider(settings.llm_model_path, settings.llm_context_size, settings.llm_gpu_layers)
        except (RuntimeError, FileNotFoundError):
            if settings.llm_provider == "llama_cpp":
                raise
    return DemoProvider()


def make_tts_provider():
    if settings.tts_provider == "kokoro":
        return KokoroProvider(
            settings.tts_kokoro_model_dir,
            voice=settings.tts_voice,
            language=settings.tts_language,
            device=settings.tts_device,
            speed=settings.tts_speed,
            enabled=settings.tts_enabled,
        )
    if settings.tts_provider == "piper":
        provider = PiperProvider(
            settings.tts_model_path,
            settings.tts_use_cuda,
            settings.tts_length_scale,
        )
        provider.enabled = settings.tts_enabled
        return provider
    raise ValueError(f"TTS_PROVIDER desconhecido: {settings.tts_provider}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(ROOT)
    persona = load_persona(settings.persona_path)
    store = SQLiteStore(settings.database_path)
    embeddings = SentenceTransformerEmbeddings(settings.embedding_model)
    vectors = QdrantMemoryStore(settings.qdrant_path, embeddings.dimension)
    semantic = SemanticMemory(store, vectors, embeddings, settings.memory_similarity_threshold)
    semantic.sync_existing()
    memory = MemoryService(store, semantic, MemoryCandidateExtractor())
    catalog = CatalogService(settings.catalog_path)
    age_gate = AgeGate()
    safety = ContentSafetyPolicy(age_gate)
    live_agent = LiveAgent(
        safety,
        OBSController(
            host=settings.obs_host,
            port=settings.obs_port,
            password=settings.obs_password,
            enabled=settings.obs_enabled,
        ),
        LiveMessageQueue(
            max_size=settings.live_queue_size,
            duplicate_window_seconds=settings.live_duplicate_window_seconds,
        ),
    )
    tools = CommerceToolRouter(catalog, age_gate)
    provider = make_provider()
    stt = FasterWhisperProvider(settings.stt_model_path, settings.stt_device, settings.stt_compute_type)
    tts = make_tts_provider()
    avatar = AvatarController(settings.avatar_sprite_url)
    app.state.persona = persona
    app.state.store = store
    app.state.memory = memory
    app.state.semantic = semantic
    app.state.provider = provider
    app.state.catalog = catalog
    app.state.age_gate = age_gate
    app.state.tools = tools
    app.state.stt = stt
    app.state.tts = tts
    app.state.avatar = avatar
    app.state.live_agent = live_agent
    app.state.orchestrator = Orchestrator(
        provider, store, memory, PromptBuilder(persona), ResponseValidator(),
        ContextManager(settings.history_limit, settings.memory_limit),
        tools=tools, intent_router=CommerceIntentRouter(), safety=safety,
    )
    logger.info(
        "startup provider=%s semantic_memory=online stt_ready=%s tts_ready=%s",
        provider.name, stt.ready, tts.ready,
    )
    yield
    live_agent.stop()
    semantic.close()
    close = getattr(provider, "close", None)
    if close:
        close()


app = FastAPI(title="Luna IA Local", version="0.6.0", lifespan=lifespan)
WEB = ROOT / "ui" / "web"
app.mount("/static", StaticFiles(directory=WEB), name="static")
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB / "index.html")


@app.get("/health")
def health():
    database_ok = app.state.store.health()
    llm_ok = app.state.provider.name != "demo"
    return {
        "status": "ok" if database_ok else "degraded",
        "version": "0.6.0",
        "persona": app.state.persona.name,
        "api": "ok", "llm": "ok" if llm_ok else "demo",
        "database": "ok" if database_ok else "error",
        "memory": "ok", "qdrant": "ok", "catalog": "ok" if app.state.catalog.health() else "error",
        "tts": "ok" if app.state.tts.ready else "offline",
        "tts_optional": True,
        "tts_provider": app.state.tts.name,
        "tts_voice": getattr(app.state.tts, "voice", "configured"),
        "tts_voice_gender": getattr(app.state.tts, "voice_gender", "unknown"),
        "stt": "ok" if app.state.stt.ready else "offline",
        "avatar": "ok" if (ROOT / "assets" / "avatar" / "luna_sprite_v1_1.png").is_file() else "offline",
        "comfyui": "offline",
        "obs": "online" if app.state.live_agent.obs.connected else "configured" if settings.obs_enabled else "offline",
        "live": "running" if app.state.live_agent.running else "stopped",
        "llm_provider": app.state.provider.name, "model_ready": llm_ok,
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    request_id = uuid4().hex[:12]
    try:
        result = await app.state.orchestrator.process(request.user_id, request.text)
        avatar_state = app.state.avatar.react(result.emotion)
        return {
            **result.model_dump(), "provider": app.state.provider.name,
            "request_id": request_id, "avatar_state": avatar_state,
        }
    except Exception as exc:
        logger.exception("chat_failed request_id=%s provider=%s error_type=%s", request_id, app.state.provider.name, type(exc).__name__)
        raise HTTPException(status_code=500, detail="Falha ao gerar resposta local.", headers={"X-Request-ID": request_id}) from exc


@app.get("/memory/{user_id}")
def get_memory(user_id: str):
    return {"user_id": user_id, "memories": app.state.store.memories(user_id)}


@app.delete("/memory/{user_id}", status_code=204)
def delete_memory(user_id: str):
    app.state.memory.clear_user(user_id)
    app.state.orchestrator.sessions.clear(user_id)
    app.state.age_gate.clear(user_id)


@app.get("/products")
def list_products(category: str | None = None):
    return {"products": [product.model_dump() for product in app.state.catalog.search(category=category)]}


@app.get("/products/{sku}")
def get_product(sku: str):
    product = app.state.catalog.get(sku)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return product


@app.post("/adult/verify")
def verify_adult(request: AgeVerificationRequest):
    verified = app.state.age_gate.verify(request.user_id, request.confirmed_adult)
    return {"user_id": request.user_id, "adults_only_access": verified}


@app.post("/speech/transcribe")
async def transcribe_speech(audio: Annotated[UploadFile, File()], language: str = "pt"):
    request_id = uuid4().hex[:12]
    data = await audio.read(settings.max_audio_bytes + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Áudio vazio.")
    if len(data) > settings.max_audio_bytes:
        raise HTTPException(status_code=413, detail="Áudio maior que o limite permitido.")
    try:
        result = await asyncio.to_thread(app.state.stt.transcribe, data, language)
        return {
            "text": result.text,
            "language": result.language,
            "duration": result.duration,
            "segments": [segment.__dict__ for segment in result.segments],
            "provider": app.state.stt.name,
            "request_id": request_id,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Modelo local de transcrição indisponível.") from exc
    except Exception as exc:
        logger.exception("stt_failed request_id=%s error_type=%s", request_id, type(exc).__name__)
        raise HTTPException(status_code=400, detail="Não foi possível transcrever o áudio.") from exc


@app.post("/speech/synthesize")
async def synthesize_speech(request: SpeechSynthesisRequest):
    request_id = uuid4().hex[:12]
    try:
        result = await asyncio.to_thread(app.state.tts.synthesize, request.text)
        return Response(
            content=result.data,
            media_type=result.media_type,
            headers={
                "X-TTS-Provider": app.state.tts.name,
                "X-Audio-Duration": f"{result.duration:.3f}",
                "X-Request-ID": request_id,
            },
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Modelo local de voz indisponível.") from exc
    except Exception as exc:
        logger.exception("tts_failed request_id=%s error_type=%s", request_id, type(exc).__name__)
        raise HTTPException(status_code=500, detail="Não foi possível sintetizar a voz.") from exc


@app.get("/speech/devices")
def speech_devices():
    try:
        return {"input_devices": MicrophoneRecorder.input_devices()}
    except Exception:
        return {"input_devices": []}


@app.get("/avatar/state")
def avatar_state():
    return app.state.avatar.snapshot()


@app.get("/avatar/manifest")
def get_avatar_manifest():
    return avatar_manifest(settings.avatar_sprite_url)


@app.get("/avatar/3d/manifest")
def get_avatar_3d_manifest():
    return full_body_3d_manifest()


@app.get("/live/status")
def live_status():
    return app.state.live_agent.status()


@app.post("/live/start")
def live_start(request: LiveStartRequest):
    try:
        return app.state.live_agent.start(connect_obs=request.connect_obs)
    except OBSUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/live/stop")
def live_stop():
    return app.state.live_agent.stop()


@app.post("/live/comments")
def live_comment(request: LiveCommentRequest):
    moderation, queued = app.state.live_agent.ingest(request.platform, request.user_id, request.text)
    return {
        "accepted": bool(queued and queued.accepted),
        "code": queued.code if queued else moderation.code,
        "message": queued.message.to_dict() if queued and queued.message else None,
        "queue": app.state.live_agent.queue.stats(),
    }


@app.post("/live/process-next")
async def live_process_next():
    message = app.state.live_agent.next_message()
    if not message:
        return {"processed": False, "message": None, "response": None}
    result = await app.state.orchestrator.process(message.scoped_user_id, message.text)
    avatar_state = app.state.avatar.react(result.emotion)
    return {
        "processed": True,
        "message": message.to_dict(),
        "response": {
            **result.model_dump(),
            "provider": app.state.provider.name,
            "avatar_state": avatar_state,
        },
    }
