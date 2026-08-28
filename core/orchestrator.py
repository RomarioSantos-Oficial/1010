import asyncio

from brain.llm_provider import LLMProvider
from brain.prompt_builder import PromptBuilder
from brain.response_validator import ResponseValidator, ValidatedResponse
from core.state import PersonaState
from memory.service import MemoryService
from memory.sqlite_store import SQLiteStore


class Orchestrator:
    def __init__(
        self,
        llm: LLMProvider,
        store: SQLiteStore,
        memory: MemoryService,
        prompt_builder: PromptBuilder,
        validator: ResponseValidator,
    ):
        self.llm = llm
        self.store = store
        self.memory = memory
        self.prompt_builder = prompt_builder
        self.validator = validator
        self.state = PersonaState()
        self._lock = asyncio.Lock()

    async def process(self, user_id: str, text: str) -> ValidatedResponse:
        history = self.store.history(user_id)
        memories = self.store.retrieve(user_id, text)
        messages = self.prompt_builder.build(text, memories, history, self.state)
        async with self._lock:
            answer = await asyncio.to_thread(self.llm.chat, messages)
        result = self.validator.validate(answer)
        self.store.add_message(user_id, "user", text)
        self.store.add_message(user_id, "assistant", result.spoken_text)
        self.memory.observe(user_id, text)
        self.state.expression = result.emotion
        return result

