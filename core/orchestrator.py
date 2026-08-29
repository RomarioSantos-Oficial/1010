import asyncio

from brain.action_router import ActionRequest
from brain.context_manager import ContextManager
from brain.llm_provider import LLMProvider
from brain.prompt_builder import PromptBuilder
from brain.response_validator import ResponseValidator, ValidatedResponse
from brain.tool_router import CommerceIntentRouter, CommerceToolRouter
from core.session_manager import SessionManager
from core.state import GlobalPersonaState
from memory.service import MemoryService
from memory.sqlite_store import SQLiteStore
from safety.content_policy import ContentSafetyPolicy


class Orchestrator:
    def __init__(
        self, llm: LLMProvider, store: SQLiteStore, memory: MemoryService,
        prompt_builder: PromptBuilder, validator: ResponseValidator,
        context_manager: ContextManager | None = None, sessions: SessionManager | None = None,
        tools: CommerceToolRouter | None = None, intent_router: CommerceIntentRouter | None = None,
        safety: ContentSafetyPolicy | None = None,
    ):
        self.llm = llm
        self.store = store
        self.memory = memory
        self.prompt_builder = prompt_builder
        self.validator = validator
        self.global_state = GlobalPersonaState()
        self.sessions = sessions or SessionManager()
        self.context = context_manager or ContextManager()
        self.tools = tools
        self.intent_router = intent_router or CommerceIntentRouter()
        self.safety = safety
        self._lock = asyncio.Lock()

    async def process(self, user_id: str, text: str) -> ValidatedResponse:
        if self.safety:
            decision = self.safety.evaluate(user_id, text)
            if not decision.allowed:
                return ValidatedResponse(
                    spoken_text=decision.message or "Não posso atender a esse pedido.",
                    emotion="neutral",
                    action_args={"safety_code": decision.code},
                )
        if self.tools:
            tool_result = self.tools.execute(user_id, text, self.intent_router.classify(text))
            if tool_result:
                result = ValidatedResponse(
                    spoken_text=tool_result.spoken_text,
                    emotion="happy" if tool_result.success else "neutral",
                    action=tool_result.action,
                    action_args=tool_result.data,
                )
                self._observe(user_id, text, result)
                return result
        history = self.context.select_history(self.store.history(user_id, self.context.history_limit))
        memories = self.context.select_memories(self.memory.retrieve(user_id, text, self.context.memory_limit))
        session = self.sessions.session(user_id)
        state = GlobalPersonaState(**{**self.global_state.__dict__, "expression": session.expression})
        messages = self.prompt_builder.build(text, memories, history, state, self.sessions.relationship(user_id))
        async with self._lock:
            answer = await asyncio.to_thread(self.llm.chat, messages)
        result = self.validator.validate(answer)
        if self.tools and result.action:
            tool_result = self.tools.execute_requested(
                user_id, text, ActionRequest(action=result.action, action_args=result.action_args)
            )
            if tool_result.error_code == "invalid_arguments":
                result.action = None
                result.action_args = {}
            else:
                result.spoken_text = tool_result.spoken_text
                result.action_args = tool_result.data
        self._observe(user_id, text, result)
        return result

    def _observe(self, user_id: str, text: str, result: ValidatedResponse) -> None:
        self.store.add_message(user_id, "user", text)
        self.store.add_message(user_id, "assistant", result.spoken_text)
        self.memory.observe(user_id, text)
        self.sessions.observe(user_id, result.emotion)
